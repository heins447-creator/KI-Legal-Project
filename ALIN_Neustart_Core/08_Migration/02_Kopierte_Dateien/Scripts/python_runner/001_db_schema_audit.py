import os
import sys
import sqlite3
import traceback

root = r"I:\KI_Legal_Project"
report = sys.argv[1]

def w(text=""):
    with open(report, "a", encoding="utf-8", newline="\n") as f:
        f.write(str(text) + "\n")

def q(name):
    return '"' + str(name).replace('"', '""') + '"'

def inspect_duckdb(path, label):
    w("")
    w("DUCKDB")
    w("=" * 80)
    w("Name: " + label)
    w("Pfad: " + path)

    if not os.path.exists(path):
        w("Status: FEHLT")
        return

    try:
        import duckdb
    except Exception as e:
        w("Status: FEHLER")
        w("DuckDB-Modul nicht ladbar: " + repr(e))
        return

    try:
        con = duckdb.connect(path, read_only=True)

        tables = con.execute("""
            SELECT table_schema, table_name, table_type
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """).fetchall()

        w("Tabellen und Views: " + str(len(tables)))

        for schema, table, table_type in tables:
            w("")
            w(f"[{table_type}] {schema}.{table}")

            cols = con.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = ? AND table_name = ?
                ORDER BY ordinal_position
            """, [schema, table]).fetchall()

            for col, dtype, nullable in cols:
                w(f"  - {col} | {dtype} | nullable={nullable}")

            if table_type.upper() == "BASE TABLE":
                try:
                    count = con.execute(f"SELECT COUNT(*) FROM {q(schema)}.{q(table)}").fetchone()[0]
                    w("  Zeilen: " + str(count))
                except Exception as e:
                    w("  Zeilenzahl nicht lesbar: " + repr(e))

        con.close()
        w("Status: OK READONLY")

    except Exception:
        w("Status: FEHLER")
        w(traceback.format_exc())

def inspect_sqlite(path, label):
    w("")
    w("SQLITE")
    w("=" * 80)
    w("Name: " + label)
    w("Pfad: " + path)

    if not os.path.exists(path):
        w("Status: FEHLT")
        return

    try:
        uri = "file:" + path.replace("\\", "/") + "?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        cur = con.cursor()

        tables = cur.execute("""
            SELECT name, type
            FROM sqlite_master
            WHERE type IN ('table', 'view')
            ORDER BY type, name
        """).fetchall()

        tables = [(n, t) for n, t in tables if not n.startswith("sqlite_")]
        w("Tabellen und Views: " + str(len(tables)))

        for name, typ in tables:
            w("")
            w(f"[{typ.upper()}] {name}")

            cols = cur.execute("PRAGMA table_info(" + q(name) + ")").fetchall()
            for cid, cname, ctype, notnull, dflt, pk in cols:
                w(f"  - {cname} | {ctype} | notnull={notnull} | pk={pk}")

            if typ == "table":
                try:
                    count = cur.execute("SELECT COUNT(*) FROM " + q(name)).fetchone()[0]
                    w("  Zeilen: " + str(count))
                except Exception as e:
                    w("  Zeilenzahl nicht lesbar: " + repr(e))

        con.close()
        w("Status: OK READONLY")

    except Exception:
        w("Status: FEHLER")
        w(traceback.format_exc())

w("DATENBANKSCHEMA-AUSWERTUNG")
w("=" * 80)
w("Projekt: " + root)
w("Keine Datenbank wird verändert.")
w("AnythingLLM wird ausdrücklich ausgeklammert.")
w("")

inspect_duckdb(os.path.join(root, "Case_Data.duckdb"), "Case_Data.duckdb")
inspect_duckdb(os.path.join(root, "Database", "Legal_Brain.duckdb"), "Database\\Legal_Brain.duckdb")

inspect_sqlite(os.path.join(root, "Database", "legal_core.db"), "Database\\legal_core.db")
inspect_sqlite(os.path.join(root, "Database", "legal_hpa.db"), "Database\\legal_hpa.db")
inspect_sqlite(os.path.join(root, "Scripts", "legal_core.db"), "Scripts\\legal_core.db")

w("")
w("FACHLICHE VORBEWERTUNG POSTEINGANG")
w("=" * 80)
w("Ungeprüfte Dateien gehören nicht unmittelbar in den normalen Dokumentenbestand.")
w("In die Datenbank gehört zunächst nur der technische Eingangsvermerk.")
w("Zu speichern sind insbesondere Eingangskanal, Dateiname, Hashwert, Prüfergebnis, Signaturstatus, Absenderstatus, Quarantänestatus und Vorzimmerentscheidung.")
w("Der eigentliche Dateiinhalt bleibt bis zur Freigabe außerhalb des normalen Dokumentenbestands.")
w("Nach Freigabe durch das Vorzimmer erfolgt Übergabe an den Anwalt oder Rückfrage an den Absender.")
w("")
w("ENDE")
