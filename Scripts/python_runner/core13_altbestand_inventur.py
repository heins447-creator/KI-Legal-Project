# -*- coding: utf-8 -*-
"""
CORE-13 – Automatische Altbestandsinventur und Vor-Klassifikation

Inventarisiert den Altbestand unter I:\\KI_Legal_Project und klassifiziert
jede Datei vorläufig.  Berührt keine Originaldateien, verschiebt nicht,
löscht nicht, benennt nicht um.

Rote Linie:
    produktiv_freigegeben = false
    echte_daten_erlaubt   = false
    nur_musterdaten       = true
"""

import json
import os
import csv
import hashlib
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
PROJEKT_WURZEL = "I:/KI_Legal_Project"
AUSGABE_ORDNER = "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand"
BERICHT_ORDNER = "ALIN_Neustart_Core/Reports"

MAX_HASH_GROESSE = 100 * 1024 * 1024   # 100 MB

AUSZUSCHLIESSENDE_NAMEN = {
    ".git", "__pycache__", ".venv", "venv",
    "node_modules", ".idea", ".vscode",
    "Thumbs.db", ".DS_Store", "desktop.ini",
}

AUSZUSCHLIESSENDE_ENDUNGEN = {
    ".tmp", ".temp", ".bak", ".old", ".orig",
    ".pyc", ".pyo", ".class", ".o", ".obj",
}

AUSZUSCHLIESSENDE_MUSTER = [
    r"Windows_App[\\/]Logs",
    r"_temp_.*\\.ps1$",
    r"\\.git[\\/]",
    r"__pycache__[\\/]",
]

# Dateityp-Erkennung
TYPEN = {
    ".py":   "python",
    ".ps1":  "powershell",
    ".json": "json",
    ".md":   "markdown",
    ".csv":  "csv",
    ".txt":  "text",
    ".sql":  "sql",
    ".html": "html",
    ".htm":  "html",
    ".xml":  "xml",
    ".yaml": "yaml",
    ".yml":  "yaml",
    ".schema": "schema",
    ".schema.json": "schema",
    ".jpg":  "bild",
    ".jpeg": "bild",
    ".png":  "bild",
    ".gif":  "bild",
    ".bmp":  "bild",
    ".webp": "bild",
    ".svg":  "bild",
    ".pdf":  "pdf",
    ".docx": "dokument",
    ".doc":  "dokument",
    ".xlsx": "tabelle",
    ".xls":  "tabelle",
    ".zip":  "archiv",
    ".7z":   "archiv",
    ".tar":  "archiv",
    ".gz":   "archiv",
    ".rar":  "archiv",
    ".db":   "datenbank",
    ".duckdb": "datenbank",
    ".exe":  "binary",
    ".dll":  "binary",
}

KLASSEN = [
    "AKTIV",
    "ERSETZT",
    "ALT_ABER_NOCH_RELEVANT",
    "TESTREST",
    "LAUFZEIT_ARTEFAKT",
    "LOG_BERICHT",
    "CONFIG_LOKAL",
    "DUBLETTE",
    "UNGEKLÄRT",
    "SPERREN",
]

SCHWEREGRADE = ["KRITISCH", "HOCH", "MITTEL", "NIEDRIG"]

SPERR_MUSTER = {
    "DB_ÄNDERUNG":          [r"\\.sql$", r"INSERT\s+INTO", r"UPDATE\s+", r"DELETE\s+FROM", r"DROP\s+TABLE"],
    "ORIGINAL_ÄNDERUNG":    [r"mv\s+", r"move\s+", r"del\s+", r"rm\s+-rf", r"shutil\\.rmtree", r"os\\.remove"],
    "INTERNET":             [r"requests\\.", r"urllib", r"http://", r"https://", r"\\.com[\\/\"]", r"\\.de[\\/\"]"],
    "API":                  [r"api_key", r"apikey", r"API_KEY", r"auth_token", r"bearer\\s+"],
    "CLOUD":                [r"aws", r"azure", r"gcp", r"s3://", r"blob\\.core\\.windows\\.net"],
    "DEEPL":                [r"deepl", r"DEEPL", r"DeepL"],
    "ARGOS":                [r"argos", r"ARGOS", r"Argos"],
    "PRODUKTIVFREIGABE":    [r"produktiv_freigegeben\\s*[=:]\\s*true", r"produktiv\\s*freigeben"],
    "ECHTE_DATEN":          [r"mandant", r"Mandant", r"klient", r"Klient", r"eakten", r"E-Akte"],
    "KRITISCHES_MODUL":     [r"sperrregister", r"healthcheck.*kritisch", r"P0\\b"],
}

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def sha256_datei(pfad, max_bytes=MAX_HASH_GROESSE):
    """Berechnet SHA-256, bricht bei zu großen Dateien ab."""
    try:
        st = os.stat(pfad)
        if st.st_size > max_bytes:
            return f"<SKIP_GROSS_{st.st_size}>"
        h = hashlib.sha256()
        with open(pfad, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"<FEHLER:{e}>"


def relativ_pfad(pfad):
    """Macht absoluten Pfad relativ zum Projekt."""
    return os.path.relpath(pfad, PROJEKT_WURZEL).replace("\\", "/")


def soll_ausschliessen(pfad):
    """Prüft Ausschlusskriterien."""
    norm = pfad.replace("\\", "/")
    teile = norm.split("/")
    for t in teile:
        if t in AUSZUSCHLIESSENDE_NAMEN:
            return True
        if any(t.endswith(e) for e in AUSZUSCHLIESSENDE_ENDUNGEN):
            return True
    for pat in AUSZUSCHLIESSENDE_MUSTER:
        if re.search(pat, norm):
            return True
    return False


def erkenne_dateityp(name):
    """Bestimmt Dateityp anhand der Endung."""
    lower = name.lower()
    for ext, typ in sorted(TYPEN.items(), key=lambda x: -len(x[0])):
        if lower.endswith(ext):
            return typ
    return "unbekannt"


def erkenne_python_merkmale(pfad):
    """Liest Python-Datei sicher und extrahiert Imports/Funktionsnamen."""
    merkmale = {
        "imports": [],
        "funktionen": [],
        "klassen": [],
        "deepl": False,
        "argos": False,
        "db_aenderung": False,
        "original_aenderung": False,
        "internet": False,
        "api": False,
        "cloud": False,
        "produktiv": False,
        "mandant": False,
    }
    try:
        with open(pfad, "r", encoding="utf-8", errors="replace") as f:
            zeilen = f.readlines()[:200]   # Nur ersten 200 Zeilen
    except Exception:
        return merkmale

    text = "".join(zeilen)
    for zeile in zeilen:
        z = zeile.strip()
        if z.startswith("import ") or z.startswith("from "):
            merkmale["imports"].append(z.split()[1].split(".")[0])
        if z.startswith("def "):
            merkmale["funktionen"].append(z.split()[1].split("(")[0])
        if z.startswith("class "):
            merkmale["klassen"].append(z.split()[1].split("(")[0].split(":")[0])

    # Sperrmuster-Prüfung (nur technische Schlüsselwörter)
    ltxt = text.lower()
    merkmale["deepl"] = "deepl" in ltxt
    merkmale["argos"] = "argos" in ltxt
    merkmale["db_aenderung"] = bool(re.search(r"insert\s+into|update\s+\w+\s+set|delete\s+from|drop\s+table|alter\s+table", ltxt))
    merkmale["original_aenderung"] = bool(re.search(r"shutil\.rmtree|os\.remove\(|os\.rename\(|os\.unlink\(", ltxt))
    merkmale["internet"] = bool(re.search(r"requests\.|urllib|http://|https://", ltxt))
    merkmale["api"] = bool(re.search(r"api_key|apikey|auth_token|bearer\s+", ltxt))
    merkmale["cloud"] = bool(re.search(r"aws|azure|gcp|s3://|blob\.core\.windows\.net", ltxt))
    merkmale["produktiv"] = bool(re.search(r"produktiv_freigegeben\s*[=:]\s*true", ltxt))
    merkmale["mandant"] = bool(re.search(r"mandant|klient|eakten|echte_daten", ltxt))

    # Imports deduplizieren und begrenzen
    merkmale["imports"] = list(set(merkmale["imports"]))[:20]
    merkmale["funktionen"] = merkmale["funktionen"][:30]
    merkmale["klassen"] = merkmale["klassen"][:10]
    return merkmale


def erkenne_ps_merkmale(pfad):
    """Liest PowerShell-Datei sicher und extrahiert Funktionen."""
    merkmale = {"funktionen": [], "imports": [], "deepl": False, "db_aenderung": False}
    try:
        with open(pfad, "r", encoding="utf-8", errors="replace") as f:
            zeilen = f.readlines()[:150]
    except Exception:
        return merkmale
    for zeile in zeilen:
        z = zeile.strip()
        m = re.match(r"function\s+(\w+)", z, re.IGNORECASE)
        if m:
            merkmale["funktionen"].append(m.group(1))
    return merkmale


def erkenne_json_merkmale(pfad):
    """Prüft JSON-Datei auf technische Schlüsselwörter."""
    merkmale = {"keys": [], "produktiv": False, "mandant": False}
    try:
        with open(pfad, "r", encoding="utf-8", errors="replace") as f:
            text = f.read(50000)
    except Exception:
        return merkmale
    merkmale["keys"] = list(set(re.findall(r'"(\w+)":', text)))[:30]
    merkmale["produktiv"] = "produktiv_freigegeben\"" in text and "true" in text
    merkmale["mandant"] = bool(re.search(r"mandant|klient|eakten|echte_daten", text.lower()))
    return merkmale


def lade_register(pfad):
    """Lädt ein Register, gibt None zurück bei Fehler."""
    try:
        with open(pfad, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def abgleich_modulregister(name, pfad, register):
    """Prüft ob Datei/Name im Modulregister vorkommt."""
    if not register:
        return {"gefunden": False, "grund": "Register nicht ladbar"}
    eintraege = register.get("eintraege", [])
    for e in eintraege:
        mod_id = e.get("modul_id", "")
        if mod_id.lower() in name.lower() or mod_id.lower() in pfad.lower():
            return {"gefunden": True, "modul_id": mod_id, "typ": "modul"}
    return {"gefunden": False}


def abgleich_allgemein(name, pfad, register, feld_id="id"):
    """Generischer Abgleich mit beliebigem Register."""
    if not register:
        return {"gefunden": False, "grund": "Register nicht ladbar"}
    eintraege = register.get("eintraege", [])
    for e in eintraege:
        ids = [e.get(feld_id, ""), e.get("name", "")]
        for i in ids:
            if i and i.lower() in name.lower():
                return {"gefunden": True, "id": i, "typ": feld_id}
    return {"gefunden": False}


def bestimme_klasse(eintrag, dubletten_set, register_hits):
    """Bestimmt die Hauptklasse einer Datei."""
    name = eintrag["dateiname"].lower()
    pfad = eintrag["relativer_pfad"].lower()
    typ = eintrag["dateityp"]
    merkmale = eintrag.get("merkmale", {})
    sha = eintrag["sha256"]

    # Dublette zuerst prüfen
    if sha.startswith("<") is False and sha in dubletten_set:
        return "DUBLETTE"

    # Laufzeit-Artefakt
    if any(x in pfad for x in ["__pycache__", ".tmp", "temp/", "cache", "logs/"]):
        return "LAUFZEIT_ARTEFAKT"
    if name.endswith(".pyc") or name.endswith(".pyo"):
        return "LAUFZEIT_ARTEFAKT"

    # Log/Bericht
    if any(x in pfad for x in ["reports/", "bericht", "logs/", "log/", "_bericht", "_log"]):
        return "LOG_BERICHT"
    if typ == "text" and ("bericht" in name or "log" in name or "report" in name):
        return "LOG_BERICHT"

    # Config lokal
    if typ == "json" and ("config" in name or "cfg" in name):
        if ".gitignore" in pfad or "config" in pfad:
            return "CONFIG_LOKAL"

    # SPERREN – sicherheitsrelevant
    if merkmale.get("db_aenderung") or merkmale.get("original_aenderung"):
        return "SPERREN"
    if merkmale.get("produktiv"):
        return "SPERREN"
    if merkmale.get("internet") or merkmale.get("cloud") or merkmale.get("api"):
        return "SPERREN"

    # AKTIV – erkennbar aktueller Bestandteil
    if any(x in pfad for x in ["alin_neustart_core/", "scripts/python_runner/", "scripts/ui", "config/ui"]):
        if typ in ("python", "powershell", "json", "markdown", "html", "sql"):
            return "AKTIV"

    # ERSETZT – überholte Versionen
    if re.search(r"_old\.|_alt\.|_backup\.|_bak\.|_v\d+\.", name):
        return "ERSETZT"
    if register_hits.get("modulregister", {}).get("gefunden"):
        # Wenn neuerer Name existiert, könnte es alt sein – hier konservativ
        pass

    # TESTREST
    if any(x in pfad for x in ["test", "_test", "temp_", "experiment", "spiel"]) or name.startswith("test"):
        return "TESTREST"

    # ALT_ABER_NOCH_RELEVANT – ältere CORE-Berichte etc.
    if "alin_neustart_core/reports" in pfad:
        return "ALT_ABER_NOCH_RELEVANT"
    if "alin_neustart_core/07_bestandsaufnahme" in pfad:
        return "ALT_ABER_NOCH_RELEVANT"

    # UNGEKLÄRT
    return "UNGEKLÄRT"


def sperrhinweis_generieren(eintrag):
    """Erzeugt Sperrhinweis-Liste für eine Datei."""
    hinweise = []
    m = eintrag.get("merkmale", {})
    if m.get("db_aenderung"):
        hinweise.append({"grund": "DB_ÄNDERUNG", "schweregrad": "KRITISCH", "empfehlung": "Prüfung vor Ausführung"})
    if m.get("original_aenderung"):
        hinweise.append({"grund": "ORIGINAL_ÄNDERUNG", "schweregrad": "KRITISCH", "empfehlung": "Nicht automatisch ausführen"})
    if m.get("internet"):
        hinweise.append({"grund": "INTERNET", "schweregrad": "HOCH", "empfehlung": "Offline-Betrieb prüfen"})
    if m.get("api"):
        hinweise.append({"grund": "API_KEY", "schweregrad": "KRITISCH", "empfehlung": "Auf Schlüssel-Lecks prüfen"})
    if m.get("cloud"):
        hinweise.append({"grund": "CLOUD", "schweregrad": "HOCH", "empfehlung": "Datenschutz prüfen"})
    if m.get("deepl"):
        hinweise.append({"grund": "DEEPL", "schweregrad": "MITTEL", "empfehlung": "Offline-Konfiguration prüfen"})
    if m.get("argos"):
        hinweise.append({"grund": "ARGOS", "schweregrad": "MITTEL", "empfehlung": "Modell-Verfügbarkeit prüfen"})
    if m.get("produktiv"):
        hinweise.append({"grund": "PRODUKTIVFREIGABE", "schweregrad": "KRITISCH", "empfehlung": "Freigabe-Status widerlegen"})
    if m.get("mandant"):
        hinweise.append({"grund": "MANDANTENDATEN_VERDACHT", "schweregrad": "MITTEL", "empfehlung": "Inhalt auf Echtdaten prüfen"})
    return hinweise


# ---------------------------------------------------------------------------
# Hauptlauf
# ---------------------------------------------------------------------------

def hauptlauf():
    fehler = 0
    warnungen = 0

    print("=" * 60)
    print("CORE-13 – ALTBESTAND INVENTUR")
    print("=" * 60)

    # Register laden
    register = {
        "modulregister":        lade_register("ALIN_Neustart_Core/01_Register/modulregister.json"),
        "ressourcenregister":   lade_register("ALIN_Neustart_Core/01_Register/ressourcenregister.json"),
        "skillregister":        lade_register("ALIN_Neustart_Core/01_Register/skillregister.json"),
        "toolregister":         lade_register("ALIN_Neustart_Core/01_Register/toolregister.json"),
        "quellenregister":      lade_register("ALIN_Neustart_Core/01_Register/quellen_adapter_register.json"),
        "lizenzregister":       lade_register("ALIN_Neustart_Core/01_Register/lizenzregister.json"),
        "update_register":      lade_register("ALIN_Neustart_Core/01_Register/update_register.json"),
        "sperrregister":        lade_register("ALIN_Neustart_Core/01_Register/sperrregister.json"),
    }
    for k, v in register.items():
        if v is None:
            warnungen += 1
            print(f"[WARNUNG] Register nicht ladbar: {k}")
        else:
            print(f"[OK] Register geladen: {k}")

    # Scan
    inventar = []
    ausgeschlossen = []
    sha_zaehler = {}

    print("\n[INFO] Scanning Projektbaum ...")
    for root, dirs, files in os.walk(PROJEKT_WURZEL):
        # Filtere ausgeschlossene Verzeichnisse
        dirs[:] = [d for d in dirs if not soll_ausschliessen(os.path.join(root, d))]

        for datei in files:
            voller_pfad = os.path.join(root, datei)
            rel = relativ_pfad(voller_pfad)

            if soll_ausschliessen(voller_pfad):
                ausgeschlossen.append(rel)
                continue

            try:
                st = os.stat(voller_pfad)
                groesse = st.st_size
                mtime = datetime.fromtimestamp(st.st_mtime).isoformat()
            except Exception:
                groesse = -1
                mtime = ""

            # SHA-256
            sha = sha256_datei(voller_pfad)
            if sha not in sha_zaehler:
                sha_zaehler[sha] = 0
            sha_zaehler[sha] += 1

            # Dateityp
            typ = erkenne_dateityp(datei)
            endung = os.path.splitext(datei)[1].lower()

            # Merkmale
            merkmale = {}
            if typ == "python":
                merkmale = erkenne_python_merkmale(voller_pfad)
            elif typ == "powershell":
                merkmale = erkenne_ps_merkmale(voller_pfad)
            elif typ == "json":
                merkmale = erkenne_json_merkmale(voller_pfad)

            # Registerabgleich
            reg_hits = {
                "modulregister": abgleich_modulregister(datei, rel, register["modulregister"]),
                "toolregister":  abgleich_allgemein(datei, rel, register["toolregister"], "tool_id"),
                "skillregister": abgleich_allgemein(datei, rel, register["skillregister"], "skill_id"),
                "ressourcenregister": abgleich_allgemein(datei, rel, register["ressourcenregister"], "ressourcen_id"),
            }

            eintrag = {
                "relativer_pfad": rel,
                "dateiname": datei,
                "dateiendung": endung,
                "dateigroesse": groesse,
                "aenderungsdatum": mtime,
                "sha256": sha,
                "dateityp": typ,
                "ist_python": typ == "python",
                "ist_powershell": typ == "powershell",
                "ist_json": typ == "json",
                "ist_markdown": typ == "markdown",
                "ist_csv": typ == "csv",
                "ist_text": typ == "text",
                "ist_bericht": False,
                "ist_log": False,
                "ist_runner": "runner" in datei.lower() or "run_" in datei.lower(),
                "ist_check": datei.startswith("check_") or "check" in datei.lower(),
                "ist_config": "config" in datei.lower() or datei.endswith(".config.json"),
                "ist_laufzeit_artefakt": False,
                "ist_altversion": bool(re.search(r"_old\.|_alt\.|_backup\.|_bak\.|_v\d+", datei.lower())),
                "ist_dublette": False,
                "ist_unbekannt": typ == "unbekannt",
                "ist_sicherheitsrelevant": False,
                "merkmale": merkmale,
                "register_hits": reg_hits,
                "bemerkung": "",
            }
            inventar.append(eintrag)

    print(f"[OK] {len(inventar)} Dateien inventarisiert, {len(ausgeschlossen)} ausgeschlossen.")

    # Dubletten-Set bilden (SHA die mehrfach vorkommen)
    dubletten_set = {sha for sha, cnt in sha_zaehler.items() if cnt > 1 and not sha.startswith("<")}

    # Klassifikation + Sperrhinweise
    sperrhinweise = []
    klassen_counter = {k: 0 for k in KLASSEN}

    for eintrag in inventar:
        klasse = bestimme_klasse(eintrag, dubletten_set, eintrag["register_hits"])
        eintrag["klassifikation"] = klasse
        klassen_counter[klasse] += 1

        sh = sperrhinweis_generieren(eintrag)
        if sh:
            eintrag["ist_sicherheitsrelevant"] = True
            for h in sh:
                sperrhinweise.append({
                    "relativer_pfad": eintrag["relativer_pfad"],
                    "grund": h["grund"],
                    "schweregrad": h["schweregrad"],
                    "empfehlung": h["empfehlung"],
                })

    # Ausgabe: JSON-Inventur
    os.makedirs(AUSGABE_ORDNER, exist_ok=True)
    os.makedirs(BERICHT_ORDNER, exist_ok=True)

    json_pfad = os.path.join(AUSGABE_ORDNER, "CORE13_altbestand_inventur.json")
    with open(json_pfad, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {
                "modul_id": "CORE-13",
                "name": "Altbestand-Inventur",
                "version": "1.0.0",
                "zeitstempel": datetime.now().isoformat(),
                "projekt_wurzel": PROJEKT_WURZEL,
                "nur_lesend": True,
                "produktiv_freigegeben": False,
            },
            "zusammenfassung": {
                "anzahl_dateien": len(inventar),
                "anzahl_ausgeschlossen": len(ausgeschlossen),
                "klassifikationen": klassen_counter,
                "anzahl_dubletten": len(dubletten_set),
                "anzahl_sperrhinweise": len(sperrhinweise),
                "register_ladbar": {k: v is not None for k, v in register.items()},
            },
            "dateien": inventar,
        }, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON-Inventur: {json_pfad}")

    # CSV-Inventur
    csv_pfad = os.path.join(AUSGABE_ORDNER, "CORE13_altbestand_inventur.csv")
    with open(csv_pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["relativer_pfad", "dateiname", "endung", "groesse", "aenderungsdatum",
                    "sha256", "dateityp", "klassifikation", "sicherheitsrelevant"])
        for e in inventar:
            w.writerow([e["relativer_pfad"], e["dateiname"], e["dateiendung"], e["dateigroesse"],
                        e["aenderungsdatum"], e["sha256"], e["dateityp"],
                        e["klassifikation"], e["ist_sicherheitsrelevant"]])
    print(f"[OK] CSV-Inventur: {csv_pfad}")

    # CSV-Klassifikation
    csv_klass_pfad = os.path.join(AUSGABE_ORDNER, "CORE13_klassifikation.csv")
    with open(csv_klass_pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["klasse", "anzahl", "anteil_prozent"])
        for k in KLASSEN:
            anteil = round(100.0 * klassen_counter[k] / max(len(inventar), 1), 2)
            w.writerow([k, klassen_counter[k], anteil])
    print(f"[OK] CSV-Klassifikation: {csv_klass_pfad}")

    # CSV-Dubletten
    csv_dubl_pfad = os.path.join(AUSGABE_ORDNER, "CORE13_dubletten.csv")
    with open(csv_dubl_pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sha256", "relativer_pfad", "dateiname", "groesse"])
        for e in inventar:
            if e["sha256"] in dubletten_set and not e["sha256"].startswith("<"):
                w.writerow([e["sha256"], e["relativer_pfad"], e["dateiname"], e["dateigroesse"]])
    print(f"[OK] CSV-Dubletten: {csv_dubl_pfad}")

    # CSV-Sperrhinweise
    csv_sperr_pfad = os.path.join(AUSGABE_ORDNER, "CORE13_sperrhinweise.csv")
    with open(csv_sperr_pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["relativer_pfad", "grund", "schweregrad", "empfehlung"])
        for s in sperrhinweise:
            w.writerow([s["relativer_pfad"], s["grund"], s["schweregrad"], s["empfehlung"]])
    print(f"[OK] CSV-Sperrhinweise: {csv_sperr_pfad}")

    # Bericht
    bericht_pfad = os.path.join(BERICHT_ORDNER, "CORE13_ALTBESTAND_INVENTUR_BERICHT.txt")
    with open(bericht_pfad, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("CORE-13 – ALTBESTAND INVENTUR BERICHT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Zeitstempel: {datetime.now().isoformat()}\n")
        f.write("Modus: NUR LESEND – keine Dateien verschoben, gelöscht oder umbenannt\n")
        f.write("Produktivfreigabe: NEIN\n\n")

        f.write("ZUSAMMENFASSUNG\n")
        f.write("-" * 40 + "\n")
        f.write(f"Gescannte Dateien:     {len(inventar)}\n")
        f.write(f"Ausgeschlossen:        {len(ausgeschlossen)}\n")
        f.write(f"Dubletten (SHA):       {len(dubletten_set)}\n")
        f.write(f"Sperrhinweise:         {len(sperrhinweise)}\n")
        f.write(f"Fehler:                {fehler}\n")
        f.write(f"Warnungen:             {warnungen}\n\n")

        f.write("KLASSIFIKATIONEN\n")
        f.write("-" * 40 + "\n")
        for k in KLASSEN:
            f.write(f"  {k:<25} {klassen_counter[k]:>6}\n")
        f.write("\n")

        f.write("REGISTER-STATUS\n")
        f.write("-" * 40 + "\n")
        for k, v in register.items():
            f.write(f"  {k:<25} {'OK' if v else 'FEHLER/UNBEKANNT'}\n")
        f.write("\n")

        f.write("AUSGESCHLOSSENE BEREICHE (Beispiele)\n")
        f.write("-" * 40 + "\n")
        for a in ausgeschlossen[:20]:
            f.write(f"  {a}\n")
        if len(ausgeschlossen) > 20:
            f.write(f"  ... und {len(ausgeschlossen)-20} weitere\n")
        f.write("\n")

        f.write("SPERRHINWEISE (nach Schweregrad)\n")
        f.write("-" * 40 + "\n")
        for sg in SCHWEREGRADE:
            anz = sum(1 for s in sperrhinweise if s["schweregrad"] == sg)
            f.write(f"  {sg:<10} {anz}\n")
        f.write("\n")

        f.write("WICHTIGE RISIKEN\n")
        f.write("-" * 40 + "\n")
        kritisch = [s for s in sperrhinweise if s["schweregrad"] == "KRITISCH"]
        if kritisch:
            f.write(f"  KRITISCHE Hinweise: {len(kritisch)}\n")
            for s in kritisch[:10]:
                f.write(f"    {s['relativer_pfad']} – {s['grund']}\n")
        else:
            f.write("  Keine kritischen Hinweise.\n")
        f.write("\n")

        f.write("NÄCHSTE EMPFOHLENE SCHRITTE\n")
        f.write("-" * 40 + "\n")
        f.write("1. CORE-14: Bereinigung der Dubletten und Testreste planen\n")
        f.write("2. CORE-15: SPERREN-Kandidaten manuell prüfen und freigeben oder löschen\n")
        f.write("3. CORE-16: AKTIV- und ALT_ABER_NOCH_RELEVANT-Dateien in Register überführen\n")
        f.write("\n" + "=" * 60 + "\n")
        f.write("ENDE BERICHT\n")
    print(f"[OK] Bericht: {bericht_pfad}")

    print("\n" + "=" * 60)
    print(f"CORE-13 abgeschlossen. Fehler: {fehler}, Warnungen: {warnungen}")
    print("=" * 60)

    return fehler, warnungen


if __name__ == "__main__":
    fehler, warnungen = hauptlauf()
    import sys
    sys.exit(0 if fehler == 0 else 1)
