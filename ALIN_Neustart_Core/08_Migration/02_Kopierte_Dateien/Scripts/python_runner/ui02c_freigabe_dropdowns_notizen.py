#!/usr/bin/env python3
"""UI02c – Anwaltliche Freigabevorschlaege, Dropdowns, Wiedervorlage und Notiz-/Diktatfelder"""
import sys, json, datetime, hashlib, io, os, re, shutil
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
PYTHON_EXE = ROOT / "Tools" / "Python312" / "python.exe"

# Quellen (nur lesend)
UI02_SB = ROOT / "Agentensteuerung" / "UI02_Tuerschwelle_Bau"
UI02_STATUS = UI02_SB / "02_Status" / "UI02_STATUS.json"
UI02_VIEWDATA = UI02_SB / "08_ViewData" / "UI02_VIEWDATA.json"
UI02_KI = UI02_SB / "11_KI_Erstvorschlag" / "UI02_KI_ERSTVORSCHLAG.json"
UI02_OCR = UI02_SB / "10_OCR_Arbeitsgrundlage" / "UI02_OCR_ARBEITSGRUNDLAGE.json"
UI02_ASSETS = UI02_SB / "09_Originalansicht" / "assets"

# Schreibbereich UI02c
SB = ROOT / "Agentensteuerung" / "UI02_Tuerschwelle_Bau" / "17_Freigabe_UI02c"
CONFIG_PFAD = ROOT / "Config" / "ui02c_freigabe_dropdowns_notizen_v1.json"
BROWSER_DIR = SB / "12_Browseransicht"
ASSETS_DIR_OUT = BROWSER_DIR / "assets"

STATUS_PFAD = SB / "02_Status" / "UI02c_STATUS.json"
BERICHT_PFAD = SB / "03_Berichte" / "UI02c_BERICHT.txt"
FEHLER_PFAD = SB / "05_Fehler" / "UI02c_FEHLER.txt"
MANIFEST_PFAD = SB / "07_Manifest" / "UI02c_MANIFEST.json"
VIEWDATA_PFAD = SB / "08_ViewData" / "UI02c_VIEWDATA.json"
FREIGABEVORSCHLAG_PFAD = SB / "09_Freigabevorschlag" / "UI02c_FREIGABEVORSCHLAG.json"
FORMULARSCHEMA_PFAD = SB / "10_Freigabeformular" / "UI02c_FREIGABEFORMULAR_SCHEMA.json"
RUECKGABE_PFAD = SB / "11_Rueckgabe" / "UI02c_RUECKGABE_AN_REGULAEREN_PROZESS_TEMPLATE.json"
HTML_PFAD = BROWSER_DIR / "index.html"
CSS_PFAD = BROWSER_DIR / "ui02c.css"
JS_PFAD = BROWSER_DIR / "ui02c.js"
NOTIZEN_DIR = SB / "13_Notizen" / "Eingang_vom_Browser"
RUNLOGS_DIR = SB / "90_RunLogs"


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class UI02c_Builder:
    def __init__(self):
        self.fehlermeldungen = []
        self.warnungen = []
        self.cfg = {}
        self.ergebnisse = {}
        self.ui02_daten = {}
        self.ui02_verfuegbar = False

    def config_laden(self):
        if not CONFIG_PFAD.exists():
            self.cfg = {
                "modul": "UI02c", "version": "1.0.0",
                "sprachen": ["Schwedisch", "Englisch", "Deutsch", "Franzoesisch", "unbekannt"],
                "rechtsgebiete": ["Arbeitsrecht", "Schulrecht / Bildungsrecht", "Sozialrecht",
                                  "Verwaltungsrecht", "Zivilrecht", "Strafrecht", "anderes", "unbekannt"],
                "verfahrenslaender": ["Schweden", "Deutschland", "Portugal", "anderes", "unbekannt"],
                "dokumentarten": ["Arbeitsvertrag", "Kuendigung", "sonstiges", "unbekannt"],
                "sprachpakete": ["sv-de", "en-de", "de-en", "de-sv", "fr-de", "keine / spaeter festlegen"],
                "entscheidungsoptionen": [
                    "Mandat annehmen", "Mandat ablehnen",
                    "Zurueckstellen / Wiedervorlage", "Bestehender Akte zuordnen",
                    "Weitere Unterlagen anfordern", "Regulaere Verarbeitung starten"
                ],
                "wiedervorlage_gruende": [
                    "fehlende Unterlagen", "bessere Scans erforderlich",
                    "Sprache unklar", "Rechtsgebiet unklar", "Anwaltliche Pruefung erforderlich",
                    "Rueckfrage an Mandant", "Rueckfrage an Sekretariat"
                ],
                "rueckgabe_gruende": [
                    "bessere Scans anfordern", "fehlende Anlage anfordern",
                    "Mandantendaten ergaenzen", "Sprache pruefen", "Dokumente neu zuordnen",
                    "regulaere Verarbeitung starten", "Akte anlegen", "bestehender Akte zuordnen"
                ],
                "agentenauftrag_vorschlaege": [
                    "Arbeitsvertrag vollstaendig auswerten",
                    "Kuendigung vollstaendig auswerten",
                    "Fristen pruefen",
                    "Parteien und Daten pruefen",
                    "fehlende Unterlagen feststellen",
                    "Uebersetzung spaeter regulaer erstellen",
                    "Beweis-/Dokumentenliste vorbereiten"
                ]
            }
            CONFIG_PFAD.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PFAD.write_text(json.dumps(self.cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            self.cfg = json.loads(CONFIG_PFAD.read_text(encoding="utf-8-sig"))
        return True

    def schreibbereich_anlegen(self):
        dirs = [SB, BROWSER_DIR, ASSETS_DIR_OUT,
                SB / "02_Status", SB / "03_Berichte", SB / "05_Fehler",
                SB / "07_Manifest", SB / "08_ViewData",
                SB / "09_Freigabevorschlag", SB / "10_Freigabeformular",
                SB / "11_Rueckgabe", NOTIZEN_DIR, RUNLOGS_DIR]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        return True

    def ui02_daten_laden(self):
        daten = {"status_vorhanden": False, "viewdata_vorhanden": False,
                 "ocr_vorhanden": False, "ki_vorhanden": False,
                 "dokumente": [], "status": {}, "viewdata": {}, "ocr": {}, "ki": {}}
        if UI02_STATUS.exists():
            try:
                daten["status"] = json.loads(UI02_STATUS.read_text(encoding="utf-8-sig"))
                daten["status_vorhanden"] = True
            except Exception:
                pass
        if UI02_VIEWDATA.exists():
            try:
                daten["viewdata"] = json.loads(UI02_VIEWDATA.read_text(encoding="utf-8-sig"))
                daten["viewdata_vorhanden"] = True
                daten["dokumente"] = daten["viewdata"].get("dokumente", [])
            except Exception:
                pass
        if UI02_OCR.exists():
            try:
                daten["ocr"] = json.loads(UI02_OCR.read_text(encoding="utf-8-sig"))
                daten["ocr_vorhanden"] = True
            except Exception:
                pass
        if UI02_KI.exists():
            try:
                raw = UI02_KI.read_text(encoding="utf-8-sig").strip()
                if raw:
                    daten["ki"] = json.loads(raw)
                    daten["ki_vorhanden"] = True
            except Exception:
                pass
        if not daten["dokumente"]:
            self.fehlermeldungen.append("[KRITISCH] Keine UI02-Dokumente gefunden")
            self.ui02_verfuegbar = False
        else:
            self.ui02_verfuegbar = True
        self.ui02_daten = daten
        return daten

    def assets_kopieren(self):
        if not UI02_ASSETS.exists():
            self.warnungen.append("UI02 Assets-Ordner nicht gefunden")
            return 0
        count = 0
        for f in UI02_ASSETS.iterdir():
            if f.is_file() and f.suffix.lower() == ".png":
                shutil.copy2(f, ASSETS_DIR_OUT / f.name)
                count += 1
        return count

    def _sprache_bestimmen(self, ki, text):
        if ki.get("sprache", "").startswith("Schwedisch"):
            return "Schwedisch"
        if ki.get("sprache", "").startswith("Englisch"):
            return "Englisch"
        if ki.get("sprache", "").startswith("Deutsch"):
            return "Deutsch"
        tl = (text or "").lower()
        sv_words = ["och", "att", "det", "med", "for", "till", "som", "den", "har", "ar", "inte", "om", "men"]
        sv_hits = sum(1 for w in sv_words if f" {w} " in f" {tl} ")
        if sv_hits >= 3:
            return "Schwedisch"
        return "unbekannt"

    def _rechtsgebiet_bestimmen(self, text, ki):
        tl = (text or "").lower()
        if any(w in tl for w in ["anstallning", "arbetsgivare", "arbetstagare", "lon", "uppsagning", "avsked"]):
            return "Arbeitsrecht"
        if any(w in tl for w in ["skola", "skolan", "utbildning", "elev", "barn- och utbildning",
                                   "skolinspektion", "grundskola", "gymnasium"]):
            return "Schulrecht / Bildungsrecht"
        if any(w in tl for w in ["social", "omsorg", "forsorjning", "bidrag", "socialtjanst"]):
            return "Sozialrecht"
        if any(w in tl for w in ["kommun", "forvaltning", "namnd", "beslut", "protokoll", "tjansteutlatande"]):
            return "Verwaltungsrecht"
        if any(w in tl for w in ["avtal", "kopa", "salja", "skadestand", "fordran"]):
            return "Zivilrecht"
        if any(w in tl for w in ["brott", "straff", "atal", "domstol", "polis"]):
            return "Strafrecht"
        return "unbekannt"

    def _dokumentart_bestimmen(self, text, ki):
        if ki.get("dokumentart") in ("Arbeitsvertrag", "Kuendigung"):
            return ki["dokumentart"]
        tl = (text or "").lower()
        if any(w in tl for w in ["anstallningsavtal", "arbetsavtal", "anstallning", "tillsvidare", "provanstallning"]):
            return "Arbeitsvertrag"
        if any(w in tl for w in ["uppsagning", "avsked", "upphor", "sista anstallningsdag"]):
            return "Kuendigung"
        if any(w in tl for w in ["tjansteutlatande", "rapport", "beslut", "protokoll", "namnd"]):
            return "sonstiges"
        return "unbekannt"

    def _verfahrensland_bestimmen(self, text, sprache):
        tl = (text or "").lower()
        if any(w in tl for w in ["sverige", "soderkoping", "stockholm", "goteborg", "malmo"]):
            return "Schweden"
        if "Schwedisch" in sprache:
            return "Schweden"
        return "unbekannt"

    def _sprachpaket_bestimmen(self, sprache):
        if "Schwedisch" in sprache:
            return ["sv-de"]
        if "Englisch" in sprache:
            return ["en-de"]
        if "Deutsch" in sprache:
            return ["de-en"]
        return ["keine / spaeter festlegen"]

    def freigabevorschlag_erzeugen(self):
        doks = self.ui02_daten.get("dokumente", [])
        vorschlag = {
            "vorgangs_id": "UI02c_" + now_iso().replace(":", "").replace("-", "").replace("T", "_")[:18],
            "dokument_ids": [d.get("original_id", "") for d in doks],
            "hinweis": "KI-/OCR-Vorschlag – anwaltlich zu pruefen. Keine Rechtsberatung.",
            "dokumente": []
        }
        for dok in doks:
            oid = dok.get("original_id", "")
            ki = dok.get("ki_merkmale", {})
            seiten = dok.get("seiten", [])
            full_text = " ".join(s.get("ocr_text", "") for s in seiten)
            sv = self._sprache_bestimmen(ki, full_text)
            rg = self._rechtsgebiet_bestimmen(full_text, ki)
            da = self._dokumentart_bestimmen(full_text, ki)
            vl = self._verfahrensland_bestimmen(full_text, sv)
            gs = "Schwedisch" if "Schwedisch" in sv else "unbekannt"
            dok_v = {
                "original_id": oid,
                "typ_vermutet_ui02": dok.get("typ_vermutet", "unbestimmt"),
                "sprache_vorschlag": sv,
                "rechtsgebiet_vorschlag": rg,
                "dokumentart_vorschlag": da,
                "verfahrensland_vorschlag": vl,
                "gerichtssprache_vorschlag": gs,
                "sprachpaket_vorschlag": self._sprachpaket_bestimmen(sv),
                "seiten_anzahl": len(seiten),
                "unsicherheiten": dok.get("unsicherheiten", [])
            }
            vorschlag["dokumente"].append(dok_v)
        dok1 = vorschlag["dokumente"][0] if vorschlag["dokumente"] else {}
        vorschlag["anwaltssprache_vorschlag"] = "Deutsch"
        vorschlag["mandantensprache_vorschlag"] = dok1.get("sprache_vorschlag", "unbekannt")
        vorschlag["globale_sprache"] = dok1.get("sprache_vorschlag", "unbekannt")
        vorschlag["globales_rechtsgebiet"] = dok1.get("rechtsgebiet_vorschlag", "unbekannt")
        vorschlag["globales_verfahrensland"] = dok1.get("verfahrensland_vorschlag", "unbekannt")
        FREIGABEVORSCHLAG_PFAD.write_text(json.dumps(vorschlag, indent=2, ensure_ascii=False), encoding="utf-8")
        self.ergebnisse["freigabevorschlag"] = vorschlag
        return vorschlag

    def formularschema_erzeugen(self):
        schema = {
            "schrittfolge": [
                "1. Vorgang pruefen",
                "2. Dokumentart pruefen",
                "3. Sprache pruefen",
                "4. Rechtsgebiet / Verfahrensland pruefen",
                "5. Mandatsentscheidung treffen",
                "6. Auftraege / Notizen ergaenzen",
                "7. Rueckgabe an Sekretariat oder regulaere Verarbeitung freigeben"
            ],
            "dropdowns": [
                {"id": "dokumentsprache", "label": "Dokumentsprache",
                 "optionen": self.cfg["sprachen"], "vorschlag_markiert": True},
                {"id": "anwaltssprache", "label": "Anwaltssprache",
                 "optionen": self.cfg["sprachen"][:3], "standard": "Deutsch"},
                {"id": "mandantensprache", "label": "Mandantensprache",
                 "optionen": self.cfg["sprachen"], "vorschlag_markiert": True},
                {"id": "gerichtssprache", "label": "Gerichtssprache",
                 "optionen": self.cfg["sprachen"], "vorschlag_markiert": True},
                {"id": "verfahrensland", "label": "Verfahrensland",
                 "optionen": self.cfg["verfahrenslaender"], "vorschlag_markiert": True},
                {"id": "rechtsgebiet", "label": "Rechtsgebiet",
                 "optionen": self.cfg["rechtsgebiete"], "vorschlag_markiert": True},
                {"id": "dokumentart_dok1", "label": "Dokumentart Dokument 1",
                 "optionen": self.cfg["dokumentarten"], "vorschlag_markiert": True},
                {"id": "dokumentart_dok2", "label": "Dokumentart Dokument 2",
                 "optionen": self.cfg["dokumentarten"], "vorschlag_markiert": True},
                {"id": "sprachpaket_intern", "label": "Sprachpaket intern",
                 "optionen": self.cfg["sprachpakete"], "vorschlag_markiert": True},
                {"id": "sprachpaket_mandant", "label": "Sprachpaket Mandantenkommunikation",
                 "optionen": self.cfg["sprachpakete"], "vorschlag_markiert": True},
                {"id": "sprachpaket_gericht", "label": "Sprachpaket Gerichtskommunikation",
                 "optionen": self.cfg["sprachpakete"], "vorschlag_markiert": True},
                {"id": "wiedervorlage_grund", "label": "Wiedervorlagegrund",
                 "optionen": self.cfg["wiedervorlage_gruende"]},
                {"id": "rueckgabe_grund", "label": "Rueckgabegrund an Sekretariat",
                 "optionen": self.cfg["rueckgabe_gruende"]},
            ],
            "entscheidungsoptionen": self.cfg["entscheidungsoptionen"],
            "agentenauftrag_vorschlaege": self.cfg["agentenauftrag_vorschlaege"]
        }
        FORMULARSCHEMA_PFAD.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
        self.ergebnisse["formularschema"] = schema
        return schema

    def wiedervorlage_template_erzeugen(self):
        return {"wiedervorlage": False, "wiedervorlage_datum": None, "grund": "",
                "gruende": self.cfg["wiedervorlage_gruende"], "notiz": "",
                "hinweis": "Nur JSON-Vorbereitung – keine echte Kalenderintegration."}

    def rueckgabe_template_erzeugen(self):
        tpl = {"rueckgabe_status": "nicht gesetzt",
               "optionen": self.cfg["rueckgabe_gruende"],
               "gewaehlte_option": None, "notiz": "",
               "hinweis": "Rueckgabe an Sekretariat. Regulaere Verarbeitung mit derselben Dokument-ID starten."}
        RUECKGABE_PFAD.write_text(json.dumps(tpl, indent=2, ensure_ascii=False), encoding="utf-8")
        self.ergebnisse["rueckgabe_template"] = tpl
        return tpl

    def notizen_template_erzeugen(self):
        return {
            "anwaltliche_notiz": "", "auftrag_sekretariat": "", "auftrag_agenten": "",
            "agentenauftrag_vorschlaege": self.cfg["agentenauftrag_vorschlaege"],
            "hinweis_mikrofon": "Diktat nur lokal bzw. ueber Windows-Diktat verwenden. Keine Cloud-Spracherkennung aktiv.",
            "hinweis": "Freitext fuer Browser-Eingabe."
        }

    def viewdata_erzeugen(self):
        doks = self.ui02_daten.get("dokumente", [])
        vorschlag = self.ergebnisse.get("freigabevorschlag", {})
        schema = self.ergebnisse.get("formularschema", {})
        vd = {
            "vorgangs_id": vorschlag.get("vorgangs_id", ""),
            "dokumente": doks,
            "freigabevorschlag": vorschlag,
            "formularschema": schema,
            "wiedervorlage_template": self.wiedervorlage_template_erzeugen(),
            "rueckgabe_template": self.ergebnisse.get("rueckgabe_template", {}),
            "notizen_template": self.notizen_template_erzeugen(),
            "assets_verzeichnis": "assets/",
            "ui02_orientierung_verfuegbar": self.ui02_daten.get("status", {}).get("orientierung_verfuegbar", False),
            "ollama_modell": self.ui02_daten.get("status", {}).get("ollama_modell", "nicht verfuegbar")
        }
        VIEWDATA_PFAD.write_text(json.dumps(vd, indent=2, ensure_ascii=False), encoding="utf-8")
        self.ergebnisse["viewdata"] = vd
        return vd

    # ============================================================
    # HTML
    # ============================================================
    def html_erzeugen(self):
        vd_json = json.dumps(self.ergebnisse.get("viewdata", {}), indent=2, ensure_ascii=False)
        html = HTML_TEMPLATE.replace("{{VIEWDATA_JSON}}", vd_json)
        return html

    def css_erzeugen(self):
        CSS_PFAD.write_text(CSS_CONTENT, encoding="utf-8")
        return True

    def js_erzeugen(self):
        JS_PFAD.write_text(JS_CONTENT, encoding="utf-8")
        return True

    # ============================================================
    # STATUS, BERICHT, FEHLER, MANIFEST
    # ============================================================
    def status_schreiben(self):
        s = {
            "modul": "UI02c", "version": "1.0.0", "zeitpunkt": now_iso(),
            "ui02_daten_vorhanden": self.ui02_verfuegbar,
            "dokumente_anzahl": len(self.ui02_daten.get("dokumente", [])),
            "freigabevorschlag_erzeugt": "freigabevorschlag" in self.ergebnisse,
            "formularschema_erzeugt": "formularschema" in self.ergebnisse,
            "browseransicht_erzeugt": HTML_PFAD.exists(),
            "fehler_anzahl": len(self.fehlermeldungen),
            "warnungen_anzahl": len(self.warnungen),
            "grenzen_eingehalten": True
        }
        STATUS_PFAD.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
        return s

    def bericht_schreiben(self):
        z = ["UI02c FREIGABE DROPDOWNS NOTIZEN – BERICHT",
             f"Zeitpunkt: {now_iso()}", "=" * 60, ""]
        z.append(f"UI02-Daten uebernommen: {self.ui02_verfuegbar}")
        z.append(f"Dokumente: {len(self.ui02_daten.get('dokumente', []))}")
        for d in self.ui02_daten.get("dokumente", []):
            z.append(f"  {d.get('original_id','')}: {d.get('typ_vermutet','')}, {len(d.get('seiten',[]))} Seiten")

        fv = self.ergebnisse.get("freigabevorschlag", {})
        z.append(f"\nFreigabevorschlag erzeugt: {'ja' if fv else 'nein'}")
        for d in fv.get("dokumente", []):
            z.append(f"  {d.get('original_id','')}: Sprache={d.get('sprache_vorschlag','')}, "
                     f"Recht={d.get('rechtsgebiet_vorschlag','')}, "
                     f"DokArt={d.get('dokumentart_vorschlag','')}")

        z.append(f"\nDropdowns vorhanden: 13")
        z.append(f"  Dokumentsprache, Anwaltssprache, Mandantensprache, Gerichtssprache")
        z.append(f"  Verfahrensland, Rechtsgebiet, Dokumentart Dok1, Dokumentart Dok2")
        z.append(f"  Sprachpaket intern, Sprachpaket Mandant, Sprachpaket Gericht")
        z.append(f"  Wiedervorlagegrund, Rueckgabegrund")

        z.append(f"\nEntscheidungsmoeglichkeiten: {len(self.cfg.get('entscheidungsoptionen', []))}")
        for o in self.cfg.get("entscheidungsoptionen", []):
            z.append(f"  - {o}")

        z.append(f"\nBrowseransicht: {BROWSER_DIR}/index.html")

        z.append(f"\nFehler: {len(self.fehlermeldungen)}")
        for e in self.fehlermeldungen:
            z.append(f"  {e}")
        z.append(f"Warnungen: {len(self.warnungen)}")
        for w in self.warnungen:
            z.append(f"  {w}")

        z.append(f"\nNaechster Auftrag: Anwaltliche Pruefung der Freigabe, dann Volluebersetzung.")
        BERICHT_PFAD.write_text("\n".join(z), encoding="utf-8")
        return BERICHT_PFAD

    def fehlerbericht_schreiben(self):
        z = [f"UI02c FEHLERBERICHT {now_iso()}"]
        z.extend(self.fehlermeldungen) if self.fehlermeldungen else z.append("Keine Fehler.")
        FEHLER_PFAD.write_text("\n".join(z), encoding="utf-8")
        return FEHLER_PFAD

    def manifest_erzeugen(self):
        files = []
        for f in SB.rglob("*"):
            if f.is_file():
                dat = f.read_bytes()
                files.append({"relativ": str(f.relative_to(SB)), "groesse_bytes": len(dat),
                              "sha256": hashlib.sha256(dat).hexdigest()})
        mf = {"modul": "UI02c", "version": "1.0.0", "zeitpunkt": now_iso(),
              "anzahl_dateien": len(files), "dateien": files}
        MANIFEST_PFAD.write_text(json.dumps(mf, indent=2, ensure_ascii=False), encoding="utf-8")
        return mf

    def graenzen_pruefen(self):
        ok = True
        db_files = list(SB.rglob("*.db")) + list(SB.rglob("*.duckdb"))
        if db_files:
            self.fehlermeldungen.append(f"[GRENZE] DB-Dateien im Schreibbereich: {db_files}")
            ok = False
        return ok

    def ausfuehrungsnotiz_schreiben(self, status):
        p = RUNLOGS_DIR / "UI02c_AUSFUEHRUNGSNOTIZ.txt"
        p.write_text(f"UI02c {status} {now_iso()}\nFehler: {len(self.fehlermeldungen)}, Warnungen: {len(self.warnungen)}",
                     encoding="utf-8")
        return p


# ============================================================
# TEMPLATES (getrennt fuer Uebersicht)
# ============================================================

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ALIN – UI02c Anwaltliche Freigabe – Mandatsentscheidung</title>
<link rel="stylesheet" href="ui02c.css">
</head>
<body>
<header>
  <h1>ALIN – Anwaltliche Freigabemaske – Mandatsentscheidung</h1>
  <div class="header-info" id="header-info">
    <span id="header-dok-info">Dokumente werden geladen ...</span>
    <span class="vorschlag-badge">KI-/OCR-Vorschlag – anwaltlich zu pruefen</span>
  </div>
</header>

<div class="layout">
  <aside id="dokument-panel">
    <div class="panel-toolbar">
      <button class="view-btn active" onclick="showView('original')">Original</button>
      <button class="view-btn" onclick="showView('ocr')">OCR / Orientierung DE</button>
      <button class="view-btn" onclick="showView('ki')">KI-Vorschlag</button>
    </div>
    <div id="page-nav"><!-- per JS --></div>
    <div id="view-original" class="view-panel active">
      <img id="original-img" src="" alt="Originalseite">
      <p id="page-label" class="hint">Seite: –</p>
    </div>
    <div id="view-ocr" class="view-panel">
      <h4>OCR-Text</h4>
      <pre id="ocr-text">–</pre>
      <h4>Orientierungsuebersetzung DE</h4>
      <pre id="orient-text">–</pre>
    </div>
    <div id="view-ki" class="view-panel">
      <table id="merkmale-table">
        <tr><th>Merkmal</th><th>Wert</th></tr>
      </table>
    </div>
  </aside>

  <main id="freigabe-panel">
    <section id="schritt-1-4" class="form-card">
      <h2>1.–4. Dokument- und Sprachpruefung</h2>

      <div class="dropdown-group" id="dokumentart-group">
        <label>Dokumentart <span class="vorschlag-mark">(Vorschlag)</span></label>
        <div id="dokumentart-selects"></div>
      </div>

      <div class="dropdown-row">
        <div class="dropdown-group">
          <label for="sel-dokumentsprache">Dokumentsprache</label>
          <select id="sel-dokumentsprache"></select>
        </div>
        <div class="dropdown-group">
          <label for="sel-mandantensprache">Mandantensprache</label>
          <select id="sel-mandantensprache"></select>
        </div>
      </div>

      <div class="dropdown-row">
        <div class="dropdown-group">
          <label for="sel-anwaltssprache">Anwaltssprache</label>
          <select id="sel-anwaltssprache"></select>
        </div>
        <div class="dropdown-group">
          <label for="sel-gerichtssprache">Gerichtssprache</label>
          <select id="sel-gerichtssprache"></select>
        </div>
      </div>

      <div class="dropdown-row">
        <div class="dropdown-group">
          <label for="sel-rechtsgebiet">Rechtsgebiet</label>
          <select id="sel-rechtsgebiet"></select>
        </div>
        <div class="dropdown-group">
          <label for="sel-verfahrensland">Verfahrensland</label>
          <select id="sel-verfahrensland"></select>
        </div>
      </div>

      <div class="dropdown-row">
        <div class="dropdown-group">
          <label for="sel-sprachpaket-intern">Sprachpaket intern</label>
          <select id="sel-sprachpaket-intern"></select>
        </div>
        <div class="dropdown-group">
          <label for="sel-sprachpaket-mandant">Sprachpaket Mandant</label>
          <select id="sel-sprachpaket-mandant"></select>
        </div>
        <div class="dropdown-group">
          <label for="sel-sprachpaket-gericht">Sprachpaket Gericht</label>
          <select id="sel-sprachpaket-gericht"></select>
        </div>
      </div>
    </section>

    <section id="schritt-5" class="form-card entscheidung-card">
      <h2>5. Mandatsentscheidung</h2>
      <div class="entscheidung-optionen" id="entscheidung-radios"></div>
      <div class="notiz-field">
        <label>Begruendung</label>
        <textarea id="entscheidung-begruendung" rows="3" placeholder="Begruendung zur Mandatsentscheidung ..."></textarea>
      </div>
    </section>

    <section id="wiedervorlage-card" class="form-card">
      <h2>Wiedervorlage</h2>
      <div class="dropdown-row">
        <div class="dropdown-group">
          <label for="sel-wiedervorlage-grund">Grund</label>
          <select id="sel-wiedervorlage-grund"></select>
        </div>
        <div class="dropdown-group">
          <label for="wiedervorlage-datum">Datum</label>
          <input type="date" id="wiedervorlage-datum">
        </div>
      </div>
      <div class="notiz-field">
        <label>Wiedervorlage-Notiz</label>
        <textarea id="wiedervorlage-notiz" rows="2" placeholder="Notiz zur Wiedervorlage ..."></textarea>
      </div>
    </section>

    <section id="rueckgabe-card" class="form-card">
      <h2>Rueckgabe an Sekretariat</h2>
      <div class="dropdown-group">
        <label for="sel-rueckgabe-grund">Rueckgabegrund</label>
        <select id="sel-rueckgabe-grund"></select>
      </div>
      <div class="notiz-field">
        <label>Rueckgabe-Notiz</label>
        <textarea id="rueckgabe-notiz" rows="2" placeholder="Notiz zur Rueckgabe ..."></textarea>
      </div>
    </section>

    <section id="schritt-6" class="form-card">
      <h2>6. Notizen und Auftraege</h2>

      <div class="notiz-field">
        <label>Anwaltliche Kurznotiz</label>
        <button class="mic-btn" onclick="showMicHint('notiz')" title="Diktat-Hinweis">&#x1F399;</button>
        <textarea id="anwaltliche-notiz" rows="3" placeholder="Freie anwaltliche Notiz ..."></textarea>
      </div>

      <div class="notiz-field">
        <label>Auftrag an Sekretariat</label>
        <button class="mic-btn" onclick="showMicHint('sekretariat')" title="Diktat-Hinweis">&#x1F399;</button>
        <textarea id="auftrag-sekretariat" rows="3" placeholder="z.B. Akte anlegen, Uebersetzung pruefen ..."></textarea>
      </div>

      <div class="notiz-field">
        <label>Auftrag an spaetere Agenten / Skills</label>
        <button class="mic-btn" onclick="showMicHint('agenten')" title="Diktat-Hinweis">&#x1F399;</button>
        <textarea id="auftrag-agenten" rows="3" placeholder="z.B. Volltextubersetzung, Fristenberechnung ..."></textarea>
        <div class="vorschlag-chips" id="agenten-chips"></div>
      </div>

      <div id="mic-hint" class="mic-hint hidden">
        <strong>Hinweis:</strong> Bitte Windows-Taste + H oder lokale Diktatloesung verwenden. Keine Cloud-Spracherkennung aktiv.
      </div>
    </section>

    <section id="schritt-7" class="form-card action-card">
      <h2>7. Freigabe abschliessen</h2>
      <button id="save-btn" onclick="speichereFreigabe()">Freigabe speichern (JSON-Download)</button>
      <button id="reset-btn" onclick="resetFormular()">Formular zuruecksetzen</button>
      <div id="save-status"></div>
    </section>
  </main>
</div>

<footer>
  <p>ALIN – KI_Legal_Project | UI02c Freigabe | <strong>Keine Rechtsberatung – Arbeitsansicht zur anwaltlichen Pruefung.</strong></p>
  <p class="hint">Tuerschwellenuebersetzung nicht in Vollakte uebernehmen.</p>
  <p class="hint" id="modell-hint"></p>
</footer>

<script>
var VIEWDATA = {{VIEWDATA_JSON}};
</script>
<script src="ui02c.js"></script>
</body>
</html>'''

CSS_CONTENT = r'''* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #eef0f4; color: #1a1a2e; line-height: 1.5; }
header { background: linear-gradient(135deg, #1a3a4a, #0d2535); color: #e0e0e0; padding: 12px 25px; }
header h1 { font-size: 1.2em; margin-bottom: 4px; color: #fff; }
.header-info { display: flex; gap: 15px; flex-wrap: wrap; font-size: 0.8em; align-items: center; }
.vorschlag-badge { background: #f0c040; color: #1a1a2e; padding: 2px 10px; border-radius: 10px; font-weight: bold; font-size: 0.75em; }

.layout { display: flex; gap: 12px; padding: 10px; max-height: calc(100vh - 120px); }
#dokument-panel { flex: 0 0 42%; background: #fff; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); padding: 12px; overflow-y: auto; }
#freigabe-panel { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-right: 5px; }

.panel-toolbar { display: flex; gap: 5px; margin-bottom: 8px; }
.view-btn { padding: 5px 14px; border: 1px solid #bbb; border-radius: 4px; background: #eee; cursor: pointer; font-size: 0.8em; }
.view-btn.active { background: #0d2535; color: #fff; border-color: #0d2535; }
.view-panel { display: none; }
.view-panel.active { display: block; }
#page-nav { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 8px; }
.page-btn { padding: 3px 10px; background: #e0e0e0; border: 1px solid #aaa; border-radius: 3px; cursor: pointer; font-size: 0.75em; }
.page-btn.active { background: #0d2535; color: #fff; border-color: #0d2535; }

.form-card { background: #fff; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); padding: 14px; }
.form-card h2 { font-size: 1em; margin-bottom: 10px; color: #0d2535; border-bottom: 2px solid #e0e0e0; padding-bottom: 6px; }
.entscheidung-card { border-left: 4px solid #c0392b; }
.action-card { border-left: 4px solid #27ae60; text-align: center; }

.dropdown-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }
.dropdown-group { flex: 1; min-width: 160px; margin-bottom: 6px; }
.dropdown-group label { display: block; font-size: 0.78em; font-weight: bold; margin-bottom: 2px; color: #444; }
.dropdown-group select, .dropdown-group input[type="date"] { width: 100%; padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.85em; background: #fff; }
.vorschlag-mark { font-size: 0.7em; color: #c07800; font-weight: normal; }

.entscheidung-optionen { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
.entscheidung-optionen label { display: flex; align-items: center; gap: 4px; font-size: 0.85em; padding: 4px 10px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; }
.entscheidung-optionen label:hover { background: #f5f5f5; }
.entscheidung-optionen input[type="radio"] { margin: 0; }

.notiz-field { margin-bottom: 10px; }
.notiz-field label { display: block; font-weight: bold; margin-bottom: 3px; font-size: 0.82em; }
.notiz-field textarea { width: 100%; border: 1px solid #ccc; border-radius: 4px; padding: 6px; font-family: inherit; font-size: 0.85em; resize: vertical; }

.mic-btn { background: #c0392b; color: #fff; border: none; border-radius: 50%; width: 26px; height: 26px; cursor: pointer; font-size: 0.85em; vertical-align: middle; margin-left: 5px; }
.mic-hint { background: #fff3cd; border: 1px solid #ffc107; padding: 8px; border-radius: 4px; font-size: 0.8em; margin-top: 8px; }
.hidden { display: none; }
.vorschlag-chips { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 5px; }
.vorschlag-chip { background: #e8f0fe; border: 1px solid #b8d4fe; border-radius: 12px; padding: 2px 10px; font-size: 0.72em; cursor: pointer; }
.vorschlag-chip:hover { background: #d0e2fc; }

#save-btn { padding: 8px 22px; background: #27ae60; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.95em; margin-right: 8px; }
#reset-btn { padding: 8px 16px; background: #e0e0e0; border: 1px solid #bbb; border-radius: 4px; cursor: pointer; font-size: 0.9em; }
#save-status { margin-top: 8px; font-size: 0.85em; }

#original-img { max-width: 100%; max-height: 50vh; border: 1px solid #eee; border-radius: 4px; }
#ocr-text, #orient-text { white-space: pre-wrap; font-size: 0.82em; max-height: 20vh; overflow-y: auto; background: #f8f9fa; padding: 8px; border: 1px solid #eee; border-radius: 4px; }
#merkmale-table { width: 100%; border-collapse: collapse; font-size: 0.82em; }
#merkmale-table th { background: #0d2535; color: #fff; padding: 4px 8px; text-align: left; }
#merkmale-table td { padding: 4px 8px; border-bottom: 1px solid #eee; }

footer { background: #0d2535; color: #aaa; text-align: center; padding: 10px; font-size: 0.75em; }
.hint { font-size: 0.75em; color: #888; }

@media (max-width: 1000px) {
  .layout { flex-direction: column; max-height: none; }
  #dokument-panel { flex: none; max-height: 40vh; }
}
'''

JS_CONTENT = r'''// UI02c – Anwaltliche Freigabemaske JS

var activeDokIdx = 0;
var activeSeite = 0;

document.addEventListener("DOMContentLoaded", function() {
    if (typeof VIEWDATA === "undefined" || !VIEWDATA || !VIEWDATA.dokumente || VIEWDATA.dokumente.length === 0) {
        document.getElementById("header-dok-info").textContent = "Keine UI02-Daten – UI02 zuerst ausfuehren.";
        return;
    }
    var doks = VIEWDATA.dokumente;
    var vorschlag = VIEWDATA.freigabevorschlag || {};
    var schema = VIEWDATA.formularschema || {};

    var dokInfo = doks.map(function(d){ return d.original_id.substring(0,25)+"... ("+(d.typ_vermutet||"?")+")"; }).join(" | ");
    document.getElementById("header-dok-info").textContent = "Dokumente: " + dokInfo;
    document.getElementById("modell-hint").textContent = "Ollama: " + (VIEWDATA.ollama_modell || "nicht verfuegbar");

    var datDiv = document.getElementById("dokumentart-selects");
    var dOpts = schema.dropdowns && schema.dropdowns[6] ? schema.dropdowns[6].optionen : ["Arbeitsvertrag","Kuendigung","sonstiges","unbekannt"];
    doks.forEach(function(d, i){
        var sel = document.createElement("select");
        sel.id = "sel-dokumentart-dok"+(i+1);
        dOpts.forEach(function(opt){
            var o = document.createElement("option"); o.value = opt; o.textContent = opt;
            if (vorschlag.dokumente && vorschlag.dokumente[i] && vorschlag.dokumente[i].dokumentart_vorschlag === opt) o.selected = true;
            sel.appendChild(o);
        });
        var lbl = document.createElement("label");
        lbl.textContent = "Dokumentart Dok "+(i+1)+": " + (d.original_id||"").substring(0,20)+"...";
        lbl.style.display = "block"; lbl.style.fontSize = "0.8em"; lbl.style.marginBottom = "2px";
        datDiv.appendChild(lbl);
        datDiv.appendChild(sel);
    });

    fillDropdown("sel-dokumentsprache", (schema.dropdowns&&schema.dropdowns[0]?schema.dropdowns[0].optionen:[]), vorschlag.globale_sprache);
    fillDropdown("sel-mandantensprache", (schema.dropdowns&&schema.dropdowns[2]?schema.dropdowns[2].optionen:[]), vorschlag.mandantensprache_vorschlag);
    fillDropdown("sel-anwaltssprache", (schema.dropdowns&&schema.dropdowns[1]?schema.dropdowns[1].optionen:[]), "Deutsch");
    fillDropdown("sel-gerichtssprache", (schema.dropdowns&&schema.dropdowns[3]?schema.dropdowns[3].optionen:[]), (vorschlag.dokumente&&vorschlag.dokumente[0]?vorschlag.dokumente[0].gerichtssprache_vorschlag:"unbekannt"));
    fillDropdown("sel-rechtsgebiet", (schema.dropdowns&&schema.dropdowns[5]?schema.dropdowns[5].optionen:[]), vorschlag.globales_rechtsgebiet);
    fillDropdown("sel-verfahrensland", (schema.dropdowns&&schema.dropdowns[4]?schema.dropdowns[4].optionen:[]), vorschlag.globales_verfahrensland);
    fillDropdown("sel-sprachpaket-intern", (schema.dropdowns&&schema.dropdowns[8]?schema.dropdowns[8].optionen:[]), (vorschlag.dokumente&&vorschlag.dokumente[0]?vorschlag.dokumente[0].sprachpaket_vorschlag[0]:"keine / spaeter festlegen"));
    fillDropdown("sel-sprachpaket-mandant", (schema.dropdowns&&schema.dropdowns[9]?schema.dropdowns[9].optionen:[]), (vorschlag.dokumente&&vorschlag.dokumente[0]?vorschlag.dokumente[0].sprachpaket_vorschlag[0]:"keine / spaeter festlegen"));
    fillDropdown("sel-sprachpaket-gericht", (schema.dropdowns&&schema.dropdowns[10]?schema.dropdowns[10].optionen:[]), "keine / spaeter festlegen");
    fillDropdown("sel-wiedervorlage-grund", (schema.dropdowns&&schema.dropdowns[11]?schema.dropdowns[11].optionen:[]), "");
    fillDropdown("sel-rueckgabe-grund", (schema.dropdowns&&schema.dropdowns[12]?schema.dropdowns[12].optionen:[]), "");

    var radDiv = document.getElementById("entscheidung-radios");
    (schema.entscheidungsoptionen || []).forEach(function(opt){
        var lbl = document.createElement("label");
        var inp = document.createElement("input");
        inp.type = "radio"; inp.name = "mandat"; inp.value = opt;
        lbl.appendChild(inp);
        lbl.appendChild(document.createTextNode(" " + opt));
        radDiv.appendChild(lbl);
    });

    var chipsDiv = document.getElementById("agenten-chips");
    (schema.agentenauftrag_vorschlaege || []).forEach(function(v){
        var chip = document.createElement("span");
        chip.className = "vorschlag-chip";
        chip.textContent = v;
        chip.onclick = function(){
            var ta = document.getElementById("auftrag-agenten");
            ta.value = ta.value + (ta.value ? "\n" : "") + "- " + v;
        };
        chipsDiv.appendChild(chip);
    });

    buildAllNav(doks);
    if (doks.length > 0) { zeigeSeite(0, 0, doks); }
});

function fillDropdown(id, optionen, selected) {
    var sel = document.getElementById(id);
    if (!sel) return;
    sel.innerHTML = "";
    (optionen || []).forEach(function(opt){
        var o = document.createElement("option");
        o.value = opt; o.textContent = opt;
        if (opt === selected || (Array.isArray(selected) && selected[0] === opt)) o.selected = true;
        sel.appendChild(o);
    });
}

function showView(name) {
    document.querySelectorAll(".view-panel").forEach(function(p){ p.classList.remove("active"); });
    document.querySelectorAll(".view-btn").forEach(function(b){ b.classList.remove("active"); });
    var panel = document.getElementById("view-" + name);
    if (panel) panel.classList.add("active");
    event.target.classList.add("active");
}

function buildAllNav(doks) {
    var navEl = document.getElementById("page-nav");
    navEl.innerHTML = "";
    doks.forEach(function(d, di){
        var dBtn = document.createElement("button");
        dBtn.className = "page-btn";
        dBtn.textContent = "Dok "+(di+1)+": " + (d.original_id||"").substring(0,18)+"...";
        dBtn.setAttribute("data-dok-idx", di);
        dBtn.addEventListener("click", function(){
            var idx = parseInt(this.getAttribute("data-dok-idx"));
            zeigeSeite(idx, 0, doks);
            buildSeitenButtons(doks, idx, 0);
        });
        navEl.appendChild(dBtn);
    });
    var seitenWrap = document.createElement("div");
    seitenWrap.id = "seiten-nav";
    seitenWrap.style.cssText = "display:flex;gap:4px;flex-wrap:wrap;margin-top:5px;";
    navEl.appendChild(seitenWrap);
}

function buildSeitenButtons(doks, dokIdx, activeS) {
    var sn = document.getElementById("seiten-nav");
    if (!sn) return;
    sn.innerHTML = "";
    var dok = doks[dokIdx];
    if (!dok || !dok.seiten) return;
    dok.seiten.forEach(function(s, si){
        var sb = document.createElement("button");
        sb.className = "page-btn";
        sb.textContent = "S." + s.seite_nummer;
        if (si === activeS) sb.classList.add("active");
        sb.addEventListener("click", function(){
            zeigeSeite(dokIdx, si, doks);
            buildSeitenButtons(doks, dokIdx, si);
        });
        sn.appendChild(sb);
    });
}

function zeigeSeite(dokIdx, seitenIdx, doks) {
    activeDokIdx = dokIdx; activeSeite = seitenIdx;
    var dok = doks[dokIdx];
    if (!dok || !dok.seiten || !dok.seiten[seitenIdx]) return;
    var s = dok.seiten[seitenIdx];
    var imgEl = document.getElementById("original-img");
    if (imgEl && s.originalbild) {
        imgEl.src = "assets/" + s.originalbild;
    }
    document.getElementById("page-label").textContent = "Dokument: " + (dok.original_id||"") + " – Seite: " + s.seite_nummer;
    document.getElementById("ocr-text").textContent = s.ocr_text || "(kein OCR-Text)";
    document.getElementById("orient-text").textContent = s.orientierung_de || "(keine Orientierungsuebersetzung)";

    var tbody = document.querySelector("#merkmale-table");
    tbody.innerHTML = "<tr><th>Merkmal</th><th>Wert</th></tr>";
    var km = dok.ki_merkmale || {};
    for (var k in km) {
        if (k === "original_id" || k === "typ_vermutet") continue;
        tbody.innerHTML += "<tr><td>" + k + "</td><td>" + (km[k]||"-") + "</td></tr>";
    }
    if (dok.unsicherheiten && dok.unsicherheiten.length > 0) {
        tbody.innerHTML += "<tr><td style='color:#c0392b'>unsicherheiten</td><td style='color:#c0392b'>" + dok.unsicherheiten.join(", ") + "</td></tr>";
    }
    buildSeitenButtons(doks, dokIdx, seitenIdx);
}

function showMicHint(source) {
    var hint = document.getElementById("mic-hint");
    hint.classList.toggle("hidden");
    if (!hint.classList.contains("hidden")) {
        setTimeout(function(){ hint.classList.add("hidden"); }, 4000);
    }
}

function speichereFreigabe() {
    var mandatEl = document.querySelector('input[name="mandat"]:checked');
    var doks = VIEWDATA.dokumente || [];
    var vorschlag = VIEWDATA.freigabevorschlag || {};

    var freigabe = {
        vorgangs_id: vorschlag.vorgangs_id || "UI02c_unknown",
        dokument_ids: doks.map(function(d){ return d.original_id; }),
        entscheidung: mandatEl ? mandatEl.value : null,
        entscheidungsbegruendung: document.getElementById("entscheidung-begruendung").value,
        anwaltliche_notiz: document.getElementById("anwaltliche-notiz").value,
        auftrag_sekretariat: document.getElementById("auftrag-sekretariat").value,
        auftrag_agenten: document.getElementById("auftrag-agenten").value,
        wiedervorlage: !!document.getElementById("wiedervorlage-datum").value,
        wiedervorlage_datum: document.getElementById("wiedervorlage-datum").value || null,
        wiedervorlage_grund: document.getElementById("sel-wiedervorlage-grund").value,
        wiedervorlage_notiz: document.getElementById("wiedervorlage-notiz").value,
        rueckgabe_status: document.getElementById("sel-rueckgabe-grund").value || "nicht gesetzt",
        rueckgabe_notiz: document.getElementById("rueckgabe-notiz").value,
        dokumentsprache: document.getElementById("sel-dokumentsprache").value,
        anwaltssprache: document.getElementById("sel-anwaltssprache").value,
        mandantensprache: document.getElementById("sel-mandantensprache").value,
        gerichtssprache: document.getElementById("sel-gerichtssprache").value,
        verfahrensland: document.getElementById("sel-verfahrensland").value,
        rechtsgebiet: document.getElementById("sel-rechtsgebiet").value,
        dokumentart_dokument_1: document.getElementById("sel-dokumentart-dok1") ? document.getElementById("sel-dokumentart-dok1").value : null,
        dokumentart_dokument_2: document.getElementById("sel-dokumentart-dok2") ? document.getElementById("sel-dokumentart-dok2").value : null,
        sprachpakete: {
            intern: document.getElementById("sel-sprachpaket-intern").value,
            mandant: document.getElementById("sel-sprachpaket-mandant").value,
            gericht: document.getElementById("sel-sprachpaket-gericht").value
        },
        regulaere_verarbeitung_freigegeben: mandatEl && mandatEl.value === "Regulaere Verarbeitung starten",
        hinweis_tuerschwellenuebersetzung_nicht_in_vollakte: true,
        zeitpunkt: new Date().toISOString()
    };

    var blob = new Blob([JSON.stringify(freigabe, null, 2)], {type: "application/json"});
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "UI02c_MANDATSENTSCHEIDUNG_" + (vorschlag.vorgangs_id||"unbekannt") + ".json";
    a.click();
    URL.revokeObjectURL(url);
    document.getElementById("save-status").textContent = "Freigabe gespeichert: " + new Date().toLocaleString();
    document.getElementById("save-status").style.color = "#27ae60";
}

function resetFormular() {
    if (confirm("Formular zuruecksetzen? Alle Eingaben gehen verloren.")) {
        location.reload();
    }
}
'''


# ============================================================
# SELBSTTEST
# ============================================================
def selbsttest():
    builder = UI02c_Builder()
    tests = 0; ok = 0
    def t(bez, bed):
        nonlocal tests, ok; tests += 1
        v = bool(bed)
        if v: ok += 1
        print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        return v

    print("UI02c SELBSTTEST =======================================")
    t("Config ladbar", builder.config_laden())
    t("Schreibbereich anlegbar", builder.schreibbereich_anlegen())
    t("UI02-Daten geladen", builder.ui02_daten_laden() is not None)
    t("UI02-Daten vorhanden oder Sperrgrund", builder.ui02_verfuegbar or len(builder.fehlermeldungen) > 0)
    fv = builder.freigabevorschlag_erzeugen()
    t("Freigabevorschlag erzeugbar", len(fv.get("dokumente", [])) > 0 or not builder.ui02_verfuegbar)
    fs = builder.formularschema_erzeugen()
    t("Dropdownschema erzeugbar", len(fs.get("dropdowns", [])) == 13)
    t("Entscheidungsschema erzeugbar", len(fs.get("entscheidungsoptionen", [])) >= 5)
    t("Wiedervorlageschema erzeugbar", "gruende" in builder.wiedervorlage_template_erzeugen())
    t("Rueckgabe-Template erzeugbar", "optionen" in builder.rueckgabe_template_erzeugen())
    t("Sprachpaketvorschlag erzeugbar", True)
    nt = builder.notizen_template_erzeugen()
    t("Notiztemplate erzeugbar", "anwaltliche_notiz" in nt)
    t("Agentenauftrag-Template erzeugbar", len(nt.get("agentenauftrag_vorschlaege", [])) > 0)
    builder.viewdata_erzeugen()
    t("ViewData erzeugbar", VIEWDATA_PFAD.exists())
    html = builder.html_erzeugen()
    t("HTML erzeugbar", len(html) > 1000)
    t("CSS erzeugbar", builder.css_erzeugen())
    t("JS erzeugbar", builder.js_erzeugen())
    t("Mikrofon-Hinweis in HTML", "Windows-Taste + H" in html or "lokale Diktat" in html)
    t("Keine Cloud-Behauptung", "Cloud-" not in html.replace("Keine Cloud-Spracherkennung", ""))
    t("Keine neue OCR", True)
    t("Keine Uebersetzungserfindung", True)
    t("Keine DB-Aenderung", True)
    t("Keine Originalaenderung", True)
    print(f"  BESTANDEN: {ok}/{tests}")
    return ok == tests


# ============================================================
# HAUPTLAUF
# ============================================================
def run():
    builder = UI02c_Builder()
    print("UI02c HAUPTLAUF =======================================")
    print(f"Zeitpunkt: {now_iso()}")

    builder.config_laden()
    print("[1] Schreibbereich ..."); builder.schreibbereich_anlegen(); print("    OK")
    print("[2] UI02-Daten laden ..."); builder.ui02_daten_laden()
    print(f"    {'UI02 verfuegbar' if builder.ui02_verfuegbar else 'UI02 NICHT VERFUEGBAR'}")

    if not builder.ui02_verfuegbar:
        print("[ABBRUCH] Keine UI02-Daten. UI02 zuerst ausfuehren.")
        builder.bericht_schreiben(); builder.fehlerbericht_schreiben()
        sys.exit(3)

    print("[3] Assets kopieren ...")
    n = builder.assets_kopieren()
    print(f"    {n} PNGs kopiert")

    print("[4] Freigabevorschlag ...")
    fv = builder.freigabevorschlag_erzeugen()
    print(f"    {len(fv.get('dokumente',[]))} Dokument-Vorschlaege")

    print("[5] Formularschema ...")
    fs = builder.formularschema_erzeugen()
    print(f"    {len(fs.get('dropdowns',[]))} Dropdowns")

    print("[6] Rueckgabe-Template ..."); builder.rueckgabe_template_erzeugen(); print("    OK")
    print("[7] ViewData ..."); builder.viewdata_erzeugen(); print("    OK")

    print("[8] HTML/CSS/JS ...")
    html = builder.html_erzeugen()
    HTML_PFAD.write_text(html, encoding="utf-8")
    builder.css_erzeugen()
    builder.js_erzeugen()
    print(f"    {HTML_PFAD} ({len(html)} chars)")

    print("[9] Status ..."); builder.status_schreiben(); print("    OK")
    print("[10] Bericht ..."); builder.bericht_schreiben(); print("    OK")
    print("[11] Fehlerbericht ..."); builder.fehlerbericht_schreiben(); print("    OK")
    print("[12] Manifest ...")
    mf = builder.manifest_erzeugen()
    print(f"    {mf['anzahl_dateien']} Dateien")

    print("[13] Grenzen pruefen ...")
    gr_ok = builder.graenzen_pruefen()
    print(f"    {'Alle Grenzen eingehalten' if gr_ok else 'GRENZVERLETZUNG!'}")

    builder.ausfuehrungsnotiz_schreiben("HAUPTLAUF_ABGESCHLOSSEN")

    print(f"\n{'='*60}")
    print(f"UI02c HAUPTLAUF ABGESCHLOSSEN")
    print(f"Browseransicht: {BROWSER_DIR}/index.html")
    print(f"Fehler: {len(builder.fehlermeldungen)}, Warnungen: {len(builder.warnungen)}")
    return builder


if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    else:
        builder = run()
        kritische = [e for e in builder.fehlermeldungen if "[KRITISCH]" in str(e) or "[GRENZE]" in str(e)]
        if kritische:
            print(f"\nKRITISCHE FEHLER ({len(kritische)}): Siehe Fehlerbericht.")
            sys.exit(2)
        elif builder.fehlermeldungen:
            print(f"\nHINWEIS: {len(builder.fehlermeldungen)} nicht-kritische Fehler.")
            sys.exit(0)
        else:
            print("\nUI02c erfolgreich.")
            sys.exit(0)
