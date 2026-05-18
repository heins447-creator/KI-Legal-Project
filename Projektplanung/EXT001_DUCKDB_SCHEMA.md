# EXT-001 – DuckDB-Schema für lokale Datenhaltung

## Zweck

Einführung von DuckDB als lokale, dateibasierte analytische Datenbank für das ALIN-Projekt. DuckDB eignet sich besonders für:

- Lokale Analytik ohne Server-Installation
- In-Process-Betrieb (kein separater Dienst)
- Spaltenorientierte Speicherung für OLAP-Abfragen
- Parquet- und CSV-Integration
- Vollständige Offline-Fähigkeit

## Sicherheitsgrenzen

- **Kein Cloud-DB-Service** (AWS RDS, Azure SQL, Google Cloud SQL verboten)
- **Keine echten Mandantendaten** in der Entwicklungsdatenbank
- **Keine Remote-Verbindungen** (nur lokale .duckdb-Dateien)
- **Schema-Migration nur nach Backup**
- Datenbankdatei liegt unter `Database/DuckDB/alin_local.duckdb`

## Schema-Struktur

### Tabellen

| Tabelle | Zweck | Schlüsselfelder |
|---------|-------|-----------------|
| `dokumente` | Metadaten zu importierten Dokumenten | `dokument_id` (UUID) |
| `ocr_ergebnisse` | OCR-Ergebnisse pro Dokument/Seite | `ocr_id` (UUID) |
| `uebersetzungen` | Übersetzungen von Textsegmenten | `uebersetzung_id` (UUID) |
| `terminologie` | EU-Terminologie und Übersetzungsäquivalente | `begriff_id` (UUID) |
| `vektor_embeddings` | Vektorembeddings für semantische Suche | `embedding_id` (UUID) |

### Views

| View | Zweck |
|------|-------|
| `v_dokumente_vollstaendigkeit` | Verarbeitungsstatus aller Dokumente (OCR, Übersetzung, Embeddings) |

### Indizes

- `idx_dokumente_status`, `idx_dokumente_sprache`
- `idx_ocr_dokument`, `idx_uebersetzung_dokument`
- `idx_terminologie_sprache`, `idx_terminologie_kategorie`
- `idx_embedding_dokument`

## Datenfluss

```
Import → dokumente → OCR → ocr_ergebnisse → Übersetzung → uebersetzungen
                                          → Terminologie → terminologie
                                          → Embeddings → vektor_embeddings
```

## Abhängigkeiten

- STUFE-026 (abgeschlossen)
- STUFE-001 (Datenbank-Grundschema)
- UI14 (Ausführungs-Nachlaufzentrale)

## Ausgaben

- `Database/Migrations/100_duckdb_schema_ext001.sql`
- `Database/DuckDB/alin_local.duckdb`
- `Scripts/python_runner/ext001_duckdb_schema.py`
- `Scripts/python_runner/check_ext001_duckdb_schema.py`
- `Scripts/EXT001_DUCKDB_SCHEMA_AUTOLAUF.ps1`
- `Config/ext001_duckdb_schema_v1.json`
- `ALIN_Neustart_Core/Reports/EXT001_DUCKDB_SCHEMA_BERICHT.txt`

## Idempotenz

Die Migration verwendet ausschließlich `CREATE ... IF NOT EXISTS`, sodass mehrfache Ausführung sicher ist.

## Testdaten

Ein synthetischer Test-Datensatz (`test_dokument.pdf`) wird eingefügt, um die Verbindung zu validieren. Keine echten Mandantendaten.

## Nächste Stufen

- EXT-002: Verbesserte OCR mit PaddleOCR
- EXT-003: EU-Terminologiepakete
- EXT-004: FastAPI-Backend
