-- Formula Intelligence V4.4 additive schema only (does not overwrite V4.1/V4.2/V4.3).
-- Requires pgcrypto UUID support; review against production schema before migration.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS formula_optimization_runs (
  run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_type_id INTEGER NULL,
  engine_version TEXT NOT NULL DEFAULT '4.4.0',
  input_payload JSONB NOT NULL,
  output_payload JSONB NULL,
  dataset_snapshot_id TEXT NULL,
  status TEXT NOT NULL CHECK (status IN ('PENDING','FEASIBLE','INFEASIBLE','INSUFFICIENT_DATA_OR_SELECTION','FAILED')),
  evidence_status TEXT NOT NULL DEFAULT 'SIMULATION_NOT_VALIDATED',
  regulatory_status TEXT NOT NULL DEFAULT 'NOT_ASSESSED',
  approved_for_manufacturing BOOLEAN NOT NULL DEFAULT FALSE CHECK (approved_for_manufacturing = FALSE),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  computed_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS ix_formula_optimization_runs_created_at ON formula_optimization_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_formula_optimization_runs_status ON formula_optimization_runs(status);

CREATE TABLE IF NOT EXISTS formula_optimization_raw_materials (
  run_id UUID NOT NULL REFERENCES formula_optimization_runs(run_id) ON DELETE CASCADE,
  material_key TEXT NOT NULL,
  grade_id TEXT NULL,
  primary_group_code TEXT NOT NULL,
  min_percent NUMERIC(12,6) NOT NULL CHECK (min_percent>=0 AND min_percent<=100),
  max_percent NUMERIC(12,6) NOT NULL CHECK (max_percent>=0 AND max_percent<=100),
  prior_percent NUMERIC(12,6) NULL CHECK (prior_percent>=0 AND prior_percent<=100),
  composition_status TEXT NOT NULL CHECK (composition_status IN ('verified','supplier_range','user_assumption','unknown')),
  composition_complete BOOLEAN NOT NULL DEFAULT FALSE,
  supplier_evidence_url TEXT NULL,
  PRIMARY KEY (run_id,material_key),
  CHECK (min_percent<=max_percent)
);

CREATE TABLE IF NOT EXISTS formula_optimization_component_ranges (
  run_id UUID NOT NULL,
  material_key TEXT NOT NULL,
  inci TEXT NOT NULL,
  fraction_min NUMERIC(12,9) NOT NULL CHECK (fraction_min>=0 AND fraction_min<=1),
  fraction_max NUMERIC(12,9) NOT NULL CHECK (fraction_max>=0 AND fraction_max<=1),
  evidence_status TEXT NOT NULL DEFAULT 'NOT_VERIFIED',
  PRIMARY KEY (run_id,material_key,inci),
  FOREIGN KEY (run_id,material_key) REFERENCES formula_optimization_raw_materials(run_id,material_key) ON DELETE CASCADE,
  CHECK (fraction_min<=fraction_max)
);

CREATE TABLE IF NOT EXISTS formula_optimization_claims (
  run_id UUID NOT NULL REFERENCES formula_optimization_runs(run_id) ON DELETE CASCADE,
  claim_key TEXT NOT NULL,
  basis TEXT NOT NULL CHECK (basis IN ('raw_material','finished_inci','ambiguous')),
  target_key TEXT NOT NULL,
  claim_percent NUMERIC(12,6) NOT NULL CHECK (claim_percent>=0 AND claim_percent<=100),
  verification_state TEXT NOT NULL DEFAULT 'MARKETING_CLAIM_UNVERIFIED',
  PRIMARY KEY (run_id,claim_key)
);
COMMENT ON TABLE formula_optimization_runs IS 'Simulation and review data only: never legal, stability, safety or manufacturing approval.';
COMMENT ON TABLE formula_optimization_component_ranges IS 'Quantitative commercial-grade components; no fabricated fraction if grade assay unknown.';
