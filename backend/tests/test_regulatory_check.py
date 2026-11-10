"""Kiểm tra sơ bộ theo bộ luật tham chiếu đồng bộ từ check_formula.py."""
from fastapi.testclient import TestClient

from main import app
from regulatory_check import RegulatoryCheckIn, check_limit

client = TestClient(app)


def run(**kwargs):
    base = {'market': 'EU', 'category': 'leave_on', 'purpose': 'preservative', 'inci': 'Phenoxyethanol', 'pct': 1.0}
    base.update(kwargs)
    return check_limit(RegulatoryCheckIn(**base))


def test_above_numeric_max_is_flagged():
    r = run(pct=1.2)
    assert r['status'] == 'EXCEEDS_NUMERIC_MAX'
    assert r['limit_pct'] == 1
    assert r['rule_id'] == 'CR-0113'


def test_below_numeric_max_is_not_flagged():
    assert run(pct=0.5)['status'] == 'NOT_ABOVE_NUMERIC_MAX'


def test_basis_mismatch_requires_conversion():
    assert run(pct=1.2, basis='as_benzoic_acid')['status'] == 'NEEDS_BASIS_CONVERSION'


def test_no_matching_rule_never_means_allowed():
    r = run(market='KR')
    assert r['status'] == 'NEEDS_LEGAL_REVIEW'
    assert 'does not imply allowed' in r['explanation']


def test_unknown_ingredient_needs_legal_review():
    assert run(inci='Nonexistent Thing')['status'] == 'NEEDS_LEGAL_REVIEW'


def test_manual_conditions_are_not_auto_decided():
    r = run(market='US', category='otc_sunscreen_drug', purpose='otc_sunscreen_active', inci='Bemotrizinol', pct=1.0)
    assert r['status'] == 'MANUAL_CONDITIONS_REQUIRED'


def test_endpoint_returns_same_result_and_disclaimer():
    body = {'market': 'EU', 'category': 'leave_on', 'purpose': 'preservative', 'inci': 'Phenoxyethanol', 'pct': 1.2}
    r = client.post('/api/v2/regulatory/check', json=body)
    assert r.status_code == 200
    assert r.json()['status'] == 'EXCEEDS_NUMERIC_MAX'
    assert 'Never use as regulatory approval' in r.json()['disclaimer']


def test_endpoint_rejects_negative_pct():
    body = {'market': 'EU', 'category': 'leave_on', 'inci': 'Phenoxyethanol', 'pct': -1}
    assert client.post('/api/v2/regulatory/check', json=body).status_code == 422
