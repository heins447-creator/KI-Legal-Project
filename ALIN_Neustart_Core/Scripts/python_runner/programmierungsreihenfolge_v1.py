#!/usr/bin/env python3
"""PROGRAMMIERUNGSREIHENFOLGE_V1 erzeugen.

Der Laeufer schreibt die verbindliche Arbeitsreihenfolge aus dem
Arbeitsauftrag vom 19.05.2026 in maschinenlesbarer und lesbarer Form.
Es werden keine Internetzugriffe, Installationen oder Datenbankaenderungen
ausgeloest.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "Config"
PLAN_DIR = ROOT / "Projektplanung"
REPORTS_DIR = ROOT / "Reports"
LOG_DIR = ROOT / "Windows_App" / "Logs"

CONFIG_PATH = CONFIG_DIR / "programmierungsreihenfolge_v1.json"
PLAN_PATH = PLAN_DIR / "PROGRAMMIERUNGSREIHENFOLGE_V1.md"
REPORT_PATH = REPORTS_DIR / "PROGRAMMIERUNGSREIHENFOLGE_V1_BERICHT.txt"
LOG_PATH = LOG_DIR / "PROGRAMMIERUNGSREIHENFOLGE_V1_BERICHT.txt"


RED_LINES = [
    "Keine Aenderungen ausserhalb von I:\\KI_Legal_Project\\ALIN_Neustart_Core.",
    "Keine echte Mandantendaten, keine Cloud, keine Fremd-API-Aufrufe.",
    "Keine freie Internetrecherche und keine automatische Internetverbindung.",
    "Keine Datenbankaenderung ohne Migration.",
    "Keine Tuerschwelle, bevor Quellenregister, Fachanwaltsraster, Quellenbetreuer, Adapter, Cache und Offline-Fallback stehen.",
    "Keine Auslieferung ohne Testlauf, Bericht und Git-Status.",
]


ORDER = [
    {
        "rang": 0,
        "id": "PROGRAMMIERUNGSREIHENFOLGE_V1",
        "titel": "Verbindliche Programmierungsreihenfolge festlegen",
        "phase": "Vorbereitung",
        "ziel": "Den neuen Arbeitsauftrag in eine pruefbare Ausfuehrungsreihenfolge ueberfuehren.",
        "liefert": [
            "Config/programmierungsreihenfolge_v1.json",
            "Projektplanung/PROGRAMMIERUNGSREIHENFOLGE_V1.md",
            "Scripts/python_runner/programmierungsreihenfolge_v1.py",
            "Scripts/python_runner/check_programmierungsreihenfolge_v1.py",
            "Scripts/Run_PROGRAMMIERUNGSREIHENFOLGE_V1.ps1",
            "Reports/PROGRAMMIERUNGSREIHENFOLGE_V1_BERICHT.txt",
            "Windows_App/Logs/PROGRAMMIERUNGSREIHENFOLGE_V1_BERICHT.txt",
        ],
        "blockiert": [],
        "naechster_schritt": "Phase 0 starten, beginnend mit AP 0.1.",
    },
    {
        "rang": 1,
        "id": "PHASE_0_FUNDAMENT",
        "titel": "Phase 0: Fundament",
        "phase": "0",
        "ziel": "Reproduzierbare Umgebung, technische Sperren, versionierte Datenbank.",
        "arbeitspakete": [
            "0.1 pyproject.toml mit uv, Lockfile, Offline-Wheelhouse",
            "0.2 DuckDB-Schema mit versionierten Migrationen und Migrations-Runner",
            "0.3 pytest-Aufsetzung und tests/-Struktur",
            "0.4 strukturiertes JSON-Logging",
            "0.5 rote Linien als technische Blocker",
            "0.6 Dispatcher alin.py mit dry-run/execute",
            "0.7 Internet-Sperre mit Update-Ausnahme",
        ],
        "blockiert": [
            "Alle produktiven Pipeline-Bausteine",
            "Jede Tuerschwellen-Funktion",
            "Jede echte Datenbankfunktion ohne Migration",
        ],
        "naechster_schritt": "PHASE_1_WERKZEUGKASTEN_BOOTSTRAPPER",
    },
    {
        "rang": 2,
        "id": "PHASE_1_WERKZEUGKASTEN_BOOTSTRAPPER",
        "titel": "Phase 1: Werkzeugkasten und Bootstrapper",
        "phase": "1",
        "ziel": "Offline-Installationspaket, Lizenzcheck, Healthcheck und MSIX-Skelett.",
        "arbeitspakete": ["1.1", "1.2", "1.3", "1.4", "1.5"],
        "blockiert": ["Phase 2 Eingang und Sicherheit"],
        "naechster_schritt": "PHASE_2_EINGANG_SICHERHEIT",
    },
    {
        "rang": 3,
        "id": "PHASE_2_EINGANG_SICHERHEIT",
        "titel": "Phase 2: Eingang und Sicherheit",
        "phase": "2",
        "ziel": "Posteingang, Schutzsoftware, Dateityp-, PDF-, Office-, Container- und Quarantaenepruefung.",
        "arbeitspakete": ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6"],
        "blockiert": ["Sichtungsschicht mit Triage-Agent"],
        "naechster_schritt": "PHASE_3_SICHTUNG_TRIAGE",
    },
    {
        "rang": 4,
        "id": "PHASE_3_SICHTUNG_TRIAGE",
        "titel": "Phase 3: Sichtungsschicht mit Triage-Agent",
        "phase": "3",
        "ziel": "Sichtung vor der Mandatsannahme mit Schnell-OCR, lokaler KI und anwaltlicher Entscheidung.",
        "arbeitspakete": ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8"],
        "blockiert": ["Aktenbearbeitung nach Annahme"],
        "naechster_schritt": "PHASE_4_AKTENBEARBEITUNG",
    },
    {
        "rang": 5,
        "id": "QUELLENBETREUER_FACHANWALTSRASTER_V1",
        "titel": "Quellenbetreuer und Fachanwaltsraster",
        "phase": "Sperrfolge vor Tuerschwelle",
        "ziel": "Quellenbetreuung und fachliche Rasterung pruefbar machen, bevor die Mandatsannahme produktiv wird.",
        "blockiert": ["MANDATSANNAHME_TUERSCHWELLE_V1"],
        "naechster_schritt": "AGENTEN_KONTEXT_SKILL_REGISTER_V1",
    },
    {
        "rang": 6,
        "id": "AGENTEN_KONTEXT_SKILL_REGISTER_V1",
        "titel": "Agenten-Kontext und Skill-Register",
        "phase": "Sperrfolge vor Tuerschwelle",
        "ziel": "Agenten duerfen nur mit registriertem Kontext, Skill-Grenzen und Pruefpflichten arbeiten.",
        "blockiert": ["MANDATSANNAHME_TUERSCHWELLE_V1"],
        "naechster_schritt": "AGENTEN_KOMMUNIKATION_UND_PRUEFAUFTRAEGE_V1",
    },
    {
        "rang": 7,
        "id": "AGENTEN_KOMMUNIKATION_UND_PRUEFAUFTRAEGE_V1",
        "titel": "Agentenkommunikation und Pruefauftraege",
        "phase": "Sperrfolge vor Tuerschwelle",
        "ziel": "Pruefauftraege zwischen Agenten nachvollziehbar und auditierbar machen.",
        "blockiert": ["MANDATSANNAHME_TUERSCHWELLE_V1"],
        "naechster_schritt": "RECHTSKONTEXT_SPRACHPAKET_CACHE_V1",
    },
    {
        "rang": 8,
        "id": "RECHTSKONTEXT_SPRACHPAKET_CACHE_V1",
        "titel": "Rechtskontext-Sprachpaket-Cache",
        "phase": "Sperrfolge vor Tuerschwelle",
        "ziel": "Relevante Sprach- und Rechtskontextpakete lokal, nachvollziehbar und offline verfuegbar halten.",
        "blockiert": ["MANDATSANNAHME_TUERSCHWELLE_V1"],
        "naechster_schritt": "ANYTHINGLLM_OFFLINE_HANDAKTE_ZENTRALE_V1",
    },
    {
        "rang": 9,
        "id": "ANYTHINGLLM_OFFLINE_HANDAKTE_ZENTRALE_V1",
        "titel": "AnythingLLM Offline-Handakte-Zentrale",
        "phase": "Sperrfolge vor Tuerschwelle",
        "ziel": "Lokale Recherche in der Handakte ohne Cloud, Telemetrie oder Fremd-API absichern.",
        "blockiert": ["MANDATSANNAHME_TUERSCHWELLE_V1"],
        "naechster_schritt": "MANDATSANNAHME_TUERSCHWELLE_V1",
    },
    {
        "rang": 10,
        "id": "MANDATSANNAHME_TUERSCHWELLE_V1",
        "titel": "Mandatsannahme-Tuerschwelle",
        "phase": "Sperrfolge vor Tuerschwelle",
        "ziel": "Harte Grenze zwischen Sichtung und Aktenbearbeitung technisch erzwingen.",
        "blockiert": ["Phase 4 darf keine Triage-Ergebnisse still uebernehmen."],
        "naechster_schritt": "PHASE_4_AKTENBEARBEITUNG",
    },
    {
        "rang": 11,
        "id": "PHASE_4_AKTENBEARBEITUNG",
        "titel": "Phase 4: Aktenbearbeitung",
        "phase": "4",
        "ziel": "Doppel-OCR, CAT-Uebersetzung, Quellen- und Auditnachweise nach Mandatsannahme.",
        "arbeitspakete": ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9"],
        "blockiert": ["EU-Quellen-Adapter und Pflege-Maske"],
        "naechster_schritt": "PHASE_5_EU_QUELLEN_ADAPTER",
    },
    {
        "rang": 12,
        "id": "PHASE_5_EU_QUELLEN_ADAPTER",
        "titel": "Phase 5: EU-Quellen-Adapter und Pflege-Maske",
        "phase": "5",
        "ziel": "Modulare Quellenadapter, Selbsttests, Pflege-Maske und sichere Schluesselablage.",
        "arbeitspakete": ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6"],
        "blockiert": ["Laptop-Anwendung"],
        "naechster_schritt": "PHASE_6_LAPTOP_ANWENDUNG",
    },
    {
        "rang": 13,
        "id": "PHASE_6_LAPTOP_ANWENDUNG",
        "titel": "Phase 6: Laptop-Anwendung",
        "phase": "6",
        "ziel": "Verschluesselte Aktenpakete, Lesegeraet, Notizen, lokales RAG und Rueckspiel.",
        "arbeitspakete": ["6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "6.8"],
        "blockiert": ["Reife Bedienoberflaeche"],
        "naechster_schritt": "PHASE_7_UI_BARRIEREFREIHEIT",
    },
    {
        "rang": 14,
        "id": "PHASE_7_UI_BARRIEREFREIHEIT",
        "titel": "Phase 7: Bedienoberflaeche und Barrierefreiheit",
        "phase": "7",
        "ziel": "Reife Windows-Anwendung mit Tastaturbedienung, Kontrast, Skalierung und Sprachen.",
        "arbeitspakete": ["7.1", "7.2", "7.3", "7.4", "7.5"],
        "blockiert": ["Update, Backup, Lizenz"],
        "naechster_schritt": "PHASE_8_UPDATE_BACKUP_LIZENZ",
    },
    {
        "rang": 15,
        "id": "PHASE_8_UPDATE_BACKUP_LIZENZ",
        "titel": "Phase 8: Update, Backup, Lizenz",
        "phase": "8",
        "ziel": "Rollback-faehige Updates, Backup/Restore, Lizenzschluessel-Architektur und Kundendokumentation.",
        "arbeitspakete": ["8.1", "8.2", "8.3", "8.4", "8.5"],
        "blockiert": [],
        "naechster_schritt": "Abnahme durch Anwalt, keine KI-Selbstfreigabe.",
    },
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def ensure_required_inputs() -> None:
    required = [
        ROOT / "AGENTS.md",
        ROOT / "00_Dokumentation" / "ALIN_ARBEITSAUFTRAG_KI_ENTWICKLUNG.md",
        ROOT / "00_Dokumentation" / "OFFENE_FRAGEN_AN_ANWALT.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Pflichtdateien fehlen: " + ", ".join(missing))


def build_payload(timestamp: str) -> dict:
    return {
        "schema_version": "1.0",
        "created_at": timestamp,
        "source_documents": [
            "AGENTS.md",
            "00_Dokumentation/ALIN_ARBEITSAUFTRAG_KI_ENTWICKLUNG.md",
            "00_Dokumentation/OFFENE_FRAGEN_AN_ANWALT.md",
        ],
        "working_root": str(ROOT),
        "policy": {
            "current_phase": "Vorbereitung / Phase 0",
            "next_programming_step": "Phase 0, AP 0.1: pyproject.toml mit uv, Lockfile und Offline-Wheelhouse-Konzept.",
            "commit_rule": "Commit erst nach erfolgreichem Build und erfolgreicher Pruefung.",
            "no_threshold_before": [
                "Quellenregister",
                "Fachanwaltsraster",
                "Quellenbetreuer",
                "Adapter",
                "Cache",
                "Offline-Fallback",
            ],
            "red_lines": RED_LINES,
        },
        "order": ORDER,
        "open_questions_policy": "Bei Architektur-, Lizenz-, Modell-, Adapter- oder Sicherheitsentscheidungen Frage eintragen statt raten.",
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# PROGRAMMIERUNGSREIHENFOLGE_V1",
        "",
        f"Erstellt: {payload['created_at']}",
        "",
        "## Zweck",
        "",
        "Dieses Dokument legt die verbindliche Reihenfolge fuer die weitere Programmierung fest. Es uebersetzt den Arbeitsauftrag vom 19.05.2026 in eine pruefbare Reihenfolge, ohne selbst eine fachliche oder sicherheitsrelevante Entscheidung zu ersetzen.",
        "",
        "## Grundsatz",
        "",
        "Die Phasen aus dem Arbeitsauftrag bleiben fuehrend. Die im Projekt zusaetzlich genannte Sperrfolge vor der Mandatsannahme wird als harte Zwischenreihenfolge vor der Tuerschwelle gefuehrt.",
        "",
        "## Naechster umzusetzender Programmierbaustein",
        "",
        payload["policy"]["next_programming_step"],
        "",
        "## Harte Sperren",
        "",
    ]
    for item in payload["policy"]["red_lines"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Reihenfolge", ""])
    for item in payload["order"]:
        lines.append(f"### {item['rang']}. {item['id']}")
        lines.append("")
        lines.append(f"- Titel: {item['titel']}")
        lines.append(f"- Phase: {item['phase']}")
        lines.append(f"- Ziel: {item['ziel']}")
        if item.get("arbeitspakete"):
            lines.append("- Arbeitspakete: " + ", ".join(item["arbeitspakete"]))
        if item.get("blockiert"):
            lines.append("- Blockiert: " + "; ".join(item["blockiert"]))
        lines.append(f"- Danach: {item['naechster_schritt']}")
        lines.append("")

    lines.extend(
        [
            "## Umgang mit offenen Punkten",
            "",
            "Nicht von der KI entschieden werden: LLM-Standardmodell, Adapter-Reihenfolge jenseits der bereits freigegebenen Sperrfolge, Software-Lizenz, beA-Aufnahme in Version 1, PyMuPDF-Lizenzvariante und Abschluss einer Phase. Bei Beruehrung wird eine Frage in `00_Dokumentation/OFFENE_FRAGEN_AN_ANWALT.md` eingetragen.",
            "",
        ]
    )
    return "\n".join(lines)


def render_report(payload: dict) -> str:
    lines = [
        "PROGRAMMIERUNGSREIHENFOLGE_V1 BERICHT",
        "=" * 70,
        f"Erstellt: {payload['created_at']}",
        f"Arbeitswurzel: {payload['working_root']}",
        "",
        "ERGEBNIS",
        "-" * 70,
        "Die verbindliche Reihenfolge wurde erzeugt und als JSON-Konfiguration sowie als Projektdokument abgelegt.",
        "",
        "NAECHSTER SCHRITT",
        "-" * 70,
        payload["policy"]["next_programming_step"],
        "",
        "ERZEUGTE DATEIEN",
        "-" * 70,
        str(CONFIG_PATH.relative_to(ROOT)),
        str(PLAN_PATH.relative_to(ROOT)),
        str(REPORT_PATH.relative_to(ROOT)),
        str(LOG_PATH.relative_to(ROOT)),
        "",
        "SPERRFOLGE VOR TUERSCHWELLE",
        "-" * 70,
    ]
    for item in payload["order"]:
        if item["phase"] == "Sperrfolge vor Tuerschwelle":
            lines.append(f"{item['rang']}. {item['id']}")
    lines.extend(["", "ENDE BERICHT", "=" * 70, ""])
    return "\n".join(lines)


def main() -> int:
    ensure_required_inputs()

    # Pflichtdateien bewusst lesen, damit fehlende oder unlesbare Dateien
    # den Lauf abbrechen.
    read_text(ROOT / "AGENTS.md")
    read_text(ROOT / "00_Dokumentation" / "ALIN_ARBEITSAUFTRAG_KI_ENTWICKLUNG.md")
    read_text(ROOT / "00_Dokumentation" / "OFFENE_FRAGEN_AN_ANWALT.md")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = build_payload(timestamp)

    for directory in [CONFIG_DIR, PLAN_DIR, REPORTS_DIR, LOG_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    CONFIG_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PLAN_PATH.write_text(render_markdown(payload), encoding="utf-8")
    report = render_report(payload)
    REPORT_PATH.write_text(report, encoding="utf-8")
    LOG_PATH.write_text(report, encoding="utf-8")

    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
