# CORE-08 – Skillregister Vervollständigung

## Zweck

Dieser Baustein vervollständigt das zentrale Skillregister (`skillregister.json`) im ALIN Neustart Core.

Er erfasst alle Skills für den Posteingang, die Dokument-Voranalyse, das Routing, OCR/Fundstellen, Sprache/Übersetzung und Kanzlei-Arbeit.

## Grenzen

Dieser Baustein führt keine freie Internetrecherche aus. Er lädt keine Massendaten. Er verarbeitet keine echten Mandantendaten. Er erstellt keine Türschwellenmaske, keine endgültige Übersetzung und keine rechtliche Endbewertung.

Kein Skill darf `darf_bewerten`, `darf_beweiswuerdigen`, `darf_rechtsbewertung`, `darf_stammdaten_aendern` oder `darf_originale_veraendern` auf `true` gesetzt haben.

## Durchgeführte Arbeiten

1. **Skillregister befüllt**
   - Vorher: 5 Einträge (SKILL_OCR, SKILL_DOKUMENTART, SKILL_SACHVERHALTSBEZUG, SKILL_SPRACHE, SKILL_QUELLEN)
   - Nachher: 30 Einträge
   - Zuwachs: 25 Einträge

2. **Bestehende Skills aktualisiert**
   - Alle 5 Altbestand-Skills erhielten zusätzliche Felder: `skillgruppe`, `verwendete_tools`, `benoetigte_ressourcen`, `benoetigte_quellen`, `offline_moeglich`, `online_erforderlich`, `status`, `pruefstatus`, `sicherheitsstufe`, `darf_rechtsbewertung`, `darf_stammdaten_aendern`, `darf_originale_veraendern`

3. **Neue Skills nach Gruppen**
   - **Eingang/Briefkasten (6):** Dateityp, Sicherheitsstatus, Passwortschutz, Signaturhinweis, Container/ZIP, Hash/Dublette
   - **Dokument-Voranalyse (7):** Aktenzeichen, Gerichtszeichen, Behördenzeichen, Absender, Beteiligte, Kontaktdaten, Fristverdacht
   - **Routing/Weiche (5):** Bestandsakte, Neumandat, Verwaltungspost, Sicherheitsproblem, Sekretariat/Anwalt
   - **OCR/Fundstellen (5):** Seitenstruktur, OCR-Qualität, Fundstellen, Unsicherheiten, Layoutbezug
   - **Sprache/Übersetzung (4):** Übersetzungsbedarf, Übersetzungsrichtung, Terminologiebedarf, Sprachprofil
   - **Kanzlei-Arbeit (4):** Wiedervorlage, Unterlagennachforderung, Aktenanlage, Rücklauf
   - **Quellen/Adapter (1):** Quellenbetreuung (bestehend)

4. **Verknüpfungen gesetzt**
   - Jeder Skill verweist auf verwendete Tools (TESSERACT, OLLAMA, ARGOS_TRANSLATE, PYTHON, PYMUPDF, PILLOW, SQLITE)
   - Jeder Skill verweist auf benötigte Ressourcen (OCR-Sprachpakete, Übersetzungsmodelle, Terminologie)
   - Jeder Skill verweist auf benötigte Quellen (IATE, DGT_TRANSLATION_MEMORY, EUR_LEX, ECLI, EUROVOC)

5. **Sicherheitsregeln eingehalten**
   - Alle 30 Skills: `darf_bewerten: false`
   - Alle 30 Skills: `darf_beweiswuerdigen: false`
   - Alle 30 Skills: `darf_rechtsbewertung: false`
   - Alle 30 Skills: `darf_stammdaten_aendern: false`
   - Alle 30 Skills: `darf_originale_veraendern: false`
   - Alle 30 Skills: `status: gesperrt`

6. **Altbestand aktualisiert**
   - `altbestand_schnittstellen.json` erhielt aktualisierten Timestamp

## Registerstruktur

Das Register enthält pro Eintrag:
- `skill_id` – Eindeutige Kennung (Pattern: `^[A-Z0-9_-]+$`)
- `skillname` – Lesbarer Name
- `skillgruppe` – Kategorie (z. B. `eingang_briefkasten`, `dokument_voranalyse`)
- `zweck` – Beschreibung
- `eingabe` – Was der Skill verarbeitet
- `ausgabe` – Was der Skill liefert
- `verwendete_tools` – Array von Tool-IDs
- `benoetigte_ressourcen` – Array von Resource-IDs
- `benoetigte_quellen` – Array von Quellen-IDs
- `modellabhaengigkeit` – `tesseract`, `ollama`, `argos_translate`, `keine`
- `offline_moeglich` – Boolean
- `online_erforderlich` – Boolean
- `fallback` – `manuell` oder Skill-ID
- `darf_bewerten`, `darf_beweiswuerdigen`, `darf_rechtsbewertung` – immer `false`
- `darf_stammdaten_aendern`, `darf_originale_veraendern` – immer `false`
- `status` – `gesperrt` (alle)
- `pruefstatus` – `ungeprueft`
- `teststatus` – `ungeprueft` / `testbar` / `geprueft` / `gesperrt`
- `sicherheitsstufe` – `normal`, `hoch`, `kritisch`
- `warnungen` – Array von Warnstrings

## Abgleich mit anderen Registern

- **Toolregister:** Alle verwendeten Tools sind im Toolregister verzeichnet
- **Ressourcenregister:** Alle benötigten Ressourcen sind im Ressourcenregister verzeichnet
- **Quellen-/Adapterregister:** Alle benötigten Quellen sind im Quellenregister verzeichnet
- **Modulregister:** Skills werden später von Modulen referenziert (noch nicht verknüpft)

## Nächster Schritt

- CORE-09 – Modulregister vervollständigen
- Oder: Quellenbetreuer-Fachanwaltsraster für Arbeitsrecht Schweden aktivieren

## Technische Pflicht

- Python-Läufer: `Scripts\alin_core08_skillregister_befuellen.py`
- Python-Prüfdatei: `Scripts\alin_core08_pruefung.py`
- PowerShell-Starter: `Scripts\Run_CORE08_Skillregister.ps1`
- Bericht: `Reports\ALIN_CORE08_SKILLREGISTER_BERICHT.txt`
- Prüfbericht: `Reports\ALIN_CORE08_PRUEFBERICHT.txt`
