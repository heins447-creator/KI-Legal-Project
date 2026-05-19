#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KM12b – Behandlung übergroßer Arbeitsabbildungen
=================================================
Erkennt übergroße TIFF-Arbeitsabbildungen und erstellt OCR-taugliche
abgeleitete Kopien via kontrolliertem Downscaling.

Nutzung:
  python km12b_uebergrosse_arbeitsabbildungen.py          (Hauptlauf)
  python km12b_uebergrosse_arbeitsabbildungen.py --selftest  (Selbsttest)

Schreibbereich: Agentensteuerung\\12b_Uebergrosse_Arbeitsabbildungen
"""

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Projektkonstanten
# ---------------------------------------------------------------------------
PROJEKTWURZEL = Path(r"I:\KI_Legal_Project")
CONFIG_PFAD = PROJEKTWURZEL / "Config" / "km12b_uebergrosse_arbeitsabbildungen_v1.json"

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def jetzt_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_datei(dateipfad: Path) -> str:
    """SHA-256-Hash einer Datei berechnen."""
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


def csv_schreiben(pfad: Path, zeilen: list, feldnamen: list):
    """CSV-Datei schreiben."""
    dirs_erstellen(pfad.parent)
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=feldnamen, delimiter=";")
        w.writeheader()
        for z in zeilen:
            w.writerow(z)


def txt_schreiben(pfad: Path, inhalt: str):
    """Textdatei schreiben."""
    dirs_erstellen(pfad.parent)
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(inhalt)


# ---------------------------------------------------------------------------
# Kernlogik
# ---------------------------------------------------------------------------

def config_laden(pfad: Path) -> dict:
    """Konfiguration laden und validieren."""
    if not pfad.exists():
        raise FileNotFoundError(f"Config nicht gefunden: {pfad}")
    return json_laden(pfad)


def km12_manifest_laden(quellpfad: Path) -> dict:
    """KM12-Abbildungsmanifest laden."""
    if not quellpfad.exists():
        raise FileNotFoundError(f"KM12-Manifest nicht gefunden: {quellpfad}")
    return json_laden(quellpfad)


def seite_klassifizieren(seite: dict, limits: dict) -> dict:
    """Eine KM12-Seite gegen Limits prüfen.

    Returns dict mit keys:
      original_id, seite_nummer, breite_px, hoehe_px, tiff_pfad, tiff_sha256,
      tiff_groesse_bytes, gesamtpixel, klassifikation, ueberschreitungen,
      render_status
    """
    breite = seite.get("breite_px", 0)
    hoehe = seite.get("hoehe_px", 0)
    gesamt = breite * hoehe
    groesse = seite.get("tiff_groesse_bytes", 0)

    ueberschreitungen = []
    if breite > limits["max_breite_px"]:
        ueberschreitungen.append(f"breite {breite} > {limits['max_breite_px']}")
    if hoehe > limits["max_hoehe_px"]:
        ueberschreitungen.append(f"hoehe {hoehe} > {limits['max_hoehe_px']}")
    if gesamt > limits["max_gesamtpixel"]:
        ueberschreitungen.append(f"gesamtpixel {gesamt} > {limits['max_gesamtpixel']}")
    if groesse > limits["max_dateigroesse_bytes"]:
        ueberschreitungen.append(
            f"dateigroesse {groesse:_d} > {limits['max_dateigroesse_bytes']:_d}"
        )

    klassifikation = "NORMAL" if not ueberschreitungen else "UEBERGROSS"

    return {
        "original_id": seite["original_id"],
        "seite_nummer": seite["seite_nummer"],
        "breite_px": breite,
        "hoehe_px": hoehe,
        "gesamtpixel": gesamt,
        "tiff_pfad": seite.get("tiff_pfad", ""),
        "tiff_sha256": seite.get("tiff_sha256", ""),
        "tiff_groesse_bytes": groesse,
        "klassifikation": klassifikation,
        "ueberschreitungen": ueberschreitungen,
        "render_status": seite.get("render_status", ""),
    }


def downscale_tiff(seite: dict, limits: dict, downscale_cfg: dict,
                   schreibbereich_root: Path) -> dict:
    """Übergroße TIFF-Seite herunter skalieren.

    Returns dict mit Ergebnisfeldern oder Fehler.
    """
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None

    eingabe_pfad = Path(seite["tiff_pfad"])
    if not eingabe_pfad.exists():
        return {"status": "FEHLER", "grund": f"TIFF nicht gefunden: {eingabe_pfad}"}

    ziel_hoehe = downscale_cfg["target_max_hoehe_px"]
    orig_breite = seite["breite_px"]
    orig_hoehe = seite["hoehe_px"]

    faktor = ziel_hoehe / orig_hoehe
    neue_breite = int(orig_breite * faktor)
    neue_hoehe = ziel_hoehe

    # Prüfen ob nach dem Downscaling immer noch ein Limit überschritten wird
    neue_pixel = neue_breite * neue_hoehe
    if neue_pixel > limits["max_gesamtpixel"]:
        return {
            "status": "SPERRUNG",
            "grund": (
                f"Auch nach Downscaling ({neue_breite}x{neue_hoehe}) "
                f"noch {neue_pixel:_d} Pixel > Limit {limits['max_gesamtpixel']:_d}"
            ),
        }

    # Ausgabeverzeichnis
    oid = seite["original_id"]
    snum = seite["seite_nummer"]
    ausgabe_dir = schreibbereich_root / "08_Abgeleitete_Arbeitsabbildungen" / oid
    dirs_erstellen(ausgabe_dir)
    ausgabe_pfad = ausgabe_dir / f"seite_{snum:04d}_downscaled.tiff"

    try:
        im = Image.open(eingabe_pfad)
        orig_mode = im.mode
        orig_dpi = im.info.get("dpi", (300, 300))

        # Downscaling
        filter_name = downscale_cfg.get("resample_filter", "LANCZOS")
        resample = getattr(Image, filter_name, Image.LANCZOS)

        im_resized = im.resize((neue_breite, neue_hoehe), resample)

        # DPI beibehalten
        dpi_tuple = orig_dpi if downscale_cfg.get("dpi_beibehalten", True) else (300, 300)
        im_resized.info["dpi"] = dpi_tuple

        # Speichern
        compression = downscale_cfg.get("output_compression", "tiff_adobe_deflate")
        im_resized.save(
            str(ausgabe_pfad),
            format="TIFF",
            compression=compression,
            dpi=dpi_tuple,
        )
        im.close()
        im_resized.close()

        # Nachberechnung
        ausgabe_sha = sha256_datei(ausgabe_pfad)
        ausgabe_groesse = ausgabe_pfad.stat().st_size

        return {
            "status": "DOWNSCALED",
            "orig_breite_px": orig_breite,
            "orig_hoehe_px": orig_hoehe,
            "orig_mode": orig_mode,
            "neu_breite_px": neue_breite,
            "neu_hoehe_px": neue_hoehe,
            "skalierungsfaktor": round(faktor, 6),
            "abgeleiteter_pfad": str(ausgabe_pfad),
            "abgeleiteter_sha256": ausgabe_sha,
            "abgeleiteter_groesse_bytes": ausgabe_groesse,
            "resample": filter_name,
        }
    except MemoryError:
        return {"status": "SPERRUNG",
                "grund": "Speicher unzureichend für Downscaling – Seitensplitting empfohlen"}
    except Exception as e:
        return {"status": "FEHLER",
                "grund": f"Downscaling-Fehler: {e}"}


def verarbeite_alle_seiten(manifest: dict, config: dict) -> dict:
    """Alle Seiten aus KM12-Manifest prüfen und ggf. downscalen.

    Returns dict mit Status, Manifest-Zeilen, Rückbindung, Statistik.
    """
    limits = config["limits"]
    downscale_cfg = config["downscaling"]
    sb_root = Path(config["schreibbereich"]["root"])

    seiten = manifest.get("seiten", [])
    ergebnisse = []
    rueckbindungen = []

    stat_normal = 0
    stat_uebergross_downscaled = 0
    stat_uebergross_gesperrt = 0
    stat_fehler = 0

    for seite in seiten:
        klass = seite_klassifizieren(seite, limits)
        eintrag = dict(klass)

        if klass["klassifikation"] == "NORMAL":
            eintrag["behandlung"] = "KEINE"
            eintrag["behandlungsstatus"] = "OK"
            stat_normal += 1

        elif klass["klassifikation"] == "UEBERGROSS":
            ds_ergebnis = downscale_tiff(seite, limits, downscale_cfg, sb_root)
            eintrag["behandlung"] = "DOWNSCALING"
            eintrag["behandlungsstatus"] = ds_ergebnis["status"]

            if ds_ergebnis["status"] == "DOWNSCALED":
                eintrag["abgeleiteter_pfad"] = ds_ergebnis["abgeleiteter_pfad"]
                eintrag["abgeleiteter_sha256"] = ds_ergebnis["abgeleiteter_sha256"]
                eintrag["abgeleiteter_groesse_bytes"] = ds_ergebnis["abgeleiteter_groesse_bytes"]
                eintrag["skalierungsfaktor"] = ds_ergebnis["skalierungsfaktor"]
                eintrag["neu_breite_px"] = ds_ergebnis["neu_breite_px"]
                eintrag["neu_hoehe_px"] = ds_ergebnis["neu_hoehe_px"]
                stat_uebergross_downscaled += 1

                # Rückbindungseintrag
                rueckbindungen.append({
                    "original_id": eintrag["original_id"],
                    "seite_nummer": eintrag["seite_nummer"],
                    "urspr_tiff_pfad": seite["tiff_pfad"],
                    "urspr_tiff_sha256": seite["tiff_sha256"],
                    "abgeleiteter_tiff_pfad": ds_ergebnis["abgeleiteter_pfad"],
                    "abgeleiteter_tiff_sha256": ds_ergebnis["abgeleiteter_sha256"],
                    "skalierungsfaktor": ds_ergebnis["skalierungsfaktor"],
                    "aktion": "downscale",
                    "hinweis": "Abgeleitete Arbeitskopie – Original unverändert",
                })

            elif ds_ergebnis["status"] == "SPERRUNG":
                eintrag["sperrgrund"] = ds_ergebnis["grund"]
                stat_uebergross_gesperrt += 1

            else:
                eintrag["fehlergrund"] = ds_ergebnis["grund"]
                stat_fehler += 1

        ergebnisse.append(eintrag)

    return {
        "ergebnisse": ergebnisse,
        "rueckbindungen": rueckbindungen,
        "statistik": {
            "seiten_gesamt": len(seiten),
            "normal": stat_normal,
            "uebergross_downscaled": stat_uebergross_downscaled,
            "uebergross_gesperrt": stat_uebergross_gesperrt,
            "fehler": stat_fehler,
        },
    }


def schreibe_ausgaben(ergebnis_dict: dict, config: dict, startzeit: str):
    """Alle Ausgabedateien schreiben."""
    sb = config["schreibbereich"]
    sb_root = Path(sb["root"])

    stats = ergebnis_dict["statistik"]
    endzeit = jetzt_iso()

    # ---- Status ----
    status_daten = {
        "modul": "KM12b",
        "version": config["version"],
        "zeitpunkt": endzeit,
        "startzeit": startzeit,
        "limits": config["limits"],
        "downscaling_config": config["downscaling"],
        "statistik": stats,
        "rueckbindungen_anzahl": len(ergebnis_dict["rueckbindungen"]),
    }
    json_schreiben(sb_root / sb["status_pfad"], status_daten)

    # ---- Manifest JSON ----
    manifest_json = {
        "modul": "KM12b",
        "version": config["version"],
        "zeitpunkt": endzeit,
        "limits": config["limits"],
        "statistik": stats,
        "ergebnisse": ergebnis_dict["ergebnisse"],
    }
    json_schreiben(sb_root / sb["manifest_json_pfad"], manifest_json)

    # ---- Manifest CSV ----
    csv_felder = [
        "original_id", "seite_nummer", "breite_px", "hoehe_px", "gesamtpixel",
        "tiff_groesse_bytes", "klassifikation", "behandlungsstatus",
        "skalierungsfaktor", "neu_breite_px", "neu_hoehe_px",
        "abgeleiteter_pfad", "abgeleiteter_sha256",
    ]
    csv_zeilen = []
    for e in ergebnis_dict["ergebnisse"]:
        z = {k: e.get(k, "") for k in csv_felder}
        z["tiff_groesse_bytes"] = e.get("tiff_groesse_bytes", "")
        csv_zeilen.append(z)
    csv_schreiben(sb_root / sb["manifest_csv_pfad"], csv_zeilen, csv_felder)

    # ---- SHA256 CSV ----
    sha_felder = [
        "original_id", "seite_nummer", "urspr_tiff_sha256",
        "abgeleiteter_tiff_sha256", "abgeleiteter_pfad",
    ]
    sha_zeilen = []
    for r in ergebnis_dict["rueckbindungen"]:
        sha_zeilen.append({
            "original_id": r["original_id"],
            "seite_nummer": r["seite_nummer"],
            "urspr_tiff_sha256": r["urspr_tiff_sha256"],
            "abgeleiteter_tiff_sha256": r["abgeleiteter_tiff_sha256"],
            "abgeleiteter_pfad": r["abgeleiteter_tiff_pfad"],
        })
    csv_schreiben(sb_root / sb["sha256_csv_pfad"], sha_zeilen, sha_felder)

    # ---- Rückbindung ----
    json_schreiben(
        sb_root / sb["rueckbindung_pfad"],
        {
            "modul": "KM12b",
            "version": config["version"],
            "zeitpunkt": endzeit,
            "beschreibung": "Rückbindung abgeleiteter Arbeitsabbildungen an KM12-Originale",
            "rueckbindungen": ergebnis_dict["rueckbindungen"],
        },
    )

    # ---- Bericht ----
    bericht_zeilen = [
        "KM12b – Bericht: Übergroße Arbeitsabbildungen",
        "=" * 60,
        f"Zeitpunkt: {endzeit}",
        f"Startzeit: {startzeit}",
        "",
        f"Seiten geprüft:      {stats['seiten_gesamt']}",
        f"Normal (OK):          {stats['normal']}",
        f"Übergroß downscaled: {stats['uebergross_downscaled']}",
        f"Übergroß gesperrt:   {stats['uebergross_gesperrt']}",
        f"Fehler:              {stats['fehler']}",
        "",
        "Limits:",
        f"  max_breite_px:          {config['limits']['max_breite_px']}",
        f"  max_hoehe_px:           {config['limits']['max_hoehe_px']}",
        f"  max_gesamtpixel:        {config['limits']['max_gesamtpixel']}",
        f"  max_dateigroesse_bytes: {config['limits']['max_dateigroesse_bytes']}",
        "",
        f"Downscaling target_max_hoehe_px: {config['downscaling']['target_max_hoehe_px']}",
        "",
        "Details:",
    ]

    for e in ergebnis_dict["ergebnisse"]:
        bericht_zeilen.append("")
        bericht_zeilen.append(
            f"  {e['original_id']} Seite {e['seite_nummer']}: "
            f"{e['breite_px']}x{e['hoehe_px']}px, "
            f"{e['tiff_groesse_bytes']:_d} bytes → {e['klassifikation']}"
        )
        if e["klassifikation"] == "UEBERGROSS":
            bericht_zeilen.append(f"    Überschreitungen: {e.get('ueberschreitungen', [])}")
            bericht_zeilen.append(f"    Behandlung: {e.get('behandlungsstatus', '?')}")
            if e.get("abgeleiteter_pfad"):
                bericht_zeilen.append(f"    Abgeleitet: {e['abgeleiteter_pfad']}")
                bericht_zeilen.append(
                    f"    Skalierungsfaktor: {e['skalierungsfaktor']}, "
                    f"Neu: {e['neu_breite_px']}x{e['neu_hoehe_px']}px"
                )
            if e.get("sperrgrund"):
                bericht_zeilen.append(f"    Sperrgrund: {e['sperrgrund']}")
            if e.get("fehlergrund"):
                bericht_zeilen.append(f"    Fehler: {e['fehlergrund']}")

    txt_schreiben(sb_root / sb["bericht_pfad"], "\n".join(bericht_zeilen))

    # ---- Fehlerbericht ----
    fehler_eintraege = [e for e in ergebnis_dict["ergebnisse"]
                        if e.get("behandlungsstatus") in ("FEHLER", "SPERRUNG")]
    if fehler_eintraege:
        fz = [
            "KM12b – Fehlerbericht",
            "=" * 60,
            f"Zeitpunkt: {endzeit}",
            f"Fehler-/Sperreinträge: {len(fehler_eintraege)}",
            "",
        ]
        for e in fehler_eintraege:
            fz.append(f"  {e['original_id']} S.{e['seite_nummer']}: "
                      f"{e.get('behandlungsstatus')} — "
                      f"{e.get('sperrgrund', e.get('fehlergrund', '?'))}")
        txt_schreiben(sb_root / sb["fehler_pfad"], "\n".join(fz))
    else:
        txt_schreiben(
            sb_root / sb["fehler_pfad"],
            f"KM12b – Fehlerbericht\nKeine Fehler oder Sperrungen. ({endzeit})\n",
        )

    # ---- Ausführungsnotiz ----
    notiz = (
        f"KM12b – Ausführungsnotiz\n"
        f"Modul:  {config['modul']}\n"
        f"Version: {config['version']}\n"
        f"Start:  {startzeit}\n"
        f"Ende:   {endzeit}\n"
        f"Exitcode: 0\n"
    )
    txt_schreiben(sb_root / sb["ausfuehrungsnotiz_pfad"], notiz)


# ---------------------------------------------------------------------------
# Selbsttest
# ---------------------------------------------------------------------------

def selftest(config: dict):
    """Selbsttest mit Dummy-Bilddaten durchführen."""
    from PIL import Image
    import tempfile

    print("=== KM12b SELBSTTEST ===")
    fehler = []
    sb_root = Path(config["schreibbereich"]["root"])
    limits = config["limits"]

    # 1. Config ladbar
    assert "limits" in config, "Config unvollständig"
    print("[OK] 1  Config ladbar")

    # 2. Größenlimit wird erkannt
    dummy_ue = config["selftest"]["dummy_uebergross"]
    assert dummy_ue["breite_px"] > limits["max_breite_px"] or \
           dummy_ue["hoehe_px"] > limits["max_hoehe_px"] or \
           (dummy_ue["breite_px"] * dummy_ue["hoehe_px"]) > limits["max_gesamtpixel"], \
           "Dummy-übergroß muss Limits überschreiten"
    print("[OK] 2  Größenlimit wird erkannt")

    # 3. Dummy-Bilder erstellen
    tmpdir = Path(tempfile.mkdtemp(prefix="km12b_selftest_"))
    try:
        # Normale Dummy-Seite
        dn = config["selftest"]["dummy_normal"]
        normal_img = Image.new("RGB", (dn["breite_px"], dn["hoehe_px"]), color=(200, 200, 200))
        normal_tiff = tmpdir / "normal.tiff"
        normal_img.save(normal_tiff, format="TIFF")
        normal_img.close()

        # Übergroße Dummy-Seite (klein gehalten für schnellen Test)
        du = config["selftest"]["dummy_uebergross"]
        # Für den Test eine skalierte Version mit gleichem Seitenverhältnis verwenden
        test_hoehe = limits["max_hoehe_px"] + 1000  # 16000 > 15000, garantiert UEBERGROSS
        test_breite = int(du["breite_px"] * test_hoehe / du["hoehe_px"])
        ue_img = Image.new("RGB", (test_breite, test_hoehe), color=(100, 100, 255))
        ue_tiff = tmpdir / "uebergross.tiff"
        ue_img.save(ue_tiff, format="TIFF")
        ue_img.close()

        # Manifests für Test bauen
        test_manifest = {
            "seiten": [
                {
                    "original_id": "TEST-NORMAL-001",
                    "seite_nummer": 1,
                    "breite_px": dn["breite_px"],
                    "hoehe_px": dn["hoehe_px"],
                    "tiff_pfad": str(normal_tiff),
                    "tiff_sha256": sha256_datei(normal_tiff),
                    "tiff_groesse_bytes": normal_tiff.stat().st_size,
                    "render_status": "OK",
                },
                {
                    "original_id": "TEST-UEBERGROSS-001",
                    "seite_nummer": 1,
                    "breite_px": test_breite,
                    "hoehe_px": test_hoehe,
                    "tiff_pfad": str(ue_tiff),
                    "tiff_sha256": sha256_datei(ue_tiff),
                    "tiff_groesse_bytes": ue_tiff.stat().st_size,
                    "render_status": "OK",
                },
            ]
        }

        # 4. Normale Seite bleibt unverändert
        klass_norm = seite_klassifizieren(test_manifest["seiten"][0], limits)
        assert klass_norm["klassifikation"] == "NORMAL", \
            f"Normale Seite falsch klassifiziert: {klass_norm['klassifikation']}"
        print("[OK] 3  Normale TIFF-Seite bleibt unverändert")

        # 5. Übergroße Dummy-Seite wird markiert
        klass_ue = seite_klassifizieren(test_manifest["seiten"][1], limits)
        # Die Test-Übergroße könnte mit 5000 Höhe unter dem Limit sein, prüfen wir die Breite
        assert klass_ue["klassifikation"] == "UEBERGROSS", \
    f"UEBERGROSS erwartet, ist: {klass_ue['klassifikation']} " \
    f"(breite={test_breite}, hoehe={test_hoehe})"
        print("[OK] 4  Übergroße Dummy-Seite wird markiert")

        # 6. Verarbeitung durchführen
        erg_dict = verarbeite_alle_seiten(test_manifest, config)
        print("[OK] 5  Verarbeitung durchgeführt")

        # 7. Abgeleitete Arbeitskopie getrennt gespeichert
        for e in erg_dict["ergebnisse"]:
            if e["klassifikation"] == "UEBERGROSS" and e.get("abgeleiteter_pfad"):
                assert "08_Abgeleitete_Arbeitsabbildungen" in e["abgeleiteter_pfad"], \
                    "Abgeleitete Datei nicht im korrekten Pfad"
                assert e["abgeleiteter_pfad"] != e.get("tiff_pfad", ""), \
                    "Abgeleitete Datei überschreibt Original"
        print("[OK] 6  Abgeleitete Arbeitskopie getrennt gespeichert")

        # 8. SHA256 berechnet
        for r in erg_dict["rueckbindungen"]:
            assert len(r["abgeleiteter_tiff_sha256"]) == 64, "SHA256 fehlt"
        print("[OK] 7  SHA256 berechnet")

        # 9. Rückbindung geschrieben
        assert len(erg_dict["rueckbindungen"]) > 0, "Keine Rückbindungen"
        print("[OK] 8  Rückbindung geschrieben")

        # 10. Ausgaben schreiben
        schreibe_ausgaben(erg_dict, config, jetzt_iso())
        print("[OK] 9  Ausgaben geschrieben")

        # 11. Keine Originaldatei verändert (SHA256 vergleichen)
        for seite in test_manifest["seiten"]:
            aktuell = sha256_datei(Path(seite["tiff_pfad"]))
            assert aktuell == seite["tiff_sha256"], \
                f"Original {seite['original_id']} verändert!"
        print("[OK] 10 Keine Originaldatei verändert")

        # 12. Keine OCR-Ausgabe
        for e in erg_dict["ergebnisse"]:
            assert not any(k.startswith("ocr_") for k in e), "OCR-Feld gefunden"
        print("[OK] 11 Keine OCR ausgeführt")

        # 13. Keine Übersetzungsdatei
        assert not (sb_root / "Uebersetzungen").exists(), "Übersetzungsdatei gefunden"
        print("[OK] 12 Keine Übersetzung erzeugt")

        # 14. Keine DB-Änderung
        db_files = list(sb_root.rglob("*.db")) + list(sb_root.rglob("*.sqlite"))
        assert not db_files, f"DB-Datei gefunden: {db_files}"
        print("[OK] 13 Keine DB geändert")

        # 15. Statusdatei geschrieben
        assert (sb_root / config["schreibbereich"]["status_pfad"]).exists(), \
            "Status nicht geschrieben"
        print("[OK] 14 Statusdatei geschrieben")

        # 16. Manifest geschrieben
        assert (sb_root / config["schreibbereich"]["manifest_json_pfad"]).exists(), \
            "Manifest nicht geschrieben"
        print("[OK] 15 Manifest geschrieben")

        # 17. JSON gültig
        json_s = json_laden(sb_root / config["schreibbereich"]["status_pfad"])
        assert json_s["statistik"]["seiten_gesamt"] == 2
        print("[OK] 16 JSON-Dateien gültig")

    finally:
        # Aufräumen
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

        # Dummy-Ausgaben aus SB löschen
        shutil.rmtree(sb_root / "08_Abgeleitete_Arbeitsabbildungen", ignore_errors=True)

    print("\n=== KM12b SELBSTTEST: 16/16 BESTANDEN ===")
    return True


# ---------------------------------------------------------------------------
# Hauptlauf
# ---------------------------------------------------------------------------

def hauptlauf():
    """Hauptlauf: KM12-Manifest lesen, Seiten klassifizieren, downscalen."""
    startzeit = jetzt_iso()

    # Config laden
    cfg = config_laden(CONFIG_PFAD)

    # KM12-Manifest laden
    km12_pfad = Path(cfg["quellen"]["km12_manifest_pfad"])
    manifest = km12_manifest_laden(km12_pfad)

    # Schreibbereich vorbereiten
    sb_root = Path(cfg["schreibbereich"]["root"])
    for sub in ["02_Status", "03_Berichte", "05_Fehler", "07_Manifest",
                "08_Abgeleitete_Arbeitsabbildungen", "09_Pruefsummen",
                "10_Rueckbindung", "13_Ausfuehrungsnotizen", "90_RunLogs"]:
        dirs_erstellen(sb_root / sub)

    # Alle Seiten verarbeiten
    erg_dict = verarbeite_alle_seiten(manifest, cfg)

    # Ausgaben schreiben
    schreibe_ausgaben(erg_dict, cfg, startzeit)

    # Kurzstatus auf stderr
    s = erg_dict["statistik"]
    print(
        f"KM12b: {s['seiten_gesamt']} Seiten geprüft, "
        f"{s['normal']} normal, "
        f"{s['uebergross_downscaled']} downscaled, "
        f"{s['uebergross_gesperrt']} gesperrt, "
        f"{s['fehler']} Fehler",
        file=sys.stderr,
    )
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KM12b – Übergroße Arbeitsabbildungen")
    parser.add_argument("--selftest", action="store_true", help="Selbsttest ausführen")
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
                f"KM12b ABBRUCH: {exc}\n\n"
                f"Traceback:\n{traceback.format_exc()}\n"
            )
            print(fehler_text, file=sys.stderr)
            # Fehlerbericht schreiben falls möglich
            try:
                cfg = config_laden(CONFIG_PFAD)
                sb_root = Path(cfg["schreibbereich"]["root"])
                dirs_erstellen(sb_root / "05_Fehler")
                txt_schreiben(sb_root / "05_Fehler" / "KM12b_FEHLER.txt", fehler_text)
            except Exception:
                pass
            sys.exit(1)
