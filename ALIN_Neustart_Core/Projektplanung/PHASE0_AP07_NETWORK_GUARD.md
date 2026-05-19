# Phase 0, AP 0.7: Internet-Sperre als technische Komponente

## Ziel

ALIN bekommt eine app-interne Outbound-Sperre. Standard ist: keine Verbindung ins Internet.

## Modul

`alin_core/network_guard.py` stellt bereit:

- `check_outbound_allowed`
- `enforce_network_guard`
- `NetworkBlockedError`

## Update-Kanal

Der Update-Kanal ist als Ausnahme vorgesehen, aber noch ohne echten Host konfiguriert. Eine Verbindung wird nur erlaubt, wenn:

1. der Host in `Config/phase0_ap07_network_guard_v1.json` als Update-Host eingetragen ist, und
2. ein ausdruecklicher Update-Klick uebergeben wird.

Bis zur spaeteren Festlegung eines Hersteller-Update-Hosts bleibt die Allowlist leer.

## Start

```powershell
Scripts\Run_PHASE0_AP07_Network_Guard.ps1
```
