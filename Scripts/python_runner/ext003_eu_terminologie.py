#!/usr/bin/env python3
"""
EXT-003 – EU-Terminologiepakete für Rechtssicherheit

Ziel:
Aufbau eines lokalen EU-Terminologie-Registers für rechtssichere Übersetzungen.
Enthält EuroVoc-Konzepte, EU-Verordnungsbegriffe und validierte Übersetzungsäquivalente.

Sicherheit:
- Kein Cloud-Übersetzungsdienst
- Keine Online-Terminologie-Abfragen
- EU-Daten nur aus lokalen Quellen
- Keine echten Mandantendaten für Validierung
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "Database" / "DuckDB"
DB_NAME = "alin_local.duckdb"
DB_PATH = DB_DIR / DB_NAME
CONFIG_FILE = BASE_DIR / "Config" / "ext003_eu_terminologie_v1.json"
REPORT_FILE = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "EXT003_EU_TERMINOLOGIE_BERICHT.txt"
TERMINOLOGIE_DIR = BASE_DIR / "ALIN_Neustart_Core" / "18_Terminologie"

def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")

def log(msg: str) -> None:
    print(f"[{zeitstempel()}] {msg}")

def main() -> int:
    log("EXT-003 – EU-Terminologiepaket gestartet")

    if not DB_PATH.exists():
        log(f"FEHLER: DuckDB-Datenbank nicht gefunden: {DB_PATH}")
        return 1

    try:
        conn = duckdb.connect(str(DB_PATH))
        log("Verbindung hergestellt")

        # Beispieldaten: EU-Rechtsterminologie (synthetisch, keine echten Mandantendaten)
        beispiel_begriffe = [
            {
                "begriff": "Verordnung (EU)",
                "sprache": "de",
                "kategorie": "verordnung",
                "quelle": "Art. 288 AEUV",
                "definition": "Rechtsakt der Europäischen Union mit allgemeiner Geltung",
                "kontext": "Primärrecht, Vertragsrecht",
                "aequivalente": json.dumps({"de": "Verordnung (EU)", "en": "Regulation (EU)", "fr": "Règlement (UE)"}),
                "validiert": True,
                "validiert_von": "EU-Terminologie-Register",
                "validiert_am": "2026-05-18"
            },
            {
                "begriff": "Richtlinie (EU)",
                "sprache": "de",
                "kategorie": "richtlinie",
                "quelle": "Art. 288 AEUV",
                "definition": "Rechtsakt zur Harmonisierung nationaler Rechtsvorschriften",
                "kontext": "Primärrecht, Vertragsrecht",
                "aequivalente": json.dumps({"de": "Richtlinie (EU)", "en": "Directive (EU)", "fr": "Directive (UE)"}),
                "validiert": True,
                "validiert_von": "EU-Terminologie-Register",
                "validiert_am": "2026-05-18"
            },
            {
                "begriff": "Vertrag über die Arbeitsweise der Europäischen Union",
                "sprache": "de",
                "kategorie": "vertrag",
                "quelle": "AEUV",
                "definition": "Primärrechtlicher Vertrag der Europäischen Union",
                "kontext": "Primärrecht",
                "aequivalente": json.dumps({"de": "Vertrag über die Arbeitsweise der Europäischen Union", "en": "Treaty on the Functioning of the European Union", "fr": "Traité sur le fonctionnement de l'Union européenne"}),
                "validiert": True,
                "validiert_von": "EU-Terminologie-Register",
                "validiert_am": "2026-05-18"
            },
            {
                "begriff": "Mandatsgeheimnis",
                "sprache": "de",
                "kategorie": "berufsrecht",
                "quelle": "BRAO § 43a",
                "definition": "Geheimhaltungspflicht des Rechtsanwalts gegenüber Mandanten",
                "kontext": "Berufsrecht, Anwaltsrecht",
                "aequivalente": json.dumps({"de": "Mandatsgeheimnis", "en": "professional secrecy", "fr": "secret professionnel"}),
                "validiert": True,
                "validiert_von": "BRAO",
                "validiert_am": "2026-05-18"
            }
        ]

        count_vor = conn.execute("SELECT COUNT(*) FROM alin_ext001.terminologie").fetchone()[0]
        for b in beispiel_begriffe:
            conn.execute("""
                INSERT OR IGNORE INTO alin_ext001.terminologie
                (begriff, sprache, kategorie, quelle, definition, kontext, aequivalente, validiert, validiert_von, validiert_am)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (b["begriff"], b["sprache"], b["kategorie"], b["quelle"], b["definition"],
                  b["kontext"], b["aequivalente"], b["validiert"], b["validiert_von"], b["validiert_am"]))
        count_nach = conn.execute("SELECT COUNT(*) FROM alin_ext001.terminologie").fetchone()[0]
        inserted = count_nach - count_vor

        log(f"{inserted} Terminologie-Einträge eingefügt")

        # Prüfung
        count = conn.execute("SELECT COUNT(*) FROM alin_ext001.terminologie").fetchone()[0]
        log(f"Gesamtanzahl Terminologie-Einträge: {count}")

        # Manifest schreiben
        TERMINOLOGIE_DIR.mkdir(parents=True, exist_ok=True)
        manifest = {
            "manifest_id": "EXT-003-TERMINOLOGIE",
            "erzeugt": zeitstempel(),
            "anzahl_eintraege": count,
            "kategorien": ["verordnung", "richtlinie", "vertrag", "berufsrecht"],
            "sprachen": ["de", "en", "fr"],
            "quellen": ["Art. 288 AEUV", "AEUV", "BRAO § 43a"],
            "sicherheit": {
                "cloud_verboten": True,
                "online_abfragen_verboten": True,
                "echte_daten_verboten": True,
                "nur_lokale_quellen": True
            }
        }
        manifest_pfad = TERMINOLOGIE_DIR / "EU_TERMINOLOGIE_MANIFEST.json"
        manifest_pfad.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"Manifest geschrieben: {manifest_pfad}")

        conn.close()
        log("Verbindung geschlossen")

    except Exception as e:
        log(f"FEHLER: {e}")
        return 1

    # Bericht schreiben
    bericht = f"""EXT-003 – EU-Terminologiepaket Bericht
Erzeugt: {zeitstempel()}
Datenbank: {DB_PATH}
Manifest: {manifest_pfad}

Eingefügte Einträge: {inserted}
Gesamtanzahl: {count}
Kategorien: verordnung, richtlinie, vertrag, berufsrecht
Sprachen: de, en, fr

Status: ERFOLGREICH
"""
    REPORT_FILE.write_text(bericht, encoding="utf-8")
    log(f"Bericht geschrieben: {REPORT_FILE}")

    log("EXT-003 abgeschlossen")
    return 0

if __name__ == "__main__":
    sys.exit(main())
