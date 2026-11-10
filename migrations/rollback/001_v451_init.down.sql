-- Rollback for 001_v451_init.sql. Refuses to run if any study, batch or measurement exists.
-- Apply 002 rollback first. Records are append-only; this script never deletes data.
BEGIN;
DO $$
BEGIN
  IF (SELECT count(*) FROM rnd_v451_studies) > 0 OR (SELECT count(*) FROM rnd_v451_batches) > 0
     OR (SELECT count(*) FROM rnd_v451_measurements) > 0 THEN
    RAISE EXCEPTION 'Refusing rollback 001: V4.5 tables contain data';
  END IF;
END $$;
DROP TRIGGER IF EXISTS rnd_v451_measurements_immutable ON rnd_v451_measurements;
DROP TABLE IF EXISTS rnd_v451_measurements;
DROP TABLE IF EXISTS rnd_v451_batches;
DROP TABLE IF EXISTS rnd_v451_studies;
DROP FUNCTION IF EXISTS rnd_v451_deny_measurement_mutation();
COMMIT;
