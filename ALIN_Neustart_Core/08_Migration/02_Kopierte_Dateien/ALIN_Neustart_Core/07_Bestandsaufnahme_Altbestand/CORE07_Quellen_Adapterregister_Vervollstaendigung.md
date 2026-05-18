# CORE-07 – Quellen- und Adapterregister Vervollständigung

## Zweck

Dieser Baustein vervollständigt das zentrale Quellen- und Adapterregister (`quellen_adapter_register.json`) im ALIN Neustart Core.

Er erfasst alle identifizierten Quellenkandidaten aus der Projektplanung und ordnet ihnen Adapter, Statuswerte und Warnungen zu.

## Grenzen

Dieser Baustein führt keine freie Internetrecherche aus. Er lädt keine Massendaten. Er verarbeitet keine echten Mandantendaten. Er erstellt keine Türschwellenmaske, keine endgültige Übersetzung und keine rechtliche Endbewertung.

Keine Quelle wird auf `darf_verwendet_werden: true` gesetzt, bevor der Quellenbetreuer-Fachanwaltsraster nicht geprüft hat.

## Durchgeführte Arbeiten

1. **Quellen-Adapterregister befüllt**
   - Vorher: 1 Eintrag (EUR_LEX)
   - Nachher: 15 Einträge
   - Zuwachs: 14 Einträge

2. **Quellen nach Kategorien**
   - **EU-Quellen (7):** EUR-Lex, ECLI, EU-Justizportal, IATE, EuroVoc, DGT Translation Memory, CCBE
   - **Deutsche Quellen (3):** Gesetze-im-Internet, BGH, BAG
   - **Schwedische Quellen (5):** Sveriges Rikes Lag, Domstolsverket, Advokatsamfundet, Arbetsdomstolen, Medlingsinstitutet

3. **Adapter zugeordnet**
   - Jede Quelle erhielt einen eindeutigen Adapter-Namen (z. B. `EU_R_Lex_Adapter`, `SE_Arbetsdomstolen_Adapter`)

4. **Status gesetzt**
   - `online_status`: `verfuegbar` (für alle bekannten Quellen)
   - `offline_cache_status`: `nicht_vorgesehen` (kein Massendownload)
   - `dry_run_status`: `ungetestet`
   - `darf_verwendet_werden`: `false` (gesperrt bis Quellenbetreuer-Prüfung)

5. **Warnungen hinterlegt**
   - Jede Quelle enthält Warnhinweise zur Notwendigkeit des Quellenbetreuer-Fachanwaltsrasters
   - Schwedische Quellen enthalten zusätzlichen Hinweis auf Sprachpaket `sv_de_arbeitsrecht_se`

6. **Altbestand aktualisiert**
   - `altbestand_schnittstellen.json` erhielt aktualisierten Timestamp

## Registerstruktur

Das Register enthält pro Eintrag:
- `quelle_id` – Eindeutige Kennung (z. B. `EUR_LEX`, `SE_ARBETSDOMSTOLEN`)
- `quellentyp` – `gesetz`, `verordnung`, `gerichtsentscheidung`, `fachliteratur`, `datenbank`, `sonstiges`
- `land` – `EU`, `DE`, `SE`
- `rechtsgebiet` – Zugeordnetes Rechtsgebiet
- `sprache` – `de`, `sv`, `mehrsprachig`
- `adapter` – Name des zuständigen Adapters
- `online_status` – `verfuegbar`, `eingeschraenkt`, `nicht_verfuegbar`, `unbekannt`
- `offline_cache_status` – `aktuell`, `veraltet`, `fehlt`, `nicht_vorgesehen`
- `dry_run_status` – `moeglich`, `nicht_moeglich`, `ungetestet`
- `letzter_healthcheck` – ISO-8601-Zeitstempel
- `darf_verwendet_werden` – Boolean (aktuell `false` für alle)
- `warnungen` – Array von Warnstrings

## Abgleich mit anderen Registern

- **Ressourcenregister:** Quellen-IDs sind als `quellenregister`/`adapter`-Typen im Ressourcenregister verzeichnet (z. B. `QUELLEN_EU_SE`)
- **Toolregister:** Keine direkte Verknüpfung (Adapter sind logische Komponenten, keine Tools)
- **Update-Register:** Keine direkte Verknüpfung (Quellen-Updates werden separat überwacht)
- **Lizenzregister:** Keine direkte Verknüpfung (Quellen-Nutzungsbedingungen werden separat geprüft)

## Nächster Schritt

- CORE-08 – Skillregister vervollständigen
- Oder: Quellenbetreuer-Fachanwaltsraster für Arbeitsrecht Schweden aktivieren

## Technische Pflicht

- Python-Läufer: `Scripts\alin_core07_quellen_adapterregister_befuellen.py`
- Python-Prüfdatei: `Scripts\alin_core07_pruefung.py`
- PowerShell-Starter: `Scripts\Run_CORE07_Quellen_Adapterregister.ps1`
- Bericht: `Reports\ALIN_CORE07_QUELLEN_ADAPTERREGISTER_BERICHT.txt`
- Prüfbericht: `Reports\ALIN_CORE07_PRUEFBERICHT.txt`
