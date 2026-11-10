-- Formula Intelligence V4.5.2 stabilization R1: immutable candidate + batch audit.
-- Apply AFTER 001_v451_init.sql on a dedicated backup/test database.
BEGIN;
CREATE TABLE IF NOT EXISTS rnd_v452_candidates (
  study_id TEXT NOT NULL REFERENCES rnd_v451_studies(id),
  candidate_id TEXT NOT NULL,
  candidate_sha256 CHAR(64) NOT NULL,
  composition JSONB NOT NULL,design JSONB NOT NULL,
  PRIMARY KEY(study_id,candidate_id)
);
CREATE TABLE IF NOT EXISTS rnd_v452_batch_provenance (
  batch_id TEXT PRIMARY KEY,
  study_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  candidate_sha256 CHAR(64) NOT NULL,
  actual_weights JSONB NOT NULL,
  raw_material_lots JSONB NOT NULL,
  process JSONB NOT NULL,
  weighed_by TEXT NOT NULL,
  deviation_max_pp DOUBLE PRECISION NOT NULL CHECK(deviation_max_pp>=0),
  traceability_status TEXT NOT NULL CHECK(traceability_status IN ('LINKED_MATCHED','LINKED_DEVIATED')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  FOREIGN KEY(batch_id,study_id) REFERENCES rnd_v451_batches(id,study_id),
  FOREIGN KEY(study_id,candidate_id) REFERENCES rnd_v452_candidates(study_id,candidate_id)
);
CREATE OR REPLACE FUNCTION rnd_v452_deny_mutation() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'R&D candidate and provenance records are append-only'; END $$;
CREATE TRIGGER rnd_v452_candidates_immutable BEFORE UPDATE OR DELETE ON rnd_v452_candidates
 FOR EACH ROW EXECUTE FUNCTION rnd_v452_deny_mutation();
CREATE TRIGGER rnd_v452_provenance_immutable BEFORE UPDATE OR DELETE ON rnd_v452_batch_provenance
 FOR EACH ROW EXECUTE FUNCTION rnd_v452_deny_mutation();
COMMIT;
