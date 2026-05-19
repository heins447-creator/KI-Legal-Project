import sys
import os
import traceback
import duckdb

db_path = sys.argv[1]
sql_path = sys.argv[2]
report_path = sys.argv[3]

def w(text=""):
    with open(report_path, "a", encoding="utf-8", newline="\n") as f:
        f.write(str(text) + "\n")

def main():
    w("")
    w("PYTHON MIGRATION START")
    w("Datenbank: " + db_path)
    w("SQL:       " + sql_path)

    if not os.path.exists(db_path):
        raise FileNotFoundError(db_path)

    if not os.path.exists(sql_path):
        raise FileNotFoundError(sql_path)

    with open(sql_path, "r", encoding="utf-8-sig") as f:
        sql = f.read()

    con = duckdb.connect(db_path)

    try:
        statements = []
        current = []

        for line in sql.splitlines():
            stripped = line.strip()
            if not stripped:
                current.append(line)
                continue

            current.append(line)

            if stripped.endswith(";"):
                statement = "\n".join(current).strip()
                current = []
                if statement:
                    statements.append(statement)

        tail = "\n".join(current).strip()
        if tail:
            statements.append(tail)

        for statement in statements:
            con.execute(statement)

        tables = con.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND table_name LIKE 'posteingang_%'
            ORDER BY table_name
        """).fetchall()

        w("")
        w("Angelegte oder vorhandene Posteingang-Tabellen:")
        for (table_name,) in tables:
            count = con.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
            w(f"- {table_name}: {count} Zeilen")

        con.close()
        w("PYTHON MIGRATION OK")

    except Exception:
        try:
            con.close()
        except Exception:
            pass
        raise

try:
    main()
except Exception:
    w("PYTHON MIGRATION FEHLER")
    w(traceback.format_exc())
    sys.exit(1)
