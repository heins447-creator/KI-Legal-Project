#!/usr/bin/env python3
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
