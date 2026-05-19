# -*- coding: utf-8 -*-
import sys
import csv
import json
import shutil
import hashlib
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
ROH = POST / "00_Roh_Eingang"
LOG = ROOT / "Windows_App" / "Logs"
OUT = LOG / "DB_Dateien_Auswahl_Posteingang"

SAFE_EXT = {
    ".txt",
    ".pdf",
    ".docx",
    ".rtf",
    ".eml",
    ".msg",
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
}

BLOCK_EXT = {
    ".exe", ".dll", ".com", ".scr", ".bat", ".cmd", ".ps1", ".vbs", ".js",
    ".jse", ".wsf", ".msi", ".msp", ".hta", ".jar", ".lnk", ".reg", ".zip",
    ".7z", ".rar"
}

LANG_HINTS = {
    "sv": ["sv", "schwed", "swedish", "sverige", "arbets", "tingsr", "skol", "förvalt", "domstol"],
    "de": ["de", "deutsch", "german", "klage", "schriftsatz", "gericht", "jobcenter"],
    "en": ["en", "english", "opposing", "counsel", "lawyer", "court"],
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def clean_name(name):
    return "".join(c if c.isalnum() or c in " ._-()" else "_" for c in name)

def is_inside(child, parent):
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False

def read_existing_documents():
    con = duckdb.connect(str(DB), read_only=True)
    try:
        tables = [x[0] for x in con.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchall()]

        if "documents" not in tables:
            raise RuntimeError("Tabelle documents fehlt in Legal_Brain.duckdb.")

        cols = [x[1] for x in con.execute('PRAGMA table_info("documents")').fetchall()]
        wanted = []
        for c in ["id", "filename", "path", "status", "priority", "timestamp", "analysis_result", "legal_deadline"]:
            if c in cols:
                wanted.append(c)

        sql = "SELECT " + ", ".join(['"' + c + '"' for c in wanted]) + ' FROM "documents"'
        rows = con.execute(sql).fetchall()

        result = []
        for row in rows:
            d = dict(zip(wanted, row))
            result.append(d)

        return result
    finally:
        con.close()

def infer_language_hint(path, filename):
    text = (str(path) + " " + str(filename)).lower()
    for code, hints in LANG_HINTS.items():
        for h in hints:
            if h in text:
                return code
    return "unknown"

def score_candidate(item):
    filename = str(item.get("filename") or "")
    p = Path(str(item.get("path") or ""))
    ext = p.suffix.lower()

    score = 0

    if ext == ".txt":
        score += 30
    elif ext == ".pdf":
        score += 25
    elif ext == ".docx":
        score += 20
    elif ext == ".eml":
        score += 18
    else:
        score += 10

    lang = infer_language_hint(p, filename)
    if lang == "sv":
        score += 40
    elif lang == "de":
        score += 30
    elif lang == "en":
        score += 20

    status = str(item.get("status") or "").lower()
    if "ok" in status or "analys" in status or "processed" in status:
        score += 10

    try:
        size = p.stat().st_size
        if 0 < size <= 20 * 1024 * 1024:
            score += 10
        elif size > 20 * 1024 * 1024:
            score -= 20
    except Exception:
        score -= 50

    return score

def usable_candidate(item):
    filename = str(item.get("filename") or "")
    raw_path = str(item.get("path") or "").strip()

    if not raw_path:
        return False, "Kein Pfad in Datenbank."

    path = Path(raw_path)

    if not path.exists():
        return False, "Datei existiert nicht mehr."

    if not path.is_file():
        return False, "Pfad ist keine Datei."

    if is_inside(path, POST):
        return False, "Datei liegt bereits im Posteingang."

    if "AnythingLLM_Storage" in str(path):
        return False, "AnythingLLM-Ablage wird nicht als Testeingang verwendet."

    ext = path.suffix.lower()

    if ext in BLOCK_EXT:
        return False, "Aktive, gepackte oder gefährliche Endung wird nicht zurückgelegt."

    if ext not in SAFE_EXT:
        return False, "Dateityp nicht in der zulässigen Testliste."

    try:
        size = path.stat().st_size
    except Exception:
        return False, "Dateigröße nicht lesbar."

    if size <= 0:
        return False, "Leere Datei."

    if size > 20 * 1024 * 1024:
        return False, "Datei für Testlauf zu groß."

    return True, "geeignet"

def select_candidates(rows, max_count=6):
    candidates = []

    for item in rows:
        ok, reason = usable_candidate(item)
        if not ok:
            item["_skip_reason"] = reason
            continue

        p = Path(str(item.get("path")))
        item["_path_obj"] = p
        item["_extension"] = p.suffix.lower()
        item["_language_hint"] = infer_language_hint(p, item.get("filename") or p.name)
        item["_score"] = score_candidate(item)
        candidates.append(item)

    candidates.sort(key=lambda x: (-x["_score"], str(x.get("path"))))

    selected = []
    used_ext = set()
    used_lang = set()

    for lang in ["sv", "de", "en", "unknown"]:
        for item in candidates:
            if item in selected:
                continue
            if item["_language_hint"] == lang:
                selected.append(item)
                used_ext.add(item["_extension"])
                used_lang.add(item["_language_hint"])
                break
            if len(selected) >= max_count:
                break

    for item in candidates:
        if len(selected) >= max_count:
            break
        if item in selected:
            continue
        if item["_extension"] not in used_ext:
            selected.append(item)
            used_ext.add(item["_extension"])
            used_lang.add(item["_language_hint"])

    for item in candidates:
        if len(selected) >= max_count:
            break
        if item not in selected:
            selected.append(item)

    return selected, candidates

def copy_selected(selected):
    ROH.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    manifest = OUT / f"DB_DATEIEN_AUSWAHL_POSTEINGANG_{ts}.csv"
    report_json = OUT / f"DB_DATEIEN_AUSWAHL_POSTEINGANG_{ts}.json"
    report_txt = OUT / f"DB_DATEIEN_AUSWAHL_POSTEINGANG_{ts}.txt"

    copied = []

    for index, item in enumerate(selected, start=1):
        src = item["_path_obj"]
        digest = sha256_file(src)
        name = clean_name(src.name)
        dst = ROH / f"DBTEST_{ts}_{index:02d}_{digest[:12]}__{name}"

        if dst.exists():
            dst = ROH / f"DBTEST_{ts}_{index:02d}_{digest[:12]}__{datetime.datetime.now().strftime('%H%M%S')}__{name}"

        shutil.copy2(str(src), str(dst))

        copied.append({
            "index": index,
            "database_id": str(item.get("id", "")),
            "filename": str(item.get("filename", src.name)),
            "source_path": str(src),
            "target_path": str(dst),
            "sha256": digest,
            "size_bytes": dst.stat().st_size,
            "extension": item["_extension"],
            "language_hint": item["_language_hint"],
            "score": item["_score"],
            "status": str(item.get("status", "")),
        })

    with open(manifest, "w", encoding="utf-8", newline="") as f:
        fields = [
            "index",
            "database_id",
            "filename",
            "source_path",
            "target_path",
            "sha256",
            "size_bytes",
            "extension",
            "language_hint",
            "score",
            "status",
        ]
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for row in copied:
            writer.writerow(row)

    report_json.write_text(
        json.dumps(
            {
                "time": now(),
                "database": str(DB),
                "target_raw_inbox": str(ROH),
                "copied_count": len(copied),
                "copied": copied,
                "principle": "Es wurden nur Kopien in den Roh-Eingang gelegt. Die Ursprungsdateien wurden nicht verändert."
            },
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8",
        newline="\n"
    )

    with open(report_txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("DB-DATEIEN AUSWAHL FÜR POSTEINGANG TESTLAUF V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + now() + "\n")
        f.write("Datenbank: " + str(DB) + "\n")
        f.write("Ziel: " + str(ROH) + "\n")
        f.write("Kopien: " + str(len(copied)) + "\n\n")

        for row in copied:
            f.write(str(row["index"]) + ". " + row["filename"] + "\n")
            f.write("Quelle: " + row["source_path"] + "\n")
            f.write("Ziel:   " + row["target_path"] + "\n")
            f.write("Sprachehinweis: " + row["language_hint"] + "\n")
            f.write("SHA256: " + row["sha256"] + "\n\n")

    return copied, manifest, report_txt, report_json

def main():
    rows = read_existing_documents()
    selected, candidates = select_candidates(rows, max_count=6)

    if not selected:
        raise RuntimeError("Keine geeigneten Dateien aus der Tabelle documents gefunden.")

    copied, manifest, report_txt, report_json = copy_selected(selected)

    print("")
    print("POSTEINGANG_DB_DATEIEN_AUSWAHL_TESTLAUF_V1 FERTIG")
    print("Datenbankeinträge gelesen:", len(rows))
    print("Geeignete Kandidaten:", len(candidates))
    print("In Roh-Eingang kopiert:", len(copied))
    print("Manifest:", manifest)
    print("TXT:", report_txt)
    print("JSON:", report_json)
    print("")
    print("Kopierte Dateien:")
    for row in copied:
        print(row["target_path"])

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
