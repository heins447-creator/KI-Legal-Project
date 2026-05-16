# Zwischenabnahme UI03-1b bis UI03-1f

**Zeitpunkt:** 2026-05-16T22:35:00+02:00  
**Prüfer:** Statische Code-Analyse (Agent)  
**Umfang:** UI03-1b, UI03-1c, UI03-1d, UI03-1e, UI03-1f  
**Methode:** Vollständige Quellcode-Lektüre aller Python-Runner, Check-Dateien, Configs und Dokumentation

---

## 1. Review-Punkt: UI03-1d – Seitenfreigabe korrekt?

**Status:** ✓ BESTANDEN

| Aspekt | Befund |
|--------|--------|
| Freigabe-Optionen | 4 Radio-Button-Optionen definiert (`FREIGABE_OPTIONEN`, Zeile 65–70) |
| freigegeben | „OCR qualitativ ausreichend – freigegeben für Übersetzung" |
| neu_ocr | „OCR mangelhaft – Neu-OCR erforderlich" |
| ausschliessen | „Seite nicht übersetzungsrelevant – ausschließen" |
| zurueckstellen | „Anwalt prüft – Freigabe zurückstellen" |
| Pro-Seite-Freitext | `textarea` mit `name="anmerkung_{s_id}"` (Zeile 141) |
| Keine Vorauswahl | Kein `checked`-Attribut gesetzt – Anwalt muss aktiv entscheiden |
| Gesamtübersicht | Statistik-Panel mit Dokument-/Seiten-Zählern (Zeile 146–156) |

**Grenzen:** Alle 6 Grenzen deklariert (Keine Originaländerung, keine neue OCR, keine endgültige Übersetzung, keine DB-Änderung, kein Internet/Cloud, keine Registeränderung).

---

## 2. Review-Punkt: UI03-1e – Sauberer Übersetzungsauftrag?

**Status:** ✓ BESTANDEN

| Aspekt | Befund |
|--------|--------|
| Auftrags-ID | Zeitstempel-basiert: `UA_{akten_id}_{YYYYMMDDhhmmss}` (Zeile 95) |
| Status | `"vorbereitet"` (Zeile 120) |
| Parkgrund | `"Argos-Modelle nicht verfügbar – keine echte Übersetzung gestartet"` (Zeile 121) |
| Seiten-Array | Vollständig mit `seiten_id`, `dokument_id`, `seite_nummer`, `sprache`, `ocr_text_vorschau`, `kategorie`, `urspruenglicher_status`, `anmerkung` (Zeile 102–114) |
| Initiale Kategorisierung | `initiale_kategorie()` leitet aus `ocr_verwertbarkeit_status` und `uebersetzung_status` ab (Zeile 77–88) |
| 5 Kategorien | `freigegeben`, `neu_ocr`, `ausgeschlossen`, `zurueckgestellt`, `wartet` (Zeile 69–75) |
| JSON-Ausgabe | Sauberes `json.dumps(auftrag, indent=2, ensure_ascii=False)` (Zeile 345) |
| Status-JSON | Detaillierte Aufschlüsselung pro Kategorie (Zeile 348–380) |

**Kettenkonsistenz:** UI03-1e liest die Akte (nicht UI03-1d-Output), da UI03-1d noch keine Persistenzschicht hat. Die initiale Kategorisierung ist semantisch korrekt und bildet einen sauberen Übersetzungsauftrag.

---

## 3. Review-Punkt: UI03-1f – Auftrag korrekt als geparkt angezeigt?

**Status:** ✓ BESTANDEN

| Aspekt | Befund |
|--------|--------|
| Auftragssuche | `suche_geparkte_auftraege()` sucht in UI03-1e-Schreibbereich via `rglob("UI03_1e_UEBERGABE_FREIGABE.json")` (Zeile 68–70) |
| Filter | Nur Einträge mit `status == "vorbereitet"` (Zeile 73) |
| GEPARKT-Badge | `<span class="badge badge-warn">GEPARKT</span>` pro Auftrag (Zeile 146) |
| Parkgrund-Box | Hervorgehobene Anzeige des Parkgrunds (Zeile 149–150) |
| Mini-Statistik | 6 Kategorien pro Auftrag (Seiten, Freigegeben, Neu-OCR, Ausgeschlossen, Zurückgestellt, Wartet) (Zeile 152–158) |
| Argos-Banner | Grün/Rot je nach Verfügbarkeit (Zeile 128–131) |
| Wiederaufnahme-Button | `disabled={not argos_status['verfuegbar']}` (Zeile 161) |
| Gesamtstatus | „WARTET AUF LOKALE MODELLE" oder „BEREIT FÜR WIEDERAUFNAHME" (Zeile 248) |

---

## 4. Review-Punkt: Argos=False konservativ behandelt?

**Status:** ✓ BESTANDEN – alle Module

| Modul | Argos-Prüfung | Verhalten bei Argos=False |
|-------|---------------|---------------------------|
| **UI03-1b** | `installiert` + `>=2` Paare → freigegeben, sonst `gesperrt` (Zeile 123–138) | Status „gesperrt", Deutsche Arbeitsansicht = Orientierungsübersetzung |
| **UI03-1c** | `installiert` + `vorhanden_count>0` → `teilweise`, nie `freigegeben` (Zeile 127–135) | `ocr_als_basis=True`, DEEPL gesperrt, Empfohlene Vorgehensweise = OCR als Basis |
| **UI03-1d** | Keine Argos-Prüfung (reine Freigabe-Markierung) | Keine Übersetzung gestartet |
| **UI03-1e** | Toolregister + Ressourcenregister, `installiert` + `ARGOS_*` Paare (Zeile 316–328) | `status="vorbereitet"`, `parkgrund` gesetzt, Park-Banner „GEPARKT" |
| **UI03-1f** | Detaillierte Prüfung mit Fehlergründen (Zeile 93–115) | Button disabled, Status „WARTET AUF LOKALE MODELLE" |

**Kritisch:** Kein Modul startet eine Übersetzung oder täuscht Verfügbarkeit vor. UI03-1e setzt explizit `parkgrund` und `status="vorbereitet"`.

---

## 5. Review-Punkt: Keine echte Übersetzung vorgetäuscht?

**Status:** ✓ BESTANDEN – alle Module

| Modul | Formulierung | Ort |
|-------|-------------|-----|
| **UI03-1b** | „Nicht endgültig – anwaltlich zu prüfen" | `deutsche_arbeitsansicht.hinweis` (Zeile 157) |
| **UI03-1c** | „Orientierungsübersetzung (nicht endgültig)" | HTML-Spalte 3 (Zeile 423) |
| **UI03-1d** | „Orientierungsübersetzung" (nur 400 Zeichen Vorschau) | HTML-Vorschau (Zeile 131) |
| **UI03-1e** | „Argos-Modelle nicht verfügbar – keine echte Übersetzung gestartet" | `parkgrund` (Zeile 121) |
| **UI03-1f** | „Keine echte Übersetzung (nur vorbereiten/parken)" | Grenzen-Panel (Zeile 263) |

Alle Module deklarieren in ihren Grenzen explizit:
- `keine_endgueltige_uebersetzung: True`
- `keine_echte_uebersetzung: True` (UI03-1e/1f)

---

## Zusätzliche Prüfungen

### CORE-11-Konformität
| Prüfung | Status |
|---------|--------|
| Register nur lesend | ✓ Alle Module nutzen `load_register()` ohne Schreibzugriff |
| Korrekte IDs | ✓ `TESSERACT`, `ARGOS_TRANSLATE`, `DEEPL_API`, `resource_id` |
| Keine Hartverdrahtung | ✓ Keine feste sv/de-Annahme in UI03-1b/1c |

### Schreibbereiche (getrennt pro Modul)
| Modul | Schreibbereich |
|-------|---------------|
| UI03-1b | `Agentensteuerung\UI03_Mandantenakte\21_OCR_Uebersetzungskontrolle_UI03_1b\` |
| UI03-1c | `Agentensteuerung\UI03_Mandantenakte\22_Uebersetzungsarbeitsplatz_UI03_1c\` |
| UI03-1d | `Agentensteuerung\UI03_Mandantenakte\23_OCR_Freigabeablauf_UI03_1d\` |
| UI03-1e | `Agentensteuerung\UI03_Mandantenakte\24_Uebergabe_Freigabe_UI03_1e\` |
| UI03-1f | `Agentensteuerung\UI03_Mandantenakte\25_Geparkte_Auftraege_UI03_1f\` |

### Lieferpflicht je Programmierauftrag (AGENTS.md)
| Pflicht | UI03-1b | UI03-1c | UI03-1d | UI03-1e | UI03-1f |
|---------|---------|---------|---------|---------|---------|
| Python-Läufer | ✓ | ✓ | ✓ | ✓ | ✓ |
| Prüfdatei | ✓ | ✓ | ✓ | ✓ | ✓ |
| PowerShell-Starter | ✓ | ✓ | ✓ | ✓ | ✓ |
| Config | ✓ | ✓ | ✓ | ✓ | ✓ |
| Dokumentation | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Befunde

### Keine Blocker
Alle 5 Review-Punkte sind erfüllt. Die Kette UI03-1b → UI03-1c → UI03-1d → UI03-1e → UI03-1f ist konsistent.

### Hinweise (keine Mängel)
1. **UI03-1d Persistenz:** Die Freigabe-Entscheidungen werden aktuell nur als Radio-Buttons im HTML dargestellt, nicht persistiert. Das ist korrekt für ein reines Interface-Modul – eine Persistenzschicht wäre ein separater Baustein.
2. **UI03-1e → UI03-1d Kopplung:** UI03-1e liest die Akte direkt (nicht UI03-1d-Output), da UI03-1d noch keine Persistenz hat. Die initiale Kategorisierung über `ocr_verwertbarkeit_status` ist semantisch korrekt als Brücke.
3. **UI03-1f Auftragssuche:** `rglob()` im UI03-1e-Schreibbereich ist robust gegen zukünftige Unterverzeichnisse.

---

## Gesamturteil

**ZWISCHENABNAHME BESTANDEN**

Alle Module UI03-1b bis UI03-1f erfüllen die Review-Kriterien:
- ✓ Seitenfreigabe korrekt implementiert (4 Optionen + Freitext)
- ✓ Sauberer Übersetzungsauftrag mit Parkstatus
- ✓ Geparkte Aufträge korrekt angezeigt mit Argos-Abhängigkeit
- ✓ Argos=False konservativ überall behandelt
- ✓ Keine echte Übersetzung wird vorgetäuscht
- ✓ CORE-11-konform (nur lesende Registerzugriffe)
- ✓ Alle AGENTS.md-Lieferpflichten erfüllt

**Empfohlener nächster Schritt:** KM21b (lokale Argos-Modelle bereitstellen) oder UI03-1g (kombinierte Gesamtansicht).
