import json
import sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core"
MIGRATION = CORE / "08_Migration" / "02_Kopierte_Dateien"
REPORTS = CORE / "Reports"

checks = []
errors = []

def require(path, label):
    if not path.exists():
        errors.append(f"FEHLT: {label}: {path}")
    else:
        checks.append(f"OK: {label}")

active_json = CORE / ".alin_active_root.json"
status_json = REPORTS / "S0_02_ARBEITSKERN_BEREINIGUNG_STATUS.json"

require(CORE / "AKTIVER_PROGRAMMIERORDNER.md", "AKTIVER_PROGRAMMIERORDNER.md")
require(CORE / "AGENTS.md", "AGENTS.md")
require(active_json, ".alin_active_root.json")
require(ROOT / "ALIN_PROGRAMMIERUNG.code-workspace", "ALIN_PROGRAMMIERUNG.code-workspace")
require(ROOT / "ALTBEstand_NUR_SICHERUNG_NICHT_AKTIV_BEARBEITEN.md", "Altbestand-Sperrdatei")
require(MIGRATION / "NUR_MIGRATION_NICHT_AKTIV_BEARBEITEN.md", "Migrations-Sperrdatei")
require(REPORTS / "S0_02_ARBEITSKERN_BEREINIGUNG_BERICHT.txt", "Bericht")
require(status_json, "Status-JSON")

try:
    data = json.loads(active_json.read_text(encoding="utf-8"))
    if data.get("aktiver_programmierordner") != r"I:\KI_Legal_Project\ALIN_Neustart_Core":
        errors.append("aktiver_programmierordner zeigt nicht auf ALIN_Neustart_Core")
    for key in ("loeschen_erlaubt", "internet_erlaubt", "cloud_erlaubt"):
        if data.get(key) is not False:
            errors.append(f"{key} ist nicht false")
except Exception as exc:
    errors.append(f".alin_active_root.json ungueltig: {exc}")

try:
    status = json.loads(status_json.read_text(encoding="utf-8"))
    if status.get("aktive_wurzel") != r"I:\KI_Legal_Project\ALIN_Neustart_Core":
        errors.append("Status aktive_wurzel zeigt nicht auf ALIN_Neustart_Core")
    if status.get("produktiv_freigegeben") is not False:
        errors.append("produktiv_freigegeben ist nicht false")
except Exception as exc:
    errors.append(f"Status-JSON ungueltig: {exc}")

if errors:
    print("S0-02 PRUEFUNG FEHLGESCHLAGEN")
    for error in errors:
        print(error)
    sys.exit(1)

print("S0-02 PRUEFUNG OK")
for item in checks:
    print(item)
sys.exit(0)