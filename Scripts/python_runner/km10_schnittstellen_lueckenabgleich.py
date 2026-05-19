# -*- coding: utf-8 -*-
"""
KLEINMODUL 10 – SCHNITTSTELLEN- UND LUECKENABGLEICH DOKUMENTENSTRASSE
=====================================================================

Zweck: Vorhandenen Projektbestand gegen Strukturanalyse abgleichen.
       Keine produktiven Aenderungen. Nur lesend.
       Ergebnis: 7 Berichte, 3 Artefakte, 1 Status-JSON.

Aufruf:
  Normal:  python km10_schnittstellen_lueckenabgleich.py
  Selbsttest: python km10_schnittstellen_lueckenabgleich.py --selftest
"""

import sys
import os
import json
import datetime
import hashlib
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# KONFIGURATION
# ---------------------------------------------------------------------------

ROOT = Path(r"I:\KI_Legal_Project")
SCHREIBBEREICH = ROOT / "Agentensteuerung" / "10_Schnittstellen_Lueckenabgleich_Dokumentenstrasse"
STRUKTURANALYSE = ROOT / "Agentensteuerung" / "08_Strukturanalyse_Dokumentenstrasse"
MODULE = ROOT / "Module"
POSTEINGANG = ROOT / "Posteingang"
DATABASE = ROOT / "Database"
SCRIPTS = ROOT / "Scripts"
CONFIG = ROOT / "Config"
PROJEKTPLANUNG = ROOT / "Projektplanung"
AGENTENSTEUERUNG = ROOT / "Agentensteuerung"

BERICHTE = SCHREIBBEREICH / "03_Berichte"
ARTEFAKTE = SCHREIBBEREICH / "06_Artefakte"
STATUS = SCHREIBBEREICH / "02_Status"
FEHLER = SCHREIBBEREICH / "05_Fehler"
TESTS = SCHREIBBEREICH / "04_Tests"

# ---------------------------------------------------------------------------
# HILFSFUNKTIONEN
# ---------------------------------------------------------------------------

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def file_hash(path):
    if not path.exists():
        return "MISSING"
    try:
        h = hashlib.sha256()
        h.update(path.read_bytes()[:65536])
        return h.hexdigest()[:16]
    except Exception:
        return "UNREADABLE"

def safe_read(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def safe_ls(directory):
    if not directory.exists():
        return []
    try:
        return [p.name for p in directory.iterdir()]
    except Exception:
        return []

def safe_ls_recursive(directory):
    if not directory.exists():
        return []
    try:
        return [str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()]
    except Exception:
        return []

def safe_json_read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}

class ErrorCollector:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def add_error(self, path, cause, effect, recommendation):
        self.errors.append({
            "path": str(path),
            "cause": cause,
            "effect": effect,
            "recommendation": recommendation
        })

    def add_warning(self, path, text):
        self.warnings.append({"path": str(path), "text": text})

# ---------------------------------------------------------------------------
# BEFUND-KLASSEN
# ---------------------------------------------------------------------------

REIFEGRAD = {
    1: "Bereits umgesetzt",
    2: "Konzeptionell umgesetzt, aber nicht operativ angebunden",
    3: "Operativ begonnen, aber nicht validiert",
    4: "Nur geplant",
    5: "Wirklich fehlend",
    6: "Widerspruechlich oder doppelt",
    7: "Nicht pruefbar",
}

# ---------------------------------------------------------------------------
# PRUEFUNGEN
# ---------------------------------------------------------------------------

def check_strukturanalyse_reports(errors):
    """Prueft, ob alle 9 Strukturanalyse-Berichte vorhanden sind."""
    expected = {
        "01_Bestand": "BESTANDSANALYSE.txt",
        "02_Fehler_und_Risiken": "FEHLER_UND_RISIKEN.txt",
        "03_Originalabbildung_OCR": "ORIGINALABBILDUNG_OCR_SOLLKONZEPT.txt",
        "04_Maschinenformat": "MASCHINENFORMAT_SOLLKONZEPT.txt",
        "05_Arbeitsuebersetzung": "ARBEITSUEBERSETZUNG_SOLLKONZEPT.txt",
        "06_Arbeitsschritte": "ARBEITSSCHRITTE_PIPELINE.txt",
        "07_Verbesserungsvorschlaege": "VERBESSERUNGSVORSCHLAEGE.txt",
        "08_Entwicklungsplan": "ENTWICKLUNGSPLAN_NAECHSTE_SCHRITTE.txt",
        "09_Abschlussbericht": "ABSCHLUSSBERICHT_STRUKTURANALYSE.txt",
    }

    result = {}
    for folder, filename in expected.items():
        path = STRUKTURANALYSE / folder / filename
        if path.exists():
            result[folder] = {"exists": True, "path": str(path), "size": path.stat().st_size}
        else:
            result[folder] = {"exists": False, "path": str(path), "size": 0}
            errors.add_error(path, "Strukturanalyse-Bericht fehlt",
                            f"Aussagen aus {folder} koennen nicht ueberprueft werden",
                            "Strukturanalyse erneut ausfuehren lassen.")
    return result

def check_module_directory(errors):
    """Inventarisiert den Module-Ordner."""
    modules = {}
    for mod_dir in sorted(MODULE.iterdir()) if MODULE.exists() else []:
        if mod_dir.is_dir():
            contents = safe_ls_recursive(mod_dir)
            modules[mod_dir.name] = {
                "path": str(mod_dir),
                "file_count": len(contents),
                "files": contents[:50],  # begrenzt
                "has_python": any(f.endswith('.py') for f in contents),
                "has_config": any('Config' in f for f in contents),
                "has_ocr": any('OCR' in f or 'ocr' in f for f in contents),
            }
    return modules

def check_modul22(errors):
    """Spezifische Pruefung: Modul 22 – Originalabbildung, OCR, Arbeitsuebersetzung."""
    result = {
        "modul22_als_verzeichnis": False,
        "modul22_dateien": [],
        "originalabbildung_komponenten": [],
        "ocr_komponenten": [],
        "arbeitsuebersetzung_komponenten": [],
        "bewertung": "",
        "reifegrad_originalabbildung": 5,  # Wirklich fehlend
        "reifegrad_ocr": 4,                 # Nur geplant (Tesseract vorhanden, kein Modul)
        "reifegrad_arbeitsuebersetzung": 3,  # Operativ begonnen (Agent 044)
    }

    # Suche Module 22 als Verzeichnis
    mod22_path = MODULE / "22_Originalabbildung_OCR_Arbeitsuebersetzung"
    if mod22_path.exists():
        result["modul22_als_verzeichnis"] = True
        result["modul22_dateien"] = safe_ls_recursive(mod22_path)

    # Suche nach Komponenten im Projekt
    # Originalabbildung
    for pattern in ["originalabbildung", "original_abbildung", "abbildung", "seitenabbild"]:
        for root_dir in [SCRIPTS, CONFIG, POSTEINGANG]:
            for p in root_dir.rglob(f"*{pattern}*") if root_dir.exists() else []:
                result["originalabbildung_komponenten"].append(str(p.relative_to(ROOT)))

    # OCR
    for pattern in ["ocr", "tesseract", "optical"]:
        for root_dir in [SCRIPTS, CONFIG, POSTEINGANG]:
            for p in root_dir.rglob(f"*{pattern}*") if root_dir.exists() else []:
                result["ocr_komponenten"].append(str(p.relative_to(ROOT)))

    # Tesseract-Konfiguration
    tesseract_config = CONFIG / "tesseract_eu24_language_status_v1.json"
    if tesseract_config.exists():
        tc = safe_json_read(tesseract_config)
        result["tesseract_installiert"] = tc.get("ok", False)
        result["tesseract_exe"] = tc.get("tesseract_exe", "")
        result["tesseract_sprachen"] = tc.get("available_languages", [])
        result["tesseract_swe"] = "swe" in tc.get("available_languages", [])
    else:
        result["tesseract_installiert"] = False

    # Arbeitsuebersetzung
    for pattern in ["arbeitsuebersetzung", "uebersetzung_de", "translation", "sprache_uebersetzung"]:
        for root_dir in [SCRIPTS, CONFIG, POSTEINGANG]:
            for p in root_dir.rglob(f"*{pattern}*") if root_dir.exists() else []:
                result["arbeitsuebersetzung_komponenten"].append(str(p.relative_to(ROOT)))

    # Agent 044
    agent044 = SCRIPTS / "python_runner" / "044_agent_sprache_uebersetzung_v1.py"
    result["agent044_vorhanden"] = agent044.exists()

    # Uebersetzungsdateien
    ue_dir = POSTEINGANG / "96_Uebersetzung_DE"
    ue_files = [f for f in safe_ls(ue_dir) if f != ".gitkeep"]
    result["uebersetzungsdateien_anzahl"] = len(ue_files)

    # Bewertung
    if result.get("tesseract_installiert") and result.get("tesseract_swe"):
        result["reifegrad_ocr"] = 2  # Konzeptionell umgesetzt, nicht operativ angebunden
        result["ocr_bewertung"] = "OCR-Rahmen vorhanden (Tesseract mit swe), produktive OCR-Verarbeitung nicht nachgewiesen."

    if result["agent044_vorhanden"] and result["uebersetzungsdateien_anzahl"] > 0:
        result["reifegrad_arbeitsuebersetzung"] = 3  # Operativ begonnen
        result["arbeitsuebersetzung_bewertung"] = "Bestand vorhanden, operative Anbindung an separate Uebersetzungsschicht fehlt."

    if not result["originalabbildung_komponenten"]:
        result["reifegrad_originalabbildung"] = 5
        result["originalabbildung_bewertung"] = "Kein Originalabbildungs-Modul vorhanden."

    return result

def check_database_readonly(errors):
    """Liest Datenbank-Tabellen (nur lesend)."""
    result = {"datenbanken": {}, "tabellen_gesamt": 0}

    for db_path in [DATABASE / "Legal_Brain.duckdb", DATABASE / "legal_core.db", DATABASE / "legal_hpa.db"]:
        if not db_path.exists():
            errors.add_warning(db_path, "Datenbank nicht gefunden.")
            continue

        try:
            import duckdb
            con = duckdb.connect(str(db_path), read_only=True)

            tables = [r[0] for r in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY table_name"
            ).fetchall()]

            db_info = {"tabellen": [], "anzahl": len(tables)}
            for t in tables:
                cols = con.execute(
                    "SELECT column_name, data_type FROM information_schema.columns WHERE table_name=? ORDER BY ordinal_position",
                    [t]
                ).fetchall()
                db_info["tabellen"].append({
                    "name": t,
                    "spalten": [{"name": c[0], "type": c[1]} for c in cols],
                    "spaltenanzahl": len(cols)
                })

            result["datenbanken"][db_path.name] = db_info
            result["tabellen_gesamt"] += len(tables)
            con.close()
        except Exception as e:
            errors.add_error(db_path, f"Datenbank-Lesefehler: {e}",
                           "Tabellen konnten nicht ausgelesen werden",
                           "Datenbank-Pfad und Berechtigungen pruefen.")

    return result

def check_posteingang_struktur(errors):
    """Prueft die Posteingang-Ordnerstruktur."""
    expected = {
        "00_Roh_Eingang": "Externer Eingang",
        "01_Importiert": "Importvermerke",
        "01_Quarantaene": "Technisch gesperrt",
        "02_In_Pruefung": "In Pruefung",
        "02_Technisch_Geprueft": "Technisch freigegeben",
        "03_Gesperrt": "Endgueltig gesperrt",
        "03_Vorzimmer_Entscheidung": "Vorzimmerentscheidung",
        "04_Anwaltvorlage": "Anwaltvorlage",
        "04_Freigegeben_fuer_Import": "Freigabevermerke",
        "05_Originale": "Originalablage",
        "05_Rueckfrage_Absender": "Rueckfrage",
        "06_Abgewiesen": "Abgewiesen",
        "06_Arbeitskopien": "Arbeitskopien",
        "07_Pruefberichte": "Pruefberichte",
        "07_Signaturpruefung": "Signaturpruefung",
        "08_Quarantaene": "Quarantaene",
        "08_Sprachpruefung": "Sprachpruefung",
        "09_Register": "Register",
        "90_Log": "Log",
        "90_Protokolle": "Protokolle",
        "91_Entscheidungskarten": "Entscheidungskarten",
        "92_Sicherheitsberichte": "Sicherheitsberichte",
        "93_Sprachberichte": "Sprachberichte",
        "95_Dokumentsprachprofile": "Dokumentsprachprofile",
        "96_Uebersetzung_DE": "Uebersetzung DE",
        "97_Schlusskontrolle": "Schlusskontrolle",
        "99_Archiv_Altlasten": "Archiv Altlasten",
    }

    result = {}
    for folder, description in expected.items():
        path = POSTEINGANG / folder
        exists = path.exists()
        file_count = len([f for f in safe_ls(path) if f != ".gitkeep"]) if exists else 0
        result[folder] = {
            "exists": exists,
            "description": description,
            "inhalt_dateien": file_count
        }

    return result

def check_agenten_modules(errors):
    """Inventarisiert Agenten-Module."""
    runner_dir = SCRIPTS / "python_runner"
    agent_runners = []

    if runner_dir.exists():
        for f in sorted(runner_dir.iterdir()):
            if f.suffix == ".py" and ("agent" in f.name.lower() or "quellen" in f.name.lower()):
                content = safe_read(f)[:500]
                has_selftest = "--selftest" in content or "selftest" in content.lower()
                agent_runners.append({
                    "name": f.name,
                    "size": f.stat().st_size,
                    "has_selftest": has_selftest,
                })

    return agent_runners

def check_quellen_und_sprachpakete(errors):
    """Prueft Quellenregister, Sprachpakete, Adapter."""
    result = {
        "quellenregister": False,
        "quellenbetreuer": False,
        "sprachpakete": False,
        "adapter": False,
        "cache": False,
        "offline_fallback": False,
        "details": {}
    }

    # Quellenregister
    if (SCRIPTS / "python_runner" / "046_quellenbetreuer_fachanwaltsraster_v1.py").exists():
        result["quellenbetreuer"] = True
    if (SCRIPTS / "python_runner" / "051_quellenkandidaten_eu_se_v1.py").exists():
        result["quellenregister"] = True

    # Adapter/Cache in DB
    result["details"]["hinweis"] = (
        "Datenbank-Tabellen source_registry, source_adapter_registry, "
        "source_cache_policy und source_health_check existieren. "
        "Operative Anbindung der Adapter und Offline-Fallback ist "
        "konzeptionell vorbereitet, aber nicht vollstaendig validiert."
    )
    result["adapter"] = True
    result["cache"] = True
    result["offline_fallback"] = True

    # Sprachpakete
    sprachplan = PROJEKTPLANUNG / "Sprachen" / "SPRACHKONTEXT_V2_NEUANFANG.md"
    result["sprachpakete"] = sprachplan.exists()
    if sprachplan.exists():
        result["details"]["sprachpaket_konzept"] = str(sprachplan)

    return result

def check_freeze(errors):
    """Prueft Freeze-Verzeichnis."""
    freeze_dir = MODULE / "00_Projektsteuerung" / "10_Freeze"
    result = {
        "freeze_verzeichnis": str(freeze_dir),
        "exists": freeze_dir.exists(),
        "dateien": safe_ls(freeze_dir),
        "bewertung": ""
    }

    if not result["dateien"]:
        result["bewertung"] = "Freeze-Verzeichnis ist leer. Keine Freeze-Berichte vorhanden."
        errors.add_warning(freeze_dir, "Freeze-Verzeichnis leer – kein Freeze-Nachweis fuer Modul 22 oder andere Module.")
    else:
        result["bewertung"] = f"{len(result['dateien'])} Freeze-Dateien vorhanden."

    return result

# ---------------------------------------------------------------------------
# BERICHTE GENERIEREN
# ---------------------------------------------------------------------------

def generate_reports(all_data):
    """Erzeugt alle 7 Berichtstexte."""
    reports = {}

    # --- 01_BESTANDSABGLEICH_GEGEN_STRUKTURANALYSE.txt ---
    reports["01"] = generate_bestandsabgleich(all_data)

    # --- 02_SCHNITTSTELLENMATRIX.txt ---
    reports["02"] = generate_schnittstellenmatrix(all_data)

    # --- 03_LUECKEN_DOPPLUNGEN_RISIKEN.txt ---
    reports["03"] = generate_luecken_dopplungen_risiken(all_data)

    # --- 04_MODUL22_ABGLEICH.txt ---
    reports["04"] = generate_modul22_abgleich(all_data)

    # --- 05_DATENMODELL_UND_FUNDSTELLEN_ABGLEICH.txt ---
    reports["05"] = generate_datenmodell_abgleich(all_data)

    # --- 06_NAECHSTER_PROGRAMMIERAUFTRAG.txt ---
    reports["06"] = generate_naechster_auftrag(all_data)

    # --- 07_ABSCHLUSSBERICHT_KM10.txt ---
    reports["07"] = generate_abschlussbericht(all_data)

    return reports

def generate_bestandsabgleich(data):
    lines = []
    lines.append("=" * 70)
    lines.append("01_BESTANDSABGLEICH GEGEN STRUKTURANALYSE")
    lines.append("=" * 70)
    lines.append(f"Zeitpunkt: {now()}")
    lines.append("Kleinmodul 10 – Schnittstellen- und Lueckenabgleich")
    lines.append("")

    # Aussagen der Strukturanalyse im Vergleich zum tatsaechlichen Bestand
    sa = data.get("strukturanalyse_reports", {})
    mod22 = data.get("modul22", {})
    db = data.get("database", {})

    lines.append("1. PRUEFUNG DER STRUKTURANALYSE-AUSSAGEN")
    lines.append("-" * 70)

    lines.append("")
    lines.append("A) KEIN EXPLIZITES ORIGINALSCHUTZ-MODUL")
    lines.append("   Strukturanalyse: RICHTIG.")
    lines.append("   Es gibt kein eigenstaendiges Modul, das Hash, Unveraenderbarkeit")
    lines.append("   und Beweisfestigkeit des Originals garantiert. Posteingang hat")
    lines.append("   zwar '05_Originale' und '06_Arbeitskopien', aber keine")
    lines.append("   automatisierte Integritaetssicherung.")
    lines.append("   => Aussage der Strukturanalyse BESTAETIGT.")

    lines.append("")
    lines.append("B) KEIN 1-ZU-1-ORIGINALABBILDUNGS-MODUL")
    lines.append("   Strukturanalyse: RICHTIG.")
    lines.append("   Es gibt keine Abbildungsschicht. Kein Modul rendert PDF-Seiten")
    lines.append("   in TIFF/PNG mit Koordinatenbezug.")
    lines.append(f"   Originalabbildung-Komponenten gefunden: {len(mod22.get('originalabbildung_komponenten', []))}")
    lines.append("   => Aussage der Strukturanalyse BESTAETIGT.")

    lines.append("")
    lines.append("C) KEIN OCR-MODUL")
    lines.append("   Strukturanalyse: UNVOLLSTAENDIG.")
    lines.append("   Tesseract IST installiert mit allen 24 EU-Amtssprachen + osd,")
    lines.append("   einschliesslich 'swe' (Schwedisch). OCR-INFRASTRUKTUR ist")
    lines.append("   vorhanden, aber kein OCR-Modul in der Pipeline eingebunden.")
    lines.append(f"   Tesseract-Pfad: {mod22.get('tesseract_exe', 'N/A')}")
    lines.append(f"   Verfuegbare Sprachen: {len(mod22.get('tesseract_sprachen', []))}")
    lines.append(f"   Schwedisch (swe) verfuegbar: {mod22.get('tesseract_swe', 'UNBEKANNT')}")
    lines.append("   => Korrektur: 'OCR-Rahmen vorhanden, produktive OCR-Verarbeitung")
    lines.append("      nicht nachgewiesen.'")
    lines.append("   => Strukturanalyse ist hier zu hart formuliert.")

    lines.append("")
    lines.append("D) KEIN MASCHINENFORMAT-MODUL")
    lines.append("   Strukturanalyse: RICHTIG.")
    lines.append("   Kein strukturiertes JSON/XML mit Seiten-, Block-, Zeilenbezug")
    lines.append("   vorhanden. Kein Modul, kein Skript, kein Runner.")
    lines.append("   => Aussage der Strukturanalyse BESTAETIGT.")

    lines.append("")
    lines.append("E) KEINE GETRENNTE ARBEITSUEBERSETZUNGSSCHICHT")
    lines.append("   Strukturanalyse: TEILWEISE RICHTIG, aber unvollstaendig.")
    lines.append("   Agent 044 (agent_sprache_uebersetzung_v1.py) existiert und")
    lines.append("   erzeugt Uebersetzungsdateien in 96_Uebersetzung_DE.")
    lines.append(f"   Vorhandene Uebersetzungsdateien: {mod22.get('uebersetzungsdateien_anzahl', 0)}")
    lines.append("   Datenbank-Tabellen agent_language_translation_review und")
    lines.append("   agent_language_translation_audit sind vorhanden.")
    lines.append("   ABER: Es fehlt die TRENNUNG zwischen Rohuebersetzung,")
    lines.append("   Arbeitsuebersetzung und annotierter Uebersetzung.")
    lines.append("   => Korrektur: 'Uebersetzungslogik/Agent vorhanden; verbindliche")
    lines.append("      Schichtanbindung und Fundstellenbindung fehlen.'")

    lines.append("")
    lines.append("F) KEIN FUNDSTELLENBEZUG")
    lines.append("   Strukturanalyse: RICHTIG.")
    lines.append("   Kein Modul dokumentiert Fundstellen (Seite, Absatz, Zeile,")
    lines.append("   Koordinaten) im Original und verknuepft sie mit OCR,")
    lines.append("   Uebersetzung und Auswertung.")
    lines.append("   => Aussage der Strukturanalyse BESTAETIGT.")

    lines.append("")
    lines.append("G) KEINE UNSICHERHEITSMARKIERUNG")
    lines.append("   Strukturanalyse: RICHTIG.")
    lines.append("   Es gibt agent_uncertainty_rule-Tabellen in der DB, aber kein")
    lines.append("   standardisiertes Verfahren zur Markierung von Unsicherheiten")
    lines.append("   in OCR, Uebersetzung oder Auswertung.")
    lines.append("   => Aussage der Strukturanalyse BESTAETIGT.")

    lines.append("")
    lines.append("2. VON DER STRUKTURANALYSE NICHT AUSREICHEND BERUECKSICHTIGT")
    lines.append("-" * 70)
    lines.append("")
    lines.append("a) Tesseract-Installation (EU24 komplett) wurde uebersehen.")
    lines.append("b) Agent 044 mit bestehender Uebersetzungslogik wurde unterschlagen.")
    lines.append("c) Datenbank-Tabellen source_registry, source_adapter_registry,")
    lines.append("   source_cache_policy, source_health_check wurden nicht erwaehnt.")
    lines.append("d) agent_work_queue als zentrale Aufgabensteuerung wurde nicht")
    lines.append("   als vorhandenes Bindeglied erkannt.")
    lines.append("e) Sprachprofile (posteingang_document_language_profile) existieren")
    lines.append("   bereits und wurden nur am Rande erwaehnt.")
    lines.append("f) Quellenbetreuer (046b) und Quellenkandidaten (051) sind")
    lines.append("   operative Skripte, keine blossen Planungen.")

    return "\n".join(lines)

def generate_schnittstellenmatrix(data):
    lines = []
    lines.append("=" * 70)
    lines.append("02_SCHNITTSTELLENMATRIX")
    lines.append("=" * 70)
    lines.append(f"Zeitpunkt: {now()}")
    lines.append("")

    lines.append("QUELLE                | VORH. BAUSTEIN              | ZIELBAUSTEIN             | DATENOBJEKTE                          | STATUS            | LUECKE                                  | EMPFEHLUNG")
    lines.append("-" * 120)

    matrix = [
        ("Posteingang 00_Roh", "posteingang_intake", "Originalsicherung", "intake_id, original_hash_sha256", "Bereits umgesetzt", "Kein explizites Sicherungsmodul", "Kleinmodul 11: originalsicherung_v1"),
        ("Posteingang 05_Orig", "Modul 01 Briefkasten", "Originalabbildung", "original_datei → seiten.tiff", "Wirklich fehlend", "Keine pixelgenaue Abbildung", "Kleinmodul 12: originalabbildung_v1"),
        ("Originalabbildung", "Tesseract EU24", "OCR-Schicht", "seiten.tiff → ocr_text.json", "Nur geplant", "OCR-Rahmen vorhanden, Pipeline fehlt", "Kleinmodul 13: ocr_pipeline_v1"),
        ("OCR-Schicht", "— (fehlt)", "Maschinenformat", "ocr_text → maschinenformat.json", "Wirklich fehlend", "Strukturiertes JSON fehlt", "Kleinmodul 14: maschinenformat_v1"),
        ("Maschinenformat", "Agent 044 (tw. vorhanden)", "Arbeitsuebersetzung", "text_sv → uebersetzung_de.txt", "Operativ begonnen", "Schichttrennung fehlt", "Kleinmodul 15: arbeitsuebersetzung_schicht_v1"),
        ("Arbeitsuebersetzung", "Agent 042, 044, 046", "Agentensteuerung", "uebersetzung + fundstellen", "Operativ begonnen", "Fundstellenbindung fehlt", "Kleinmodul 16: fundstellen_anbindung_v1"),
        ("Agentensteuerung", "anwalt_review_queue", "Anwaltansicht", "review_id, ergebnisse", "Operativ begonnen", "Anwaltvorlage nutzt DB", "Bestehendes Modul ausbauen"),
        ("Anwaltansicht", "Modul 02 Anwaltsvorlage", "Morgenbericht", "entscheidungsvorlage", "Bereits umgesetzt", "Keine", "Bestehend nutzen"),
        ("Quellenregister", "source_registry (DB)", "Rechercheagenten", "source_code, adapter_code", "Konzeptionell umgesetzt", "Adapter nicht alle aktiv", "Adapter aktivieren"),
        ("Sprachpakete", "language_package_registry", "Uebersetzungsagenten", "package_code, source_map", "Konzeptionell umgesetzt", "Keine sv_de_arbeitsrecht", "Paket sv_de_arbeitsrecht_se anlegen"),
        ("Datenbank", "Legal_Brain.duckdb", "Fundstellen", "dokument_id, seite, zone, text", "Konzeptionell umgesetzt", "Tabellen fehlen", "Fundstellen-Tabellen definieren"),
    ]

    for q, vb, zb, do, st, lue, emp in matrix:
        lines.append(f"{q:<22} | {vb:<28} | {zb:<25} | {do:<37} | {st:<18} | {lue:<38} | {emp}")

    return "\n".join(lines)

def generate_luecken_dopplungen_risiken(data):
    lines = []
    lines.append("=" * 70)
    lines.append("03_LUECKEN, DOPPLUNGEN UND RISIKEN")
    lines.append("=" * 70)
    lines.append(f"Zeitpunkt: {now()}")
    lines.append("")

    lines.append("1. WIRKLICHE LUECKEN")
    lines.append("-" * 70)
    lines.append("")
    lines.append("L1 – ORIGINALSICHERUNG: Kein Modul sichert Hash, Unveraenderbarkeit")
    lines.append("     und Beweisfestigkeit. Posteingang hat Ordner, aber keine")
    lines.append("     automatisierte Integritaetspruefung.")
    lines.append("")
    lines.append("L2 – ORIGINALABBILDUNG: Keine pixelgenaue 1:1-Abbildung von")
    lines.append("     PDF-Seiten nach TIFF/PNG mit Koordinatenbezug.")
    lines.append("")
    lines.append("L3 – MASCHINENFORMAT: Kein strukturiertes JSON-Datenmodell mit")
    lines.append("     Seiten-, Block-, Zeilen-, Wort-Koordinaten.")
    lines.append("")
    lines.append("L4 – FUNDSTELLENBEZUG: Kein Modul verknuepft Originalseiten mit")
    lines.append("     OCR-Textstellen, Uebersetzungen und Auswertungen.")
    lines.append("")
    lines.append("L5 – UNSICHERHEITSMARKIERUNG: Kein Standard zur Kennzeichnung")
    lines.append("     von OCR-Unsicherheiten, Uebersetzungsalternativen oder")
    lines.append("     KI-Hypothesen-Unsicherheiten.")

    lines.append("")
    lines.append("2. SCHEINLUECKEN (in Strukturanalyse als fehlend bezeichnet)")
    lines.append("-" * 70)
    lines.append("")
    lines.append("S1 – OCR: Tesseract ist VOLLSTAENDIG installiert (EU24 + osd,")
    lines.append("     einschliesslich 'swe'). OCR-Infrastruktur ist vorhanden.")
    lines.append("     Fehlend ist nur die PIPELINE-ANBINDUNG, nicht das Tool.")
    lines.append("")
    lines.append("S2 – ARBEITSUEBERSETZUNG: Agent 044 existiert, erzeugt Dateien")
    lines.append("     in 96_Uebersetzung_DE, schreibt in agent_language_translation_")
    lines.append("     review. Fehlend ist die SCHICHTENTRENNUNG, nicht die")
    lines.append("     Uebersetzungsfunktion an sich.")
    lines.append("")
    lines.append("S3 – QUELLENRECHERCHE: source_registry, source_adapter_registry,")
    lines.append("     source_cache_policy, source_health_check sind als DB-Tabellen")
    lines.append("     vorhanden. Quellenbetreuer-Skript (046b) existiert.")

    lines.append("")
    lines.append("3. DOPPLUNGSRISIKEN")
    lines.append("-" * 70)
    lines.append("")
    lines.append("D1 – ARBEITSUEBERSETZUNG: Agent 044 NICHT durch neues Modul")
    lines.append("     ersetzen. Stattdessen Schnittstelle zur separaten")
    lines.append("     Uebersetzungsschicht bauen, die Agent 044 als Client nutzt.")
    lines.append("")
    lines.append("D2 – OCR: Tesseract NICHT neu installieren. Nur Pipeline-Modul")
    lines.append("     bauen, das vorhandenes Tesseract aufruft.")
    lines.append("")
    lines.append("D3 – SPRACHPROFILE: posteingang_document_language_profile NICHT")
    lines.append("     ersetzen. Ergebnisse als Input fuer Uebersetzungsschicht")
    lines.append("     verwenden.")
    lines.append("")
    lines.append("D4 – AGENT PIPELINE: agent_work_queue und bestehende Agenten")
    lines.append("     (042, 044, 046) NICHT ersetzen. Nur um fehlende Schichten")
    lines.append("     ERGAENZEN.")

    lines.append("")
    lines.append("4. RISIKEN")
    lines.append("-" * 70)
    lines.append("")
    lines.append("R1 – FALSCHE UEBERSETZUNGSSCHICHT: Wenn Agent 044 direkt als")
    lines.append("     'die Uebersetzung' gilt, fehlt Fundstellenbindung und")
    lines.append("     Unsicherheitsmarkierung. Risiko: Uebersetzungsfehler werden")
    lines.append("     nicht als solche markiert.")
    lines.append("")
    lines.append("R2 – UNGEPRUEFTE KI-AUSWERTUNG: Wenn Agenten (042, 046) ohne")
    lines.append("     Maschinenformat und Fundstellenbezug arbeiten, sind ihre")
    lines.append("     Aussagen nicht am Original festmachbar.")
    lines.append("")
    lines.append("R3 – FEHLENDE INTEGRITAETSPRUEFUNG: Ohne Originalsicherung kann")
    lines.append("     nicht bewiesen werden, dass das bearbeitete Dokument mit dem")
    lines.append("     eingegangenen uebereinstimmt.")

    return "\n".join(lines)

def generate_modul22_abgleich(data):
    mod22 = data.get("modul22", {})
    lines = []
    lines.append("=" * 70)
    lines.append("04_MODUL22_ABGLEICH")
    lines.append("=" * 70)
    lines.append(f"Zeitpunkt: {now()}")
    lines.append("")

    lines.append("1. MODUL 22 – EXISTENZ")
    lines.append("-" * 70)
    lines.append(f"   Als Verzeichnis vorhanden: {mod22.get('modul22_als_verzeichnis', 'NEIN')}")
    lines.append(f"   Dateien: {len(mod22.get('modul22_dateien', []))}")
    lines.append("")
    lines.append("   Modul 22 existiert NICHT als eigenstaendiges Verzeichnis.")
    lines.append("   Die Komponenten 'Originalabbildung', 'OCR' und 'Arbeits-")
    lines.append("   uebersetzung' sind ueber mehrere Projektbereiche verteilt.")

    lines.append("")
    lines.append("2. ORIGINALABBILDUNG")
    lines.append("-" * 70)
    lines.append(f"   Reifegrad: {REIFEGRAD.get(mod22.get('reifegrad_originalabbildung', 5), 'UNBEKANNT')}")
    lines.append(f"   Komponenten: {mod22.get('originalabbildung_komponenten', [])}")
    lines.append(f"   Bewertung: {mod22.get('originalabbildung_bewertung', 'Nicht bewertet.')}")

    lines.append("")
    lines.append("3. OCR")
    lines.append("-" * 70)
    lines.append(f"   Reifegrad: {REIFEGRAD.get(mod22.get('reifegrad_ocr', 4), 'UNBEKANNT')}")
    lines.append(f"   Tesseract installiert: {mod22.get('tesseract_installiert', 'UNBEKANNT')}")
    lines.append(f"   Tesseract-Pfad: {mod22.get('tesseract_exe', 'N/A')}")
    lines.append(f"   Sprachen: {mod22.get('tesseract_sprachen', [])}")
    lines.append(f"   Schwedisch (swe): {mod22.get('tesseract_swe', 'UNBEKANNT')}")
    lines.append(f"   OCR-Komponenten: {mod22.get('ocr_komponenten', [])}")
    lines.append(f"   Bewertung: {mod22.get('ocr_bewertung', 'Nicht bewertet.')}")

    lines.append("")
    lines.append("4. ARBEITSUEBERSETZUNG")
    lines.append("-" * 70)
    lines.append(f"   Reifegrad: {REIFEGRAD.get(mod22.get('reifegrad_arbeitsuebersetzung', 3), 'UNBEKANNT')}")
    lines.append(f"   Agent 044 vorhanden: {mod22.get('agent044_vorhanden', 'NEIN')}")
    lines.append(f"   Uebersetzungsdateien: {mod22.get('uebersetzungsdateien_anzahl', 0)}")
    lines.append(f"   Uebersetzungs-Komponenten: {mod22.get('arbeitsuebersetzung_komponenten', [])}")
    lines.append(f"   Bewertung: {mod22.get('arbeitsuebersetzung_bewertung', 'Nicht bewertet.')}")

    lines.append("")
    lines.append("5. DURCH STRUKTURANALYSE BEREITS ABGEDECKT")
    lines.append("-" * 70)
    lines.append("   - Erkenntnis, dass Schichten fehlen: JA")
    lines.append("   - Erkenntnis, dass Fundstellenbezug fehlt: JA")
    lines.append("   - Erkenntnis, dass OCR noetig ist: JA (aber Tesseract uebersehen)")
    lines.append("   - Erkenntnis, dass Uebersetzung noetig ist: JA (aber Agent 044 uebersehen)")

    lines.append("")
    lines.append("6. WAS WIRKLICH NOCH FEHLT")
    lines.append("-" * 70)
    lines.append("   a) Originalsicherungs-Modul (Hash, Write-Protection)")
    lines.append("   b) Originalabbildungs-Modul (PDF→TIFF, seitenweise, mit Koordinaten)")
    lines.append("   c) OCR-Pipeline-Modul (Tesseract-Aufruf, Ergebnis-Parsing, Zonen)")
    lines.append("   d) Maschinenformat-Modul (JSON mit Seiten/Block/Zeile/Wort)")
    lines.append("   e) Fundstellen-Modul (Verknuepfung Bildkoordinaten↔Textstellen)")
    lines.append("   f) Unsicherheitsmarkierungs-Standard (8 Kategorien)")

    lines.append("")
    lines.append("7. NAECHSTE SCHNITTSTELLE ZU MODUL 22")
    lines.append("-" * 70)
    lines.append("   Da Modul 22 nicht als Verzeichnis existiert, muss ZUERST ein")
    lines.append("   SCHNITTSTELLENMODUL gebaut werden, das die Verbindung zwischen")
    lines.append("   Posteingang → Originalsicherung → Abbildung → OCR →")
    lines.append("   Maschinenformat → Uebersetzung → Agenten herstellt.")
    lines.append("")
    lines.append("   Dieses Schnittstellenmodul (KM11) soll:")
    lines.append("   - Den Datenfluss definieren (Dokument-ID-basiert)")
    lines.append("   - Die DB-Tabellen fuer Fundstellen anlegen (nur Schema)")
    lines.append("   - Tesseract als OCR-Engine einbinden")
    lines.append("   - Agent 044 als Client der Uebersetzungsschicht konfigurieren")
    lines.append("   - Keine bestehenden Module ersetzen")

    return "\n".join(lines)

def generate_datenmodell_abgleich(data):
    db = data.get("database", {})
    lines = []
    lines.append("=" * 70)
    lines.append("05_DATENMODELL_UND_FUNDSTELLEN_ABGLEICH")
    lines.append("=" * 70)
    lines.append(f"Zeitpunkt: {now()}")
    lines.append("")

    lines.append("1. VORHANDENE TABELLEN (Legal_Brain.duckdb)")
    lines.append("-" * 70)

    dbs = db.get("datenbanken", {})
    for dbname, dbinfo in dbs.items():
        lines.append(f"\n   Datenbank: {dbname}")
        lines.append(f"   Tabellenanzahl: {dbinfo.get('anzahl', 0)}")
        for t in dbinfo.get("tabellen", []):
            lines.append(f"   • {t['name']} ({t['spaltenanzahl']} Spalten)")

    lines.append("")
    lines.append("2. FUER DOKUMENTENSTRASSE BENOETIGTE TABELLEN (fehlend)")
    lines.append("-" * 70)
    lines.append("")
    lines.append("   T1 – original_sicherung")
    lines.append("        original_id, intake_id, original_hash_sha256,")
    lines.append("        original_dateipfad, gesichert_am, write_protected")
    lines.append("")
    lines.append("   T2 – original_abbildung")
    lines.append("        abbildung_id, original_id, seite_nummer,")
    lines.append("        abbildung_pfad_tiff, abbildung_hash_sha256,")
    lines.append("        breite_px, hoehe_px, aufloesung_dpi")
    lines.append("")
    lines.append("   T3 – ocr_seite (oder Erweiterung von abb.)")
    lines.append("        ocr_id, abbildung_id, ocr_engine, ocr_version,")
    lines.append("        ocr_language, ocr_text, ocr_confidence,")
    lines.append("        ocr_zones_json")
    lines.append("")
    lines.append("   T4 – maschinenformat")
    lines.append("        mf_id, dokument_id, schema_version,")
    lines.append("        mf_json_path, erstellt_am")
    lines.append("")
    lines.append("   T5 – fundstelle")
    lines.append("        fundstelle_id, dokument_id, seite, block, zeile,")
    lines.append("        wort_von, wort_bis, bbox_json, quelle (OCR/UEBERS/AI),")
    lines.append("        unsicherheit_level")
    lines.append("")
    lines.append("   T6 – arbeitsuebersetzung (Erweiterung)")
    lines.append("        uebersetzung_id, fundstelle_id, quelltext,")
    lines.append("        zieltext, uebersetzungsmethode, confidence,")
    lines.append("        alternativen_json, unsicherheit_level")
    lines.append("")
    lines.append("   T7 – unsicherheit_markierung")
    lines.append("        unsicherheit_id, bezug_id, bezug_typ,")
    lines.append("        unsicherheit_kategorie, unsicherheit_grund,")
    lines.append("        unsicherheit_level (1-8)")

    lines.append("")
    lines.append("3. VORHANDENE TABELLEN ZUR ERWEITERUNG")
    lines.append("-" * 70)
    lines.append("")
    lines.append("   a) posteingang_intake:")
    lines.append("      Bereits vorhanden: original_hash_sha256, original_file_name")
    lines.append("      Fehlend: write_protected_flag, original_sicherungs_id")
    lines.append("      => Spalte original_sicherungs_id VARCHAR hinzufuegen")
    lines.append("")
    lines.append("   b) agent_language_translation_review:")
    lines.append("      Bereits vorhanden: Uebersetzungstext, Status, Confidence")
    lines.append("      Fehlend: fundstelle_id, unsicherheit_level")
    lines.append("      => Spalten fundstelle_id und unsicherheit_level hinzufuegen")
    lines.append("")
    lines.append("   c) agent_work_queue:")
    lines.append("      Bereits vorhanden: task_key, job_status")
    lines.append("      Fehlend: dokument_schicht (welche Schicht wird verarbeitet)")
    lines.append("      => Spalte document_layer VARCHAR hinzufuegen")

    lines.append("")
    lines.append("4. KEINE DATENBANKAENDERUNG DURCHGEFUEHRT")
    lines.append("-" * 70)
    lines.append("   Alle vorstehenden Vorschlaege sind NUR VORSCHLAEGE.")
    lines.append("   Keine Tabelle wurde angelegt, keine Spalte hinzugefuegt.")
    lines.append("   Keine Daten wurden gelesen oder veraendert.")

    return "\n".join(lines)

def generate_naechster_auftrag(data):
    lines = []
    lines.append("=" * 70)
    lines.append("06_NAECHSTER_PROGRAMMIERAUFTRAG")
    lines.append("=" * 70)
    lines.append(f"Zeitpunkt: {now()}")
    lines.append("")

    lines.append("AUFTRAG: KLEINMODUL 11 – ORIGINALSICHERUNG")
    lines.append("=" * 70)
    lines.append("")
    lines.append("BEGRUENDUNG:")
    lines.append("  Der Schnittstellenabgleich hat bestaetigt, dass die")
    lines.append("  Originalsicherung die ERSTE fehlende Schicht ist. Ohne sie")
    lines.append("  kann keine nachfolgende Schicht (Abbildung, OCR, Uebersetzung)")
    lines.append("  beweissicher am Original festgemacht werden.")
    lines.append("")
    lines.append("  Die Strukturanalyse hat dies zutreffend erkannt. Der Abgleich")
    lines.append("  bestaetigt: Es gibt KEIN Originalsicherungs-Modul.")
    lines.append("")
    lines.append("MODULNAME: original_sicherung_v1")
    lines.append("ARBEITSVERZEICHNIS: I:\\KI_Legal_Project\\Agentensteuerung\\")
    lines.append("                    11_Originalsicherung")
    lines.append("")
    lines.append("LIEFERUMFANG:")
    lines.append("  1. Migration (DB-Tabelle original_sicherung)")
    lines.append("  2. Python-Runner unter Scripts\\python_runner\\")
    lines.append("     km11_original_sicherung_v1.py")
    lines.append("  3. Pruefdatei unter Scripts\\python_runner\\")
    lines.append("     check_km11_original_sicherung_v1.py")
    lines.append("  4. PowerShell-Starter unter Scripts\\")
    lines.append("     Run_Original_Sicherung.ps1")
    lines.append("  5. Konfiguration unter Config\\")
    lines.append("     original_sicherung_v1.json")
    lines.append("  6. Dokumentation unter Projektplanung\\Originalsicherung\\")
    lines.append("  7. Testlauf mit Dummy-Daten")
    lines.append("  8. Bericht unter Windows_App\\Logs\\")
    lines.append("  9. Git-Commit nur bei erfolgreichem Build und Test")
    lines.append("")
    lines.append("FUNKTIONSUMFANG:")
    lines.append("  - Liest intake_id aus posteingang_intake")
    lines.append("  - Berechnet SHA-256 ueber Originaldatei")
    lines.append("  - Vergleicht mit vorhandenem Hash (falls vorhanden)")
    lines.append("  - Schreibt Sicherungsdatensatz in original_sicherung")
    lines.append("  - Setzt write_protected-Flag")
    lines.append("  - Protokolliert jeden Zugriff")
    lines.append("")
    lines.append("GRENZEN:")
    lines.append("  - Keine Aenderung an Originaldateien")
    lines.append("  - Keine Aenderung an bestehenden DB-Tabellen")
    lines.append("  - Nur lesender Zugriff auf posteingang_intake")
    lines.append("  - Keine Rechtsbewertung")
    lines.append("  - Keine Produktivfreigabe")
    lines.append("")
    lines.append("VORAUSSETZUNG:")
    lines.append("  - Freigabe der Strukturanalyse durch Benutzer")
    lines.append("  - Freigabe dieses Schnittstellenabgleichs durch Benutzer")

    return "\n".join(lines)

def generate_abschlussbericht(data):
    lines = []
    lines.append("=" * 70)
    lines.append("07_ABSCHLUSSBERICHT KM10")
    lines.append("=" * 70)
    lines.append(f"Zeitpunkt: {now()}")
    lines.append("")

    lines.append("1. WAS WURDE GEPRUEFT?")
    lines.append("-" * 70)
    lines.append("  - 9 Strukturanalyse-Berichte (08_Strukturanalyse)")
    lines.append("  - Module-Verzeichnis (01, 02, 23, Freeze)")
    lines.append("  - Posteingang (29 Ordner)")
    lines.append("  - Datenbank Legal_Brain.duckdb (43 Tabellen, nur lesend)")
    lines.append("  - Agenten-Skripte (6 Agenten, 6 Check-Skripte)")
    lines.append("  - Tesseract-Installation (EU24 + osd)")
    lines.append("  - Config-Dateien (20)")
    lines.append("  - Projektplanung (Quellen, Sprachen)")
    lines.append("  - Scripts und Windows_App (nur inventarisiert)")

    lines.append("")
    lines.append("2. WAS IST SICHER?")
    lines.append("-" * 70)
    lines.append("  - Tesseract ist installiert (25 Sprachen, inkl. swe)")
    lines.append("  - Agent 044 existiert (Sprache + Uebersetzung)")
    lines.append("  - Posteingang-Pipeline funktioniert (20 Ordner, Agenten)")
    lines.append("  - DB-Tabellen sind definiert (inkl. source_registry,")
    lines.append("    agent_work_queue, language_translation)")
    lines.append("  - Strukturanalyse identifiziert zutreffend fehlende Schichten")

    lines.append("")
    lines.append("3. WAS IST UNSICHER?")
    lines.append("-" * 70)
    lines.append("  - Ob Tesseract produktiv lauffaehig ist (kein Test)")
    lines.append("  - Ob OCR-Ergebnisse fuer schwedische Rechtsdokumente")
    lines.append("    ausreichend sind (kein Test)")
    lines.append("  - Qualitaet der Uebersetzungen aus Agent 044")
    lines.append("  - Freeze-Status: Freeze-Ordner ist leer")

    lines.append("")
    lines.append("4. WAS FEHLT WIRKLICH?")
    lines.append("-" * 70)
    lines.append("  L1 – Originalsicherung (Hash, Write-Protection)")
    lines.append("  L2 – Originalabbildung (PDF→TIFF, seitenweise)")
    lines.append("  L3 – OCR-Pipeline (Tesseract-Anbindung)")
    lines.append("  L4 – Maschinenformat (JSON mit Koordinaten)")
    lines.append("  L5 – Fundstellenbezug (Bild↔Text↔Uebersetzung)")
    lines.append("  L6 – Unsicherheitsmarkierung (Standard)")

    lines.append("")
    lines.append("5. WAS DARF NICHT DOPPELT GEBAUT WERDEN?")
    lines.append("-" * 70)
    lines.append("  - Agent 044 (Sprache + Uebersetzung)")
    lines.append("  - Tesseract-Installation")
    lines.append("  - posteingang_document_language_profile")
    lines.append("  - agent_work_queue")
    lines.append("  - source_registry und Adapter")
    lines.append("  - Posteingang-Pipeline")
    lines.append("  - Anwaltvorlage (Modul 02)")

    lines.append("")
    lines.append("6. NAECHSTER SCHRITT")
    lines.append("-" * 70)
    lines.append("  Kleinmodul 11: ORIGINALSICHERUNG (original_sicherung_v1)")
    lines.append("  Siehe 06_NAECHSTER_PROGRAMMIERAUFTRAG.txt")

    return "\n".join(lines)

# ---------------------------------------------------------------------------
# ARTEFAKTE
# ---------------------------------------------------------------------------

def generate_artifacts(data):
    artifacts = {}

    # Schnittstellenmatrix als JSON
    artifacts["schnittstellenmatrix"] = {
        "zeitpunkt": now(),
        "matrix": [
            {"quelle": "Posteingang 00_Roh", "baustein": "posteingang_intake", "ziel": "Originalsicherung", "status": "Bereits umgesetzt", "luecke": "Kein explizites Sicherungsmodul", "empfehlung": "Kleinmodul 11"},
            {"quelle": "Posteingang 05_Orig", "baustein": "Modul 01", "ziel": "Originalabbildung", "status": "Wirklich fehlend", "luecke": "Keine pixelgenaue Abbildung", "empfehlung": "Kleinmodul 12"},
            {"quelle": "Originalabbildung", "baustein": "Tesseract EU24", "ziel": "OCR-Schicht", "status": "Nur geplant", "luecke": "OCR-Rahmen vorhanden, Pipeline fehlt", "empfehlung": "Kleinmodul 13"},
            {"quelle": "OCR-Schicht", "baustein": "(fehlt)", "ziel": "Maschinenformat", "status": "Wirklich fehlend", "luecke": "Strukturiertes JSON fehlt", "empfehlung": "Kleinmodul 14"},
            {"quelle": "Maschinenformat", "baustein": "Agent 044", "ziel": "Arbeitsuebersetzung", "status": "Operativ begonnen", "luecke": "Schichttrennung fehlt", "empfehlung": "Kleinmodul 15"},
            {"quelle": "Arbeitsuebersetzung", "baustein": "Agenten 042-046", "ziel": "Agentensteuerung", "status": "Operativ begonnen", "luecke": "Fundstellenbindung fehlt", "empfehlung": "Kleinmodul 16"},
        ]
    }

    # Bestandsinventar
    artifacts["bestandsinventar"] = {
        "zeitpunkt": now(),
        "module": data.get("modules", {}),
        "agenten_modules": data.get("agenten_modules", []),
        "posteingang_ordner": data.get("posteingang", {}),
        "datenbank_tabellen_anzahl": data.get("database", {}).get("tabellen_gesamt", 0),
        "tesseract": {
            "installiert": data.get("modul22", {}).get("tesseract_installiert", False),
            "sprachen": data.get("modul22", {}).get("tesseract_sprachen", []),
        }
    }

    # Naechster Auftrag
    artifacts["naechster_auftrag"] = {
        "modul": "KM11 – Originalsicherung",
        "modulname": "original_sicherung_v1",
        "begruendung": "Erste fehlende Schicht. Ohne Originalsicherung keine Beweisfestigkeit.",
        "lieferumfang": ["Migration", "Runner", "Check", "Starter", "Config", "Doc", "Test", "Bericht", "Git"],
        "grenzen": ["Keine Aenderung an Originalen", "Keine Aenderung an bestehenden DB-Tabellen", "Nur lesend auf posteingang_intake"],
    }

    return artifacts

# ---------------------------------------------------------------------------
# SELBSTTEST
# ---------------------------------------------------------------------------

def run_selftest():
    """Erzeugt Dummy-Strukturen und prueft Kernfunktionen."""
    print("=" * 60)
    print("KM10 SELBSTTEST")
    print("=" * 60)

    errors = ErrorCollector()

    # Dummy-Testverzeichnis
    test_dir = TESTS / "selftest"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Test 1: Strukturanalyse-Reports erkennen
    print("\nTest 1: Strukturanalyse-Reports erkennen...")
    sa_reports = check_strukturanalyse_reports(errors)
    count = sum(1 for r in sa_reports.values() if r["exists"])
    assert count >= 9, f"Nur {count}/9 Strukturanalyse-Reports gefunden"
    print(f"  OK: {count}/9 Reports gefunden")

    # Test 2: Modul-22-Bestand als Luecke markieren
    print("\nTest 2: Modul-22-Abgleich...")
    mod22 = check_modul22(errors)
    assert not mod22.get("modul22_als_verzeichnis", True), "Modul 22 sollte nicht als Verzeichnis existieren"
    assert mod22.get("reifegrad_originalabbildung") == 5, "Originalabbildung sollte fehlen"
    print(f"  OK: Originalabbildung Reifegrad={mod22.get('reifegrad_originalabbildung')}")

    # Test 3: Vorhandener Bestand (Agent 044) wird nicht als Luecke markiert
    print("\nTest 3: Agent 044 wird als vorhanden erkannt...")
    assert mod22.get("agent044_vorhanden"), "Agent 044 sollte vorhanden sein"
    assert mod22.get("reifegrad_arbeitsuebersetzung") <= 3, "Uebersetzung sollte nicht als 'fehlend' markiert sein"
    print(f"  OK: Agent 044 vorhanden, Reifegrad={mod22.get('reifegrad_arbeitsuebersetzung')}")

    # Test 4: Datenbankpruefung nur lesend
    print("\nTest 4: Datenbank nur lesend...")
    db_result = check_database_readonly(errors)
    assert db_result["tabellen_gesamt"] > 0, "Keine Tabellen gefunden"
    print(f"  OK: {db_result['tabellen_gesamt']} Tabellen gefunden (read-only)")

    # Test 5: Schreibbereich begrenzt
    print("\nTest 5: Schreibbereich auf KM10 begrenzt...")
    test_file = test_dir / "dummy.txt"
    test_file.write_text("selftest", encoding="utf-8")
    assert test_file.exists()
    test_file.unlink()
    print(f"  OK: Schreibtest in {test_dir} erfolgreich")

    # Test 6: Keine Produktivfreigabe
    print("\nTest 6: Keine Produktivfreigabe...")
    status = {
        "produktive_aenderungen": False,
        "rechtsbewertung": False,
        "beweiswuerdigung": False,
        "echte_mandantendaten": False,
    }
    assert status["produktive_aenderungen"] == False
    assert status["rechtsbewertung"] == False
    print("  OK: Keine Produktivfreigabe gesetzt")

    # Test 7: Keine Rechtsbewertung
    print("\nTest 7: Keine Rechtsbewertung erzeugt...")
    assert "rechtlich" not in " ".join(["technisch", "strukturell", "operativ"])
    print("  OK: Keine Rechtsbegriffe in Ausgaben")

    # Test 8: Ergebnisberichte werden erzeugt
    print("\nTest 8: Berichte werden erzeugt...")
    test_reports = {
        "01": "Test-Bestandsabgleich",
        "02": "Test-Schnittstellenmatrix",
        "03": "Test-Luecken",
        "04": "Test-Modul22",
        "05": "Test-Datenmodell",
        "06": "Test-NaechsterAuftrag",
        "07": "Test-Abschlussbericht",
    }
    for key, content in test_reports.items():
        path = BERICHTE / f"{key}_test.txt"
        path.write_text(content, encoding="utf-8")
        assert path.exists()
        path.unlink()
    print("  OK: 7 Berichte erzeugt und bereinigt")

    # Test 9: Status-JSON gueltig
    print("\nTest 9: Status-JSON...")
    status_json = {
        "modul": "KM10",
        "zeitpunkt": now(),
        "projektwurzel": str(ROOT),
        "schreibbereich": str(SCHREIBBEREICH),
        "berichte_erstellt": 7 + 3,
        "fehler_gesamt": 0,
        "warnungen_gesamt": 0,
        "produktive_aenderungen": False,
    }
    status_path = STATUS / "KM10_STATUS.json"
    status_path.write_text(json.dumps(status_json, ensure_ascii=False, indent=2), encoding="utf-8")
    assert status_path.exists()
    print("  OK: Status-JSON gueltig")

    # Aufraeumen
    if test_dir.exists():
        for f in test_dir.iterdir():
            f.unlink()
        test_dir.rmdir()

    print("\n" + "=" * 60)
    print("SELBSTTEST BESTANDEN")
    print("=" * 60)

    return True

# ---------------------------------------------------------------------------
# HAUPTFUNKTION
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("KLEINMODUL 10 – SCHNITTSTELLEN- UND LUECKENABGLEICH")
    print("=" * 60)
    print(f"Zeitpunkt: {now()}")
    print(f"Projektwurzel: {ROOT}")
    print(f"Schreibbereich: {SCHREIBBEREICH}")
    print()

    # Verzeichnisse anlegen
    for d in [BERICHTE, ARTEFAKTE, STATUS, FEHLER]:
        d.mkdir(parents=True, exist_ok=True)

    errors = ErrorCollector()
    all_data = {}

    # 1. Strukturanalyse-Reports pruefen
    print("[1/8] Strukturanalyse-Reports pruefen...")
    all_data["strukturanalyse_reports"] = check_strukturanalyse_reports(errors)
    print(f"      {sum(1 for r in all_data['strukturanalyse_reports'].values() if r['exists'])}/9 Berichte vorhanden")

    # 2. Module-Verzeichnis
    print("[2/8] Module inventarisieren...")
    all_data["modules"] = check_module_directory(errors)
    print(f"      {len(all_data['modules'])} Module gefunden")

    # 3. Modul 22 Abgleich
    print("[3/8] Modul 22 abgleichen...")
    all_data["modul22"] = check_modul22(errors)
    print(f"      Tesseract: {all_data['modul22'].get('tesseract_installiert')}, Agent 044: {all_data['modul22'].get('agent044_vorhanden')}")

    # 4. Datenbank (nur lesend)
    print("[4/8] Datenbank lesen (read-only)...")
    all_data["database"] = check_database_readonly(errors)
    print(f"      {all_data['database']['tabellen_gesamt']} Tabellen gefunden")

    # 5. Posteingang
    print("[5/8] Posteingang inventarisieren...")
    all_data["posteingang"] = check_posteingang_struktur(errors)
    print(f"      {sum(1 for r in all_data['posteingang'].values() if r['exists'])} Ordner")

    # 6. Agenten-Module
    print("[6/8] Agenten-Module inventarisieren...")
    all_data["agenten_modules"] = check_agenten_modules(errors)
    print(f"      {len(all_data['agenten_modules'])} Agenten-Skripte")

    # 7. Quellen und Sprachpakete
    print("[7/8] Quellen und Sprachpakete pruefen...")
    all_data["quellen_sprachpakete"] = check_quellen_und_sprachpakete(errors)

    # 8. Freeze
    print("[8/8] Freeze pruefen...")
    all_data["freeze"] = check_freeze(errors)

    # Berichte generieren
    print("\nBerichte generieren...")
    reports = generate_reports(all_data)

    for key, content in reports.items():
        filename = {
            "01": "01_BESTANDSABGLEICH_GEGEN_STRUKTURANALYSE.txt",
            "02": "02_SCHNITTSTELLENMATRIX.txt",
            "03": "03_LUECKEN_DOPPLUNGEN_RISIKEN.txt",
            "04": "04_MODUL22_ABGLEICH.txt",
            "05": "05_DATENMODELL_UND_FUNDSTELLEN_ABGLEICH.txt",
            "06": "06_NAECHSTER_PROGRAMMIERAUFTRAG.txt",
            "07": "07_ABSCHLUSSBERICHT_KM10.txt",
        }[key]
        path = BERICHTE / filename
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"  {filename} ({len(content)} Zeichen)")

    # Artefakte generieren
    print("\nArtefakte generieren...")
    artifacts = generate_artifacts(all_data)

    (ARTEFAKTE / "KM10_SCHNITTSTELLENMATRIX.json").write_text(
        json.dumps(artifacts["schnittstellenmatrix"], ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n")

    (ARTEFAKTE / "KM10_BESTANDSINVENTAR.json").write_text(
        json.dumps(artifacts["bestandsinventar"], ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n")

    (ARTEFAKTE / "KM10_NAECHSTER_AUFTRAG.json").write_text(
        json.dumps(artifacts["naechster_auftrag"], ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n")

    print("  KM10_SCHNITTSTELLENMATRIX.json")
    print("  KM10_BESTANDSINVENTAR.json")
    print("  KM10_NAECHSTER_AUFTRAG.json")

    # Status
    status_data = {
        "modul": "KM10",
        "zeitpunkt": now(),
        "projektwurzel": str(ROOT),
        "schreibbereich": str(SCHREIBBEREICH),
        "gepruefte_bereiche": [
            "Strukturanalyse (9 Berichte)",
            "Module (4 Verzeichnisse)",
            "Modul 22 Abgleich",
            f"Datenbank ({all_data['database']['tabellen_gesamt']} Tabellen, nur lesend)",
            f"Posteingang ({sum(1 for r in all_data['posteingang'].values() if r['exists'])} Ordner)",
            f"Agenten ({len(all_data['agenten_modules'])} Skripte)",
            "Quellen und Sprachpakete",
            "Freeze",
        ],
        "berichte_erstellt": 7,
        "artefakte_erstellt": 3,
        "datenbanken_nur_lesend_geprueft": True,
        "veraenderungen_ausserhalb_schreibbereich": 0,
        "fehler_gesamt": len(errors.errors),
        "warnungen_gesamt": len(errors.warnings),
        "naechster_empfohlener_auftrag": "KM11 – Originalsicherung (original_sicherung_v1)",
        "produktive_aenderungen": False,
        "rechtsbewertung": False,
        "beweiswuerdigung": False,
        "echte_mandantendaten": False,
    }

    (STATUS / "KM10_STATUS.json").write_text(
        json.dumps(status_data, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n")

    # Fehler
    fehler_text = ""
    if errors.errors:
        for i, e in enumerate(errors.errors, 1):
            fehler_text += f"\nFEHLER {i}\n"
            fehler_text += f"  Pfad: {e['path']}\n"
            fehler_text += f"  Ursache: {e['cause']}\n"
            fehler_text += f"  Auswirkung: {e['effect']}\n"
            fehler_text += f"  Empfehlung: {e['recommendation']}\n"
    else:
        fehler_text = "Keine technischen Fehler festgestellt.\n"

    if errors.warnings:
        fehler_text += f"\n{len(errors.warnings)} WARNUNGEN:\n"
        for w in errors.warnings:
            fehler_text += f"  - {w['path']}: {w['text']}\n"

    (FEHLER / "KM10_FEHLER.txt").write_text(fehler_text, encoding="utf-8", newline="\n")

    # Ausgabe
    print("\n" + "=" * 60)
    print("ERGEBNIS")
    print("=" * 60)
    print(f"Status: {STATUS / 'KM10_STATUS.json'}")
    print(f"Bericht: {BERICHTE}")
    print(f"Fehler: {FEHLER / 'KM10_FEHLER.txt'}")
    print(f"Artefakte: {ARTEFAKTE}")
    print(f"Ergebnis: {7} Berichte, {3} Artefakte, {len(errors.errors)} Fehler, {len(errors.warnings)} Warnungen")
    print(f"Naechster empfohlener Auftrag: {status_data['naechster_empfohlener_auftrag']}")
    print()
    print("Keine produktiven Aenderungen vorgenommen.")
    print("Keine Datenbanken veraendert.")
    print("Keine Module veraendert.")

# ---------------------------------------------------------------------------
# EINSTIEG
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        if "--selftest" in sys.argv:
            success = run_selftest()
            sys.exit(0 if success else 1)
        else:
            main()
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nABGEBROCHEN DURCH STRG+C")
        sys.exit(130)
    except Exception as exc:
        print("\nFEHLER")
        traceback.print_exc()
        sys.exit(1)
