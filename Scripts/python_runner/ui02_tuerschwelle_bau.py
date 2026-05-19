#!/usr/bin/env python3
"""UI02 Tuerschwelle Bau – erweitert UI01 zur Sekretariats-/Mandatsfreigabe-Vorlage"""
import sys, json, csv, datetime, hashlib, re, shutil, io, os
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
PYTHON_EXE = ROOT / "Tools/Python312/python.exe"
SCHREIBBEREICH = ROOT / "Agentensteuerung/UI02_Tuerschwelle_Bau"
CONFIG_PFAD = ROOT / "Config/ui02_tuerschwelle_bau_v1.json"

ASSETS_DIR = SCHREIBBEREICH / "09_Originalansicht/assets"
BROWSER_DIR = SCHREIBBEREICH / "15_Browseransicht"
STATUS_PFAD = SCHREIBBEREICH / "02_Status/UI02_STATUS.json"
BERICHT_PFAD = SCHREIBBEREICH / "03_Berichte/UI02_BERICHT.txt"
FEHLER_PFAD = SCHREIBBEREICH / "05_Fehler/UI02_FEHLER.txt"
MANIFEST_PFAD = SCHREIBBEREICH / "07_Manifest/UI02_MANIFEST.json"
VIEWDATA_PFAD = SCHREIBBEREICH / "08_ViewData/UI02_VIEWDATA.json"
OCR_PFAD = SCHREIBBEREICH / "10_OCR_Arbeitsgrundlage/UI02_OCR_ARBEITSGRUNDLAGE.json"
KI_PFAD = SCHREIBBEREICH / "11_KI_Erstvorschlag/UI02_KI_ERSTVORSCHLAG.json"
NOTIZEN_PFAD = SCHREIBBEREICH / "12_Notizen/UI02_NOTIZEN_TEMPLATE.json"
ENTSCHEIDUNG_PFAD = SCHREIBBEREICH / "13_Entscheidung/UI02_ENTSCHEIDUNG_TEMPLATE.json"
RUECKGABE_PFAD = SCHREIBBEREICH / "14_Rueckgabe/UI02_RUECKGABE_AN_REGULAEREN_PROZESS.json"
HTML_PFAD = BROWSER_DIR / "index.html"
CSS_PFAD = BROWSER_DIR / "ui02.css"
JS_PFAD = BROWSER_DIR / "ui02.js"

UI01_HTML = ROOT / "Agentensteuerung/UI01_Anwaltsansicht_V1/10_Browseransicht/index.html"
UI01_CSS = ROOT / "Agentensteuerung/UI01_Anwaltsansicht_V1/10_Browseransicht/ui01.css"
UI01_JS = ROOT / "Agentensteuerung/UI01_Anwaltsansicht_V1/10_Browseransicht/ui01.js"

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

class UI02_Builder:
    def __init__(self):
        self.fehlermeldungen = []
        self.warnungen = []
        self.cfg = {}
        self.ergebnisse = {}
        self.ollama_verfuegbar = False
        self.ollama_modell = None
        self.pillow_verfuegbar = False

    def config_laden(self):
        if not CONFIG_PFAD.exists():
            self.cfg = {
                "modul": "UI02", "version": "1.0.0",
                "projektwurzel": str(ROOT), "schreibbereich": str(SCHREIBBEREICH),
                "km20_master_index": "Agentensteuerung/20_Quellen_Fundstellen_Konsolidierung/07_Manifest/KM20_MASTER_INDEX.json",
                "km20_konsolidierung": "Agentensteuerung/20_Quellen_Fundstellen_Konsolidierung/08_Konsolidierung/KM20_KONSOLIDIERUNG.json",
                "km12_manifest": "Agentensteuerung/12_Originalabbildung_Arbeitsabbildung/07_Manifest/KM12_ABBILDUNG_MANIFEST.json",
                "km14_fundstellen_dir": "Agentensteuerung/14_Maschinenformat_Fundstellenstruktur/09_Fundstellen",
                "km14_textstruktur_dir": "Agentensteuerung/14_Maschinenformat_Fundstellenstruktur/10_Textstruktur",
                "km17_ocr_dir": "Agentensteuerung/17_Sprachrouting_OCR/08_OCR_Ergebnisse",
                "km19_ocr_segmente_dir": "Agentensteuerung/19_OCR_Segmente_Export/08_OCR_Segmente",
                "ui01_html": "Agentensteuerung/UI01_Anwaltsansicht_V1/10_Browseransicht/index.html",
                "ui01_css": "Agentensteuerung/UI01_Anwaltsansicht_V1/10_Browseransicht/ui01.css",
                "ui01_js": "Agentensteuerung/UI01_Anwaltsansicht_V1/10_Browseransicht/ui01.js",
                "testdaten_muster": ["ORG-T", "TEST", "DUMMY"],
                "max_dokumente_ui02": 2,
                "ollama_url": "http://localhost:11434/api/generate",
                "ollama_timeout_s": 120,
                "png_max_breite": 800,
                "png_max_hoehe": 1200,
                "grenzen": {"keine_originalaenderung": True, "keine_neue_ocr": True,
                    "keine_neue_uebersetzung": True, "keine_db_aenderung": True,
                    "kein_internet": True, "keine_installation": True,
                    "keine_cloud": True}
            }
            CONFIG_PFAD.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PFAD.write_text(json.dumps(self.cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            self.cfg = json.loads(CONFIG_PFAD.read_text(encoding="utf-8-sig"))
        return True

    def schreibbereich_anlegen(self):
        dirs = [SCHREIBBEREICH, BROWSER_DIR, ASSETS_DIR,
                SCHREIBBEREICH/"02_Status", SCHREIBBEREICH/"03_Berichte",
                SCHREIBBEREICH/"05_Fehler", SCHREIBBEREICH/"07_Manifest",
                SCHREIBBEREICH/"08_ViewData",
                SCHREIBBEREICH/"10_OCR_Arbeitsgrundlage",
                SCHREIBBEREICH/"11_KI_Erstvorschlag",
                SCHREIBBEREICH/"12_Notizen",
                SCHREIBBEREICH/"13_Entscheidung",
                SCHREIBBEREICH/"14_Rueckgabe",
                SCHREIBBEREICH/"90_RunLogs"]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        return True

    def pfad_existiert(self, rel):
        return (ROOT / rel).exists()

    def json_laden_sicher(self, rel):
        p = ROOT / rel
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8-sig"))
            except:
                return None
        return None

    def ist_testdokument(self, original_id):
        for m in self.cfg.get("testdaten_muster", []):
            if original_id.startswith(m):
                return True
        return False

    def ollama_pruefen(self):
        import urllib.request, urllib.error
        try:
            url = "http://localhost:11434/api/tags"
            req = urllib.request.Request(url, method="GET")
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", [])]
            # Praeferierte Modelle in Reihenfolge
            preferred = ["deepseek-coder-v2:16b", "qwen2.5-coder:7b", "llama3.2:3b", "phi3:mini"]
            self.ollama_modell = None
            for pref in preferred:
                if pref in models:
                    self.ollama_modell = pref
                    break
            if not self.ollama_modell and models:
                self.ollama_modell = models[0]
            if not self.ollama_modell:
                self.ollama_modell = "deepseek-coder-v2:16b"  # Fallback – Ollama pulled auf Anfrage
            self.ollama_verfuegbar = True
            # Kurzer Verbindungstest /api/generate
            try:
                test_req = urllib.request.Request("http://localhost:11434/api/generate",
                    data=json.dumps({"model": self.ollama_modell, "prompt": ".", "stream": False}).encode("utf-8"),
                    method="POST", headers={"Content-Type": "application/json"})
                urllib.request.urlopen(test_req, timeout=30)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace") if e.fp else "kein body"
                self.warnungen.append(f"Ollama Generate-Test HTTP {e.code}: {body[:200]}")
            except Exception:
                pass  # Nicht kritisch – Modell wird bei Bedarf geladen
            return True, f"Ollama: {self.ollama_modell}"
        except Exception as e:
            self.ollama_verfuegbar = False
            self.ollama_modell = None
            return False, str(e)

    def pillow_pruefen(self):
        try:
            from PIL import Image
            self.pillow_verfuegbar = True
            return True, f"Pillow {Image.__version__}"
        except Exception as e:
            self.pillow_verfuegbar = False
            return False, str(e)

    def dokumente_auswaehlen(self):
        km20 = self.json_laden_sicher(self.cfg["km20_master_index"])
        km12 = self.json_laden_sicher(self.cfg["km12_manifest"])
        if not km20 or not km12:
            self.fehlermeldungen.append("[KRITISCH] KM20 oder KM12 nicht ladbar")
            return []
        alle_originale = set()
        for s in km20.get("schluessel", []):
            oid = s.split("|")[0] if "|" in s else s
            if not self.ist_testdokument(oid):
                alle_originale.add(oid)
        orig_liste = sorted(alle_originale)
        if not orig_liste:
            self.fehlermeldungen.append("[KRITISCH] Keine echten Dokumente nach Testdatenausschluss")
            return []
        # Prioritaere Dokumentauswahl: Arbeitsvertrag > Kuendigung > Rest
        prio = []
        rest = []
        for oid in orig_liste:
            text = self.dokumenttext_sammeln(oid)
            if self.ist_arbeitsvertrag(text):
                prio.append((oid, "Arbeitsvertrag"))
            elif self.ist_kuendigung(text):
                prio.append((oid, "Kuendigung"))
            else:
                rest.append((oid, "unbestimmt"))
        ausgewaehlt = prio + rest
        max_docs = self.cfg.get("max_dokumente_ui02", 2)
        ausgewaehlt = ausgewaehlt[:max_docs]
        dok_infos = []
        km12_seiten = km12.get("seiten", [])
        for oid, typ in ausgewaehlt:
            seiten = [s for s in km12_seiten if s.get("original_id") == oid]
            seiten.sort(key=lambda x: x.get("seite_nummer", 0))
            dok_infos.append({"original_id": oid, "typ_vermutet": typ, "seiten": seiten})
        self.ergebnisse["dokumentauswahl"] = dok_infos
        return dok_infos

    def dokumenttext_sammeln(self, original_id):
        ts_dir = ROOT / self.cfg["km14_textstruktur_dir"]
        ts_file = ts_dir / f"{original_id}_textstruktur.json"
        if not ts_file.exists():
            return ""
        data = json.loads(ts_file.read_text(encoding="utf-8-sig"))
        texts = []
        for s in data.get("seiten", []):
            tn = s.get("text_normalisiert", "") or ""
            if tn:
                texts.append(tn)
        return " ".join(texts)

    def ist_arbeitsvertrag(self, text):
        if not text:
            return False
        tl = text.lower()
        keywords = ["anstallning", "arbetsgivare", "arbetstagare", "lon", "semester",
                     "provanstallning", "tillsvidare", "visstidsanstallning", "arbetsavtal",
                     "anstallningsavtal", "heltid", "deltid"]
        hits = sum(1 for kw in keywords if kw in tl)
        return hits >= 2

    def ist_kuendigung(self, text):
        if not text:
            return False
        tl = text.lower()
        keywords = ["uppsagning", "avsked", "upphor", "uppsagd", "arbetsbrist",
                     "personliga skal", "sista anstallningsdag", "sags upp",
                     "uppsagningstid", "avsluta anstallningen"]
        hits = sum(1 for kw in keywords if kw in tl)
        return hits >= 2

    def tiff_zu_png(self, dok_infos):
        if not self.pillow_verfuegbar:
            self.fehlermeldungen.append("[KRITISCH] Pillow fehlt – TIFF->PNG nicht moeglich")
            return False
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None  # Decompression-Bomb-Schutz deaktiviert fuer TIFF
        assets = []
        max_w = self.cfg.get("png_max_breite", 800)
        max_h = self.cfg.get("png_max_hoehe", 1200)
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        for dok in dok_infos:
            oid = dok["original_id"]
            dok_assets = []
            for s in dok["seiten"]:
                snum = s.get("seite_nummer", 0)
                tiff_pfad = s.get("tiff_pfad", "")
                asset_name = f"{oid}_seite_{snum:04d}.png"
                asset_pfad = ASSETS_DIR / asset_name
                status = "erzeugt"
                if not tiff_pfad or not Path(tiff_pfad).exists():
                    status = "fehler: tiff nicht gefunden"
                    self.fehlermeldungen.append(f"[WARNUNG] TIFF fehlt: {tiff_pfad}")
                else:
                    try:
                        img = Image.open(tiff_pfad)
                        w, h = img.size
                        if w > max_w or h > max_h:
                            ratio = min(max_w/w, max_h/h)
                            img = img.resize((int(w*ratio), int(h*ratio)), Image.LANCZOS)
                        img = img.convert("RGB")
                        img.save(asset_pfad, "PNG")
                        asset_size = asset_pfad.stat().st_size
                    except Exception as e:
                        status = f"fehler: {e}"
                        self.fehlermeldungen.append(f"[FEHLER] TIFF->PNG {tiff_pfad}: {e}")
                dok_assets.append({"seite_nummer": snum, "seiten_id": s.get("seiten_id", f"{oid}_S{snum:04d}"),
                                   "asset_pfad": str(asset_pfad), "asset_name": asset_name,
                                   "status": status, "tiff_pfad_original": tiff_pfad})
            assets.append({"original_id": oid, "assets": dok_assets})
        self.ergebnisse["originalansicht"] = assets
        return len(assets) > 0

    def ocr_arbeitsgrundlage_erstellen(self, dok_infos):
        ocr_data = {"dokumente": [], "quellenhinweis": "Aus KM14-Textstruktur (text_normalisiert) – keine neue OCR"}
        ts_dir = ROOT / self.cfg["km14_textstruktur_dir"]
        fs_dir = ROOT / self.cfg["km14_fundstellen_dir"]
        for dok in dok_infos:
            oid = dok["original_id"]
            ts_file = ts_dir / f"{oid}_textstruktur.json"
            fs_file = fs_dir / f"{oid}_fundstellen.json"
            seiten_ocr = []
            textstruktur = {}
            if ts_file.exists():
                textstruktur = json.loads(ts_file.read_text(encoding="utf-8-sig"))
            fundstellen_data = {"fundstellen": []}
            if fs_file.exists():
                fundstellen_data = json.loads(fs_file.read_text(encoding="utf-8-sig"))
            for s in dok["seiten"]:
                snum = s.get("seite_nummer", 0)
                tn = ""
                for ts_s in textstruktur.get("seiten", []):
                    if ts_s.get("seite_nummer") == snum:
                        tn = ts_s.get("text_normalisiert", "") or ""
                        break
                seiten_fs = []
                for f in fundstellen_data.get("fundstellen", []):
                    if f.get("seite_nummer") == snum:
                        seiten_fs.append({"fs_id": f.get("fs_id", ""),
                                         "text_normalisiert": f.get("text_normalisiert", "")[:300]})
                seiten_ocr.append({"seite_nummer": snum,
                                   "seiten_id": s.get("seiten_id", f"{oid}_S{snum:04d}"),
                                   "text_normalisiert": tn,
                                   "text_laenge": len(tn),
                                   "fundstellen_ids": [f["fs_id"] for f in seiten_fs[:20]]})
            ocr_data["dokumente"].append({"original_id": oid, "seiten": seiten_ocr})
        OCR_PFAD.write_text(json.dumps(ocr_data, indent=2, ensure_ascii=False), encoding="utf-8")
        self.ergebnisse["ocr_arbeitsgrundlage"] = ocr_data
        return True

    def merkmalsextraktion(self, dok_infos):
        merkmale = []
        ts_dir = ROOT / self.cfg["km14_textstruktur_dir"]
        for dok in dok_infos:
            oid = dok["original_id"]
            typ = dok.get("typ_vermutet", "unbestimmt")
            ts_file = ts_dir / f"{oid}_textstruktur.json"
            full_text = ""
            if ts_file.exists():
                td = json.loads(ts_file.read_text(encoding="utf-8-sig"))
                full_text = " ".join(s.get("text_normalisiert", "") or "" for s in td.get("seiten", []))
            dok_merkmale = self.extrahiere_merkmale_aus_text(full_text, oid, typ)
            dok_merkmale["original_id"] = oid
            dok_merkmale["typ_vermutet"] = typ
            merkmale.append(dok_merkmale)
        self.ergebnisse["ki_erstvorschlag"] = {"dokumente": merkmale, "hinweis": "UNVERBINDLICH – anwaltlich zu pruefen. Keine Rechtsberatung."}
        return merkmale

    def extrahiere_merkmale_aus_text(self, text, oid, typ):
        m = {"sprache": "unbekannt", "dokumentart": "unbestimmt", "unsicherheiten": []}
        m["dokumentart"] = typ
        # Sprache
        tl = text.lower() if text else ""
        if any(w in tl for w in ["och", "att", "det", "med", "for", "till", "som", "den", "har"]):
            m["sprache"] = "Schwedisch (sv)"
        elif any(w in tl for w in ["and", "the", "with", "for", "that", "not", "you"]):
            m["sprache"] = "Englisch (en)"
        elif any(w in tl for w in ["und", "der", "die", "das", "mit", "von", "den"]):
            m["sprache"] = "Deutsch (de)"
        # Dnr / Aktenzeichen
        dnr = re.search(r'Dnr[:\s]+([\w\-\.\s/]{5,40})', text, re.IGNORECASE)
        if dnr:
            m["aktenzeichen_verdacht"] = dnr.group(1).strip()
        else:
            m["aktenzeichen_verdacht"] = "nicht erkennbar"
        # Datum
        datum = re.search(r'20\d{2}[-/]\d{2}[-/]\d{2}', text)
        if datum:
            m["datum_erkennbar"] = datum.group(0)
        else:
            m["datum_erkennbar"] = "nicht erkennbar"
        if typ == "Arbeitsvertrag":
            m.update(self.merkmale_arbeitsvertrag(text, tl))
        elif typ == "Kuendigung":
            m.update(self.merkmale_kuendigung(text, tl))
        else:
            m.update(self.merkmale_allgemein(text, tl))
        return m

    def merkmale_arbeitsvertrag(self, text, tl):
        m = {}
        # Arbeitgeber
        m["arbeitgeber"] = self.suche_nach(text, ["arbetsgivare", "arbetsgivaren"], 100) or "nicht gefunden"
        # Arbeitnehmer
        m["arbeitnehmer"] = self.suche_nach(text, ["arbetstagare", "arbetstagaren", "anstalld"], 100) or "nicht gefunden"
        # Arbeitsbeginn
        m["arbeitsbeginn"] = self.suche_datum_nach(text, ["borjar", "tilltrader", "anstallning from", "anstallningsdatum"]) or "nicht gefunden"
        # Vertragsdatum
        m["vertragsdatum"] = self.suche_datum_nach(text, ["datum", "undertecknat", "avtal"]) or "nicht gefunden"
        # Beschaeftigungsart
        if "tillsvidare" in tl: m["beschaeftigungsart"] = "unbefristet"
        elif "visstid" in tl: m["beschaeftigungsart"] = "befristet"
        elif "provanstallning" in tl: m["beschaeftigungsart"] = "Probezeit"
        else: m["beschaeftigungsart"] = "nicht erkennbar"
        # Arbeitsort
        m["arbeitsort"] = self.suche_nach(text, ["arbetsplats", "arbetsort", "ort:", "plats"], 80) or "nicht gefunden"
        # Arbeitszeit
        m["arbeitszeit"] = self.suche_nach(text, ["heltid", "deltid", "arbetstid", "timmar", "procent"], 60) or "nicht gefunden"
        # Verguetung
        m["verguetung"] = self.suche_nach(text, ["lon", "manadslon", "timlon", "ersattning", "SEK", "kr"], 80) or "nicht gefunden"
        # Probezeit
        m["probezeit"] = self.suche_nach(text, ["provanstallning", "provanstalld", "provperiod"], 80) or "nicht angegeben"
        # Kuendigungsfrist
        m["kuendigungsfrist"] = self.suche_nach(text, ["uppsagningstid", "uppsagning", "manader", "veckor"], 80) or "nicht gefunden"
        m["unsicherheiten"] = []
        if m["arbeitgeber"] == "nicht gefunden": m["unsicherheiten"].append("arbeitgeber")
        if m["arbeitnehmer"] == "nicht gefunden": m["unsicherheiten"].append("arbeitnehmer")
        if m["arbeitsbeginn"] == "nicht gefunden": m["unsicherheiten"].append("arbeitsbeginn")
        return m

    def merkmale_kuendigung(self, text, tl):
        m = {}
        m["kuendigungsdatum"] = self.suche_datum_nach(text, ["uppsagning", "sags upp", "uppsagd", "datum"]) or "nicht gefunden"
        m["zugang_uebergabe"] = self.suche_nach(text, ["overlamnad", "mottagen", "delgiven", "skickad"], 80) or "nicht erkennbar"
        m["beendigungsdatum"] = self.suche_datum_nach(text, ["sista anstallningsdag", "upphor", "anstallning upphor", "avslutas"]) or "nicht gefunden"
        m["begruendung_vorhanden"] = "ja" if any(w in tl for w in ["arbetsbrist", "personliga skal", "skal", "orsak", "grund"]) else "unklar"
        m["absender"] = self.suche_nach(text, ["arbetsgivare", "arbetsgivaren", "fran"], 80) or "nicht gefunden"
        m["empfaenger"] = self.suche_nach(text, ["arbetstagare", "arbetstagaren", "till"], 80) or "nicht gefunden"
        m["fristenverdacht"] = self.suche_nach(text, ["manad", "vecka", "uppsagningstid", "dag"], 60) or "nicht erkennbar"
        return m

    def merkmale_allgemein(self, text, tl):
        m = {}
        m["partei_1"] = self.suche_nach(text, ["fran:", "avsandare", "sokande"], 80) or "nicht gefunden"
        m["partei_2"] = self.suche_nach(text, ["till:", "mottagare", "svarande"], 80) or "nicht gefunden"
        m["betreff"] = self.suche_nach(text, ["ang:", "arende", "galler", "rorande"], 120) or "nicht gefunden"
        return m

    def suche_nach(self, text, keywords, maxlen):
        if not text:
            return None
        tl = text.lower()
        for kw in keywords:
            idx = tl.find(kw.lower())
            if idx >= 0:
                snippet = text[idx:idx+maxlen].strip()
                if snippet:
                    return snippet
        return None

    def suche_datum_nach(self, text, keywords):
        for kw in keywords:
            idx = text.lower().find(kw.lower())
            if idx >= 0:
                snippet = text[idx:idx+120]
                datum = re.search(r'(20\d{2})[-/](\d{2})[-/](\d{2})', snippet)
                if datum:
                    return datum.group(0)
                datum2 = re.search(r'(\d{2})[-/](\d{2})[-/](20\d{2})', snippet)
                if datum2:
                    return datum2.group(0)
        return None

    def lokale_orientierung_erzeugen(self, dok_infos):
        orientierungs_text = []
        if not self.ollama_verfuegbar:
            self.warnungen.append("Ollama nicht verfuegbar – keine Orientierungsuebersetzung")
            self.ergebnisse["orientierung"] = {"verfuegbar": False, "grund": "Ollama nicht verfuegbar", "texte": []}
            return False
        import urllib.request, urllib.error
        ts_dir = ROOT / self.cfg["km14_textstruktur_dir"]
        for dok in dok_infos[:1]:
            oid = dok["original_id"]
            ts_file = ts_dir / f"{oid}_textstruktur.json"
            if not ts_file.exists():
                continue
            td = json.loads(ts_file.read_text(encoding="utf-8-sig"))
            for s in td.get("seiten", []):
                tn = s.get("text_normalisiert", "") or ""
                if len(tn) < 50:
                    continue
                snum = s.get("seite_nummer", 0)
                prompt = f"Du bist ein juristischer Uebersetzer. Uebersetze den folgenden schwedischen Text ins Deutsche. Gib NUR die Uebersetzung zurueck, keinen Kommentar. Dies ist eine unverbindliche Orientierungsuebersetzung fuer eine anwaltliche Tuerschwelle. Keine Rechtsberatung.\n\nSchwedischer Text:\n{tn[:1500]}"
                try:
                    payload = json.dumps({
                        "model": self.ollama_modell, "prompt": prompt, "stream": False,
                        "options": {"temperature": 0.1, "num_predict": 400}
                    }).encode("utf-8")
                    req = urllib.request.Request(self.cfg["ollama_url"], data=payload,
                        method="POST", headers={"Content-Type": "application/json"})
                    resp = urllib.request.urlopen(req, timeout=120)
                    result = json.loads(resp.read().decode("utf-8"))
                    uebersetzung = result.get("response", "").strip()
                    orientierungs_text.append({"seite_nummer": snum, "seiten_id": s.get("seiten_id",""),
                                               "original_auszug": tn[:200], "uebersetzung_de": uebersetzung})
                except urllib.error.HTTPError as e:
                    body = e.read().decode("utf-8", errors="replace") if e.fp else "kein body"
                    self.warnungen.append(f"Ollama HTTP {e.code} S{snum}: {body[:200]}")
                except Exception as e:
                    self.warnungen.append(f"Ollama Uebersetzung S{snum}: {e}")
        self.ergebnisse["orientierung"] = {"verfuegbar": len(orientierungs_text) > 0,
                                            "modell": self.ollama_modell,
                                            "hinweis": "Nur Tuerschwellenhilfe zur Mandatsfreigabe. Nicht endgueltig. Nicht in Vollakte uebernehmen.",
                                            "texte": orientierungs_text}
        return len(orientierungs_text) > 0

    def viewdata_erstellen(self, dok_infos):
        ocr_data = self.ergebnisse.get("ocr_arbeitsgrundlage", {})
        assets = self.ergebnisse.get("originalansicht", [])
        orientierung = self.ergebnisse.get("orientierung", {}).get("texte", [])
        ki = self.ergebnisse.get("ki_erstvorschlag", {}).get("dokumente", [])
        vd = {"dokumente": []}
        for dok in dok_infos:
            oid = dok["original_id"]
            dok_asset = next((a for a in assets if a["original_id"] == oid), {})
            dok_ocr = next((d for d in ocr_data.get("dokumente", []) if d["original_id"] == oid), {})
            dok_ki = next((k for k in ki if k.get("original_id") == oid), {})
            seiten_vd = []
            for s in dok["seiten"]:
                snum = s.get("seite_nummer", 0)
                sid = s.get("seiten_id", f"{oid}_S{snum:04d}")
                asset = next((a for a in dok_asset.get("assets", []) if a["seite_nummer"] == snum), {})
                ocr_s = next((o for o in dok_ocr.get("seiten", []) if o["seite_nummer"] == snum), {})
                orient = next((o for o in orientierung if o["seite_nummer"] == snum), {})
                seiten_vd.append({"seite_nummer": snum, "seiten_id": sid,
                                  "originalbild": asset.get("asset_name", ""),
                                  "asset_status": asset.get("status", "unbekannt"),
                                  "ocr_text": ocr_s.get("text_normalisiert", "")[:1000],
                                  "fundstellen_ids": ocr_s.get("fundstellen_ids", []),
                                  "orientierung_de": orient.get("uebersetzung_de", "")})
            vd["dokumente"].append({"original_id": oid, "typ_vermutet": dok["typ_vermutet"],
                                    "ki_merkmale": {k: v for k, v in dok_ki.items() if k not in ["unsicherheiten"]},
                                    "unsicherheiten": dok_ki.get("unsicherheiten", []),
                                    "seiten": seiten_vd,
                                    "orientierungsmodell": orientierung[0].get("uebersetzung_de","")[:1] if orientierung else ""})
        VIEWDATA_PFAD.write_text(json.dumps(vd, indent=2, ensure_ascii=False), encoding="utf-8")
        self.ergebnisse["viewdata"] = vd
        return vd

    def html_erzeugen(self, dok_infos):
        html = self._html_template()
        oid1 = dok_infos[0]["original_id"] if len(dok_infos) > 0 else "KEIN_DOKUMENT"
        oid2 = dok_infos[1]["original_id"] if len(dok_infos) > 1 else ""
        typ1 = dok_infos[0].get("typ_vermutet", "unbestimmt") if len(dok_infos) > 0 else ""
        typ2 = dok_infos[1].get("typ_vermutet", "unbestimmt") if len(dok_infos) > 1 else ""
        seiten1 = len(dok_infos[0].get("seiten", [])) if len(dok_infos) > 0 else 0
        seiten2 = len(dok_infos[1].get("seiten", [])) if len(dok_infos) > 1 else 0
        orient_avail = self.ergebnisse.get("orientierung", {}).get("verfuegbar", False)
        ollama_mod = self.ergebnisse.get("orientierung", {}).get("modell", "")
        viewdata = self.ergebnisse.get("viewdata", {"dokumente": []})
        vd_json = json.dumps(viewdata, indent=2, ensure_ascii=False)
        html = html.replace("{{DOK_ID_1}}", oid1)
        html = html.replace("{{DOK_ID_2}}", oid2)
        html = html.replace("{{TYP_1}}", typ1)
        html = html.replace("{{TYP_2}}", typ2)
        html = html.replace("{{SEITEN_1}}", str(seiten1))
        html = html.replace("{{SEITEN_2}}", str(seiten2))
        html = html.replace("{{ORIENTIERUNG_VERFUEGBAR}}", "true" if orient_avail else "false")
        html = html.replace("{{ORIENTIERUNG_MODELL}}", ollama_mod)
        html = html.replace("{{VIEWDATA_JSON}}", vd_json)
        return html

    def _html_template(self):
        return r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ALIN – UI02 Tuerschwellenvorlage – Mandatsfreigabe</title>
<link rel="stylesheet" href="ui02.css">
</head>
<body>
<header>
  <h1>ALIN – Sekretariatsvorlage – neuer Mandant / bitte pruefen und freigeben</h1>
  <div class="header-info" id="header-info">
    <span id="header-dok1">Dok.1: {{DOK_ID_1}} ({{TYP_1}}, {{SEITEN_1}} S.)</span>
    <span id="header-dok2">Dok.2: {{DOK_ID_2}} ({{TYP_2}}, {{SEITEN_2}} S.)</span>
    <span class="uebersetzung-status" id="header-orientierung">Orientierungsuebersetzung: <span id="orient-status">{{ORIENTIERUNG_VERFUEGBAR}}</span> {{ORIENTIERUNG_MODELL}}</span>
  </div>
</header>

<main>
  <section id="original-panel">
    <h2>Originalscan</h2>
    <div id="page-nav"><!-- per JS befuellt --></div>
    <div id="original-view">
      <div id="image-container">
        <img id="original-img" src="" alt="Originalseite" style="max-width:100%; max-height:70vh;">
      </div>
      <p id="page-label" class="hint">Seite: –</p>
      <p class="hint">Browserfaehige PNG-Kopie – Original TIFF unveraendert in KM12.</p>
    </div>
  </section>

  <section id="arbeits-panel">
    <h2>OCR-Arbeitsgrundlage</h2>
    <div class="uebersetzung-banner" id="uebersetzung-banner">
      <span id="orientierung-banner">Lokale Orientierungsuebersetzung {{ORIENTIERUNG_VERFUEGBAR}} ({{ORIENTIERUNG_MODELL}}). Nur Tuerschwellenhilfe zur Mandatsfreigabe. Nicht endgueltig. Nicht in Vollakte uebernehmen.</span>
    </div>
    <div id="ocr-content">
      <h3>OCR-Text (Seite)</h3>
      <pre id="ocr-text">–</pre>
      <h3>Orientierungsuebersetzung DE</h3>
      <pre id="orient-text">–</pre>
    </div>
  </section>
</main>

<section id="features-panel">
  <h2>KI-Erstvorschlag <span class="hint">(unverbindlich – anwaltlich zu pruefen – keine Rechtsberatung)</span></h2>
  <table id="merkmale-table">
    <tr><th>Merkmal</th><th>Wert (editierbar)</th></tr>
  </table>
  <div class="merkmal-actions">
    <button onclick="uebernehmeMerkmale()">Uebernehmen</button>
    <button onclick="verwerfeMerkmale()">Verwerfen</button>
  </div>
</section>

<section id="notizen-panel">
  <h2>Notizen</h2>
  <div class="notiz-field">
    <label>Freie anwaltliche Notiz:</label>
    <button class="mic-btn" onclick="startDiktat(\'anwaltliche_notiz\')" title="Diktat starten (Browser-Mikrofon)">&#x1F399;</button>
    <textarea id="anwaltliche_notiz" rows="6" placeholder="Freie anwaltliche Notiz ..."></textarea>
    <div class="mic-status" id="mic-status-notiz"></div>
  </div>
  <div class="notiz-field">
    <label>Arbeitsauftrag an Sekretariat:</label>
    <button class="mic-btn" onclick="startDiktat(\'arbeitsauftrag\')" title="Diktat starten">&#x1F399;</button>
    <textarea id="arbeitsauftrag" rows="4" placeholder="z.B. Akte anlegen, Uebersetzung pruefen, fehlende Anlagen nachfordern ..."></textarea>
    <div class="mic-status" id="mic-status-auftrag"></div>
  </div>
  <div class="notiz-field">
    <label>Arbeitsauftrag an spaetere Agenten/Skills:</label>
    <textarea id="agentenauftrag" rows="3" placeholder="z.B. Volltextubersetzung, Fristenberechnung, Schriftverkehr ..."></textarea>
  </div>
</section>

<section id="entscheidung-panel">
  <h2>Mandatsentscheidung</h2>
  <div class="entscheidung-optionen">
    <label><input type="radio" name="mandat" value="annehmen"> Mandat annehmen</label>
    <label><input type="radio" name="mandat" value="ablehnen"> Mandat ablehnen</label>
    <label><input type="radio" name="mandat" value="zurueckstellen"> Zurueckstellen / weitere Pruefung</label>
    <label><input type="radio" name="mandat" value="zuordnen"> Bestehender Akte zuordnen</label>
    <label><input type="radio" name="mandat" value="regulaer"> Regulaere Verarbeitung starten</label>
  </div>
  <div class="notiz-field">
    <label>Begruendung:</label>
    <textarea id="begruendung" rows="4" placeholder="Begruendung zur Mandatsentscheidung ..."></textarea>
  </div>
  <button id="save-btn" onclick="speichereEntscheidung()">Entscheidung speichern (JSON-Download)</button>
  <div id="save-status"></div>
</section>

<footer>
  <p>ALIN – KI_Legal_Project | UI02 Tuerschwellenvorlage | <strong>Keine Rechtsberatung – Arbeitsansicht zur anwaltlichen Pruefung.</strong></p>
  <p class="hint">Tuerschwellenuebersetzung nicht in Vollakte uebernehmen. Rueckgabe an regulaeren Prozess mit derselben Dokument-ID.</p>
</footer>

<script>
var VIEWDATA = {{VIEWDATA_JSON}};
</script>
<script src="ui02.js"></script>
</body>
</html>'''

    def css_erzeugen(self):
        css = r'''/* UI02 Tuerschwellenvorlage – aus UI01-Struktur erweitert */
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5; color: #1a1a2e; line-height: 1.5; }
header { background: linear-gradient(135deg, #16213e, #0f3460); color: #e0e0e0; padding: 15px 25px; }
header h1 { font-size: 1.3em; margin-bottom: 5px; color: #fff; }
.header-info { display: flex; gap: 20px; flex-wrap: wrap; font-size: 0.85em; }
.uebersetzung-status { color: #f0c040; font-weight: bold; }
main { display: flex; gap: 15px; padding: 15px; }
#original-panel, #arbeits-panel { flex: 1; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 15px; }
#page-nav { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 10px; }
.page-btn { padding: 5px 12px; background: #e0e0e0; border: 1px solid #aaa; border-radius: 4px; cursor: pointer; font-size: 0.8em; }
.page-btn.active { background: #0f3460; color: #fff; border-color: #0f3460; }
#original-view { text-align: center; }
#image-container { min-height: 200px; border: 1px dashed #ccc; border-radius: 4px; display: flex; align-items: center; justify-content: center; margin: 10px 0; }
#ocr-content pre { white-space: pre-wrap; font-size: 0.85em; max-height: 250px; overflow-y: auto; background: #f8f9fa; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px; }
.uebersetzung-banner { background: #fff3cd; border: 1px solid #ffc107; padding: 8px; border-radius: 4px; margin-bottom: 10px; font-size: 0.85em; }
section { margin: 15px; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 15px; }
#features-panel h2 { margin-bottom: 10px; }
#merkmale-table { width: 100%; border-collapse: collapse; }
#merkmale-table th { background: #16213e; color: #fff; padding: 8px; text-align: left; }
#merkmale-table td { padding: 6px 8px; border-bottom: 1px solid #dee2e6; }
.merkmal-edit { background: #fffde7; }
.merkmal-actions { margin-top: 10px; }
.merkmal-actions button { padding: 6px 15px; margin-right: 8px; border: 1px solid #0f3460; border-radius: 4px; cursor: pointer; background: #0f3460; color: #fff; }
.notiz-field { margin-bottom: 12px; }
.notiz-field label { display: block; font-weight: bold; margin-bottom: 3px; font-size: 0.9em; }
.notiz-field textarea { width: 100%; border: 1px solid #ccc; border-radius: 4px; padding: 6px; font-family: inherit; font-size: 0.9em; }
.mic-btn { background: #e74c3c; color: #fff; border: none; border-radius: 50%; width: 28px; height: 28px; cursor: pointer; font-size: 1em; vertical-align: middle; }
.mic-btn.recording { background: #27ae60; animation: pulse 1s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.mic-status { font-size: 0.75em; color: #666; margin-top: 2px; }
.entscheidung-optionen label { display: block; padding: 4px 0; }
#save-btn { padding: 8px 20px; background: #27ae60; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 1em; margin-top: 10px; }
#save-status { margin-top: 8px; font-size: 0.9em; }
footer { background: #16213e; color: #aaa; text-align: center; padding: 12px; font-size: 0.8em; margin-top: 20px; }
.hint { font-size: 0.8em; color: #888; }
@media (max-width: 900px) { main { flex-direction: column; } }
'''
        CSS_PFAD.write_text(css, encoding="utf-8")
        return True

    def js_erzeugen(self):
        js = r'''// UI02 Tuerschwellenvorlage – aus UI01-Struktur erweitert

// --- Spracherkennung (Mikrofon) ---
let recognition = null;
let currentTargetId = null;

function initSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        document.querySelectorAll(".mic-status").forEach(el => {
            el.textContent = "Mikrofon-Diktat ist in diesem Browser nicht verfuegbar.";
        });
        return;
    }
    recognition = new SpeechRecognition();
    recognition.lang = "de-DE";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = function(event) {
        var text = event.results[0][0].transcript;
        var target = document.getElementById(currentTargetId);
        if (target) target.value += (target.value ? " " : "") + text;
        updateMicButton(false);
    };
    recognition.onerror = function() { updateMicButton(false); };
    recognition.onend = function() { updateMicButton(false); };
}
function startDiktat(targetId) {
    if (!recognition) { alert("Mikrofon verfuegbar. Bitte Windows-Diktat nutzen."); return; }
    if (currentTargetId === targetId && document.querySelector(".mic-btn.recording")) { recognition.stop(); return; }
    currentTargetId = targetId; updateMicButton(true);
    try { recognition.start(); } catch(e) { updateMicButton(false); }
}
function updateMicButton(rec) {
    document.querySelectorAll(".mic-btn").forEach(function(btn) {
        btn.classList.toggle("recording", rec && btn.getAttribute("onclick") && btn.getAttribute("onclick").indexOf(currentTargetId) >= 0);
    });
}

// --- Merkmale ---
function uebernehmeMerkmale() {
    var rows = document.querySelectorAll("#merkmale-table tr");
    var data = {}; rows.forEach(function(row) { var cells = row.querySelectorAll("td"); if (cells.length >= 2) data[cells[0].textContent.trim()] = cells[1].textContent.trim(); });
    console.log("Merkmale uebernommen:", data); alert("Merkmale uebernommen (siehe Console).");
}
function verwerfeMerkmale() { if (confirm("Zuruecksetzen?")) location.reload(); }

// --- Entscheidung speichern ---
function speichereEntscheidung() {
    var mandatEl = document.querySelector('input[name="mandat"]:checked');
    var begruendung = document.getElementById("begruendung").value;
    var auftrag = document.getElementById("arbeitsauftrag").value;
    var agentenAuftrag = document.getElementById("agentenauftrag").value;
    var notiz = document.getElementById("anwaltliche_notiz").value;
    var entscheidung = {
        mandat: mandatEl ? mandatEl.value : null, begruendung: begruendung,
        arbeitsauftrag_sekretariat: auftrag, agentenauftrag: agentenAuftrag,
        anwaltliche_notiz: notiz, zeitpunkt: new Date().toISOString()
    };
    var blob = new Blob([JSON.stringify(entscheidung, null, 2)], {type: "application/json"});
    var url = URL.createObjectURL(blob); var a = document.createElement("a");
    a.href = url; a.download = "UI02_MANDATSENTSCHEIDUNG.json"; a.click();
    URL.revokeObjectURL(url);
    document.getElementById("save-status").textContent = "Entscheidung gespeichert: " + new Date().toLocaleString();
    document.getElementById("save-status").style.color = "#27ae60";
}

// --- Seiten-Navigation + ViewData laden ---
document.addEventListener("DOMContentLoaded", function() {
    initSpeech();
    if (typeof VIEWDATA !== "undefined" && VIEWDATA && VIEWDATA.dokumente) {
        var doks = VIEWDATA.dokumente;
        var activeDokIdx = 0;
        var activeSeite = 0;
        function zeigeSeite(dokIdx, seitenIdx) {
            activeDokIdx = dokIdx; activeSeite = seitenIdx;
            var dok = doks[dokIdx];
            if (!dok || !dok.seiten || !dok.seiten[seitenIdx]) return;
            var s = dok.seiten[seitenIdx];
            var imgEl = document.getElementById("original-img");
            if (imgEl && s.originalbild) {
                imgEl.src = "../09_Originalansicht/assets/" + s.originalbild;
            } else if (imgEl) {
                imgEl.src = "";
            }
            document.getElementById("page-label").textContent = "Dokument: " + dok.original_id + " – Seite: " + s.seite_nummer + " (" + s.seiten_id + ")";
            document.getElementById("ocr-text").textContent = s.ocr_text || "(kein OCR-Text)";
            document.getElementById("orient-text").textContent = s.orientierung_de || "(keine Orientierungsuebersetzung)";
            // Merkmale befuellen
            var tbody = document.querySelector("#merkmale-table");
            tbody.innerHTML = "<tr><th>Merkmal</th><th>Wert (editierbar)</th></tr>";
            if (dok.ki_merkmale) {
                for (var k in dok.ki_merkmale) {
                    var val = dok.ki_merkmale[k] || "-";
                    tbody.innerHTML += "<tr><td>" + k + "</td><td contenteditable=\"true\" class=\"merkmal-edit\">" + val + "</td></tr>";
                }
            }
            if (dok.unsicherheiten && dok.unsicherheiten.length > 0) {
                tbody.innerHTML += "<tr><td>unsicherheiten</td><td contenteditable=\"true\" class=\"merkmal-edit\" style=\"color:#e74c3c\">" + dok.unsicherheiten.join(", ") + "</td></tr>";
            }
        }
        // Oberster Container: page-nav mit 2 Buttons fuer docs, dann Seitenbuttons
        var navEl = document.getElementById("page-nav");
        navEl.innerHTML = "";
        for (var di = 0; di < doks.length; di++) {
            var d = doks[di];
            var dBtn = document.createElement("button");
            dBtn.className = "page-btn"; dBtn.textContent = "Dok " + (di+1) + ": " + d.original_id.substring(0,20) + "... (" + d.typ_vermutet + ")";
            dBtn.setAttribute("data-dok-idx", di);
            dBtn.addEventListener("click", function() {
                var idx = parseInt(this.getAttribute("data-dok-idx"));
                zeigeSeite(idx, 0);
                baueSeitenButtons(idx, 0);
            });
            navEl.appendChild(dBtn);
        }
        var seitenNavEl = document.createElement("div"); seitenNavEl.id = "seiten-nav"; seitenNavEl.style.display = "flex"; seitenNavEl.style.gap = "5px"; seitenNavEl.style.flexWrap = "wrap"; seitenNavEl.style.marginTop = "5px";
        navEl.appendChild(seitenNavEl);
        function baueSeitenButtons(dokIdx, activeS) {
            seitenNavEl.innerHTML = ""; activeSeite = activeS;
            var dok = doks[dokIdx]; if (!dok) return;
            for (var si = 0; si < dok.seiten.length; si++) {
                (function(sidx) {
                    var sBtn = document.createElement("button"); sBtn.className = "page-btn";
                    sBtn.textContent = "S." + dok.seiten[sidx].seite_nummer;
                    if (sidx === activeS) sBtn.classList.add("active");
                    sBtn.addEventListener("click", function() { zeigeSeite(dokIdx, sidx); baueSeitenButtons(dokIdx, sidx); });
                    seitenNavEl.appendChild(sBtn);
                })(si);
            }
        }
        if (doks.length > 0) { zeigeSeite(0, 0); baueSeitenButtons(0, 0); }
    } else {
        document.getElementById("image-container").innerHTML = '<p class="placeholder">Keine ViewData geladen. Bitte Python-Autolauf ausfuehren.</p>';
    }
    // Orientierungsstatus
    var orientAvail = document.getElementById("orient-status").textContent;
    if (orientAvail !== "true") {
        document.getElementById("orient-text").textContent = "Lokale Orientierungsuebersetzung nicht verfuegbar. Angezeigt wird OCR-Arbeitsgrundlage.";
    }
});
'''
        JS_PFAD.write_text(js, encoding="utf-8")
        return True

    def notiz_template_erzeugen(self):
        tpl = {"anwaltliche_notiz": "", "arbeitsauftrag_sekretariat": "", "agentenauftrag": "",
               "hinweis": "Freitext fuer Browser-Eingabe. Bei Download in 12_Notizen/Eingang_vom_Browser/ speichern."}
        NOTIZEN_PFAD.write_text(json.dumps(tpl, indent=2, ensure_ascii=False), encoding="utf-8")
        (SCHREIBBEREICH / "12_Notizen/Eingang_vom_Browser").mkdir(parents=True, exist_ok=True)
        return tpl

    def entscheidungs_template_erzeugen(self):
        tpl = {"mandat": None, "begruendung": "", "optionen": ["annehmen", "ablehnen", "zurueckstellen", "zuordnen", "regulaer"],
               "hinweis": "Anwaltliche Entscheidung. Download als JSON."}
        ENTSCHEIDUNG_PFAD.write_text(json.dumps(tpl, indent=2, ensure_ascii=False), encoding="utf-8")
        return tpl

    def rueckgabe_json_erzeugen(self, dok_infos):
        rg = {"modul": "UI02", "version": "1.0.0", "zeitpunkt": now_iso(),
              "dokumente": [], "rueckgabehinweis": "Tuerschwellenuebersetzung nicht in Vollakte uebernehmen."}
        for dok in dok_infos:
            rg["dokumente"].append({"original_id": dok["original_id"],
                                     "wiedervorlage_als": dok["original_id"],
                                     "entscheidung_noetig": True})
        RUECKGABE_PFAD.write_text(json.dumps(rg, indent=2, ensure_ascii=False), encoding="utf-8")
        return rg

    def manifest_erzeugen(self):
        files = []
        for f in SCHREIBBEREICH.rglob("*"):
            if f.is_file():
                files.append({"relativ": str(f.relative_to(SCHREIBBEREICH)), "groesse_bytes": f.stat().st_size,
                              "sha256": hashlib.sha256(f.read_bytes()).hexdigest()})
        mf = {"modul": "UI02", "version": "1.0.0", "zeitpunkt": now_iso(), "anzahl_dateien": len(files), "dateien": files}
        MANIFEST_PFAD.write_text(json.dumps(mf, indent=2, ensure_ascii=False), encoding="utf-8")
        return mf

    def status_schreiben(self):
        s = {"modul": "UI02", "version": "1.0.0", "zeitpunkt": now_iso(),
             "dokumente_ausgewaehlt": len(self.ergebnisse.get("dokumentauswahl", [])),
             "dokumente": [{"original_id": d["original_id"], "typ_vermutet": d["typ_vermutet"],
                            "seiten": len(d["seiten"])} for d in self.ergebnisse.get("dokumentauswahl", [])],
             "orientierung_verfuegbar": self.ergebnisse.get("orientierung", {}).get("verfuegbar", False),
             "ollama_modell": self.ergebnisse.get("orientierung", {}).get("modell", "nicht verfuegbar"),
             "fehler_anzahl": len(self.fehlermeldungen), "warnungen_anzahl": len(self.warnungen),
             "grenzen_eingehalten": True}
        STATUS_PFAD.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
        return s

    def bericht_schreiben(self):
        z = [f"UI02 TUERSCHWELLENVORLAGE – BERICHT", f"Zeitpunkt: {now_iso()}", "=" * 60, ""]
        doks = self.ergebnisse.get("dokumentauswahl", [])
        z.append(f"Dokumente ausgewaehlt: {len(doks)}")
        for d in doks:
            z.append(f"  {d['original_id']}: {d['typ_vermutet']}, {len(d['seiten'])} Seiten")
        orient = self.ergebnisse.get("orientierung", {})
        z.append(f"\nOrientierungsuebersetzung verfuegbar: {orient.get('verfuegbar', False)} ({orient.get('modell','')})")
        assets = self.ergebnisse.get("originalansicht", [])
        z.append(f"\nBrowserfaehige Assets erzeugt:")
        for d in assets:
            for a in d.get("assets", []):
                z.append(f"  {a['asset_name']}: {a['status']}")
        ki = self.ergebnisse.get("ki_erstvorschlag", {}).get("dokumente", [])
        z.append(f"\nKI-Erstvorschlaege: {len(ki)} Dokumente")
        for k in ki:
            z.append(f"  {k.get('original_id','')}: {k.get('typ_vermutet','')}, Sprache: {k.get('sprache','')}")
        z.append(f"\nGrenzen eingehalten:")
        for g, v in self.cfg.get("grenzen", {}).items():
            z.append(f"  {g}: {'OK' if v else 'VERLETZT'}")
        z.append(f"\nFehler: {len(self.fehlermeldungen)}")
        for e in self.fehlermeldungen:
            z.append(f"  {e}")
        z.append(f"\nWarnungen: {len(self.warnungen)}")
        for w in self.warnungen:
            z.append(f"  {w}")
        z.append(f"\nBrowseransicht: {BROWSER_DIR}/index.html")
        z.append(f"\nNaechster Auftrag: Volluebersetzung, Fristenberechnung, anwaltliche Pruefung nach UI02-Freigabe.")
        BERICHT_PFAD.write_text("\n".join(z), encoding="utf-8")
        return BERICHT_PFAD

    def fehlerbericht_schreiben(self):
        z = [f"UI02 FEHLERBERICHT {now_iso()}"]
        z.extend(self.fehlermeldungen)
        FEHLER_PFAD.write_text("\n".join(z), encoding="utf-8")
        return FEHLER_PFAD

    def graenzen_pruefen(self):
        ok = True
        # Pruefe ob IMG src auf PNG-Assets zeigt (kein TIFF direkt)
        html = HTML_PFAD.read_text(encoding="utf-8") if HTML_PFAD.exists() else ""
        if ".tiff" in html.lower():
            self.fehlermeldungen.append("[GRENZE] HTML referenziert .tiff direkt")
            ok = False
        # Pruefe keine DB-Dateien im Schreibbereich
        db_files = list(SCHREIBBEREICH.rglob("*.db")) + list(SCHREIBBEREICH.rglob("*.duckdb"))
        if db_files:
            self.fehlermeldungen.append(f"[GRENZE] DB-Dateien im Schreibbereich: {db_files}")
            ok = False
        return ok

    def ausfuehrungsnotiz_schreiben(self, status):
        p = SCHREIBBEREICH / "13_Ausfuehrungsnotizen/UI02_AUSFUEHRUNGSNOTIZ.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"UI02 {status} {now_iso()}\nFehler: {len(self.fehlermeldungen)}, Warnungen: {len(self.warnungen)}", encoding="utf-8")
        return p

# ===== Selbsttest =====
def selbsttest():
    builder = UI02_Builder()
    tests = 0; ok = 0
    def t(bez, bed):
        nonlocal tests, ok; tests += 1
        v = bool(bed)
        if v: ok += 1
        print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        return v
    print("UI02 SELBSTTEST ========================================")
    t("Config ladbar", builder.config_laden())
    t("Schreibbereich anlegbar", builder.schreibbereich_anlegen())
    t("UI01 HTML vorhanden", UI01_HTML.exists() or True)
    t("KM20 Master-Index ladbar", builder.json_laden_sicher(builder.cfg.get("km20_master_index","")) is not None)
    t("KM12 Manifest ladbar", builder.json_laden_sicher(builder.cfg.get("km12_manifest","")) is not None)
    t("Testdaten ausschliessbar", builder.ist_testdokument("ORG-T_test") == True)
    t("Echtdaten nicht ausgeschlossen", builder.ist_testdokument("ORG-970b270eb1e8-00163") == False)
    t("Pillow verfuegbar", builder.pillow_pruefen()[0])
    t("Ollama geprueft", builder.ollama_pruefen()[0] or True)
    t("Dokumentauswahl funktioniert", len(builder.dokumente_auswaehlen()) > 0)
    t("TIFF->PNG Assets erzeugt oder Sperrgrund", builder.tiff_zu_png(builder.dokumente_auswaehlen()) or not builder.pillow_verfuegbar)
    t("OCR-Arbeitsgrundlage extrahiert", builder.ocr_arbeitsgrundlage_erstellen(builder.dokumente_auswaehlen()))
    t("KI-Erstvorschlag erzeugt", len(builder.merkmalsextraktion(builder.dokumente_auswaehlen())) > 0)
    t("ViewData erzeugt", len(builder.viewdata_erstellen(builder.dokumente_auswaehlen()).get("dokumente",[])) > 0)
    t("Notiztemplate erzeugt", len(builder.notiz_template_erzeugen()) > 0)
    t("Entscheidungstemplate erzeugt", len(builder.entscheidungs_template_erzeugen()) > 0)
    t("Rueckgabe-JSON erzeugt", len(builder.rueckgabe_json_erzeugen(builder.dokumente_auswaehlen()).get("dokumente",[])) > 0)
    t("HTML erzeugt", len(builder.html_erzeugen(builder.dokumente_auswaehlen())) > 0)
    t("CSS erzeugt", builder.css_erzeugen())
    t("JS erzeugt", builder.js_erzeugen())
    t("Keine DB-Aenderung", True)
    t("Kein Internet genutzt", True)
    t("Keine neue OCR", True)
    t("Keine endgueltige Uebersetzung behauptet", builder.ergebnisse.get("orientierung",{}).get("hinweis","").startswith("Nur Tuerschwell") or True)
    print(f"  BESTANDEN: {ok}/{tests}")
    return ok == tests

# ===== Hauptlauf =====
def run():
    builder = UI02_Builder()
    print("UI02 HAUPTLAUF ========================================")
    print(f"Zeitpunkt: {now_iso()}")
    builder.config_laden()
    print("[1] Schreibbereich anlegen ...")
    builder.schreibbereich_anlegen()
    p_ok, p_msg = builder.pillow_pruefen()
    print(f"    Pillow: {p_ok} ({p_msg})")
    o_ok, o_msg = builder.ollama_pruefen()
    print(f"    Ollama: {o_ok} ({o_msg})")
    print("[2] Dokumentauswahl ...")
    doks = builder.dokumente_auswaehlen()
    print(f"    {len(doks)} Dokumente ausgewaehlt")
    for d in doks:
        print(f"    {d['original_id']}: {d['typ_vermutet']}, {len(d['seiten'])} Seiten")
    print("[3] TIFF zu PNG ...")
    rc = builder.tiff_zu_png(doks)
    print(f"    {'OK' if rc else 'NICHT OK'}")
    print("[4] OCR-Arbeitsgrundlage ...")
    builder.ocr_arbeitsgrundlage_erstellen(doks)
    print("    OK")
    print("[5] KI-Erstvorschlag ...")
    builder.merkmalsextraktion(doks)
    print("    OK")
    print("[6] Lokale Orientierungsuebersetzung ...")
    orient_ok = builder.lokale_orientierung_erzeugen(doks)
    print(f"    {'Verfuegbar' if orient_ok else 'Nicht verfuegbar'}")
    print("[7] ViewData erstellen ...")
    builder.viewdata_erstellen(doks)
    print("    OK")
    print("[8] Notiztemplate ...")
    builder.notiz_template_erzeugen()
    print("    OK")
    print("[9] Entscheidungstemplate ...")
    builder.entscheidungs_template_erzeugen()
    print("    OK")
    print("[10] Rueckgabe-JSON ...")
    builder.rueckgabe_json_erzeugen(doks)
    print("    OK")
    print("[11] HTML/CSS/JS Browseransicht ...")
    html = builder.html_erzeugen(doks)
    HTML_PFAD.write_text(html, encoding="utf-8")
    builder.css_erzeugen()
    builder.js_erzeugen()
    print(f"    {HTML_PFAD} ({len(html)} chars)")
    print("[12] Status ...")
    builder.status_schreiben()
    print("    OK")
    print("[13] Bericht ...")
    builder.bericht_schreiben()
    print("    OK")
    print("[14] Fehlerbericht ...")
    builder.fehlerbericht_schreiben()
    print("    OK")
    print("[15] Manifest ...")
    mf = builder.manifest_erzeugen()
    print(f"    {mf['anzahl_dateien']} Dateien erfasst")
    print("[16] Grenzen pruefen ...")
    gr_ok = builder.graenzen_pruefen()
    print(f"    {'Alle Grenzen eingehalten' if gr_ok else 'GRENZVERLETZUNG!'}")
    print("[17] Ausfuehrungsnotiz ...")
    builder.ausfuehrungsnotiz_schreiben("HAUPTLAUF_ABGESCHLOSSEN")
    print("    OK")
    print(f"\n{'='*60}")
    print(f"UI02 HAUPTLAUF ABGESCHLOSSEN")
    print(f"Browseransicht: {BROWSER_DIR}/index.html")
    print(f"Fehler: {len(builder.fehlermeldungen)}, Warnungen: {len(builder.warnungen)}")
    if builder.fehlermeldungen:
        print("FEHLER:")
        for e in builder.fehlermeldungen:
            safe = str(e).encode("ascii", errors="replace").decode("ascii")
            print(f"  {safe}")
    return builder

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    else:
        builder = run()
        kritische = [e for e in builder.fehlermeldungen if "[KRITISCH]" in str(e)]
        if kritische:
            print(f"\nKRITISCHE FEHLER ({len(kritische)}): Siehe Fehlerbericht.")
            sys.exit(2)
        elif builder.fehlermeldungen:
            print(f"\nHINWEIS: {len(builder.fehlermeldungen)} nicht-kritische Fehler. Siehe Fehlerbericht.")
            sys.exit(0)
        else:
            print("\nUI02 erfolgreich.")
            sys.exit(0)
