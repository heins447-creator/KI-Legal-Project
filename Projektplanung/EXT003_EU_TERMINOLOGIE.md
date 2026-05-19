# EXT-003 – EU-Terminologiepakete für Rechtssicherheit

## Zweck

Aufbau eines lokalen EU-Terminologie-Registers für rechtssichere Übersetzungen. Das Register enthält:

- EuroVoc-Konzepte (EU-Thesaurus)
- EU-Verordnungsbegriffe
- Validierbare Übersetzungsäquivalente
- Kontextinformationen und Quellennachweise

## Sicherheitsgrenzen

- **Kein Cloud-Übersetzungsdienst** (DeepL, Google Translate verboten)
- **Keine Online-Terminologie-Abfragen**
- **EU-Daten nur aus lokalen Quellen**
- **Keine echten Mandantendaten** für Validierung

## Inhalt

### Beispiel-Einträge (synthetisch)

| Begriff | Sprache | Kategorie | Quelle | Äquivalente |
|---------|---------|-----------|--------|-------------|
| Verordnung (EU) | de | verordnung | Art. 288 AEUV | en: Regulation (EU), fr: Règlement (UE) |
| Richtlinie (EU) | de | richtlinie | Art. 288 AEUV | en: Directive (EU), fr: Directive (UE) |
| AEUV | de | vertrag | AEUV | en: TFEU, fr: TFUE |
| Mandatsgeheimnis | de | berufsrecht | BRAO § 43a | en: professional secrecy, fr: secret professionnel |

### Manifest

Das Terminologie-Manifest (`ALIN_Neustart_Core/18_Terminologie/EU_TERMINOLOGIE_MANIFEST.json`) dokumentiert:
- Anzahl der Einträge
- Verfügbare Kategorien
- Abgedeckte Sprachen
- Quellennachweise
- Sicherheitsstatus

## Datenbank-Integration

Einträge werden in die DuckDB-Tabelle `alin_ext001.terminologie` eingefügt und sind über:
- Begriffssuche
- Kategorie-Filter
- Sprachfilter
- Validierungsstatus

abfragbar.

## Ausgaben

- `Scripts/python_runner/ext003_eu_terminologie.py`
- `Scripts/python_runner/check_ext003_eu_terminologie.py`
- `Scripts/EXT003_EU_TERMINOLOGIE_AUTOLAUF.ps1`
- `Config/ext003_eu_terminologie_v1.json`
- `ALIN_Neustart_Core/18_Terminologie/EU_TERMINOLOGIE_MANIFEST.json`
- `ALIN_Neustart_Core/Reports/EXT003_EU_TERMINOLOGIE_BERICHT.txt`

## Nächste Stufe

- EXT-004: FastAPI-Backend (nutzt Terminologie-Register)