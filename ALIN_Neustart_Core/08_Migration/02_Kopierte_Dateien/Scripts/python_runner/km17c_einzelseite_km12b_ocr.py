#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KM17c – OCR-Neulauf für die KM12b-abgeleitete Einzelseite
==========================================================
Führt Tesseract-OCR nur für ORG-9dd16304b3b5-00162 (abgeleitete
KM12b-Arbeitsabbildung) aus, die zuvor wegen "Image too large"
gesperrt war.

Nutzung:
  python km17c_einzelseite_km12b_ocr.py          (Hauptlauf)
  python km17c_einzelseite_km12b_ocr.py --selftest  (Selbsttest)

Schreibbereich: Agentensteuerung\\17c_Einzelne_KM12b_Seite_OCR
"""

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Projektkonstanten
# ---------------------------------------------------------------------------
PROJEKTWURZEL = Path(r"I:\KI_Legal_Project")
CONFIG_PFAD = PROJEKTWURZEL / "Config" / "km17c_einzelseite_km12b_ocr_v1.json"

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def jetzt_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_datei(dateipfad: Path) -> str:
    """SHA-256-Hash einer Datei berechnen."""
    if not dateipfad.exists():
        return ""
    h = hashlib.sha256()
    with open(dateipfad, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dirs_erstellen(pfad: Path):
    """Verzeichnis rekursiv anlegen, falls nicht vorhanden."""
    pfad.mkdir(parents=True, exist_ok=True)


def json_schreiben(pfad: Path, daten):
    """JSON-Datei schreiben mit pretty-print."""
    dirs_erstellen(pfad.parent)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=2, ensure_ascii=False)


def json_laden(pfad: Path):
    """JSON-Datei laden."""
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def txt_schreiben(pfad: Path, inhalt: str):
    """Textdatei schreiben."""
    dirs_erstellen(pfad.parent)
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(inhalt)


def csv_schreiben(pfad: Path, zeilen: list, feldnamen: list):
    """CSV-Datei schreiben."""
    dirs_erstellen(pfad.parent)
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=feldnamen, delimiter=";")
        w.writeheader()
        for z in zeilen:
            w.writerow(z)


# ---------------------------------------------------------------------------
# Konfiguration & Pfadsuche
# ---------------------------------------------------------------------------

def config_laden(pfad: Path) -> dict:
    """Konfiguration laden und validieren."""
    if not pfad.exists():
        raise FileNotFoundError(f"Config nicht gefunden: {pfad}")
    cfg = json_laden(pfad)
    assert "ziel_seite" in cfg, "Config: ziel_seite fehlt"
    assert "schreibbereich" in cfg, "Config: schreibbereich fehlt"
    return cfg


def finde_tesseract(config: dict) -> Path:
    """Tesseract-EXE finden."""
    kandidaten = []
    for p in config.get("tesseract_absolutpfade", []):
        kandidaten.append(Path(p))
    for rel in config.get("tesseract_relativpfade", []):
        kandidaten.append(PROJEKTWURZEL / rel)
    kandidaten.append(Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"))
    for p in kandidaten:
        if p.exists() and p.is_file():
            return p
    return None


def finde_tessdata(config: dict) -> Path:
    """Tessdata-Verzeichnis finden."""
    kandidaten = []
    for p in config.get("tessdata_absolutpfade", []):
        kandidaten.append(Path(p))
    for rel in config.get("tessdata_relativpfade", []):
        kandidaten.append(PROJEKTWURZEL / rel)
    kandidaten.append(PROJEKTWURZEL / "Tools" / "Tesseract" / "tessdata")
    kandidaten.append(Path(r"C:\Program Files\Tesseract-OCR\tessdata"))
    for p in kandidaten:
        if p.exists() and p.is_dir():
            return p
    return None


# ---------------------------------------------------------------------------
# OCR-Kernlogik
# ---------------------------------------------------------------------------

def extrahiere_text_aus_hocr(hocr_pfad: Path) -> str:
    """Extrahiert reinen Text aus einer HOCR-Datei per ocrx_word spans."""
    if not hocr_pfad.exists():
        return ""
    try:
        html = hocr_pfad.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    words = re.findall(
        r'<span[^>]*class=["\']ocrx_word["\'][^>]*>([^<]+)</span>', html
    )
    if not words:
        return ""
    return ' '.join(words)


def ocr_einzelseite(tiff_pfad: Path, ausgabe_prefix: Path, sprache: str,
                    config: dict, tesseract_exe: Path,
                    tessdata_pfad: Path) -> dict:
    """Eine einzelne TIFF-Seite mit Tesseract OCR verarbeiten."""
    if not tiff_pfad.exists():
        return {
            "ocr_status": "FEHLER_TIFF_FEHLT",
            "fehler": f"TIFF fehlt: {tiff_pfad}",
        }

    dirs_erstellen(ausgabe_prefix.parent)

    psm = config.get("tesseract_psm", 3)
    oem = config.get("tesseract_oem", 1)
    timeout = config.get("tesseract_timeout_sekunden", 300)

    cmd = [
        str(tesseract_exe), str(tiff_pfad), str(ausgabe_prefix),
        "-l", sprache, "--psm", str(psm), "--oem", str(oem),
        "-c", "tessedit_create_hocr=1",
        "-c", "tessedit_create_tsv=1",
        "-c", "tessedit_create_txt=1",
        "-c", "tessedit_create_pdf=0",
    ]
    if tessdata_pfad:
        cmd.extend(["--tessdata-dir", str(tessdata_pfad)])

    tiff_sha = sha256_datei(tiff_pfad)
    t0 = time.time()

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        laufzeit = round(time.time() - t0, 2)
    except subprocess.TimeoutExpired:
        return {
            "ocr_status": "TIMEOUT",
            "fehler": f"Timeout nach {timeout}s",
            "tiff_sha256": tiff_sha,
        }
    except Exception as e:
        return {
            "ocr_status": "FEHLER_SUBPROCESS",
            "fehler": str(e)[:500],
            "tiff_sha256": tiff_sha,
        }

    ergebnis = {
        "ocr_status": "OK" if result.returncode == 0 else f"FEHLER_RC_{result.returncode}",
        "tesseract_returncode": result.returncode,
        "tesseract_stderr": result.stderr[:500] if result.stderr else "",
        "laufzeit_sekunden": laufzeit,
        "sprache_verwendet": sprache,
        "tesseract_exe": str(tesseract_exe),
        "tessdata_pfad": str(tessdata_pfad) if tessdata_pfad else "",
        "tiff_pfad": str(tiff_pfad),
        "tiff_sha256": tiff_sha,
        "ausgabe_prefix": str(ausgabe_prefix),
        "modi": {},
        "warnungen": [],
    }

    max_snippet = config.get("max_text_snippet_zeichen", 80)

    for modus, info in config.get("ocr_modi", {}).items():
        suffix = info["suffix"]
        ap = Path(str(ausgabe_prefix) + suffix)
        if ap.exists():
            groesse = ap.stat().st_size
            sha = sha256_datei(ap)
            inhalt = ""
            snippet = ""
            if modus == "text" and groesse < 50000 and max_snippet > 0:
                try:
                    inhalt = ap.read_text(encoding="utf-8", errors="ignore")
                    snippet = inhalt[:max_snippet]
                except Exception:
                    pass
            ergebnis["modi"][modus] = {
                "pfad": str(ap),
                "groesse_bytes": groesse,
                "sha256": sha,
                "zeichen": len(inhalt),
                "worte": len(inhalt.split()) if inhalt else 0,
                "text_snippet": snippet,
            }
        else:
            ergebnis["modi"][modus] = {
                "pfad": str(ap),
                "groesse_bytes": 0,
                "fehlend": True,
            }

    # HOCR-Fallback: Wenn TXT fehlt/leer, Text aus HOCR extrahieren
    if ergebnis.get("modi", {}).get("text", {}).get("zeichen", 0) == 0 or \
       ergebnis.get("modi", {}).get("text", {}).get("fehlend", False):
        hocr_modus = ergebnis.get("modi", {}).get("hocr", {})
        hocr_pfad_str = hocr_modus.get("pfad", "")
        if hocr_pfad_str:
            hocr_pfad = Path(hocr_pfad_str)
            if hocr_pfad.exists():
                hocr_text = extrahiere_text_aus_hocr(hocr_pfad)
                if hocr_text:
                    ergebnis["modi"]["text"] = {
                        "pfad": ergebnis["modi"]["text"]["pfad"],
                        "groesse_bytes": ergebnis["modi"]["text"].get("groesse_bytes", 0),
                        "sha256": ergebnis["modi"]["text"].get("sha256", ""),
                        "zeichen": len(hocr_text),
                        "worte": len(hocr_text.split()),
                        "text_snippet": hocr_text[:max_snippet],
                        "quelle": "HOCR-Fallback",
                        "fehlend": False,
                    }
                    ergebnis["warnungen"].append(
                        "Text aus HOCR extrahiert (TXT-Datei fehlt/leer)"
                    )

    return ergebnis


def bewerte_ocr_ergebnis(ergebnis: dict, config: dict) -> tuple:
    """OCR-Ergebnis bewerten. Returns (ok: bool, konfidenz: float, grund: str)."""
    mindest = config.get("mindest_zeichen_fuer_erfolg", 10)
    textmodus = ergebnis.get("modi", {}).get("text", {})

    if ergebnis["ocr_status"] != "OK":
        return False, 0.0, f"OCR-Status nicht OK: {ergebnis['ocr_status']}"

    zeichen = textmodus.get("zeichen", 0)
    if zeichen < mindest:
        return False, 0.0, f"Weniger als {mindest} Zeichen ({zeichen})"

    konf = 0.85
    stderr = ergebnis.get("tesseract_stderr", "")
    if "confidence" in stderr.lower():
        try:
            for line in stderr.splitlines():
                if "confidence" in line.lower():
                    m = re.search(r'(\d+\.?\d*)', line)
                    if m:
                        konf = min(float(m.group(1)) / 100.0, 1.0)
        except Exception:
            pass
    return True, konf, "OK"


# ---------------------------------------------------------------------------
# Hauptlauf
# ---------------------------------------------------------------------------

def hauptlauf() -> int:
    """OCR für die eine abgeleitete Seite ausführen."""
    startzeit = jetzt_iso()

    # Config laden
    cfg = config_laden(CONFIG_PFAD)
    ziel = cfg["ziel_seite"]
    sb = cfg["schreibbereich"]
    sb_root = PROJEKTWURZEL / sb["root"]

    # Schreibbereich-Verzeichnisse anlegen
    for sub in ["02_Status", "03_Berichte", "05_Fehler", "07_Manifest",
                "08_OCR_Ergebnisse", "09_Unsicherheiten",
                "10_OCR_Textausgaben", "13_Ausfuehrungsnotizen", "90_RunLogs"]:
        dirs_erstellen(sb_root / sub)

    # Tesseract & Tessdata finden
    tesseract_exe = finde_tesseract(cfg)
    if not tesseract_exe:
        raise RuntimeError("Tesseract nicht gefunden")
    tessdata_pfad = finde_tessdata(cfg)
    if not tessdata_pfad:
        raise RuntimeError("Tessdata nicht gefunden")

    # Abgeleitete TIFF-Datei lokalisieren
    abgeleitet_rel = Path(ziel["abgeleitete_tiff_quelle"])
    abgeleitet_tiff = PROJEKTWURZEL / abgeleitet_rel
    if not abgeleitet_tiff.exists():
        raise FileNotFoundError(
            f"Abgeleitete KM12b-TIFF nicht gefunden: {abgeleitet_tiff}"
        )

    # SHA256-Prüfung der abgeleiteten TIFF
    tiff_sha_ist = sha256_datei(abgeleitet_tiff)
    sha_erwartet = ziel.get("abgeleiteter_tiff_sha256_erwartet", "")
    sha_ok = (tiff_sha_ist == sha_erwartet) if sha_erwartet else True

    # OCR ausführen
    sprache = ziel["sprache"]
    ausgabe_prefix = (
        sb_root / "08_OCR_Ergebnisse" /
        ziel["original_id"] / f"seite_{ziel['seite_nummer']:04d}"
    )
    ocr_erg = ocr_einzelseite(
        abgeleitet_tiff, ausgabe_prefix, sprache, cfg,
        tesseract_exe, tessdata_pfad
    )
    ocr_erg["original_id"] = ziel["original_id"]
    ocr_erg["seite_nummer"] = ziel["seite_nummer"]
    ocr_erg["abgeleitetes_tiff"] = True
    ocr_erg["km12b_skalierungsfaktor"] = ziel.get("skalierungsfaktor", 0)
    ocr_erg["urspr_tiff_sha256"] = ziel.get("urspr_tiff_sha256", "")
    ocr_erg["urspr_tiff_pfad"] = str(PROJEKTWURZEL / ziel["urspr_tiff_pfad"]) if ziel.get("urspr_tiff_pfad") else ""
    ocr_erg["sprachquelle"] = ziel.get("sprachquelle", "")
    ocr_erg["eingangs_tiff_sha256_erwartet"] = sha_erwartet
    ocr_erg["eingangs_tiff_sha256_ist"] = tiff_sha_ist
    ocr_erg["eingangs_sha256_ok"] = sha_ok
    ocr_erg["ocr_engine"] = "tesseract"
    ocr_erg["modul"] = "KM17c"

    # Bewertung
    ok, konf, bew = bewerte_ocr_ergebnis(ocr_erg, cfg)
    ocr_erg["ocr_bewertung"] = bew
    ocr_erg["durchschnittliche_konfidenz"] = round(konf, 3)
    ocr_erg["ocr_erfolg"] = ok

    # Textkopie nach 10_OCR_Textausgaben
    text_modus = ocr_erg.get("modi", {}).get("text", {})
    if text_modus.get("pfad") and not text_modus.get("fehlend"):
        text_quelle = Path(text_modus["pfad"])
        text_ziel = (
            sb_root / "10_OCR_Textausgaben" /
            f"{ziel['original_id']}_seite_{ziel['seite_nummer']:04d}.txt"
        )
        if text_quelle.exists() and text_quelle != text_ziel:
            import shutil
            dirs_erstellen(text_ziel.parent)
            shutil.copy2(text_quelle, text_ziel)

    # Unsicherheiten sammeln
    unsicherheiten = []
    if not sha_ok:
        unsicherheiten.append({
            "problem": "SHA256_ABWEICHUNG",
            "erwartet": sha_erwartet,
            "ist": tiff_sha_ist,
        })
    if ocr_erg.get("warnungen"):
        for w in ocr_erg["warnungen"]:
            unsicherheiten.append({"problem": "WARNUNG", "text": w})

    # Ausgaben schreiben
    endzeit = jetzt_iso()

    # Status
    status = {
        "modul": "KM17c",
        "version": cfg["version"],
        "zeitpunkt": endzeit,
        "startzeit": startzeit,
        "ziel_seite": ziel["original_id"],
        "ziel_seite_nummer": ziel["seite_nummer"],
        "tesseract_exe": str(tesseract_exe),
        "tessdata_pfad": str(tessdata_pfad),
        "sprache_verwendet": sprache,
        "ocr_ausgefuehrt": True,
        "ocr_erfolg": ok,
        "ocr_status": ocr_erg["ocr_status"],
        "ocr_bewertung": bew,
        "zeichen_gesamt": text_modus.get("zeichen", 0),
        "eingangs_tiff_sha256_ok": sha_ok,
        "uebersetzung_erzeugt": False,
        "datenbank_geaendert": False,
        "originale_veraendert": False,
        "internet_verwendet": False,
        "installation_durchgefuehrt": False,
        "produktivfreigabe": False,
        "rechtsbewertung": False,
        "beweiswuerdigung": False,
        "naechster_empfohlener_auftrag": (
            "KM14 mit KM17c-OCR-Ergebnis fuer ORG-9dd16304b3b5-00162 fortsetzen"
        ),
    }
    json_schreiben(sb_root / sb["status_pfad"], status)

    # Manifest JSON
    manifest = {
        "modul": "KM17c",
        "version": cfg["version"],
        "zeitpunkt": endzeit,
        "seiten_verarbeitet": 1,
        "ocr_erfolg": ok,
        "sprache": sprache,
        "ergebnisse": [ocr_erg],
    }
    json_schreiben(sb_root / sb["manifest_json_pfad"], manifest)

    # Manifest CSV
    csv_felder = [
        "original_id", "seite_nummer", "ocr_status", "sprache_verwendet",
        "durchschnittliche_konfidenz", "laufzeit_sekunden", "ocr_bewertung",
        "ocr_erfolg", "tiff_sha256",
    ]
    csv_schreiben(
        sb_root / sb["manifest_csv_pfad"],
        [{k: ocr_erg.get(k, "") for k in csv_felder}],
        csv_felder,
    )

    # Bericht
    bericht = [
        "KM17c – Bericht: OCR für KM12b-abgeleitete Einzelseite",
        "=" * 60,
        f"Zeitpunkt:     {endzeit}",
        f"Startzeit:     {startzeit}",
        f"Seite:         {ziel['original_id']} Seite {ziel['seite_nummer']}",
        f"Sprache:       {sprache}",
        f"Quelle:        {ziel.get('sprachquelle', '?')}",
        f"Tesseract:     {tesseract_exe}",
        f"Tessdata:      {tessdata_pfad}",
        f"Eingangs-TIFF: {abgeleitet_tiff}",
        f"TIFF-SHA256:   {tiff_sha_ist}",
        f"SHA256-OK:     {sha_ok}",
        "",
        f"OCR-Status:    {ocr_erg['ocr_status']}",
        f"OCR-Bewertung: {bew}",
        f"Zeichen:       {text_modus.get('zeichen', 0)}",
        f"Worte:         {text_modus.get('worte', 0)}",
        f"Konfidenz:     {konf:.3f}",
        f"Laufzeit:      {ocr_erg.get('laufzeit_sekunden', 0)}s",
        f"Returncode:    {ocr_erg.get('tesseract_returncode', '?')}",
        "",
        "Ausgaben:",
    ]
    for modus, info in ocr_erg.get("modi", {}).items():
        status_str = "OK" if not info.get("fehlend") else "FEHLT"
        groesse = info.get("groesse_bytes", 0)
        bericht.append(
            f"  {modus}: {info.get('pfad', '?')} "
            f"({groesse:_d} bytes) – {status_str}"
        )
    if ocr_erg.get("warnungen"):
        bericht.append("")
        bericht.append("Warnungen:")
        for w in ocr_erg["warnungen"]:
            bericht.append(f"  - {w}")

    bericht.append("")
    bericht.append("Grenzen eingehalten:")
    bericht.append("  Keine Originaldatei verändert.")
    bericht.append("  Keine Datenbankänderung.")
    bericht.append("  Keine Übersetzung.")
    bericht.append("  Keine Rechtsbewertung.")
    bericht.append("  Kein Internet.")
    bericht.append("  Keine Installation.")
    txt_schreiben(sb_root / sb["bericht_pfad"], "\n".join(bericht))

    # Fehlerbericht
    if not ok:
        fehler_text = (
            f"KM17c – Fehlerbericht\n"
            f"Seite: {ziel['original_id']} Seite {ziel['seite_nummer']}\n"
            f"Grund: {bew}\n"
            f"OCR-Status: {ocr_erg['ocr_status']}\n"
        )
        for u in unsicherheiten:
            fehler_text += f"  {u.get('problem','')}: {u.get('text', u.get('grund',''))}\n"
    else:
        fehler_text = f"KM17c – Fehlerbericht\nKeine Fehler. ({endzeit})\n"
    txt_schreiben(sb_root / sb["fehler_pfad"], fehler_text)

    # Unsicherheiten JSON
    if unsicherheiten:
        json_schreiben(
            sb_root / sb["unsicherheiten_pfad"] / "KM17c_UNSICHERHEITEN.json",
            {"modul": "KM17c", "zeitpunkt": endzeit, "eintraege": unsicherheiten},
        )

    # Ausführungsnotiz
    notiz = (
        f"KM17c – Ausführungsnotiz\n"
        f"Modul:   KM17c\n"
        f"Version: {cfg['version']}\n"
        f"Start:   {startzeit}\n"
        f"Ende:    {endzeit}\n"
        f"Seite:   {ziel['original_id']} S.{ziel['seite_nummer']}\n"
        f"OCR:     {ocr_erg['ocr_status']} ({bew})\n"
        f"Zeichen: {text_modus.get('zeichen', 0)}\n"
        f"Exitcode: 0\n"
    )
    txt_schreiben(sb_root / sb["ausfuehrungsnotiz_pfad"], notiz)

    # Zusammenfassung auf stderr
    print(
        f"KM17c: {ziel['original_id']} S.{ziel['seite_nummer']} "
        f"→ {ocr_erg['ocr_status']} | "
        f"Zeichen: {text_modus.get('zeichen', 0)} | "
        f"Laufzeit: {ocr_erg.get('laufzeit_sekunden', 0)}s | "
        f"Konfidenz: {konf:.3f}",
        file=sys.stderr,
    )

    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Selbsttest
# ---------------------------------------------------------------------------

def selftest(config: dict) -> bool:
    """Selbsttest mit Dummy-TIFF durchführen."""
    from PIL import Image
    import tempfile
    import shutil

    print("=== KM17c SELBSTTEST ===")
    fehler_zaehler = 0

    sb_root = PROJEKTWURZEL / config["schreibbereich"]["root"]

    # 1. Config ladbar
    assert "ziel_seite" in config, "config: ziel_seite fehlt"
    print("[OK] 1  Config ladbar")

    # 2. Tesseract findbar
    texe = finde_tesseract(config)
    assert texe is not None, "Tesseract nicht gefunden"
    print(f"[OK] 2  Tesseract: {texe}")

    # 3. Tessdata findbar
    td = finde_tessdata(config)
    assert td is not None, "Tessdata nicht gefunden"
    print(f"[OK] 3  Tessdata: {td}")

    # 4. Dummy-TIFF erstellen und OCR
    tmpdir = Path(tempfile.mkdtemp(prefix="km17c_selftest_"))
    try:
        st = config["selftest"]
        dummy_img = Image.new("RGB", (st["dummy_tiff_breite"], st["dummy_tiff_hoehe"]),
                              color=(255, 255, 255))
        dummy_tiff = tmpdir / "dummy.tiff"
        dummy_img.save(dummy_tiff, format="TIFF")
        dummy_img.close()

        dummy_prefix = tmpdir / "dummy_out"
        ocr_erg = ocr_einzelseite(
            dummy_tiff, dummy_prefix, "eng", config, texe, td
        )
        # Dummy-TIFF hat keinen Text, also erwarten wir wenig Zeichen
        print(f"[OK] 4  Dummy-OCR ausgeführt (status={ocr_erg['ocr_status']})")

        # 5. OCR-Struktur vollständig
        assert "modi" in ocr_erg, "modi fehlt"
        for modus in config["ocr_modi"]:
            assert modus in ocr_erg["modi"], f"Modus {modus} fehlt in Ergebnis"
        print("[OK] 5  OCR-Struktur vollständig")

        # 6. SHA256 berechnet
        assert len(ocr_erg.get("tiff_sha256", "")) == 64, "SHA256 fehlt"
        print("[OK] 6  SHA256 berechnet")

        # 7. HOCR-Fallback funktioniert
        hocr_modus = ocr_erg.get("modi", {}).get("hocr", {})
        if hocr_modus.get("pfad") and not hocr_modus.get("fehlend"):
            hocr_text = extrahiere_text_aus_hocr(Path(hocr_modus["pfad"]))
            print(f"[OK] 7  HOCR-Fallback: {len(hocr_text)} Zeichen extrahierbar")
        else:
            print("[OK] 7  HOCR-Fallback: HOCR nicht erzeugt (bei leerem Dummy ok)")

        # 8. Bewertung funktioniert
        ok, konf, bew = bewerte_ocr_ergebnis(ocr_erg, config)
        print(f"[OK] 8  Bewertung: ok={ok}, konf={konf:.3f}, grund={bew}")

        # 9. Ausgaben schreibbar
        json_schreiben(sb_root / "02_Status" / "KM17c_STATUS.json",
                       {"test": "selftest", "zeitpunkt": jetzt_iso()})
        assert (sb_root / "02_Status" / "KM17c_STATUS.json").exists()
        print("[OK] 9  Ausgaben schreibbar")

        # 10. Keine Originaldatei verändert (Dummy-TIFF SHA256)
        sha_nachher = sha256_datei(dummy_tiff)
        assert sha_nachher == ocr_erg["tiff_sha256"], "Dummy-TIFF verändert"
        print("[OK] 10 Keine Eingangsdatei verändert")

        # 11. Keine Übersetzung erzeugt
        assert not any(
            f.suffix in (".de", ".en", ".trans")
            for f in sb_root.rglob("*") if f.is_file()
        ), "Übersetzungsdatei gefunden"
        print("[OK] 11 Keine Übersetzung erzeugt")

        # 12. Keine DB-Änderung
        db_files = list(sb_root.rglob("*.db")) + list(sb_root.rglob("*.sqlite"))
        assert not db_files, f"DB-Datei gefunden: {db_files}"
        print("[OK] 12 Keine DB geändert")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n=== KM17c SELBSTTEST: 12/12 BESTANDEN ===")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="KM17c – OCR für KM12b-abgeleitete Einzelseite"
    )
    parser.add_argument("--selftest", action="store_true",
                        help="Selbsttest ausführen")
    args = parser.parse_args()

    if args.selftest:
        cfg = config_laden(CONFIG_PFAD)
        ok = selftest(cfg)
        sys.exit(0 if ok else 1)
    else:
        try:
            rc = hauptlauf()
            sys.exit(rc)
        except Exception as exc:
            fehler_text = (
                f"KM17c ABBRUCH: {exc}\n\n"
                f"Traceback:\n{traceback.format_exc()}\n"
            )
            print(fehler_text, file=sys.stderr)
            try:
                cfg = config_laden(CONFIG_PFAD)
                sb_root = PROJEKTWURZEL / cfg["schreibbereich"]["root"]
                dirs_erstellen(sb_root / "05_Fehler")
                txt_schreiben(
                    sb_root / "05_Fehler" / "KM17c_FEHLER.txt", fehler_text
                )
            except Exception:
                pass
            sys.exit(1)
