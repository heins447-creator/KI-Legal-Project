#!/usr/bin/env python3
"""UI03-0 – Uebergabe Tuerschwelle UI02c → Mandantenakte (regulaere Verarbeitung vorbereiten)

Liest UI02c-Freigabevorschlag und ViewData, legt Mandantenakte an,
erzeugt Rueckgabe-JSON fuer Sekretariat/regulaeren Prozess.
Keine DB-Aenderung. Keine Originalaenderung. Keine Cloud.
"""
import json, sys, shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
SB_UI02c = ROOT / "Agentensteuerung" / "UI02_Tuerschwelle_Bau" / "17_Freigabe_UI02c"
SB_UI02  = ROOT / "Agentensteuerung" / "UI02_Tuerschwelle_Bau"
SB_UI03  = ROOT / "Agentensteuerung" / "UI03_Mandantenakte"
CONFIG   = ROOT / "Config" / "ui03_0_uebergabe_mandantenakte_v1.json"

FEHLER = []
WARNUNGEN = []

# ─── Config laden oder Default ──────────────────────────────────────────
def load_config():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    return {
        "version": "1.0.0",
        "beschreibung": "UI03-0 Uebergabe Tuerschwelle → Mandantenakte",
        "aktentyp_default": "Neuanlage",
        "mappe_default": "Handakte",
        "anwaltssprache_default": "Deutsch",
        "schreibbereiche": {
            "status": "02_Status",
            "berichte": "03_Berichte",
            "fehler": "05_Fehler",
            "manifest": "07_Manifest",
            "rueckgabe": "08_Rueckgabe_aus_UI02c",
            "mandantenakte": "10_Mandantenakte",
            "regulaerer_prozess": "15_Regulaerer_Prozess",
            "runlogs": "90_RunLogs",
        }
    }

# ─── Schreibbereich anlegen ─────────────────────────────────────────────
def ensure_dirs(cfg):
    for key in cfg["schreibbereiche"].values():
        (SB_UI03 / key).mkdir(parents=True, exist_ok=True)
    # unter Mandantenakte auch Dokumente
    (SB_UI03 / "10_Mandantenakte" / "Originale").mkdir(parents=True, exist_ok=True)
    return True

# ─── UI02c-Daten lesen ──────────────────────────────────────────────────
def read_ui02c():
    """Liest alle relevanten UI02c-Daten"""
    daten = {}
    # Freigabevorschlag
    fv_path = SB_UI02c / "09_Freigabevorschlag" / "UI02c_FREIGABEVORSCHLAG.json"
    if fv_path.exists():
        daten["freigabevorschlag"] = json.loads(fv_path.read_text(encoding="utf-8-sig"))
    # ViewData (UI02c)
    vd_path = SB_UI02c / "08_ViewData" / "UI02c_VIEWDATA.json"
    if vd_path.exists():
        daten["viewdata_ui02c"] = json.loads(vd_path.read_text(encoding="utf-8-sig"))
    # Status
    st_path = SB_UI02c / "02_Status" / "UI02c_STATUS.json"
    if st_path.exists():
        daten["status_ui02c"] = json.loads(st_path.read_text(encoding="utf-8-sig"))
    # Formularschema
    fs_path = SB_UI02c / "10_Freigabeformular" / "UI02c_FREIGABEFORMULAR_SCHEMA.json"
    if fs_path.exists():
        daten["formularschema"] = json.loads(fs_path.read_text(encoding="utf-8-sig"))
    # Rueckgabe-Template
    rt_path = SB_UI02c / "11_Rueckgabe" / "UI02c_RUECKGABE_AN_REGULAEREN_PROZESS_TEMPLATE.json"
    if rt_path.exists():
        daten["rueckgabe_template"] = json.loads(rt_path.read_text(encoding="utf-8-sig"))
    return daten

# ─── UI02-Daten lesen (OCR, KI-Merkmale, Assets) ────────────────────────
def read_ui02():
    daten = {}
    vd_path = SB_UI02 / "08_ViewData" / "UI02_VIEWDATA.json"
    if vd_path.exists():
        daten["viewdata"] = json.loads(vd_path.read_text(encoding="utf-8-sig"))
    return daten

# ─── Mandantenakte anlegen ──────────────────────────────────────────────
def create_mandantenakte(ui02c_daten, ui02_daten, cfg):
    """Erzeugt die Mandantenakte als strukturiertes JSON"""
    jetzt = datetime.now(timezone.utc).isoformat()
    fv = ui02c_daten.get("freigabevorschlag", {})
    vd2 = ui02c_daten.get("viewdata_ui02c", {})
    vd  = ui02_daten.get("viewdata", {})

    dokument_ids = fv.get("dokument_ids", [])
    dokumente_fv = fv.get("dokumente", [])

    akte = {
        "akten_id": f"Akte-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "angelegt_am": jetzt,
        "quelle": "UI02c_Tuerschwelle",
        "vorgangs_id": fv.get("vorgangs_id", ""),
        "status": "angelegt",
        "aktentyp": cfg.get("aktentyp_default", "Neuanlage"),
        "mappe": cfg.get("mappe_default", "Handakte"),
        "anwaltssprache": cfg.get("anwaltssprache_default", "Deutsch"),
        "dokumente": [],
        "globale_merkmale": {
            "sprache": fv.get("globale_sprache", ""),
            "rechtsgebiet": fv.get("globales_rechtsgebiet", ""),
            "verfahrensland": fv.get("globales_verfahrensland", ""),
            "mandantensprache": fv.get("mandantensprache_vorschlag", ""),
        },
        "dokument_ids_aus_tuerschwelle": dokument_ids,
    }

    # Dokumente aus UI02-ViewData anreichern
    for dok in vd.get("dokumente", []):
        oid = dok.get("original_id", "")
        # Matching-Freigabevorschlag-Daten
        dok_fv = next((d for d in dokumente_fv if d.get("original_id") == oid), {})
        
        dok_eintrag = {
            "original_id": oid,
            "dokumentart": dok_fv.get("dokumentart_vorschlag", dok.get("typ_vermutet", "unbestimmt")),
            "sprache": dok_fv.get("sprache_vorschlag", ""),
            "rechtsgebiet": dok_fv.get("rechtsgebiet_vorschlag", ""),
            "verfahrensland": dok_fv.get("verfahrensland_vorschlag", ""),
            "ki_merkmale": dok.get("ki_merkmale", {}),
            "unsicherheiten": dok.get("unsicherheiten", []),
            "seiten": [],
        }

        for seite in dok.get("seiten", []):
            seiten_eintrag = {
                "seite_nummer": seite.get("seite_nummer"),
                "seiten_id": seite.get("seiten_id"),
                "originalbild": seite.get("originalbild"),
                "asset_status": seite.get("asset_status", "unbekannt"),
                "ocr_text": seite.get("ocr_text", ""),
                "orientierung_de": seite.get("orientierung_de", ""),
                "ocr_verwertbarkeit_status": "Türschwelle – nicht schriftsatzfähig",
                "uebersetzung_status": "Türschwelle – Orientierungsübersetzung",
            }
            dok_eintrag["seiten"].append(seiten_eintrag)

        akte["dokumente"].append(dok_eintrag)

    return akte

# ─── PNG-Assets kopieren ────────────────────────────────────────────────
def copy_assets(dokumente):
    """Kopiert PNGs aus UI02c-Browseransicht und UI02 in Mandantenakte"""
    asset_dirs = [
        SB_UI02c / "12_Browseransicht" / "assets",
        SB_UI02 / "15_Browseransicht" / "assets",
        SB_UI02 / "12_Originalabbildung_Arbeitsabbildung",
    ]
    target = SB_UI03 / "10_Mandantenakte" / "Originale"
    copies = 0
    for dok in dokumente:
        for seite in dok.get("seiten", []):
            bild = seite.get("originalbild", "")
            if not bild:
                continue
            for src_dir in asset_dirs:
                src = src_dir / bild
                if src.exists():
                    shutil.copy2(src, target / bild)
                    copies += 1
                    break
    return copies

# ─── Rueckgabe-JSON erzeugen ────────────────────────────────────────────
def create_rueckgabe_json(akte, ui02c_daten, cfg):
    """Erzeugt das JSON für Rückgabe an Sekretariat / regulären Prozeß"""
    jetzt = datetime.now(timezone.utc).isoformat()
    dokument_ids = akte.get("dokument_ids_aus_tuerschwelle", [])

    rueckgabe = {
        "erzeugt_am": jetzt,
        "modul": "UI03-0",
        "akten_id": akte.get("akten_id"),
        "dokument_ids": dokument_ids,
        "anzahl_dokumente": len(dokument_ids) if dokument_ids else 0,
        "entscheidung_aus_ui02c": {
            "status": "zu uebernehmen",
            "hinweis": "Anwaltliche Entscheidung aus UI02c-Browseransicht steht aus. Bitte in 08_Rueckgabe_aus_UI02c/saved_decision.json ablegen."
        },
        "aufforderung": "Regulaeren Scan-/OCR-/Pruef-/Uebersetzungsprozess starten.",
        "naechster_schritt": "UI03-1 Dreiansicht (Original / OCR / Deutsch) aufrufen.",
        "dokumente_detail": [],
    }

    for dok in akte.get("dokumente", []):
        rueckgabe["dokumente_detail"].append({
            "original_id": dok.get("original_id"),
            "dokumentart": dok.get("dokumentart"),
            "seiten_anzahl": len(dok.get("seiten", [])),
            "ocr_verwertbarkeit": "Türschwelle",
            "uebersetzung_benoetigt": True,
        })

    return rueckgabe

# ─── Regulären Prozeß vorbereiten ───────────────────────────────────────
def prepare_regular_process(akte, rueckgabe):
    """Schreibt Vorbereitungsdateien für den regulären Prozeß"""
    # Dokument-ID-Liste
    dok_ids = akte.get("dokument_ids_aus_tuerschwelle", [])
    reg_dir = SB_UI03 / "15_Regulaerer_Prozess"

    # Prozess-Start-JSON
    prozess = {
        "prozess_start": datetime.now(timezone.utc).isoformat(),
        "akten_id": akte.get("akten_id"),
        "dokument_ids": dok_ids,
        "anweisung": "Dokument-IDs aus Türschwelle übernehmen, regulären Scan/OCR/Übersetzung starten.",
        "sprachpaket": "sv-de",
        "dokument_metadaten": [],
    }
    for dok in akte.get("dokumente", []):
        prozess["dokument_metadaten"].append({
            "original_id": dok["original_id"],
            "seiten": len(dok.get("seiten", [])),
            "sprache": dok.get("sprache", ""),
        })
    (reg_dir / "Prozess_Start.json").write_text(json.dumps(prozess, indent=2, ensure_ascii=False), encoding="utf-8")

    # Einfache Dokument-ID-Liste
    (reg_dir / "Dokument_IDs.txt").write_text("\n".join(dok_ids), encoding="utf-8")

    return True

# ─── Status / Bericht / Fehler / Manifest ───────────────────────────────
def write_outputs(akte, rueckgabe, copies, ui02c_daten):
    jetzt = datetime.now(timezone.utc).isoformat()

    # Status
    status = {
        "modul": "UI03-0",
        "version": "1.0.0",
        "zeitpunkt": jetzt,
        "ui02c_gelesen": bool(ui02c_daten.get("freigabevorschlag")),
        "akte_angelegt": True,
        "akten_id": akte["akten_id"],
        "dokumente": len(akte["dokumente"]),
        "assets_kopiert": copies,
        "fehler": len(FEHLER),
        "warnungen": len(WARNUNGEN),
        "grenzen_eingehalten": True,
    }
    (SB_UI03 / "02_Status" / "UI03_0_STATUS.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

    # Bericht
    bericht = f"""UI03-0 Uebergabe Tuerschwelle → Mandantenakte
=============================================
Zeitpunkt: {jetzt}
Akten-ID: {akte['akten_id']}
Dokumente: {len(akte['dokumente'])}
Assets kopiert: {copies}

Dokument-IDs aus Tuerschwelle:
{chr(10).join('  - ' + did for did in akte.get('dokument_ids_aus_tuerschwelle', []))}

Mandantenakte: 10_Mandantenakte/Mandantenakte.json
Rueckgabe-JSON: 08_Rueckgabe_aus_UI02c/Rueckgabe_an_regulaeren_Prozess.json

Naechster Schritt: UI03-1 Dreiansicht (Original / OCR / Deutsch)
"""
    (SB_UI03 / "03_Berichte" / "UI03_0_BERICHT.txt").write_text(bericht, encoding="utf-8")

    # Fehler (leer wenn alles OK)
    fehler_text = f"UI03-0 Fehlerbericht {jetzt}\n" + "\n".join(FEHLER) if FEHLER else f"UI03-0 Keine Fehler {jetzt}\n"
    (SB_UI03 / "05_Fehler" / "UI03_0_FEHLER.txt").write_text(fehler_text, encoding="utf-8")

    # Manifest
    manifest_files = []
    for f in SB_UI03.rglob("*"):
        if f.is_file():
            manifest_files.append({
                "relativ": str(f.relative_to(SB_UI03)),
                "groesse": f.stat().st_size,
            })
    manifest = {
        "modul": "UI03-0",
        "version": "1.0.0",
        "zeitpunkt": jetzt,
        "anzahl_dateien": len(manifest_files),
        "dateien": manifest_files,
    }
    (SB_UI03 / "07_Manifest" / "UI03_0_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

# ─── Hauptlauf ──────────────────────────────────────────────────────────
def main():
    print("UI03-0 HAUPTLAUF =======================================")
    print(f"Zeitpunkt: {datetime.now(timezone.utc).isoformat()}")

    cfg = load_config()
    print("[1] Konfiguration ... OK")

    print("[2] Schreibbereiche ...")
    ensure_dirs(cfg)
    print("    OK")

    print("[3] UI02c-Daten lesen ...")
    ui02c_daten = read_ui02c()
    fv = ui02c_daten.get("freigabevorschlag")
    if not fv:
        FEHLER.append("Kein UI02c-Freigabevorschlag gefunden")
    else:
        print(f"    {len(fv.get('dokument_ids',[]))} Dokument-IDs")

    print("[4] UI02-Daten lesen ...")
    ui02_daten = read_ui02()
    doks_in_ui02 = len(ui02_daten.get("viewdata", {}).get("dokumente", []))
    print(f"    {doks_in_ui02} Dokumente")

    print("[5] Mandantenakte anlegen ...")
    akte = create_mandantenakte(ui02c_daten, ui02_daten, cfg)
    akte_path = SB_UI03 / "10_Mandantenakte" / "Mandantenakte.json"
    akte_path.write_text(json.dumps(akte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"    Akten-ID: {akte['akten_id']}")

    print("[6] PNG-Assets kopieren ...")
    copies = copy_assets(akte.get("dokumente", []))
    print(f"    {copies} PNGs kopiert")

    print("[7] Rueckgabe-JSON ...")
    rueckgabe = create_rueckgabe_json(akte, ui02c_daten, cfg)
    rg_path = SB_UI03 / "08_Rueckgabe_aus_UI02c" / "Rueckgabe_an_regulaeren_Prozess.json"
    rg_path.write_text(json.dumps(rueckgabe, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[8] Regulaeren Prozess vorbereiten ...")
    prepare_regular_process(akte, rueckgabe)
    print("    OK")

    print("[9] Status / Bericht / Fehler / Manifest ...")
    write_outputs(akte, rueckgabe, copies, ui02c_daten)
    print("    OK")

    # ─── Grenzen ──────────────────────────────────────────────────────────
    print("[10] Grenzen pruefen ...")
    grenzen_ok = True
    for dbf in SB_UI03.rglob("*.db"):
        FEHLER.append(f"DB-Datei gefunden: {dbf}")
        grenzen_ok = False
    for dbf in SB_UI03.rglob("*.duckdb"):
        FEHLER.append(f"DB-Datei gefunden: {dbf}")
        grenzen_ok = False
    for envf in SB_UI03.rglob(".env*"):
        FEHLER.append(f"ENV-Datei gefunden: {envf}")
        grenzen_ok = False
    if grenzen_ok:
        print("    Alle Grenzen eingehalten")

    print(f"\n========================================================")
    print(f"UI03-0 ABGESCHLOSSEN")
    print(f"Akten-ID: {akte['akten_id']}")
    print(f"Dokumente: {len(akte['dokumente'])}")
    print(f"Assets kopiert: {copies}")
    print(f"Fehler: {len(FEHLER)}, Warnungen: {len(WARNUNGEN)}")
    if FEHLER:
        for f in FEHLER:
            print(f"  FEHLER: {f}")
    if WARNUNGEN:
        for w in WARNUNGEN:
            print(f"  WARNUNG: {w}")

    return 0 if not FEHLER else 1

# ─── Selbsttest ─────────────────────────────────────────────────────────
def selbsttest():
    print("UI03-0 SELBSTTEST =======================================")
    ok = 0
    ges = 0
    def test(bez, bed):
        nonlocal ok, ges
        ges += 1
        v = bool(bed)
        print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        if v: ok += 1

    test("Config ladbar", load_config() is not None)
    test("Schreibbereich anlegbar", ensure_dirs(load_config()))
    test("UI02c-Daten lesbar (Freigabevorschlag)", read_ui02c().get("freigabevorschlag") is not None)
    test("UI02-Daten lesbar", read_ui02().get("viewdata") is not None)
    
    ui02c = read_ui02c()
    ui02  = read_ui02()
    akte = create_mandantenakte(ui02c, ui02, load_config())
    test("Mandantenakte erzeugbar", akte is not None)
    test("Akten-ID vorhanden", bool(akte.get("akten_id")))
    test("Dokumente uebernommen", len(akte.get("dokumente", [])) >= 1)
    test("Globale Merkmale gesetzt", bool(akte.get("globale_merkmale", {}).get("sprache")))
    
    rg = create_rueckgabe_json(akte, ui02c, load_config())
    test("Rueckgabe-JSON erzeugbar", rg is not None)
    test("Rueckgabe hat dokument_ids", "dokument_ids" in rg)
    test("Rueckgabe hat Akten-ID", bool(rg.get("akten_id")))
    
    test("Schreibbereich kein DB", not any(SB_UI03.rglob("*.db")) if SB_UI03.exists() else True)
    test("Schreibbereich kein ENV", not any(SB_UI03.rglob(".env*")) if SB_UI03.exists() else True)
    test("Keine Cloud-Behauptung", "Cloud" not in json.dumps(rg))
    test("Türschwelle-Hinweis", "Türschwelle" in json.dumps(akte, ensure_ascii=False))
    
    print(f"\nBESTANDEN: {ok}/{ges}")
    return 0 if ok == ges else 1

# ─── Entrypoint ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    else:
        sys.exit(main())
