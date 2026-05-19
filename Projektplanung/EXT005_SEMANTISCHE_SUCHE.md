# EXT-005 – Semantische Suche in Dokumenten

## Ziel
Lokale semantische Suche ueber Dokumenteninhalte mit TF-IDF-basierten Vektor-Embeddings. Vollstaendig offline-faehig, keine externen Modelle oder Cloud-Dienste.

## Abhaengigkeiten
- EXT-001 (DuckDB-Schema)
- EXT-002 (PaddleOCR / Layout-Analyse)
- EXT-004 (FastAPI-Backend)

## Sicherheitsregeln
- **Cloud verboten**: Kein Cloud-Embedding-Service.
- **Offline**: Embedding-Berechnung lokal und offline.
- **Keine echten Daten**: Keine echten Mandantendokumente fuer Indexierung.
- **NumPy-only**: Keine externen ML-Frameworks erforderlich.

## Technik
### TF-IDF Vektorisierung
1. **Tokenisierung**: Simple Wort-Split, Lowercasing, Satzzeichen-Entfernung
2. **Vokabular**: Alle eindeutigen Wörter aus dem Korpus
3. **TF**: Term-Frequenz normalisiert auf Dokumentenlaenge
4. **IDF**: Inverse Document-Frequenz (log(N/df))
5. **TF-IDF**: Elementweise Multiplikation TF * IDF
6. **L2-Normalisierung**: Vektoren auf Laenge 1 skaliert

### Speicherung
- Vektoren als `FLOAT[]` (DuckDB Array) in `alin_ext001.vektor_embeddings`
- Segment-Typ: `terminologie` oder `ocr`
- Modell: `tfidf_numpy_local`

## Dateien
| Datei | Zweck |
|-------|-------|
| `Scripts/python_runner/ext005_semantische_suche.py` | Runner: TF-IDF-Berechnung, Speicherung, Test-Suche |
| `Scripts/python_runner/check_ext005_semantische_suche.py` | Check: prueft NumPy, DuckDB, Tabellen |
| `Scripts/EXT005_SEMANTISCHE_SUCHE_AUTOLAUF.ps1` | PowerShell-Autolauf |
| `Config/ext005_semantische_suche_v1.json` | Konfiguration |
| `Projektplanung/EXT005_SEMANTISCHE_SUCHE.md` | Diese Dokumentation |

## Testlauf
Der Autolauf fuehrt folgende Schritte durch:
1. py_compile auf Runner und Check
2. Check prueft Voraussetzungen
3. Runner liest Terminologie + OCR, berechnet TF-IDF, speichert Vektoren
4. Semantische Test-Suche: Query "Verordnung Europaeische Union"
5. Bericht wird geschrieben

## API-Integration
Die semantische Suche wird in EXT-006 ueber FastAPI-Endpunkt `/suche` verfuegbar gemacht.

## Aenderungshistorie
| Datum | Autor | Aenderung |
|-------|-------|----------|
| 2026-05-18 | ALIN-Agent | Erste Version |
