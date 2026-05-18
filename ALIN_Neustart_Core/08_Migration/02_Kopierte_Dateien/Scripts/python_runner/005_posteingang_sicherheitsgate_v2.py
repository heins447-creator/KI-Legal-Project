import sys
import csv
import json
import shutil
import hashlib
import subprocess
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(r"I:\KI_Legal_Project")
POST_DIR = ROOT / "Posteingang"
HELPER = ROOT / "Scripts" / "python_runner" / "005_windows_security_probe.ps1"

DIRS = {
    "roh": POST_DIR / "00_Roh_Eingang",
    "quarantaene": POST_DIR / "01_Quarantaene",
    "geprueft": POST_DIR / "02_Technisch_Geprueft",
    "vorzimmer": POST_DIR / "03_Vorzimmer_Entscheidung",
    "anwalt": POST_DIR / "04_Anwaltvorlage",
    "rueckfrage": POST_DIR / "05_Rueckfrage_Absender",
    "abgewiesen": POST_DIR / "06_Abgewiesen",
    "signatur": POST_DIR / "07_Signaturpruefung",
    "protokolle": POST_DIR / "90_Protokolle",
    "karten": POST_DIR / "91_Entscheidungskarten",
    "sicherheit": POST_DIR / "92_Sicherheitsberichte"
}

ACTIVE_EXT = {
    ".exe", ".dll", ".com", ".scr", ".bat", ".cmd", ".ps1", ".vbs",
    ".js", ".jse", ".wsf", ".msi", ".msp", ".hta", ".jar", ".lnk", ".reg"
}

SAFE_DOC_EXT = {
    ".pdf", ".txt", ".rtf", ".docx", ".xlsx", ".pptx",
    ".odt", ".ods", ".odp", ".jpg", ".jpeg", ".png",
    ".tif", ".tiff", ".eml", ".msg"
}

SIGNED_CONTAINER_EXT = {
    ".p7m", ".p7s", ".p7c", ".asice", ".sce", ".sig", ".asc"
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    for p in DIRS.values():
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def read_head(path, size=1024 * 1024):
    with open(path, "rb") as f:
        return f.read(size)

def read_zone_identifier(path):
    try:
        ads = str(path) + ":Zone.Identifier"
        with open(ads, "r", encoding="utf-8", errors="replace") as f:
            return f.read(4000)
    except Exception:
        return ""

def head_type(path, head):
    ext = path.suffix.lower()

    if head.startswith(b"%PDF-"):
        return "PDF"
    if head.startswith(b"PK\x03\x04"):
        if ext == ".docx":
            return "DOCX"
        if ext == ".xlsx":
            return "XLSX"
        if ext == ".pptx":
            return "PPTX"
        if ext in {".odt", ".ods", ".odp"}:
            return "OPENDOCUMENT"
        return "ZIP_CONTAINER"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if head.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    try:
        head.decode("utf-8")
        return "TEXT"
    except Exception:
        return "UNBEKANNT"

def signature_evidence(path, head):
    ext = path.suffix.lower()
    low = head.lower()
    findings = []

    if ext in SIGNED_CONTAINER_EXT:
        findings.append("Signatur- oder Nachrichtencontainer anhand Dateiendung erkannt.")

    if ext == ".eml":
        if b"multipart/signed" in low:
            findings.append("E-Mail enthält Hinweis auf multipart/signed.")
        if b"application/pkcs7-signature" in low or b"application/x-pkcs7-signature" in low:
            findings.append("E-Mail enthält Hinweis auf PKCS7-Signatur.")
        if b"smime.p7s" in low or b"smime.p7m" in low:
            findings.append("E-Mail enthält Hinweis auf S/MIME-Anlage.")

    if ext == ".pdf":
        if b"/byterange" in low and b"/sig" in low:
            findings.append("PDF enthält Hinweis auf eingebettete Signatur.")

    if ext == ".xml":
        if b"<signature" in low or b"xmldsig" in low:
            findings.append("XML enthält Hinweis auf XML-Signatur.")

    return findings

def windows_security_probe(path):
    result = {
        "defender_available": False,
        "defender_scan_started": False,
        "defender_error": "PowerShell-Helfer nicht ausgeführt.",
        "authenticode_available": False,
        "authenticode_status": "",
        "authenticode_status_message": "",
        "signer_subject": "",
        "signer_issuer": "",
        "signer_thumbprint": "",
        "signer_not_before": "",
        "signer_not_after": "",
        "authenticode_error": ""
    }

    if not HELPER.exists():
        result["defender_error"] = "PowerShell-Helfer fehlt: " + str(HELPER)
        return result

    try:
        p = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(HELPER),
                "-Path",
                str(path)
            ],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        out = (p.stdout or "").strip()
        if not out:
            result["defender_error"] = "PowerShell-Helfer lieferte keine Ausgabe."
            return result

        last = out.splitlines()[-1]
        data = json.loads(last)

        for k, v in data.items():
            result[k] = v

        if p.returncode != 0 and not result.get("defender_error"):
            result["defender_error"] = "PowerShell-Helfer Exitcode: " + str(p.returncode)

    except Exception as e:
        result["defender_error"] = repr(e)

    return result

def classify(path):
    ext = path.suffix.lower()
    suffixes = [s.lower() for s in path.suffixes]
    size = path.stat().st_size
    head = read_head(path)
    dtype = head_type(path, head)
    zone = read_zone_identifier(path)
    sig_findings = signature_evidence(path, head)
    probe = windows_security_probe(path)

    status = "SICHERHEIT_FREIGEGEBEN_VORZIMMER"
    risk = "niedrig"
    reasons = []

    if size == 0:
        status = "TECHNISCH_GESPERRT"
        risk = "hoch"
        reasons.append("Datei ist leer.")

    if ext in ACTIVE_EXT:
        status = "TECHNISCH_GESPERRT"
        risk = "hoch"
        reasons.append("Aktive oder ausführbare Dateiendung.")

    if len(suffixes) >= 2 and suffixes[-1] in ACTIVE_EXT:
        status = "TECHNISCH_GESPERRT"
        risk = "hoch"
        reasons.append("Doppelte Dateiendung mit ausführbarem Endtyp.")

    if dtype == "ZIP_CONTAINER":
        status = "TECHNISCH_UNKLAR_QUARANTAENE"
        risk = "mittel"
        reasons.append("ZIP-Container ohne freigegebene Dokumentenendung.")

    if ext not in SAFE_DOC_EXT and ext not in ACTIVE_EXT and ext not in SIGNED_CONTAINER_EXT:
        status = "TECHNISCH_UNKLAR_QUARANTAENE"
        risk = "mittel"
        reasons.append("Dateityp nicht in sicherer Dokumentenliste.")

    if sig_findings:
        if status != "TECHNISCH_GESPERRT":
            status = "SIGNATURPRUEFUNG_ERFORDERLICH"
            risk = "mittel"
        reasons.extend(sig_findings)
        reasons.append("Signatur wurde erkannt oder vermutet, aber noch nicht fachlich vollständig validiert.")

    if not probe.get("defender_available"):
        if status not in {"TECHNISCH_GESPERRT", "SIGNATURPRUEFUNG_ERFORDERLICH"}:
            status = "TECHNISCH_UNKLAR_QUARANTAENE"
            risk = "mittel"
        reasons.append("Windows-Defender-Prüfung nicht verfügbar.")

    elif not probe.get("defender_scan_started"):
        if status not in {"TECHNISCH_GESPERRT", "SIGNATURPRUEFUNG_ERFORDERLICH"}:
            status = "TECHNISCH_UNKLAR_QUARANTAENE"
            risk = "mittel"
        reasons.append("Windows-Defender-Prüfung konnte nicht gestartet werden.")

    if probe.get("authenticode_status") == "Valid":
        reasons.append("Authenticode-Signatur ist laut Windows gültig.")
    elif probe.get("authenticode_status"):
        reasons.append("Authenticode-Status: " + str(probe.get("authenticode_status")))

    if zone:
        reasons.append("Zone.Identifier vorhanden.")

    if not reasons:
        reasons.append("Keine Sperrregel ausgelöst. Defender-Prüfung wurde angestoßen.")

    return {
        "extension": ext,
        "size_bytes": size,
        "detected_type": dtype,
        "zone_identifier": zone,
        "signature_evidence": " | ".join(sig_findings),
        "risk_level": risk,
        "security_status": status,
        "reason": " ".join(reasons),
        "defender_available": probe.get("defender_available"),
        "defender_scan_started": probe.get("defender_scan_started"),
        "defender_error": probe.get("defender_error", ""),
        "authenticode_status": probe.get("authenticode_status", ""),
        "authenticode_status_message": probe.get("authenticode_status_message", ""),
        "signer_subject": probe.get("signer_subject", ""),
        "signer_issuer": probe.get("signer_issuer", ""),
        "signer_thumbprint": probe.get("signer_thumbprint", ""),
        "signer_not_before": probe.get("signer_not_before", ""),
        "signer_not_after": probe.get("signer_not_after", ""),
        "authenticode_error": probe.get("authenticode_error", "")
    }

def safe_name(intake_id, name):
    clean = "".join(c if c.isalnum() or c in " ._-()" else "_" for c in name)
    return intake_id + "__" + clean

def recommendation(status):
    if status == "SICHERHEIT_FREIGEGEBEN_VORZIMMER":
        return "Vorzimmerentscheidung: Anwaltvorlage, Aktenzuordnung, Rückfrage oder Zurückweisung."
    if status == "SIGNATURPRUEFUNG_ERFORDERLICH":
        return "Nicht normal übernehmen. Signaturprüfung oder Absenderprüfung erforderlich."
    if status == "TECHNISCH_UNKLAR_QUARANTAENE":
        return "Nicht öffnen. Quarantäne, Rückfrage oder technische Nachprüfung."
    return "Nicht öffnen. Sperre, Rückfrage, Zurückweisung oder gesonderte technische Prüfung."

def target_dirs(status):
    if status == "SICHERHEIT_FREIGEGEBEN_VORZIMMER":
        return DIRS["geprueft"], DIRS["vorzimmer"]
    if status == "SIGNATURPRUEFUNG_ERFORDERLICH":
        return DIRS["signatur"], DIRS["signatur"]
    return DIRS["quarantaene"], DIRS["rueckfrage"]

def create_test_files():
    raw = DIRS["roh"]
    if any(p.is_file() and p.name != ".gitkeep" for p in raw.iterdir()):
        return

    (raw / "TEST_V2_001_ungefaehrlich.txt").write_text(
        "Testdatei fuer Sicherheitsgate V2. Keine echte Mandantendatei.\n",
        encoding="utf-8",
        newline="\n"
    )

    (raw / "TEST_V2_002_aktive_Datei.ps1").write_text(
        "Write-Host 'Diese Datei darf nicht in den normalen Bestand.'\n",
        encoding="utf-8",
        newline="\n"
    )

    (raw / "TEST_V2_003_signierte_mail_hinweis.eml").write_text(
        "From: test@example.invalid\n"
        "To: kanzlei@example.invalid\n"
        "Subject: Test signierte Nachricht\n"
        "MIME-Version: 1.0\n"
        "Content-Type: multipart/signed; protocol=\"application/pkcs7-signature\"; micalg=sha-256; boundary=\"abc\"\n"
        "\n"
        "--abc\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Nur Test. Keine echte Postsendung.\n"
        "--abc\n"
        "Content-Type: application/pkcs7-signature; name=smime.p7s\n"
        "\n"
        "TEST\n"
        "--abc--\n",
        encoding="utf-8",
        newline="\n"
    )

def process_file(path):
    digest = sha256_file(path)
    data = classify(path)
    intake_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_" + digest[:12]

    target_dir, card_dir = target_dirs(data["security_status"])
    target = target_dir / safe_name(intake_id, path.name)

    shutil.move(str(path), str(target))

    rec = {
        "intake_id": intake_id,
        "received_at": now(),
        "original_name": path.name,
        "stored_path": str(target),
        "sha256": digest,
        "size_bytes": data["size_bytes"],
        "extension": data["extension"],
        "detected_type": data["detected_type"],
        "zone_identifier": data["zone_identifier"],
        "signature_evidence": data["signature_evidence"],
        "risk_level": data["risk_level"],
        "security_status": data["security_status"],
        "reason": data["reason"],
        "defender_available": data["defender_available"],
        "defender_scan_started": data["defender_scan_started"],
        "defender_error": data["defender_error"],
        "authenticode_status": data["authenticode_status"],
        "authenticode_status_message": data["authenticode_status_message"],
        "signer_subject": data["signer_subject"],
        "signer_issuer": data["signer_issuer"],
        "signer_thumbprint": data["signer_thumbprint"],
        "signer_not_before": data["signer_not_before"],
        "signer_not_after": data["signer_not_after"],
        "authenticode_error": data["authenticode_error"],
        "decision_recommendation": recommendation(data["security_status"])
    }

    card = card_dir / f"{intake_id}_sicherheitskarte.json"
    card.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    rec["security_card"] = str(card)

    security_report = DIRS["sicherheit"] / f"{intake_id}_sicherheitsbericht.json"
    security_report.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    rec["security_report"] = str(security_report)

    return rec

def main():
    ensure_dirs()

    if "--create-test" in sys.argv:
        create_test_files()

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    protocol = DIRS["protokolle"] / f"POSTEINGANG_SICHERHEITSGATE_V2_{ts}.txt"
    csv_file = DIRS["protokolle"] / f"POSTEINGANG_SICHERHEITSGATE_V2_{ts}.csv"
    jsonl_file = DIRS["protokolle"] / f"POSTEINGANG_SICHERHEITSGATE_V2_{ts}.jsonl"

    records = []

    for file in sorted(DIRS["roh"].iterdir()):
        if file.is_file() and file.name != ".gitkeep":
            try:
                records.append(process_file(file))
            except Exception as e:
                records.append({
                    "intake_id": "FEHLER",
                    "received_at": now(),
                    "original_name": file.name,
                    "stored_path": str(file),
                    "sha256": "",
                    "size_bytes": file.stat().st_size if file.exists() else 0,
                    "extension": file.suffix.lower(),
                    "detected_type": "FEHLER",
                    "zone_identifier": "",
                    "signature_evidence": "",
                    "risk_level": "hoch",
                    "security_status": "FEHLER_BEI_SICHERHEITSPRUEFUNG",
                    "reason": repr(e),
                    "defender_available": "",
                    "defender_scan_started": "",
                    "defender_error": "",
                    "authenticode_status": "",
                    "authenticode_status_message": "",
                    "signer_subject": "",
                    "signer_issuer": "",
                    "signer_thumbprint": "",
                    "signer_not_before": "",
                    "signer_not_after": "",
                    "authenticode_error": "",
                    "decision_recommendation": "Nicht öffnen. Sicherheitsprüfung fehlgeschlagen.",
                    "security_card": "",
                    "security_report": ""
                })

    fields = [
        "intake_id", "received_at", "original_name", "stored_path", "sha256",
        "size_bytes", "extension", "detected_type", "zone_identifier",
        "signature_evidence", "risk_level", "security_status", "reason",
        "defender_available", "defender_scan_started", "defender_error",
        "authenticode_status", "authenticode_status_message",
        "signer_subject", "signer_issuer", "signer_thumbprint",
        "signer_not_before", "signer_not_after", "authenticode_error",
        "decision_recommendation", "security_card", "security_report"
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, "") for k in fields})

    with open(jsonl_file, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(protocol, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG SICHERHEITSGATE V2\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + now() + "\n")
        f.write("Verarbeitete Dateien: " + str(len(records)) + "\n\n")

        for k, v in DIRS.items():
            f.write(k + ": " + str(v) + "\n")

        f.write("\nERGEBNISSE\n")
        f.write("-" * 80 + "\n")
        for r in records:
            f.write(
                f"{r.get('intake_id')} | {r.get('original_name')} | "
                f"{r.get('security_status')} | {r.get('risk_level')} | "
                f"{r.get('authenticode_status')} | Defender={r.get('defender_scan_started')}\n"
            )

    print("")
    print("POSTEINGANG_SICHERHEITSGATE_V2 FERTIG")
    print("Protokoll:", protocol)
    print("CSV:", csv_file)
    print("JSONL:", jsonl_file)
    print("Verarbeitete Dateien:", len(records))

if __name__ == "__main__":
    main()
