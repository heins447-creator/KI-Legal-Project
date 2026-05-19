# -*- coding: utf-8 -*-
"""
PRUEFDATEI KM10 – SCHNITTSTELLEN- UND LUECKENABGLEICH
=====================================================

Prueft, ob alle Ausgaben von km10_schnittstellen_lueckenabgleich.py
vorhanden und gueltig sind.
"""

import sys
import json
import traceback
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SCHREIBBEREICH = ROOT / "Agentensteuerung" / "10_Schnittstellen_Lueckenabgleich_Dokumentenstrasse"
BERICHTE = SCHREIBBEREICH / "03_Berichte"
ARTEFAKTE = SCHREIBBEREICH / "06_Artefakte"
STATUS = SCHREIBBEREICH / "02_Status"
FEHLER = SCHREIBBEREICH / "05_Fehler"


def check_file(path, desc):
    if not path.exists():
        return False, f"FEHLT: {desc} ({path})"
    size = path.stat().st_size
    if size < 100:
        return False, f"ZU KLEIN: {desc} ({size} Bytes)"
    return True, f"OK: {desc} ({size} Bytes)"


def main():
    print("=" * 60)
    print("PRUEFDATEI KM10")
    print("=" * 60)

    errors = 0
    ok = 0

    # Pruefe Verzeichnisse
    for d in [BERICHTE, ARTEFAKTE, STATUS, FEHLER]:
        if not d.exists():
            print(f"FEHLER: Verzeichnis fehlt: {d}")
            errors += 1
        else:
            print(f"OK: Verzeichnis: {d}")

    # Pruefe Berichte
    expected_reports = [
        "01_BESTANDSABGLEICH_GEGEN_STRUKTURANALYSE.txt",
        "02_SCHNITTSTELLENMATRIX.txt",
        "03_LUECKEN_DOPPLUNGEN_RISIKEN.txt",
        "04_MODUL22_ABGLEICH.txt",
        "05_DATENMODELL_UND_FUNDSTELLEN_ABGLEICH.txt",
        "06_NAECHSTER_PROGRAMMIERAUFTRAG.txt",
        "07_ABSCHLUSSBERICHT_KM10.txt",
    ]

    print(f"\nBerichte ({len(expected_reports)}):")
    for r in expected_reports:
        success, msg = check_file(BERICHTE / r, r)
        if success:
            ok += 1
        else:
            errors += 1
        print(f"  {msg}")

    # Pruefe Artefakte
    expected_artifacts = [
        "KM10_SCHNITTSTELLENMATRIX.json",
        "KM10_BESTANDSINVENTAR.json",
        "KM10_NAECHSTER_AUFTRAG.json",
    ]

    print(f"\nArtefakte ({len(expected_artifacts)}):")
    for a in expected_artifacts:
        success, msg = check_file(ARTEFAKTE / a, a)
        if success:
            # Pruefe JSON-Gueltigkeit
            try:
                data = json.loads((ARTEFAKTE / a).read_text(encoding="utf-8"))
                msg += f" (JSON OK)"
            except json.JSONDecodeError:
                msg += f" (JSON UNGUELTIG)"
                success = False
                errors += 1
        if success:
            ok += 1
        else:
            errors += 1
        print(f"  {msg}")

    # Pruefe Status
    print("\nStatus:")
    success, msg = check_file(STATUS / "KM10_STATUS.json", "Status-JSON")
    if success:
        try:
            data = json.loads((STATUS / "KM10_STATUS.json").read_text(encoding="utf-8"))
            assert data.get("produktive_aenderungen") == False, "Produktive Aenderungen gesetzt!"
            assert data.get("rechtsbewertung") == False, "Rechtsbewertung gesetzt!"
            assert data.get("beweiswuerdigung") == False, "Beweiswuerdigung gesetzt!"
            msg += " (Produktivfreigabe: NEIN)"
        except (json.JSONDecodeError, AssertionError) as e:
            msg += f" (FEHLER: {e})"
            success = False
            errors += 1
    if success:
        ok += 1
    else:
        errors += 1
    print(f"  {msg}")

    # Pruefe Fehlerdatei
    print("\nFehlerdatei:")
    success, msg = check_file(FEHLER / "KM10_FEHLER.txt", "Fehlerdatei")
    if success:
        ok += 1
    else:
        errors += 1
    print(f"  {msg}")

    print("\n" + "=" * 60)
    print(f"ERGEBNIS: {ok} OK, {errors} FEHLER")
    print("=" * 60)

    if errors == 0:
        print("PRUEFUNG BESTANDEN")
        return 0
    else:
        print("PRUEFUNG NICHT BESTANDEN")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nABGEBROCHEN")
        sys.exit(130)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
