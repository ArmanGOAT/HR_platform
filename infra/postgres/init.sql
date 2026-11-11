-- Minimal MVP schema. Runs once, when the Postgres volume is created.
-- Full list of planned tables: docs/ARCHITECTURE.md, section 7.2.

CREATE TABLE IF NOT EXISTS resumes (
    id               CHAR(64) PRIMARY KEY,                -- sha256 of the original file
    source           TEXT NOT NULL CHECK (source IN ('upload', 'telegram')),
    status           TEXT NOT NULL DEFAULT 'queued'
                     CHECK (status IN ('queued', 'processing', 'ready', 'failed')),
    error            TEXT,
    language         TEXT,                                -- en / ru / uz / unknown
    supported        BOOLEAN NOT NULL DEFAULT FALSE,      -- MVP: only English is searchable
    ocr_used         BOOLEAN,
    pages            INTEGER,
    title            TEXT,
    skills           TEXT[] NOT NULL DEFAULT '{}',
    experience_years REAL,
    consent          BOOLEAN NOT NULL DEFAULT FALSE,
    person_key       TEXT,                                -- keyed hash of e-mail/phone, never the raw value
    uploaded_at      TIMESTAMPTZ NOT NULL DEFAULT now(),  -- for Telegram: the post date
    processed_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS chunks (
    id        TEXT PRIMARY KEY,                           -- "<resume_id>:<n>"
    resume_id CHAR(64) NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    position  INTEGER NOT NULL,
    section   TEXT NOT NULL,                              -- summary / experience / project / education / skills / other
    text      TEXT NOT NULL                               -- anonymized
);

CREATE INDEX IF NOT EXISTS resumes_status_idx ON resumes (status);
CREATE INDEX IF NOT EXISTS chunks_resume_idx ON chunks (resume_id);
