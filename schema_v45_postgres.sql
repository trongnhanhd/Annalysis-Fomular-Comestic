-- V4.5 design for a real PostgreSQL deployment. Do not run against production without migration review.
-- Access controls, backup, object storage and role approvals must be integrated by the host app.
CREATE TABLE IF NOT EXISTS rnd_v45_studies (
  study_id UUID PRIMARY KEY, title TEXT NOT NULL, created_by TEXT NOT NULL,
  product_type TEXT NOT NULL, formula_sha256 CHAR(64) NOT NULL,
  scenario JSONB NOT NULL, protocol JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS rnd_v45_batches (
  batch_id UUID PRIMARY KEY, study_id UUID NOT NULL REFERENCES rnd_v45_studies(study_id),
  lot_code TEXT NOT NULL, operator_id TEXT NOT NULL,
  prepared_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(study_id,lot_code)
);
CREATE TABLE IF NOT EXISTS rnd_v45_measurements (
  measurement_id UUID PRIMARY KEY, study_id UUID NOT NULL REFERENCES rnd_v45_studies(study_id),
  batch_id UUID NOT NULL REFERENCES rnd_v45_batches(batch_id),
  metric_code VARCHAR(48) NOT NULL, day INTEGER NOT NULL CHECK(day BETWEEN 0 AND 3650),
  value_numeric DOUBLE PRECISION, value_text TEXT, unit TEXT NOT NULL,
  method TEXT NOT NULL, instrument_id TEXT NOT NULL, operator_id TEXT NOT NULL,
  evidence_uri TEXT NOT NULL, data_kind TEXT NOT NULL CHECK(data_kind IN ('MEASURED','DEMO_SYNTHETIC')),
  supersedes_measurement_id UUID REFERENCES rnd_v45_measurements(measurement_id),
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT v45_one_value CHECK ((value_numeric IS NULL) <> (value_text IS NULL))
);
CREATE INDEX IF NOT EXISTS idx_v45_measurements_study_batch
 ON rnd_v45_measurements(study_id,batch_id,metric_code,day);
-- Stronger DB-level audit triggers, append-only security policies, RLS, and attachments
-- integrity checks are mandatory before production adoption.
