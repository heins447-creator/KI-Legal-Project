# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
DB_PATH = ROOT / "Database" / "Legal_Brain.duckdb"
LOG_DIR = ROOT / "Windows_App" / "Logs"
REPORT = LOG_DIR / f"RUN_049_check_agenten_kontext_skill_register_v1_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

REQUIRED_TABLES = [
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
    "agent_arbeitsrecht_se",
    "agent_quellenbetreuer",
    "agent_sprachpaket_sv_de",
    "agent_medizinrecht_pruef",
    "agent_sozialrecht_pruef",
    "agent_zivilrecht_pruef",
]

REQUIRED_SKILLS = [
    "skill_arbeitsrecht_se_vertrag",
    "skill_arbeitsrecht_se_kuendigung",
    "skill_quellenbetreuer_registrierung",
    "skill_sprachpaket_sv_de_uebersetzung",
    "skill_medizinrecht_pruefung",
    "skill_sozialrecht_pruefung",
    "skill_zivilrecht_pruefung",
]


def log(text: str = "") -> None:
    line = f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {text}"
    print(line)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.open("a", encoding="utf-8").write(line + "\n")


def find_duckdb_exe() -> str | None:
    candidates = [
        ROOT / "Tools" / "DuckDB" / "duckdb.exe",
        ROOT / "Tools" / "duckdb.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return shutil.which("duckdb")


try:
    import duckdb  # type: ignore
    DUCKDB_MODULE = True
except Exception:
    duckdb = None
    DUCKDB_MODULE = False


class Db:
    def __init__(self):
        self.exe = find_duckdb_exe()
        self.con = None

    def __enter__(self):
        if DUCKDB_MODULE:
            self.con = duckdb.connect(str(DB_PATH), read_only=True)
        elif not self.exe:
            raise RuntimeError("Weder Python-Modul duckdb noch duckdb.exe gefunden.")
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.con is not None:
            self.con.close()

    def scalar(self, sql: str) -> int:
        if self.con is not None:
            return int(self.con.execute(sql).fetchone()[0])
        result = subprocess.run(
            [self.exe, str(DB_PATH), "-csv", "-noheader", "-c", sql],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return int(result.stdout.strip().splitlines()[0].strip())


def main() -> int:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log("CHECK AGENTEN KONTEXT SKILL REGISTER V1 gestartet.")
        log(f"Datenbank: {DB_PATH}")
        log(f"Report: {REPORT}")

        if not DB_PATH.exists():
            raise FileNotFoundError(f"Datenbank fehlt: {DB_PATH}")

        with Db() as db:
            for table in REQUIRED_TABLES:
                count = db.scalar(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    f"WHERE table_name = '{table}';"
                )
                if count != 1:
                    raise RuntimeError(f"Tabelle fehlt: {table}")
                log(f"OK Tabelle: {table}")

            for role in REQUIRED_ROLES:
                count = db.scalar(
                    f"SELECT COUNT(*) FROM agent_role_registry WHERE role_code = '{role}';"
                )
                if count != 1:
                    raise RuntimeError(f"Rolle fehlt: {role}")
                log(f"OK Rolle: {role}")

            for skill in REQUIRED_SKILLS:
                count = db.scalar(
                    f"SELECT COUNT(*) FROM agent_skill_registry WHERE skill_code = '{skill}';"
                )
                if count != 1:
                    raise RuntimeError(f"Skill fehlt: {skill}")
                log(f"OK Skill: {skill}")

            scope_count = db.scalar("SELECT COUNT(*) FROM agent_scope_rule;")
            if scope_count < 6:
                raise RuntimeError(f"Zu wenige Scope-Regeln: {scope_count}")
            log(f"OK Scope-Regeln: {scope_count}")

            handoff_count = db.scalar("SELECT COUNT(*) FROM agent_handoff_protocol;")
            if handoff_count < 3:
                raise RuntimeError(f"Zu wenige Handoff-Protokolle: {handoff_count}")
            log(f"OK Handoff-Protokolle: {handoff_count}")

            route_count = db.scalar("SELECT COUNT(*) FROM agent_handoff_route;")
            if route_count < 3:
                raise RuntimeError(f"Zu wenige Handoff-Routen: {route_count}")
            log(f"OK Handoff-Routen: {route_count}")

            uncert_count = db.scalar("SELECT COUNT(*) FROM agent_uncertainty_rule;")
            if uncert_count < 3:
                raise RuntimeError(f"Zu wenige Unsicherheitsregeln: {uncert_count}")
            log(f"OK Unsicherheitsregeln: {uncert_count}")

            source_bind_count = db.scalar("SELECT COUNT(*) FROM agent_source_binding;")
            if source_bind_count < 12:
                raise RuntimeError(f"Zu wenige Quellenbindungen: {source_bind_count}")
            log(f"OK Quellenbindungen: {source_bind_count}")

            lang_bind_count = db.scalar("SELECT COUNT(*) FROM agent_language_package_binding;")
            if lang_bind_count < 2:
                raise RuntimeError(f"Zu wenige Sprachpaketbindungen: {lang_bind_count}")
            log(f"OK Sprachpaketbindungen: {lang_bind_count}")

        log("OK: Agenten Kontext Skill Register V1 pruefbar.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
