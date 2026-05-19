#!/usr/bin/env python3
"""
EXT-005 – Semantische Suche in Dokumenten

Ziel:
Lokale semantische Suche ueber Dokumenteninhalte mit TF-IDF-basierten
Vektor-Embeddings. Vollstaendig offline-faehig, keine externen Modelle.

Sicherheit:
- Kein Cloud-Embedding-Service
- Keine Vektor-Cloud-Datenbank
- Embedding-Berechnung offline und lokal
- Keine echten Mandantendokumente
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "Database" / "DuckDB"
DB_PATH = DB_DIR / "alin_local.duckdb"
REPORT_FILE = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "EXT005_SEMANTISCHE_SUCHE_BERICHT.txt"
CONFIG_FILE = BASE_DIR / "Config" / "ext005_semantische_suche_v1.json"

def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")

def log(msg: str) -> None:
    print(f"[{zeitstempel()}] {msg}")

def tokenisiere(text: str) -> list[str]:
    return text.lower().replace(",", " ").replace(".", " ").replace(";", " ").split()

def berechne_tfidf(dokumente: list[str]) -> tuple[np.ndarray, list[str]]:
    """Berechnet TF-IDF-Matrix fuer eine Liste von Dokumenten."""
    tokenisierte = [tokenisiere(d) for d in dokumente]
    vocab = sorted({w for tokens in tokenisierte for w in tokens})
    vocab_index = {w: i for i, w in enumerate(vocab)}
    N = len(dokumente)

    # TF
    tf = np.zeros((N, len(vocab)), dtype=np.float64)
    for i, tokens in enumerate(tokenisierte):
        for w in tokens:
            tf[i, vocab_index[w]] += 1
        tf[i] /= max(len(tokens), 1)

    # IDF
    df = np.zeros(len(vocab), dtype=np.float64)
    for tokens in tokenisierte:
        unique = set(tokens)
        for w in unique:
            df[vocab_index[w]] += 1
    idf = np.log((N + 1) / (df + 1)) + 1

    tfidf = tf * idf
    # L2-Normalisierung
    norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
    norms[norms == 0] = 1
    tfidf = tfidf / norms
    return tfidf, vocab

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))

def main() -> int:
    log("EXT-005 – Semantische Suche gestartet")

    if not DB_PATH.exists():
        log(f"FEHLER: DuckDB nicht gefunden: {DB_PATH}")
        return 1

    conn = duckdb.connect(str(DB_PATH))

    # 1) Texte sammeln
    texte = []
    metadaten = []

    # Terminologie-Eintraege
    term_rows = conn.execute(
        "SELECT begriff, definition, kontext FROM alin_ext001.terminologie"
    ).fetchall()
    for r in term_rows:
        text = f"{r[0]} {r[1] or ''} {r[2] or ''}"
        texte.append(text)
        metadaten.append({"typ": "terminologie", "id": r[0]})

    # OCR-Ergebnisse
    ocr_rows = conn.execute(
        "SELECT ocr_id, roh_text, strukturiertes_text FROM alin_ext001.ocr_ergebnisse"
    ).fetchall()
    for r in ocr_rows:
        text = r[1] or ""
        if r[2]:
            try:
                strukt = json.loads(r[2])
                if isinstance(strukt, dict) and "blocks" in strukt:
                    text += " " + " ".join(b.get("text", "") for b in strukt["blocks"])
            except json.JSONDecodeError:
                pass
        texte.append(text)
        metadaten.append({"typ": "ocr", "id": str(r[0])})

    if not texte:
        log("FEHLER: Keine Texte zum Indexieren gefunden")
        conn.close()
        return 1

    log(f"{len(texte)} Texte zum Indexieren gefunden")

    # 2) TF-IDF berechnen
    tfidf_matrix, vocab = berechne_tfidf(texte)
    dimension = len(vocab)
    log(f"Vokabular-Groesse: {dimension}")

    # 3) Dokument-ID holen (wir verwenden das erste Dokument als Referenz)
    doc_rows = conn.execute("SELECT dokument_id FROM alin_ext001.dokumente LIMIT 1").fetchall()
    dokument_id = doc_rows[0][0] if doc_rows else "00000000-0000-0000-0000-000000000000"

    # 4) Vektoren in DuckDB speichern
    count_vor = conn.execute("SELECT COUNT(*) FROM alin_ext001.vektor_embeddings WHERE embedding_model = 'tfidf_numpy_local'").fetchone()[0]

    for i, meta in enumerate(metadaten):
        vec = tfidf_matrix[i].tolist()
        conn.execute("""
            INSERT INTO alin_ext001.vektor_embeddings
            (dokument_id, segment_typ, segment_id, embedding_model, dimension, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT DO NOTHING
        """, (dokument_id, meta["typ"], meta["id"], "tfidf_numpy_local", dimension, vec))

    count_nach = conn.execute("SELECT COUNT(*) FROM alin_ext001.vektor_embeddings WHERE embedding_model = 'tfidf_numpy_local'").fetchone()[0]
    inserted = count_nach - count_vor
    log(f"{inserted} Vektor-Embeddings eingefuegt")

    # 5) Semantische Suche testen
    test_query = "Verordnung Europaeische Union"
    query_tokens = tokenisiere(test_query)
    query_vec = np.zeros(dimension, dtype=np.float64)
    vocab_index = {w: i for i, w in enumerate(vocab)}
    for w in query_tokens:
        if w in vocab_index:
            query_vec[vocab_index[w]] += 1
    query_norm = np.linalg.norm(query_vec)
    if query_norm > 0:
        query_vec /= query_norm

    best_score = -1
    best_idx = -1
    for i in range(len(texte)):
        score = cosine_similarity(query_vec, tfidf_matrix[i])
        if score > best_score:
            best_score = score
            best_idx = i

    best_text = texte[best_idx] if best_idx >= 0 else ""
    log(f"Test-Suche '{test_query}': beste Uebereinstimmung = {best_score:.4f} ({best_text[:80]}...)")

    conn.close()

    # 6) Bericht
    bericht = f"""EXT-005 – Semantische Suche Bericht
Erzeugt: {zeitstempel()}
Datenbank: {DB_PATH}

Texte indexiert: {len(texte)}
Vokabular-Groesse: {dimension}
Eingefuegte Embeddings: {inserted}

Test-Suche: '{test_query}'
Bestes Ergebnis: Score={best_score:.4f}
Text: {best_text[:200]}

Status: ERFOLGREICH
"""
    REPORT_FILE.write_text(bericht, encoding="utf-8")
    log(f"Bericht geschrieben: {REPORT_FILE}")

    log("EXT-005 abgeschlossen")
    return 0

if __name__ == "__main__":
    sys.exit(main())
