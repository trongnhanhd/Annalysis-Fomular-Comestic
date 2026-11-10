-- V4.2 additive migration only. Review against existing migrations before applying.
-- This SQL intentionally DOES NOT assign legal status or mark ingredients approved.
CREATE TABLE IF NOT EXISTS ingredient_knowledge_profiles (
  ingredient_id TEXT PRIMARY KEY,
  inci_name_candidate TEXT NOT NULL,
  v41_phase_candidate TEXT,
  phase TEXT,
  solubility_water TEXT,
  solubility_oil TEXT,
  water_solubility_percent_25c NUMERIC(12,5),
  reference_ph_min NUMERIC(5,2),
  reference_ph_max NUMERIC(5,2),
  temperature_note TEXT,
  evidence_id TEXT,
  grade_scope TEXT,
  property_status TEXT NOT NULL DEFAULT 'not_assessed',
  regulatory_status TEXT NOT NULL DEFAULT 'not_assessed',
  verified_at TIMESTAMPTZ,
  verified_by TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_ph_range CHECK ((reference_ph_min IS NULL OR reference_ph_min BETWEEN 0 AND 14) AND (reference_ph_max IS NULL OR reference_ph_max BETWEEN 0 AND 14)),
  CONSTRAINT chk_profile_status CHECK (property_status IN ('not_assessed','supplier_grade_reference','grade_specific_review','lab_verified'))
);
CREATE TABLE IF NOT EXISTS ingredient_evidence_sources (
 source_id TEXT PRIMARY KEY,
 source_name TEXT NOT NULL,
 source_type TEXT NOT NULL,
 source_url TEXT,
 document_date TEXT,
 applicability_scope TEXT NOT NULL,
 verification TEXT NOT NULL,
 captured_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS commercial_grade_models (
 grade_id TEXT PRIMARY KEY,
 display_name TEXT NOT NULL,
 expected_inci TEXT,
 supplier_name TEXT,
 active_fraction_min NUMERIC(12,8),
 active_fraction_max NUMERIC(12,8),
 carrier_inci TEXT,
 source_id TEXT REFERENCES ingredient_evidence_sources(source_id),
 composition_complete BOOLEAN NOT NULL DEFAULT FALSE,
 verification_status TEXT NOT NULL DEFAULT 'NEED_COA_AND_FULL_INCI',
 CONSTRAINT chk_assay CHECK (active_fraction_min IS NULL OR (active_fraction_min>=0 AND active_fraction_min<=1)),
 CONSTRAINT chk_assay_max CHECK (active_fraction_max IS NULL OR (active_fraction_max>=0 AND active_fraction_max<=1))
);
CREATE TABLE IF NOT EXISTS commercial_grade_components (
 grade_id TEXT NOT NULL REFERENCES commercial_grade_models(grade_id),
 component_order INTEGER NOT NULL,
 component_inci TEXT NOT NULL,
 nominal_mass_fraction NUMERIC(12,8) NOT NULL CHECK (nominal_mass_fraction BETWEEN 0 AND 1),
 evidence_status TEXT NOT NULL,
 is_unknown_remainder BOOLEAN NOT NULL DEFAULT FALSE,
 PRIMARY KEY (grade_id,component_order)
);
CREATE TABLE IF NOT EXISTS compatibility_rule_definitions (
 rule_id TEXT PRIMARY KEY,
 severity TEXT NOT NULL,
 statement_vi TEXT NOT NULL,
 evidence_source_id TEXT,
 rule_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
 reviewed_at TIMESTAMPTZ,
 reviewed_by TEXT,
 enabled BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS compatibility_screening_runs (
 run_id UUID PRIMARY KEY,
 formula_scenario_id TEXT,
 engine_version TEXT NOT NULL,
 input_snapshot JSONB NOT NULL,
 findings JSONB NOT NULL,
 regulatory_status TEXT NOT NULL DEFAULT 'NOT_ASSESSED',
 stability_status TEXT NOT NULL DEFAULT 'NOT_TESTED',
 manufacturing_approval BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ingredient_profiles_evidence ON ingredient_knowledge_profiles(evidence_id);
CREATE INDEX IF NOT EXISTS ix_compat_runs_created ON compatibility_screening_runs(created_at DESC);
