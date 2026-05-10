# Quellenbetreuer Fachanwaltsraster V1

## Zweck

Dieser Baustein legt das Grundgerüst für den Quellenbetreuer, das deutsche Fachanwaltsraster, die länderbezogene Rechtsgebietszuordnung und das erste Sprachpaket `sv_de_arbeitsrecht_se` an.

Er ist die Grundlage für spätere Türschwelle, Sprachpakete, Agentenkommunikation und die endgültige Dokumentenbearbeitung.

## Grenzen

Dieser Baustein führt keine freie Internetrecherche aus. Er lädt keine Massendaten. Er verarbeitet keine echten Mandantendaten. Er erstellt keine Türschwellenmaske, keine endgültige Übersetzung und keine rechtliche Endbewertung.

## Quellenrang

Die Quellen werden zunächst nur als Registereinträge vorbereitet. Der Rang bildet die spätere Prüf- und Quellenlogik ab.

Vorgemerkt werden EU-Justizportal, CCBE, EUR-Lex / Cellar / ELI, ECLI, IATE / VJM, DGT-TM, EuroVoc sowie nationale Gesetzes-, Gerichts- und Berufsquellen für Schweden.

## Offline-Fallback

Offline-Fallback wird in dieser Version nur strukturell vorbereitet. Dazu dienen `source_cache_policy`, `source_health_check` und `source_registry`.

Es werden noch keine vollständigen Quellenbestände gespiegelt.

## Cache-Strategie

Der Cache-Ordner wird unter `Data\Sources\Cache` vorbereitet.

Die Cache-Strategie ist derzeit auf Metadaten und gezielte Auszüge angelegt. Ein vollständiger Import großer EU- oder Länderbestände ist nicht vorgesehen.

## Warum keine freie Internetsuche

Das System soll nicht unkontrolliert das Internet durchsuchen. Rechtsquellen, Terminologiequellen und Berufsquellen müssen gezielt freigegeben, versioniert und geprüft werden.

Die spätere Recherche läuft über definierte Quellenregister, Adapter, Aktualitätsprüfung und Cache.

## Warum zuerst Quellen, danach Türschwelle

Die Türschwelle zwischen Sekretariat und Anwalt darf erst dann fachlich erweitert werden, wenn feststeht, welche Quellen, Rechtsgebiete, Sprachen, Länder und fachgebundenen Agenten zugelassen sind.

Deshalb entsteht zuerst der Quellenbetreuer.

## Zusammenhang mit Arbeitsrecht Schweden

Der erste aktive Testfall ist das deutsche Fachanwaltsgebiet Arbeitsrecht mit Zielland Schweden.

Die interne deutsche Kanzleirasterung lautet `arbeitsrecht`. Die länderbezogene Arbeitsrechtsbezeichnung wird als `arbetsraett` vorbereitet.

## Zusammenhang mit Sprachpaket sv_de_arbeitsrecht_se

Das Sprachpaket `sv_de_arbeitsrecht_se` verbindet Ausgangssprache Schwedisch, Zielsprache Deutsch, Zielland Schweden, deutsches internes Fachgebiet Arbeitsrecht sowie quellengebundene Terminologie und Rechtsquellen.

Ein Rechtsbegriff darf dabei nicht isoliert übersetzt werden. Maßgeblich bleiben Satz, Klausel, Dokumenttyp, Rechtsgebiet, Rechtssystem und Verfahrenssituation.