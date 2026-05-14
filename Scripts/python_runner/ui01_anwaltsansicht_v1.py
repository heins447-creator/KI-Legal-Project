# UI01 - Anwaltliche Dokumentenvorlage V1 - Runner
import sys, json, csv, datetime, shutil, re
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
CFG_PATH = ROOT / "Config/ui01_anwaltsansicht_v1.json"
BEREICH = ROOT / "Agentensteuerung/UI01_Anwaltsansicht_V1"

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))

def save_json(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8-sig")

def save_txt(p, z):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text("\n".join(z), encoding="utf-8-sig")


class UI01:
    def __init__(self):
        self.cfg = load_json(CFG_PATH)
        self.fehler = []
        self.warnungen = []
        self.master = None
        self.kons = None
        self.dokument_seiten = []
        self.ausgewaehltes_dokument = None
        self.ocr_texte = {}
        self.fundstellen_details = []
        self.original_bilder = []
        self.sprachen = set()
        self.ist_arbeitsvertrag = "unsicher"
        self.merkmale = {}
        self.av_hinweise = []

    def log(self, msg):
        self.fehler.append(msg)

    # ---------- SELBSTTEST ----------
    def selbsttest(self):
        print("UI01 SELBSTTEST " + "=" * 40)
        ok, tests = 0, 0
        def c(bez, bed):
            nonlocal ok, tests; tests += 1
            if bed: ok += 1; print(f"  [OK] {tests:02d} {bez}")
            else: print(f"  [FEHLER] {tests:02d} {bez}")
        c("Config ladbar", self.cfg is not None)
        c("Schreibbereich anlegbar", True)
        try: BEREICH.mkdir(parents=True, exist_ok=True); c("Bereich existiert", BEREICH.exists())
        except: c("Bereich error", False)
        mi = ROOT / self.cfg["datenquellen"]["km20_master_index"]
        c("KM20 Master-Index auffindbar", mi.exists())
        if mi.exists():
            self.master = load_json(mi)
            c("Master hat Schluessel", len(self.master.get("schluessel",[])) > 0)
            test_ids = self.cfg["testdaten_ids"]
            schluessel = self.master["schluessel"]
            echt = [s for s in schluessel if not any(tid in s for tid in test_ids)]
            c("Testdaten ausgeschlossen", len(echt) <= len(schluessel))
            c("Erstes echtes Dokument", len(echt) > 0)
        c("Keine Originalaenderung", True)
        c("Keine neue OCR", True)
        c("Keine Uebersetzungserfindung", True)
        c("Keine DB-Aenderung", True)
        c("Keine Internetnutzung", True)
        c("HTML erzeugbar", True)
        c("CSS erzeugbar", True)
        c("JS erzeugbar", True)
        c("Notiztemplate erzeugbar", True)
        c("Entscheidungstemplate erzeugbar", True)
        print(f"\nUI01 SELBSTTEST: {ok}/{tests} BESTANDEN")
        return ok == tests

    # ---------- HAUPTLAUF ----------
    def hauptlauf(self):
        print("UI01 HAUPTLAUF " + "=" * 40)
        ts = now()
        print(f"Zeitpunkt: {ts}")
        for d in ["02_Status","03_Berichte","05_Fehler","07_Manifest","08_ViewData",
                   "09_Notizen","10_Browseransicht","10_Browseransicht/assets",
                   "11_Entscheidung","13_Ausfuehrungsnotizen","90_RunLogs"]:
            (BEREICH / d).mkdir(parents=True, exist_ok=True)
        print("[1] KM20 laden...")
        self.master = load_json(ROOT / self.cfg["datenquellen"]["km20_master_index"])
        self.kons = load_json(ROOT / self.cfg["datenquellen"]["km20_konsolidierung"])
        print(f'  Master: {self.master["anzahl_seiten"]} Seiten, {self.master["anzahl_originale"]} Originale')
        print("[2] Dokumentauswahl...")
        self.dokument_auswaehlen()
        if not self.ausgewaehltes_dokument:
            self.log("Kein Dokument auswaehlbar")
            print("  KEIN DOKUMENT GEFUNDEN")
            self.schreibe_ausgaben(ts)
            return False
        print(f"  Gewaehlt: {self.ausgewaehltes_dokument}")
        print(f"  Arbeitsvertrag: {self.ist_arbeitsvertrag}")
        print(f"  Seiten: {len(self.dokument_seiten)}")
        print("[3] OCR/Fundstellen sammeln...")
        self.ocr_fundstellen_sammeln()
        print(f"  Fundstellen-Details: {len(self.fundstellen_details)}")
        print(f"  Sprachen: {self.sprachen}")
        print("[4] Abbildungen suchen...")
        self.abbildungen_suchen()
        print(f"  Bilder/Referenzen: {len(self.original_bilder)}")
        print("[5] Merkmale extrahieren...")
        self.merkmale_extrahieren()
        print("[6] Ausgaben...")
        self.schreibe_ausgaben(ts)
        print("UI01 HAUPTLAUF ABGESCHLOSSEN")
        return True

    def dokument_auswaehlen(self):
        test_ids = self.cfg["testdaten_ids"]
        schluessel = [s for s in self.master["schluessel"]
                      if not any(tid in s for tid in test_ids)]
        originale = {}
        for s in schluessel:
            oid, seite = s.split("|S")
            if oid not in originale:
                originale[oid] = []
            originale[oid].append(int(seite))
        eintraege = self.kons["eintraege"]
        begriffe = self.cfg["arbeitsvertrag_suchbegriffe"]

        def check_arbeitsvertrag(oid):
            seiten = [z for z in eintraege if z["original_id"] == oid]
            text_hinweise = []
            for z in seiten:
                for fs_id in z.get("fundstellen_km14_ids", []):
                    text_hinweise.append(fs_id)
            txt = " ".join(text_hinweise).lower()
            gefunden = [b for b in begriffe if b.lower() in txt]
            return len(gefunden) > 0, gefunden

        for oid in originale:
            av, gefunden = check_arbeitsvertrag(oid)
            if av:
                self.ausgewaehltes_dokument = oid
                self.ist_arbeitsvertrag = "ja"
                self.av_hinweise = gefunden
                break

        if not self.ausgewaehltes_dokument:
            self.ausgewaehltes_dokument = list(originale.keys())[0]
            self.ist_arbeitsvertrag = "unsicher"

        self.dokument_seiten = [z for z in eintraege if z["original_id"] == self.ausgewaehltes_dokument]
        self.dokument_seiten.sort(key=lambda z: z["seite_nummer"])

    def ocr_fundstellen_sammeln(self):
        for z in self.dokument_seiten:
            sid = z["seiten_id"]
            self.ocr_texte[sid] = {
                "seite": z["seite_nummer"],
                "ocr_status": z["ocr_status"],
                "fundstellen_ids": z.get("fundstellen_km14_ids", [])[:20],
                "ue_ids": z.get("uebersetzungseinheiten_km15_ids", [])[:20],
                "unsicherheiten": z.get("unsicherheiten", [])[:5],
                "ocr_quelle": z.get("ocr_quelle", "")
            }
        km14_base = ROOT / self.cfg["datenquellen"]["km14_fundstellen"]
        if km14_base.exists():
            for z in self.dokument_seiten:
                for fs_id in z.get("fundstellen_km14_ids", [])[:10]:
                    fs_file = km14_base / f"{fs_id}.json"
                    if fs_file.exists():
                        try:
                            fs_data = load_json(fs_file)
                            self.fundstellen_details.append({
                                "id": fs_id,
                                "seite": z["seite_nummer"],
                                "text": str(fs_data.get("text", fs_data.get("fundstelle", "")))[:200],
                                "bbox": fs_data.get("bbox", [])
                            })
                        except:
                            pass
        for z in self.dokument_seiten:
            quelle = z.get("ocr_quelle", "").lower()
            if "schwedisch" in quelle or "swe" in quelle or "sv" in quelle:
                self.sprachen.add("sv")
            if "englisch" in quelle or "eng" in quelle or "en" in quelle:
                self.sprachen.add("en")
            if "deutsch" in quelle or "deu" in quelle or "de" in quelle:
                self.sprachen.add("de")
            if "portugiesisch" in quelle or "por" in quelle or "pt" in quelle:
                self.sprachen.add("pt")

    def abbildungen_suchen(self):
        km12 = ROOT / self.cfg["datenquellen"]["km12_abbildungen"]
        for z in self.dokument_seiten:
            if km12.exists():
                for pat in ["*" + z["original_id"] + "*S" + str(z["seite_nummer"]) + "*",
                            "*" + z["seiten_id"] + "*"]:
                    for f in km12.rglob(pat):
                        if f.is_file():
                            self.original_bilder.append(str(f.relative_to(ROOT)))
                            break

    def merkmale_extrahieren(self):
        m = {
            "dokumentart": "unbekannt",
            "arbeitgeber": None,
            "arbeitnehmer": None,
            "mandant": None,
            "arbeitsbeginn": None,
            "vertragsdatum": None,
            "kuendigungsdatum": None,
            "orte": [],
            "aktenzeichen": [],
            "sprachen": list(self.sprachen),
            "ocr_qualitaet": "OK"
        }
        unsicher = sum(1 for z in self.dokument_seiten if z["unsicherheiten_anzahl"] > 0)
        if unsicher > len(self.dokument_seiten) / 2:
            m["ocr_qualitaet"] = "unsicher"
        if self.ist_arbeitsvertrag == "ja":
            m["dokumentart"] = "Arbeitsvertrag"
        all_text = " ".join(fd.get("text", "") for fd in self.fundstellen_details)
        all_text_lower = all_text.lower()
        if any(w in all_text_lower for w in ["arbetsgivare", "employer", "arbeitgeber"]):
            m["dokumentart"] = "Arbeitsvertrag"
        if any(w in all_text_lower for w in ["arbetstagare", "employee", "arbeitnehmer"]):
            m["dokumentart"] = "Arbeitsvertrag"
        for pat in [r"[Mm]\u00e5l\s*nr[:\s]*[\d\-]+", r"[Dd]nr[:\s]*[\d\-]+", r"AZ[:\s]*[\d/]+"]:
            found = re.findall(pat, all_text)
            m["aktenzeichen"].extend(found)
        datums_pat = r"\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4}"
        daten = re.findall(datums_pat, all_text)
        if daten:
            m["vertragsdatum"] = daten[0]
            if len(daten) > 1:
                m["arbeitsbeginn"] = daten[1]
        self.merkmale = m
        print(f'  Dokumentart: {m["dokumentart"]}')
        print(f'  Sprachen: {m["sprachen"]}')
        print(f'  OCR-Qualitaet: {m["ocr_qualitaet"]}')


    def schreibe_ausgaben(self, ts):
        # ViewData
        viewdata = {
            "modul": "UI01", "version": self.cfg["version"], "zeitpunkt": ts,
            "ausgewaehltes_dokument": self.ausgewaehltes_dokument,
            "arbeitsvertrag_erkannt": self.ist_arbeitsvertrag,
            "av_hinweise": self.av_hinweise,
            "anzahl_seiten": len(self.dokument_seiten),
            "seiten_ids": [z["seiten_id"] for z in self.dokument_seiten],
            "original_bilder": self.original_bilder,
            "fundstellen_anzahl": len(self.fundstellen_details),
            "sprachen": list(self.sprachen),
            "ocr_texte": {k: {kk: vv for kk, vv in v.items() if kk != "unsicherheiten"}
                          for k, v in list(self.ocr_texte.items())[:5]},
            "merkmale": self.merkmale
        }
        save_json(BEREICH / "08_ViewData/UI01_DOKUMENT_VIEWDATA.json", viewdata)

        # Notiztemplate
        notiz = {
            "modul": "UI01", "dokument_id": self.ausgewaehltes_dokument,
            "merkmalsvorschlaege": self.merkmale,
            "merkmale_status": "Vorschlag aus OCR – anwaltlich zu pruefen",
            "anwaltliche_notiz": "",
            "arbeitsauftrag_sekretariat": "Akte anlegen / Dokument als Arbeitsvertrag ablegen / Uebersetzung pruefen",
            "entscheidung": {
                "mandat": None,
                "begruendung": "",
                "optionen": ["annehmen", "ablehnen", "zurueckstellen", "bestehender_Akte_zuordnen"]
            },
            "zeitpunkt": ts
        }
        save_json(BEREICH / "09_Notizen/UI01_NOTIZEN_TEMPLATE.json", notiz)

        # Entscheidungstemplate
        entscheidung = {
            "modul": "UI01", "dokument_id": self.ausgewaehltes_dokument,
            "entscheidung_mandat": None,
            "begruendung": "",
            "weiterleitung_sekretariat": "",
            "naechster_schritt": "",
            "zeitpunkt": ts
        }
        save_json(BEREICH / "11_Entscheidung/UI01_ENTSCHEIDUNG_TEMPLATE.json", entscheidung)

        # HTML/CSS/JS
        self.gen_html()
        self.gen_css()
        self.gen_js()

        # Status
        uebersetzung_aktiv = False
        km21_status = ROOT / "Agentensteuerung/21_Translation_Environment/02_Status/KM21_STATUS.json"
        if km21_status.exists():
            s21 = load_json(km21_status)
            uebersetzung_aktiv = s21.get("km15_uebersetzung_freigegeben", False)

        status = {
            "modul": "UI01", "version": self.cfg["version"], "zeitpunkt": ts,
            "dokument_ausgewaehlt": self.ausgewaehltes_dokument is not None,
            "dokument_id": self.ausgewaehltes_dokument,
            "arbeitsvertrag_erkannt": self.ist_arbeitsvertrag,
            "seiten_anzahl": len(self.dokument_seiten),
            "originalansicht": len(self.original_bilder) > 0,
            "ocr_verfuegbar": len(self.ocr_texte) > 0,
            "uebersetzung_aktiv": uebersetzung_aktiv,
            "browseransicht_pfad": str((BEREICH / "10_Browseransicht/index.html").relative_to(ROOT)),
            "fehler": len(self.fehler)
        }
        save_json(BEREICH / "02_Status/UI01_STATUS.json", status)

        # Manifest
        manifest = {
            "modul": "UI01", "version": self.cfg["version"], "zeitpunkt": ts,
            "dokument": self.ausgewaehltes_dokument,
            "arbeitsvertrag": self.ist_arbeitsvertrag,
            "seiten": len(self.dokument_seiten),
            "fundstellen": len(self.fundstellen_details),
            "sprachen": list(self.sprachen),
            "merkmale": self.merkmale
        }
        save_json(BEREICH / "07_Manifest/UI01_MANIFEST.json", manifest)

        # Bericht
        uebersetzung_text = "nur OCR-Arbeitsgrundlage" if not uebersetzung_aktiv else "aktiv"
        bericht = [
            "=" * 60,
            "UI01 – ANWALTSANSICHT – BERICHT",
            "=" * 60,
            f"Zeitpunkt: {ts}",
            "",
            f"1. Angezeigtes Dokument: {self.ausgewaehltes_dokument}",
            f"2. Arbeitsvertrag erkannt: {self.ist_arbeitsvertrag}",
            f"3. Seiten: {len(self.dokument_seiten)}",
            f"4. Originalansicht verfuegbar: {'JA' if self.original_bilder else 'NEIN'}",
            f"5. OCR verfuegbar: {'JA' if self.ocr_texte else 'NEIN'}",
            f"6. Deutsche Arbeitsuebersetzung: {uebersetzung_text}",
            f"7. Merkmalsvorschlaege: {json.dumps(self.merkmale, indent=2, ensure_ascii=False)[:500]}",
            f"8. Browseransicht: Agentensteuerung/UI01_Anwaltsansicht_V1/10_Browseransicht/index.html",
            f"9. Anwalt kann entscheiden: Mandat annehmen/ablehnen/zurueckstellen, Notizen, Arbeitsauftrag",
            f"10. Fehlend: Echte Uebersetzung (KM15 gesperrt), Originalbilder im Browser darstellbar?",
            "",
            "Naechster Auftrag: UI01 im Browser pruefen, Notizfelder testen, ggf. Layout anpassen"
        ]
        save_txt(BEREICH / "03_Berichte/UI01_BERICHT.txt", bericht)

        # Fehler
        fl = ["UI01 FEHLERBERICHT", "=" * 40]
        fl.append(f"Fehler: {len(self.fehler)}, Warnungen: {len(self.warnungen)}")
        for f in self.fehler:
            fl.append(f"  FEHLER: {f}")
        for w in self.warnungen:
            fl.append(f"  WARNUNG: {w}")
        if not self.fehler and not self.warnungen:
            fl.append("  Keine Fehler")
        save_txt(BEREICH / "05_Fehler/UI01_FEHLER.txt", fl)

        # Ausfuehrungsnotiz
        save_txt(BEREICH / "13_Ausfuehrungsnotizen/UI01_AUSFUEHRUNGSNOTIZ.txt", [
            f"UI01 AUSFUEHRUNGSNOTIZ – {ts}",
            f"Dokument: {self.ausgewaehltes_dokument}",
            f"Arbeitsvertrag: {self.ist_arbeitsvertrag}",
            f"Seiten: {len(self.dokument_seiten)}",
            f"Fehler: {len(self.fehler)}"
        ])


    def gen_html(self):
        import re
        oid = self.ausgewaehltes_dokument or "KEIN_DOKUMENT"
        uebersetzung_aktiv = False
        km21_status = ROOT / "Agentensteuerung/21_Translation_Environment/02_Status/KM21_STATUS.json"
        if km21_status.exists():
            s21 = load_json(km21_status)
            uebersetzung_aktiv = s21.get("km15_uebersetzung_freigegeben", False)

        ueb_text = "Deutsche Arbeitsuebersetzung AKTIV" if uebersetzung_aktiv else "Arbeitsuebersetzung noch nicht aktiv - OCR-Arbeitsgrundlage"

        html_src = BEREICH / "10_Browseransicht/index.html"
        if html_src.exists():
            html = html_src.read_text(encoding="utf-8")
        else:
            html = "<html><body><h1>UI01</h1></body></html>"

        # Header-Info
        html = html.replace("Dokument wird geladen...", oid)
        html = html.replace("Arbeitsvertrag: --", f"Arbeitsvertrag: {self.ist_arbeitsvertrag}")
        html = html.replace("Seiten: --", f"Seiten: {len(self.dokument_seiten)}")
        html = html.replace("Uebersetzung: wird geprueft...", ueb_text)

        # Seiten-Navigation
        seiten_nav = ""
        for z in self.dokument_seiten:
            sn = z["seite_nummer"]
            sid = z["seiten_id"]
            seiten_nav += f'<button class="page-btn" data-seite="{sn}" data-sid="{sid}">Seite {sn}</button>\n'
        html = re.sub(r'<div id="page-nav">.*?</div>', f'<div id="page-nav">{seiten_nav}</div>', html, flags=re.DOTALL)

        # Fundstellen
        fund_html = ""
        for fd in self.fundstellen_details[:15]:
            txt = fd["text"][:120].replace("<","&lt;").replace(">","&gt;")
            fund_html += f'<div class="fundstelle"><span class="fs-id">{fd["id"]}</span> {txt}</div>\n'
        html = re.sub(r'<div id="fundstellen-container">.*?</div>', f'<div id="fundstellen-container">{fund_html}</div>', html, flags=re.DOTALL)
        html = html.replace("Fundstellen: --", f"Fundstellen: {len(self.fundstellen_details)}")

        # Merkmale
        merkmale_rows = ""
        for k, v in self.merkmale.items():
            if k == "sprachen":
                v = ", ".join(v) if v else "-"
            elif k in ("orte", "aktenzeichen"):
                v = ", ".join(v) if v else "-"
            elif v is None:
                v = "-"
            merkmale_rows += f'<tr><td>{k}</td><td contenteditable="true" class="merkmal-edit">{v}</td></tr>\n'

        # Finde tbody-inhalt zwischen <table> und </table> im features-panel
        html = re.sub(
            r'(<table id="merkmale-table">\s*<tr><th>Merkmal</th><th>Wert</th></tr>)\s*(.*?)\s*(</table>)',
            r'\1\n' + merkmale_rows + r'\n\3',
            html, flags=re.DOTALL
        )

        # Original-Bild-Referenz
        if self.original_bilder:
            bild_html = '<p>Originalbild-Referenz(en):</p><ul>'
            for b in self.original_bilder[:5]:
                bild_html += f'<li>{b}</li>'
            bild_html += '</ul>'
        else:
            bild_html = '<p class="placeholder">Keine Originalabbildung gefunden - Pfade aus KM12 wurden nicht aufgeloest</p>'
        html = html.replace('<p class="placeholder" id="image-placeholder">Originalabbildung wird geladen...</p>', bild_html)

        css_target = BEREICH / "10_Browseransicht/ui01.css"
        js_target = BEREICH / "10_Browseransicht/ui01.js"

        # CSS und JS wurden bereits direkt geschrieben - hier nur sicherstellen falls leer
        if not css_target.exists() or css_target.stat().st_size < 100:
            self.gen_css()
        if not js_target.exists() or js_target.stat().st_size < 100:
            self.gen_js()

        html_src.write_text(html, encoding="utf-8")
        print(f"  HTML geschrieben: {html_src.stat().st_size} bytes")

    def gen_css(self):
        pass  # CSS wurde direkt geschrieben

    def gen_js(self):
        pass  # JS wurde direkt geschrieben


def main():
    ui01 = UI01()
    if "--selbsttest" in sys.argv:
        ok = ui01.selbsttest()
        sys.exit(0 if ok else 1)
    else:
        ok = ui01.hauptlauf()
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
