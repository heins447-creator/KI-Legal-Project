#!/usr/bin/env python3
"""
EXT-006 – Semantische Suche API-Endpunkt

Ziel:
Erweiterung des FastAPI-Backends um einen /suche Endpunkt,
der semantische Suche ueber DuckDB-Vektoren ermoeglicht.
TF-IDF-basiert, offline-faehig, vollstaendig lokal.

Sicherheit:
- Kein Cloud-Service
- Keine externen Modelle
- Nur localhost
- Keine echten Mandantendaten
"""

import json
import math
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
API_DIR = BASE_DIR / "ALIN_Neustart_Core" / "25_API_Backend"
DB_PATH = BASE_DIR / "Database" / "DuckDB" / "alin_local.duckdb"
REPORT_FILE = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "EXT006_SEMANTISCHE_SUCHE_API_BERICHT.txt"
CONFIG_FILE = BASE_DIR / "Config" / "ext006_semantische_suche_api_v1.json"

API_FILE = API_DIR / "alin_api_erweitert.py"
START_SCRIPT = API_DIR / "start_api_erweitert.ps1"
HOST = "127.0.0.1"
PORT = 8745

def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")

def log(msg: str) -> None:
    print(f"[{zeitstempel()}] {msg}")

def tokenisiere(text: str) -> list[str]:
    return text.lower().replace(",", " ").replace(".", " ").replace(";", " ").split()

def berechne_tfidf(dokumente: list[str]) -> tuple[np.ndarray, list[str]]:
    tokenisierte = [tokenisiere(d) for d in dokumente]
    vocab = sorted({w for tokens in tokenisierte for w in tokens})
    vocab_index = {w: i for i, w in enumerate(vocab)}
    N = len(dokumente)
    tf = np.zeros((N, len(vocab)), dtype=np.float64)
    for i, tokens in enumerate(tokenisierte):
        for w in tokens:
            tf[i, vocab_index[w]] += 1
        tf[i] /= max(len(tokens), 1)
    df = np.zeros(len(vocab), dtype=np.float64)
    for tokens in tokenisierte:
        for w in set(tokens):
            df[vocab_index[w]] += 1
    idf = np.log((N + 1) / (df + 1)) + 1
    tfidf = tf * idf
    norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
    norms[norms == 0] = 1
    tfidf = tfidf / norms
    return tfidf, vocab

def erzeuge_erweiterte_api() -> None:
    api_code = '''#!/usr/bin/env python3
"""ALIN FastAPI-Erweitert – mit semantischer Suche"""

import json
import math
from contextlib import asynccontextmanager
from pathlib import Path

import duckdb
import numpy as np
from fastapi import FastAPI, HTTPException, Query

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "Database" / "DuckDB" / "alin_local.duckdb"

# Globale Index-Struktur (wird beim Start geladen)
INDEX = {"texte": [], "vektoren": None, "vocab": [], "vocab_index": {}}

def tokenisiere(text: str):
    return text.lower().replace(",", " ").replace(".", " ").replace(";", " ").split()

def lade_index():
    if not DB_PATH.exists():
        return
    conn = duckdb.connect(str(DB_PATH))
    texte = []
    # Terminologie
    rows = conn.execute("SELECT begriff, definition, kontext FROM alin_ext001.terminologie").fetchall()
    for r in rows:
        texte.append(f"{r[0]} {r[1] or ''} {r[2] or ''}")
    # OCR
    ocr_rows = conn.execute("SELECT roh_text, strukturiertes_text FROM alin_ext001.ocr_ergebnisse").fetchall()
    for r in ocr_rows:
        t = r[0] or ""
        if r[1]:
            try:
                s = json.loads(r[1])
                if isinstance(s, dict) and "blocks" in s:
                    t += " " + " ".join(b.get("text", "") for b in s["blocks"])
            except:
                pass
        texte.append(t)
    conn.close()
    if not texte:
        return
    tokenisierte = [tokenisiere(d) for d in texte]
    vocab = sorted({w for tokens in tokenisierte for w in tokens})
    vocab_index = {w: i for i, w in enumerate(vocab)}
    N = len(texte)
    tf = np.zeros((N, len(vocab)), dtype=np.float64)
    for i, tokens in enumerate(tokenisierte):
        for w in tokens:
            tf[i, vocab_index[w]] += 1
        tf[i] /= max(len(tokens), 1)
    df = np.zeros(len(vocab), dtype=np.float64)
    for tokens in tokenisierte:
        for w in set(tokens):
            df[vocab_index[w]] += 1
    idf = np.log((N + 1) / (df + 1)) + 1
    tfidf = tf * idf
    norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
    norms[norms == 0] = 1
    tfidf = tfidf / norms
    INDEX["texte"] = texte
    INDEX["vektoren"] = tfidf
    INDEX["vocab"] = vocab
    INDEX["vocab_index"] = vocab_index

@asynccontextmanager
async def lifespan(app: FastAPI):
    lade_index()
    yield

app = FastAPI(
    title="ALIN Local API - Erweitert",
    description="Lokales API-Backend mit semantischer Suche",
    version="0.6.0",
    lifespan=lifespan,
)

@app.get("/")
def root():
    return {
        "name": "ALIN Local API - Erweitert",
        "version": "0.6.0",
        "endpoints": ["/health", "/terminologie", "/terminologie/{begriff}", "/dokumente", "/suche"],
        "docs": "/docs",
    }

from datetime import datetime, timezone

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "service": "ALIN-API-EXT"}

@app.get("/suche")
def suche(q: str = Query(..., min_length=1)):
    if INDEX["vektoren"] is None or len(INDEX["texte"]) == 0:
        raise HTTPException(status_code=503, detail="Suchindex nicht verfuegbar")
    query_tokens = tokenisiere(q)
    query_vec = np.zeros(len(INDEX["vocab"]), dtype=np.float64)
    for w in query_tokens:
        if w in INDEX["vocab_index"]:
            query_vec[INDEX["vocab_index"][w]] += 1
    q_norm = np.linalg.norm(query_vec)
    if q_norm == 0:
        return {"query": q, "count": 0, "ergebnisse": []}
    query_vec /= q_norm
    scores = np.dot(INDEX["vektoren"], query_vec)
    top_indices = np.argsort(scores)[::-1][:5]
    ergebnisse = []
    for idx in top_indices:
        if scores[idx] > 0:
            ergebnisse.append({"rang": int(idx), "text": INDEX["texte"][idx][:200], "score": float(scores[idx])})
    return {"query": q, "count": len(ergebnisse), "ergebnisse": ergebnisse}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8745, log_level="info")
'''
    API_FILE.write_text(api_code, encoding="utf-8")
    log(f"Erweiterte API-Datei erzeugt: {API_FILE}")

def erzeuge_start_script() -> None:
    script = f'''$ErrorActionPreference = "Stop"
$ProjektPython = "I:\\KI_Legal_Project\\Tools\\Python312\\python.exe"
$ApiDatei = "{API_FILE}"

Write-Host "ALIN FastAPI-Erweitert wird gestartet ..."
Write-Host "URL: http://{HOST}:{PORT}"
Write-Host "Docs: http://{HOST}:{PORT}/docs"
Write-Host "Druecken Sie STRG+C zum Beenden."
Write-Host ""

& $ProjektPython -m uvicorn alin_api_erweitert:app --host {HOST} --port {PORT} --app-dir "{API_DIR}"
'''
    START_SCRIPT.write_text(script, encoding="utf-8")
    log(f"Start-Skript erzeugt: {START_SCRIPT}")

def smoke_test() -> tuple[bool, str]:
    log("Smoke-Test gestartet")
    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "alin_api_erweitert:app",
             "--host", HOST, "--port", str(PORT), "--app-dir", str(API_DIR)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        time.sleep(3)
        req = urllib.request.Request(f"http://{HOST}:{PORT}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            health_data = json.loads(resp.read().decode("utf-8"))
            if health_data.get("status") != "ok":
                return False, f"Healthcheck ungueltig: {health_data}"
        req2 = urllib.request.Request(f"http://{HOST}:{PORT}/suche?q=Verordnung")
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            suche_data = json.loads(resp2.read().decode("utf-8"))
            if suche_data.get("count", 0) < 1:
                return False, "Suche liefert keine Ergebnisse"
        return True, f"Health={health_data}, Suche={suche_data['count']} Ergebnisse"
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
    log("EXT-006 – Semantische Suche API-Endpunkt gestartet")

    if not DB_PATH.exists():
        log(f"FEHLER: DuckDB nicht gefunden: {DB_PATH}")
        return 1

    API_DIR.mkdir(parents=True, exist_ok=True)

    try:
        erzeuge_erweiterte_api()
        erzeuge_start_script()
        smoke_ok, smoke_msg = smoke_test()
        if not smoke_ok:
            log(f"FEHLER: {smoke_msg}")
            return 1
        log(f"Smoke-Test erfolgreich: {smoke_msg}")
    except Exception as e:
        log(f"FEHLER: {e}")
        return 1

    bericht = f"""EXT-006 – Semantische Suche API-Endpunkt Bericht
Erzeugt: {zeitstempel()}
API-Datei: {API_FILE}
Start-Skript: {START_SCRIPT}

Smoke-Test: ERFOLGREICH
{smoke_msg}

Status: ERFOLGREICH
"""
    REPORT_FILE.write_text(bericht, encoding="utf-8")
    log(f"Bericht geschrieben: {REPORT_FILE}")

    log("EXT-006 abgeschlossen")
    return 0

if __name__ == "__main__":
    sys.exit(main())
