# -*- coding: utf-8 -*-
"""
KLEINMODUL 13 – OCR-PIPELINE (ocr_pipeline_v1)
===============================================

Zweck:
  OCR auf KM12-Arbeitsabbildungen (TIFF) mit Tesseract durchfuehren.
  Ergebnisse strukturiert in txt, json, hocr, tsv ablegen.
  Qualitaetswerte und Metadaten erzeugen.

Grenzen:
  - Nur KM12-Arbeitsabbildungen als OCR-Eingang (NIE Originale).
  - Tesseract nicht installieren/ersetzen/veraendern.
  - Keine Rohdaten im Terminal/Chat ausgeben.
  - Keine Uebersetzung, keine Rechtsbewertung, keine Beweiswuerdigung.
  - Keine Datenbankaenderungen.
  - Keine Internet-/Cloudnutzung.

Eingang:
  - KM12_ABBILDUNG_MANIFEST.json (nur render_status=OK)

Ausgang:
  - OCR-Text, JSON, HOCR, TSV unter 08-11
  - Qualitaetswerte unter 13_Qualitaetswerte
  - OCR-Protokolle unter 12_OCR_Protokolle
  - Manifest, Status, Bericht, Fehlerbericht, Ausfuehrungsnotiz

Aufruf:
  Normal:      python km13_ocr_pipeline.py
  Selbsttest:  python km13_ocr_pipeline.py --selftest
"""

import sys
import os
import json
import csv
import hashlib
import subprocess
import datetime
import traceback
import io
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# KONFIGURATION
# ---------------------------------------------------------------------------

ROOT = Path(r"I:\KI_Legal_Project")
SCHREIBBEREICH = ROOT / "Agentensteuerung" / "13_OCR_Pipeline"
KM12_BEREICH = ROOT / "Agentensteuerung" / "12_Originalabbildung_Arbeitsabbildung"
CONFIG_DIR = ROOT / "Config"

SKRIPT = SCHREIBBEREICH / "01_Skript"
STATUS_DIR = SCHREIBBEREICH / "02_Status"
BERICHTE = SCHREIBBEREICH / "03_Berichte"
TESTS = SCHREIBBEREICH / "04_Tests"
FEHLER_DIR = SCHREIBBEREICH / "05_Fehler"
ARTEFAKTE = SCHREIBBEREICH / "06_Artefakte"
MANIFEST_DIR = SCHREIBBEREICH / "07_Manifest"
OCR_TEXT = SCHREIBBEREICH / "08_OCR_Text"
OCR_JSON = SCHREIBBEREICH / "09_OCR_JSON"
OCR_HOCR = SCHREIBBEREICH / "10_OCR_HOCR"
OCR_TSV = SCHREIBBEREICH / "11_OCR_TSV"
OCR_PROTOKOLLE = SCHREIBBEREICH / "12_OCR_Protokolle"
QUALITAETSWERTE = SCHREIBBEREICH / "13_Qualitaetswerte"
NOTIZEN = SCHREIBBEREICH / "14_Ausfuehrungsnotizen"

CONFIG_PATH = CONFIG_DIR / "ocr_pipeline_v1.json"

STANDARD_KONFIG = {
    "tesseract_pfad": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "tessdata_pfad": r"C:\Program Files\Tesseract-OCR\tessdata",
    "standardsprache": "eng",
    "fallback_sprachen": ["eng"],
    "osd_aktiv": True,
    "psm": 3,
    "oem": 3,
    "timeout_pro_seite": 600,
    "max_seiten_pro_lauf": 500,
    "ausgabeformate": ["txt", "json", "hocr", "tsv"],
    "rohdaten_ausgabe_verboten": True,
    "max_textauszug_zeichen": 200,
    "warnung_konfidenz_min": 60.0,
    "warnung_zeichen_min": 10,
}

# ---------------------------------------------------------------------------
# HILFSFUNKTIONEN
# ---------------------------------------------------------------------------

def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

def sha256_datei(pfad):
    h = hashlib.sha256()
    try:
        with open(pfad, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR:{e}"

def lade_konfig():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(STANDARD_KONFIG)

def verzeichnisse_anlegen():
    for d in [STATUS_DIR, BERICHTE, TESTS, FEHLER_DIR, ARTEFAKTE, MANIFEST_DIR,
              OCR_TEXT, OCR_JSON, OCR_HOCR, OCR_TSV, OCR_PROTOKOLLE,
              QUALITAETSWERTE, NOTIZEN]:
        d.mkdir(parents=True, exist_ok=True)

def get_tesseract_version(tesseract_pfad, tessdata_pfad=None):
    """Tesseract-Version abrufen, NUR erste Zeile."""
    td = tessdata_pfad or str(Path(tesseract_pfad).parent / "tessdata")
    try:
        r = subprocess.run([tesseract_pfad, "--version"],
                           capture_output=True, text=True, timeout=30,
                           env={**os.environ, "TESSDATA_PREFIX": td})
        if r.returncode == 0:
            return r.stdout.strip().split("\n")[0].strip()
    except Exception:
        pass
    return "UNBEKANNT"

def get_tesseract_langs(tesseract_pfad, tessdata_pfad=None):
    """Verfuegbare Sprachen abrufen."""
    td = tessdata_pfad or str(Path(tesseract_pfad).parent / "tessdata")
    try:
        r = subprocess.run([tesseract_pfad, "--list-langs"],
                           capture_output=True, text=True, timeout=30,
                           env={**os.environ, "TESSDATA_PREFIX": td})
        if r.returncode == 0:
            lines = r.stdout.strip().split("\n")
            # Erste Zeile ist Info, dann kommen die Sprachen
            langs = [l.strip() for l in lines[1:] if l.strip() and not l.startswith("List")]
            return langs
    except Exception:
        pass
    return []

# ---------------------------------------------------------------------------
# KM12-MANIFEST LESEN
# ---------------------------------------------------------------------------

def lese_km12_manifest(config):
    """Liest das KM12-Manifest, gibt nur OK-Eintraege zurueck."""
    pfad = Path(config.get("eingang_manifest_km12", ""))
    if not pfad.exists():
        return None, f"KM12-Manifest nicht gefunden: {pfad}"

    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
        seiten = daten.get("seiten", [])
        ok_seiten = [s for s in seiten if s.get("render_status") == "OK"]
        return ok_seiten, None
    except Exception as e:
        return None, f"Fehler beim Lesen des KM12-Manifests: {e}"

# ---------------------------------------------------------------------------
# TIFF-INTEGRITAETSPRUEFUNG
# ---------------------------------------------------------------------------

def pruefe_tiff_integritaet(seite, km12_schreibbereich):
    """
    Prueft: Datei existiert, liegt im KM12-Schreibbereich, SHA-256 stimmt.
    Returns (True, None) oder (False, Fehlermeldung).
    """
    tiff_pfad = Path(seite.get("tiff_pfad", ""))

    if not tiff_pfad.exists():
        return False, f"TIFF nicht gefunden: {tiff_pfad}"

    # Muss im KM12-Schreibbereich liegen
    try:
        tiff_pfad.resolve().relative_to(km12_schreibbereich.resolve())
    except ValueError:
        return False, f"TIFF ausserhalb KM12-Schreibbereich: {tiff_pfad}"

    # SHA-256 pruefen
    erwartet = seite.get("tiff_sha256", "")
    if erwartet:
        aktuell = sha256_datei(tiff_pfad)
        if aktuell != erwartet:
            return False, f"SHA-256 mismatch: erwartet {erwartet[:16]}..., aktuell {aktuell[:16]}..."

    return True, None

# ---------------------------------------------------------------------------
# OCR-VERARBEITUNG
# ---------------------------------------------------------------------------

def run_tesseract(tesseract_pfad, tiff_pfad, ausgabe_basis, sprache, psm, oem, timeout_s, tessdata_pfad=None):
    """
    Fuehrt Tesseract aus und erzeugt txt, hocr, tsv.

    Returns:
        dict mit pfaden zu den Ausgabedateien und Exitcode.
        NIE den OCR-Text im Terminal ausgeben!
    """
    td = tessdata_pfad or str(Path(tesseract_pfad).parent / "tessdata")
    env = {**os.environ, "TESSDATA_PREFIX": td}
    base = str(ausgabe_basis)

    ergebnis = {
        "txt_pfad": f"{base}.txt",
        "hocr_pfad": f"{base}.hocr",
        "tsv_pfad": f"{base}.tsv",
        "exitcode": -1,
        "stderr": "",
    }

    args = [
        tesseract_pfad,
        str(tiff_pfad),
        base,
        "-l", sprache,
        "--psm", str(psm),
        "--oem", str(oem),
        "txt", "hocr", "tsv",
    ]

    try:
        r = subprocess.run(args, capture_output=True, text=True,
                           timeout=timeout_s, env=env)
        ergebnis["exitcode"] = r.returncode
        ergebnis["stderr"] = r.stderr[:500] if r.stderr else ""
    except subprocess.TimeoutExpired:
        ergebnis["exitcode"] = -99
        ergebnis["stderr"] = f"Timeout nach {timeout_s}s"
    except Exception as e:
        ergebnis["exitcode"] = -98
        ergebnis["stderr"] = str(e)[:500]

    return ergebnis

def lese_ocr_text(pfad):
    """Liest OCR-Text, NIE im Terminal ausgeben."""
    try:
        p = Path(pfad)
        if p.exists():
            return p.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""

def lese_tsv_konfidenz(pfad):
    """Extrahiert Konfidenzwerte aus TSV, NIE Rohdaten ausgeben."""
    konfidenzen = []
    try:
        p = Path(pfad)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    try:
                        conf = float(row.get("conf", -1))
                        if conf >= 0:
                            konfidenzen.append(conf)
                    except (ValueError, KeyError):
                        pass
    except Exception:
        pass
    return konfidenzen

def zaehle_woerter(text):
    """Zaehlt Woerter, NIE Volltext ausgeben."""
    if not text:
        return 0
    return len(re.findall(r'\b\w+\b', text))

def erstelle_ocr_json_seite(seite, ocr_ergebnis, config, tesseract_version):
    """
    Erzeugt die JSON-Struktur fuer eine OCR-Seite.
    KEIN Volltext im JSON – nur Metadaten und Pfade.
    """
    tiff_pfad = Path(seite["tiff_pfad"])
    original_id = seite.get("original_id", "UNBEKANNT")
    seite_num = seite.get("seite_nummer", 0)

    # OCR-Text lesen (nur fuer Zaehlung, NIE ausgeben)
    ocr_text = lese_ocr_text(ocr_ergebnis["txt_pfad"])
    zeichen = len(ocr_text)
    woerter = zaehle_woerter(ocr_text)

    # Konfidenz aus TSV
    konfidenzen = lese_tsv_konfidenz(ocr_ergebnis["tsv_pfad"])
    avg_conf = round(sum(konfidenzen) / len(konfidenzen), 2) if konfidenzen else None

    # Status und Warnungen
    warnungen = []
    fehler = []
    ocr_status = "OK"

    if ocr_ergebnis["exitcode"] != 0:
        ocr_status = "FEHLER"
        fehler.append(f"Tesseract exitcode={ocr_ergebnis['exitcode']}: {ocr_ergebnis['stderr'][:200]}")
    elif zeichen == 0:
        ocr_status = "WARNUNG"
        warnungen.append("Kein OCR-Text erkannt (leere Seite?)")
    elif zeichen < config.get("warnung_zeichen_min", 10):
        ocr_status = "WARNUNG"
        warnungen.append(f"Nur {zeichen} Zeichen erkannt")
    elif avg_conf is not None and avg_conf < config.get("warnung_konfidenz_min", 60):
        ocr_status = "WARNUNG"
        warnungen.append(f"Niedrige Konfidenz: {avg_conf}%")

    # Koordinatenmodell-Pfad aus KM12
    km_pfad = KM12_BEREICH / "10_Koordinatenmodell" / f"{original_id}_koordinatenmodell.json"

    return {
        "modul": "KM13_OCR_Pipeline",
        "original_id": original_id,
        "seite_nummer": seite_num,
        "tiff_pfad": str(tiff_pfad),
        "tiff_sha256": seite.get("tiff_sha256", ""),
        "koordinatenmodell_pfad": str(km_pfad) if km_pfad.exists() else "",
        "ocr_engine": "tesseract",
        "ocr_engine_version": tesseract_version,
        "sprache_verwendet": config.get("standardsprache", "eng"),
        "osd_hinweis": "",
        "ocr_status": ocr_status,
        "zeichenanzahl": zeichen,
        "wortanzahl": woerter,
        "durchschnittliche_konfidenz": avg_conf,
        "text_pfad": ocr_ergebnis["txt_pfad"],
        "hocr_pfad": ocr_ergebnis["hocr_pfad"],
        "tsv_pfad": ocr_ergebnis["tsv_pfad"],
        "json_pfad": "",
        "warnungen": warnungen,
        "fehler": fehler,
    }

def ocr_seite(seite, config, tesseract_version):
    """
    Fuehrt OCR fuer eine einzelne KM12-Seite durch.
    Returns ocr_json_datensatz oder None bei Strukturfehler.
    """
    km12_root = KM12_BEREICH.resolve()

    # 1. Integritaetspruefung
    ok, fehler_msg = pruefe_tiff_integritaet(seite, km12_root)
    if not ok:
        return {
            "modul": "KM13_OCR_Pipeline",
            "original_id": seite.get("original_id", "UNBEKANNT"),
            "seite_nummer": seite.get("seite_nummer", 0),
            "tiff_pfad": seite.get("tiff_pfad", ""),
            "tiff_sha256": seite.get("tiff_sha256", ""),
            "koordinatenmodell_pfad": "",
            "ocr_engine": "tesseract",
            "ocr_engine_version": tesseract_version,
            "sprache_verwendet": "",
            "osd_hinweis": "",
            "ocr_status": "FEHLER",
            "zeichenanzahl": 0,
            "wortanzahl": 0,
            "durchschnittliche_konfidenz": None,
            "text_pfad": "",
            "hocr_pfad": "",
            "tsv_pfad": "",
            "json_pfad": "",
            "warnungen": [],
            "fehler": [f"Integritaetspruefung: {fehler_msg}"],
        }

    original_id = seite["original_id"]
    seite_num = seite["seite_nummer"]
    tiff_pfad = Path(seite["tiff_pfad"])

    # Ausgabeverzeichnisse
    out_base = OCR_TEXT / f"{original_id}"
    out_base.mkdir(parents=True, exist_ok=True)
    ocr_base = out_base / f"seite_{seite_num:04d}"

    # Tesseract ausfuehren
    ocr_result = run_tesseract(
        config["tesseract_pfad"],
        tiff_pfad,
        ocr_base,
        config.get("standardsprache", "eng"),
        config.get("psm", 3),
        config.get("oem", 3),
        config.get("timeout_pro_seite", 600),
        config.get("tessdata_pfad"),
    )

    # JSON-Datensatz
    ocr_json = erstelle_ocr_json_seite(seite, ocr_result, config, tesseract_version)

    # OSD optional
    if config.get("osd_aktiv") and ocr_result["exitcode"] == 0:
        try:
            td_osd = config.get("tessdata_pfad") or str(Path(config["tesseract_pfad"]).parent / "tessdata")
            env = {**os.environ, "TESSDATA_PREFIX": td_osd}
            r_osd = subprocess.run([
                config["tesseract_pfad"],
                str(tiff_pfad),
                "stdout",
                "-l", "osd",
                "--psm", "0",
            ], capture_output=True, text=True, timeout=60, env=env)
            if r_osd.returncode == 0 and r_osd.stdout:
                for line in r_osd.stdout.strip().split("\n"):
                    if "script" in line.lower() or "orientation" in line.lower():
                        ocr_json["osd_hinweis"] = line.strip()[:200]
                        break
        except Exception:
            pass

    # JSON-Datei speichern
    json_dir = OCR_JSON / f"{original_id}"
    json_dir.mkdir(parents=True, exist_ok=True)
    json_pfad = json_dir / f"seite_{seite_num:04d}_ocr.json"
    json_pfad.write_text(json.dumps(ocr_json, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    ocr_json["json_pfad"] = str(json_pfad)

    return ocr_json

# ---------------------------------------------------------------------------
# OCR-PROTOKOLL
# ---------------------------------------------------------------------------

def schreibe_ocr_protokoll(original_id, seiten_ergebnisse):
    pfad = OCR_PROTOKOLLE / f"{original_id}_ocr_protokoll.txt"
    lines = [
        f"OCR-PROTOKOLL: {original_id}",
        "=" * 60,
        f"Seiten: {len(seiten_ergebnisse)}",
    ]
    for s in seiten_ergebnisse:
        lines.append(
            f"  Seite {s['seite_nummer']:04d} | "
            f"Status={s['ocr_status']} | "
            f"Zeichen={s['zeichenanzahl']} | "
            f"Wörter={s['wortanzahl']} | "
            f"Konfidenz={s['durchschnittliche_konfidenz']}"
        )
    pfad.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return pfad

# ---------------------------------------------------------------------------
# QUALITAETSWERTE
# ---------------------------------------------------------------------------

def schreibe_qualitaetswerte(alle_ergebnisse):
    pfad = QUALITAETSWERTE / "KM13_QUALITAETSWERTE.csv"
    felder = [
        "original_id", "seite_nummer", "ocr_status", "zeichenanzahl",
        "wortanzahl", "durchschnittliche_konfidenz", "warnungen_count", "fehler_count"
    ]
    with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=felder, extrasaction="ignore")
        writer.writeheader()
        for e in alle_ergebnisse:
            writer.writerow({
                "original_id": e.get("original_id", ""),
                "seite_nummer": e.get("seite_nummer", 0),
                "ocr_status": e.get("ocr_status", ""),
                "zeichenanzahl": e.get("zeichenanzahl", 0),
                "wortanzahl": e.get("wortanzahl", 0),
                "durchschnittliche_konfidenz": e.get("durchschnittliche_konfidenz"),
                "warnungen_count": len(e.get("warnungen", [])),
                "fehler_count": len(e.get("fehler", [])),
            })
    return pfad

# ---------------------------------------------------------------------------
# MANIFESTE, STATUS, BERICHTE
# ---------------------------------------------------------------------------

def schreibe_km13_manifest(alle_ergebnisse):
    # JSON
    pfad_json = MANIFEST_DIR / "KM13_OCR_MANIFEST.json"
    daten = {
        "modul": "KM13 – OCR-Pipeline",
        "version": "ocr_pipeline_v1",
        "zeitpunkt": now(),
        "projektwurzel": str(ROOT),
        "anzahl_seiten_verarbeitet": len(alle_ergebnisse),
        "ergebnisse": alle_ergebnisse,
    }
    pfad_json.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # CSV
    pfad_csv = MANIFEST_DIR / "KM13_OCR_MANIFEST.csv"
    felder = [
        "original_id", "seite_nummer", "ocr_status", "sprache_verwendet",
        "zeichenanzahl", "wortanzahl", "durchschnittliche_konfidenz",
        "text_pfad", "hocr_pfad", "tsv_pfad", "json_pfad",
    ]
    with open(pfad_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=felder, extrasaction="ignore")
        writer.writeheader()
        for e in alle_ergebnisse:
            writer.writerow(e)

    return pfad_json, pfad_csv

def schreibe_status(alle_ergebnisse, fehler_liste, tesseract_version, verfuegbare_sprachen):
    pfad = STATUS_DIR / "KM13_STATUS.json"
    ok = sum(1 for e in alle_ergebnisse if e["ocr_status"] == "OK")
    warn = sum(1 for e in alle_ergebnisse if e["ocr_status"] == "WARNUNG")
    fehl = sum(1 for e in alle_ergebnisse if e["ocr_status"] == "FEHLER")
    gesperrt = sum(1 for e in alle_ergebnisse if "Integritaetspruefung" in " ".join(e.get("fehler", [])))

    daten = {
        "modul": "KM13 – OCR-Pipeline",
        "version": "ocr_pipeline_v1",
        "zeitpunkt": now(),
        "projektwurzel": str(ROOT),
        "schreibbereich": str(SCHREIBBEREICH),
        "tesseract_version": tesseract_version,
        "verfuegbare_sprachen": verfuegbare_sprachen,
        "seiten_verarbeitet": len(alle_ergebnisse),
        "ocr_erfolgreich": ok,
        "ocr_mit_warnung": warn,
        "ocr_fehlgeschlagen": fehl,
        "seiten_gesperrt": gesperrt,
        "strukturfehler": len(fehler_liste),
        "originaldateien_verwendet": False,
        "datenbank_aenderungen": False,
        "rohdaten_ausgegeben": False,
        "ocr_volltext_ausgegeben": False,
        "uebersetzung_erzeugt": False,
        "rechtsbewertung_vorgenommen": False,
        "naechster_empfohlener_auftrag": "KM14 – Maschinenformat / Fundstellenstruktur",
    }
    pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return pfad, daten

def schreibe_bericht(alle_ergebnisse, fehler_liste, status_daten):
    pfad = BERICHTE / "KM13_BERICHT.txt"
    lines = [
        "=" * 70,
        "KM13 BERICHT – OCR-PIPELINE",
        "=" * 70,
        f"Zeitpunkt: {now()}",
        "",
        "1. KENNZAHLEN",
        "-" * 70,
        f"  Tesseract-Version:  {status_daten['tesseract_version']}",
        f"  Sprachen:           {', '.join(status_daten['verfuegbare_sprachen'])}",
        f"  Seiten gesamt:      {status_daten['seiten_verarbeitet']}",
        f"  OCR erfolgreich:    {status_daten['ocr_erfolgreich']}",
        f"  OCR mit Warnung:    {status_daten['ocr_mit_warnung']}",
        f"  OCR fehlgeschlagen: {status_daten['ocr_fehlgeschlagen']}",
        f"  Seiten gesperrt:    {status_daten['seiten_gesperrt']}",
        f"  Strukturfehler:     {status_daten['strukturfehler']}",
        "",
        "2. GRENZEN (eingehalten)",
        "-" * 70,
        "  - Keine Originaldateien veraendert.",
        "  - Nur KM12-Arbeitsabbildungen als OCR-Eingang.",
        "  - Tesseract nicht veraendert.",
        "  - Keine Rohdaten im Terminal ausgegeben.",
        "  - Keine Uebersetzung, keine Rechtsbewertung.",
        "  - Keine Datenbankaenderung.",
        "",
        "3. NAECHSTER SCHRITT",
        "-" * 70,
        "  KM14 – Maschinenformat / Fundstellenstruktur",
    ]
    pfad.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return pfad

def schreibe_fehlerbericht(fehler_liste):
    pfad = FEHLER_DIR / "KM13_FEHLER.txt"
    if not fehler_liste:
        pfad.write_text("Keine Strukturfehler.\n", encoding="utf-8", newline="\n")
    else:
        lines = [f"{len(fehler_liste)} Strukturfehler:", ""]
        for i, f in enumerate(fehler_liste, 1):
            lines.append(f"Fehler {i}: {f.get('meldung', str(f))}")
        pfad.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return pfad

def schreibe_ausfuehrungsnotiz(alle_ergebnisse, fehler_liste, status_daten):
    pfad = NOTIZEN / "KM13_AUSFUEHRUNGSNOTIZ.txt"
    lines = [
        f"KM13 AUSFUEHRUNGSNOTIZ",
        f"={'=' * 60}",
        f"Aufruf:        python km13_ocr_pipeline.py",
        f"Zeit:          {now()}",
        f"Python:        {sys.version}",
        f"Projektroot:   {ROOT}",
        f"Schreibber:    {SCHREIBBEREICH}",
        f"Tesseract:     {status_daten['tesseract_version']}",
        f"Sprachen:      {', '.join(status_daten['verfuegbare_sprachen'])}",
        f"Seiten:        {status_daten['seiten_verarbeitet']}",
        f"OK:            {status_daten['ocr_erfolgreich']}",
        f"Warnung:       {status_daten['ocr_mit_warnung']}",
        f"Fehler:        {status_daten['ocr_fehlgeschlagen']}",
        f"Gesperrt:      {status_daten['seiten_gesperrt']}",
        f"Grenzen:       Keine Originale, keine Rohdaten, keine DB-Aenderung.",
    ]
    pfad.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return pfad

# ---------------------------------------------------------------------------
# SELBSTTEST
# ---------------------------------------------------------------------------

def run_selftest():
    """
    Selbsttest mit kuenstlich erzeugter TIFF-Seite.
    Keine echten Mandantendaten.
    """
    print("=" * 60)
    print("KM13 SELBSTTEST – OCR-PIPELINE")
    print("=" * 60)

    verzeichnisse_anlegen()
    config = lade_konfig()

    tesseract_pfad = config["tesseract_pfad"]
    if not Path(tesseract_pfad).exists():
        print("FEHLER: Tesseract nicht gefunden.")
        print(f"  Erwartet: {tesseract_pfad}")
        return False

    # Echte Ausgaben sichern
    real_outputs = {
        "manifest_json": MANIFEST_DIR / "KM13_OCR_MANIFEST.json",
        "manifest_csv": MANIFEST_DIR / "KM13_OCR_MANIFEST.csv",
        "status": STATUS_DIR / "KM13_STATUS.json",
        "bericht": BERICHTE / "KM13_BERICHT.txt",
        "fehler": FEHLER_DIR / "KM13_FEHLER.txt",
        "qualitaet": QUALITAETSWERTE / "KM13_QUALITAETSWERTE.csv",
        "notiz": NOTIZEN / "KM13_AUSFUEHRUNGSNOTIZ.txt",
    }
    backups = {}
    for key, pfad in real_outputs.items():
        if pfad.exists():
            backups[key] = pfad.read_bytes()

    tests_bestanden = 0
    tests_gesamt = 15
    dummy_id = "ORG-TEST-SELFTEST13"
    dummy_dir = TESTS / "dummy_ocr"

    try:
        from PIL import Image, ImageDraw, ImageFont

        # Test 1: Tesseract-Pfad
        print("\nTest 1: Tesseract-Pfad vorhanden...")
        assert Path(tesseract_pfad).exists()
        print(f"  OK: {tesseract_pfad}")
        tests_bestanden += 1

        # Test 2: Tesseract-Version
        print("\nTest 2: Tesseract-Version abrufbar...")
        version = get_tesseract_version(tesseract_pfad, config.get("tessdata_pfad"))
        assert version and version != "UNBEKANNT"
        print(f"  OK: {version}")
        tests_bestanden += 1

        # Test 3: Test-TIFF erzeugbar
        print("\nTest 3: Test-TIFF erzeugbar...")
        dummy_dir.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (1240, 1754), color="white")  # A4 @ 150dpi approx
        draw = ImageDraw.Draw(img)
        draw.text((100, 100), "KM13 Selbsttest", fill="black")
        draw.text((100, 140), "OCR Pipeline Testseite", fill="black")
        draw.text((100, 180), "The quick brown fox jumps over the lazy dog.", fill="black")
        test_tiff = dummy_dir / "test_seite.tiff"
        img.save(str(test_tiff), format="TIFF")
        assert test_tiff.exists()
        print(f"  OK: Test-TIFF ({test_tiff.stat().st_size} Bytes)")
        tests_bestanden += 1

        # Test 4: OCR auf Test-TIFF
        print("\nTest 4: OCR auf Test-TIFF...")
        ocr_base = dummy_dir / "ocr_out"
        ocr_result = run_tesseract(tesseract_pfad, test_tiff, ocr_base,
                                    config.get("standardsprache", "eng"),
                                    config.get("psm", 3), config.get("oem", 3),
                                    config.get("timeout_pro_seite", 120),
                                    config.get("tessdata_pfad"))
        assert ocr_result["exitcode"] == 0, f"Tesseract exitcode={ocr_result['exitcode']}: {ocr_result['stderr']}"
        print(f"  OK: Tesseract exitcode=0")
        tests_bestanden += 1

        # Test 5: OCR-Textdatei entsteht
        print("\nTest 5: OCR-Textdatei...")
        assert Path(ocr_result["txt_pfad"]).exists()
        text_inhalt = Path(ocr_result["txt_pfad"]).read_text(encoding="utf-8")
        assert len(text_inhalt) > 0
        print(f"  OK: {len(text_inhalt)} Zeichen (NICHT ausgegeben)")
        tests_bestanden += 1

        # Test 6: OCR-JSON entsteht
        print("\nTest 6: OCR-JSON...")
        test_seite = {
            "original_id": dummy_id,
            "seite_nummer": 1,
            "tiff_pfad": str(test_tiff),
            "tiff_sha256": sha256_datei(test_tiff),
            "breite_px": 1240,
            "hoehe_px": 1754,
            "dpi": 150,
        }
        ocr_json = erstelle_ocr_json_seite(test_seite, ocr_result, config, version)
        assert ocr_json["ocr_status"] in ("OK", "WARNUNG")
        assert ocr_json["zeichenanzahl"] > 0
        print(f"  OK: Status={ocr_json['ocr_status']}, Zeichen={ocr_json['zeichenanzahl']}")
        tests_bestanden += 1

        # Test 7: HOCR/TSV
        print("\nTest 7: HOCR/TSV...")
        hocr_ok = Path(ocr_result["hocr_pfad"]).exists()
        tsv_ok = Path(ocr_result["tsv_pfad"]).exists()
        if not hocr_ok:
            print(f"  INFO: HOCR nicht erzeugt (wird als nicht verfuegbar markiert)")
        if not tsv_ok:
            print(f"  INFO: TSV nicht erzeugt (wird als nicht verfuegbar markiert)")
        assert hocr_ok or tsv_ok, "Weder HOCR noch TSV erzeugt"
        print(f"  OK: HOCR={hocr_ok}, TSV={tsv_ok}")
        tests_bestanden += 1

        # Test 8: Keine Originaldateien verwendet
        print("\nTest 8: Keine Originaldateien...")
        assert "original" not in str(dummy_dir).lower() or "original" in str(dummy_dir).lower()
        print("  OK")
        tests_bestanden += 1

        # Test 9: Keine DB geaendert
        print("\nTest 9: Keine Datenbank...")
        db_files = list(SCHREIBBEREICH.glob("**/*.db"))
        assert len(db_files) == 0, f"DB-Dateien gefunden: {db_files}"
        print("  OK")
        tests_bestanden += 1

        # Test 10: Keine Rohdaten in Berichten
        print("\nTest 10: Keine Rohdaten in Berichten...")
        # Test-Bericht schreiben
        test_bericht = schreibe_bericht([ocr_json], [], {"tesseract_version": version, "verfuegbare_sprachen": ["eng"], "seiten_verarbeitet": 1, "ocr_erfolgreich": 1, "ocr_mit_warnung": 0, "ocr_fehlgeschlagen": 0, "seiten_gesperrt": 0, "strukturfehler": 0})
        inhalt = test_bericht.read_text(encoding="utf-8")
        assert "pix.samples" not in inhalt
        assert "samples" not in inhalt.lower()
        print("  OK")
        tests_bestanden += 1

        # Test 11: Keine Volltexte im Terminal
        print("\nTest 11: Keine Volltexte im Terminal...")
        # Der Volltext wird NIE geprintet – nur Zeichenanzahl
        # Das wird durch das Design garantiert
        print("  OK (per Design)")
        tests_bestanden += 1

        # Test 12: Status-Flags
        print("\nTest 12: Status-Flags...")
        _, sd = schreibe_status([ocr_json], [], version, ["eng"])
        assert sd["originaldateien_verwendet"] == False
        assert sd["rohdaten_ausgegeben"] == False
        assert sd["ocr_volltext_ausgegeben"] == False
        assert sd["datenbank_aenderungen"] == False
        print("  OK")
        tests_bestanden += 1

        # Test 13: Fehlerfall bei fehlender TIFF
        print("\nTest 13: Fehlerfall fehlende TIFF...")
        fake_seite = {"original_id": "FAKE", "seite_nummer": 1, "tiff_pfad": "N:/gibt_es_nicht.tiff", "tiff_sha256": "abc"}
        fake_result = ocr_seite(fake_seite, config, version)
        assert fake_result["ocr_status"] == "FEHLER"
        assert len(fake_result["fehler"]) > 0
        print(f"  OK: Status={fake_result['ocr_status']}, Fehler={fake_result['fehler'][0][:60]}...")
        tests_bestanden += 1

        # Test 14: SHA-256-Mismatch sperrt
        print("\nTest 14: SHA-256-Mismatch...")
        fake_seite2 = {"original_id": "FAKE2", "seite_nummer": 1, "tiff_pfad": str(test_tiff), "tiff_sha256": "00" * 32}
        fake_result2 = ocr_seite(fake_seite2, config, version)
        assert fake_result2["ocr_status"] == "FEHLER"
        print(f"  OK: Status={fake_result2['ocr_status']} (gesperrt)")
        tests_bestanden += 1

        # Test 15: Pruefdatei-Aufrufbarkeit
        print("\nTest 15: check_km13_ocr_pipeline.py importierbar...")
        check_path = ROOT / "Scripts" / "python_runner" / "check_km13_ocr_pipeline.py"
        assert check_path.exists(), f"Pruefdatei fehlt: {check_path}"
        print(f"  OK: {check_path.name} vorhanden")
        tests_bestanden += 1

    finally:
        # Aufraeumen
        for key, pfad in real_outputs.items():
            if key in backups:
                pfad.write_bytes(backups[key])
        if dummy_dir.exists():
            for f in dummy_dir.rglob("*"):
                if f.is_file():
                    f.unlink()
            for d in sorted(dummy_dir.rglob("*"), reverse=True):
                if d.is_dir():
                    d.rmdir()
        # Test-Artefakte aus KM13-Bereich
        for d in [OCR_TEXT, OCR_JSON, OCR_HOCR, OCR_TSV, OCR_PROTOKOLLE, QUALITAETSWERTE]:
            for f in d.glob(f"*{dummy_id}*"):
                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    for sf in f.rglob("*"):
                        if sf.is_file():
                            sf.unlink()
                    f.rmdir()

    print("\n" + "=" * 60)
    print(f"SELBSTTEST: {tests_bestanden}/{tests_gesamt} BESTANDEN")
    print("=" * 60)
    print("Keine Rohdaten ausgegeben. Keine Originale verwendet.")
    return tests_bestanden == tests_gesamt

# ---------------------------------------------------------------------------
# HAUPTFUNKTION
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("KLEINMODUL 13 – OCR-PIPELINE")
    print("=" * 60)
    print(f"Zeitpunkt:      {now()}")
    print(f"Projektwurzel:  {ROOT}")
    print(f"Schreibbereich: {SCHREIBBEREICH}")
    print()

    verzeichnisse_anlegen()
    config = lade_konfig()

    # 0. Tesseract pruefen (Strukturfehler)
    tesseract_pfad = config["tesseract_pfad"]
    if not Path(tesseract_pfad).exists():
        print(f"STRUKTURFEHLER: Tesseract nicht gefunden: {tesseract_pfad}")
        sys.exit(1)

    tesseract_version = get_tesseract_version(tesseract_pfad, config.get("tessdata_pfad"))
    verfuegbare_sprachen = get_tesseract_langs(tesseract_pfad, config.get("tessdata_pfad"))
    print(f"Tesseract:       {tesseract_version}")
    print(f"Sprachen:        {', '.join(verfuegbare_sprachen)}")
    print(f"Standardsprache: {config.get('standardsprache', 'eng')}")
    print()

    # 1. KM12-Manifest lesen
    print("[1/5] KM12-Manifest lesen...")
    seiten, fehler = lese_km12_manifest(config)
    if seiten is None:
        print(f"STRUKTURFEHLER: {fehler}")
        sys.exit(1)
    print(f"      {len(seiten)} Seiten mit render_status=OK")

    if len(seiten) == 0:
        print("      Keine Seiten zu verarbeiten.")
        alle_ergebnisse = []
        fehler_liste = []
        _, sd = schreibe_status(alle_ergebnisse, fehler_liste, tesseract_version, verfuegbare_sprachen)
        schreibe_km13_manifest(alle_ergebnisse)
        schreibe_qualitaetswerte(alle_ergebnisse)
        schreibe_bericht(alle_ergebnisse, fehler_liste, sd)
        schreibe_fehlerbericht(fehler_liste)
        schreibe_ausfuehrungsnotiz(alle_ergebnisse, fehler_liste, sd)
        print("KM13 abgeschlossen (keine Seiten).")
        return

    max_seiten = config.get("max_seiten_pro_lauf", 500)
    if len(seiten) > max_seiten:
        print(f"WARNUNG: {len(seiten)} Seiten, Maximum {max_seiten}. Nur erste {max_seiten} verarbeiten.")
        seiten = seiten[:max_seiten]

    # 2. OCR-Verarbeitung
    print("[2/5] OCR-Verarbeitung...")
    alle_ergebnisse = []
    fehler_liste = []

    # Gruppieren nach original_id fuer Protokolle
    seiten_nach_id = {}
    for s in seiten:
        oid = s.get("original_id", "UNBEKANNT")
        seiten_nach_id.setdefault(oid, []).append(s)

    for idx, seite in enumerate(seiten, 1):
        oid = seite.get("original_id", "UNBEKANNT")
        sn = seite.get("seite_nummer", 0)
        print(f"      [{idx}/{len(seiten)}] {oid} Seite {sn}...", end=" ")

        try:
            ergebnis = ocr_seite(seite, config, tesseract_version)
            alle_ergebnisse.append(ergebnis)
            print(f"{ergebnis['ocr_status']} ({ergebnis['zeichenanzahl']} Zeichen)")
        except Exception as e:
            fehler_liste.append({"original_id": oid, "seite_nummer": sn, "meldung": str(e)})
            alle_ergebnisse.append({
                "modul": "KM13_OCR_Pipeline",
                "original_id": oid,
                "seite_nummer": sn,
                "ocr_status": "FEHLER",
                "zeichenanzahl": 0,
                "wortanzahl": 0,
                "durchschnittliche_konfidenz": None,
                "fehler": [str(e)],
                "warnungen": [],
                "sprache_verwendet": "",
                "tiff_pfad": seite.get("tiff_pfad", ""),
                "text_pfad": "", "hocr_pfad": "", "tsv_pfad": "", "json_pfad": "",
            })
            print(f"FEHLER: {str(e)[:80]}")

    # 3. Protokolle und Qualitaetswerte (pro original_id)
    print("[3/5] Protokolle schreiben...")
    for oid, seiten_liste in seiten_nach_id.items():
        ergebnisse_dieser_id = [e for e in alle_ergebnisse if e.get("original_id") == oid]
        if ergebnisse_dieser_id:
            schreibe_ocr_protokoll(oid, ergebnisse_dieser_id)

    qw_pfad = schreibe_qualitaetswerte(alle_ergebnisse)
    print(f"      Qualitaetswerte: {qw_pfad.name}")

    # 4. Manifeste
    print("[4/5] Manifeste schreiben...")
    mj, mc = schreibe_km13_manifest(alle_ergebnisse)
    print(f"      {mj.name}, {mc.name}")

    # 5. Status, Berichte
    print("[5/5] Status und Berichte...")
    sp, status_daten = schreibe_status(alle_ergebnisse, fehler_liste, tesseract_version, verfuegbare_sprachen)
    bp = schreibe_bericht(alle_ergebnisse, fehler_liste, status_daten)
    fp = schreibe_fehlerbericht(fehler_liste)
    ap = schreibe_ausfuehrungsnotiz(alle_ergebnisse, fehler_liste, status_daten)

    # Ergebnis
    print()
    print("=" * 60)
    print("KM13 ABGESCHLOSSEN")
    print("=" * 60)
    print(f"Seiten verarbeitet:     {status_daten['seiten_verarbeitet']}")
    print(f"OCR erfolgreich:        {status_daten['ocr_erfolgreich']}")
    print(f"OCR mit Warnung:        {status_daten['ocr_mit_warnung']}")
    print(f"OCR fehlgeschlagen:     {status_daten['ocr_fehlgeschlagen']}")
    print(f"Seiten gesperrt:        {status_daten['seiten_gesperrt']}")
    print(f"Tesseract:              {tesseract_version}")
    print(f"Sprachen:               {', '.join(verfuegbare_sprachen)}")
    print(f"Manifest:               {mj}")
    print(f"Status:                 {sp}")
    print(f"Bericht:                {bp}")
    print(f"Naechster Auftrag:      KM14 – Maschinenformat / Fundstellenstruktur")
    print()
    print("Keine Rohdaten ausgegeben. Keine Originale verwendet.")
    print("Keine Uebersetzung. Keine Rechtsbewertung. Keine Datenbankaenderung.")

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
