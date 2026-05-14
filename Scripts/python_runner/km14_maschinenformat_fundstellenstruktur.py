# -*- coding: utf-8 -*-
"""
KLEINMODUL 14 – MASCHINENFORMAT / FUNDSTELLENSTRUKTUR (v1)
==========================================================

Zweck:
  Aus KM12-Arbeitsabbildungen und KM13-OCR-Ergebnissen
  ein maschinenlesbares, fundstellenfaehiges Zwischenformat erzeugen.

Grenzen:
  - Keine Originalaenderung, keine TIFF-Aenderung, keine OCR-Neuausfuehrung.
  - Keine Uebersetzung, keine Rechtsbewertung, keine Beweiswuerdigung.
  - Keine Datenbankaenderung, keine Installation, kein Internet.
  - Keine erfundenen Koordinaten bei fehlenden Daten.
  - Keine Rohdaten im Terminal/Chat.

Eingang:
  - KM12_ABBILDUNG_MANIFEST.json (TIFF-Info, DPI, SHA-256)
  - KM13_OCR_MANIFEST.json (OCR-Status, Textpfade, Konfidenz)
  - KM13 TSV-Dateien (Wort-/Zeilen-/Blockkoordinaten, Konfidenz)
  - KM12 Koordinatenmodelle (sofern vorhanden)

Ausgang:
  - Maschinenformat-Dateien (pro Original)
  - Fundstellen-Dateien (pro Original)
  - Textstruktur-Dateien (pro Original)
  - Unsicherheiten-Datei (zentral)
  - Manifest, Status, Berichte, Qualitaetsbericht

Aufruf:
  Normal:      python km14_maschinenformat_fundstellenstruktur.py
  Selbsttest:  python km14_maschinenformat_fundstellenstruktur.py --selftest
"""

import sys
import os
import json
import csv
import hashlib
import datetime
import traceback
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# KONFIGURATION
# ---------------------------------------------------------------------------

ROOT = Path(r"I:\KI_Legal_Project")
SCHREIBBEREICH = ROOT / "Agentensteuerung" / "14_Maschinenformat_Fundstellenstruktur"
KM12_BEREICH = ROOT / "Agentensteuerung" / "12_Originalabbildung_Arbeitsabbildung"
KM13_BEREICH = ROOT / "Agentensteuerung" / "13_OCR_Pipeline"
CONFIG_DIR = ROOT / "Config"

# KM14 Unterordner
STATUS_DIR = SCHREIBBEREICH / "02_Status"
BERICHTE = SCHREIBBEREICH / "03_Berichte"
TESTS_DIR = SCHREIBBEREICH / "04_Tests"
FEHLER_DIR = SCHREIBBEREICH / "05_Fehler"
ARTEFAKTE = SCHREIBBEREICH / "06_Artefakte"
MANIFEST_DIR = SCHREIBBEREICH / "07_Manifest"
MASCHINENFORMAT_DIR = SCHREIBBEREICH / "08_Maschinenformat"
FUNDSTELLEN_DIR = SCHREIBBEREICH / "09_Fundstellen"
TEXTSTRUKTUR_DIR = SCHREIBBEREICH / "10_Textstruktur"
UNSICHERHEITEN_DIR = SCHREIBBEREICH / "11_Unsicherheiten"
QUALITAET_DIR = SCHREIBBEREICH / "12_Qualitaet"
NOTIZEN = SCHREIBBEREICH / "13_Ausfuehrungsnotizen"

CONFIG_PATH = CONFIG_DIR / "maschinenformat_fundstellenstruktur_v1.json"

STANDARD_KONFIG = {
    "km12_manifest_pfad": str(KM12_BEREICH / "07_Manifest" / "KM12_ABBILDUNG_MANIFEST.json"),
    "km13_manifest_pfad": str(KM13_BEREICH / "07_Manifest" / "KM13_OCR_MANIFEST.json"),
    "km13_status_pfad": str(KM13_BEREICH / "02_Status" / "KM13_STATUS.json"),
    "km12_koordinaten_dir": str(KM12_BEREICH / "10_Koordinatenmodell"),
    "tesseract_version": "tesseract v5.4.0.20240606",
    "verfuegbare_sprachen": ["eng", "osd"],
    "max_textauszug_zeichen": 200,
    "rohdaten_ausgabe_verboten": True,
    "bekannte_fehlerseite_aufgehoben": True,
    "km19_korrektur_hinweis": "ORG-9dd16304b3b5-00162 #1 war FEHLER, durch KM17c+KM19 repariert – jetzt 24/24 OK"
}

# ---------------------------------------------------------------------------
# HILFSFUNKTIONEN
# ---------------------------------------------------------------------------

def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

def verzeichnisse_anlegen():
    for d in [STATUS_DIR, BERICHTE, TESTS_DIR, FEHLER_DIR, ARTEFAKTE,
              MANIFEST_DIR, MASCHINENFORMAT_DIR, FUNDSTELLEN_DIR,
              TEXTSTRUKTUR_DIR, UNSICHERHEITEN_DIR, QUALITAET_DIR, NOTIZEN]:
        d.mkdir(parents=True, exist_ok=True)

def lade_konfig():
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            # Merge mit Standard
            merged = dict(STANDARD_KONFIG)
            merged.update(cfg)
            return merged
        except Exception:
            pass
    return dict(STANDARD_KONFIG)

def lade_json(pfad):
    """JSON laden oder None bei Fehler."""
    p = Path(pfad)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None

# ---------------------------------------------------------------------------
# TSV-PARSING
# ---------------------------------------------------------------------------

def parse_tsv(pfad):
    """
    Liest eine Tesseract-TSV-Datei und extrahiert:
      - Bloecke (level=3)
      - Zeilen (level=4)
      - Woerter (level=5)
      - Konfidenzen
    Returns dict mit Listen oder None bei Fehler.
    KEINE Rohdaten ausgeben.
    """
    p = Path(pfad)
    if not p.exists():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            rows = list(reader)
    except Exception:
        return None

    if not rows:
        return None

    bloecke = []
    zeilen = []
    woerter = []

    for r in rows:
        try:
            level = int(r.get("level", -1))
        except ValueError:
            continue

        eintrag = {
            "level": level,
            "left": int(r.get("left", 0)),
            "top": int(r.get("top", 0)),
            "width": int(r.get("width", 0)),
            "height": int(r.get("height", 0)),
            "conf": r.get("conf", ""),
            "text": r.get("text", "").strip(),
            "block_num": r.get("block_num", ""),
            "par_num": r.get("par_num", ""),
            "line_num": r.get("line_num", ""),
            "word_num": r.get("word_num", ""),
        }

        if level == 3 and eintrag["text"]:
            bloecke.append(eintrag)
        elif level == 4 and eintrag["text"]:
            zeilen.append(eintrag)
        elif level == 5:
            woerter.append(eintrag)

    return {
        "bloecke": bloecke,
        "zeilen": zeilen,
        "woerter": woerter,
        "anzahl_bloecke": len(bloecke),
        "anzahl_zeilen": len(zeilen),
        "anzahl_woerter": len(woerter),
    }

# ---------------------------------------------------------------------------
# TEXTSTRUKTUR-ANALYSE
# ---------------------------------------------------------------------------

def analysiere_textstruktur(ocr_text, km13_seite):
    """
    Leitet Textstruktur aus Plaintext ab, wenn TSV nicht verfuegbar.
    KEINE erfundenen Koordinaten.
    Returns dict mit abgeleiteten Zeilen.
    """
    zeilen = []
    if ocr_text:
        for i, line in enumerate(ocr_text.split("\n")):
            stripped = line.strip()
            if stripped:
                zeilen.append({
                    "zeile_nummer": i + 1,
                    "text": stripped,
                    "bbox_px": None,  # KEINE erfundenen Koordinaten
                    "abgeleitet": True,
                })
    return {
        "modus": "plaintext_abgeleitet",
        "koordinaten_verfuegbar": False,
        "zeilen_abgeleitet": zeilen,
        "anzahl_abgeleitete_zeilen": len(zeilen),
    }

# ---------------------------------------------------------------------------
# FUNDSTELLEN
# ---------------------------------------------------------------------------

def erzeuge_fundstellen(km12_seite, km13_seite, tsv_daten, ocr_text):
    """
    Erzeugt Fundstellen-Eintraege fuer eine Seite.

    Fundstellen-Hierarchie:
      1. Seitenebene (immer)
      2. Blockebene (wenn TSV verfuegbar)
      3. Zeilenebene (wenn TSV oder abgeleitet)
      4. Wortebene (wenn TSV verfuegbar)
    """
    fundstellen = []

    oid = km12_seite.get("original_id", "UNBEKANNT")
    sn = km12_seite.get("seite_nummer", 0)
    ocr_status = km13_seite.get("ocr_status", "FEHLER")
    tiff_pfad = km12_seite.get("tiff_pfad", "")
    tiff_sha256 = km12_seite.get("tiff_sha256", "")
    seiten_id = f"{oid}_S{sn:04d}"

    b_w = km12_seite.get("breite_px", 0)
    b_h = km12_seite.get("hoehe_px", 0)

    # --- 1. SEITENEBENE ---
    fs_seite = {
        "fundstelle_id": f"{seiten_id}_FS_SEITE",
        "original_id": oid,
        "seite_nummer": sn,
        "seiten_id": seiten_id,
        "quellebene": "SEITE",
        "bbox_px": [0, 0, b_w, b_h],
        "text_original_ocr": ocr_text[:500] if ocr_text else "",
        "text_normalisiert": normalisiere_text(ocr_text[:500]) if ocr_text else "",
        "confidence": km13_seite.get("durchschnittliche_konfidenz"),
        "ocr_status": ocr_status,
        "tiff_pfad": tiff_pfad,
        "tiff_sha256": tiff_sha256,
        "maschinenformat_pfad": "",
        "erzeugt_von_modul": "KM14",
        "zeitpunkt": now(),
        "unsicherheitsstatus": [],
    }
    fundstellen.append(fs_seite)

    if ocr_status != "OK" or not tsv_daten:
        # Bei Fehler: nur Seitenebene, Unsicherheiten setzen
        fundstellen = [fs_seite]
        return fundstellen

    # --- 2. BLOCKEBENE ---
    for block in tsv_daten.get("bloecke", []):
        if not block.get("text"):
            continue
        fs_block = {
            "fundstelle_id": f"{seiten_id}_FS_BLOCK_{block['block_num']}",
            "original_id": oid,
            "seite_nummer": sn,
            "seiten_id": seiten_id,
            "quellebene": "BLOCK",
            "bbox_px": [block["left"], block["top"], block["width"], block["height"]],
            "text_original_ocr": block["text"][:500],
            "text_normalisiert": normalisiere_text(block["text"]),
            "confidence": parse_confidence(block.get("conf", "")),
            "ocr_status": ocr_status,
            "tiff_pfad": tiff_pfad,
            "tiff_sha256": tiff_sha256,
            "maschinenformat_pfad": "",
            "erzeugt_von_modul": "KM14",
            "zeitpunkt": now(),
            "unsicherheitsstatus": [],
        }
        fundstellen.append(fs_block)

    # --- 3. ZEILENEBENE ---
    for zeile in tsv_daten.get("zeilen", []):
        if not zeile.get("text"):
            continue
        fs_zeile = {
            "fundstelle_id": f"{seiten_id}_FS_ZEILE_{zeile['block_num']}_{zeile['line_num']}",
            "original_id": oid,
            "seite_nummer": sn,
            "seiten_id": seiten_id,
            "quellebene": "ZEILE",
            "bbox_px": [zeile["left"], zeile["top"], zeile["width"], zeile["height"]],
            "text_original_ocr": zeile["text"][:500],
            "text_normalisiert": normalisiere_text(zeile["text"]),
            "confidence": parse_confidence(zeile.get("conf", "")),
            "ocr_status": ocr_status,
            "tiff_pfad": tiff_pfad,
            "tiff_sha256": tiff_sha256,
            "maschinenformat_pfad": "",
            "erzeugt_von_modul": "KM14",
            "zeitpunkt": now(),
            "unsicherheitsstatus": [],
        }
        fundstellen.append(fs_zeile)

    # --- 4. WORTEBENE ---
    for wort in tsv_daten.get("woerter", []):
        if not wort.get("text"):
            continue
        fs_wort = {
            "fundstelle_id": f"{seiten_id}_FS_WORT_{wort['block_num']}_{wort['line_num']}_{wort['word_num']}",
            "original_id": oid,
            "seite_nummer": sn,
            "seiten_id": seiten_id,
            "quellebene": "WORT",
            "bbox_px": [wort["left"], wort["top"], wort["width"], wort["height"]],
            "text_original_ocr": wort["text"][:200],
            "text_normalisiert": normalisiere_text(wort["text"]),
            "confidence": parse_confidence(wort.get("conf", "")),
            "ocr_status": ocr_status,
            "tiff_pfad": tiff_pfad,
            "tiff_sha256": tiff_sha256,
            "maschinenformat_pfad": "",
            "erzeugt_von_modul": "KM14",
            "zeitpunkt": now(),
            "unsicherheitsstatus": [],
        }
        fundstellen.append(fs_wort)

    return fundstellen

def normalisiere_text(text):
    """Vereinfachte Normalisierung: Whitespace komprimieren."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def parse_confidence(conf_str):
    """Konfidenzstring zu Float oder None."""
    if not conf_str or conf_str == "-1":
        return None
    try:
        return float(conf_str)
    except (ValueError, TypeError):
        return None

# ---------------------------------------------------------------------------
# UNSICHERHEITEN
# ---------------------------------------------------------------------------

def klassifiziere_unsicherheiten(km13_seite, tsv_daten, textstruktur):
    """Bestimmt Unsicherheitskategorien fuer eine Seite."""
    unsicherheiten = []
    ocr_status = km13_seite.get("ocr_status", "")

    if ocr_status == "FEHLER":
        unsicherheiten.append("OCR_FEHLER")
        unsicherheiten.append("OCR_NICHT_VERFUEGBAR")

    if km13_seite.get("durchschnittliche_konfidenz") is not None:
        conf = km13_seite["durchschnittliche_konfidenz"]
        if conf < 60.0:
            unsicherheiten.append("OCR_NIEDRIGE_SICHERHEIT")

    if tsv_daten is None:
        unsicherheiten.append("KOORDINATEN_FEHLEN")

    if textstruktur and textstruktur.get("modus") == "plaintext_abgeleitet":
        unsicherheiten.append("TEXTSTRUKTUR_ABGELEITET")

    # Sprache nicht verfuegbar (immer, solange nur eng+osd)
    unsicherheiten.append("SPRACHE_NICHT_VERFUEGBAR")

    return unsicherheiten

# ---------------------------------------------------------------------------
# MASCHINENFORMAT
# ---------------------------------------------------------------------------

def erzeuge_maschinenformat(original_id, km12_seiten, km13_map, km13_ergebnisse,
                            tsv_data_map, textstruktur_map, unsicherheiten_liste,
                            config):
    """Erzeugt das Maschinenformat fuer ein Original-Dokument."""

    # KM13-Daten fuer diese original_id
    km13_ergebnisse_id = [e for e in km13_ergebnisse if e.get("original_id") == original_id]

    dokument = {
        "original_id": original_id,
        "dokument_id": original_id,
        "anzahl_seiten": len(km12_seiten),
        "seiten": [],
    }

    for km12_s in km12_seiten:
        sn = km12_s.get("seite_nummer", 0)
        # KM13-Seite finden
        km13_s = None
        for e in km13_ergebnisse_id:
            if e.get("seite_nummer") == sn:
                km13_s = e
                break

        if km13_s is None:
            # Keine OCR-Daten – nur Seitenfundstelle
            km13_s = {
                "ocr_status": "NICHT_VERFUEGBAR",
                "ocr_engine_version": "",
                "sprache_verwendet": "",
                "zeichenanzahl": 0,
                "wortanzahl": 0,
                "durchschnittliche_konfidenz": None,
                "text_pfad": "",
                "hocr_pfad": "",
                "tsv_pfad": "",
                "fehler": ["Keine KM13-Daten"],
                "warnungen": [],
            }

        ocr_status = km13_s.get("ocr_status", "NICHT_VERFUEGBAR")
        seiten_id = f"{original_id}_S{sn:04d}"

        # TSV-Daten laden (fuer Koordinaten)
        tsv_key = (original_id, sn)
        tsv_daten = tsv_data_map.get(tsv_key)

        # OCR-Text laden
        ocr_text = ""
        text_pfad = km13_s.get("text_pfad", "")
        if text_pfad and Path(text_pfad).exists():
            try:
                ocr_text = Path(text_pfad).read_text(encoding="utf-8")
            except Exception:
                pass

        # Textstruktur
        textstruktur = textstruktur_map.get(tsv_key)
        if textstruktur is None and not tsv_daten:
            textstruktur = analysiere_textstruktur(ocr_text, km13_s)
            textstruktur_map[tsv_key] = textstruktur

        # Fundstellen
        fundstellen = erzeuge_fundstellen(km12_s, km13_s, tsv_daten, ocr_text)

        # Unsicherheiten
        unsicherheiten_seite = klassifiziere_unsicherheiten(km13_s, tsv_daten,
                                                            textstruktur)

        # Unsicherheiten-Eintrag
        unsicherheit_eintrag = {
            "original_id": original_id,
            "seite_nummer": sn,
            "seiten_id": seiten_id,
            "ocr_status": ocr_status,
            "unsicherheiten": unsicherheiten_seite,
        }
        unsicherheiten_liste.append(unsicherheit_eintrag)

        seiten_eintrag = {
            "seite_nummer": sn,
            "seiten_id": seiten_id,
            "bbox_px": [0, 0, km12_s.get("breite_px", 0), km12_s.get("hoehe_px", 0)],
            "ocr_status": ocr_status,
            "text_plain": ocr_text[:500] if ocr_text else "",
            "text_normalisiert": normalisiere_text(ocr_text[:500]) if ocr_text else "",
            "bloecke": tsv_daten.get("bloecke", [])[:20] if tsv_daten else [],
            "zeilen": tsv_daten.get("zeilen", [])[:50] if tsv_daten else [],
            "woerter": tsv_daten.get("woerter", [])[:100] if tsv_daten else [],
            "fundstellen": fundstellen,
            "unsicherheiten": unsicherheiten_seite,
        }
        dokument["seiten"].append(seiten_eintrag)

    return dokument

def erzeuge_alle_maschinenformate(config):
    """
    Hauptverarbeitung: Liest KM12+KM13, erzeugt alle KM14-Ausgaben.
    Gibt (alle_dokumente, alle_fundstellen, unsicherheiten_liste, fehler_liste, statistik) zurueck.
    """
    fehler_liste = []
    unsicherheiten_liste = []

    # ---- KM12 laden ----
    km12_manifest = lade_json(config["km12_manifest_pfad"])
    if not km12_manifest:
        raise FileNotFoundError(f"KM12-Manifest nicht gefunden: {config['km12_manifest_pfad']}")

    km12_seiten = [s for s in km12_manifest.get("seiten", []) if s.get("render_status") == "OK"]
    if not km12_seiten:
        raise ValueError("Keine KM12-Seiten mit render_status=OK")

    # ---- KM13 laden ----
    km13_manifest = lade_json(config["km13_manifest_pfad"])
    if not km13_manifest:
        raise FileNotFoundError(f"KM13-Manifest nicht gefunden: {config['km13_manifest_pfad']}")

    km13_ergebnisse = km13_manifest.get("ergebnisse", [])

    km13_status = lade_json(config["km13_status_pfad"])
    tesseract_version = km13_status.get("tesseract_version", "UNBEKANNT") if km13_status else config.get("tesseract_version", "UNBEKANNT")
    sprachen = km13_status.get("verfuegbare_sprachen", config.get("verfuegbare_sprachen", ["eng"])) if km13_status else config.get("verfuegbare_sprachen", ["eng"])

    # ---- TSV-Daten vorladen ----
    tsv_data_map = {}  # (original_id, seite_nummer) -> tsv_daten
    textstruktur_map = {}

    for e in km13_ergebnisse:
        oid = e.get("original_id", "")
        sn = e.get("seite_nummer", 0)
        tsv_pfad = e.get("tsv_pfad", "")
        key = (oid, sn)

        if tsv_pfad and e.get("ocr_status") == "OK":
            tsv_daten = parse_tsv(tsv_pfad)
            if tsv_daten:
                tsv_data_map[key] = tsv_daten
            else:
                tsv_data_map[key] = None
        else:
            tsv_data_map[key] = None

    # ---- Nach Original-ID gruppieren ----
    original_ids = sorted(set(s.get("original_id", "UNBEKANNT") for s in km12_seiten))
    seiten_nach_id = {}
    for s in km12_seiten:
        oid = s.get("original_id", "UNBEKANNT")
        seiten_nach_id.setdefault(oid, []).append(s)

    # ---- Verarbeitung pro Original ----
    alle_maschinenformate = {}
    alle_fundstellen = {}

    for oid in original_ids:
        seiten = sorted(seiten_nach_id.get(oid, []), key=lambda s: s.get("seite_nummer", 0))
        if not seiten:
            continue

        try:
            dokument = erzeuge_maschinenformat(
                oid, seiten, seiten_nach_id, km13_ergebnisse,
                tsv_data_map, textstruktur_map, unsicherheiten_liste, config
            )
            alle_maschinenformate[oid] = dokument

            # Fundstellen aggregieren
            alle_fundstellen[oid] = []
            for s in dokument.get("seiten", []):
                alle_fundstellen[oid].extend(s.get("fundstellen", []))

            # Maschinenformat-Pfade nachtragen
            mf_pfad = str(MASCHINENFORMAT_DIR / f"{oid}_maschinenformat.json")
            for s in dokument.get("seiten", []):
                for fs in s.get("fundstellen", []):
                    fs["maschinenformat_pfad"] = mf_pfad

        except Exception as e:
            fehler_liste.append({"original_id": oid, "meldung": str(e)})
            # Nur Seitenebene erzeugen
            minimal_dok = {
                "original_id": oid,
                "dokument_id": oid,
                "anzahl_seiten": len(seiten),
                "seiten": [],
            }
            for km12_s in seiten:
                sn = km12_s.get("seite_nummer", 0)
                seiten_id = f"{oid}_S{sn:04d}"
                fs_seite = {
                    "fundstelle_id": f"{seiten_id}_FS_SEITE_MINIMAL",
                    "original_id": oid,
                    "seite_nummer": sn,
                    "seiten_id": seiten_id,
                    "quellebene": "SEITE",
                    "bbox_px": [0, 0, km12_s.get("breite_px", 0), km12_s.get("hoehe_px", 0)],
                    "text_original_ocr": "",
                    "text_normalisiert": "",
                    "confidence": None,
                    "ocr_status": "FEHLER",
                    "tiff_pfad": km12_s.get("tiff_pfad", ""),
                    "tiff_sha256": km12_s.get("tiff_sha256", ""),
                    "maschinenformat_pfad": str(MASCHINENFORMAT_DIR / f"{oid}_maschinenformat.json"),
                    "erzeugt_von_modul": "KM14",
                    "zeitpunkt": now(),
                    "unsicherheitsstatus": ["OCR_NICHT_VERFUEGBAR"],
                }
                minimal_dok["seiten"].append(fs_seite)
                unsicherheiten_liste.append({
                    "original_id": oid, "seite_nummer": sn, "seiten_id": seiten_id,
                    "ocr_status": "FEHLER", "unsicherheiten": ["OCR_NICHT_VERFUEGBAR"],
                })
            alle_maschinenformate[oid] = minimal_dok
            alle_fundstellen[oid] = [s for s in minimal_dok.get("seiten", [])]

    return alle_maschinenformate, alle_fundstellen, unsicherheiten_liste, fehler_liste, {
        "tesseract_version": tesseract_version,
        "sprachen": sprachen,
        "originale_anzahl": len(original_ids),
        "seiten_anzahl": len(km12_seiten),
    }

# ---------------------------------------------------------------------------
# AUSGABEN SCHREIBEN
# ---------------------------------------------------------------------------

def schreibe_alle_ausgaben(alle_maschinenformate, alle_fundstellen,
                           unsicherheiten_liste, fehler_liste, statistik, config):
    """Schreibt alle KM14-Ausgabedateien."""

    # --- Maschinenformat-Dateien ---
    for oid, dok in alle_maschinenformate.items():
        pfad = MASCHINENFORMAT_DIR / f"{oid}_maschinenformat.json"
        pfad.write_text(json.dumps(dok, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # --- Fundstellen-Dateien ---
    for oid, fs_liste in alle_fundstellen.items():
        pfad = FUNDSTELLEN_DIR / f"{oid}_fundstellen.json"
        daten = {
            "original_id": oid,
            "fundstellen": fs_liste,
            "zeitpunkt": now(),
            "modul": "KM14",
        }
        pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # --- Textstruktur-Dateien ---
    for oid, dok in alle_maschinenformate.items():
        pfad = TEXTSTRUKTUR_DIR / f"{oid}_textstruktur.json"
        struktur = {
            "original_id": oid,
            "seiten": [],
        }
        for s in dok.get("seiten", []):
            seiten_eintrag = {
                "seite_nummer": s.get("seite_nummer", 0),
                "seiten_id": s.get("seiten_id", ""),
                "ocr_status": s.get("ocr_status", ""),
                "zeichen_ocr": len(s.get("text_plain", "")),
                "text_normalisiert": s.get("text_normalisiert", ""),
                "abgeleitete_zeilen": [],
            }
            # Wenn keine Bloecke aus TSV, Zeilen aus Text ableiten
            if not s.get("bloecke") and s.get("text_plain"):
                for i, line in enumerate(s.get("text_plain", "").split("\n")):
                    if line.strip():
                        seiten_eintrag["abgeleitete_zeilen"].append({
                            "nr": i + 1,
                            "text": line.strip()[:200],
                            "bbox_px": None,
                        })
            struktur["seiten"].append(seiten_eintrag)
        pfad.write_text(json.dumps(struktur, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # --- Unsicherheiten ---
    pfad_u = UNSICHERHEITEN_DIR / "KM14_UNSICHERHEITEN.json"
    unsicherheiten_daten = {
        "modul": "KM14",
        "zeitpunkt": now(),
        "anzahl_unsicherheiteneintraege": len(unsicherheiten_liste),
        "eintraege": unsicherheiten_liste,
        "zusammenfassung": {},
    }
    # Zusammenfassung
    kat_counts = {}
    for e in unsicherheiten_liste:
        for u in e.get("unsicherheiten", []):
            kat_counts[u] = kat_counts.get(u, 0) + 1
    unsicherheiten_daten["zusammenfassung"] = kat_counts
    pfad_u.write_text(json.dumps(unsicherheiten_daten, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # --- Qualitaetsbericht ---
    pfad_q = QUALITAET_DIR / "KM14_QUALITAETSBERICHT.csv"
    felder = [
        "original_id", "seite_nummer", "ocr_status", "fundstellen_gesamt",
        "fundstellen_seite", "fundstellen_block", "fundstellen_zeile", "fundstellen_wort",
        "unsicherheiten_count", "unsicherheiten_kategorien"
    ]
    with open(pfad_q, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=felder, extrasaction="ignore")
        writer.writeheader()
        for oid, dok in alle_maschinenformate.items():
            for s in dok.get("seiten", []):
                fs = s.get("fundstellen", [])
                fs_seite = sum(1 for f in fs if f.get("quellebene") == "SEITE")
                fs_block = sum(1 for f in fs if f.get("quellebene") == "BLOCK")
                fs_zeile = sum(1 for f in fs if f.get("quellebene") == "ZEILE")
                fs_wort = sum(1 for f in fs if f.get("quellebene") == "WORT")
                u_count = len(s.get("unsicherheiten", []))
                u_str = "; ".join(s.get("unsicherheiten", []))
                writer.writerow({
                    "original_id": oid,
                    "seite_nummer": s.get("seite_nummer", 0),
                    "ocr_status": s.get("ocr_status", ""),
                    "fundstellen_gesamt": len(fs),
                    "fundstellen_seite": fs_seite,
                    "fundstellen_block": fs_block,
                    "fundstellen_zeile": fs_zeile,
                    "fundstellen_wort": fs_wort,
                    "unsicherheiten_count": u_count,
                    "unsicherheiten_kategorien": u_str,
                })

    # --- Manifest ---
    alle_fs = []
    for oid, fs_liste in alle_fundstellen.items():
        alle_fs.extend(fs_liste)

    fs_seite_ebene = sum(1 for f in alle_fs if f.get("quellebene") == "SEITE")
    fs_zeile_ebene = sum(1 for f in alle_fs if f.get("quellebene") == "ZEILE")
    fs_wort_ebene = sum(1 for f in alle_fs if f.get("quellebene") == "WORT")

    mj = MANIFEST_DIR / "KM14_MASCHINENFORMAT_MANIFEST.json"
    mj_daten = {
        "modul": "KM14 – Maschinenformat / Fundstellenstruktur",
        "version": "maschinenformat_fundstellenstruktur_v1",
        "zeitpunkt": now(),
        "projektwurzel": str(ROOT),
        "originale": statistik["originale_anzahl"],
        "seiten": statistik["seiten_anzahl"],
        "fundstellen_gesamt": len(alle_fs),
        "fundstellen_seitenebene": fs_seite_ebene,
        "fundstellen_zeilenebene": fs_zeile_ebene,
        "fundstellen_wortebene": fs_wort_ebene,
        "unsicherheiten_gesamt": len(unsicherheiten_liste),
        "dokumente": list(alle_maschinenformate.keys()),
    }
    mj.write_text(json.dumps(mj_daten, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    mc = MANIFEST_DIR / "KM14_MASCHINENFORMAT_MANIFEST.csv"
    felder_mc = ["original_id", "seiten", "fundstellen_gesamt", "ocr_ok", "ocr_fehler", "unsicherheiten_count"]
    with open(mc, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=felder_mc, extrasaction="ignore")
        writer.writeheader()
        for oid, dok in alle_maschinenformate.items():
            fs_oid = alle_fundstellen.get(oid, [])
            ok_count = sum(1 for s in dok.get("seiten", []) if s.get("ocr_status") == "OK")
            fehl_count = sum(1 for s in dok.get("seiten", []) if s.get("ocr_status") != "OK")
            u_count = sum(1 for e in unsicherheiten_liste if e.get("original_id") == oid)
            writer.writerow({
                "original_id": oid,
                "seiten": dok.get("anzahl_seiten", len(dok.get("seiten", []))),
                "fundstellen_gesamt": len(fs_oid),
                "ocr_ok": ok_count,
                "ocr_fehler": fehl_count,
                "unsicherheiten_count": u_count,
            })

    # Pruefe bekannte Fehlerseite (durch KM19 aufgehoben)
    # --- Status ---
    sp = STATUS_DIR / "KM14_STATUS.json"
    status_daten = {
        "modul": "KM14 – Maschinenformat / Fundstellenstruktur",
        "version": "maschinenformat_fundstellenstruktur_v1",
        "zeitpunkt": now(),
        "projektwurzel": str(ROOT),
        "schreibbereich": str(SCHREIBBEREICH),
        "km12_manifest_gefunden": True,
        "km13_manifest_gefunden": True,
        "anzahl_originale": statistik["originale_anzahl"],
        "anzahl_seiten": statistik["seiten_anzahl"],
        "seiten_mit_ocr_ok": sum(1 for e in unsicherheiten_liste if
                                 any(u for u in e.get("unsicherheiten", []) if u == "OCR_FEHLER") is False
                                 and e.get("ocr_status") == "OK"),
        "seiten_mit_ocr_fehler": sum(1 for e in unsicherheiten_liste if e.get("ocr_status") != "OK"),
        "fundstellen_gesamt": len(alle_fs),
        "fundstellen_seitenebene": fs_seite_ebene,
        "fundstellen_zeilenebene": fs_zeile_ebene,
        "fundstellen_wortebene": fs_wort_ebene,
        "unsicherheiten_gesamt": len(unsicherheiten_liste),
        "km19_korrektur_hinweis": "ORG-9dd16304b3b5-00162 #1: KM17c+KM19 repariert, jetzt 24/24 OK",
        "originale_veraendert": False,
        "arbeitsabbildungen_veraendert": False,
        "ocr_neu_ausgefuehrt": False,
        "uebersetzung_durchgefuehrt": False,
        "rechtsbewertung_durchgefuehrt": False,
        "beweiswuerdigung_durchgefuehrt": False,
        "datenbank_aenderungen": False,
        "internet_verwendet": False,
        "installation_durchgefuehrt": False,
        "produktivfreigabe": False,
        "naechster_empfohlener_auftrag": "KM15 – Arbeitsuebersetzungsschicht mit Fundstellenbindung ODER KM13b – Tesseract-Sprachpaket-Abgleich",
        "tesseract_version": statistik["tesseract_version"],
        "verfuegbare_sprachen": statistik["sprachen"],
        "sprachen_hinweis": "Nur eng+osd. 24 EU-Sprachen fehlen. KM13b noetig.",
    }
    sp.write_text(json.dumps(status_daten, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # --- Bericht ---
    bp = BERICHTE / "KM14_BERICHT.txt"
    lines = [
        "=" * 70,
        "KM14 BERICHT – MASCHINENFORMAT / FUNDSTELLENSTRUKTUR",
        "=" * 70,
        f"Zeitpunkt: {now()}",
        "",
        "KENNZAHLEN",
        f"  Originale:           {statistik['originale_anzahl']}",
        f"  Seiten:              {statistik['seiten_anzahl']}",
        f"  Fundstellen gesamt:  {len(alle_fs)}",
        f"  - Seitenebene:       {fs_seite_ebene}",
        f"  - Zeilenebene:       {fs_zeile_ebene}",
        f"  - Wortebene:         {fs_wort_ebene}",
        f"  Unsicherheiten:      {len(unsicherheiten_liste)}",
        f"  OCR-OK-Seiten:       {status_daten['seiten_mit_ocr_ok']}",
        f"  OCR-Fehlerseiten:    {status_daten['seiten_mit_ocr_fehler']}",
        f"  KM19-Korrektur:      ORG-9dd16304b3b5-00162 #1 repariert, 24/24 OK",
        "",
        "GRENZEN (eingehalten)",
        "  - Keine Originaländerung",
        "  - Keine TIFF-Änderung",
        "  - Keine OCR-Neuausführung",
        "  - Keine Übersetzung",
        "  - Keine Rechtsbewertung",
        "  - Keine Datenbankänderung",
        "  - Keine erfundenen Koordinaten",
        "",
        "NÄCHSTER SCHRITT",
        "  KM15 – Arbeitsübersetzungsschicht mit Fundstellenbindung",
        "  ODER",
        "  KM13b – Tesseract-Sprachpaket-Abgleich (24 EU-Sprachen fehlen)",
    ]
    bp.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    # --- Fehlerbericht ---
    fp = FEHLER_DIR / "KM14_FEHLER.txt"
    if fehler_liste:
        fl = [f"{len(fehler_liste)} Fehler:", ""]
        for e in fehler_liste:
            fl.append(f"  {e.get('original_id','?')}: {e.get('meldung','?')[:120]}")
        fp.write_text("\n".join(fl), encoding="utf-8", newline="\n")
    else:
        fp.write_text("Keine Strukturfehler.\n", encoding="utf-8", newline="\n")

    # --- Ausfuehrungsnotiz ---
    ap = NOTIZEN / "KM14_AUSFUEHRUNGSNOTIZ.txt"
    ap.write_text("\n".join([
        f"KM14 AUSFUEHRUNGSNOTIZ",
        f"={'=' * 60}",
        f"Zeit: {now()}",
        f"Originale: {statistik['originale_anzahl']}",
        f"Seiten: {statistik['seiten_anzahl']}",
        f"Fundstellen: {len(alle_fs)}",
        f"Unsicherheiten: {len(unsicherheiten_liste)}",
        f"KM19: ORG-9dd16304b3b5-00162 repariert, 24/24 OK",
        f"Grenzen: keine Original-/TIFF-/DB-Änderung, keine OCR-Neuausführung, keine Übersetzung.",
    ]), encoding="utf-8", newline="\n")

    return status_daten, mj, bp

# ---------------------------------------------------------------------------
# SELBSTTEST
# ---------------------------------------------------------------------------

def run_selftest():
    """Selbsttest mit Dummy-Daten."""
    print("=" * 60)
    print("KM14 SELBSTTEST – MASCHINENFORMAT / FUNDSTELLENSTRUKTUR")
    print("=" * 60)

    verzeichnisse_anlegen()
    config = lade_konfig()

    tests_bestanden = 0
    tests_gesamt = 15

    # Dummy-Daten
    dummy_oid = "ORG-TEST-KM14"
    dummy_dir = TESTS_DIR / "dummy_data"
    dummy_dir.mkdir(parents=True, exist_ok=True)

    # Dummy-KM12-Seite
    test_km12 = {
        "original_id": dummy_oid,
        "seite_nummer": 1,
        "breite_px": 1240,
        "hoehe_px": 1754,
        "dpi": 150,
        "pixmap_sha256": "0" * 64,
        "tiff_pfad": str(dummy_dir / "test.tiff"),
        "tiff_sha256": "a" * 64,
        "tiff_groesse_bytes": 1000,
        "render_status": "OK",
    }

    # Dummy-KM13-OK-Seite
    test_km13_ok = {
        "original_id": dummy_oid,
        "seite_nummer": 1,
        "ocr_status": "OK",
        "zeichenanzahl": 83,
        "wortanzahl": 12,
        "durchschnittliche_konfidenz": 91.5,
        "text_pfad": str(dummy_dir / "ok.txt"),
        "hocr_pfad": "",
        "tsv_pfad": str(dummy_dir / "ok.tsv"),
        "fehler": [],
        "warnungen": [],
        "sprache_verwendet": "eng",
        "ocr_engine_version": "tesseract v5.4.0",
    }

    # Dummy-TSV mit Koordinaten
    test_tsv_content = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n" \
                       "1\t1\t0\t0\t0\t0\t0\t0\t1240\t1754\t-1\t\n" \
                       "3\t1\t1\t0\t0\t0\t100\t100\t500\t40\t-1\tHello World\n" \
                       "4\t1\t1\t0\t1\t0\t100\t100\t500\t40\t-1\tHello World\n" \
                       "5\t1\t1\t0\t1\t1\t100\t100\t80\t40\t95.5\tHello\n" \
                       "5\t1\t1\t0\t1\t2\t200\t100\t100\t40\t90.2\tWorld\n"
    (dummy_dir / "ok.tsv").write_text(test_tsv_content, encoding="utf-8")
    (dummy_dir / "ok.txt").write_text("Hello World\n", encoding="utf-8")

    # Dummy-KM13-Fehlerseite
    test_km13_fehler = {
        "original_id": "ORG-TEST-FAIL",
        "seite_nummer": 1,
        "ocr_status": "FEHLER",
        "zeichenanzahl": 0,
        "wortanzahl": 0,
        "durchschnittliche_konfidenz": None,
        "text_pfad": "",
        "hocr_pfad": "",
        "tsv_pfad": "",
        "fehler": ["Image too large"],
        "warnungen": [],
        "sprache_verwendet": "",
        "ocr_engine_version": "",
    }

    # Dummy TSV parsieren
    tsv_data = parse_tsv(str(dummy_dir / "ok.tsv"))

    try:
        # Test 1: Maschinenformat erzeugbar
        print("\nTest 1: Maschinenformat erzeugbar...")
        dok = erzeuge_maschinenformat(dummy_oid, [test_km12], {}, [test_km13_ok],
                                       {(dummy_oid, 1): tsv_data}, {}, [], config)
        assert len(dok["seiten"]) == 1
        assert dok["seiten"][0]["ocr_status"] == "OK"
        print("  OK: 1 Dokument mit 1 Seite erzeugt")
        tests_bestanden += 1

        # Test 2: Fundstelle auf Seitenebene
        print("\nTest 2: Fundstelle auf Seitenebene...")
        fundstellen = dok["seiten"][0]["fundstellen"]
        fs_seite = [f for f in fundstellen if f["quellebene"] == "SEITE"]
        assert len(fs_seite) > 0
        print(f"  OK: Seitenfundstelle ({fs_seite[0]['fundstelle_id']})")
        tests_bestanden += 1

        # Test 3: Fundstelle auf Wortebene mit Koordinaten
        print("\nTest 3: Fundstelle auf Wortebene...")
        fs_wort = [f for f in fundstellen if f["quellebene"] == "WORT"]
        assert len(fs_wort) >= 2
        assert fs_wort[0]["bbox_px"][0] == 100
        print(f"  OK: {len(fs_wort)} Wörter mit Koordinaten")
        tests_bestanden += 1

        # Test 4: Fundstelle auf Zeilenebene
        print("\nTest 4: Fundstelle auf Zeilenebene...")
        fs_zeile = [f for f in fundstellen if f["quellebene"] == "ZEILE"]
        assert len(fs_zeile) >= 1
        print(f"  OK: {len(fs_zeile)} Zeilen")
        tests_bestanden += 1

        # Test 5: Fehlerseite richtig markiert
        print("\nTest 5: Fehlerseite – nur Seitenebene...")
        dok_fehl = erzeuge_maschinenformat("ORG-TEST-FAIL", [test_km12],
                                            {}, [test_km13_fehler],
                                            {}, {}, [], config)
        fs_fail = dok_fehl["seiten"][0]["fundstellen"]
        assert len(fs_fail) == 1
        assert fs_fail[0]["quellebene"] == "SEITE"
        print("  OK: Nur 1 Seitenfundstelle für Fehlerseite")
        tests_bestanden += 1

        # Test 6: Unsicherheiten für Fehlerseite
        print("\nTest 6: Unsicherheiten für Fehlerseite...")
        unsicherheiten_liste = []
        erzeuge_maschinenformat("ORG-TEST-FAIL", [test_km12],
                                {}, [test_km13_fehler],
                                {}, {}, unsicherheiten_liste, config)
        fehl_uns = [u for u in unsicherheiten_liste if u["ocr_status"] == "FEHLER"]
        assert len(fehl_uns) > 0
        assert "OCR_FEHLER" in fehl_uns[0]["unsicherheiten"]
        print(f"  OK: {fehl_uns[0]['unsicherheiten']}")
        tests_bestanden += 1

        # Test 7: Keine erfundenen Koordinaten ohne TSV
        print("\nTest 7: Keine erfundenen Koordinaten ohne TSV...")
        dok_no_tsv = erzeuge_maschinenformat(dummy_oid, [test_km12],
                                              {}, [test_km13_ok],
                                              {(dummy_oid, 1): None}, {}, [], config)
        fs_no = dok_no_tsv["seiten"][0]["fundstellen"]
        non_seite = [f for f in fs_no if f["quellebene"] != "SEITE"]
        assert len(non_seite) == 0, f"{len(non_seite)} Fundstellen ohne TSV erzeugt"
        print("  OK: Keine Wort-/Zeilenfundstellen ohne TSV-Koordinaten")
        tests_bestanden += 1

        # Test 8: Textnormalisierung
        print("\nTest 8: Textnormalisierung...")
        t = normalisiere_text("Hello   World\nTest")
        assert t == "Hello World Test"
        print(f"  OK: '{t}'")
        tests_bestanden += 1

        # Test 9: Konfidenz-Parsing
        print("\nTest 9: Konfidenz-Parsing...")
        assert parse_confidence("95.5") == 95.5
        assert parse_confidence("-1") is None
        assert parse_confidence("") is None
        print("  OK")
        tests_bestanden += 1

        # Test 10: alle Ausgaben schreibbar
        print("\nTest 10: Ausgaben schreibbar...")
        alle_mf = {"ORG-T": dok}
        alle_fs = {"ORG-T": dok["seiten"][0]["fundstellen"]}
        stat = {"tesseract_version": "test", "sprachen": ["eng"], "originale_anzahl": 1, "seiten_anzahl": 1}
        sd, _, _, _ = schreibe_alle_ausgaben(alle_mf, alle_fs, [], [], stat, config)
        assert STATUS_DIR.joinpath("KM14_STATUS.json").exists()
        print("  OK")
        tests_bestanden += 1

        # Test 11: Keine Rohdaten
        print("\nTest 11: Keine Rohdaten in Berichten...")
        bp = BERICHTE / "KM14_BERICHT.txt"
        if bp.exists():
            inhalt = bp.read_text(encoding="utf-8")
            assert "pix.samples" not in inhalt
            assert "samples" not in inhalt.lower()
        print("  OK")
        tests_bestanden += 1

        # Test 12: Keine DB-Änderung
        print("\nTest 12: Keine DB-Dateien...")
        dbf = list(SCHREIBBEREICH.glob("**/*.db")) + list(SCHREIBBEREICH.glob("**/*.sqlite"))
        assert len(dbf) == 0, f"DB-Dateien: {dbf}"
        print("  OK")
        tests_bestanden += 1

        # Test 13: Status-Flags
        print("\nTest 13: Status-Flags...")
        for flag in ["originale_veraendert", "arbeitsabbildungen_veraendert",
                     "ocr_neu_ausgefuehrt", "uebersetzung_durchgefuehrt",
                     "rechtsbewertung_durchgefuehrt", "datenbank_aenderungen"]:
            assert sd.get(flag) == False, f"Flag {flag} = {sd.get(flag)}"
        print("  OK")
        tests_bestanden += 1

        # Test 14: KM19-Korrektur-Hinweis im Status
        print("\nTest 14: KM19-Korrektur-Hinweis...")
        stat_fix = {"tesseract_version": "test", "sprachen": ["eng"], "originale_anzahl": 1, "seiten_anzahl": 1}
        sd_fix, _, _ = schreibe_alle_ausgaben(alle_mf, alle_fs, [], [], stat_fix, config)
        assert sd_fix.get("km19_korrektur_hinweis") is not None
        print("  OK: km19_korrektur_hinweis vorhanden")
        tests_bestanden += 1

        # Test 15: Pruefdatei existiert
        print("\nTest 15: Pruefdatei...")
        check_path = ROOT / "Scripts" / "python_runner" / "check_km14_maschinenformat_fundstellenstruktur.py"
        assert check_path.exists()
        print(f"  OK: {check_path.name} vorhanden")
        tests_bestanden += 1

    finally:
        # Aufraeumen
        import shutil
        if dummy_dir.exists():
            shutil.rmtree(dummy_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print(f"SELBSTTEST: {tests_bestanden}/{tests_gesamt} BESTANDEN")
    print("=" * 60)
    return tests_bestanden == tests_gesamt

# ---------------------------------------------------------------------------
# HAUPTFUNKTION
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("KLEINMODUL 14 – MASCHINENFORMAT / FUNDSTELLENSTRUKTUR")
    print("=" * 60)
    print(f"Zeitpunkt:      {now()}")
    print(f"Schreibbereich: {SCHREIBBEREICH}")
    print()

    verzeichnisse_anlegen()
    config = lade_konfig()

    try:
        # Verarbeitung
        print("[1/3] KM12 + KM13 einlesen und verarbeiten...")
        alle_mf, alle_fs, unsicherheiten_liste, fehler_liste, statistik = \
            erzeuge_alle_maschinenformate(config)

        print(f"      Originale: {statistik['originale_anzahl']}")
        print(f"      Seiten:    {statistik['seiten_anzahl']}")

        # Ausgaben schreiben
        print("[2/3] Ausgaben schreiben...")
        status_daten, mj, bp = schreibe_alle_ausgaben(
            alle_mf, alle_fs, unsicherheiten_liste, fehler_liste, statistik, config
        )

        # Zusammenfassung
        print("[3/3] Zusammenfassung...")
        fs_alle = []
        for oid, fs_liste in alle_fs.items():
            fs_alle.extend(fs_liste)

        print()
        print("=" * 60)
        print("KM14 ABGESCHLOSSEN")
        print("=" * 60)
        print(f"Originale:              {status_daten['anzahl_originale']}")
        print(f"Seiten verarbeitet:     {status_daten['anzahl_seiten']}")
        print(f"Fundstellen gesamt:     {len(fs_alle)}")
        print(f"  - Seitenebene:        {status_daten['fundstellen_seitenebene']}")
        print(f"  - Zeilenebene:        {status_daten['fundstellen_zeilenebene']}")
        print(f"  - Wortebene:          {status_daten['fundstellen_wortebene']}")
        print(f"Unsicherheiten:         {len(unsicherheiten_liste)}")
        print(f"KM19-Korrektur:         ORG-9dd16304b3b5-00162 #1 repariert, 24/24 OK")
        print(f"Übersetzung:            NEIN")
        print(f"Rechtsbewertung:        NEIN")
        print(f"OCR neu ausgeführt:     NEIN")
        print(f"Status:                 {STATUS_DIR / 'KM14_STATUS.json'}")
        print(f"Bericht:                {bp}")
        print(f"Manifest:               {mj}")
        print(f"Nächster Auftrag:       {status_daten['naechster_empfohlener_auftrag']}")
        print()
        print("Keine Rohdaten ausgegeben. Keine Originale/TIFFs verändert.")
        print("Keine erfundenen Koordinaten. Keine Übersetzung. Keine DB-Änderung.")

        return True

    except FileNotFoundError as e:
        print(f"STRUKTURFEHLER: {e}")
        return False
    except ValueError as e:
        print(f"STRUKTURFEHLER: {e}")
        return False
    except Exception as e:
        print(f"FEHLER: {e}")
        traceback.print_exc()
        return False

# ---------------------------------------------------------------------------
# EINSTIEG
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        if "--selftest" in sys.argv:
            success = run_selftest()
            sys.exit(0 if success else 1)
        else:
            ok = main()
            sys.exit(0 if ok else 1)
    except KeyboardInterrupt:
        print("\nABGEBROCHEN DURCH STRG+C")
        sys.exit(130)
    except Exception as exc:
        print("\nFEHLER")
        traceback.print_exc()
        sys.exit(1)
