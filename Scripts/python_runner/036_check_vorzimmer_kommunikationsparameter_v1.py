# -*- coding: utf-8 -*-
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import duckdb

DB = Path(r"I:\KI_Legal_Project\Database\Legal_Brain.duckdb")

con = duckdb.connect(str(DB), read_only=True)

tables = [x[0] for x in con.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'main'
    ORDER BY table_name
""").fetchall()]

required = [
    "vz_language_package_catalog",
    "vz_communication_context_template",
    "vz_participant_communication_profile",
    "vz_address_language_inference_rule",
    "vz_communication_parameter_audit",
]

missing = [x for x in required if x not in tables]

print("Datenbank:", DB)
print("Fehlende Tabellen:", missing)

if missing:
    raise RuntimeError("Tabellen fehlen: " + repr(missing))

print("EU24:", con.execute("SELECT COUNT(*) FROM vz_language_package_catalog WHERE eu_official = TRUE").fetchone()[0])

print("Template:", con.execute("""
    SELECT jurisdiction_country_code, official_language_code, procedural_language_code,
           internal_work_language_code, rough_translation_target_language_code,
           default_document_language_code
    FROM vz_communication_context_template
    WHERE template_key = 'TEMPLATE_SE_ARBEITSRECHT'
""").fetchone())

print("Beteiligtenprofile:", con.execute("SELECT COUNT(*) FROM vz_participant_communication_profile").fetchone()[0])
print("Adressregeln:", con.execute("SELECT COUNT(*) FROM vz_address_language_inference_rule WHERE active = TRUE").fetchone()[0])

print("Externe Kommunikation nicht Schwedisch:", con.execute("""
    SELECT COUNT(*)
    FROM vz_participant_communication_profile
    WHERE template_key = 'TEMPLATE_SE_ARBEITSRECHT'
      AND participant_role IN ('gericht', 'gegenseite', 'gegnerischer_anwalt')
      AND communication_language_code <> 'sv'
""").fetchone()[0])

con.close()
