#!/usr/bin/env python3
"""
EXT-004 – FastAPI-Backend für lokale API

Ziel:
Bereitstellung eines lokalen API-Backends mit FastAPI für interne Dienste.
Exportiert die API-App als ausführbare Python-Datei, das OpenAPI-Schema
und ein PowerShell-Start-Skript. Führt einen kurzen Smoke-Test durch.

Sicherheit:
- Kein Cloud-Upload
- Keine Online-Anbindung
- Nur localhost (127.0.0.1)
- Keine echten Mandantendaten
"""

import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
API_DIR = BASE_DIR / "ALIN_Neustart_Core" / "25_API_Backend"
DB_DIR = BASE_DIR / "Database" / "DuckDB"
DB_PATH = DB_DIR / "alin_local.duckdb"
REPORT_FILE = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "EXT004_FASTAPI_BACKEND_BERICHT.txt"
CONFIG_FILE = BASE_DIR / "Config" / "ext004_fastapi_backend_v1.json"

API_FILE = API_DIR / "alin_api_main.py"
OPENAPI_FILE = API_DIR / "openapi_schema.json"
START_SCRIPT = API_DIR / "start_api.ps1"

HOST = "127.0.0.1"
PORT = 8744


def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def log(msg: str) -> None:
    print(f"[{zeitstempel()}] {msg}")


def erzeuge_api_datei() -> None:
    api_code = '''#!/usr/bin/env python3
"""ALIN FastAPI-Backend – lokale API"""

import json
from contextlib import asynccontextmanager
from pathlib import Path

import duckdb
from fastapi import FastAPI, HTTPException

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "Database" / "DuckDB" / "alin_local.duckdb"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/Shutdown Hook"""
    yield


app = FastAPI(
    title="ALIN Local API",
    description="Lokales API-Backend für ALIN Legal AI – keine Cloud-Anbindung",
    version="0.4.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "name": "ALIN Local API",
        "version": "0.4.0",
        "endpoints": [
            "/health",
            "/terminologie",
            "/terminologie/{begriff}",
            "/dokumente",
        ],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    from datetime import datetime, timezone
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "ALIN-API",
    }


@app.get("/terminologie")
def terminologie_liste():
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Datenbank nicht verfuegbar")
    conn = duckdb.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT begriff, sprache, kategorie, quelle, definition, kontext, aequivalente, validiert FROM alin_ext001.terminologie"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "begriff": r[0],
            "sprache": r[1],
            "kategorie": r[2],
            "quelle": r[3],
            "definition": r[4],
            "kontext": r[5],
            "aequivalente": json.loads(r[6]) if r[6] else {},
            "validiert": r[7],
        })
    return {"count": len(result), "eintraege": result}


@app.get("/terminologie/{begriff}")
def terminologie_eintrag(begriff: str):
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Datenbank nicht verfuegbar")
    conn = duckdb.connect(str(DB_PATH))
    row = conn.execute(
        "SELECT begriff, sprache, kategorie, quelle, definition, kontext, aequivalente, validiert FROM alin_ext001.terminologie WHERE begriff = ?",
        (begriff,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Begriff nicht gefunden")
    return {
        "begriff": row[0],
        "sprache": row[1],
        "kategorie": row[2],
        "quelle": row[3],
        "definition": row[4],
        "kontext": row[5],
        "aequivalente": json.loads(row[6]) if row[6] else {},
        "validiert": row[7],
    }


@app.get("/dokumente")
def dokumente_liste():
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Datenbank nicht verfuegbar")
    conn = duckdb.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT id, titel, sprache, status, erstellt_am FROM alin_ext001.dokumente"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "titel": r[1],
            "sprache": r[2],
            "status": r[3],
            "erstellt_am": r[4],
        })
    return {"count": len(result), "eintraege": result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8744, log_level="info")
'''
    API_FILE.write_text(api_code, encoding="utf-8")
    log(f"API-Datei erzeugt: {API_FILE}")


def erzeuge_start_script() -> None:
    script = f'''$ErrorActionPreference = "Stop"
$ProjektPython = "I:\\KI_Legal_Project\\Tools\\Python312\\python.exe"
$ApiDatei = "{API_FILE}"

Write-Host "ALIN FastAPI-Backend wird gestartet ..."
Write-Host "URL: http://{HOST}:{PORT}"
Write-Host "Docs: http://{HOST}:{PORT}/docs"
Write-Host "Druecken Sie STRG+C zum Beenden."
Write-Host ""

& $ProjektPython -m uvicorn alin_api_main:app --host {HOST} --port {PORT} --app-dir "{API_DIR}"
'''
    START_SCRIPT.write_text(script, encoding="utf-8")
    log(f"Start-Skript erzeugt: {START_SCRIPT}")


def exportiere_openapi() -> None:
    """Exportiert das OpenAPI-Schema durch einen kurzen Import der App."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("alin_api_main", API_FILE)
        mod = importlib.util.module_from_spec(spec)
        # Wir muessen den Pfad so setzen, dass DuckDB gefunden wird, aber wir
        # koennen das Schema auch ueber einen subprocess mit FastAPI CLI exportieren.
        # Alternativ: Wir nutzen den FastAPI app.openapi() Aufruf direkt nach dem Laden.
        spec.loader.exec_module(mod)
        schema = mod.app.openapi()
        OPENAPI_FILE.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"OpenAPI-Schema exportiert: {OPENAPI_FILE}")
    except Exception as e:
        log(f"WARNUNG: OpenAPI-Schema-Export fehlgeschlagen: {e}")


def smoke_test() -> tuple[bool, str]:
    """Startet uvicorn kurz, macht Requests, stoppt wieder."""
    log("Smoke-Test gestartet")
    proc = None
    try:
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "alin_api_main:app",
                "--host", HOST,
                "--port", str(PORT),
                "--app-dir", str(API_DIR),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Warte auf Server-Start
        time.sleep(3)

        # Healthcheck
        req = urllib.request.Request(f"http://{HOST}:{PORT}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            health_data = json.loads(resp.read().decode("utf-8"))
            if health_data.get("status") != "ok":
                return False, f"Healthcheck ungueltig: {health_data}"

        # Terminologie-Liste
        req2 = urllib.request.Request(f"http://{HOST}:{PORT}/terminologie")
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            term_data = json.loads(resp2.read().decode("utf-8"))
            if term_data.get("count", 0) < 1:
                return False, "Terminologie-Endpunkt liefert keine Daten"

        # Root
        req3 = urllib.request.Request(f"http://{HOST}:{PORT}/")
        with urllib.request.urlopen(req3, timeout=5) as resp3:
            root_data = json.loads(resp3.read().decode("utf-8"))
            if root_data.get("name") != "ALIN Local API":
                return False, "Root-Endpunkt ungueltig"

        return True, f"Health={health_data}, Terminologie={term_data['count']} Eintraege"
    except Exception as e:
        return False, f"Smoke-Test-Fehler: {e}"
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        log("Smoke-Test beendet")


def main() -> int:
    log("EXT-004 – FastAPI-Backend gestartet")

    if not DB_PATH.exists():
        log(f"FEHLER: DuckDB-Datenbank nicht gefunden: {DB_PATH}")
        return 1

    API_DIR.mkdir(parents=True, exist_ok=True)

    try:
        erzeuge_api_datei()
        erzeuge_start_script()
        exportiere_openapi()

        smoke_ok, smoke_msg = smoke_test()
        if not smoke_ok:
            log(f"FEHLER: {smoke_msg}")
            return 1

        log(f"Smoke-Test erfolgreich: {smoke_msg}")

    except Exception as e:
        log(f"FEHLER: {e}")
        return 1

    # Bericht
    bericht = f"""EXT-004 – FastAPI-Backend Bericht
Erzeugt: {zeitstempel()}
API-Datei: {API_FILE}
OpenAPI-Schema: {OPENAPI_FILE}
Start-Skript: {START_SCRIPT}
Datenbank: {DB_PATH}

Smoke-Test: ERFOLGREICH
{smoke_msg}

Status: ERFOLGREICH
"""
    REPORT_FILE.write_text(bericht, encoding="utf-8")
    log(f"Bericht geschrieben: {REPORT_FILE}")

    log("EXT-004 abgeschlossen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
