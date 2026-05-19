"""
AP 1.3 — Bootstrapper: Alle 16 Tools pruefen und fehlende installieren.

Aufruf: python phase1_ap03_bootstrapper.py [--check-only] [--tool TOOL_ID]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "Config" / "phase1_ap03_bootstrapper_v1.json"
PYTHON = ROOT / "Tools" / "Python312" / "python.exe"
if not PYTHON.exists():
    PYTHON = Path(sys.executable)


GRUEN = "\033[92m"
ROT = "\033[91m"
GELB = "\033[93m"
RESET = "\033[0m"


def run_befehl(befehl: str, timeout: int = 15) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            befehl, shell=True, capture_output=True, text=True, timeout=timeout
        )
        ausgabe = (r.stdout + r.stderr).strip()
        return r.returncode == 0, ausgabe
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def pruefe_python_befehl(befehl: str) -> tuple[bool, str]:
    if befehl.startswith("python"):
        befehl = befehl.replace("python", f'"{PYTHON}"', 1)
    return run_befehl(befehl)


def installiere_pip_wheel(depot_unterverzeichnis: str, pip_paket_name: str) -> bool:
    if depot_unterverzeichnis:
        depot = ROOT / "09_Toolbibliothek" / "02_Installer_Offline" / depot_unterverzeichnis
        wheels = list(depot.glob("*.whl")) + list(depot.glob("*.tar.gz"))
        if wheels:
            cmd = f'"{PYTHON}" -m pip install "{wheels[0]}" --quiet'
            ok, ausgabe = run_befehl(cmd, timeout=120)
            if ok:
                return True
            print(f"    Wheel-Installation fehlgeschlagen: {ausgabe[:100]}")

    print(f"    Versuche Online-Installation: pip install {pip_paket_name}")
    cmd = f'"{PYTHON}" -m pip install {pip_paket_name} --quiet'
    ok, ausgabe = run_befehl(cmd, timeout=300)
    if not ok:
        print(f"    Online-Installation fehlgeschlagen: {ausgabe[:200]}")
    return ok


def verarbeite_tool(schritt: dict, check_only: bool) -> tuple[str, str]:
    tool_id = schritt["tool_id"]
    typ = schritt["typ"]
    pruef_befehl = schritt.get("pruef_befehl", "")

    ok, ausgabe = pruefe_python_befehl(pruef_befehl) if pruef_befehl else (False, "kein Prüfbefehl")

    if ok:
        return "OK", ausgabe.split("\n")[0][:60]

    if check_only or typ == "check_only":
        return "FEHLT", ausgabe.split("\n")[0][:60]

    if typ == "pip_wheel":
        depot_dir = schritt.get("depot_unterverzeichnis", "")
        paket_name = tool_id.lower().replace("_", "-")
        print(f"  → Installiere {tool_id} ...")
        installiert = installiere_pip_wheel(depot_dir, paket_name)
        if installiert:
            ok2, ausgabe2 = pruefe_python_befehl(pruef_befehl)
            return ("OK" if ok2 else "INSTALL_FEHLER"), ausgabe2.split("\n")[0][:60]
        return "INSTALL_FEHLER", "pip fehlgeschlagen"

    if typ == "pfad_check":
        for pfad_str in schritt.get("bekannte_pfade", []):
            pfad = Path(pfad_str) if pfad_str.startswith("C:") or pfad_str.startswith("/") else ROOT / pfad_str
            if pfad.exists():
                return "OK", f"gefunden: {pfad}"
        return "FEHLT", "kein bekannter Pfad gefunden"

    return "UNBEKANNT", typ


def main():
    parser = argparse.ArgumentParser(description="AP 1.3 Bootstrapper")
    parser.add_argument("--check-only", action="store_true", help="Nur pruefen, nicht installieren")
    parser.add_argument("--tool", help="Nur dieses Tool (Tool-ID)")
    args = parser.parse_args()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    schritte = config["install_schritte"]

    if args.tool:
        schritte = [s for s in schritte if s["tool_id"] == args.tool.upper()]
        if not schritte:
            print(f"Tool-ID nicht gefunden: {args.tool}")
            sys.exit(1)

    ergebnisse = []
    print(f"\n{'='*65}")
    print(f"ALIN Bootstrapper — AP 1.3 ({'Nur-Pruefen' if args.check_only else 'Pruefen+Installieren'})")
    print(f"{'='*65}")

    for schritt in schritte:
        tool_id = schritt["tool_id"]
        print(f"\n[{tool_id}]")
        status, detail = verarbeite_tool(schritt, args.check_only)
        ergebnisse.append((tool_id, status, detail))

        farbe = GRUEN if status == "OK" else ROT if status in ("FEHLT", "INSTALL_FEHLER") else GELB
        print(f"  {farbe}{status}{RESET} — {detail}")

    print(f"\n{'='*65}")
    ok_count = sum(1 for _, s, _ in ergebnisse if s == "OK")
    fehler = [(t, s, d) for t, s, d in ergebnisse if s != "OK"]

    print(f"Ergebnis: {ok_count}/{len(ergebnisse)} Tools OK")
    if fehler:
        print(f"\nFEHLER ({len(fehler)}):")
        for t, s, d in fehler:
            print(f"  {ROT}{t}{RESET}: {s} — {d}")
        sys.exit(1)
    else:
        print(f"{GRUEN}Alle Tools bereit.{RESET}")


if __name__ == "__main__":
    main()
