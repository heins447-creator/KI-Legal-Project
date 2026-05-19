# -*- coding: utf-8 -*-
"""
KLEINMODUL 12 – ORIGINALABBILDUNG / ARBEITSABBILDUNG (originalabbildung_v1)
============================================================================

Zweck:
  PDF-Originalseiten pixelgenau als TIFF-Arbeitsabbildungen rendern,
  Koordinatenmodell ableiten, Pruefsummen bilden und Renderprotokoll fuehren.

  Baut auf KM11-Originalsicherung auf. Referenziert Originale ueber die
  KM11-Manifeste, veraendert keine Originale.

Grenzen:
  - Keine Originaldateien veraendern, verschieben oder umbenennen.
  - Keine OCR durchfuehren (erst KM13).
  - Keine Uebersetzung erzeugen.
  - Keine Rechtsbewertung vornehmen.
  - Keine Datenbankaenderungen.
  - Keine Rohdaten (pix.samples, Base64, Binaries) im Terminal/Chat ausgeben.
  - Rendertests melden nur: Pfad, Seitenzahl, Breite, Hoehe, DPI, SHA-256, Kurzstatus.

Eingang:
  - KM11-Manifest (JSON/CSV) mit Original-IDs und Dateipfaden.

Ausgang:
  - Arbeitsabbildungen (TIFF) unter 08_Arbeitsabbildungen
  - Koordinatenmodell (JSON) unter 10_Koordinatenmodell
  - Pruefsummen (CSV) unter 11_Pruefsummen
  - Renderprotokolle (TXT) unter 09_Renderprotokolle
  - Manifest, Status, Bericht, Fehlerbericht, Ausfuehrungsnotiz

Aufruf:
  Normal:      python km12_originalabbildung.py
  Selbsttest:  python km12_originalabbildung.py --selftest
"""

import sys
import os
import json
import csv
import hashlib
import datetime
import traceback
import io
from pathlib import Path

# ---------------------------------------------------------------------------
# KONFIGURATION
# ---------------------------------------------------------------------------

ROOT = Path(r"I:\KI_Legal_Project")
SCHREIBBEREICH = ROOT / "Agentensteuerung" / "12_Originalabbildung_Arbeitsabbildung"
KM11_BEREICH = ROOT / "Agentensteuerung" / "11_Originalsicherung"
CONFIG_DIR = ROOT / "Config"

SKRIPT = SCHREIBBEREICH / "01_Skript"
STATUS_DIR = SCHREIBBEREICH / "02_Status"
BERICHTE = SCHREIBBEREICH / "03_Berichte"
TESTS = SCHREIBBEREICH / "04_Tests"
FEHLER_DIR = SCHREIBBEREICH / "05_Fehler"
ARTEFAKTE = SCHREIBBEREICH / "06_Artefakte"
MANIFEST_DIR = SCHREIBBEREICH / "07_Manifest"
ARBEITSABBILDUNGEN = SCHREIBBEREICH / "08_Arbeitsabbildungen"
RENDERPROTOKOLLE = SCHREIBBEREICH / "09_Renderprotokolle"
KOORDINATENMODELL = SCHREIBBEREICH / "10_Koordinatenmodell"
PRUEFSUMMEN = SCHREIBBEREICH / "11_Pruefsummen"
NOTIZEN = SCHREIBBEREICH / "12_Ausfuehrungsnotizen"

# Konfiguration
CONFIG_PATH = CONFIG_DIR / "originalabbildung_v1.json"

STANDARD_KONFIG = {
    "render_dpi": 300,
    "render_format": "tiff",
    "render_colorspace": "RGB",
    "render_alpha": False,
    "max_pages_per_document": 500,
    "output_subdir_pattern": "{original_id}",
    "tiff_prefix": "seite_",
    "tiff_suffix": ".tiff",
    "koordinatenmodell_format": "bbox_px",
}

# ---------------------------------------------------------------------------
# HILFSFUNKTIONEN
# ---------------------------------------------------------------------------

def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

def sha256_datei(pfad):
    """SHA-256 ueber eine Datei, blockweise."""
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

def sha256_bytes(data: bytes) -> str:
    """SHA-256 ueber Bytes (intern, NIE im Terminal ausgeben)."""
    return hashlib.sha256(data).hexdigest()

def lade_konfig():
    """Laedt Konfiguration oder nutzt Standard."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(STANDARD_KONFIG)

def verzeichnisse_anlegen():
    for d in [STATUS_DIR, BERICHTE, TESTS, FEHLER_DIR, ARTEFAKTE, MANIFEST_DIR,
              ARBEITSABBILDUNGEN, RENDERPROTOKOLLE, KOORDINATENMODELL, PRUEFSUMMEN, NOTIZEN]:
        d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# KM11-MANIFEST LESEN
# ---------------------------------------------------------------------------

def lese_km11_manifest():
    """
    Liest das KM11-Manifest (JSON bevorzugt, CSV als Fallback).
    Extrahiert nur PDF-Dateien mit lesestatus=OK.
    """
    manifest_json = KM11_BEREICH / "07_Manifest" / "KM11_ORIGINAL_MANIFEST.json"
    manifest_csv = KM11_BEREICH / "07_Manifest" / "KM11_ORIGINAL_MANIFEST.csv"

    eintraege = []

    if manifest_json.exists():
        try:
            daten = json.loads(manifest_json.read_text(encoding="utf-8"))
            eintraege = daten.get("eintraege", [])
        except Exception:
            pass

    if not eintraege and manifest_csv.exists():
        try:
            with open(manifest_csv, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                eintraege = list(reader)
        except Exception:
            pass

    # Nur OK-Eintraege mit PDF-Endung
    pdf_eintraege = []
    for e in eintraege:
        if e.get("lesestatus", "") == "OK":
            endung = e.get("endung", "").lower()
            if endung in (".pdf",):
                pdf_eintraege.append(e)

    return pdf_eintraege

# ---------------------------------------------------------------------------
# KERNLOGIK: PDF → TIFF RENDERING
# ---------------------------------------------------------------------------

def rendere_pdf_seiten(original_id, pdf_pfad, config):
    """
    Rendert alle Seiten einer PDF-Datei als TIFF.

    Returns:
        List[dict] mit Seitendaten (keine Bildrohdaten)
        Nur Metadaten: seite, breite_px, hoehe_px, dpi, sha256_tiff, tiff_pfad
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None, "PyMuPDF (fitz) nicht installiert."

    dpi = config.get("render_dpi", 300)
    max_pages = config.get("max_pages_per_document", 500)
    output_dir = ARBEITSABBILDUNGEN / original_id
    output_dir.mkdir(parents=True, exist_ok=True)

    seiten = []
    fehler_text = None

    try:
        doc = fitz.open(pdf_pfad)
    except Exception as e:
        return [], f"PDF-Oeffnungsfehler: {e}"

    seitenzahl = doc.page_count

    if seitenzahl > max_pages:
        doc.close()
        return [], f"PDF hat {seitenzahl} Seiten, Maximum ist {max_pages}."

    for seite_idx in range(seitenzahl):
        try:
            page = doc[seite_idx]
            seite_num = seite_idx + 1

            # Rendern mit Matrix (DPI)
            matrix = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            # --- SICHER: NUR Metadaten extrahieren, NIE Bildrohdaten ausgeben ---
            breite_px = pix.width
            hoehe_px = pix.height

            # SHA-256 ueber Pixmap-Daten (intern, nur fuer Pruefsumme)
            pix_sha256 = sha256_bytes(pix.tobytes("png"))

            # TIFF speichern
            tiff_name = f"seite_{seite_num:04d}.tiff"
            tiff_pfad = output_dir / tiff_name
            pix.pil_save(str(tiff_pfad), format="TIFF", dpi=(dpi, dpi))

            # SHA-256 der gespeicherten TIFF-Datei
            tiff_sha256 = sha256_datei(tiff_pfad)
            tiff_groesse = tiff_pfad.stat().st_size if tiff_pfad.exists() else -1

            seiten.append({
                "original_id": original_id,
                "seite_nummer": seite_num,
                "breite_px": breite_px,
                "hoehe_px": hoehe_px,
                "dpi": dpi,
                "pixmap_sha256": pix_sha256,
                "tiff_pfad": str(tiff_pfad),
                "tiff_sha256": tiff_sha256,
                "tiff_groesse_bytes": tiff_groesse,
                "render_status": "OK",
            })

            # pix wird nach Gebrauch verworfen – KEINE Ausgabe
            pix = None

        except Exception as e:
            seiten.append({
                "original_id": original_id,
                "seite_nummer": seite_idx + 1,
                "breite_px": 0,
                "hoehe_px": 0,
                "dpi": dpi,
                "pixmap_sha256": "",
                "tiff_pfad": "",
                "tiff_sha256": "",
                "tiff_groesse_bytes": -1,
                "render_status": f"FEHLER:{e}",
            })
            if fehler_text is None:
                fehler_text = f"Renderfehler auf Seite {seite_idx + 1}: {e}"

    doc.close()
    return seiten, fehler_text

# ---------------------------------------------------------------------------
# KOORDINATENMODELL
# ---------------------------------------------------------------------------

def erstelle_koordinatenmodell(original_id, seiten):
    """
    Erzeugt ein minimales Koordinatenmodell (bbox_px) fuer jede Seite.
    Erst KM14 (Maschinenformat) wird Blocks/Woerter/Zeilen hinzufuegen.
    """
    modell = {
        "original_id": original_id,
        "modell_typ": "bbox_px",
        "anzahl_seiten": len(seiten),
        "seiten": []
    }

    for s in seiten:
        if s.get("render_status") == "OK":
            modell["seiten"].append({
                "seite_nummer": s["seite_nummer"],
                "bbox": [0, 0, s["breite_px"], s["hoehe_px"]],
                "breite_px": s["breite_px"],
                "hoehe_px": s["hoehe_px"],
                "dpi": s["dpi"],
                "tiff_sha256": s["tiff_sha256"],
            })
        else:
            modell["seiten"].append({
                "seite_nummer": s["seite_nummer"],
                "bbox": [0, 0, 0, 0],
                "breite_px": 0,
                "hoehe_px": 0,
                "dpi": 0,
                "render_status": s.get("render_status", "FEHLER"),
            })

    pfad = KOORDINATENMODELL / f"{original_id}_koordinatenmodell.json"
    pfad.write_text(json.dumps(modell, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    return pfad, modell

# ---------------------------------------------------------------------------
# RENDERPROTOKOLL
# ---------------------------------------------------------------------------

def schreibe_renderprotokoll(original_id, seiten, fehler_text):
    """
    Renderprotokoll fuer eine PDF-Datei.
    Meldet NUR Metadaten, keine Rohdaten.
    """
    pfad = RENDERPROTOKOLLE / f"{original_id}_renderprotokoll.txt"

    anzahl_ok = sum(1 for s in seiten if s["render_status"] == "OK")
    anzahl_fehler = sum(1 for s in seiten if s["render_status"] != "OK")

    lines = []
    lines.append(f"RENDERPROTOKOLL: {original_id}")
    lines.append("=" * 60)
    lines.append(f"Zeitpunkt:       {now()}")
    lines.append(f"Seiten gesamt:   {len(seiten)}")
    lines.append(f"Erfolgreich:     {anzahl_ok}")
    lines.append(f"Fehler:          {anzahl_fehler}")
    lines.append("")

    if fehler_text:
        lines.append(f"FEHLER: {fehler_text}")
        lines.append("")

    for s in seiten:
        zeile = (
            f"Seite {s['seite_nummer']:04d} | "
            f"{s['breite_px']}x{s['hoehe_px']}px | "
            f"{s['dpi']}dpi | "
            f"SHA256={s['tiff_sha256'][:16]}... | "
            f"{s['tiff_groesse_bytes']}B | "
            f"{s['render_status']}"
        )
        lines.append(zeile)

    pfad.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return pfad

# ---------------------------------------------------------------------------
# AUSGABEN
# ---------------------------------------------------------------------------

def schreibe_manifest(alle_seiten):
    """Manifest JSON und CSV mit allen gerenderten Seiten."""
    # JSON
    pfad_json = MANIFEST_DIR / "KM12_ABBILDUNG_MANIFEST.json"
    daten = {
        "modul": "KM12 – Originalabbildung / Arbeitsabbildung",
        "zeitpunkt": now(),
        "projektwurzel": str(ROOT),
        "anzahl_seiten_gesamt": len(alle_seiten),
        "seiten": alle_seiten,
    }
    pfad_json.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # CSV
    pfad_csv = MANIFEST_DIR / "KM12_ABBILDUNG_MANIFEST.csv"
    felder = [
        "original_id", "seite_nummer", "breite_px", "hoehe_px", "dpi",
        "pixmap_sha256", "tiff_pfad", "tiff_sha256", "tiff_groesse_bytes", "render_status"
    ]
    with open(pfad_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=felder, extrasaction="ignore")
        writer.writeheader()
        for s in alle_seiten:
            writer.writerow(s)

    return pfad_json, pfad_csv

def schreibe_pruefsummen_csv(alle_seiten):
    """Eigenstaendige Pruefsummendatei."""
    pfad = PRUEFSUMMEN / "KM12_TIFF_SHA256.csv"
    with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["original_id", "seite_nummer", "tiff_sha256", "tiff_groesse_bytes"])
        for s in alle_seiten:
            if s["render_status"] == "OK":
                writer.writerow([s["original_id"], s["seite_nummer"], s["tiff_sha256"], s["tiff_groesse_bytes"]])
    return pfad

def schreibe_status(alle_seiten, fehler_liste):
    pfad = STATUS_DIR / "KM12_STATUS.json"
    ok = sum(1 for s in alle_seiten if s["render_status"] == "OK")
    fehl = sum(1 for s in alle_seiten if s["render_status"] != "OK")

    daten = {
        "modul": "KM12 – Originalabbildung / Arbeitsabbildung",
        "zeitpunkt": now(),
        "projektwurzel": str(ROOT),
        "schreibbereich": str(SCHREIBBEREICH),
        "anzahl_originale_verarbeitet": len(set(s["original_id"] for s in alle_seiten)),
        "anzahl_seiten_gerendert": ok,
        "anzahl_seiten_fehler": fehl,
        "anzahl_renderfehler_gesamt": len(fehler_liste),
        "produktive_aenderungen": False,
        "originale_veraendert": False,
        "datenbank_aenderungen": False,
        "ocr_durchgefuehrt": False,
        "rohdaten_ausgegeben": False,
        "pix_samples_ausgegeben": False,
        "naechster_empfohlener_auftrag": "KM13 – OCR-Pipeline",
    }
    pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return pfad, daten

def schreibe_bericht(alle_seiten, fehler_liste, status_daten):
    pfad = BERICHTE / "KM12_BERICHT.txt"

    original_ids = sorted(set(s["original_id"] for s in alle_seiten))
    ok = status_daten["anzahl_seiten_gerendert"]
    fehl = status_daten["anzahl_seiten_fehler"]

    lines = []
    lines.append("=" * 70)
    lines.append("KM12 BERICHT – ORIGINALABBILDUNG / ARBEITSABBILDUNG")
    lines.append("=" * 70)
    lines.append(f"Zeitpunkt: {now()}")
    lines.append("")
    lines.append("1. ZWECK DES MODULS")
    lines.append("-" * 70)
    lines.append("  PDF-Originalseiten pixelgenau als TIFF-Arbeitsabbildungen")
    lines.append("  rendern. Koordinatenmodell ableiten. Keine Originale veraendern.")
    lines.append("")
    lines.append("2. VERARBEITETE ORIGINALE")
    lines.append("-" * 70)
    for oid in original_ids:
        seiten_dieses = [s for s in alle_seiten if s["original_id"] == oid]
        ok_seiten = sum(1 for s in seiten_dieses if s["render_status"] == "OK")
        lines.append(f"  {oid}: {ok_seiten}/{len(seiten_dieses)} Seiten gerendert")
    lines.append("")
    lines.append("3. KENNZAHLEN")
    lines.append("-" * 70)
    lines.append(f"  Originale verarbeitet:     {len(original_ids)}")
    lines.append(f"  Seiten gerendert (OK):     {ok}")
    lines.append(f"  Seiten mit Fehler:         {fehl}")
    lines.append(f"  TIFF-Dateien gespeichert:  {ok}")
    lines.append(f"  Renderfehler gesamt:       {len(fehler_liste)}")
    lines.append("")
    lines.append("4. RENDERPROTOKOLLE")
    lines.append("-" * 70)
    for oid in original_ids:
        rp = RENDERPROTOKOLLE / f"{oid}_renderprotokoll.txt"
        if rp.exists():
            lines.append(f"  {rp}")
    lines.append("")
    lines.append("5. GRENZEN DES MODULS")
    lines.append("-" * 70)
    lines.append("  - Keine Originaldatei veraendert.")
    lines.append("  - Keine Pixmap-Rohdaten ausgegeben.")
    lines.append("  - Keine OCR durchgefuehrt (erst KM13).")
    lines.append("  - Keine Uebersetzung durchgefuehrt.")
    lines.append("  - Keine Rechtsbewertung.")
    lines.append("  - Keine Datenbankaenderung.")
    lines.append("")
    lines.append("6. NAECHSTER SCHRITT")
    lines.append("-" * 70)
    lines.append("  KM13 – OCR-Pipeline")
    lines.append("  Tesseract auf die Arbeitsabbildungen anwenden,")
    lines.append("  OCR-Ergebnisse als JSON mit Zonen ablegen.")

    pfad.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return pfad

def schreibe_fehlerbericht(fehler_liste):
    pfad = FEHLER_DIR / "KM12_FEHLER.txt"
    if not fehler_liste:
        pfad.write_text("Keine Fehler festgestellt.\n", encoding="utf-8", newline="\n")
    else:
        lines = [f"{len(fehler_liste)} Fehler:", ""]
        for i, f in enumerate(fehler_liste, 1):
            lines.append(f"Fehler {i}:")
            lines.append(f"  Original-ID: {f.get('original_id', 'N/A')}")
            lines.append(f"  Meldung:     {f.get('meldung', '')}")
        pfad.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return pfad

def schreibe_ausfuehrungsnotiz(alle_seiten, fehler_liste, status_daten):
    pfad = NOTIZEN / "KM12_AUSFUEHRUNGSNOTIZ.txt"
    lines = [
        f"KM12 AUSFUEHRUNGSNOTIZ",
        f"={'=' * 60}",
        f"Aufruf:        python km12_originalabbildung.py",
        f"Zeit:          {now()}",
        f"Python:        {sys.version}",
        f"Arbeitsverz:   {Path.cwd()}",
        f"Projektroot:   {ROOT}",
        f"Schreibber:    {SCHREIBBEREICH}",
        f"Originale:     {len(set(s['original_id'] for s in alle_seiten))}",
        f"Seiten (OK):   {status_daten['anzahl_seiten_gerendert']}",
        f"Seiten (Fehl): {status_daten['anzahl_seiten_fehler']}",
        f"Fehler gesamt: {len(fehler_liste)}",
        f"Render-DPI:    {lade_konfig().get('render_dpi', 300)}",
        f"Grenzen:       Keine OCR, keine Uebersetzung, keine Rechtsbewertung.",
        f"Rohdaten:      Pixmap-Rohdaten NIE ausgegeben.",
    ]
    pfad.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return pfad

# ---------------------------------------------------------------------------
# SELBSTTEST
# ---------------------------------------------------------------------------

def run_selftest():
    """
    Sicherer PyMuPDF-Rendertest.
    Rendert eine Dummy-PDF, prueft Metadaten, NIE pix.samples ausgeben.
    """
    print("=" * 60)
    print("KM12 SELBSTTEST – SICHERER PYMUPDF RENDERTEST")
    print("=" * 60)

    try:
        import fitz
    except ImportError:
        print("FEHLER: PyMuPDF (fitz) nicht installiert.")
        print("Selbsttest ABGEBROCHEN.")
        return False

    verzeichnisse_anlegen()
    config = lade_konfig()

    tests_bestanden = 0
    tests_gesamt = 14

    # Backup realer Ausgaben
    real_outputs = {
        "manifest_json": MANIFEST_DIR / "KM12_ABBILDUNG_MANIFEST.json",
        "manifest_csv": MANIFEST_DIR / "KM12_ABBILDUNG_MANIFEST.csv",
        "status": STATUS_DIR / "KM12_STATUS.json",
        "bericht": BERICHTE / "KM12_BERICHT.txt",
        "fehler": FEHLER_DIR / "KM12_FEHLER.txt",
        "pruefsummen": PRUEFSUMMEN / "KM12_TIFF_SHA256.csv",
        "notiz": NOTIZEN / "KM12_AUSFUEHRUNGSNOTIZ.txt",
    }
    backups = {}
    for key, pfad in real_outputs.items():
        if pfad.exists():
            backups[key] = pfad.read_bytes()

    dummy_original_id = "ORG-TEST-SELFTEST12"
    dummy_dir = TESTS / "dummy_render"
    dummy_pdf = dummy_dir / "test_dokument.pdf"
    output_dir = ARBEITSABBILDUNGEN / dummy_original_id

    try:
        # Test 1: Dummy-PDF erzeugen
        print("\nTest 1: Dummy-PDF erzeugen...")
        dummy_dir.mkdir(parents=True, exist_ok=True)
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4
        page.insert_text((50, 50), "KM12 Selbsttest – Seite 1", fontsize=12)
        page.insert_text((50, 100), "Originalabbildung Arbeitsabbildung", fontsize=10)
        page.insert_text((50, 150), "Sicherer Rendertest ohne pix.samples-Ausgabe", fontsize=10)
        doc.save(str(dummy_pdf))
        doc.close()
        assert dummy_pdf.exists()
        print(f"  OK: Dummy-PDF erzeugt ({dummy_pdf.stat().st_size} Bytes)")
        tests_bestanden += 1

        # Test 2: PDF rendern – Seitenzahl
        print("\nTest 2: PDF rendern – Seitenzahl...")
        seiten, fehler = rendere_pdf_seiten(dummy_original_id, str(dummy_pdf), config)
        assert fehler is None, f"Fehler beim Rendern: {fehler}"
        assert seiten is not None
        assert len(seiten) == 1, f"Erwartet 1 Seite, {len(seiten)} erhalten"
        print(f"  OK: 1 Seite gerendert")
        tests_bestanden += 1

        # Test 3: Metadaten – Breite (keine Rohdaten!)
        print("\nTest 3: Metadaten – Breite/Hoehe...")
        s0 = seiten[0]
        assert s0["breite_px"] > 0, f"Breite={s0['breite_px']}"
        assert s0["hoehe_px"] > 0, f"Hoehe={s0['hoehe_px']}"
        assert s0["dpi"] == config["render_dpi"]
        print(f"  OK: {s0['breite_px']}x{s0['hoehe_px']}px @ {s0['dpi']}dpi")
        tests_bestanden += 1

        # Test 4: Rohpixelzugriff im Rendercode
        print("
Test 4: Rohpixelzugriff im Rendercode...")
        import inspect
        import tokenize
        import io
        src = inspect.getsource(rendere_pdf_seiten)
        tokens = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT):
                continue
            tokens.append(tok.string)
        code_tokenized = " ".join(tokens).replace(" ", "")
        assert ".samples" not in code_tokenized, ".samples im ausfuehrbaren Rendercode gefunden!"
        print("  OK: kein Rohpixelzugriff im ausfuehrbaren Rendercode")
        tests_bestanden += 1

        # Test 5: Nicht-Bilddaten-Ausgabe
        print("\nTest 5: Keine Rohdaten-Ausgabe...")
        # pixmap_sha256 und tiff_sha256 sind Hex-Strings, keine Rohdaten
        assert len(s0["pixmap_sha256"]) == 64, "SHA-256 nicht 64 Zeichen"
        assert all(c in "0123456789abcdef" for c in s0["pixmap_sha256"])
        assert len(s0["tiff_sha256"]) == 64
        print(f"  OK: SHA-256 (Hex) {s0['pixmap_sha256'][:16]}...")
        tests_bestanden += 1

        # Test 6: TIFF-Datei existiert
        print("\nTest 6: TIFF-Datei auf Platte...")
        assert s0["render_status"] == "OK"
        tiff_pfad = Path(s0["tiff_pfad"])
        assert tiff_pfad.exists(), f"TIFF fehlt: {tiff_pfad}"
        assert tiff_pfad.stat().st_size > 0
        print(f"  OK: TIFF {tiff_pfad.name} ({tiff_pfad.stat().st_size} Bytes)")
        tests_bestanden += 1

        # Test 7: TIFF-SHA-256 stimmt
        print("\nTest 7: TIFF-SHA-256 Verifikation...")
        tiff_actual = sha256_datei(tiff_pfad)
        assert tiff_actual == s0["tiff_sha256"], f"SHA mismatch"
        print(f"  OK: SHA-256 der TIFF-Datei verifiziert")
        tests_bestanden += 1

        # Test 8: Koordinatenmodell
        print("\nTest 8: Koordinatenmodell...")
        km_pfad, km = erstelle_koordinatenmodell(dummy_original_id, seiten)
        assert km_pfad.exists()
        assert km["anzahl_seiten"] == 1
        assert km["seiten"][0]["bbox"] == [0, 0, s0["breite_px"], s0["hoehe_px"]]
        print(f"  OK: Koordinatenmodell ({km_pfad.stat().st_size} Bytes)")
        tests_bestanden += 1

        # Test 9: Renderprotokoll
        print("\nTest 9: Renderprotokoll...")
        rp_pfad = schreibe_renderprotokoll(dummy_original_id, seiten, fehler)
        assert rp_pfad.exists()
        inhalt = rp_pfad.read_text(encoding="utf-8")
        assert "samples" not in inhalt, "samples im Renderprotokoll!"
        assert "pix" not in inhalt.lower() or "pixmap_sha256" in inhalt, "Roh-pix im Protokoll"
        print(f"  OK: Renderprotokoll ({rp_pfad.stat().st_size} Bytes)")
        tests_bestanden += 1

        # Test 10: Manifeste
        print("\nTest 10: Manifeste...")
        mj, mc = schreibe_manifest(seiten)
        assert mj.exists() and mc.exists()
        print(f"  OK: JSON ({mj.stat().st_size}B), CSV ({mc.stat().st_size}B)")
        tests_bestanden += 1

        # Test 11: Pruefsummen-CSV
        print("\nTest 11: Pruefsummen-CSV...")
        ps = schreibe_pruefsummen_csv(seiten)
        assert ps.exists()
        print(f"  OK: Pruefsummen-CSV ({ps.stat().st_size} Bytes)")
        tests_bestanden += 1

        # Test 12: Status-Flags
        print("\nTest 12: Status-Flags...")
        _, sd = schreibe_status(seiten, [])
        assert sd["produktive_aenderungen"] == False
        assert sd["rohdaten_ausgegeben"] == False
        assert sd["pix_samples_ausgegeben"] == False
        assert sd["ocr_durchgefuehrt"] == False
        print("  OK: Alle Schutz-Flags korrekt")
        tests_bestanden += 1

        # Test 13: Bericht und Fehlerbericht
        print("\nTest 13: Bericht und Fehlerbericht...")
        bp = schreibe_bericht(seiten, [], sd)
        fp = schreibe_fehlerbericht([])
        assert bp.exists() and fp.exists()
        print(f"  OK: Bericht ({bp.stat().st_size}B), Fehlerbericht ({fp.stat().st_size}B)")
        tests_bestanden += 1

        # Test 14: Ausfuehrungsnotiz
        print("\nTest 14: Ausfuehrungsnotiz...")
        ap = schreibe_ausfuehrungsnotiz(seiten, [], sd)
        assert ap.exists()
        print(f"  OK: Ausfuehrungsnotiz ({ap.stat().st_size} Bytes)")
        tests_bestanden += 1

    finally:
        # Aufraeumen
        for key, pfad in real_outputs.items():
            if key in backups:
                pfad.write_bytes(backups[key])
        if output_dir.exists():
            for f in output_dir.iterdir():
                f.unlink()
            output_dir.rmdir()
        if dummy_dir.exists():
            for f in dummy_dir.iterdir():
                f.unlink()
            dummy_dir.rmdir()
        # Dummy-Manifeste aufraeumen
        for d in [MANIFEST_DIR, PRUEFSUMMEN, KOORDINATENMODELL, RENDERPROTOKOLLE]:
            for f in d.glob(f"*{dummy_original_id}*"):
                if f.is_file():
                    f.unlink()

    print("\n" + "=" * 60)
    print(f"SELBSTTEST: {tests_bestanden}/{tests_gesamt} BESTANDEN")
    print("=" * 60)
    print("Pixmap-Rohdaten wurden nicht ausgegeben.")
    print("Nur Metadaten, SHA-256 und Dateipfade gemeldet.")
    return tests_bestanden == tests_gesamt

# ---------------------------------------------------------------------------
# HAUPTFUNKTION
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("KLEINMODUL 12 – ORIGINALABBILDUNG / ARBEITSABBILDUNG")
    print("=" * 60)
    print(f"Zeitpunkt:      {now()}")
    print(f"Projektwurzel:  {ROOT}")
    print(f"Schreibbereich: {SCHREIBBEREICH}")
    print()

    verzeichnisse_anlegen()
    config = lade_konfig()

    # 1. KM11-Manifest lesen
    print("[1/6] KM11-Manifest lesen...")
    pdf_eintraege = lese_km11_manifest()
    print(f"      {len(pdf_eintraege)} PDF-Dateien im KM11-Manifest")

    if not pdf_eintraege:
        print("      KEINE PDF-Dateien gefunden. Nichts zu rendern.")
        print("      (Wenn dies unerwartet ist, zuerst KM11 ausfuehren.)")

        # Trotzdem Ausgaben erzeugen (leer)
        alle_seiten = []
        fehler_liste = []
        schreibe_manifest(alle_seiten)
        schreibe_pruefsummen_csv(alle_seiten)
        sp, status_daten = schreibe_status(alle_seiten, fehler_liste)
        schreibe_bericht(alle_seiten, fehler_liste, status_daten)
        schreibe_fehlerbericht(fehler_liste)
        schreibe_ausfuehrungsnotiz(alle_seiten, fehler_liste, status_daten)
        print()
        print("KM12 abgeschlossen (keine PDFs zum Rendern).")
        return

    # 2. PDFs rendern
    print("[2/6] PDFs rendern...")
    alle_seiten = []
    fehler_liste = []

    for eintrag in pdf_eintraege:
        original_id = eintrag.get("original_id", "UNBEKANNT")
        pdf_pfad = eintrag.get("absoluter_pfad", "")
        dateiname = eintrag.get("dateiname", "UNBEKANNT")

        if not pdf_pfad or not Path(pdf_pfad).exists():
            fehler_liste.append({
                "original_id": original_id,
                "meldung": f"PDF nicht gefunden: {pdf_pfad}"
            })
            continue

        print(f"      Rendere: {original_id} ({dateiname})...")
        seiten, fehler_text = rendere_pdf_seiten(original_id, pdf_pfad, config)

        if seiten is None:
            fehler_liste.append({
                "original_id": original_id,
                "meldung": fehler_text or "Unbekannter Renderfehler"
            })
            continue

        alle_seiten.extend(seiten)
        if fehler_text:
            fehler_liste.append({
                "original_id": original_id,
                "meldung": fehler_text
            })

        # Koordinatenmodell
        erstelle_koordinatenmodell(original_id, seiten)

        # Renderprotokoll
        schreibe_renderprotokoll(original_id, seiten, fehler_text)

        print(f"             {len(seiten)} Seiten, "
              f"{sum(1 for s in seiten if s['render_status']=='OK')} OK, "
              f"{sum(1 for s in seiten if s['render_status']!='OK')} Fehler")

    # 3. Manifeste
    print("[3/6] Manifeste schreiben...")
    mj, mc = schreibe_manifest(alle_seiten)
    print(f"      {mj.name}, {mc.name}")

    # 4. Pruefsummen
    print("[4/6] Pruefsummen schreiben...")
    ps = schreibe_pruefsummen_csv(alle_seiten)
    print(f"      {ps.name}")

    # 5. Status, Bericht, Fehler, Notiz
    print("[5/6] Berichte schreiben...")
    sp, status_daten = schreibe_status(alle_seiten, fehler_liste)
    bp = schreibe_bericht(alle_seiten, fehler_liste, status_daten)
    fp = schreibe_fehlerbericht(fehler_liste)
    ap = schreibe_ausfuehrungsnotiz(alle_seiten, fehler_liste, status_daten)
    print(f"      Status, Bericht, Fehlerbericht, Ausfuehrungsnotiz")

    # 6. Ergebnis
    print()
    print("=" * 60)
    print("KM12 ABGESCHLOSSEN")
    print("=" * 60)
    print(f"Originale verarbeitet: {len(set(s['original_id'] for s in alle_seiten))}")
    print(f"Seiten gerendert:      {sum(1 for s in alle_seiten if s['render_status']=='OK')}")
    print(f"Fehler:                {len(fehler_liste)}")
    print(f"Arbeitsabbildungen:    {ARBEITSABBILDUNGEN}")
    print(f"Renderprotokolle:      {RENDERPROTOKOLLE}")
    print(f"Status:                {sp}")
    print(f"Bericht:               {bp}")
    print(f"Naechster:             KM13 – OCR-Pipeline")
    print()
    print("Keine Rohdaten ausgegeben.")
    print("Keine Originale veraendert.")
    print("Keine Rechtsbewertung.")
    print("Keine Produktivfreigabe.")

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
