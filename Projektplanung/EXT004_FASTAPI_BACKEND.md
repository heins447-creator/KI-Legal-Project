# EXT-004 – FastAPI-Backend für lokale API

## Ziel
Bereitstellung eines lokalen API-Backends mit FastAPI für interne ALIN-Dienste.

## Abhängigkeiten
- EXT-001 (DuckDB-Schema)
- EXT-003 (EU-Terminologiepaket)

## Sicherheitsregeln
- **Cloud verboten**: Kein Cloud-Upload, keine externe API-Anbindung.
- **Nur localhost**: Server bindet an `127.0.0.1:8744`.
- **Keine echten Mandantendaten**: Alle Testdaten sind synthetisch.
- **Kein automatischer Hintergrunddienst**: Server muss manuell gestartet werden.

## Architektur
```
Client (lokal)
    │
    ▼
FastAPI (127.0.0.1:8744)
    │
    ├── GET /          → API-Info
    ├── GET /health    → Healthcheck
    ├── GET /terminologie          → Alle Begriffe (DuckDB)
    ├── GET /terminologie/{begriff} → Einzelner Begriff
    └── GET /dokumente            → Alle Dokumente (DuckDB)
    │
    ▼
DuckDB (alin_local.duckdb)
```

## Dateien
| Datei | Zweck |
|-------|-------|
| `Scripts/python_runner/ext004_fastapi_backend.py` | Runner: erzeugt API-Datei, OpenAPI-Schema, Start-Skript, führt Smoke-Test durch |
| `Scripts/python_runner/check_ext004_fastapi_backend.py` | Check: prüft FastAPI, Uvicorn, DuckDB, Tabellen |
| `Scripts/EXT004_FASTAPI_BACKEND_AUTOLAUF.ps1` | PowerShell-Autolauf |
| `Config/ext004_fastapi_backend_v1.json` | Konfiguration |
| `ALIN_Neustart_Core/25_API_Backend/alin_api_main.py` | Erzeugte FastAPI-Anwendung |
| `ALIN_Neustart_Core/25_API_Backend/openapi_schema.json` | Erzeugtes OpenAPI-Schema |
| `ALIN_Neustart_Core/25_API_Backend/start_api.ps1` | Erzeugtes Start-Skript |

## Schnellstart
```powershell
# API-Server manuell starten
& ALIN_Neustart_Core\25_API_Backend\start_api.ps1
# Oder direkt:
cd ALIN_Neustart_Core\25_API_Backend
I:\KI_Legal_Project\Tools\Python312\python.exe alin_api_main.py
```

## Endpunkte
- **Docs**: http://127.0.0.1:8744/docs
- **OpenAPI JSON**: http://127.0.0.1:8744/openapi.json

## Testlauf
Der Autolauf führt einen Smoke-Test durch:
1. Startet uvicorn im Hintergrund
2. Ruft `/health`, `/terminologie`, `/` ab
3. Stoppt den Server

## Änderungshistorie
| Datum | Autor | Änderung |
|-------|-------|----------|
| 2026-05-18 | ALIN-Agent | Erste Version |
