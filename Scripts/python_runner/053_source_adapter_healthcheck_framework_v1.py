# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
DB_PATH = ROOT / "Database" / "Legal_Brain.duckdb"
MIGRATION = ROOT / "Database" / "Migrations" / "014_source_adapter_healthcheck_framework_v1.sql"
CONFIG_PATH = ROOT / "Config" / "source_adapter_policy_v1.json"
LOG_DIR = ROOT / "Windows_App" / "Logs"
REPORT = LOG_DIR / f"RUN_053_source_adapter_healthcheck_framework_v1_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"


def log(text: str = "") -> None:
    line = f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {text}"
    print(line)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.open("a", encoding="utf-8").write(line + "\n")


def sql_quote(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


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
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        if DUCKDB_MODULE:
            self.con = duckdb.connect(str(DB_PATH))
        elif not self.exe:
            raise RuntimeError("Weder Python-Modul duckdb noch duckdb.exe gefunden.")
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.con is not None:
            self.con.close()

    def execute(self, sql: str):
        if self.con is not None:
            self.con.execute(sql)
            return
        result = subprocess.run(
            [self.exe, str(DB_PATH), "-c", sql],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())

    def scalar(self, sql: str):
        if self.con is not None:
            return self.con.execute(sql).fetchone()[0]
        result = subprocess.run(
            [self.exe, str(DB_PATH), "-csv", "-noheader", "-c", sql],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip().splitlines()[0].strip()


def upsert(db: Db, table: str, key: str, row: dict) -> None:
    cols = list(row.keys())
    values = ", ".join(sql_quote(row[col]) for col in cols)
    col_sql = ", ".join(cols)
    db.execute(f"DELETE FROM {table} WHERE {key} = {sql_quote(row[key])};")
    db.execute(f"INSERT INTO {table} ({col_sql}) VALUES ({values});")


def main() -> int:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log("SOURCE ADAPTER HEALTHCHECK FRAMEWORK V1 gestartet.")
        log(f"Root: {ROOT}")
        log(f"Datenbank: {DB_PATH}")
        log(f"Migration: {MIGRATION}")
        log(f"Config: {CONFIG_PATH}")
        log(f"Report: {REPORT}")

        if not MIGRATION.exists():
            raise FileNotFoundError(f"Migration fehlt: {MIGRATION}")
        if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"Config fehlt: {CONFIG_PATH}")

        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        log("Config geladen.")

        with Db() as db:
            db.execute(MIGRATION.read_text(encoding="utf-8"))
            log("Migration angewendet.")

            upsert(db, "schema_migrations", "migration_id", {
                "migration_id": "014_source_adapter_healthcheck_framework_v1",
                "note_de": "Source Adapter Healthcheck Framework mit Dry-Run-Only-Standard",
            })

            # Adapter-Policies
            policies = [
                ("policy_rest", "REST-API Adapter Policy", "REST", "dryrun_only", False, True, "keine_im_klartext", "*.europa.eu", False),
                ("policy_html_meta", "HTML-Metadaten Adapter Policy", "HTML-Metadaten", "dryrun_only", False, False, "keine_im_klartext", "*.europa.eu", False),
                ("policy_download_manual", "Download-Manuell Adapter Policy", "Download-Manuell", "dryrun_only", False, False, "nicht_anwendbar", None, False),
                ("policy_offline_cache", "Offline-Cache Adapter Policy", "Offline-Cache", "dryrun_only", False, False, "nicht_anwendbar", None, True),
            ]
            for code, name, typ, scope, live, auth, cred, domain, offline in policies:
                upsert(db, "source_adapter_policy", "policy_code", {
                    "policy_code": code,
                    "policy_name": name,
                    "adapter_type": typ,
                    "allowed_scope": scope,
                    "live_run_enabled": live,
                    "auth_required": auth,
                    "credential_storage_rule": cred,
                    "allowed_domain_pattern": domain,
                    "offline_fallback_enabled": offline,
                    "notes_de": "Nur Dry-Run bis Freigabe. Kein Live-Abruf.",
                })
            log("Adapter-Policies angelegt.")

            # Endpoints (Dry-Run Platzhalter)
            endpoints = [
                ("ep_rest_eurlex", "policy_rest", "https://eur-lex.europa.eu/eli/", "dryrun_placeholder", False),
                ("ep_rest_ecli", "policy_rest", "https://ecli.eu/", "dryrun_placeholder", False),
                ("ep_html_justice", "policy_html_meta", "https://e-justice.europa.eu/", "dryrun_placeholder", False),
                ("ep_html_iate", "policy_html_meta", "https://iate.europa.eu/", "dryrun_placeholder", False),
                ("ep_manual_ccbe", "policy_download_manual", "CCBE manuell", "dryrun_placeholder", False),
                ("ep_offline_eurovoc", "policy_offline_cache", "EuroVoc Cache", "dryrun_placeholder", False),
            ]
            for code, pol, url_hint, etype, active in endpoints:
                upsert(db, "source_adapter_endpoint", "endpoint_code", {
                    "endpoint_code": code,
                    "policy_code": pol,
                    "endpoint_url_hint": url_hint,
                    "endpoint_type": etype,
                    "active": active,
                    "dryrun_result": "nicht_geprueft",
                    "notes_de": "Nur Platzhalter; kein Netzwerkzugriff im Standardlauf.",
                })
            log("Endpoints angelegt.")

            # Dry-Run Checks
            dryrun_checks = [
                ("dr_rest_schema", "ep_rest_eurlex", "schema_validierung", "bestanden", "Schema pruefung simuliert ohne Netzwerk.", True),
                ("dr_rest_auth", "ep_rest_eurlex", "auth_konfiguration_pruefung", "bestanden", "Auth-Config pruefung simuliert; keine Credentials im Klartext.", True),
                ("dr_html_meta", "ep_html_justice", "schema_validierung", "bestanden", "Schema pruefung simuliert ohne Netzwerk.", True),
                ("dr_offline_fallback", "ep_offline_eurovoc", "offline_fallback_verfuegbarkeit", "bestanden", "Offline-Fallback als konfiguriert markiert.", True),
                ("dr_manual_scope", "ep_manual_ccbe", "endpoint_erreichbarkeit_simuliert", "bestanden", "Manueller Download erfordert keine Erreichbarkeitspruefung.", True),
            ]
            for code, ep, ctype, result, detail, passed in dryrun_checks:
                upsert(db, "source_adapter_dryrun_check", "check_code", {
                    "check_code": code,
                    "endpoint_code": ep,
                    "check_type": ctype,
                    "check_result": result,
                    "check_detail_de": detail,
                    "passed": passed,
                    "notes_de": "Dry-Run ohne Netzwerkverbindung.",
                })
            log("Dry-Run-Checks angelegt.")

            # Security Rules
            security_rules = [
                ("sec_domain_whitelist", "policy_rest", "domain_whitelist", "domain IN ('eur-lex.europa.eu', 'curia.europa.eu', 'iate.europa.eu')", "erlauben_nach_freigabe", True, "Nur freigegebene Domains erlaubt."),
                ("sec_no_creds", "policy_rest", "no_credentials_in_code", "api_key IS NULL AND password IS NULL AND token IS NULL", "blockieren", True, "Keine Credentials im Klartext."),
                ("sec_dryrun_default", "policy_rest", "dryrun_only_default", "run_type != 'live'", "blockieren", True, "Live-Run standardmaessig blockiert."),
                ("sec_html_no_creds", "policy_html_meta", "no_credentials_in_code", "api_key IS NULL AND password IS NULL AND token IS NULL", "blockieren", True, "Keine Credentials im Klartext."),
                ("sec_html_dryrun", "policy_html_meta", "dryrun_only_default", "run_type != 'live'", "blockieren", True, "Live-Run standardmaessig blockiert."),
            ]
            for code, pol, rtype, expr, action, active, note in security_rules:
                upsert(db, "source_adapter_security_rule", "rule_code", {
                    "rule_code": code,
                    "policy_code": pol,
                    "rule_type": rtype,
                    "rule_expression": expr,
                    "rule_action": action,
                    "active": active,
                    "rule_note_de": note,
                })
            log("Sicherheitsregeln angelegt.")

            # Offline Fallbacks
            fallbacks = [
                ("fb_rest_eurlex", "policy_rest", "metadaten_cache", "EUR-Lex Metadaten-Cache", False, "Noch nicht befuellt."),
                ("fb_html_justice", "policy_html_meta", "html_snapshot", "HTML-Snapshot lokal", False, "Noch nicht befuellt."),
                ("fb_offline_eurovoc", "policy_offline_cache", "thesaurus_dump", "EuroVoc Thesaurus-Dump", True, "Offline-Cache als verfuegbar markiert."),
            ]
            for code, pol, ftype, hint, avail, note in fallbacks:
                upsert(db, "source_adapter_offline_fallback", "fallback_code", {
                    "fallback_code": code,
                    "policy_code": pol,
                    "fallback_type": ftype,
                    "fallback_content_hint": hint,
                    "fallback_available": avail,
                    "notes_de": note,
                })
            log("Offline-Fallbacks angelegt.")

            # Run Log: Nur Dry-Run-Eintrag, kein Live-Run
            upsert(db, "source_adapter_run_log", "log_id", {
                "log_id": "run_dryrun_initial",
                "policy_code": "policy_rest",
                "endpoint_code": "ep_rest_eurlex",
                "run_type": "dryrun",
                "run_status": "abgeschlossen",
                "run_result_de": "Dry-Run ohne Netzwerkverbindung erfolgreich.",
                "http_status": None,
                "network_used": False,
                "notes_de": "Standardlauf verwendet kein Netzwerk.",
            })
            log("Run-Log angelegt (nur Dry-Run).")

            # Pruefung
            policy_count = int(db.scalar("SELECT COUNT(*) FROM source_adapter_policy;"))
            endpoint_count = int(db.scalar("SELECT COUNT(*) FROM source_adapter_endpoint;"))
            dryrun_count = int(db.scalar("SELECT COUNT(*) FROM source_adapter_dryrun_check;"))
            rule_count = int(db.scalar("SELECT COUNT(*) FROM source_adapter_security_rule;"))
            fallback_count = int(db.scalar("SELECT COUNT(*) FROM source_adapter_offline_fallback;"))
            log(f"Pruefung: policies={policy_count}, endpoints={endpoint_count}, dryrun_checks={dryrun_count}, rules={rule_count}, fallbacks={fallback_count}")

            if policy_count < 4:
                raise RuntimeError("Nicht alle Adapter-Policies angelegt.")
            if endpoint_count < 6:
                raise RuntimeError("Nicht alle Endpoints angelegt.")

        log("OK: Source Adapter Healthcheck Framework V1 angelegt.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
