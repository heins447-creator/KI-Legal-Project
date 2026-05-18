# ALIN Windows-Deployment-Prüfpunkte V1

## Deployment-Modelle

### MSIX (empfohlen)
- Moderne Paketierung
- Saubere Installation und Deinstallation
- Automatische Updates möglich
- Sandbox-Modus
- Voraussetzung: Windows 10 1809+ / Windows 11

### Standalone
- Einzelne ausführbare Datei
- Keine Installation erforderlich
- Einfache Verteilung
- Nachteil: Keine automatischen Updates

### Framework-dependent
- Erfordert .NET Runtime
- Kleinere Paketgröße
- Nachteil: Runtime-Installation erforderlich

## Zielumgebungen

### Kanzlei-PC
- Online-Betrieb
- Volle Funktionalität
- Automatische Updates möglich

### Gerichtslaptop
- Offline-Betrieb
- Lokale Ressourcen
- Synchronisation: Büro → Gericht → Büro

## Prüfpunkte

- [ ] MSIX-Paketierung geprüft
- [ ] Offline-Installation getestet
- [ ] Gerichtslaptop-Profil getestet
- [ ] Trennung Programm / Daten / Cache / Logs
- [ ] Barrierefreiheit geprüft
- [ ] Tastaturbedienung getestet
- [ ] Hoher Kontrast getestet
- [ ] Skalierung getestet
- [ ] Rollback-Verfahren dokumentiert
