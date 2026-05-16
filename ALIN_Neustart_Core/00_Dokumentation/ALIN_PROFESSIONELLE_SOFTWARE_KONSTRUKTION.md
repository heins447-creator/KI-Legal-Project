# ALIN Professionelle Software-Konstruktion

## Grundsätze

1. **Altbestand bleibt unverändert.**
2. **Neue Architektur entsteht in `ALIN_Neustart_Core`.**
3. **Fachmodule werden später einzeln geprüft und angebunden.**
4. **Keine harte Verdrahtung** von Tools, Sprachen, Quellen, Adaptern oder Skills.
5. **Tools werden zentral registriert.**
6. **Lizenzen werden zentral überwacht.**
7. **Updates werden zentral überwacht.**
8. **Quellen und Adapter bekommen Healthchecks.**
9. **UI verwendet Kanzleisprache.**
10. **Technische Begriffe bleiben intern.**
11. **Jede Entscheidung wird protokolliert.**
12. **Jede Übergabe hat ein Schema.**
13. **Jede Ressource hat Version, Status, Lizenz, Hash und Healthcheck.**
14. **Unsichere Treffer werden markiert, nicht stillschweigend übernommen.**
15. **Keine automatische Stammdatenüberschreibung.**
16. **Keine Beweiswürdigung durch System oder Skill.**
17. **Keine endgültige Rechtsbewertung durch System oder Skill.**
18. **Keine endgültige Übersetzung ohne gesonderte Freigabe.**
19. **Keine Cloudpflicht.**
20. **Gerichtslaptop muss offlinefähig bleiben.**

## Software-Qualitätsmerkmale

| Merkmal | Umsetzung |
|---------|-----------|
| Wartbarkeit | Zentrale Register, klare Schnittstellen, keine harte Verdrahtung |
| Erweiterbarkeit | Neue Module melden sich im Modulregister an |
| Nachvollziehbarkeit | Audit-Protokoll für jede Entscheidung |
| Sicherheit | Lizenzprüfung vor Nutzung, Secrets-Policy, keine API-Keys in Git |
| Offlinefähigkeit | Lokale Ressourcen, Cache, Fallbacks |
| Barrierefreiheit | Tastaturbedienung, Kontrast, Skalierung, Screenreader |
| Testbarkeit | Selbsttest, Modultest, Integrationstest, Regressionstest |
| Rollbackfähigkeit | Versionierung, Backup/Restore, Update-Rollback |

## Trennung der Anliegen

| Schicht | Verantwortung |
|---------|---------------|
| UI (ALIN-Windows) | Darstellung, Bedienung, Kanzleisprache |
| UI-Adapter | Übersetzung zwischen UI und Core |
| ALIN-Core | Register, Resolver, Status, Schnittstellen, Healthcheck |
| Fachmodule | Posteingang, OCR, Anwaltsvorlage, Rücklauf, Quellen, Skills |
| Infrastruktur | Datenbank, Dateisystem, Tools, Netzwerk |

## Keine Monolith-Bildung

ALIN-Core ist kein Monolith. Es ist eine Sammlung klar abgegrenzter Register und Verträge. Fachmodule bleiben eigenständig und kommunizieren über definierte Schnittstellen.

## Versionsverwaltung

- Jedes Register hat eine Schema-Version.
- Jedes Modul hat eine Versionsangabe.
- Jede Änderung wird im Changelog dokumentiert.
- Jede Release hat eine Checkliste und einen Rollback-Plan.
