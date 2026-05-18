#!/usr/bin/env python3
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

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "service": "ALIN-API-EXT"}

from datetime import datetime, timezone

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
