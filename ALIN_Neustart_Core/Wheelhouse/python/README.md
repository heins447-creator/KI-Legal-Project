# ALIN Python-Wheelhouse

Dieses Verzeichnis ist der lokale Spiegel fuer Python-Wheels.

Regeln:

- Keine Downloads durch die ALIN-Software.
- Befuellung nur als kontrollierter Hersteller-/Entwicklungsakt.
- Jedes Wheel wird mit SHA-256 in einem Manifest erfasst.
- Installation erfolgt spaeter nur offline, z. B. mit:

```powershell
uv pip sync --offline --find-links Wheelhouse/python requirements.lock
```

Stand AP 0.1: Struktur angelegt, Wheel-Dateien noch nicht gespiegelt.
