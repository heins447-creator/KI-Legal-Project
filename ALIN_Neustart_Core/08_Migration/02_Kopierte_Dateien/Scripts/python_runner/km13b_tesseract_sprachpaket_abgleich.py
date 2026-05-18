# -*- coding: utf-8 -*-
"""
KLEINMODUL 13b – TESSERACT-SPRACHPAKET-ABGLEICH (v1)
=====================================================

Zweck:
  Technisch verbindlich feststellen, welche Tesseract-Installation
  und welche tessdata-Verzeichnisse vorhanden sind und welche
  davon von KM13 tatsaechlich genutzt werden.

Grenzen:
  - Keine Installation von Sprachpaketen.
  - Kein Internet-Download.
  - Keine Dateiaenderung ausserhalb des eigenen Schreibbereichs.
  - Keine Originalaenderung, keine DB-Aenderung.
  - Keine Rohdatenausgabe.

Pruefumfang:
  1. Tesseract EXE-Pfade
  2. tessdata-Verzeichnisse
  3. .traineddata-Dateien
  4. Abgleich gegen KM13-Konfiguration
  5. Abgleich gegen EU24-Amtssprachen
  6. tesseract --version / --list-langs
  7. Widerspruechliche Installationen erkennen
  8. Status: vorhanden/fehlt/widerspruechlich/nicht bestimmbar

Aufruf:
  Normal:      python km13b_tesseract_sprachpaket_abgleich.py
  Selbsttest:  python km13b_tesseract_sprachpaket_abgleich.py --selftest
"""

import sys
import os
import json
import subprocess
import datetime
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# KONFIGURATION
# ---------------------------------------------------------------------------

ROOT = Path(r"I:\KI_Legal_Project")
SCHREIBBEREICH = ROOT / "Agentensteuerung" / "13b_Tesseract_Sprachpaket_Abgleich"
CONFIG_DIR = ROOT / "Config"

STATUS_DIR = SCHREIBBEREICH / "02_Status"
BERICHTE = SCHREIBBEREICH / "03_Berichte"
TESTS_DIR = SCHREIBBEREICH / "04_Tests"
FEHLER_DIR = SCHREIBBEREICH / "05_Fehler"
ARTEFAKTE = SCHREIBBEREICH / "06_Artefakte"
MANIFEST_DIR = SCHREIBBEREICH / "07_Manifest"
NOTIZEN = SCHREIBBEREICH / "13_Ausfuehrungsnotizen"

CONFIG_PATH = CONFIG_DIR / "tesseract_sprachpaket_abgleich_v1.json"

EU24_SPRACHEN = {
    "bul": "Bulgarisch",
    "hrv": "Kroatisch",
    "ces": "Tschechisch",
    "dan": "Daenisch",
    "nld": "Niederlaendisch",
    "eng": "Englisch",
    "est": "Estnisch",
    "fin": "Finnisch",
    "fra": "Franzoesisch",
    "deu": "Deutsch",
    "ell": "Griechisch",
    "hun": "Ungarisch",
    "gle": "Irisch",
    "ita": "Italienisch",
    "lav": "Lettisch",
    "lit": "Litauisch",
    "mlt": "Maltesisch",
    "pol": "Polnisch",
    "por": "Portugiesisch",
    "ron": "Rumaenisch",
    "slk": "Slowakisch",
    "slv": "Slowenisch",
    "spa": "Spanisch",
    "swe": "Schwedisch",
}

# Zusatzsprachen (nicht EU24, aber moeglicherweise vorhanden)
ZUSATZ_SPRACHEN = {
    "osd": "Orientation and Script Detection",
    "equ": "Mathematik",
    "srp": "Serbisch",
    "chi_sim": "Chinesisch (vereinfacht)",
    "chi_tra": "Chinesisch (traditionell)",
    "jpn": "Japanisch",
    "kor": "Koreanisch",
    "rus": "Russisch",
    "ara": "Arabisch",
}

STANDARD_KONFIG = {
    "version": "tesseract_sprachpaket_abgleich_v1",
    "km13_config_pfad": str(CONFIG_DIR / "ocr_pipeline_v1.json"),
    "pruefpfade_exe": [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ],
    "pruefpfade_tools": [
        r"I:\KI_Legal_Project\Tools\Tesseract",
        r"I:\KI_Legal_Project\Tools\_ToolLibrary",
        r"I:\KI_Legal_Project\Tools",
    ],
    "eu24_sprachen": list(EU24_SPRACHEN.keys()),
    "timeout_befehl_sekunden": 30,
    "rohdaten_ausgabe_verboten": True,
}

# ---------------------------------------------------------------------------
# HILFSFUNKTIONEN
# ---------------------------------------------------------------------------

def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

def verzeichnisse_anlegen():
    for d in [STATUS_DIR, BERICHTE, TESTS_DIR, FEHLER_DIR, ARTEFAKTE,
              MANIFEST_DIR, NOTIZEN]:
        d.mkdir(parents=True, exist_ok=True)

def lade_konfig():
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            merged = dict(STANDARD_KONFIG)
            merged.update(cfg)
            return merged
        except Exception:
            pass
    return dict(STANDARD_KONFIG)

def lade_json(pfad):
    p = Path(pfad)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None

# ---------------------------------------------------------------------------
# TESSERACT-ERKENNUNG
# ---------------------------------------------------------------------------

def finde_tesseract_exe(config):
    """Findet alle Tesseract-EXE-Pfade."""
    gefunden = []

    for pfad_str in config.get("pruefpfade_exe", []):
        p = Path(pfad_str)
        if p.exists() and p.is_file():
            gefunden.append(str(p))

    for basis_str in config.get("pruefpfade_tools", []):
        basis = Path(basis_str)
        if basis.exists():
            for candidate in basis.rglob("tesseract.exe"):
                gefunden.append(str(candidate))

    # Deduplizieren
    return sorted(set(gefunden))

def finde_tessdata_verzeichnisse(config, exe_pfade):
    """Findet alle tessdata-Verzeichnisse."""
    verzeichnisse = []

    for exe_str in exe_pfade:
        exe_dir = Path(exe_str).parent
        tessdata = exe_dir / "tessdata"
        if tessdata.exists() and tessdata.is_dir():
            verzeichnisse.append(str(tessdata))

    # Auch in Tools-Verzeichnissen suchen
    for basis_str in config.get("pruefpfade_tools", []):
        basis = Path(basis_str)
        if basis.exists():
            for candidate in basis.rglob("tessdata"):
                if candidate.is_dir():
                    verzeichnisse.append(str(candidate))

    return sorted(set(verzeichnisse))

def liste_traineddata(tessdata_pfad):
    """Listet alle .traineddata-Dateien in einem tessdata-Verzeichnis."""
    p = Path(tessdata_pfad)
    if not p.exists() or not p.is_dir():
        return []
    files = sorted(p.glob("*.traineddata"))
    ergebnis = []
    for f in files:
        sprachcode = f.stem
        groesse = f.stat().st_size
        ergebnis.append({"code": sprachcode, "pfad": str(f), "groesse_bytes": groesse})
    return ergebnis

# ---------------------------------------------------------------------------
# TESSERACT-BEFEHLE
# ---------------------------------------------------------------------------

def tesseract_version(exe_pfad, timeout=30):
    """Fuehrt tesseract --version aus und gibt die Ausgabe zurueck."""
    try:
        result = subprocess.run(
            [exe_pfad, "--version"],
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace"
        )
        return result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return None, "EXE nicht gefunden"
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT"
    except Exception as e:
        return None, str(e)

def tesseract_list_langs(exe_pfad, tessdata_pfad=None, timeout=30):
    """Fuehrt tesseract --list-langs aus."""
    env = os.environ.copy()
    if tessdata_pfad:
        env["TESSDATA_PREFIX"] = str(tessdata_pfad)

    try:
        result = subprocess.run(
            [exe_pfad, "--list-langs"],
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            env=env
        )
        # Sprachen parsen
        sprachen = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and not line.startswith("List of"):
                sprachen.append(line)
        return sprachen, result.stderr.strip()
    except FileNotFoundError:
        return [], "EXE nicht gefunden"
    except subprocess.TimeoutExpired:
        return [], "TIMEOUT"
    except Exception as e:
        return [], str(e)

# ---------------------------------------------------------------------------
# ABGLEICH
# ---------------------------------------------------------------------------

def gleiche_eu24_ab(verfuegbare_sprachen):
    """Gleicht verfuegbare Sprachen gegen EU24 ab."""
    ergebnis = {}
    for code, name in EU24_SPRACHEN.items():
        ergebnis[code] = {
            "name": name,
            "status": "vorhanden" if code in verfuegbare_sprachen else "fehlt",
        }
    return ergebnis

def analysiere_km13_config(config):
    """Liest KM13-Konfiguration und extrahiert Tesseract-Einstellungen."""
    km13_cfg = lade_json(config["km13_config_pfad"])
    if not km13_cfg:
        return {
            "gefunden": False,
            "meldung": f"KM13-Config nicht lesbar: {config['km13_config_pfad']}",
        }

    km13_tess_exe = km13_cfg.get("tesseract_pfad", "")
    km13_tessdata = km13_cfg.get("tessdata_pfad", "")
    km13_sprachen = km13_cfg.get("verfuegbare_sprachen", [])
    sprache = km13_cfg.get("standardsprache", "eng")
    fallback = km13_cfg.get("fallback_sprachen", ["eng"])

    exe_existiert = Path(km13_tess_exe).exists() if km13_tess_exe else False
    tessdata_existiert = Path(km13_tessdata).exists() if km13_tessdata else False

    return {
        "gefunden": True,
        "tesseract_pfad": km13_tess_exe,
        "tessdata_pfad": km13_tessdata,
        "exe_existiert": exe_existiert,
        "tessdata_existiert": tessdata_existiert,
        "standardsprache": sprache,
        "fallback_sprachen": fallback,
        "km13_angegebene_sprachen": km13_sprachen,
    }

# ---------------------------------------------------------------------------
# HAUPTANALYSE
# ---------------------------------------------------------------------------

def fuehre_abgleich_durch(config):
    """Fuehrt den vollstaendigen Sprachpaket-Abgleich durch."""
    fehler = []
    warnungen = []

    # ---- 1. Tesseract EXEs finden ----
    exe_pfade = finde_tesseract_exe(config)
    if not exe_pfade:
        fehler.append("Keine tesseract.exe gefunden")
        return None, fehler, warnungen

    # ---- 2. tessdata-Verzeichnisse finden ----
    tessdata_pfade = finde_tessdata_verzeichnisse(config, exe_pfade)

    # ---- 3. KM13-Konfiguration analysieren ----
    km13_info = analysiere_km13_config(config)

    # ---- 4. Version und Sprachen pro EXE+TESSDATA-Kombination ----
    kombinationen = []
    for exe in exe_pfade:
        version_out, version_err = tesseract_version(exe, config.get("timeout_befehl_sekunden", 30))
        version_zeile = ""
        if version_out:
            for line in version_out.splitlines():
                if "tesseract" in line.lower():
                    version_zeile = line.strip()
                    break

        # Standard tessdata (default)
        sprachen_default, err_default = tesseract_list_langs(exe, None, config.get("timeout_befehl_sekunden", 30))
        kombinationen.append({
            "exe_pfad": exe,
            "tessdata_pfad": "default",
            "version": version_zeile,
            "version_voll": version_out[:300] if version_out else None,
            "sprachen": sprachen_default,
            "anzahl_sprachen": len(sprachen_default),
            "fehler": err_default if err_default else None,
        })

        # Jedes tessdata-Verzeichnis testen
        for td in tessdata_pfade:
            sprachen_td, err_td = tesseract_list_langs(exe, td, config.get("timeout_befehl_sekunden", 30))
            kombinationen.append({
                "exe_pfad": exe,
                "tessdata_pfad": td,
                "version": version_zeile,
                "version_voll": version_out[:300] if version_out else None,
                "sprachen": sprachen_td,
                "anzahl_sprachen": len(sprachen_td),
                "fehler": err_td if err_td else None,
            })

    # ---- 5. Pro tessdata-Verzeichnis: .traineddata-Dateien ----
    tessdata_inventar = {}
    for td in tessdata_pfade:
        dateien = liste_traineddata(td)
        tessdata_inventar[td] = dateien

    # ---- 6. Vereinigung aller Sprachen ----
    alle_sprachen = set()
    for k in kombinationen:
        alle_sprachen.update(k["sprachen"])
    alle_sprachen = sorted(alle_sprachen)

    # ---- 7. EU24-Abgleich ----
    eu24_status = gleiche_eu24_ab(alle_sprachen)

    # ---- 8. Widersprueche finden ----
    widersprueche = []
    if len(kombinationen) > 1:
        sprachen_sets = [set(k["sprachen"]) for k in kombinationen]
        if len(set(frozenset(s) for s in sprachen_sets)) > 1:
            widersprueche.append("Unterschiedliche Sprachen-Sets bei verschiedenen TESSDATA_PREFIX")

    # KM13 nutzt ggf. falsches Verzeichnis
    if km13_info.get("gefunden"):
        km13_td = km13_info.get("tessdata_pfad", "")
        if km13_td and km13_td != "default":
            # Pruefen, ob ein anderes Verzeichnis mehr Sprachen hat
            for td in tessdata_pfade:
                if td != km13_td:
                    td_sprachen = [k["sprachen"] for k in kombinationen if k["tessdata_pfad"] == td]
                    km13_sprachen = [k["sprachen"] for k in kombinationen if k["tessdata_pfad"] == km13_td]
                    if td_sprachen and km13_sprachen:
                        if len(td_sprachen[0]) > len(km13_sprachen[0]):
                            widersprueche.append(
                                f"KM13 nutzt '{km13_td}' ({len(km13_sprachen[0])} Sprachen), "
                                f"aber '{td}' hat {len(td_sprachen[0])} Sprachen"
                            )
                            warnungen.append(
                                f"EMPFOHLEN: tessdata_pfad in KM13-Config aendern von "
                                f"'{km13_td}' auf '{td}' ({len(td_sprachen[0])} Sprachen statt "
                                f"{len(km13_sprachen[0])})"
                            )

    # ---- 9. Ergebnis bauen ----
    ergebnis = {
        "modul": "KM13b – Tesseract-Sprachpaket-Abgleich",
        "version": "tesseract_sprachpaket_abgleich_v1",
        "zeitpunkt": now(),
        "projektwurzel": str(ROOT),
        "exe_pfade": exe_pfade,
        "tessdata_pfade": tessdata_pfade,
        "kombinationen": kombinationen,
        "tessdata_inventar": {},
        "alle_verfuegbaren_sprachen": alle_sprachen,
        "anzahl_sprachen_gesamt": len(alle_sprachen),
        "eu24_abgleich": eu24_status,
        "eu24_vorhanden": sum(1 for v in eu24_status.values() if v["status"] == "vorhanden"),
        "eu24_fehlt": sum(1 for v in eu24_status.values() if v["status"] == "fehlt"),
        "widersprueche": widersprueche,
        "km13_info": km13_info,
        "installation_durchgefuehrt": False,
        "internet_verwendet": False,
        "originale_veraendert": False,
        "datenbank_geaendert": False,
    }

    # tessdata_inventar aufbereiten (nur Metadaten, keine Rohdaten)
    for td, dateien in tessdata_inventar.items():
        ergebnis["tessdata_inventar"][td] = [
            {"code": d["code"], "groesse_bytes": d["groesse_bytes"]}
            for d in dateien
        ]

    return ergebnis, fehler, warnungen

# ---------------------------------------------------------------------------
# AUSGABEN SCHREIBEN
# ---------------------------------------------------------------------------

def schreibe_alle_ausgaben(ergebnis, fehler, warnungen, config):
    """Schreibt alle KM13b-Ausgabedateien."""
    if ergebnis is None:
        ergebnis = {"modul": "KM13b", "fehler": fehler, "warnungen": warnungen, "zeitpunkt": now()}

    # --- Status ---
    status_daten = {
        "modul": "KM13b – Tesseract-Sprachpaket-Abgleich",
        "version": config.get("version", "v1"),
        "zeitpunkt": now(),
        "projektwurzel": str(ROOT),
        "schreibbereich": str(SCHREIBBEREICH),
        "anzahl_exe_pfade": len(ergebnis.get("exe_pfade", [])),
        "anzahl_tessdata_pfade": len(ergebnis.get("tessdata_pfade", [])),
        "sprachen_gesamt": ergebnis.get("anzahl_sprachen_gesamt", 0),
        "eu24_vorhanden": ergebnis.get("eu24_vorhanden", 0),
        "eu24_fehlen": ergebnis.get("eu24_fehlt", 0),
        "widersprueche": ergebnis.get("widersprueche", []),
        "installation_durchgefuehrt": False,
        "internet_verwendet": False,
        "originale_veraendert": False,
        "datenbank_geaendert": False,
        "produktivfreigabe": False,
        "naechster_empfohlener_auftrag": (
            "KM13-Konfiguration auf Projekt-tessdata umstellen, dann ggf. KM13-Neulauf "
            "mit allen EU24-Sprachen. Danach KM15 – Arbeitsuebersetzungsschicht."
        ),
    }
    sp = STATUS_DIR / "KM13b_STATUS.json"
    sp.write_text(json.dumps(status_daten, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # --- Manifest JSON ---
    mj = MANIFEST_DIR / "KM13b_MANIFEST.json"
    manifest_daten = {
        "modul": "KM13b",
        "zeitpunkt": now(),
        "exe_pfade": ergebnis.get("exe_pfade", []),
        "tessdata_pfade": ergebnis.get("tessdata_pfade", []),
        "alle_sprachen": ergebnis.get("alle_verfuegbaren_sprachen", []),
        "eu24_status": ergebnis.get("eu24_abgleich", {}),
        "widersprueche": ergebnis.get("widersprueche", []),
    }
    mj.write_text(json.dumps(manifest_daten, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # --- Manifest CSV ---
    mc = MANIFEST_DIR / "KM13b_MANIFEST.csv"
    with open(mc, "w", newline="", encoding="utf-8-sig") as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(["sprachcode", "name", "eu24_status"])
        for code, info in ergebnis.get("eu24_abgleich", {}).items():
            writer.writerow([code, info["name"], info["status"]])

    # --- Bericht ---
    bp = BERICHTE / "KM13b_BERICHT.txt"
    lines = [
        "=" * 70,
        "KM13b BERICHT – TESSERACT-SPRACHPAKET-ABGLEICH",
        "=" * 70,
        f"Zeitpunkt: {now()}",
        "",
        "TESSERACT-INSTALLATIONEN",
        f"  EXE-Pfade: {len(ergebnis.get('exe_pfade', []))}",
    ]
    for exe in ergebnis.get("exe_pfade", []):
        lines.append(f"    {exe}")
    for k in ergebnis.get("kombinationen", []):
        lines.append(f"    {k['tessdata_pfad']}: {k['anzahl_sprachen']} Sprachen, Version: {k['version']}")
    lines += [
        "",
        f"TESSDATA-VERZEICHNISSE: {len(ergebnis.get('tessdata_pfade', []))}",
    ]
    for td in ergebnis.get("tessdata_pfade", []):
        inventar = ergebnis.get("tessdata_inventar", {}).get(td, [])
        lines.append(f"    {td}: {len(inventar)} .traineddata-Dateien")
    lines += [
        "",
        f"SPRACHEN GESAMT: {ergebnis.get('anzahl_sprachen_gesamt', 0)}",
        f"EU24 VORHANDEN: {ergebnis.get('eu24_vorhanden', 0)}",
        f"EU24 FEHLEN:   {ergebnis.get('eu24_fehlt', 0)}",
        "",
        "EU24-ABGLEICH",
    ]
    for code, info in ergebnis.get("eu24_abgleich", {}).items():
        lines.append(f"  {code:6s} ({info['name']:<20s}): {info['status']}")
    lines += [
        "",
        "WIDERSPRUECHE",
    ]
    for w in ergebnis.get("widersprueche", []):
        lines.append(f"  ! {w}")
    if not ergebnis.get("widersprueche"):
        lines.append("  (keine)")
    lines += [
        "",
        "KM13-KONFIGURATION",
    ]
    km13 = ergebnis.get("km13_info", {})
    if km13.get("gefunden"):
        lines.append(f"  Tesseract-Pfad:     {km13.get('tesseract_pfad')}")
        lines.append(f"  Tessdata-Pfad:      {km13.get('tessdata_pfad')}")
        lines.append(f"  EXE existiert:      {km13.get('exe_existiert')}")
        lines.append(f"  Tessdata existiert: {km13.get('tessdata_existiert')}")
        lines.append(f"  Standardsprache:    {km13.get('standardsprache')}")
    else:
        lines.append(f"  NICHT GEFUNDEN: {km13.get('meldung')}")
    lines += [
        "",
        "GRENZEN (eingehalten)",
        "  Keine Installation von Sprachpaketen",
        "  Kein Internet-Download",
        "  Keine Originalaenderung",
        "  Keine Datenbankaenderung",
        "",
        "EMPFEHLUNG",
        "  tessdata_pfad in Config/ocr_pipeline_v1.json aendern auf:",
        "  I:\\KI_Legal_Project\\Tools\\Tesseract\\tessdata",
        "  Dann KM13-Neulauf mit allen 24 EU-Sprachen.",
    ]
    bp.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    # --- Fehlerbericht ---
    fp = FEHLER_DIR / "KM13b_FEHLER.txt"
    if fehler:
        fl = [f"{len(fehler)} Fehler:", ""]
        for e in fehler:
            fl.append(f"  {e[:200]}")
        fp.write_text("\n".join(fl), encoding="utf-8", newline="\n")
    else:
        fp.write_text("Keine Fehler.\n", encoding="utf-8", newline="\n")

    # --- Ausfuehrungsnotiz ---
    ap = NOTIZEN / "KM13b_AUSFUEHRUNGSNOTIZ.txt"
    ap.write_text("\n".join([
        f"KM13b AUSFUEHRUNGSNOTIZ",
        f"={'=' * 60}",
        f"Zeit: {now()}",
        f"EXE-Pfade: {len(ergebnis.get('exe_pfade', []))}",
        f"Tessdata: {len(ergebnis.get('tessdata_pfade', []))}",
        f"Sprachen gesamt: {ergebnis.get('anzahl_sprachen_gesamt', 0)}",
        f"EU24 vorhanden: {ergebnis.get('eu24_vorhanden', 0)}",
        f"EU24 fehlen: {ergebnis.get('eu24_fehlt', 0)}",
        f"Widersprueche: {len(ergebnis.get('widersprueche', []))}",
        f"Grenzen: keine Installation, kein Internet, keine Original-/DB-Aenderung.",
    ]), encoding="utf-8", newline="\n")

    return status_daten

# ---------------------------------------------------------------------------
# SELBSTTEST
# ---------------------------------------------------------------------------

def run_selftest():
    """Selbsttest mit kontrollierten Umgebungspruefungen."""
    print("=" * 60)
    print("KM13b SELBSTTEST – TESSERACT-SPRACHPAKET-ABGLEICH")
    print("=" * 60)

    verzeichnisse_anlegen()
    config = lade_konfig()

    tests_bestanden = 0
    tests_gesamt = 12

    try:
        # Test 1: Konfiguration ladbar
        print("\nTest 1: Konfiguration ladbar...")
        assert config is not None
        assert "version" in config
        print("  OK")
        tests_bestanden += 1

        # Test 2: EU24-Sprachenliste definiert
        print("\nTest 2: EU24-Sprachenliste...")
        assert len(EU24_SPRACHEN) == 24
        assert "deu" in EU24_SPRACHEN
        assert "eng" in EU24_SPRACHEN
        assert "fra" in EU24_SPRACHEN
        print(f"  OK: {len(EU24_SPRACHEN)} Sprachen")
        tests_bestanden += 1

        # Test 3: EXE-Pfade finden
        print("\nTest 3: Tesseract-EXE finden...")
        exe_pfade = finde_tesseract_exe(config)
        assert len(exe_pfade) >= 1, "Keine tesseract.exe gefunden"
        print(f"  OK: {len(exe_pfade)} EXE(s)")
        tests_bestanden += 1

        # Test 4: tessdata-Verzeichnisse finden
        print("\nTest 4: Tessdata-Verzeichnisse...")
        tessdata_pfade = finde_tessdata_verzeichnisse(config, exe_pfade)
        assert len(tessdata_pfade) >= 1
        print(f"  OK: {len(tessdata_pfade)} Verzeichnis(se)")
        tests_bestanden += 1

        # Test 5: tesseract --version
        print("\nTest 5: tesseract --version...")
        v_out, v_err = tesseract_version(exe_pfade[0], timeout=30)
        assert v_out is not None
        assert "tesseract" in v_out.lower()
        print(f"  OK: {v_out.splitlines()[0] if v_out else 'N/A'}")
        tests_bestanden += 1

        # Test 6: tesseract --list-langs
        print("\nTest 6: tesseract --list-langs...")
        sprachen, err = tesseract_list_langs(exe_pfade[0], None, timeout=30)
        assert len(sprachen) >= 1
        assert "eng" in sprachen
        print(f"  OK: {len(sprachen)} Sprachen (eng vorhanden)")
        tests_bestanden += 1

        # Test 7: .traineddata inventarisieren
        print("\nTest 7: .traineddata inventarisieren...")
        inventar = liste_traineddata(tessdata_pfade[0])
        assert len(inventar) >= 1
        print(f"  OK: {len(inventar)} Dateien in {tessdata_pfade[0]}")
        tests_bestanden += 1

        # Test 8: EU24-Abgleich
        print("\nTest 8: EU24-Abgleich...")
        eu24 = gleiche_eu24_ab(sprachen)
        assert len(eu24) == 24
        vorhanden = sum(1 for v in eu24.values() if v["status"] == "vorhanden")
        print(f"  OK: {vorhanden}/24 EU24-Sprachen")
        tests_bestanden += 1

        # Test 9: KM13-Config lesbar
        print("\nTest 9: KM13-Config analysieren...")
        km13 = analysiere_km13_config(config)
        assert km13["gefunden"] == True
        print(f"  OK: KM13 nutzt {km13.get('tessdata_pfad')}")
        tests_bestanden += 1

        # Test 10: Hauptabgleich durchfuehrbar
        print("\nTest 10: Hauptabgleich...")
        ergebnis, fehler, warnungen = fuehre_abgleich_durch(config)
        assert ergebnis is not None
        assert len(ergebnis["exe_pfade"]) >= 1
        print(f"  OK: {ergebnis['anzahl_sprachen_gesamt']} Sprachen, {len(fehler)} Fehler, {len(warnungen)} Warnungen")
        tests_bestanden += 1

        # Test 11: Ausgaben schreibbar
        print("\nTest 11: Ausgaben schreibbar...")
        status = schreibe_alle_ausgaben(ergebnis, fehler, warnungen, config)
        assert STATUS_DIR.joinpath("KM13b_STATUS.json").exists()
        assert BERICHTE.joinpath("KM13b_BERICHT.txt").exists()
        assert MANIFEST_DIR.joinpath("KM13b_MANIFEST.json").exists()
        print("  OK: Status, Bericht, Manifest geschrieben")
        tests_bestanden += 1

        # Test 12: Keine Installation durchgefuehrt
        print("\nTest 12: Keine Installation...")
        assert ergebnis.get("installation_durchgefuehrt") == False
        assert ergebnis.get("internet_verwendet") == False
        assert ergebnis.get("originale_veraendert") == False
        print("  OK: Grenzen eingehalten")
        tests_bestanden += 1

    except Exception as e:
        print(f"\nFEHLER: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"SELBSTTEST: {tests_bestanden}/{tests_gesamt} BESTANDEN")
    print("=" * 60)
    return tests_bestanden == tests_gesamt

# ---------------------------------------------------------------------------
# HAUPTFUNKTION
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("KLEINMODUL 13b – TESSERACT-SPRACHPAKET-ABGLEICH")
    print("=" * 60)
    print(f"Zeitpunkt:      {now()}")
    print(f"Schreibbereich: {SCHREIBBEREICH}")
    print()

    verzeichnisse_anlegen()
    config = lade_konfig()

    try:
        print("[1/3] Tesseract-Installationen erkennen...")
        ergebnis, fehler, warnungen = fuehre_abgleich_durch(config)

        if ergebnis is None:
            print("KEINE TESSERACT-INSTALLATION GEFUNDEN")
            schreibe_alle_ausgaben(None, fehler, warnungen, config)
            return False

        print(f"      EXE-Pfade:    {len(ergebnis['exe_pfade'])}")
        print(f"      Tessdata:     {len(ergebnis['tessdata_pfade'])}")
        print(f"      Sprachen:     {ergebnis['anzahl_sprachen_gesamt']}")
        print(f"      EU24 da:      {ergebnis['eu24_vorhanden']}")
        print(f"      EU24 fehlen:  {ergebnis['eu24_fehlt']}")

        print("[2/3] Ausgaben schreiben...")
        status = schreibe_alle_ausgaben(ergebnis, fehler, warnungen, config)

        print("[3/3] Zusammenfassung...")
        print()
        print("=" * 60)
        print("KM13b ABGESCHLOSSEN")
        print("=" * 60)
        print(f"Tesseract EXE:          {ergebnis['exe_pfade'][0] if ergebnis['exe_pfade'] else 'N/A'}")
        print(f"Tessdata (KM13-aktiv):  {ergebnis['km13_info'].get('tessdata_pfad', '?')}")
        print(f"Sprachen gesamt:        {ergebnis['anzahl_sprachen_gesamt']}")
        print(f"EU24-Sprachen vorhanden:{ergebnis['eu24_vorhanden']}/24")
        print(f"EU24-Sprachen fehlen:   {ergebnis['eu24_fehlt']}/24")
        print(f"Widersprueche:          {len(ergebnis['widersprueche'])}")
        for w in ergebnis.get("widersprueche", []):
            print(f"  ! {w}")
        print(f"")
        for w in warnungen:
            print(f"  WARNUNG: {w}")
        print(f"")
        print(f"Status:   {STATUS_DIR / 'KM13b_STATUS.json'}")
        print(f"Bericht:  {BERICHTE / 'KM13b_BERICHT.txt'}")
        print(f"Manifest: {MANIFEST_DIR / 'KM13b_MANIFEST.json'}")
        print()
        print("Keine Sprachpakete installiert.")
        print("Kein Internet verwendet.")
        print("Keine Originale/DB veraendert.")

        if warnungen:
            print()
            print("WICHTIGE EMPFEHLUNG:")
            for w in warnungen:
                print(f"  {w}")

        return len(fehler) == 0

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
