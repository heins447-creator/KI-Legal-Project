# Offene Fragen an den Anwalt

Diese Datei sammelt alle Fragen, die während der Entwicklung auftauchen und vom Anwalt beantwortet werden müssen, bevor weitergearbeitet werden kann.

## Anleitung für die KI

**Wann eine Frage hier eingetragen wird:**

- Die Aufgabe ist nicht eindeutig.
- Eine Architekturentscheidung wäre nötig, die die KI nicht selbst treffen darf.
- Eine rote Linie könnte berührt werden.
- Eine Information aus dem Arbeitsauftrag fehlt oder widerspricht sich.
- Die Wahl einer Bibliothek, eines Modells oder eines Parameters hat sicherheitsrelevante Folgen.

**Wie eine Frage eingetragen wird:**

Jede neue Frage wird **unten angehängt**, mit folgendem Aufbau:

```
## Frage [laufende Nummer]: [Kurztitel]

- Datum: JJJJ-MM-TT HH:MM
- Phase / Arbeitspaket: z. B. Phase 2, AP 2.3
- Dringlichkeit: normal | [DRINGEND]
- Stellt: [Name oder Kennung der KI]

**Worum es geht:**
[Klare, knappe Beschreibung in einfacher Sprache, was unklar ist.]

**Was bereits geprüft wurde:**
[Welche Quellen, Dokumente, Optionen die KI bereits angeschaut hat.]

**Antwortoptionen (falls möglich):**
- Option A: [Beschreibung] — Folge: [...]
- Option B: [Beschreibung] — Folge: [...]
- Option C: [...]

**Auswirkung auf die laufende Arbeit:**
[Was blockiert ist, was parallel weitergeht.]

**Antwort des Anwalts:**
[Wird vom Anwalt ausgefüllt. Erst danach gilt die Frage als beantwortet.]

**Beantwortet am:** [JJJJ-MM-TT — wird vom Anwalt eingetragen]
```

**Wie die KI mit beantworteten Fragen umgeht:**

- Antwort lesen.
- Falls Architekturentscheidung: in den Arbeitsauftrag (`ALIN_ARBEITSAUFTRAG_KI_ENTWICKLUNG.md`) übernehmen.
- Falls ADR-würdig: ein neues ADR in `14_Architekturentscheidungen/` anlegen.
- Frage **nicht löschen**, sondern als beantwortet stehen lassen — sie ist Teil der Projekthistorie.
- Erst danach an dem Arbeitspaket weiterarbeiten, das durch die Frage blockiert war.

---

## Status

Aktuell offen: 0
Aktuell beantwortet: 1

---

## Bekannte offene Punkte aus dem Arbeitsauftrag (Teil G)

Diese Punkte sind keine konkreten KI-Fragen, sondern noch nicht entschiedene Architekturthemen. Sie werden vom Anwalt beantwortet, sobald die zugehörige Phase ansteht.

### G1. beA-Anbindung in Version 1?
- Phase: 2
- Frage: Wird die Anbindung an das besondere elektronische Anwaltspostfach (beA) bereits in der ersten Version benötigt oder erst später?
- Folgen: Aufwand bei „ja" ist erheblich (zertifizierte Schnittstelle, Karten-Hardware).
- Antwort: offen

### G2. Architekturentscheidung Windows-Oberfläche
- Phase: 7
- Frage: WinUI 3 oder WebView2 mit bestehendem HTML?
- Empfehlung der Beratung: WinUI 3.
- Antwort: offen

### G3. Software-Lizenzmodell
- Phase: 8
- Frage: Proprietär, Open Core oder Dual Licensing?
- Empfehlung der Beratung: proprietär für Kanzleisoftware üblich.
- Antwort: offen

### G4. PyMuPDF-Variante
- Phase: 4
- Frage: Freie AGPL-Variante oder kommerzielle Lizenz?
- Folgen: Bei späterem Verkauf der Software kann AGPL Lizenzkonflikte auslösen.
- Antwort: offen

### G5. LLM-Standardmodell für die Erstauslieferung
- Phase: 3 (Kanzlei-PC) und 6 (Laptop)
- Frage: Welches Modell wird im Werkzeugkasten der ersten Version mitgeliefert? Mistral, Phi-3, Llama 3.1 8B, oder mehrere?
- Antwort: offen

### G6. Sprachen der Bedienoberfläche in Version 1
- Phase: 7
- Frage: Welche EU-Sprachen werden für die Bedienoberfläche zuerst unterstützt?
- Mindestens: Deutsch und Englisch.
- Weitere?: offen

### G7. EU-Länder-Adapter-Reihenfolge
- Phase: 5
- Frage: Welche Länder-Adapter werden zuerst gebaut?
- Empfehlung der Beratung: EU, Deutschland, Österreich, Schweden, Frankreich.
- Antwort: offen

---

## Fragen der KI

## Frage 1: Freigabequelle fuer uv, pytest und Offline-Wheelhouse

- Datum: 2026-05-19 11:13
- Phase / Arbeitspaket: Phase 0, AP 0.1 und AP 0.3; Phasenabnahme Phase 0
- Dringlichkeit: [DRINGEND]
- Stellt: Codex

**Worum es geht:**
Phase 0 ist als Struktur umgesetzt, aber die Abnahmekriterien koennen nicht vollstaendig erfuellt werden, solange `uv`, `pytest` und das Offline-Wheelhouse nicht kontrolliert bereitgestellt sind. Nach den Projektregeln darf ich nichts installieren und nichts aus dem Internet laden, ohne ausdrueckliche Freigabe.

**Was bereits geprueft wurde:**
Die projektlokale Python-Laufzeit unter `I:\KI_Legal_Project\Tools\Python312\python.exe` ist vorhanden. `duckdb`, `fastapi`, `uvicorn` und `numpy` sind dort verfuegbar. `uv` und `pytest` sind in dieser Laufzeit nicht installiert. AP 0.1 bis AP 0.7 wurden als Code-/Strukturbausteine umgesetzt und jeweils geprueft; echte `uv sync`- und pytest-Laeufe bleiben blockiert.

**Antwortoptionen (falls moeglich):**
- Option A: Der Anwalt stellt einen lokalen Offline-Ordner mit `uv`, `pytest` und allen Wheels bereit. Folge: Ich inventarisiere SHA-256, befuelle das Wheelhouse und fuehre `uv sync --offline` aus.
- Option B: Der Anwalt erlaubt einmalig einen kontrollierten Download der noetigen freien Pakete in einen Offline-Spiegel. Folge: Ich lade nur diese Pakete, dokumentiere Quellen und SHA-256 und arbeite danach wieder offline.
- Option C: Phase 0 bleibt vorlaeufig technisch vorbereitet, aber nicht abgenommen. Folge: Ich darf Phase 1 nicht sauber starten, weil die Phase-0-Abnahmekriterien noch offen sind.

**Auswirkung auf die laufende Arbeit:**
Ich halte vor Phase 1 an. Ohne Antwort kann ich die Phase-0-Abnahme nicht ehrlich als erledigt melden.

**Antwort des Anwalts:**
Beim Programmieren und Testen darf das Internet genutzt werden — uv, pytest und Entwicklungswerkzeuge dürfen online installiert und aktualisiert werden.
Die fertige Software selbst darf das Internet nicht automatisch nutzen.
Updates sind erlaubt, aber nur wenn ich als Anwalt sie ausdrücklich beauftrage. Automatische Updates im Hintergrund sind verboten.
Einzustellende Regel: Keine automatischen Update-Prüfungen, keine Telemetrie, keine stillen Verbindungen. Update nur auf explizite Nutzeraktion hin.

**Beantwortet am:** 2026-05-19

---

*(Bisher keine weiteren offenen Fragen.)*
