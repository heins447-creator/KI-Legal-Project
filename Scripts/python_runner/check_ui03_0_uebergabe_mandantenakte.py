#!/usr/bin/env python3
"""UI03-0 – PRUEFDATEI – Prueft alle erzeugten Dateien auf Konsistenz"""
import sys, json
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte"

FEHLER = 0
def check(bez, bed):
    global FEHLER
    v = bool(bed)
    print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
    if not v: FEHLER += 1
    return v

print("UI03-0 PRUEFDATEI =====================================")

paths = {
    "Status": SB / "02_Status" / "UI03_0_STATUS.json",
    "Bericht": SB / "03_Berichte" / "UI03_0_BERICHT.txt",
    "Fehlerbericht": SB / "05_Fehler" / "UI03_0_FEHLER.txt",
    "Manifest": SB / "07_Manifest" / "UI03_0_MANIFEST.json",
    "Rueckgabe": SB / "08_Rueckgabe_aus_UI02c" / "Rueckgabe_an_regulaeren_Prozess.json",
    "Mandantenakte": SB / "10_Mandantenakte" / "Mandantenakte.json",
    "ProzessStart": SB / "15_Regulaerer_Prozess" / "Prozess_Start.json",
    "DokumentIDs": SB / "15_Regulaerer_Prozess" / "Dokument_IDs.txt",
}

for name, p in paths.items():
    check(f"Datei vorhanden: {name}", p.exists())

# JSON validieren
for name, p in paths.items():
    if p.suffix == ".json" and p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
            check(f"JSON gueltig: {p.name}", True)
        except Exception as e:
            check(f"JSON gueltig: {p.name}", False)

# Mandantenakte pruefen
akte_path = paths["Mandantenakte"]
if akte_path.exists():
    akte = json.loads(akte_path.read_text(encoding="utf-8-sig"))
    check("Akten-ID vorhanden", bool(akte.get("akten_id")))
    check("Dokumente > 0", len(akte.get("dokumente", [])) >= 1)
    check("Globale Merkmale gesetzt", bool(akte.get("globale_merkmale", {}).get("sprache")))
    check("Türschwelle-Hinweis in Akte", any("Türschwelle" in json.dumps(d, ensure_ascii=False) for d in akte.get("dokumente", [])))
    check("Dokument-IDs aus UI02c", len(akte.get("dokument_ids_aus_tuerschwelle", [])) >= 1)
    for dok in akte.get("dokumente", []):
        check(f"  OCR-Text vorhanden ({dok['original_id'][:12]}...)", any(s.get("ocr_text") for s in dok.get("seiten", [])))
        check(f"  Orientierung DE ({dok['original_id'][:12]}...)", any(s.get("orientierung_de") for s in dok.get("seiten", [])))

# Rueckgabe-JSON pruefen
rg_path = paths["Rueckgabe"]
if rg_path.exists():
    rg = json.loads(rg_path.read_text(encoding="utf-8-sig"))
    check("Rueckgabe hat dokument_ids", "dokument_ids" in rg)
    check("Rueckgabe hat Akten-ID", bool(rg.get("akten_id")))
    check("Rueckgabe hat naechster_schritt", "naechster_schritt" in rg)

# Prozess_Start pruefen
ps_path = paths["ProzessStart"]
if ps_path.exists():
    ps = json.loads(ps_path.read_text(encoding="utf-8-sig"))
    check("ProzessStart hat Dokument-IDs", len(ps.get("dokument_ids", [])) >= 1)
    check("ProzessStart hat Akten-ID", bool(ps.get("akten_id")))

# Dokument_IDs.txt pruefen
did_path = paths["DokumentIDs"]
if did_path.exists():
    ids = did_path.read_text().strip().split("\n")
    check("Dokument_IDs.txt nicht leer", len(ids) >= 1 and ids[0].startswith("ORG-"))

# PNG-Assets pruefen
asset_dir = SB / "10_Mandantenakte" / "Originale"
if asset_dir.exists():
    pngs = list(asset_dir.glob("*.png"))
    check(f"PNG-Assets kopiert ({len(pngs)})", len(pngs) >= 1)

# Grenzen
check("Keine DB-Datei", not any(SB.rglob("*.db")) and not any(SB.rglob("*.duckdb")))
check("Keine API-Key-Datei", not any(SB.rglob("*.env")) and not any(SB.rglob("*secret*")))

# Keine Cloud
for p in paths.values():
    if p.suffix == ".json" and p.exists():
        txt = p.read_text(encoding="utf-8-sig")
        check(f"  Kein Cloud im {p.name}", "Cloud" not in txt.lower())

print(f"\nPRUEFERGEBNIS: {FEHLER} Fehler")
sys.exit(0 if FEHLER == 0 else 1)
