# -*- coding: utf-8 -*-
import sys
import csv
import json
import hashlib
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import duckdb
except Exception as exc:
    print("FEHLER: DuckDB-Modul konnte nicht geladen werden:", repr(exc))
    raise

ROOT = Path(r"I:\KI_Legal_Project")
DB = ROOT / "Database" / "Legal_Brain.duckdb"
POST = ROOT / "Posteingang"

DIRS = {
    "geprueft": POST / "02_Technisch_Geprueft",
    "signatur": POST / "07_Signaturpruefung",
    "sprachpruefung": POST / "08_Sprachpruefung",
    "protokolle": POST / "90_Protokolle",
    "sprachberichte": POST / "93_Sprachberichte"
}

TEXT_EXT = {".txt", ".md", ".eml", ".xml", ".csv", ".json", ".rtf"}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    for p in DIRS.values():
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def intake_id_from_name(path):
    name = path.name
    if "__" in name:
        return name.split("__", 1)[0]
    return "LANG_" + sha256_file(path)[:16]

def read_text_sample(path):
    ext = path.suffix.lower()
    if ext not in TEXT_EXT:
        return path.name

    try:
        data = path.read_bytes()[:200000]
        for enc in ["utf-8", "utf-8-sig", "cp1252", "latin-1"]:
            try:
                return data.decode(enc, errors="replace")
            except Exception:
                pass
    except Exception:
        pass

    return path.name

def score_language(text):
    low = text.lower()

    markers = {
        "sv": [
            "tingsrätt", "förvaltningsrätten", "arbetsdomstolen", "arbetsrätt",
            "uppsägning", "anställning", "skolinspektionen", "skollagen",
            "mål nr", "yrkande", "bevisuppgift", "sakframställning",
            "svenska", "sverige", "las "
        ],
        "de": [
            "gericht", "klage", "beklagte", "kläger", "arbeitsrecht",
            "kündigung", "anwalt", "schriftsatz", "beweis", "antrag",
            "deutsch", "bundesrepublik", "verwaltungsgericht"
        ],
        "en": [
            "court", "claim", "employment", "lawyer", "defendant",
            "evidence", "statement", "procedure", "english", "sweden",
            "opposing counsel"
        ],
        "fr": ["tribunal", "avocat", "preuve", "requête", "français"],
        "es": ["tribunal", "abogado", "prueba", "demanda", "español"],
        "it": ["tribunale", "avvocato", "prova", "ricorso", "italiano"],
        "pl": ["sąd", "adwokat", "dowód", "pozew", "polski"],
        "nl": ["rechtbank", "advocaat", "bewijs", "nederlands"]
    }

    scores = {}
    for code, words in markers.items():
        scores[code] = sum(1 for w in words if w in low)

    best = max(scores, key=lambda k: scores[k])
    best_score = scores[best]

    if best_score == 0:
        return "unklar", "niedrig", scores

    ordered = sorted(scores.values(), reverse=True)
    second = ordered[1] if len(ordered) > 1 else 0

    if best_score >= 3 and best_score >= second + 2:
        return best, "hoch", scores
    if best_score >= 2:
        return best, "mittel", scores
    return best, "niedrig", scores

def derive_case_profile(text, detected):
    low = text.lower()

    jurisdiction = ""
    procedural = detected if detected != "unklar" else ""
    internal = "de"
    translation_required = detected not in {"de", "unklar"}
    notes = []

    if detected == "sv" or any(x in low for x in ["schweden", "sverige", "tingsrätt", "förvaltningsrätten", "arbetsdomstolen", "skolinspektionen"]):
        jurisdiction = "SE"
        procedural = "sv"
        translation_required = True
        notes.append("Schweden-Bezug erkannt. Prozeßsprache regelmäßig Schwedisch.")

        if any(x in low for x in ["arbetsrätt", "anställning", "uppsägning", "las ", "arbeitsrecht"]):
            notes.append("Arbeitsrechtlicher Schweden-Bezug erkannt.")

        notes.append("Interne Arbeitssprache Deutsch. Kommunikation mit gegnerischem Anwalt kann Englisch sein.")

    elif detected == "de":
        jurisdiction = "DE"
        procedural = "de"
        translation_required = False
        notes.append("Deutscher Sprach- und Rechtsbezug möglich.")

    elif detected == "en":
        procedural = "en"
        translation_required = True
        notes.append("Englische Kommunikation oder englischsprachiges Dokument erkannt.")

    else:
        procedural = ""
        translation_required = True
        notes.append("Sprache nicht sicher erkannt. Manuelle Sprachentscheidung erforderlich.")

    return {
        "jurisdiction_country_code": jurisdiction,
        "procedural_language_code": procedural,
        "internal_work_language_code": internal,
        "translation_required": translation_required,
        "notes": " ".join(notes)
    }

def create_test_files():
    target = DIRS["geprueft"]
    existing = [p for p in target.iterdir() if p.is_file() and p.name.startswith("TESTLANG_")]
    if existing:
        return

    (target / "TESTLANG_DE_deutscher_schriftsatz.txt").write_text(
        "Klage vor dem Verwaltungsgericht. Antrag, Beweis, Schriftsatz, deutscher Fall.\n",
        encoding="utf-8",
        newline="\n"
    )

    (target / "TESTLANG_SV_schwedischer_arbeitsrechtsfall.txt").write_text(
        "Mål nr T 4928-25. Norrköpings tingsrätt. Arbetsrätt, uppsägning, anställning, LAS och bevisuppgift.\n",
        encoding="utf-8",
        newline="\n"
    )

    (target / "TESTLANG_EN_communication_opposing_counsel.txt").write_text(
        "Communication with opposing counsel in an employment dispute concerning Sweden and court procedure.\n",
        encoding="utf-8",
        newline="\n"
    )

def load_allowed_languages(con):
    rows = con.execute("SELECT language_code FROM app_languages WHERE active_in_system = TRUE").fetchall()
    return {r[0] for r in rows}

def write_profile(con, rec):
    con.execute("DELETE FROM posteingang_language_profiles WHERE intake_id = ?", [rec["intake_id"]])
    con.execute(
        """
        INSERT INTO posteingang_language_profiles
        (intake_id, original_name, declared_language_code, detected_language_code,
         jurisdiction_country_code, procedural_language_code, internal_work_language_code,
         translation_required, confidence, notes, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        [
            rec["intake_id"],
            rec["original_name"],
            rec["declared_language_code"],
            rec["detected_language_code"],
            rec["jurisdiction_country_code"],
            rec["procedural_language_code"],
            rec["internal_work_language_code"],
            rec["translation_required"],
            rec["confidence"],
            rec["notes"]
        ]
    )

def process_file(con, path):
    text = read_text_sample(path)
    detected, confidence, scores = score_language(path.name + "\n" + text)
    profile = derive_case_profile(path.name + "\n" + text, detected)
    digest = sha256_file(path)
    intake_id = intake_id_from_name(path)

    rec = {
        "intake_id": intake_id,
        "original_name": path.name,
        "stored_path": str(path),
        "sha256": digest,
        "declared_language_code": "",
        "detected_language_code": detected,
        "confidence": confidence,
        "language_scores": json.dumps(scores, ensure_ascii=False),
        "jurisdiction_country_code": profile["jurisdiction_country_code"],
        "procedural_language_code": profile["procedural_language_code"],
        "internal_work_language_code": profile["internal_work_language_code"],
        "translation_required": profile["translation_required"],
        "notes": profile["notes"],
        "created_at": now()
    }

    write_profile(con, rec)

    report = DIRS["sprachberichte"] / f"{intake_id}_sprachbericht.json"
    report.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    rec["language_report"] = str(report)

    return rec

def main():
    ensure_dirs()

    if "--create-test" in sys.argv:
        create_test_files()

    con = duckdb.connect(str(DB))

    try:
        eu_count = con.execute("SELECT COUNT(*) FROM app_languages WHERE eu_official = TRUE").fetchone()[0]
    except Exception as exc:
        raise RuntimeError("Sprachgrundlagen fehlen. Tabelle app_languages nicht lesbar: " + repr(exc))

    if eu_count != 24:
        raise RuntimeError("EU24-Sprachen unvollständig. Gefunden: " + str(eu_count))

    try:
        con.execute("SELECT COUNT(*) FROM posteingang_language_profiles").fetchone()
    except Exception as exc:
        raise RuntimeError("Tabelle posteingang_language_profiles fehlt: " + repr(exc))

    allowed = load_allowed_languages(con)
    if "sv" not in allowed or "de" not in allowed or "en" not in allowed:
        raise RuntimeError("Pflichtsprachen de, en, sv fehlen.")

    files = []
    for folder in [DIRS["geprueft"], DIRS["signatur"]]:
        if folder.exists():
            for p in sorted(folder.iterdir()):
                if p.is_file() and p.name != ".gitkeep":
                    files.append(p)

    records = []

    con.execute("BEGIN TRANSACTION")
    try:
        for p in files:
            records.append(process_file(con, p))
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        raise

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    protocol = DIRS["protokolle"] / f"POSTEINGANG_SPRACHGATE_V1_{ts}.txt"
    csv_file = DIRS["protokolle"] / f"POSTEINGANG_SPRACHGATE_V1_{ts}.csv"
    jsonl_file = DIRS["protokolle"] / f"POSTEINGANG_SPRACHGATE_V1_{ts}.jsonl"

    fields = [
        "intake_id", "original_name", "stored_path", "sha256",
        "detected_language_code", "confidence", "language_scores",
        "jurisdiction_country_code", "procedural_language_code",
        "internal_work_language_code", "translation_required",
        "notes", "language_report"
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, "") for k in fields})

    with open(jsonl_file, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(protocol, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG SPRACHGATE V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + now() + "\n")
        f.write("Verarbeitete Dateien: " + str(len(records)) + "\n\n")
        for r in records:
            f.write(
                f"{r.get('intake_id')} | {r.get('original_name')} | "
                f"Sprache={r.get('detected_language_code')} | "
                f"Verfahren={r.get('procedural_language_code')} | "
                f"intern={r.get('internal_work_language_code')} | "
                f"Übersetzung={r.get('translation_required')}\n"
            )

    print("")
    print("POSTEINGANG_SPRACHGATE_V1 FERTIG")
    print("Protokoll:", protocol)
    print("CSV:", csv_file)
    print("JSONL:", jsonl_file)
    print("Verarbeitete Dateien:", len(records))

    con.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")
        print("ABGEBROCHEN DURCH STRG+C")
        print("Zurück zum Einstiegspunkt: I:\\KI_Legal_Project")
        sys.exit(130)
