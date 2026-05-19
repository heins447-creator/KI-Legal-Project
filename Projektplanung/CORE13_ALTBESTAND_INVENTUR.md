# CORE-13 – Automatische Altbestandsinventur und Vor-Klassifikation

## Ziel

Inventarisierung des gesamten Altbestands unter `I:\KI_Legal_Project` mit vorläufiger Klassifikation jeder Datei. Das Modul arbeitet **ausschließlich read-only** – es werden keine Dateien verschoben, gelöscht, umbenannt oder verändert.

## Rote Linie

- `produktiv_freigegeben = false`
- `nur_musterdaten = true`
- `echte_daten_erlaubt = false`

## Klassifikationen (10 Klassen)

| Klasse | Bedeutung |
|--------|-----------|
| AKTIV | Wird vom aktuellen System referenziert |
| ERSETZT | Durch neueren Baustein ersetzt |
| ALT_ABER_NOCH_RELEVANT | Alt, aber noch referenziert |
| TESTREST | Test-/Smoketest-Überbleibsel |
| LAUFZEIT_ARTEFAKT | `.tmp`, `.pyc`, `__pycache__`, Logs |
| LOG_BERICHT | Berichte, Protokolle, Audit-Trails |
| CONFIG_LOKAL | Lokale Konfigurationen, `.env` |
| DUBLETTE | SHA-256-Hash identisch mit anderer Datei |
| UNGEKLÄRT | Keine eindeutige Zuordnung möglich |
| SPERREN | Sicherheitsrelevante Auffälligkeit |

## Sperrkategorien

- `DB_ÄNDERUNG` – Datei ändert Datenbankschema
- `ORIGINAL_ÄNDERUNG` – Datei verändert Originaldokumente
- `INTERNET` – Datei greift auf Internet zu
- `API` – Datei nutzt externe APIs
- `CLOUD` – Datei nutzt Cloud-Dienste
- `DEEPL` – Datei nutzt DeepL
- `ARGOS` – Datei nutzt Argos Translate
- `PRODUKTIVFREIGABE` – Datei beansprucht Produktivfreigabe
- `ECHTE_DATEN` – Datei verarbeitet echte Mandantendaten

## Ausschlusskriterien (nicht inventarisiert)

- `.git`, `__pycache__`, `.venv`, `node_modules`
- `Windows_App/Logs` (Laufzeitartefakte)
- `.tmp`, `.pyc`, `.pyo`, `.class`

## Registerabgleich

Abgleich gegen 8 JSON-Register unter `ALIN_Neustart_Core/01_Register/`:

1. `modulregister.json`
2. `toolregister.json`
3. `ressourcenregister.json`
4. `skillregister.json`
5. `quellen_adapter_register.json`
6. `schnittstellenregister.json`
7. `lizenzregister.json`
8. `update_register.json`

## Dublettenerkennung

- SHA-256-Hash pro Datei (max. 100 MB, größere Dateien werden mit Hinweis übersprungen)
- Dubletten werden in `CORE13_dubletten.csv` dokumentiert

## Ausgabedateien

| Datei | Ordner | Inhalt |
|-------|--------|--------|
| `CORE13_altbestand_inventur.json` | `07_Bestandsaufnahme_Altbestand` | Vollständiges Inventar (JSON) |
| `CORE13_altbestand_inventur.csv` | `07_Bestandsaufnahme_Altbestand` | Vollständiges Inventar (CSV) |
| `CORE13_klassifikation.csv` | `07_Bestandsaufnahme_Altbestand` | Klassifikationsübersicht |
| `CORE13_dubletten.csv` | `07_Bestandsaufnahme_Altbestand` | Dublettenliste |
| `CORE13_sperrhinweise.csv` | `07_Bestandsaufnahme_Altbestand` | Sicherheitswarnungen |
| `CORE13_ALTBESTAND_INVENTUR_BERICHT.txt` | `Reports` | Menschenlesbarer Bericht |

## Dateien

- **Runner:** `Scripts/python_runner/core13_altbestand_inventur.py`
- **Check:** `Scripts/python_runner/check_core13_altbestand_inventur.py`
- **Starter:** `Scripts/CORE13_ALTBESTAND_INVENTUR_AUTOLAUF.ps1`
- **Doku:** `Projektplanung/CORE13_ALTBESTAND_INVENTUR.md`

## Lieferpflicht-Erfüllung

| # | Lieferpflicht | Status |
|---|---------------|--------|
| 1 | Migration (DB nicht betroffen) | N/A |
| 2 | Python-Läufer | `core13_altbestand_inventur.py` |
| 3 | Prüfdatei | `check_core13_altbestand_inventur.py` |
| 4 | PowerShell-Starter | `CORE13_ALTBESTAND_INVENTUR_AUTOLAUF.ps1` |
| 5 | Konfiguration | Inline-Konstanten (keine externe Config nötig) |
| 6 | Dokumentation | Diese Datei |
| 7 | Testlauf | Via PowerShell-Starter |
| 8 | Bericht | `CORE13_ALTBESTAND_INVENTUR_BERICHT.txt` |
| 9 | Git-Status vor/nach | Im PowerShell-Starter enthalten |
| 10 | Git-Commit | Nur bei erfolgreichem Build + Prüfung |

## Abhängigkeiten

- Keine externen Abhängigkeiten (nur Python-Standardbibliothek)
- Kein Internetzugriff
- Keine Datenbankänderungen

## Autor

Automatisch generiert im Rahmen des ALIN-Neustart-CORE-Programms.
