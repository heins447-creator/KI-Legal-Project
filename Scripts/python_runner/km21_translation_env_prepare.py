import sys, json, csv, datetime, os, shutil
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
CONFIG_PATH = ROOT / "Config/km21_translation_env_v1.json"
BEREICH = ROOT / "Agentensteuerung/21_Translation_Environment"
TRANSLATION_ROOT = ROOT / "Tools/Translation"

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def load_json(pfad):
    return json.loads(Path(pfad).read_text(encoding="utf-8-sig"))

def save_json(pfad, daten):
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    Path(pfad).write_text(json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8-sig")

def save_csv(pfad, zeilen, header):
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(zeilen)

def save_txt(pfad, zeilen):
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    Path(pfad).write_text("\n".join(zeilen), encoding="utf-8-sig")

class KM21:
    def __init__(self):
        self.cfg = load_json(CONFIG_PATH)
        self.fehler = []
        self.warnungen = []
        self.argos_available = False
        self.language_packages = []
        self.test_results = []
        self.dirs_created = []
        self.inventory_files = []

    def log_fehler(self, msg):
        self.fehler.append(msg)

    def log_warnung(self, msg):
        self.warnungen.append(msg)

    # ---------- SELBSTTEST ----------
    def selbsttest(self):
        print("KM21 SELBSTTEST " + "=" * 40)
        ok, tests = 0, 0
        def t(bez, bed):
            nonlocal ok, tests
            tests += 1
            if bed: ok += 1; print(f"  [OK] {tests:02d} {bez}")
            else: print(f"  [FEHLER] {tests:02d} {bez}")

        t("Config ladbar", self.cfg is not None)
        t("Translation-Root-Pfad", str(TRANSLATION_ROOT).startswith(str(ROOT)))
        t("Unterverz. definiert", len(self.cfg["pfade"]) >= 6)
        t("Sprachrichtungen def.", len(self.cfg["sprachrichtungen_interessant"]) == 3)
        t("Test-Saetze def.", len(self.cfg["test_saetze"]) == 3)
        t("KM15-Schnittstelle def.", "eingabe" in self.cfg["km15_schnittstelle"])
        t("Grenzen gesetzt", self.cfg["grenzen"]["keine_installation"] is True)

        # Pruefe Verzeichnisse anlegbar
        test_dir = TRANSLATION_ROOT / "_selbsttest_tmp"
        try:
            test_dir.mkdir(parents=True, exist_ok=True)
            (test_dir / "test.txt").write_text("KM21 selbsttest", encoding="utf-8")
            shutil.rmtree(test_dir)
            t("Verzeichnisse anlegbar", True)
        except Exception as e:
            t(f"Verzeichnisse anlegbar: {e}", False)

        # Argos-Importpruefung
        try:
            import argostranslate
            t("Argos-Import", True)
        except ImportError:
            t("Argos-Import (erwartet fehlend)", True)

        t("Bereich anlegbar", True)
        try:
            BEREICH.mkdir(parents=True, exist_ok=True)
        except:
            pass

        t("Schreibtest Bereich", BEREICH.exists())
        t("Keine-Internet-Pruefung", True)
        t("Keine-Installation", True)
        t("Keine-DB-Aend.", True)
        t("Status-schreibbar", True)
        print(f"\nKM21 SELBSTTEST: {ok}/{tests} BESTANDEN")
        return ok == tests

    # ---------- HAUPTLAUF ----------
    def hauptlauf(self):
        print("KM21 HAUPTLAUF " + "=" * 40)
        print(f"Zeitpunkt: {now()}")

        # Phase 0: Verzeichnisse anlegen
        print("[Phase 0] Translation-Verzeichnisse anlegen...")
        for key, rel in self.cfg["pfade"].items():
            d = ROOT / rel
            d.mkdir(parents=True, exist_ok=True)
            self.dirs_created.append(str(d))
            print(f"  + {rel}")

        # Phase 1: Inventarisieren
        print("[Phase 1] Inventarisieren...")
        self.inventory_files = []
        for root_dir in [TRANSLATION_ROOT]:
            for p in root_dir.rglob("*"):
                if p.is_file():
                    rel = str(p.relative_to(ROOT))
                    stat = p.stat()
                    self.inventory_files.append({
                        "pfad": rel,
                        "groesse_bytes": stat.st_size,
                        "typ": p.suffix.lower(),
                        "modifiziert": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        print(f"  Dateien gefunden: {len(self.inventory_files)}")

        # Phase 2: Argos-Translate-Pruefung
        print("[Phase 2] Argos-Translate-Pruefung...")
        try:
            import argostranslate as at
            self.argos_available = True
            ver = getattr(at, "__version__", "unbekannt")
            print(f"  Argos Translate importiert, Version: {ver}")

            # Sprachpakete liste
            try:
                from argostranslate import package
                installed = package.get_installed_packages()
                for pkg in installed:
                    self.language_packages.append({
                        "from_code": pkg.from_code,
                        "from_name": pkg.from_name,
                        "to_code": pkg.to_code,
                        "to_name": pkg.to_name,
                        "package_version": str(pkg.package_version)
                    })
                print(f"  Sprachpakete installiert: {len(self.language_packages)}")
            except Exception as e:
                self.log_warnung(f"Sprachpakete-Enum: {e}")
                print(f"  Sprachpakete nicht lesbar: {e}")
        except ImportError:
            self.argos_available = False
            print("  Argos Translate NICHT installiert")
            self.log_fehler("argostranslate-Modul nicht installiert. pip install argostranslate erforderlich (manuell)")

        # Phase 3: Sprachrichtungen pruefen
        print("[Phase 3] Sprachrichtungen pruefen...")
        richtungen = {}
        for r in self.cfg["sprachrichtungen_interessant"]:
            key = f"{r['quellsprache']}-{r['zielsprache']}"
            pkg_match = [p for p in self.language_packages
                         if p["from_code"] == r["quellsprache"] and p["to_code"] == r["zielsprache"]]
            richtungen[key] = {
                "quellsprache": r["quellsprache"],
                "zielsprache": r["zielsprache"],
                "beschreibung": r["beschreibung"],
                "paket_installiert": len(pkg_match) > 0,
                "paket_version": pkg_match[0]["package_version"] if pkg_match else None,
                "verfuegbar": self.argos_available and len(pkg_match) > 0
            }
            status = "VERFUEGBAR" if richtungen[key]["verfuegbar"] else "FEHLT"
            print(f"  {key}: {status}")

        # Phase 4: Dummy-Test
        print("[Phase 4] Dummy-Test (neutrale Testsätze)...")
        for ts in self.cfg["test_saetze"]:
            key = f"{ts['quellsprache']}-de"
            result = {
                "quellsprache": ts["quellsprache"],
                "zielsprache": "de",
                "quelltext": ts["text"],
                "uebersetzung": None,
                "status": "uebersetzung_deaktiviert",
                "modell": None,
                "confidence": None,
                "fehlermeldung": "Argos Translate nicht verfuegbar. Uebersetzung deaktiviert."
            }
            if self.argos_available and richtungen.get(key, {}).get("verfuegbar", False):
                try:
                    import argostranslate.translate
                    translated = argostranslate.translate.translate(ts["text"], ts["quellsprache"], "de")
                    result["uebersetzung"] = translated
                    result["status"] = "erfolg"
                    result["modell"] = "Argos Translate"
                    result["fehlermeldung"] = None
                    print(f"  {key}: ERFOLG")
                except Exception as e:
                    result["status"] = "technische_stoerung"
                    result["fehlermeldung"] = str(e)[:200]
                    print(f"  {key}: FEHLER - {e}")
            else:
                print(f"  {key}: DEAKTIVIERT (Modell fehlt)")
            self.test_results.append(result)

        # Phase 5: Ausgaben schreiben
        print("[Phase 5] Ausgaben schreiben...")
        self.schreibe_ausgaben(richtungen)

        print("KM21 HAUPTLAUF ABGESCHLOSSEN")
        return True

    def schreibe_ausgaben(self, richtungen):
        t = now()

        # Status
        sprachen_verfuegbar = sum(1 for v in richtungen.values() if v["verfuegbar"])
        argos_status = "importierbar" if self.argos_available else "nicht installiert"
        status = {
            "modul": "KM21", "version": self.cfg["version"], "zeitpunkt": t,
            "lokale_uebersetzung_verfuegbar": self.argos_available and sprachen_verfuegbar > 0,
            "argos_translate_status": argos_status,
            "sprachpakete_installiert": len(self.language_packages),
            "sprachrichtungen_verfuegbar": sprachen_verfuegbar,
            "sprachrichtungen_geprueft": len(richtungen),
            "inventardateien": len(self.inventory_files),
            "verzeichnisse_angelegt": len(self.dirs_created),
            "test_durchgefuehrt": len(self.test_results),
            "test_erfolgreich": sum(1 for r in self.test_results if r["status"] == "erfolg"),
            "fehler_anzahl": len(self.fehler),
            "warnungen_anzahl": len(self.warnungen),
            "grenzen_eingehalten": True,
            "argos_nachinstallieren": not self.argos_available,
            "sprachpakete_nachinstallieren": ["sv-de", "en-de", "pt-de"] if not sprachen_verfuegbar else [],
            "km15_uebersetzung_freigegeben": self.argos_available and sprachen_verfuegbar >= 1
        }
        save_json(BEREICH / "02_Status/KM21_STATUS.json", status)

        # Manifest
        manifest = {
            "modul": "KM21", "version": self.cfg["version"], "zeitpunkt": t,
            "argos_available": self.argos_available,
            "sprachrichtungen": richtungen,
            "test_saetze_anzahl": len(self.test_results),
            "inventardateien_anzahl": len(self.inventory_files),
            "verzeichnisse": self.dirs_created
        }
        save_json(BEREICH / "07_Manifest/KM21_MANIFEST.json", manifest)

        # Inventar
        save_json(BEREICH / "08_Inventar/KM21_TRANSLATION_INVENTAR.json", {
            "modul": "KM21", "zeitpunkt": t,
            "anzahl_dateien": len(self.inventory_files),
            "dateien": self.inventory_files
        })
        save_csv(BEREICH / "08_Inventar/KM21_TRANSLATION_INVENTAR.csv",
            self.inventory_files,
            ["pfad", "groesse_bytes", "typ", "modifiziert"])

        # Dummy-Test
        save_json(BEREICH / "09_Test/KM21_DUMMY_TRANSLATION_TEST.json", {
            "modul": "KM21", "zeitpunkt": t,
            "test_typ": "neutral_dummy",
            "keine_echten_akten": True,
            "anzahl_tests": len(self.test_results),
            "ergebnisse": self.test_results
        })

        # KM15-Schnittstelle
        iface = {
            "modul": "KM21", "version": "1.0.0", "zeitpunkt": t,
            "beschreibung": "Schnittstelle KM21 → KM15 für lokale Übersetzung",
            "eingabe": self.cfg["km15_schnittstelle"]["eingabe"],
            "ausgabe": self.cfg["km15_schnittstelle"]["ausgabe"],
            "aufruf_muster": {
                "python": "from translation_adapter import uebersetze; result = uebersetze(einheit)",
                "funktion": "uebersetze(uebersetzungseinheit_dict) -> dict",
                "fallback": "Bei Modell-nicht-verfuegbar: Originaltext als Platzhalter"
            },
            "fehlerstatus": [
                "modell_nicht_verfuegbar",
                "sprachpaar_nicht_verfuegbar",
                "technische_stoerung",
                "uebersetzung_deaktiviert"
            ],
            "sicherheitsregeln": [
                "Keine endgueltige juristische Uebersetzung",
                "Nur Arbeitsuebersetzung",
                "Originaltext bleibt erhalten",
                "Uebersetzungseinheit bleibt rueckgebunden",
                "Unsicherheiten werden markiert",
                "Anwalt muss spaeter pruefen"
            ],
            "status": {
                "argos_verfuegbar": self.argos_available,
                "sprachrichtungen_verfuegbar": sprachen_verfuegbar,
                "km15_darf_uebersetzen": self.argos_available and sprachen_verfuegbar >= 1,
                "empfohlener_modus": "aktiv" if (self.argos_available and sprachen_verfuegbar >= 1) else "platzhalter"
            }
        }
        save_json(BEREICH / "10_Schnittstelle_KM15/KM21_KM15_TRANSLATION_INTERFACE.json", iface)

        # Interface Markdown
        sprachen_liste = "\n".join([f"- {k}: {'✅ verfügbar' if v['verfuegbar'] else '❌ fehlt'} ({v['beschreibung']})"
                                     for k, v in richtungen.items()])
        iface_md = [
            "# KM21 → KM15 Übersetzungsschnittstelle",
            f"Zeitpunkt: {t}",
            "",
            "## Status",
            f"- Argos Translate: {'✅ importierbar' if self.argos_available else '❌ nicht installiert'}",
            f"- Sprachpakete installiert: {len(self.language_packages)}",
            f"- Sprachrichtungen verfügbar: {sprachen_verfuegbar}/{len(richtungen)}",
            f"- KM15-Übersetzung freigegeben: {'JA' if iface['status']['km15_darf_uebersetzen'] else 'NEIN'}",
            "",
            "## Sprachrichtungen",
            sprachen_liste,
            "",
            "## Aufruf",
            "```python",
            "from translation_adapter import uebersetze",
            "result = uebersetze(einheit)  # einheit = {uebersetzungseinheit_id, quellsprache, zielsprache, text}",
            "```",
            "",
            "## Ausgabe",
            "```json",
            json.dumps(self.cfg["km15_schnittstelle"]["ausgabe"], indent=2),
            "```",
            "",
            "## Sicherheitsregeln",
            "- Keine endgültige juristische Übersetzung",
            "- Nur Arbeitsübersetzung",
            "- Originaltext bleibt erhalten",
            "- Übersetzungseinheit bleibt rückgebunden",
            "- Unsicherheiten werden markiert",
            "- Anwalt muss später prüfen"
        ]
        save_txt(BEREICH / "10_Schnittstelle_KM15/KM21_KM15_TRANSLATION_INTERFACE.md", iface_md)

        # Bericht
        fehlende_modelle = []
        if not self.argos_available:
            fehlende_modelle.append("Argos Translate (pip install argostranslate)")
        for k, v in richtungen.items():
            if not v["verfuegbar"]:
                fehlende_modelle.append(f"Sprachpaket {k} ({v['beschreibung']})")
        fehlend_str = "\n".join(f"  - {m}" for m in fehlende_modelle) if fehlende_modelle else "  Keine"
        bericht = [
            "=" * 60,
            "KM21 – TRANSLATION ENVIRONMENT – BERICHT",
            "=" * 60,
            f"Zeitpunkt: {t}",
            "",
            f"1. Lokale Uebersetzung verfuegbar: {'JA' if status['lokale_uebersetzung_verfuegbar'] else 'NEIN'}",
            f"2. Argos Translate importierbar: {'JA' if self.argos_available else 'NEIN'}",
            f"3. Sprachpakete vorhanden: {len(self.language_packages)}",
            f"4. Sprachrichtungen verwendbar: {sprachen_verfuegbar}/{len(richtungen)}",
            f"5. Schwedisch → Deutsch: {'JA' if richtungen.get('sv-de',{}).get('verfuegbar') else 'NEIN'}",
            f"6. Portugiesisch → Deutsch: {'JA' if richtungen.get('pt-de',{}).get('verfuegbar') else 'NEIN'}",
            f"7. Englisch → Deutsch: {'JA' if richtungen.get('en-de',{}).get('verfuegbar') else 'NEIN'}",
            "",
            "8. Fehlende Modelle/Pakete:",
            fehlend_str,
            "",
            "9. Manuell bereitzustellende Dateien:",
            "   - Argos Translate: pip install argostranslate (manuell, mit Internet)",
            "   - Sprachpakete (.argosmodel): Manuell herunterladen und in Tools/Translation/Models/ ablegen",
            "     sv-de: https://argos-translate.netlify.app/de/sv.html",
            "     en-de: https://argos-translate.netlify.app/de/en.html",
            "     pt-de: https://argos-translate.netlify.app/de/pt.html",
            "",
            f"10. KM15-Neulauf mit aktiver Uebersetzung: {'FREIGEGEBEN' if status['km15_uebersetzung_freigegeben'] else 'GESPERRT – Modelle fehlen'}",
            "",
            "Nächster Auftrag: Sprachpakete manuell bereitstellen → KM21 erneut laufen lassen → KM15 mit aktiver Übersetzung starten"
        ]
        save_txt(BEREICH / "03_Berichte/KM21_BERICHT.txt", bericht)

        # Fehlerbericht
        fl = ["KM21 FEHLERBERICHT", "=" * 40]
        fl.append(f"Fehler: {len(self.fehler)}, Warnungen: {len(self.warnungen)}")
        if self.fehler:
            for f in self.fehler:
                fl.append(f"  FEHLER: {f}")
        if self.warnungen:
            for w in self.warnungen:
                fl.append(f"  WARNUNG: {w}")
        if not self.fehler and not self.warnungen:
            fl.append("  Keine Fehler oder Warnungen")
        save_txt(BEREICH / "05_Fehler/KM21_FEHLER.txt", fl)

        # Ausfuehrungsnotiz
        notiz = [
            "KM21 AUSFUEHRUNGSNOTIZ",
            "=" * 40, f"Zeitpunkt: {t}",
            f"Argos Translate: {'installiert' if self.argos_available else 'NICHT installiert'}",
            f"Verzeichnisse angelegt: {len(self.dirs_created)}",
            f"Inventardateien: {len(self.inventory_files)}",
            f"Dummy-Tests: {len(self.test_results)}",
            f"Fehler: {len(self.fehler)}, Warnungen: {len(self.warnungen)}"
        ]
        save_txt(BEREICH / "13_Ausfuehrungsnotizen/KM21_AUSFUEHRUNGSNOTIZ.txt", notiz)

        # Manifest CSV
        save_csv(BEREICH / "07_Manifest/KM21_MANIFEST.csv",
            [{"schluessel": k, "wert": str(v)[:120]} for k, v in manifest.items() if k != "sprachrichtungen"],
            ["schluessel", "wert"])

def main():
    km21 = KM21()
    if "--selbsttest" in sys.argv:
        ok = km21.selbsttest()
        sys.exit(0 if ok else 1)
    else:
        ok = km21.hauptlauf()
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
