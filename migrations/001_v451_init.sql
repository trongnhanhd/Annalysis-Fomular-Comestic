-- Formula Intelligence V4.5.1; apply to a dedicated PostgreSQL database.
-- This migration deliberately preserves TEXT IDs used by the existing V4.5 API.
BEGIN;
CREATE TABLE IF NOT EXISTS rnd_v451_studies (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, created_by TEXT NOT NULL,
  product_type TEXT NOT NULL, formula_sha256 CHAR(64) NOT NULL,
  scenario JSONB NOT NULL, protocol JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS rnd_v451_batches (
  id TEXT PRIMARY KEY,
  study_id TEXT NOT NULL REFERENCES rnd_v451_studies(id),
  lot_code TEXT NOT NULL, operator TEXT NOT NULL,
  prepared_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT rnd_v451_batch_unique UNIQUE (study_id, lot_code),
  CONSTRAINT rnd_v451_batch_study_id_unique UNIQUE (id, study_id)
);
CREATE TABLE IF NOT EXISTS rnd_v451_measurements (
  id TEXT PRIMARY KEY, study_id TEXT NOT NULL REFERENCES rnd_v451_studies(id),
  batch_id TEXT NOT NULL,
  metric_code VARCHAR(48) NOT NULL, day INTEGER NOT NULL CHECK (day BETWEEN 0 AND 3650),
  value_numeric DOUBLE PRECISION, value_text TEXT, unit TEXT NOT NULL,
  method TEXT NOT NULL, instrument_id TEXT NOT NULL, operator TEXT NOT NULL,
  evidence_uri TEXT NOT NULL,
  data_kind TEXT NOT NULL CHECK (data_kind IN ('MEASURED','DEMO_SYNTHETIC')),
  supersedes_measurement_id TEXT UNIQUE REFERENCES rnd_v451_measurements(id),
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT rnd_v451_one_value CHECK ((value_numeric IS NULL) <> (value_text IS NULL)),
  CONSTRAINT rnd_v451_batch_same_study FOREIGN KEY (batch_id, study_id)
    REFERENCES rnd_v451_batches(id, study_id)
);
CREATE INDEX IF NOT EXISTS rnd_v451_measurements_study
 ON rnd_v451_measurements(study_id, batch_id, metric_code, day);
CREATE INDEX IF NOT EXISTS rnd_v451_studies_created_at
 ON rnd_v451_studies(created_at DESC);
-- Measurements are append-only even if someone bypasses the API.
CREATE OR REPLACE FUNCTION rnd_v451_deny_measurement_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'R&D measurement records are append-only';
END $$;
DROP TRIGGER IF EXISTS rnd_v451_measurements_immutable ON rnd_v451_measurements;
CREATE TRIGGER rnd_v451_measurements_immutable
 BEFORE UPDATE OR DELETE ON rnd_v451_measurements
 FOR EACH ROW EXECUTE FUNCTION rnd_v451_deny_measurement_mutation();
COMMIT;
