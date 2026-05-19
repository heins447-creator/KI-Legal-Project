# -*- coding: utf-8 -*-
import sys
import csv
import json
import shutil
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
PIPELINE = ROOT / "Scripts" / "python_runner" / "014_posteingang_pipeline_v1.py"
LOG_DIR = ROOT / "Windows_App" / "Logs"

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

def ensure_dirs():
    for p in DIRS.values():
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

def active_files():
    files = []
    for key, path in DIRS.items():
        if key == "archiv":
            continue
        if not path.exists():
            continue
        for p in path.rglob("*"):
            if p.is_file() and p.name not in {".gitkeep", "README_POSTEINGANG.md"}:
                files.append(p)
    return sorted(files)

def read_small(path, limit=1024 * 1024):
    try:
        with open(path, "rb") as f:
            return f.read(limit)
    except Exception:
        return b""

def contains_marker(path, marker):
    if marker in path.name:
        return True
    data = read_small(path)
    try:
        return marker in data.decode("utf-8", errors="ignore")
    except Exception:
        return False

def write_file(path, text):
    path.write_text(text, encoding="utf-8", newline="\n")

def run_pipeline():
    p = subprocess.run(
        [sys.executable, str(PIPELINE), "--case-template", "TEMPLATE_SE_ARBEITSRECHT"],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    print(p.stdout or "")

    if p.returncode != 0:
        raise RuntimeError("Pipeline fehlgeschlagen. Exitcode: " + str(p.returncode))

def collect_generated(marker, start_time):
    found = []

    for key, path in DIRS.items():
        if key == "archiv":
            continue
        if not path.exists():
            continue

        for p in path.rglob("*"):
            if not p.is_file():
                continue
            if p.name in {".gitkeep", "README_POSTEINGANG.md"}:
                continue

            try:
                mtime_ok = p.stat().st_mtime >= start_time - 2
            except Exception:
                mtime_ok = False

            if contains_marker(p, marker) or (key == "protokolle" and mtime_ok):
                found.append(p)

    return sorted(set(found))

def verify(marker):
    all_files = active_files()

    def in_dir(key, needle):
        base = DIRS[key]
        hits = []
        for p in all_files:
            if p.is_relative_to(base) and needle in p.name:
                hits.append(p)
        return hits

    ps1_hits = in_dir("quarantaene", marker + "_003_aktive_datei")
    eml_hits = in_dir("signatur", marker + "_004_signierte_mail")
    sv_hits = [p for p in all_files if marker + "_001_schwedisch" in p.name]
    de_hits = [p for p in all_files if marker + "_002_deutsch" in p.name]

    sprachberichte = [
        p for p in all_files
        if p.is_relative_to(DIRS["sprachen"]) and contains_marker(p, marker)
    ]

    sprachkarten = [
        p for p in all_files
        if p.is_relative_to(DIRS["vorzimmer"]) and p.name.endswith("_sprachkarte.json") and contains_marker(p, marker)
    ]

    sicherheitsberichte = [
        p for p in all_files
        if p.is_relative_to(DIRS["sicherheit"]) and contains_marker(p, marker)
    ]

    errors = []

    if not ps1_hits:
        errors.append("Aktive PS1-Testdatei wurde nicht in Quarantaene gefunden.")

    if not eml_hits:
        errors.append("Signierte EML-Testdatei wurde nicht im Signaturbereich gefunden.")

    if not sv_hits:
        errors.append("Schwedische Testdatei wurde nach Pipeline nicht gefunden.")

    if not de_hits:
        errors.append("Deutsche Testdatei wurde nach Pipeline nicht gefunden.")

    if not sicherheitsberichte:
        errors.append("Keine Sicherheitsberichte zum Testlauf gefunden.")

    if not sprachberichte:
        errors.append("Keine Sprachberichte zum Testlauf gefunden.")

    if not sprachkarten:
        errors.append("Keine Sprachkarten zum Testlauf gefunden.")

    return {
        "errors": errors,
        "ps1_hits": [str(x) for x in ps1_hits],
        "eml_hits": [str(x) for x in eml_hits],
        "sv_hits": [str(x) for x in sv_hits],
        "de_hits": [str(x) for x in de_hits],
        "sicherheitsberichte": [str(x) for x in sicherheitsberichte],
        "sprachberichte": [str(x) for x in sprachberichte],
        "sprachkarten": [str(x) for x in sprachkarten],
    }

def archive_files(files, marker):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive = DIRS["archiv"] / f"{ts}_pipeline_smoketest_{marker}"
    archive.mkdir(parents=True, exist_ok=True)

    manifest = archive / f"MANIFEST_PIPELINE_SMOKETEST_{ts}.csv"

    rows = []

    for src in sorted(files):
        if not src.exists():
            continue
        if DIRS["archiv"] in src.parents:
            continue

        rel = src.relative_to(POST)
        dst = archive / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(src), str(dst))

        rows.append({
            "original_path": str(src),
            "archive_path": str(dst),
            "size_bytes": dst.stat().st_size if dst.exists() else 0,
        })

    with open(manifest, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["original_path", "archive_path", "size_bytes"], delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return archive, manifest, rows

def final_active_count():
    return len(active_files())

def main():
    ensure_dirs()

    if not PIPELINE.exists():
        raise RuntimeError("Pipeline fehlt: " + str(PIPELINE))

    if active_files():
        raise RuntimeError("Aktiver Posteingang ist nicht leer. Erst bereinigen, dann Smoketest ausführen.")

    marker = "SMOKE_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    start_time = datetime.datetime.now().timestamp()

    write_file(
        DIRS["roh"] / f"{marker}_001_schwedisch.txt",
        "Detta är ett svenskt arbetsrättsligt dokument. Domstolen, arbetstagaren och arbetsgivaren nämns som test.\n"
    )

    write_file(
        DIRS["roh"] / f"{marker}_002_deutsch.txt",
        "Dies ist ein deutscher Schriftsatz als Testdatei. Gericht, Mandant und Gegenseite werden erwähnt.\n"
    )

    write_file(
        DIRS["roh"] / f"{marker}_003_aktive_datei.ps1",
        "Write-Host 'Diese Testdatei darf nicht in den normalen Bestand.'\n"
    )

    write_file(
        DIRS["roh"] / f"{marker}_004_signierte_mail.eml",
        "From: test@example.invalid\n"
        "To: kanzlei@example.invalid\n"
        "Subject: Test signierte Nachricht\n"
        "MIME-Version: 1.0\n"
        "Content-Type: multipart/signed; protocol=\"application/pkcs7-signature\"; micalg=sha-256; boundary=\"abc\"\n"
        "\n"
        "--abc\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Nur Test. Keine echte Postsendung.\n"
        "--abc\n"
        "Content-Type: application/pkcs7-signature; name=smime.p7s\n"
        "\n"
        "TEST\n"
        "--abc--\n"
    )

    print("SMOKETEST MARKER:", marker)
    print("Testdateien erzeugt:", 4)

    run_pipeline()

    result = verify(marker)
    generated = collect_generated(marker, start_time)

    report_json = LOG_DIR / f"POSTEINGANG_PIPELINE_SMOKETEST_V1_{marker}.json"
    report_txt = LOG_DIR / f"POSTEINGANG_PIPELINE_SMOKETEST_V1_{marker}.txt"

    data = {
        "time": now(),
        "marker": marker,
        "result": result,
        "generated_files": [str(x) for x in generated],
    }

    report_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    with open(report_txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG PIPELINE SMOKETEST V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + now() + "\n")
        f.write("Marker: " + marker + "\n")
        f.write("Fehler: " + str(len(result["errors"])) + "\n\n")

        if result["errors"]:
            f.write("FEHLER\n")
            f.write("-" * 80 + "\n")
            for e in result["errors"]:
                f.write(e + "\n")

        f.write("\nGEFUNDENE NACHWEISE\n")
        f.write("-" * 80 + "\n")
        for key, value in result.items():
            f.write(key + ": " + json.dumps(value, ensure_ascii=False) + "\n")

        f.write("\nGENERIERTE DATEIEN\n")
        f.write("-" * 80 + "\n")
        for p in generated:
            f.write(str(p) + "\n")

    archive, manifest, rows = archive_files(generated, marker)

    remaining = final_active_count()

    print("")
    print("POSTEINGANG_PIPELINE_SMOKETEST_V1 FERTIG")
    print("Marker:", marker)
    print("Fehler:", len(result["errors"]))
    print("Windows-Report TXT:", report_txt)
    print("Windows-Report JSON:", report_json)
    print("Archiv:", archive)
    print("Manifest:", manifest)
    print("Archivierte Dateien:", len(rows))
    print("Aktive Dateien nach Archivierung:", remaining)

    if result["errors"]:
        for e in result["errors"]:
            print("FEHLER:", e)
        raise RuntimeError("Smoketest fachlich fehlgeschlagen.")

    if remaining != 0:
        raise RuntimeError("Nach Smoketest sind noch aktive Posteingangsdateien vorhanden: " + str(remaining))

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
