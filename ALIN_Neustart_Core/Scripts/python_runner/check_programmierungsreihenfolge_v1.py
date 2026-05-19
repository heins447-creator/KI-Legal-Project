#!/usr/bin/env python3
"""Pruefung fuer PROGRAMMIERUNGSREIHENFOLGE_V1."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "Config" / "programmierungsreihenfolge_v1.json"
PLAN_PATH = ROOT / "Projektplanung" / "PROGRAMMIERUNGSREIHENFOLGE_V1.md"
REPORT_PATH = ROOT / "Reports" / "PROGRAMMIERUNGSREIHENFOLGE_V1_BERICHT.txt"
LOG_PATH = ROOT / "Windows_App" / "Logs" / "PROGRAMMIERUNGSREIHENFOLGE_V1_BERICHT.txt"


REQUIRED_IDS = [
    "PROGRAMMIERUNGSREIHENFOLGE_V1",
    "PHASE_0_FUNDAMENT",
    "PHASE_1_WERKZEUGKASTEN_BOOTSTRAPPER",
    "PHASE_2_EINGANG_SICHERHEIT",
    "PHASE_3_SICHTUNG_TRIAGE",
    "QUELLENBETREUER_FACHANWALTSRASTER_V1",
    "AGENTEN_KONTEXT_SKILL_REGISTER_V1",
    "AGENTEN_KOMMUNIKATION_UND_PRUEFAUFTRAEGE_V1",
    "RECHTSKONTEXT_SPRACHPAKET_CACHE_V1",
    "ANYTHINGLLM_OFFLINE_HANDAKTE_ZENTRALE_V1",
    "MANDATSANNAHME_TUERSCHWELLE_V1",
    "PHASE_4_AKTENBEARBEITUNG",
    "PHASE_5_EU_QUELLEN_ADAPTER",
    "PHASE_6_LAPTOP_ANWENDUNG",
    "PHASE_7_UI_BARRIEREFREIHEIT",
    "PHASE_8_UPDATE_BACKUP_LIZENZ",
]


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    for path in [CONFIG_PATH, PLAN_PATH, REPORT_PATH, LOG_PATH]:
        if not path.exists():
            fail(f"Datei fehlt: {path.relative_to(ROOT)}")
        if path.stat().st_size == 0:
            fail(f"Datei ist leer: {path.relative_to(ROOT)}")

    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    order = payload.get("order", [])
    ids = [item.get("id") for item in order]
    ranks = [item.get("rang") for item in order]

    if ids != REQUIRED_IDS:
        fail("Reihenfolge der IDs entspricht nicht der Pflichtreihenfolge.")

    if ranks != list(range(len(REQUIRED_IDS))):
        fail("Raenge sind nicht lueckenlos aufsteigend.")

    if payload["policy"]["next_programming_step"].startswith("Phase 0, AP 0.1") is False:
        fail("Naechster Programmierbaustein muss Phase 0, AP 0.1 sein.")

    threshold_index = ids.index("MANDATSANNAHME_TUERSCHWELLE_V1")
    for required_before_threshold in [
        "QUELLENBETREUER_FACHANWALTSRASTER_V1",
        "RECHTSKONTEXT_SPRACHPAKET_CACHE_V1",
        "ANYTHINGLLM_OFFLINE_HANDAKTE_ZENTRALE_V1",
    ]:
        if ids.index(required_before_threshold) > threshold_index:
            fail(f"{required_before_threshold} liegt faelschlich hinter der Tuerschwelle.")

    plan_text = PLAN_PATH.read_text(encoding="utf-8")
    for marker in ["Harte Sperren", "Sperrfolge vor der Mandatsannahme", "Phase 0"]:
        if marker not in plan_text:
            fail(f"Planungsdokument enthaelt Marker nicht: {marker}")

    print("PROGRAMMIERUNGSREIHENFOLGE_V1: Pruefung erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
