# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
DB_PATH = ROOT / "Database" / "Legal_Brain.duckdb"
LOG_DIR = ROOT / "Windows_App" / "Logs"
REPORT = LOG_DIR / f"RUN_049_check_agenten_kontext_skill_register_v1_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

TABLES = [
    "agent_role_registry",
    "agent_skill_registry",
    "agent_scope_rule",
    "agent_handoff_protocol",
    "agent_handoff_route",
    "agent_uncertainty_rule",
    "agent_source_binding",
    "agent_language_package_binding",
]

REQUIRED_ROLES = [
    "se_arbeitsrecht_federfuehrend",
    "quellenbetreuer",
    "sprachpaket_sv_de_arbeitsrecht_se",
    "medizinrecht_pruefagent",
    "sozialrecht_pruefagent",
    "zivilrecht_pruefagent",
]

MIN_COUNTS = {
    "agent_role_registry": 6,
    "agent_skill_registry": 6,
    "agent_scope_rule": 1,
    "agent_handoff_protocol": 1,
    "agent_handoff_route": 1,
    "agent_uncertainty_rule": 1,
    "agent_source_binding": 1,
    "agent_language_package_binding": 1,
}

def log(text: str = "") -> None:
    line = f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {text}"
    print(line)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.open("a", encoding="utf-8").write(line + "\n")

try:
    import duckdb  # type: ignore
except Exception as exc:
    print(f"FEHLER: duckdb-Modul fehlt: {exc}")
    sys.exit(1)

def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def table_exists(con, table: str) -> bool:
    return con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [table],
    ).fetchone()[0] == 1

def count_rows(con, table: str) -> int:
    return int(con.execute(f"SELECT COUNT(*) FROM {q(table)}").fetchone()[0])

def columns(con, table: str) -> list[str]:
    return [r[1] for r in con.execute(f"PRAGMA table_info({q(table)})").fetchall()]

def first_existing(cols: list[str], candidates: list[str]) -> str | None:
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None

def count_required_role(con, role: str) -> int:
    cols = columns(con, "agent_role_registry")
    col = first_existing(cols, ["role_code", "agent_code", "code"])
    if not col:
        raise RuntimeError("agent_role_registry hat keine Code-Spalte.")
    return int(con.execute(
        f"SELECT COUNT(*) FROM agent_role_registry WHERE {q(col)} = ?",
        [role],
    ).fetchone()[0])

def main() -> int:
    try:
        log("CHECK AGENTEN KONTEXT SKILL REGISTER V1 gestartet.")
        log(f"Datenbank: {DB_PATH}")
        log(f"Report: {REPORT}")

        if not DB_PATH.exists():
            raise FileNotFoundError(f"Datenbank fehlt: {DB_PATH}")

        failed = False
        con = duckdb.connect(str(DB_PATH), read_only=True)

        try:
            for table in TABLES:
                exists = table_exists(con, table)
                log(f"Tabelle {table}: {1 if exists else 0}")
                if not exists:
                    failed = True
                    continue

                rows = count_rows(con, table)
                log(f"{table}_rows: {rows}")

                if rows < MIN_COUNTS[table]:
                    log(f"FEHLER_MINDESMENGE {table}: {rows} < {MIN_COUNTS[table]}")
                    failed = True

            for role in REQUIRED_ROLES:
                c = count_required_role(con, role)
                log(f"required_role {role}: {c}")
                if c < 1:
                    failed = True

        finally:
            con.close()

        if failed:
            raise RuntimeError("Agenten-Kontext- und Skill-Register ist unvollständig.")

        log("OK: Agenten-Kontext- und Skill-Register V1 prüfbar.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())