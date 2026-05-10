# AGENTS.md

## Geltungsbereich

Dieses Regelwerk gilt für alle KI-Coding-Agenten im Projekt `I:\KI_Legal_Project`.

## Harte Grenzen

Keine Änderungen außerhalb von `I:\KI_Legal_Project`.

Keine echten Mandantendaten an externe Modelle.

Keine freie Internetrecherche.

Keine API-Schlüssel in Git.

Keine endgültige Rechtsberatung.

Keine Beweiswürdigung.

Keine Türschwelle, bevor Quellenregister, Fachanwaltsraster, Quellenbetreuer, Adapter, Cache und Offline-Fallback stehen.

## Lieferpflicht je Programmierauftrag

Jeder Baustein muß liefern:

1. Migration, falls Datenbank betroffen ist.
2. Python-Läufer unter `Scripts\python_runner`.
3. Prüfdatei unter `Scripts\python_runner`.
4. PowerShell-Starter unter `Scripts`.
5. Konfiguration unter `Config`, falls erforderlich.
6. Dokumentation unter `Projektplanung`.
7. Testlauf.
8. Bericht unter `Windows_App\Logs`.
9. Git-Status vor und nach Änderung.
10. Git-Commit nur bei erfolgreichem Build und erfolgreicher Prüfung.

## Aktuelle Reihenfolge

1. QUELLENBETREUER_FACHANWALTSRASTER_V1
2. AGENTEN_KONTEXT_SKILL_REGISTER_V1
3. AGENTEN_KOMMUNIKATION_UND_PRUEFAUFTRAEGE_V1
4. RECHTSKONTEXT_SPRACHPAKET_CACHE_V1
5. ANYTHINGLLM_OFFLINE_HANDAKTE_ZENTRALE_V1
6. MANDATSANNAHME_TUERSCHWELLE_V1
