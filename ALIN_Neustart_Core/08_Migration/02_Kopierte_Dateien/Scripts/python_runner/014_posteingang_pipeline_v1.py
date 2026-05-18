# -*- coding: utf-8 -*-
import sys
import json
import csv
import subprocess
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(r"I:\KI_Legal_Project")
POST = ROOT / "Posteingang"

SECURITY_GATE = ROOT / "Scripts" / "python_runner" / "005_posteingang_sicherheitsgate_v2.py"
LANGUAGE_GATE = ROOT / "Scripts" / "python_runner" / "012_posteingang_sprachkontext_gate_v2.py"

DIRS = {
    "roh": POST / "00_Roh_Eingang",
    "quarantaene": POST / "01_Quarantaene",
    "geprueft": POST / "02_Technisch_Geprueft",
    "vorzimmer": POST / "03_Vorzimmer_Entscheidung",
    "anwalt": POST / "04_Anwaltvorlage",
    "rueckfrage": POST / "05_Rueckfrage_Absender",
    "abgewiesen": POST / "06_Abgewiesen",
    "signatur": POST / "07_Signaturpruefung",
    "sprachpruefung": POST / "08_Sprachpruefung",
    "protokolle": POST / "90_Protokolle",
    "karten": POST / "91_Entscheidungskarten",
    "sicherheit": POST / "92_Sicherheitsberichte",
    "sprachen": POST / "93_Sprachberichte",
    "archiv": POST / "99_Archiv_Altlasten",
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def active_files(path):
    if not path.exists():
        return []
    return sorted([
        p for p in path.rglob("*")
        if p.is_file()
        and p.name != ".gitkeep"
        and p.name != "README_POSTEINGANG.md"
        and "99_Archiv_Altlasten" not in str(p)
    ])

def count_active():
    return {key: len(active_files(path)) for key, path in DIRS.items()}

def newest(pattern):
    files = sorted(DIRS["protokolle"].glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return str(files[0]) if files else ""

def run_cmd(args, label):
    print("")
    print("STARTE:", label)
    print("BEFEHL:", " ".join(str(a) for a in args))

    p = subprocess.run(
        [str(a) for a in args],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    if p.stdout:
        print(p.stdout)

    if p.returncode != 0:
        raise RuntimeError(label + " fehlgeschlagen. Exitcode: " + str(p.returncode))

    return p.stdout or ""

def ensure_dirs():
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)
        keep = path / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

def write_pipeline_report(case_template, before, after_security, after_language, language_ran):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = DIRS["protokolle"] / f"POSTEINGANG_PIPELINE_V1_{ts}.txt"
    jsn = DIRS["protokolle"] / f"POSTEINGANG_PIPELINE_V1_{ts}.json"
    csv_file = DIRS["protokolle"] / f"POSTEINGANG_PIPELINE_V1_{ts}.csv"

    data = {
        "time": now(),
        "case_template": case_template,
        "security_gate": str(SECURITY_GATE),
        "language_gate": str(LANGUAGE_GATE),
        "language_gate_ran": language_ran,
        "counts_before": before,
        "counts_after_security": after_security,
        "counts_after_language": after_language,
        "latest_security_txt": newest("POSTEINGANG_SICHERHEITSGATE_V2_*.txt"),
        "latest_security_csv": newest("POSTEINGANG_SICHERHEITSGATE_V2_*.csv"),
        "latest_security_jsonl": newest("POSTEINGANG_SICHERHEITSGATE_V2_*.jsonl"),
        "latest_language_txt": newest("POSTEINGANG_SPRACHKONTEXT_GATE_V2_*.txt"),
        "latest_language_csv": newest("POSTEINGANG_SPRACHKONTEXT_GATE_V2_*.csv"),
        "latest_language_jsonl": newest("POSTEINGANG_SPRACHKONTEXT_GATE_V2_*.jsonl"),
    }

    jsn.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Bereich", "vorher", "nach_sicherheit", "nach_sprache"])
        for key in sorted(DIRS.keys()):
            writer.writerow([
                key,
                before.get(key, 0),
                after_security.get(key, 0),
                after_language.get(key, 0),
            ])

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG PIPELINE V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Fallvorlage: " + case_template + "\n")
        f.write("Sicherheitsgate: " + str(SECURITY_GATE) + "\n")
        f.write("Sprachgate: " + str(LANGUAGE_GATE) + "\n")
        f.write("Sprachgate ausgeführt: " + str(language_ran) + "\n\n")

        f.write("ZAEHLUNG\n")
        f.write("-" * 80 + "\n")
        for key in sorted(DIRS.keys()):
            f.write(
                f"{key}: vorher={before.get(key, 0)} | "
                f"nach_sicherheit={after_security.get(key, 0)} | "
                f"nach_sprache={after_language.get(key, 0)}\n"
            )

        f.write("\nLETZTE TEILPROTOKOLLE\n")
        f.write("-" * 80 + "\n")
        for k, v in data.items():
            if k.startswith("latest_"):
                f.write(k + ": " + str(v) + "\n")

    return txt, csv_file, jsn

def main():
    case_template = "TEMPLATE_SE_ARBEITSRECHT"

    if "--case-template" in sys.argv:
        i = sys.argv.index("--case-template")
        if i + 1 < len(sys.argv):
            case_template = sys.argv[i + 1]

    ensure_dirs()

    if not SECURITY_GATE.exists():
        raise RuntimeError("Sicherheitsgate fehlt: " + str(SECURITY_GATE))

    if not LANGUAGE_GATE.exists():
        raise RuntimeError("Sprachkontext-Gate fehlt: " + str(LANGUAGE_GATE))

    before = count_active()

    raw_count = before.get("roh", 0)
    print("Aktive Rohdateien vor Start:", raw_count)

    if raw_count > 0:
        run_cmd([sys.executable, SECURITY_GATE], "Sicherheitsgate V2")
    else:
        print("Keine Rohdateien vorhanden. Sicherheitsgate wird nicht ausgeführt.")

    after_security = count_active()

    language_ran = False
    checked_count = after_security.get("geprueft", 0)

    if checked_count > 0:
        run_cmd(
            [sys.executable, LANGUAGE_GATE, "--case-template", case_template],
            "Sprachkontext-Gate V2"
        )
        language_ran = True
    else:
        print("Keine technisch freigegebenen Dateien vorhanden. Sprachkontext-Gate wird nicht ausgeführt.")

    after_language = count_active()

    txt, csv_file, jsn = write_pipeline_report(
        case_template,
        before,
        after_security,
        after_language,
        language_ran
    )

    print("")
    print("POSTEINGANG_PIPELINE_V1 FERTIG")
    print("Fallvorlage:", case_template)
    print("Pipeline-Protokoll:", txt)
    print("Pipeline-CSV:", csv_file)
    print("Pipeline-JSON:", jsn)
    print("")
    print("Aktiver Stand:")
    for key in sorted(after_language.keys()):
        print(key + ":", after_language[key])

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except KeyboardInterrupt:
        print("")
        print("ABGEBROCHEN DURCH STRG+C")
        print("Zurueck zum Einstiegspunkt: I:\\KI_Legal_Project")
        sys.exit(130)
    except Exception as exc:
        print("")
        print("FEHLER")
        print(repr(exc))
        print("Zurueck zum Einstiegspunkt: I:\\KI_Legal_Project")
        sys.exit(1)
