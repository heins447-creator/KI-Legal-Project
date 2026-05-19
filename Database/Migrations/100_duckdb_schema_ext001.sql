-- EXT-001: DuckDB-Schema für lokale Datenhaltung
-- Ziel: Lokale, dateibasierte analytische Datenbank für ALIN
-- Sicherheit: Keine Cloud, keine echten Mandantendaten, nur lokale .duckdb-Dateien
-- Idempotent: Ja, verwendet CREATE TABLE IF NOT EXISTS und CREATE INDEX IF NOT EXISTS

-- Schema: alin_ext001
CREATE SCHEMA IF NOT EXISTS alin_ext001;

-- Tabelle: dokumente
-- Speichert Metadaten zu importierten Dokumenten
CREATE TABLE IF NOT EXISTS alin_ext001.dokumente (
    dokument_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dateiname VARCHAR NOT NULL,
    dateipfad VARCHAR NOT NULL,
    dateigroesse_bytes BIGINT,
    mime_typ VARCHAR,
    sprache_erkannt VARCHAR(10),
    md5_hash VARCHAR(32),
    import_zeit TIMESTAMP DEFAULT current_timestamp,
    status VARCHAR(20) DEFAULT 'importiert', -- importiert, ocr_gelaufen, uebersetzt, freigegeben
    datenschutz_klasse VARCHAR(20) DEFAULT 'intern', -- oeffentlich, intern, vertraulich, geheim
    mandanten_id VARCHAR(50), -- nur als Platzhalter, keine echten Daten
    UNIQUE(dateipfad)
);

-- Tabelle: ocr_ergebnisse
-- Speichert OCR-Ergebnisse pro Dokument und Seite
CREATE TABLE IF NOT EXISTS alin_ext001.ocr_ergebnisse (
    ocr_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dokument_id UUID NOT NULL REFERENCES alin_ext001.dokumente(dokument_id),
    seite_nr INTEGER NOT NULL,
    ocr_engine VARCHAR(30) NOT NULL, -- tesseract, paddleocr, etc.
    roh_text TEXT,
    strukturiertes_text JSON,
    konfidenz_score DECIMAL(5,4), -- 0.0000 bis 1.0000
    verarbeitungs_zeit_ms INTEGER,
    sprache VARCHAR(10),
    erstellt_am TIMESTAMP DEFAULT current_timestamp,
    UNIQUE(dokument_id, seite_nr, ocr_engine)
);

-- Tabelle: uebersetzungen
-- Speichert Übersetzungen von Textsegmenten
CREATE TABLE IF NOT EXISTS alin_ext001.uebersetzungen (
    uebersetzung_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dokument_id UUID NOT NULL REFERENCES alin_ext001.dokumente(dokument_id),
    quell_sprache VARCHAR(10) NOT NULL,
    ziel_sprache VARCHAR(10) NOT NULL,
    quell_text TEXT NOT NULL,
    uebersetzter_text TEXT,
    uebersetzungs_engine VARCHAR(30), -- argos, offline_model, etc.
    konfidenz_score DECIMAL(5,4),
    menschliche_freigabe BOOLEAN DEFAULT FALSE,
    freigegeben_von VARCHAR(100),
    freigegeben_am TIMESTAMP,
    erstellt_am TIMESTAMP DEFAULT current_timestamp
);

-- Tabelle: terminologie
-- Speichert EU-Terminologie und validierte Übersetzungsäquivalente
CREATE TABLE IF NOT EXISTS alin_ext001.terminologie (
    begriff_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    begriff VARCHAR(500) NOT NULL,
    sprache VARCHAR(10) NOT NULL,
    kategorie VARCHAR(50), -- eurovoc, verordnung, richtlinie, etc.
    quelle VARCHAR(100), -- EU-Verordnung, EuroVoc-Konzept, etc.
    definition TEXT,
    kontext TEXT,
    aequivalente JSON, -- {"de": "...", "en": "...", "fr": "..."}
    validiert BOOLEAN DEFAULT FALSE,
    validiert_von VARCHAR(100),
    validiert_am TIMESTAMP,
    erstellt_am TIMESTAMP DEFAULT current_timestamp,
    UNIQUE(begriff, sprache, kategorie)
);

-- Tabelle: vektor_embeddings
-- Speichert Vektorembeddings für semantische Suche
CREATE TABLE IF NOT EXISTS alin_ext001.vektor_embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dokument_id UUID NOT NULL REFERENCES alin_ext001.dokumente(dokument_id),
    segment_typ VARCHAR(20) NOT NULL, -- dokument, absatz, satz, seite
    segment_id VARCHAR(100) NOT NULL,
    embedding_model VARCHAR(50) NOT NULL,
    dimension INTEGER NOT NULL DEFAULT 384,
    embedding FLOAT[], -- DuckDB Array-Typ
    erstellt_am TIMESTAMP DEFAULT current_timestamp,
    UNIQUE(dokument_id, segment_typ, segment_id, embedding_model)
);

-- Indizes für häufige Abfragen
CREATE INDEX IF NOT EXISTS idx_dokumente_status ON alin_ext001.dokumente(status);
CREATE INDEX IF NOT EXISTS idx_dokumente_sprache ON alin_ext001.dokumente(sprache_erkannt);
CREATE INDEX IF NOT EXISTS idx_ocr_dokument ON alin_ext001.ocr_ergebnisse(dokument_id);
CREATE INDEX IF NOT EXISTS idx_uebersetzung_dokument ON alin_ext001.uebersetzungen(dokument_id);
CREATE INDEX IF NOT EXISTS idx_terminologie_sprache ON alin_ext001.terminologie(sprache);
CREATE INDEX IF NOT EXISTS idx_terminologie_kategorie ON alin_ext001.terminologie(kategorie);
CREATE INDEX IF NOT EXISTS idx_embedding_dokument ON alin_ext001.vektor_embeddings(dokument_id);

-- View: v_dokumente_vollstaendigkeit
-- Zeigt den Verarbeitungsstatus aller Dokumente
CREATE OR REPLACE VIEW alin_ext001.v_dokumente_vollstaendigkeit AS
SELECT
    d.dokument_id,
    d.dateiname,
    d.status,
    COUNT(DISTINCT o.seite_nr) AS ocr_seiten,
    COUNT(DISTINCT u.uebersetzung_id) AS uebersetzungen_anzahl,
    COUNT(DISTINCT e.embedding_id) AS embeddings_anzahl,
    d.import_zeit
FROM alin_ext001.dokumente d
LEFT JOIN alin_ext001.ocr_ergebnisse o ON d.dokument_id = o.dokument_id
LEFT JOIN alin_ext001.uebersetzungen u ON d.dokument_id = u.dokument_id
LEFT JOIN alin_ext001.vektor_embeddings e ON d.dokument_id = e.dokument_id
GROUP BY d.dokument_id, d.dateiname, d.status, d.import_zeit;

-- Sicherheit: Keine sensiblen Daten in Test-Daten
-- Test-Eintrag (nur synthetisch)
INSERT OR IGNORE INTO alin_ext001.dokumente (dokument_id, dateiname, dateipfad, mime_typ, sprache_erkannt, status)
VALUES ('00000000-0000-0000-0000-000000000001', 'test_dokument.pdf', '/test/test_dokument.pdf', 'application/pdf', 'de', 'importiert');
