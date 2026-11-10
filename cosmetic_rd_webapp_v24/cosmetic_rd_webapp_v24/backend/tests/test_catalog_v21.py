import pytest
from fastapi.testclient import TestClient
from engine import analyze
from main import app


def ingredient(out, inci):
    return next(item for item in out['results'] if item['ingredient'] == inci)


def test_catalog_references_have_real_identifiers():
    client = TestClient(app)
    res = client.get('/api/v2/catalog/research')
    assert res.status_code == 200
    assert res.json()['metadata']['record_count'] >= 5
    assert all(x['source_url'].startswith('https://') and x['doi'] and x['pmid'] for x in res.json()['data'])


def test_default_attaches_preservation_measured_evidence_without_changing_lp():
    base = {'market': 'EU', 'inci': 'Aqua, Phenoxyethanol'}
    r_off = analyze(base | {'include_catalog_evidence': False})
    r_on = analyze(base)
    a, b = ingredient(r_off, 'Phenoxyethanol'), ingredient(r_on, 'Phenoxyethanol')
    assert (a['min_pct'], a['max_pct']) == (b['min_pct'], b['max_pct'])
    assert b['research_evidence'][0]['category'] == 'measured_market_product'
    assert b['research_evidence'][0]['min_pct'] == 0.19
    assert b['research_evidence'][0]['sample_count'] == 4
    assert b['estimated_pct'] is None


def test_study_5pct_not_a_physical_constraint():
    r = analyze({'market': 'VN', 'inci': 'Aqua, Niacinamide'})
    nia = ingredient(r, 'Niacinamide')
    assert nia['min_pct'] < 5 and nia['max_pct'] > 5
    assert nia['research_evidence'][0]['category'] == 'clinical_efficacy'
    assert nia['research_evidence'][0]['max_pct'] == 5


def test_eu_regulatory_limit_not_applied_by_default():
    r = analyze({'market': 'EU', 'inci': 'Aqua, Phenoxyethanol'})
    x = ingredient(r,'Phenoxyethanol')
    assert x['max_pct'] > 1
    assert x['regulatory_references'][0]['max_pct'] == 1
    assert r['applied_catalog_limits'] == []


def test_eu_regulatory_applies_only_when_opted_in_and_use_is_matched():
    x = {'market':'EU','inci':'Aqua, Phenoxyethanol', 'apply_catalog_limits':True, 'intended_use':{'Phenoxyethanol':'preservative'}}
    r = analyze(x)
    assert ingredient(r,'Phenoxyethanol')['max_pct'] <= 1 + 1e-7
    assert len(r['applied_catalog_limits']) == 1
    assert analyze(x | {'intended_use':{'Phenoxyethanol':'solvent'}})['applied_catalog_limits'] == []
    assert ingredient(analyze(x | {'market':'VN'}),'Phenoxyethanol')['max_pct'] > 1


def test_exact_ppm_converts_to_pct():
    r = analyze({'market':'VN','inci':'Aqua, Niacinamide', 'declared_concentrations':{'Niacinamide': {'value':50000,'unit':'ppm','source':'nhãn đã xác minh'}}})
    x = ingredient(r, 'Niacinamide')
    assert x['min_pct']==x['max_pct']==5
    assert x['claims_annotations'][0]['converted_pct'] == 5


def test_exact_mg_per_g_converts_to_pct():
    r = analyze({'market':'EU','inci':'Aqua, Glycerin', 'declared_concentrations':{'Glycerin': {'value':20,'unit':'mg_per_g','source':'COA'}}})
    assert ingredient(r,'Glycerin')['min_pct']==2


def test_approximate_claim_is_not_forced():
    r = analyze({'market':'EU','inci':'Aqua, Niacinamide', 'declared_concentrations':{'Niacinamide': {'value':5,'unit':'percent','precision':'approximate','source':'marketing'}}})
    assert ingredient(r,'Niacinamide')['max_pct'] > 5
    assert any('xấp xỉ' in w for w in r['warnings'])


def test_commercial_complex_claim_is_rejected():
    with pytest.raises(ValueError, match='premixes'):
        analyze({'market':'EU','inci':'Aqua, Niacinamide','declared_concentrations':{'Niacinamide':{'value':5,'basis':'commercial_premix','source':'label'}}})


def test_percent_greater_than_100_rejected():
    with pytest.raises(ValueError, match='vượt 100%'):
        analyze({'market':'EU','inci':'Aqua, Niacinamide','declared_concentrations':{'Niacinamide':{'value':1100000,'unit':'ppm','source':'typo'}}})


def test_incompatible_catalog_law_and_claim_is_infeasible():
    r=analyze({'market':'EU','inci':'Aqua, Phenoxyethanol','apply_catalog_limits':True, 'intended_use':{'Phenoxyethanol':'preservative'},'known_pct':{'Phenoxyethanol':{'value':2,'source':'label'}}})
    assert r['status'] == 'infeasible'


def test_catalog_unknown_does_not_imply_lawful():
    r=analyze({'market':'KR','inci':'Aqua, Ethylhexylglycerin', 'apply_catalog_limits':True, 'intended_use':{'Ethylhexylglycerin':'preservative'}})
    assert r['status']=='feasible'
    assert r['applied_catalog_limits']==[]
    assert any('không có mục phù hợp' in w for w in r['warnings'])


def test_api_enriched_analysis():
    client = TestClient(app)
    res = client.post('/api/v2/analyze', json={'market':'EU','inci':'Aqua, Niacinamide'})
    assert res.status_code == 200
    assert res.json()['catalog_versions']['evidence']
    assert ingredient(res.json(), 'Niacinamide')['research_evidence'][0]['source_kind']=='reviewed_catalog'


def test_preservation_system_matches_do_not_change_lp():
    inci='Aqua, Phenoxyethanol, Caprylyl Glycol, Ethylhexylglycerin'
    r=analyze({'market':'EU','inci':inci})
    matches=next(x for x in r['preservation_system_matches'] if x['system_number']==3)
    assert matches['full_ingredient_match'] is True
    assert matches['outcome_code']=='failed_fungi'
    assert ingredient(r,'Phenoxyethanol')['estimated_pct'] is None
    assert ingredient(r,'Phenoxyethanol')['max_pct'] > .51


def test_preservation_system_partial_match_has_no_joint_claim():
    r=analyze({'market':'EU','inci':'Aqua, Sodium Benzoate'})
    x=next(x for x in r['preservation_system_matches'] if x['system_number']==2)
    assert x['full_ingredient_match'] is False
    assert x['individual_intervals_contain_studied_values'] is None


def test_preservation_catalog_api():
    res=TestClient(app).get('/api/v2/catalog/preservation?inci=Potassium%20Sorbate')
    assert res.status_code==200
    assert len(res.json()['data'])==1
    assert res.json()['data'][0]['system_number']==2
