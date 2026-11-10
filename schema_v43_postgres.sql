-- Additive migration sketch for V4.3. Do not execute on production without schema review.
-- All external facts scoped to named supplier grade and immutable evidence.
CREATE TABLE IF NOT EXISTS fi_v43_sources (
    source_id TEXT PRIMARY KEY,
    source_title TEXT NOT NULL,
    source_url TEXT,
    source_type TEXT NOT NULL,
    use_scope TEXT,
    checked_on DATE,
    evidence_status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fi_v43_supplier_grades (
    grade_id TEXT PRIMARY KEY,
    grade_name TEXT NOT NULL,
    inci_declared TEXT NOT NULL,
    supplier TEXT,
    use_context TEXT,
    source_id TEXT NOT NULL REFERENCES fi_v43_sources(source_id),
    composition_status TEXT NOT NULL,
    coa_verified BOOLEAN NOT NULL DEFAULT FALSE,
    regulatory_approved BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS fi_v43_grade_observations (
    observation_id TEXT PRIMARY KEY,
    ingredient_id TEXT,
    inci_candidate TEXT NOT NULL,
    grade_id TEXT NOT NULL REFERENCES fi_v43_supplier_grades(grade_id),
    property_key TEXT NOT NULL,
    value_min NUMERIC,
    value_max NUMERIC,
    unit TEXT,
    qualitative_value TEXT,
    conditions_and_scope TEXT,
    applies_to TEXT,
    source_id TEXT NOT NULL REFERENCES fi_v43_sources(source_id),
    evidence_status TEXT NOT NULL,
    note_vi TEXT,
    CHECK (value_min IS NULL OR value_max IS NULL OR value_min <= value_max)
);
CREATE TABLE IF NOT EXISTS fi_v43_grade_components_qualitative (
    grade_id TEXT NOT NULL REFERENCES fi_v43_supplier_grades(grade_id),
    component_order INTEGER NOT NULL CHECK (component_order>0),
    component_inci_candidate TEXT NOT NULL,
    concentration_basis TEXT NOT NULL DEFAULT 'unknown',
    status TEXT NOT NULL DEFAULT 'qualitative_composition_only',
    PRIMARY KEY (grade_id,component_order)
);
CREATE TABLE IF NOT EXISTS fi_v43_review_events (
    review_id UUID PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    grade_id TEXT REFERENCES fi_v43_supplier_grades(grade_id),
    issue_code TEXT NOT NULL,
    severity TEXT NOT NULL,
    source_id TEXT REFERENCES fi_v43_sources(source_id),
    evidence_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    reviewed_by TEXT,
    reviewed_on TIMESTAMPTZ,
    review_status TEXT NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS fi_v43_obs_grade_key_idx ON fi_v43_grade_observations (grade_id,property_key);
CREATE INDEX IF NOT EXISTS fi_v43_review_scenario_idx ON fi_v43_review_events (scenario_id,review_status);
