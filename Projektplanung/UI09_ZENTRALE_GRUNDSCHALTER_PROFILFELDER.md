# UI09 – Zentrale Grundschalter und Profilfelder

**Modul-ID:** UI09  
**Version:** 1.0.0  
**Status:** Entwurf – außerhalb Demo-Betriebsstrecke  
**Letzte Änderung:** 2026-05-17  
**Autor:** ALIN Build-System  

---

## 1. Zweck

UI09 schafft eine **zentrale Profil- und Schalterebene** für alle ALIN-Module. Bisher waren Entscheidungen wie Sprache, Aktenbezug, Sicherheitsstatus und Freigaben in jedem Einzelmodul verteilt. UI09 konsolidiert diese in ein gemeinsames, versioniertes Profilsystem.

### Motivation aus UI08c

UI08c zeigte, dass folgende Felder nicht mehr verstreut liegen sollten:

- Dokumentensprache, Anwaltssprache, Mandantensprache
- Aktenbezug, Rechtsraum, Sachgebiet
- Sicherheitsstatus
- Freigabestatus (Vorzimmer, Anwalt, Schlusskontrolle)
- Ressourcenpakete (OCR, Übersetzung)
- Betriebsmodus, Online-/Offline-Status
- Mandanten-ID

---

## 2. Rote Linie

| Regel | Wert |
|-------|------|
| `produktiv_freigegeben` | `false` |
| `nur_musterdaten` | `true` |
| `echte_daten_erlaubt` | `false` |
| Änderungen an UI03–UI07b | **Verboten** (Freeze) |
| Datenbank-Änderung | **Nein** (nur lesend) |

---

## 3. Profilfelder (15 Stück)

| Feld-ID | Name | Typ | Pflicht | Default | Nutzer |
|---------|------|-----|---------|---------|--------|
| `sprache_dokument` | Dokumentensprache | string | Ja | `unbekannt` | Posteingang, OCR, Übersetzung, Agent |
| `sprache_anwalt` | Anwaltssprache | string | Ja | `de` | Anwalt, Übersetzung, UI05 |
| `sprache_mandant` | Mandantensprache | string | Nein | `de` | Posteingang, Vorzimmer, Anwalt |
| `rechtsraum` | Rechtsraum | string | Ja | `unbekannt` | Posteingang, Anwalt, Agent, Quellen |
| `akten_id` | Aktenbezug | string | Ja | `null` | Posteingang, Mandantenakte, Agent |
| `sicherheitsstatus` | Sicherheitsstatus | string | Ja | `unbekannt` | Posteingang, Vorzimmer, Anwalt |
| `freigabe_vorzimmer` | Vorzimmer-Freigabe | boolean | Ja | `false` | Vorzimmer, Anwalt, Weiche |
| `freigabe_anwalt` | Anwalt-Freigabe | boolean | Ja | `false` | Anwalt, Mandantenakte, Agent |
| `freigabe_schlusskontrolle` | Schlusskontrolle-Freigabe | boolean | Ja | `false` | Schlusskontrolle, Mandantenakte |
| `ressourcenpaket_ocr` | OCR-Ressourcenpaket | array | Nein | `["deu", "eng"]` | OCR, Posteingang |
| `ressourcenpaket_uebersetzung` | Übersetzungs-Ressourcenpaket | array | Nein | `["de-en", "en-de"]` | Übersetzung, Agent |
| `betriebsmodus` | Betriebsmodus | string | Ja | `demo` | Alle Module |
| `online_status` | Online-/Offline-Modus | boolean | Ja | `false` | Alle Module, Update |
| `mandant_id` | Mandanten-ID | string | Ja | `null` | Posteingang, Mandantenakte, Anwalt |
| `sachgebiet` | Sachgebiet | string | Nein | `unbekannt` | Anwalt, Agent, Quellen |

---

## 4. Grundschalter (8 Stück)

| ID | Name | Default | Änderbar durch | Wirkt auf |
|----|------|---------|----------------|-----------|
| GS01 | Automatische Spracherkennung | `true` | Admin, Vorzimmer | Posteingang, OCR, Agent |
| GS02 | Automatische Aktenzuordnung | `false` | Admin, Vorzimmer | Posteingang, Mandantenakte |
| GS03 | Sicherheitsgate aktiv | `true` | Admin | Posteingang, Sicherheitsgate |
| GS04 | Agenten-Autostart | `true` | Admin, Anwalt | Agent, Anwalt |
| GS05 | Offline-Cache aktiv | `true` | Admin | Cache, Update, Alle Module |
| GS06 | Protokollierung aktiv | `true` | Admin | Audit, Alle Module |
| GS07 | Musterdaten-Modus | `true` | Admin | Alle Module |
| GS08 | Automatische Schlusskontrolle | `false` | Admin, Vorzimmer | Schlusskontrolle, Mandantenakte |

---

## 5. Validierungsregeln (5 Stück)

| Regel | Beschreibung | Schwere |
|-------|--------------|---------|
| VAL01 | Produktivmodus erfordert Online oder Offline-Cache | KRITISCH |
| VAL02 | Gesperrtes Dokument darf keine Freigaben haben | KRITISCH |
| VAL03 | Produktivmodus erfordert Akten-ID | HOCH |
| VAL04 | Mandanten-ID muss immer gesetzt sein | KRITISCH |
| VAL05 | Musterdaten-Modus aus erfordert Produktivmodus | HOCH |

---

## 6. Architektur

### 6.1 Eingabe
- Config: `Config/ui09_zentrale_grundschalter_profilfelder_v1.json`
- Sperrregister
- UI08c Sanierungsstatus (optional)

### 6.2 Verarbeitung
1. Sperrregister-Prüfung
2. Profilfelder aus Config laden
3. Grundschalter aus Config laden
4. Validierungsregeln anwenden
5. HTML/JSON/Bericht erzeugen

### 6.3 Ausgabe
- `Windows_App/Logs/UI09_PROFILUEBERSICHT.html` – Visuelle Profilübersicht
- `Windows_App/Logs/UI09_ZENTRALES_PROFIL.json` – Maschinenlesbares Profil
- `Windows_App/Logs/UI09_GRUNDSCHALTER.json` – Maschinenlesbare Schalter
- `Windows_App/Logs/UI09_ZENTRALE_GRUNDSCHALTER_BERICHT.txt` – Textbericht

---

## 7. Lieferpflichten-Checkliste

- [x] Migration (keine DB-Änderung)
- [x] Python-Runner: `Scripts/python_runner/ui09_zentrale_grundschalter_profilfelder.py`
- [x] Prüfdatei: `Scripts/python_runner/check_ui09_zentrale_grundschalter_profilfelder.py`
- [x] PowerShell-Starter: `Scripts/UI09_ZENTRALE_GRUNDSCHALTER_PROFILFELDER_AUTOLAUF.ps1`
- [x] Konfiguration: `Config/ui09_zentrale_grundschalter_profilfelder_v1.json`
- [x] Dokumentation: `Projektplanung/UI09_ZENTRALE_GRUNDSCHALTER_PROFILFELDER.md`
- [ ] Testlauf (wird manuell durchgeführt)
- [ ] Bericht unter `Windows_App/Logs`
- [ ] Git-Status vor und nach Änderung
- [ ] Git-Commit bei erfolgreicher Prüfung

---

## 8. Abhängigkeiten

| Modul | Art |
|-------|-----|
| UI08c | Liest Sanierungsstatus (optional) |
| Ressourcenregister | Prüft verfügbare Pakete |
| Sperrregister | Prüft UI09-Sperre |

---

## 9. Freeze-Kompatibilität

UI09 ist **außerhalb des UI07b-Gesamtfreeze**. Es definiert ein neues zentrales Profil, das zukünftige Module nutzen können. Die eingefrorene Strecke UI03–UI07b bleibt unverändert.

---

## 10. Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0.0 | 2026-05-17 | Erstellerstellung mit 15 Profilfeldern, 8 Grundschaltern, 5 Validierungsregeln |
