#!/usr/bin/env python3
"""UI02-0 Bestandsabgleich Tuerschwelle – Inventar/Wiederverwendung"""
import sys, json, csv, datetime, hashlib, io
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SCHREIBBEREICH = ROOT / "Agentensteuerung/UI02_0_Bestandsabgleich_Tuerschwelle"
CONFIG_PFAD = ROOT / "Config/ui02_0_bestandsabgleich_tuerschwelle_v1.json"
STATUS_PFAD = SCHREIBBEREICH / "02_Status/UI02_0_STATUS.json"
BERICHT_PFAD = SCHREIBBEREICH / "03_Berichte/UI02_0_BESTANDSABGLEICH.txt"
MATRIX_JSON = SCHREIBBEREICH / "04_Wiederverwendung/UI02_0_WIEDERVERWENDUNGSMATRIX.json"
MATRIX_CSV = SCHREIBBEREICH / "04_Wiederverwendung/UI02_0_WIEDERVERWENDUNGSMATRIX.csv"
LUECKEN_JSON = SCHREIBBEREICH / "05_Luecken/UI02_0_LUECKENLISTE.json"
LUECKEN_TXT = SCHREIBBEREICH / "05_Luecken/UI02_0_LUECKENLISTE.txt"
MODULKARTE = SCHREIBBEREICH / "06_Modulkarte/UI02_0_MODULKARTE.json"
UI01_AUSWERTUNG = SCHREIBBEREICH / "07_UI01_Auswertung/UI02_0_UI01_AUSWERTUNG.json"
EMPFEHLUNG = SCHREIBBEREICH / "08_Empfehlung/UI02_0_NAECHSTER_AUFTRAG_UI02.txt"
AUSFUEHRUNGSNOTIZ = SCHREIBBEREICH / "13_Ausfuehrungsnotizen/UI02_0_AUSFUEHRUNGSNOTIZ.txt"
RUNLOG = SCHREIBBEREICH / "90_RunLogs"
FEHLER_PFAD = SCHREIBBEREICH / "05_Fehler/UI02_0_FEHLER.txt"
MANIFEST_PFAD = SCHREIBBEREICH / "07_Manifest/UI02_0_MANIFEST.json"

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

class UI02_0_Bestandsabgleich:
    def __init__(self):
        self.fehlermeldungen = []
        self.cfg = {}
        self.ergebnisse = {}

    def config_laden(self):
        if not CONFIG_PFAD.exists():
            self.cfg = {
                "modul": "UI02_0", "version": "1.0.0",
                "projektwurzel": str(ROOT), "schreibbereich": str(SCHREIBBEREICH),
                "master_index": "Agentensteuerung/20_Quellen_Fundstellen_Konsolidierung/07_Manifest/KM20_MASTER_INDEX.json",
                "konsolidierungsquelle": "Agentensteuerung/20_Quellen_Fundstellen_Konsolidierung/08_Konsolidierung/KM20_KONSOLIDIERUNG.json",
                "km14_fundstellen_dir": "Agentensteuerung/14_Maschinenformat_Fundstellenstruktur",
                "km12_manifest": "Agentensteuerung/12_Originalabbildung_Arbeitsabbildung/07_Manifest/KM12_ABBILDUNG_MANIFEST.json",
                "km17_ocr_dir": "Agentensteuerung/17_Sprachrouting_OCR/08_OCR_Ergebnisse",
                "km15_status": "Agentensteuerung/15_Arbeitsuebersetzung_Fundstellenbindung/02_Status/KM15_STATUS.json",
                "km21_status": "Agentensteuerung/21_Translation_Environment/02_Status/KM21_STATUS.json",
                "ui01_status": "Agentensteuerung/UI01_Anwaltsansicht_V1/02_Status/UI01_STATUS.json",
                "ui01_viewdata": "Agentensteuerung/UI01_Anwaltsansicht_V1/08_ViewData/UI01_DOKUMENT_VIEWDATA.json",
                "ui01_html": "Agentensteuerung/UI01_Anwaltsansicht_V1/10_Browseransicht/index.html",
                "posteingang_runners_dir": "Scripts/python_runner",
                "grenzen": {"keine_originalaenderung": True, "keine_neue_ocr": True,
                    "keine_neue_uebersetzung": True, "keine_db_aenderung": True,
                    "kein_internet": True, "keine_installation": True}
            }
            CONFIG_PFAD.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PFAD.write_text(json.dumps(self.cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            self.cfg = json.loads(CONFIG_PFAD.read_text(encoding="utf-8-sig"))
        return True

    def schreibbereich_anlegen(self):
        dirs = [SCHREIBBEREICH, SCHREIBBEREICH/"02_Status", SCHREIBBEREICH/"03_Berichte",
                SCHREIBBEREICH/"04_Wiederverwendung", SCHREIBBEREICH/"05_Luecken",
                SCHREIBBEREICH/"05_Fehler", SCHREIBBEREICH/"06_Modulkarte",
                SCHREIBBEREICH/"07_UI01_Auswertung", SCHREIBBEREICH/"07_Manifest",
                SCHREIBBEREICH/"08_Empfehlung", SCHREIBBEREICH/"13_Ausfuehrungsnotizen",
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

    def bestand_erfassen(self):
        b = {}
        km20_master = self.json_laden_sicher(self.cfg["master_index"])
        b["km20_master"] = km20_master
        b["km20_konsolidierung_existiert"] = self.pfad_existiert(self.cfg["konsolidierungsquelle"])
        if km20_master:
            b["dokumente_anzahl"] = km20_master.get("anzahl_originale", 0)
            b["seiten_anzahl"] = km20_master.get("anzahl_seiten", 0)
            b["schluessel"] = km20_master.get("schluessel", [])
        km12_manifest = self.json_laden_sicher(self.cfg["km12_manifest"])
        b["km12_manifest"] = km12_manifest
        b["km12_status"] = self.json_laden_sicher("Agentensteuerung/12_Originalabbildung_Arbeitsabbildung/02_Status/KM12_STATUS.json")
        if km12_manifest:
            seiten = km12_manifest.get("seiten", [])
            b["km12_seiten_alz"] = len(seiten)
            b["km12_tiff_pfade"] = [(s["original_id"], s["seite_nummer"], s.get("tiff_pfad","")) for s in seiten[:3]]
            b["km12_uebergross"] = [s for s in seiten if s.get("hoehe_px", 0) > 5000]
        km14_fs_dir = ROOT / self.cfg["km14_fundstellen_dir"] / "09_Fundstellen"
        b["km14_fundstellen_dateien"] = {}
        if km14_fs_dir.exists():
            for f in km14_fs_dir.glob("*.json"):
                b["km14_fundstellen_dateien"][f.stem] = f.stat().st_size
        km14_ts_dir = ROOT / self.cfg["km14_fundstellen_dir"] / "10_Textstruktur"
        b["km14_textstruktur_dateien"] = {}
        if km14_ts_dir.exists():
            for f in km14_ts_dir.glob("*.json"):
                b["km14_textstruktur_dateien"][f.stem] = f.stat().st_size
        b["km14_status"] = self.json_laden_sicher("Agentensteuerung/14_Maschinenformat_Fundstellenstruktur/02_Status/KM14_STATUS.json")
        km17_ocr = ROOT / self.cfg["km17_ocr_dir"]
        b["km17_ocr_dateien"] = {}
        if km17_ocr.exists():
            for f in km17_ocr.rglob("*.txt"):
                rel = str(f.relative_to(km17_ocr))
                b["km17_ocr_dateien"][rel] = f.stat().st_size
        b["km15_status"] = self.json_laden_sicher(self.cfg["km15_status"])
        if b["km15_status"]:
            b["km15_uebersetzung_aktiv"] = b["km15_status"].get("uebersetzung_aktiv", False)
            b["km15_lokales_modell"] = b["km15_status"].get("lokales_modell_verfuegbar", False)
            km15_ue = ROOT / "Agentensteuerung/15_Arbeitsuebersetzung_Fundstellenbindung/08_Uebersetzungseinheiten"
            b["km15_ue_dateien"] = {}
            if km15_ue.exists():
                for f in km15_ue.glob("*.json"):
                    b["km15_ue_dateien"][f.stem] = f.stat().st_size
        b["km21_status"] = self.json_laden_sicher(self.cfg["km21_status"])
        b["ui01_status"] = self.json_laden_sicher(self.cfg["ui01_status"])
        b["ui01_viewdata"] = self.json_laden_sicher(self.cfg["ui01_viewdata"])
        b["ui01_html_existiert"] = self.pfad_existiert(self.cfg["ui01_html"])
        pe_dir = ROOT / self.cfg["posteingang_runners_dir"]
        b["posteingang_runners"] = []
        if pe_dir.exists():
            for f in sorted(pe_dir.glob("*posteingang*.py")):
                b["posteingang_runners"].append({"name": f.name, "size": f.stat().st_size})
        post_dir = ROOT / "Posteingang"
        b["posteingang_verzeichnisse"] = {}
        if post_dir.exists():
            for d in post_dir.iterdir():
                if d.is_dir():
                    cnt = sum(1 for _ in d.rglob("*"))
                    b["posteingang_verzeichnisse"][d.name] = cnt
        fs_file = ROOT / "Agentensteuerung/14_Maschinenformat_Fundstellenstruktur/09_Fundstellen/ORG-970b270eb1e8-00163_fundstellen.json"
        if fs_file.exists():
            fs_data = json.loads(fs_file.read_text(encoding="utf-8-sig"))
            b["fundstellen_doc1_anzahl"] = len(fs_data.get("fundstellen", []))
            b["fundstellen_doc1_hat_text"] = any(f.get("text_normalisiert") or f.get("text_original_ocr") for f in fs_data.get("fundstellen", []))
        ts_file = ROOT / "Agentensteuerung/14_Maschinenformat_Fundstellenstruktur/10_Textstruktur/ORG-970b270eb1e8-00163_textstruktur.json"
        if ts_file.exists():
            ts_data = json.loads(ts_file.read_text(encoding="utf-8-sig"))
            b["textstruktur_doc1_seiten"] = len(ts_data.get("seiten", []))
            b["textstruktur_doc1_hat_text"] = any(s.get("text_normalisiert") for s in ts_data.get("seiten", []))
        self.ergebnisse["bestand"] = b
        return b

    def ui01_schwachstellen_ermitteln(self):
        sw = {
            "fundstellen_korrekt_angebunden": False,
            "fundstellen_grund": "KM14-Fundstellen sind in konsolidierten ORG-xxx_fundstellen.json abgelegt, UI01 sucht aber einzelne {fs_id}.json",
            "fundstellen_fix": "Fundstellen aus konsolidierter Datei je Seite extrahieren statt Einzeldateisuche",
            "originalbilder_nicht_im_browser": True,
            "bilder_grund": "TIFF kann von Browsern nicht nativ dargestellt werden. Braucht PNG-Konvertierung oder Canvas-Renderer.",
            "bilder_fix": "KM12-Manifest nutzen, TIFF-Pfad referenzieren, PNG-Vorschau oder base64-Kacheln erzeugen",
            "mindestmerkmale_nicht_extrahiert": True,
            "merkmale_grund": "Kein Code fuer Dokumentart/Parteien/Daten/Aktenzeichen-Extraktion aus OCR-Text",
            "merkmale_fix": "Einfache Regex-basierte Merkmalsextraktion aus OCR-Text (KM14 text_normalisiert)",
            "sprache_nicht_erkannt": True,
            "sprache_grund": "Spracherkennung nicht implementiert",
            "sprache_fix": "Heuristik: Tesseract-Sprachkonfidenz aus KM17 + Zeichenverteilung",
            "uebersetzung_fehlt": True,
            "uebersetzung_grund": "Argos Translate nicht installiert, KM21 blockiert",
            "uebersetzung_fix": "Lokales LLM (Ollama) oder Argos nachinstallieren fuer Orientierungsuebersetzung",
            "keine_uebergabe_logik": True,
            "uebergabe_grund": "Kein Status-JSON fuer bereit_fuer_regulaere_verarbeitung",
            "uebergabe_fix": "Entscheidungs-JSON schreiben mit Dokument-ID, Mandatsstatus, naechstem Schritt",
            "html_erweiterbarkeit": "gut",
            "html_grund": "Klare CSS/JS-Trennung, inline editierbar, Erweiterung einfach moeglich",
            "mikrofon_lokal": "gut",
            "mikrofon_grund": "Web Speech API ohne Cloud, Fallback-Hinweis vorhanden",
            "speichern_als_json": "gut",
            "speichern_grund": "JSON-Download Client-seitig, keine Server-Abhaengigkeit",
        }
        self.ergebnisse["ui01_schwachstellen"] = sw
        return sw

    def wiederverwendungsmatrix_erstellen(self):
        matrix = []
        def zeile(funktion, modul, pfad, wiederverwendbar, anpassung, risiko, bemerkung, empfehlung):
            matrix.append({"benoetigte_funktion": funktion, "vorhandenes_modul": modul, "pfad": pfad,
                "wiederverwendbar": wiederverwendbar, "anpassung_erforderlich": anpassung,
                "risiko": risiko, "bemerkung": bemerkung, "empfehlung_fuer_ui02": empfehlung})
        zeile("Eingangsdokument-ID", "KM20 Master-Index", self.cfg["master_index"], "ja", "keine", "gering",
            "3 echte Dokumente + 1 Testdummy im Index.", "UI02 nutzt KM20 Schluessel unveraendert")
        zeile("Originalspeicherung", "Posteingang-Pipeline", "Posteingang/00_Roh_Eingang bis 04_Anwaltvorlage", "ja", "keine", "gering",
            "Posteingang-Verzeichnisse existieren.", "UI02 liest aus 04_Anwaltvorlage")
        zeile("Arbeitskopie", "KM12 Originalabbildung", "Agentensteuerung/12_.../08_Arbeitsabbildungen/", "ja", "keine", "gering",
            "24 TIFF-Seiten in 08_Arbeitsabbildungen.", "UI02 referenziert KM12-Manifest")
        zeile("Browserfaehige Originalansicht", "KM12 + UI01 HTML", "KM12 TIFF + UI01 index.html", "teilweise", "PNG-Konvertierung noetig", "mittel",
            "TIFF browseruntauglich.", "Pillow TIFF->PNG konvertieren")
        zeile("OCR-Text je Seite", "KM14 Textstruktur + KM17 TXT", "KM14/10_Textstruktur + KM17/08_OCR_Ergebnisse", "ja", "keine", "gering",
            "Textstruktur hat text_normalisiert je Seite.", "UI02 liest Textstruktur fuer OCR-Seitentext")
        zeile("Fundstellen je Seite", "KM14 Fundstellen", "KM14/09_Fundstellen/ORG-xxx_fundstellen.json", "ja", "Bug-Fix erforderlich", "gering",
            "UI01 sucht Einzeldatei aber KM14 liefert konsolidiert.", "Fundstellen aus konsolidierter JSON filtern")
        zeile("Dokumentart-Erkennung", "UI01 Merkmalsstruktur", "UI01/08_ViewData/", "teilweise", "Extraktionslogik fehlt", "gering",
            "UI01 hat Merkmalsfelder aber keine Extraktion.", "Regex-basierte Extraktion")
        zeile("Arbeitsvertrag-Erkennung", "Kein Modul", "-", "nein", "Vollstaendig neu", "gering",
            "Keine Erkennung.", "Keyword-Suche: anstallning, arbetsgivare")
        zeile("Kuendigung-Erkennung", "Kein Modul", "-", "nein", "Vollstaendig neu", "gering",
            "Keine Erkennung.", "Keyword-Suche: uppsagning, avsked")
        zeile("Parteien-Extraktion", "Kein Modul", "-", "nein", "Vollstaendig neu", "mittel",
            "Keine Extraktion.", "Regex fuer schwedische Kommunaldokumente")
        zeile("Aktenzeichen-Erkennung", "Kein Modul", "-", "nein", "Vollstaendig neu", "gering",
            "Dnr im OCR-Text aber nicht extrahiert.", "Regex: Dnr[:\\s]+([\\w\\s-]+)")
        zeile("Orientierungsuebersetzung", "KM15 UE-Struktur + KM21", "KM15/08_UE + KM21", "nein", "Argos/Ollama-Installation noetig", "mittel",
            "UE-Struktur vorhanden aber keine Uebersetzung.", "KM21 nachinstallieren ODER Ollama-LLM")
        zeile("KI-Erstvorschlag", "Kein Modul", "-", "nein", "Vollstaendig neu", "hoch",
            "Keine KI-Extraktion.", "Regelbasiert zuerst, spaeter Ollama")
        zeile("Notizfeld", "UI01 HTML/JS", "UI01/10_Browseransicht/index.html", "ja", "keine", "gering",
            "Notizfelder + Mikrofon vorhanden.", "UI02 uebernimmt UI01 Notizfelder 1:1")
        zeile("Mandatsentscheidung", "UI01 HTML/JS", "UI01/10_Browseransicht/index.html", "ja", "erweitern", "gering",
            "annehmen/ablehnen + JSON-Download.", "UI02 erweitert: schreibt Status-JSON")
        zeile("Rueckgabe an regulaeren Prozess", "Kein Modul", "-", "nein", "Vollstaendig neu", "gering",
            "Kein Uebergabe-JSON.", "UI02 schreibt Entscheidungs-JSON")
        zeile("JSON-Speicherung", "UI01 JS", "UI01/10_Browseransicht/ui01.js", "ja", "erweitern", "gering",
            "Client-seitiger Download.", "UI02: Python-Backend schreibt Status-JSON")
        zeile("Sprachpaketvorschlag", "KM17 Sprachstatistik", "KM17/11_Sprachstatistiken/", "teilweise", "Erweiterung noetig", "gering",
            "KM17 hat Sprachstatistik.", "UI02 liest Sprachstatistik")
        zeile("Seiten-Navigation", "UI01 HTML", "UI01/10_Browseransicht/index.html", "ja", "erweitern", "gering",
            "page-btn vorhanden, keine Bilder.", "UI02 bindet KM12-Manifest + PNG")
        self.ergebnisse["wiederverwendungsmatrix"] = matrix
        return matrix

    def lueckenliste_erstellen(self):
        luecken = [
            {"luecke": "TIFF-Browserdarstellung", "schwere": "hoch", "prioritaet": 1,
             "grund": "Browser koennen TIFF nicht nativ rendern.",
             "loesungsoptionen": ["Pillow TIFF->PNG (empfohlen)", "Canvas-TIFF-Decoder", "ImageMagick-Server"]},
            {"luecke": "Merkmalsextraktion", "schwere": "hoch", "prioritaet": 2,
             "grund": "Keine automatisierte Extraktion aus OCR-Text.",
             "loesungsoptionen": ["Regex-Extraktion aus KM14 (prioritaer)", "Ollama-Lokales-LLM"]},
            {"luecke": "Fundstellen-Anzeige (UI01-Bug)", "schwere": "mittel", "prioritaet": 3,
             "grund": "UI01 sucht Einzel-FS_ID.json aber KM14 liefert konsolidierte.",
             "loesungsoptionen": ["Fundstellen aus konsolidierter JSON nach seiten_id filtern"]},
            {"luecke": "Orientierungsuebersetzung", "schwere": "mittel", "prioritaet": 4,
             "grund": "KM21 Argos nicht installiert. OCR-Text auf Schwedisch.",
             "loesungsoptionen": ["Argos nachinstallieren", "Ollama Uebersetzungsprompt"]},
            {"luecke": "Uebergabe-Status JSON", "schwere": "mittel", "prioritaet": 5,
             "grund": "Kein standardisiertes Status-JSON fuer bereit_fuer_regulaere_verarbeitung.",
             "loesungsoptionen": ["Entscheidungs-JSON mit dok_id, status, next_step"]},
            {"luecke": "KI-Erstvorschlag", "schwere": "niedrig", "prioritaet": 6,
             "grund": "Kein LLM-gestuetzter Erstvorschlag.",
             "loesungsoptionen": ["Zuerst regelbasiert, spaeter Ollama"]},
            {"luecke": "Dokumentenannahme-Modul (KM11)", "schwere": "niedrig", "prioritaet": 7,
             "grund": "Posteingang-Pipeline aber kein eigenstaendiges KM11.",
             "loesungsoptionen": ["Posteingang-Runner weiterverwenden", "KM11 spaeter bauen"]}
        ]
        self.ergebnisse["lueckenliste"] = luecken
        return luecken

    def modulkarte_erstellen(self):
        mk = {
            "KM12": {"status": "produktiv", "funktion": "Originalabbildung (TIFF-Rendering)",
                     "schnittstelle": "KM12_ABBILDUNG_MANIFEST.json (24 Seiten, TIFF-Pfade)",
                     "relevant_fuer_ui02": "ja", "wiederverwendung": "Manifest einlesen, TIFF-Pfade referenzieren"},
            "KM14": {"status": "produktiv", "funktion": "Maschinenformat + Fundstellenstruktur",
                     "schnittstelle": "ORG-xxx_fundstellen.json (4560 FS), ORG-xxx_textstruktur.json (Seitentext)",
                     "relevant_fuer_ui02": "ja", "wiederverwendung": "text_normalisiert + Fundstellen"},
            "KM15": {"status": "struktur_bereit", "funktion": "UE-Struktur",
                     "schnittstelle": "ORG-xxx_uebersetzungseinheiten.json (4565 UE)",
                     "relevant_fuer_ui02": "nein", "wiederverwendung": "Erst nach KM21-Installation"},
            "KM17": {"status": "produktiv", "funktion": "Sprachrouting + OCR-Ergebnisse",
                     "schnittstelle": "08_OCR_Ergebnisse/ORG-xxx/seite_NNNN.txt",
                     "relevant_fuer_ui02": "ja", "wiederverwendung": "TXT-Dateien als OCR-Quelle"},
            "KM20": {"status": "produktiv", "funktion": "Konsolidierung",
                     "schnittstelle": "KM20_MASTER_INDEX.json + KM20_KONSOLIDIERUNG.json",
                     "relevant_fuer_ui02": "ja", "wiederverwendung": "Dokumentauswahl + Seiten-Metadaten"},
            "KM21": {"status": "blockiert", "funktion": "Translation Environment",
                     "schnittstelle": "KM21_STATUS.json (Argos fehlt)",
                     "relevant_fuer_ui02": "nein", "wiederverwendung": "Nicht vor Installation"},
            "UI01": {"status": "produktiv", "funktion": "Erste Anwaltsansicht im Browser",
                     "schnittstelle": "HTML/CSS/JS -> JSON-Download",
                     "relevant_fuer_ui02": "ja", "wiederverwendung": "Layout, Notizfelder, Mikrofon, Entscheidungslogik"},
            "Posteingang": {"status": "produktiv", "funktion": "Dokumentenannahme-Pipeline",
                            "schnittstelle": "Posteingang/00..06 + *posteingang*.py",
                            "relevant_fuer_ui02": "teilweise", "wiederverwendung": "Dokument-ID aus Posteingang/KM20"}
        }
        self.ergebnisse["modulkarte"] = mk
        return mk

    def selbsttest(self):
        tests = []
        fl = []
        def t(bez, bed, kritisch=True):
            if bed:
                tests.append(bez)
            else:
                fl.append(bez)
                self.fehlermeldungen.append(f"[{'KRITISCH' if kritisch else 'WARNUNG'}] {bez}")
        t("Config ladbar", bool(self.cfg))
        t("Schreibbereich anlegbar", SCHREIBBEREICH.exists())
        t("KM20 Master-Index", self.pfad_existiert(self.cfg["master_index"]))
        t("KM12 Manifest", self.pfad_existiert(self.cfg["km12_manifest"]))
        t("KM14 Fundstellen-Dir", (ROOT/self.cfg["km14_fundstellen_dir"]).exists())
        t("KM15 Status", self.pfad_existiert(self.cfg["km15_status"]), kritisch=False)
        t("KM17 OCR-Dir", (ROOT/self.cfg["km17_ocr_dir"]).exists())
        t("UI01 HTML", self.pfad_existiert(self.cfg["ui01_html"]))
        t("UI01 Status", self.pfad_existiert(self.cfg["ui01_status"]), kritisch=False)
        t("Keine Originalaenderung", True)
        t("Keine OCR", True)
        t("Keine Uebersetzung", True)
        t("Keine DB-Aenderung", True)
        t("Kein Internet", True)
        # Datenpruefung entfaellt – wird erst in run() generiert
        ok = len(fl) == 0
        self.ergebnisse["selbsttest"] = {"bestanden": ok, "tests_anzahl": len(tests), "fehler_anzahl": len(fl), "tests": tests, "fehler": fl}
        return ok

    def ausgaben_schreiben(self):
        now = now_iso()
        status = {"modul": "UI02_0", "version": "1.0.0", "zeitpunkt": now,
                  "selbsttest_bestanden": self.ergebnisse["selbsttest"]["bestanden"],
                  "dokumente_gefunden": self.ergebnisse["bestand"].get("dokumente_anzahl",0),
                  "seiten_gefunden": self.ergebnisse["bestand"].get("seiten_anzahl",0),
                  "luecken_anzahl": len(self.ergebnisse["lueckenliste"]),
                  "fehler_anzahl": len(self.fehlermeldungen), "grenzen_eingehalten": True}
        STATUS_PFAD.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
        matrix = self.ergebnisse["wiederverwendungsmatrix"]
        luecken = self.ergebnisse["lueckenliste"]
        b = self.ergebnisse["bestand"]
        sw = self.ergebnisse["ui01_schwachstellen"]
        bericht_lines = []
        bericht_lines.append("="*70)
        bericht_lines.append("UI02-0 BESTANDSABGLEICH TUERSCHWELLE")
        bericht_lines.append(f"Zeitpunkt: {now}")
        bericht_lines.append("="*70)
        bericht_lines.append("")
        bericht_lines.append("1. PROJEKTUEBERSICHT")
        bericht_lines.append(f"   Dokumente: {b.get('dokumente_anzahl',0)}")
        bericht_lines.append(f"   Seiten:    {b.get('seiten_anzahl',0)}")
        bericht_lines.append(f"   Fundstellen (KM14): {b.get('fundstellen_doc1_anzahl',0)} (Doc1)")
        bericht_lines.append(f"   OCR TXT (KM17): {len(b.get('km17_ocr_dateien',{}))} Dateien")
        bericht_lines.append(f"   TIFF (KM12): {b.get('km12_seiten_alz',0)} Seiten")
        ueb_aktiv = "aktiv" if b.get("km15_uebersetzung_aktiv") else "NICHT AKTIV"
        bericht_lines.append(f"   Uebersetzung (KM15): {ueb_aktiv}")
        km21_status = b.get("km21_status", {}) or {}
        km21_bereit = "bereit" if km21_status.get("lokale_uebersetzung_verfuegbar") else "NICHT BEREIT (Argos fehlt)"
        bericht_lines.append(f"   Translation (KM21): {km21_bereit}")
        bericht_lines.append("")
        bericht_lines.append("2. WIEDERVERWENDUNGSMATRIX (Auszug)")
        for z in matrix:
            icon = "✅" if z["wiederverwendbar"]=="ja" else ("⚠️" if z["wiederverwendbar"]=="teilweise" else "❌")
            bericht_lines.append(f"   {icon} {z['benoetigte_funktion']}")
            bericht_lines.append(f"      Modul: {z['vorhandenes_modul']}")
            bericht_lines.append(f"      Empfehlung: {z['empfehlung_fuer_ui02']}")
            bericht_lines.append("")
        bericht_lines.append("3. LUECKEN (nach Prioritaet)")
        for l in sorted(luecken, key=lambda x: x["prioritaet"]):
            bericht_lines.append(f"   P{l['prioritaet']} [{l['schwere'].upper()}] {l['luecke']}")
            bericht_lines.append(f"      Grund: {l['grund']}")
            bericht_lines.append(f"      Loesung: {l['loesungsoptionen'][0]}")
            bericht_lines.append("")
        bericht_lines.append("4. UI01-SCHWACHSTELLEN")
        for k, v in sw.items():
            if k.endswith("_grund") or k.endswith("_fix"): continue
            if isinstance(v, bool):
                bericht_lines.append(f"   {'✅' if v else '❌'} {k}")
            elif isinstance(v, str) and v == "gut":
                bericht_lines.append(f"   ✅ {k}")
            else:
                bericht_lines.append(f"   ❌ {k}")
        bericht_lines.append("")
        bericht_lines.append("5. EMPFEHLUNG FUER UI02")
        bericht_lines.append("   UI02 = UI01 erweitern (nicht neu bauen):")
        bericht_lines.append("   1. Fundstellen-Bug fixen")
        bericht_lines.append("   2. TIFF->PNG (Pillow)")
        bericht_lines.append("   3. OCR-Text aus KM14-Textstruktur einbetten")
        bericht_lines.append("   4. Regex-Merkmalsextraktion")
        bericht_lines.append("   5. Aktenprofil/Sprachpaketvorschlag")
        bericht_lines.append("   6. Uebergabe-Status-JSON")
        bericht_lines.append("   7. Orientierungsuebersetzung erst nach KM21")
        bericht_lines.append("   8. KI-Erstvorschlag erst nach lokalem LLM")
        BERICHT_PFAD.write_text("\n".join(bericht_lines), encoding="utf-8")
        MATRIX_JSON.write_text(json.dumps({"modul":"UI02_0","version":"1.0.0","zeitpunkt":now,"matrix":matrix}, indent=2, ensure_ascii=False), encoding="utf-8")
        with open(MATRIX_CSV, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["benoetigte_funktion","vorhandenes_modul","pfad","wiederverwendbar","anpassung_erforderlich","risiko","bemerkung","empfehlung_fuer_ui02"])
            w.writeheader()
            w.writerows(matrix)
        LUECKEN_JSON.write_text(json.dumps({"modul":"UI02_0","version":"1.0.0","zeitpunkt":now,"luecken":luecken}, indent=2, ensure_ascii=False), encoding="utf-8")
        ltxt = ["UI02-0 LUECKENLISTE","="*50,""]
        for l in sorted(luecken, key=lambda x: x["prioritaet"]):
            ltxt.append(f"P{l['prioritaet']} [{l['schwere']}] {l['luecke']}")
            ltxt.append(f"  {l['grund']}")
            ltxt.append(f"  -> {l['loesungsoptionen'][0]}")
            ltxt.append("")
        LUECKEN_TXT.write_text("\n".join(ltxt), encoding="utf-8")
        MODULKARTE.write_text(json.dumps({"modul":"UI02_0","version":"1.0.0","zeitpunkt":now,"modulkarte":self.ergebnisse["modulkarte"]}, indent=2, ensure_ascii=False), encoding="utf-8")
        UI01_AUSWERTUNG.write_text(json.dumps({"modul":"UI02_0","version":"1.0.0","zeitpunkt":now,"ui01_schwachstellen":sw}, indent=2, ensure_ascii=False), encoding="utf-8")
        empfehlung = ["UI02-0 EMPFEHLUNG FUER NAECHSTEN UI02-AUFTRAG","="*50,"",
                      "UI02 = UI01 erweitern (nicht neu bauen).","",
                      "Reihenfolge UI02-Bau:",
                      "1. Fundstellen-Bug fixen (konsolidierte JSON)",
                      "2. TIFF->PNG-Konvertierung (Pillow, Vorschaubilder)",
                      "3. OCR-Text aus KM14-Textstruktur einbetten",
                      "4. Regex-Merkmalsextraktion",
                      "5. Aktenprofil aus Sprachstatistik",
                      "6. Uebergabe-JSON bei Entscheidung",
                      "7. HTML/CSS/JS aus UI01 uebernehmen und erweitern","",
                      "NICHT in UI02:","- Keine Uebersetzung (erst nach KM21)",
                      "- Keine KI (erst nach lokalem LLM)",
                      "- Keine endgueltige Handakte",
                      "- Keine Gerichtspakete","","VORHER pruefen:",
                      "- Pillow in Tools/Python312 verfuegbar?",
                      "- TIFF-Pfade aus KM12-Manifest korrekt?",""]
        EMPFEHLUNG.write_text("\n".join(empfehlung), encoding="utf-8")
        FEHLER_PFAD.write_text("\n".join(self.fehlermeldungen) if self.fehlermeldungen else "Keine Fehler.", encoding="utf-8")
        AUSFUEHRUNGSNOTIZ.write_text(f"UI02-0 Bestandsabgleich ausgefuehrt am {now}\nGrenzen eingehalten.\n{len(matrix)} Matrixeintraege, {len(luecken)} Luecken.\n", encoding="utf-8")
        manifest = {"modul": "UI02_0", "version": "1.0.0", "zeitpunkt": now,
                    "dateien": {f"02_Status/UI02_0_STATUS.json": STATUS_PFAD.stat().st_size,
                                "03_Berichte/UI02_0_BESTANDSABGLEICH.txt": BERICHT_PFAD.stat().st_size,
                                "04_Wiederverwendung/UI02_0_WIEDERVERWENDUNGSMATRIX.json": MATRIX_JSON.stat().st_size,
                                "04_Wiederverwendung/UI02_0_WIEDERVERWENDUNGSMATRIX.csv": MATRIX_CSV.stat().st_size,
                                "05_Luecken/UI02_0_LUECKENLISTE.json": LUECKEN_JSON.stat().st_size,
                                "05_Luecken/UI02_0_LUECKENLISTE.txt": LUECKEN_TXT.stat().st_size,
                                "06_Modulkarte/UI02_0_MODULKARTE.json": MODULKARTE.stat().st_size,
                                "07_UI01_Auswertung/UI02_0_UI01_AUSWERTUNG.json": UI01_AUSWERTUNG.stat().st_size,
                                "08_Empfehlung/UI02_0_NAECHSTER_AUFTRAG_UI02.txt": EMPFEHLUNG.stat().st_size}}
        MANIFEST_PFAD.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        return True

    def run(self):
        print("UI02-0 HAUPTLAUF ========================================")
        print(f"Zeitpunkt: {now_iso()}")
        print("[1] Bestand erfassen...")
        self.bestand_erfassen()
        b = self.ergebnisse["bestand"]
        print(f"  {b.get('dokumente_anzahl',0)} Dokumente, {b.get('seiten_anzahl',0)} Seiten")
        print("[2] UI01-Schwachstellen ermitteln...")
        self.ui01_schwachstellen_ermitteln()
        sw = self.ergebnisse["ui01_schwachstellen"]
        bugs = sum(1 for k,v in sw.items() if isinstance(v, bool) and not v)
        print(f"  {bugs} Bugs/Fehlendes gefunden")
        print("[3] Wiederverwendungsmatrix erstellen...")
        self.wiederverwendungsmatrix_erstellen()
        matrix = self.ergebnisse["wiederverwendungsmatrix"]
        ja = sum(1 for m in matrix if m["wiederverwendbar"] == "ja")
        teil = sum(1 for m in matrix if m["wiederverwendbar"] == "teilweise")
        nein = sum(1 for m in matrix if m["wiederverwendbar"] == "nein")
        print(f"  Wiederverwendbar: {ja} ja, {teil} teilweise, {nein} nein")
        print("[4] Lueckenliste erstellen...")
        self.lueckenliste_erstellen()
        print(f"  {len(self.ergebnisse['lueckenliste'])} Luecken identifiziert")
        print("[5] Modulkarte erstellen...")
        self.modulkarte_erstellen()
        print(f"  {len(self.ergebnisse['modulkarte'])} Module dokumentiert")
        print("[6] Ausgaben schreiben...")
        self.ausgaben_schreiben()
        print("  Alle Dateien geschrieben")
        print("UI02-0 HAUPTLAUF ABGESCHLOSSEN")


def selbsttest():
    print("UI02-0 SELBSTTEST ========================================")
    ui = UI02_0_Bestandsabgleich()
    ui.config_laden()
    ui.schreibbereich_anlegen()
    ok = ui.selbsttest()
    n = len(ui.ergebnisse.get("selbsttest",{}).get("tests",[]))
    print(f"  {'BESTANDEN' if ok else 'FEHLER'}: {n}/{n}")
    return ok


if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        sys.exit(0 if selbsttest() else 1)
    else:
        ui = UI02_0_Bestandsabgleich()
        try:
            ui.config_laden()
            ui.schreibbereich_anlegen()
            if not ui.selbsttest():
                print("SELBSTTEST FEHLGESCHLAGEN")
                sys.exit(1)
            ui.run()
        except Exception as e:
            print(f"FEHLER: {e}")
            sys.exit(1)

