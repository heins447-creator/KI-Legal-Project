# -*- coding: utf-8 -*-
import sys
import csv
import json
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import duckdb

ROOT = Path(r"I:\KI_Legal_Project")
DB = ROOT / "Database" / "Legal_Brain.duckdb"
POST = ROOT / "Posteingang"
LOG = ROOT / "Windows_App" / "Logs"

DECISION_DIR = LOG / "Vorzimmer_Entscheidungen"
CLEAN_DIR = DECISION_DIR / "Entwuerfe_Bereinigt"
PROPOSAL_DIR = LOG / "Vorzimmer_Entscheidungsvorschlaege"

CASE_KEY = "TEMPLATE_SE_ARBEITSRECHT"

FIELDS = [
    "decision_id",
    "intake_id",
    "source_path",
    "aktion",
    "begruendung",
    "frist",
    "verantwortlich",
]

DIRS = {
    "geprueft": POST / "02_Technisch_Geprueft",
    "vorzimmer": POST / "03_Vorzimmer_Entscheidung",
    "quarantaene": POST / "01_Quarantaene",
    "signatur": POST / "07_Signaturpruefung",
    "sprachpruefung": POST / "08_Sprachpruefung",
    "anwalt": POST / "04_Anwaltvorlage",
}

IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def q(name):
    return '"' + str(name).replace('"', '""') + '"'

def table_exists(con, table):
    row = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name = ?
        """,
        [table]
    ).fetchone()
    return bool(row and row[0] > 0)

def columns(con, table):
    if not table_exists(con, table):
        return set()
    rows = con.execute("PRAGMA table_info(" + q(table) + ")").fetchall()
    return {str(r[1]) for r in rows}

def update_existing(con, table, key_col, key_val, values):
    cols = columns(con, table)
    if not cols or key_col not in cols:
        return False

    present = {k: v for k, v in values.items() if k in cols and k != key_col}
    exists = con.execute(
        "SELECT COUNT(*) FROM " + q(table) + " WHERE " + q(key_col) + " = ?",
        [key_val]
    ).fetchone()[0] > 0

    if exists:
        if present:
            sql = "UPDATE " + q(table) + " SET " + ", ".join(q(k) + " = ?" for k in present.keys()) + " WHERE " + q(key_col) + " = ?"
            con.execute(sql, list(present.values()) + [key_val])
    else:
        insert_values = dict(values)
        insert_values[key_col] = key_val
        insert_values = {k: v for k, v in insert_values.items() if k in cols}
        sql = "INSERT INTO " + q(table) + " (" + ", ".join(q(k) for k in insert_values.keys()) + ") VALUES (" + ", ".join(["?"] * len(insert_values)) + ")"
        con.execute(sql, list(insert_values.values()))

    return True

def correct_language_context(con):
    changed = []

    case_values = {
        "case_template_key": CASE_KEY,
        "case_key": CASE_KEY,
        "case_label": "Schweden Arbeitsrecht, Arbeitnehmer gegen kommunalen Arbeitgeber",
        "jurisdiction_country_code": "SE",
        "country_language_code": "sv",
        "procedural_language_code": "sv",
        "default_document_language_code": "sv",
        "expected_document_language_code": "sv",
        "internal_work_language_code": "de",
        "target_work_language_code": "de",
        "court_language_code": "sv",
        "opponent_lawyer_language_code": "sv",
        "opponent_party_language_code": "sv",
        "client_language_code": "sv",
        "translation_required": True,
        "interpreter_required": False,
        "notes": "Korrektur: schwedischer Arbeitsrechtsstreit. Amtssprache, Prozesssprache, Gericht, Arbeitgeberseite und gegnerischer Anwalt Schwedisch. Deutsch nur interne Arbeitssprache des bearbeitenden Anwalts.",
        "updated_at": datetime.datetime.now(),
    }

    for table in ["lang_case_language_settings", "case_language_profiles"]:
        cols = columns(con, table)
        if not cols:
            continue

        key_col = "case_template_key" if "case_template_key" in cols else "case_key" if "case_key" in cols else None
        if not key_col:
            continue

        if update_existing(con, table, key_col, CASE_KEY, case_values):
            changed.append(table)

    participant_rows = [
        {
            "participant_profile_key": "SE_ARBEITSRECHT_GERICHT",
            "participant_role": "gericht",
            "participant_label": "Schwedisches Gericht",
            "communication_language_code": "sv",
            "document_language_code": "sv",
            "actual_or_spoken_language_code": "sv",
            "internal_work_language_code": "de",
            "created_after_mandate_acceptance": False,
            "accepted_client_required": False,
            "translation_required": True,
            "notes": "Gerichtliche Kommunikation und Verfahrenssprache Schwedisch; interne Bearbeitung Deutsch.",
            "updated_at": datetime.datetime.now(),
        },
        {
            "participant_profile_key": "SE_ARBEITSRECHT_ARBEITGEBER",
            "participant_role": "gegenseite",
            "participant_label": "Kommunaler Arbeitgeber in Schweden",
            "communication_language_code": "sv",
            "document_language_code": "sv",
            "actual_or_spoken_language_code": "sv",
            "internal_work_language_code": "de",
            "created_after_mandate_acceptance": False,
            "accepted_client_required": False,
            "translation_required": True,
            "notes": "Arbeitgeberseite im schwedischen Arbeitsrechtsstreit grundsätzlich Schwedisch.",
            "updated_at": datetime.datetime.now(),
        },
        {
            "participant_profile_key": "SE_ARBEITSRECHT_GEGNER_ANWALT",
            "participant_role": "gegnerischer_anwalt",
            "participant_label": "Gegnerischer Anwalt Schweden",
            "communication_language_code": "sv",
            "document_language_code": "sv",
            "actual_or_spoken_language_code": "sv",
            "internal_work_language_code": "de",
            "created_after_mandate_acceptance": False,
            "accepted_client_required": False,
            "translation_required": True,
            "notes": "Korrektur: kein Grundsatz Englisch. Gegnerischer Anwalt wird für diesen Fall grundsätzlich Schwedisch geführt.",
            "updated_at": datetime.datetime.now(),
        },
        {
            "participant_profile_key": "SE_ARBEITSRECHT_MANDANT_NACH_ANNAHME",
            "participant_role": "mandant",
            "participant_label": "Mandant nach Annahme",
            "communication_language_code": "sv",
            "document_language_code": "sv",
            "actual_or_spoken_language_code": "sv",
            "internal_work_language_code": "de",
            "created_after_mandate_acceptance": True,
            "accepted_client_required": True,
            "translation_required": True,
            "notes": "Mandantenbezogene Spracheinstellung erst nach Mandatsannahme. Für diesen Fall grundsätzlich Schwedisch; interne Bearbeitung Deutsch.",
            "updated_at": datetime.datetime.now(),
        },
        {
            "participant_profile_key": "SE_ARBEITSRECHT_INTERN",
            "participant_role": "intern",
            "participant_label": "Interne anwaltliche Bearbeitung",
            "communication_language_code": "de",
            "document_language_code": "de",
            "actual_or_spoken_language_code": "de",
            "internal_work_language_code": "de",
            "created_after_mandate_acceptance": False,
            "accepted_client_required": False,
            "translation_required": False,
            "notes": "Deutsch ist nur interne Arbeitssprache des bearbeitenden Anwalts.",
            "updated_at": datetime.datetime.now(),
        },
    ]

    table = "lang_participant_language_settings"
    cols = columns(con, table)
    if cols:
        key_col = "participant_profile_key" if "participant_profile_key" in cols else None
        if key_col:
            for row in participant_rows:
                values = dict(row)
                values["case_template_key"] = CASE_KEY
                values["case_key"] = CASE_KEY
                update_existing(con, table, key_col, row["participant_profile_key"], values)
            changed.append(table)

    table = "lang_intake_language_rules"
    cols = columns(con, table)
    if cols:
        rule_values = {
            "rule_key": "SE_ARBEITSRECHT_STANDARD",
            "case_template_key": CASE_KEY,
            "case_key": CASE_KEY,
            "expected_document_language_code": "sv",
            "default_document_language_code": "sv",
            "detected_actual_language_code": "",
            "target_work_language_code": "de",
            "internal_work_language_code": "de",
            "procedural_language_code": "sv",
            "communication_language_code": "sv",
            "translation_required_if_mismatch": True,
            "translation_required": True,
            "notes": "Schwedisch ist erwartete Dokumenten-, Amts- und Prozesssprache. Deutsch ist nur interne Arbeitssprache.",
            "updated_at": datetime.datetime.now(),
        }
        key_col = "rule_key" if "rule_key" in cols else None
        if key_col:
            update_existing(con, table, key_col, "SE_ARBEITSRECHT_STANDARD", rule_values)
            changed.append(table)

    return sorted(set(changed))

def active_files(path):
    if not path.exists():
        return []
    return sorted([
        p for p in path.rglob("*")
        if p.is_file()
        and p.name not in IGNORE
    ])

def extract_intake_id(path):
    stem = path.stem
    for suffix in [
        "_entscheidungskarte",
        "_sicherheitskarte",
        "_sprachkarte",
        "_sicherheitsbericht",
        "_sprachbericht",
    ]:
        if stem.endswith(suffix):
            return stem[: -len(suffix)]

    if "__" in stem:
        return stem.split("__", 1)[0]

    parts = stem.split("_")
    if len(parts) >= 2 and parts[0].isdigit():
        return parts[0] + "_" + parts[1]

    return stem

def build_corrected_decision_draft():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)

    groups = {}

    for key in ["quarantaene", "signatur", "geprueft", "vorzimmer", "sprachpruefung", "anwalt"]:
        for file in active_files(DIRS[key]):
            intake = extract_intake_id(file)
            groups.setdefault(intake, []).append((key, file))

    rows = []
    analysis = []

    priority = {
        "quarantaene": 10,
        "signatur": 20,
        "sprachpruefung": 30,
        "geprueft": 40,
        "vorzimmer": 50,
        "anwalt": 60,
    }

    for nr, intake in enumerate(sorted(groups.keys()), start=1):
        items = sorted(groups[intake], key=lambda x: (priority.get(x[0], 99), str(x[1])))

        areas = sorted(set(k for k, _ in items))
        files = [p for _, p in items]

        actual_docs = [p for k, p in items if k == "geprueft" and p.suffix.lower() != ".json"]
        signatur = [p for k, p in items if k == "signatur"]
        quar = [p for k, p in items if k == "quarantaene"]

        if quar:
            action = "QUARANTAENE"
            source = quar[0]
            reason = "Korrigierter Fallkontext: technische Quarantäne bleibt vorrangig; nicht öffnen."
        elif signatur:
            action = "SIGNATURPRUEFUNG"
            source = signatur[0]
            reason = "Korrigierter Fallkontext: Signaturprüfung bleibt vorrangig; Schwedisch ist fachlich erwartete Sprache."
        elif actual_docs:
            action = "ANWALTVORLAGE"
            source = actual_docs[0]
            reason = "Korrigierter Fallkontext: schwedischer Arbeitsrechtsstreit. Schwedisch ist Amts-, Prozess-, Beteiligten- und Dokumentensprache. Deutsch ist nur interne Arbeitssprache; ggf. interne deutsche Arbeitsübersetzung oder Zusammenfassung."
        else:
            action = "ZURUECKSTELLEN"
            source = files[0]
            reason = "Korrigierter Fallkontext: keine eigentliche Arbeitsdatei gefunden; organisatorisch zurückstellen."

        rows.append({
            "decision_id": f"SE_ARBEITSRECHT_KORRIGIERT_{nr:03d}_{intake}",
            "intake_id": intake,
            "source_path": str(source),
            "aktion": action,
            "begruendung": reason,
            "frist": "",
            "verantwortlich": "Vorzimmer",
        })

        analysis.append({
            "intake_id": intake,
            "areas_seen": areas,
            "files_seen": [str(p) for p in files],
            "chosen_action": action,
            "chosen_source": str(source),
        })

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_csv = CLEAN_DIR / f"SE_ARBEITSRECHT_KORRIGIERTER_ENTWURF_{ts}.csv"
    out_txt = PROPOSAL_DIR / f"SE_ARBEITSRECHT_KORRIGIERTER_ENTSCHEIDUNGSVORSCHLAG_{ts}.txt"
    out_json = PROPOSAL_DIR / f"SE_ARBEITSRECHT_KORRIGIERTER_ENTSCHEIDUNGSVORSCHLAG_{ts}.json"

    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    data = {
        "time": now(),
        "case": "Schwedischer Arbeitsrechtsstreit Arbeitnehmer gegen kommunalen Arbeitgeber",
        "rule": "Schwedisch ist Amts-, Prozess-, Beteiligten- und Dokumentensprache. Deutsch ist nur interne Arbeitssprache des bearbeitenden Anwalts.",
        "execution": "Nicht ausgeführt. Nur bereinigter Entwurf.",
        "csv": str(out_csv),
        "rows": rows,
        "analysis": analysis,
    }

    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    with open(out_txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("SE ARBEITSRECHT KORRIGIERTER ENTSCHEIDUNGSVORSCHLAG\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + now() + "\n")
        f.write("Fall: Arbeitnehmer gegen kommunalen Arbeitgeber in Schweden\n")
        f.write("Amtssprache: Schwedisch\n")
        f.write("Prozesssprache: Schwedisch\n")
        f.write("Beteiligtenkommunikation: grundsätzlich Schwedisch\n")
        f.write("Interne Arbeitssprache Anwalt: Deutsch\n")
        f.write("Ausführung: nein, nur Entwurf\n\n")

        f.write("ENTSCHEIDUNGEN\n")
        f.write("-" * 80 + "\n")
        for i, row in enumerate(rows, start=1):
            f.write(str(i) + ". " + row["aktion"] + "\n")
            f.write("Intake-ID: " + row["intake_id"] + "\n")
            f.write("Quelle: " + row["source_path"] + "\n")
            f.write("Begründung: " + row["begruendung"] + "\n\n")

    return out_csv, out_txt, out_json, rows, analysis

def verify_context(con):
    result = {}

    if table_exists(con, "lang_case_language_settings"):
        cols = columns(con, "lang_case_language_settings")
        key_col = "case_template_key" if "case_template_key" in cols else "case_key" if "case_key" in cols else None
        if key_col:
            row = con.execute(
                "SELECT * FROM lang_case_language_settings WHERE " + q(key_col) + " = ?",
                [CASE_KEY]
            ).fetchone()
            result["lang_case_language_settings_present"] = row is not None

    if table_exists(con, "lang_participant_language_settings"):
        result["participant_rows"] = con.execute(
            """
            SELECT COUNT(*)
            FROM lang_participant_language_settings
            WHERE participant_profile_key LIKE 'SE_ARBEITSRECHT_%'
            """
        ).fetchone()[0]

    return result

def main():
    con = duckdb.connect(str(DB))
    try:
        changed = correct_language_context(con)
        verification = verify_context(con)
    finally:
        con.close()

    out_csv, out_txt, out_json, rows, analysis = build_corrected_decision_draft()

    action_counts = {}
    for row in rows:
        action_counts[row["aktion"]] = action_counts.get(row["aktion"], 0) + 1

    print("")
    print("SCHWEDEN_ARBEITSRECHT_SPRACHKONTEXT_KORREKTUR_V1 FERTIG")
    print("Geänderte Tabellen:", ", ".join(changed) if changed else "keine")
    print("Prüfung:", json.dumps(verification, ensure_ascii=False))
    print("Korrigierte Vorschläge:", len(rows))
    print("Aktionen:", json.dumps(action_counts, ensure_ascii=False))
    print("CSV:", out_csv)
    print("TXT:", out_txt)
    print("JSON:", out_json)
    print("")
    print("WICHTIG: Der Entwurf wurde nicht ausgeführt.")

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
