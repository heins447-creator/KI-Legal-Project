# EXT-006 – Semantische Suche API-Endpunkt

## Ziel
Erweiterung des FastAPI-Backends um einen `/suche` Endpunkt, der semantische Suche ueber DuckDB-Vektoren ermoeglicht. TF-IDF-basiert, offline-faehig.

## Abhaengigkeiten
- EXT-004 (FastAPI-Backend)
- EXT-005 (Semantische Suche / Vektor-Embeddings)

## Sicherheitsregeln
- **Cloud verboten**: Kein externer Suchdienst.
- **Offline**: Alle Berechnungen lokal.
- **Nur localhost**: API bindet an 127.0.0.1:8745.
- **Keine echten Daten**: Suche arbeitet nur mit synthetischen Testdaten.

## API-Endpunkte
| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/` | GET | API-Info |
| `/health` | GET | Healthcheck |
| `/suche?q=...` | GET | Semantische Suche mit TF-IDF |

### Beispiel
```bash
curl "http://127.0.0.1:8745/suche?q=Verordnung%20Europaeische%20Union"
```

## Architektur
```
Client (lokal)
    |
    v
FastAPI (127.0.0.1:8745)
    |-- /suche
    |   |-- Laedt alle Texte aus DuckDB
    |   |-- Berechnet TF-IDF on-the-fly
    |   |-- Cosinus-Aehnlichkeit Query vs. Dokumente
    |   |-- Gibt Top-5 Ergebnisse zurueck
    |
    v
DuckDB (alin_local.duckdb)
```

## Dateien
| Datei | Zweck |
|-------|-------|
| `Scripts/python_runner/ext006_semantische_suche_api.py` | Runner: erzeugt erweiterte API, Start-Skript, Smoke-Test |
| `Scripts/python_runner/check_ext006_semantische_suche_api.py` | Check: prueft FastAPI, NumPy, DuckDB, Embeddings |
| `Scripts/EXT006_SEMANTISCHE_SUCHE_API_AUTOLAUF.ps1` | PowerShell-Autolauf |
| `Config/ext006_semantische_suche_api_v1.json` | Konfiguration |
| `Projektplanung/EXT006_SEMANTISCHE_SUCHE_API.md` | Diese Dokumentation |
| `ALIN_Neustart_Core/25_API_Backend/alin_api_erweitert.py` | Erzeugte FastAPI-Anwendung mit /suche |
| `ALIN_Neustart_Core/25_API_Backend/start_api_erweitert.ps1` | Erzeugtes Start-Skript |

## Testlauf
Der Autolauf fuehrt folgende Schritte durch:
1. py_compile auf Runner und Check
2. Check prueft Voraussetzungen
3. Runner erzeugt erweiterte API mit /suche Endpunkt
4. Smoke-Test: Startet Server, testet /health und /suche
5. Bericht wird geschrieben

## Aenderungshistorie
| Datum | Autor | Aenderung |
|-------|-------|----------|
| 2026-05-18 | ALIN-Agent | Erste Version |
