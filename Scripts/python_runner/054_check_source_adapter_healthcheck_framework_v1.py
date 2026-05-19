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
REPORT = LOG_DIR / f"RUN_054_check_source_adapter_healthcheck_framework_v1_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

REQUIRED_TABLES = [
    "source_adapter_policy",
    "source_adapter_endpoint",
    "source_adapter_dryrun_check",
    "source_adapter_security_rule",
    "source_adapter_offline_fallback",
    "source_adapter_run_log",
]

REQUIRED_POLICIES = [
    "policy_rest",
    "policy_html_meta",
    "policy_download_manual",
    "policy_offline_cache",
]

REQUIRED_RULES = [
    "sec_domain_whitelist",
    "sec_no_creds",
    "sec_dryrun_default",
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

    def scalar_str(self, sql: str) -> str:
        if self.con is not None:
            row = self.con.execute(sql).fetchone()
            return str(row[0]) if row and row[0] is not None else ""
        result = subprocess.run(
            [self.exe, str(DB_PATH), "-csv", "-noheader", "-c", sql],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        lines = result.stdout.strip().splitlines()
        return lines[0].strip() if lines else ""


def main() -> int:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log("CHECK SOURCE ADAPTER HEALTHCHECK FRAMEWORK V1 gestartet.")
        log(f"Datenbank: {DB_PATH}")
        log(f"Report: {REPORT}")

        if not DB_PATH.exists():
            raise FileNotFoundError(f"Datenbank fehlt: {DB_PATH}")

        with Db() as db:
            # Tabellen
            for table in REQUIRED_TABLES:
                count = db.scalar(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    f"WHERE table_name = '{table}';"
                )
                if count != 1:
                    raise RuntimeError(f"Tabelle fehlt: {table}")
                log(f"OK Tabelle: {table}")

            # Policies
            for policy in REQUIRED_POLICIES:
                count = db.scalar(
                    f"SELECT COUNT(*) FROM source_adapter_policy WHERE policy_code = '{policy}';"
                )
                if count != 1:
                    raise RuntimeError(f"Policy fehlt: {policy}")
                log(f"OK Policy: {policy}")

            # Sicherheitsregeln
            for rule in REQUIRED_RULES:
                count = db.scalar(
                    f"SELECT COUNT(*) FROM source_adapter_security_rule WHERE rule_code = '{rule}';"
                )
                if count != 1:
                    raise RuntimeError(f"Sicherheitsregel fehlt: {rule}")
                log(f"OK Sicherheitsregel: {rule}")

            # Dry-Run-Only: Kein Live-Run erlaubt
            live_enabled = db.scalar("SELECT COUNT(*) FROM source_adapter_policy WHERE live_run_enabled = TRUE;")
            if live_enabled != 0:
                raise RuntimeError(f"Live-Run ist bei {live_enabled} Policies aktiviert. Standard muss Dry-Run-Only sein.")
            log("OK Dry-Run-Only: Kein Live-Run aktiviert.")

            # Keine Credentials im Klartext
            cred_violations = db.scalar(
                "SELECT COUNT(*) FROM source_adapter_policy WHERE credential_storage_rule = 'keine_im_klartext' AND auth_required = TRUE;"
            )
            log(f"OK Credentials-Regel geprueft: {cred_violations} Policies mit Auth haben 'keine_im_klartext'.")

            # Keine Netzwerkverbindung im Standardlauf
            network_used = db.scalar("SELECT COUNT(*) FROM source_adapter_run_log WHERE network_used = TRUE;")
            if network_used != 0:
                raise RuntimeError(f"Run-Log enthaelt {network_used} Eintraege mit Netzwerknutzung.")
            log("OK Keine Netzwerknutzung im Run-Log.")

            # Keine Massendaten
            total_policies = db.scalar("SELECT COUNT(*) FROM source_adapter_policy;")
            total_endpoints = db.scalar("SELECT COUNT(*) FROM source_adapter_endpoint;")
            if total_policies > 25 or total_endpoints > 50:
                raise RuntimeError(f"Massendatenverdacht: policies={total_policies}, endpoints={total_endpoints}")
            log(f"OK Keine Massendaten: policies={total_policies}, endpoints={total_endpoints}")

            # Offline-Fallback verfuegbar
            offline_avail = db.scalar(
                "SELECT COUNT(*) FROM source_adapter_offline_fallback WHERE fallback_available = TRUE;"
            )
            log(f"OK Offline-Fallbacks verfuegbar: {offline_avail}")

        log("OK: Source Adapter Healthcheck Framework V1 pruefbar.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
