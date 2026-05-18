#!/usr/bin/env python3
"""
EXT-002 – PaddleOCR / Layout-Analyse

Ziel:
Vorbereitung der OCR-Strecke mit PaddleOCR fuer komplexe Layouts.
Da PaddleOCR aktuell nicht installiert ist, erzeugt dieser Runner:
1. Synthetische OCR/Layout-Daten in DuckDB (Tabelle ocr_ergebnisse)
2. Ein Offline-Installations-Skript fuer PaddleOCR
3. Eine Layout-Analyse-Stub-Datei

Sicherheit:
- Kein Cloud-OCR-Service
- Keine Internetverbindung waehrend OCR
- Nur lokale PaddleOCR-Modelle
- Keine echten Mandantendokumente
- Nur synthetische Testdaten
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "Database" / "DuckDB"
DB_PATH = DB_DIR / "alin_local.duckdb"
REPORT_FILE = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "EXT002_PADDLEOCR_LAYOUT_BERICHT.txt"
CONFIG_FILE = BASE_DIR / "Config" / "ext002_paddleocr_layout_v1.json"
INSTALL_DIR = BASE_DIR / "ALIN_Neustart_Core" / "09_Toolbibliothek" / "01_Download_Quellen"
INSTALL_SCRIPT = INSTALL_DIR / "PADDLEOCR_INSTALL.ps1"
LAYOUT_STUB = BASE_DIR / "ALIN_Neustart_Core" / "09_Toolbibliothek" / "02_PaddleOCR_Stub" / "alin_paddleocr_layout.py"

def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")

def log(msg: str) -> None:
    print(f"[{zeitstempel()}] {msg}")

def paddleocr_verfuegbar() -> bool:
    try:
        import paddleocr
        return True
    except ImportError:
        return False

def erzeuge_installationsskript() -> None:
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    script = '''# PaddleOCR Offline-Installation (vorbereitet fuer manuelle Ausfuehrung)
# Achtung: Erfordert Internet fuer ersten Download, danach offline-faehig
$ErrorActionPreference = "Stop"
$ProjektPython = "I:\\KI_Legal_Project\\Tools\\Python312\\python.exe"

Write-Host "PaddleOCR wird installiert ..."

# 1) PaddlePaddle CPU
& $ProjektPython -m pip install paddlepaddle==2.6.2 --no-deps -f https://www.paddlepaddle.org.cn/whl/windows/mkl/avx/stable.html

# 2) PaddleOCR
& $ProjektPython -m pip install paddleocr==2.7.3

# 3) LayoutParser (optional, fuer Layout-Analyse)
& $ProjektPython -m pip install layoutparser

Write-Host "PaddleOCR Installation abgeschlossen."
Write-Host "Modelle werden beim ersten Start automatisch heruntergeladen."
Write-Host "Bitte stellen Sie sicher, dass die Lizenzbedingungen von PaddleOCR eingehalten werden."
'''
    INSTALL_SCRIPT.write_text(script, encoding="utf-8")
    log(f"Installations-Skript erzeugt: {INSTALL_SCRIPT}")

def erzeuge_layout_stub() -> None:
    stub_dir = LAYOUT_STUB.parent
    stub_dir.mkdir(parents=True, exist_ok=True)
    stub_code = '''#!/usr/bin/env python3
"""ALIN PaddleOCR Layout-Analyse – Stub

Diese Datei wird aktiviert, sobald PaddleOCR installiert ist.
Sie enthaelt die Layout-Analyse-Pipeline fuer ALIN.
"""

from pathlib import Path

# Stub: Funktionen werden implementiert, sobald PaddleOCR verfuegbar ist
def analyse_layout(pdf_pfad: Path) -> dict:
    """Analysiert das Layout einer PDF-Seite mit PaddleOCR."""
    raise NotImplementedError("PaddleOCR nicht installiert. Bitte PADDLEOCR_INSTALL.ps1 ausfuehren.")

def erkenne_tabellen(ocr_ergebnis: dict) -> list[dict]:
    """Erkennt Tabellen aus OCR-Ergebnissen."""
    raise NotImplementedError("PaddleOCR nicht installiert.")

def erkenne_spalten(ocr_ergebnis: dict) -> list[dict]:
    """Erkennt Spalten aus OCR-Ergebnissen."""
    raise NotImplementedError("PaddleOCR nicht installiert.")

if __name__ == "__main__":
    print("PaddleOCR Layout-Analyse Stub – noch nicht aktiv.")
'''
    LAYOUT_STUB.write_text(stub_code, encoding="utf-8")
    log(f"Layout-Stub erzeugt: {LAYOUT_STUB}")

def erzeuge_synthetische_ocr_daten() -> int:
    conn = duckdb.connect(str(DB_PATH))
    # Pruefen, ob Dokumente existieren
    doc_rows = conn.execute("SELECT dokument_id FROM alin_ext001.dokumente LIMIT 1").fetchall()
    if not doc_rows:
        log("WARNUNG: Keine Dokumente in der Datenbank. Erzeuge synthetisches Dokument.")
        conn.execute("""
            INSERT INTO alin_ext001.dokumente (dateiname, dateipfad, mime_typ, sprache_erkannt, status)
            VALUES ('synthetisch_test.pdf', '/tmp/synthetisch_test.pdf', 'application/pdf', 'de', 'importiert')
        """)
        doc_rows = conn.execute("SELECT dokument_id FROM alin_ext001.dokumente LIMIT 1").fetchall()
    dokument_id = doc_rows[0][0]
    log(f"Verwende dokument_id: {dokument_id}")

    count_vor = conn.execute("SELECT COUNT(*) FROM alin_ext001.ocr_ergebnisse WHERE dokument_id = ?", (dokument_id,)).fetchone()[0]

    # Synthetische OCR-Ergebnisse fuer Seite 1 (Schema: ocr_ergebnisse)
    beispiele = [
        {
            "seite_nr": 1,
            "ocr_engine": "paddleocr",
            "roh_text": "Kanzlei Muster & Partner | Amtsgericht Musterstadt\\nBetr.: Mandatsuebernahme zur Vertretung im Verfahren AZ 123/45",
            "strukturiertes_text": json.dumps({
                "blocks": [
                    {"typ": "kopfzeile", "text": "Kanzlei Muster & Partner | Amtsgericht Musterstadt", "bbox": [50, 30, 550, 60]},
                    {"typ": "text", "text": "Betr.: Mandatsuebernahme zur Vertretung im Verfahren AZ 123/45", "bbox": [50, 100, 500, 130]},
                    {"typ": "tabelle", "text": "Tabelle 1: Kostenaufstellung\\nPosition 1: 500,00 EUR\\nPosition 2: 1.200,00 EUR", "bbox": [50, 200, 400, 350], "zeilen": 3, "spalten": 2},
                    {"typ": "spalte", "text": "Rechtsgrundlage: § 43a BRAO, § 81 BRVG", "bbox": [50, 400, 250, 500]},
                    {"typ": "fussnote", "text": "1 Siehe BGH, Urteil vom 01.01.2024 - Az. IV ZR 123/23", "bbox": [50, 700, 500, 720]},
                    {"typ": "fusszeile", "text": "Seite 1 von 5 | Vertraulich", "bbox": [50, 750, 550, 780]},
                ]
            }),
            "konfidenz_score": 0.94,
            "verarbeitungs_zeit_ms": 1200,
            "sprache": "de",
        },
    ]

    for b in beispiele:
        conn.execute("""
            INSERT INTO alin_ext001.ocr_ergebnisse
            (dokument_id, seite_nr, ocr_engine, roh_text, strukturiertes_text, konfidenz_score, verarbeitungs_zeit_ms, sprache)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (dokument_id, b["seite_nr"], b["ocr_engine"], b["roh_text"],
              b["strukturiertes_text"], b["konfidenz_score"], b["verarbeitungs_zeit_ms"], b["sprache"]))

    count_nach = conn.execute("SELECT COUNT(*) FROM alin_ext001.ocr_ergebnisse WHERE dokument_id = ?", (dokument_id,)).fetchone()[0]
    inserted = count_nach - count_vor
    conn.close()
    log(f"{inserted} synthetische OCR-Ergebnisse eingefuegt")
    return inserted

def main() -> int:
    log("EXT-002 – PaddleOCR / Layout-Analyse gestartet")

    if not DB_PATH.exists():
        log(f"FEHLER: DuckDB-Datenbank nicht gefunden: {DB_PATH}")
        return 1

    paddle_ok = paddleocr_verfuegbar()
    if paddle_ok:
        log("PaddleOCR ist installiert")
    else:
        log("WARNUNG: PaddleOCR nicht installiert – erzeuge Installations-Skript und Stub")
        erzeuge_installationsskript()
        erzeuge_layout_stub()

    try:
        inserted = erzeuge_synthetische_ocr_daten()
    except Exception as e:
        log(f"FEHLER bei OCR-Datenerzeugung: {e}")
        return 1

    # Bericht
    bericht = f"""EXT-002 – PaddleOCR / Layout-Analyse Bericht
Erzeugt: {zeitstempel()}
Datenbank: {DB_PATH}
PaddleOCR verfuegbar: {paddle_ok}

Synthetische OCR-Ergebnisse eingefuegt: {inserted}
Block-Typen: kopfzeile, text, tabelle, spalte, fussnote, fusszeile

Installations-Skript: {INSTALL_SCRIPT}
Layout-Stub: {LAYOUT_STUB}

Status: ERFOLGREICH (Infrastruktur vorbereitet)
"""
    REPORT_FILE.write_text(bericht, encoding="utf-8")
    log(f"Bericht geschrieben: {REPORT_FILE}")

    log("EXT-002 abgeschlossen")
    return 0

if __name__ == "__main__":
    sys.exit(main())
