-- Rollback for 002_v452_traceability.sql. Refuses to run if any traceability row exists.
-- Records are append-only; this script never deletes data. Apply only to a dedicated test/empty DB.
BEGIN;
DO $$
BEGIN
  IF (SELECT count(*) FROM rnd_v452_candidates) > 0 OR (SELECT count(*) FROM rnd_v452_batch_provenance) > 0 THEN
    RAISE EXCEPTION 'Refusing rollback 002: traceability tables contain data';
  END IF;
END $$;
DROP TRIGGER IF EXISTS rnd_v452_provenance_immutable ON rnd_v452_batch_provenance;
DROP TRIGGER IF EXISTS rnd_v452_candidates_immutable ON rnd_v452_candidates;
DROP TABLE IF EXISTS rnd_v452_batch_provenance;
DROP TABLE IF EXISTS rnd_v452_candidates;
DROP FUNCTION IF EXISTS rnd_v452_deny_mutation();
COMMIT;
