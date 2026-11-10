import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from compatibility_engine import KnowledgeEngine
from api import app

ROOT=Path(__file__).resolve().parent
engine=KnowledgeEngine()

def scenario(physical_form='aqueous',ph=None,water=None,items=None,**opts):
    return {'product_type':'Test', 'physical_form':physical_form,'pH':ph,'water_phase_percent':water,
            'items':items or [],**opts}
def item(inci,pct,grp='active',**kwargs):
    return {'inci':inci,'percent':pct,'group_code':grp,**kwargs}
def codes(r):return [x['code'] for x in r['issues']]

def test_inventory_inherits_v41():
    assert len(engine.properties)==190
    assert len(engine.group_rules)==390
    assert len(engine.grades)==10

def test_scoped_evidence_only_four_profiles():
    assert sum(p['property_status']!='not_assessed' for p in engine.properties)==4
    assert engine.by_name['glycerin']['ph_min']==''

def test_mass_balance_no_virtual_ui_100_added():
    s=json.loads((ROOT/'examples/lip_balm_v41.json').read_text(encoding='utf8'))
    r=engine.evaluate(s)
    assert r['raw_material_mass_percent']==100
    assert r['primary_groups_raw_material_percent']['b_lip']==40
    assert r['manufacturing_approval'] is False

def test_trade_grade_keeps_unknown_carrier():
    s=json.loads((ROOT/'examples/lip_balm_v41.json').read_text(encoding='utf8'))
    r=engine.evaluate(s)
    assert r['known_trade_grade_inci_contributions_percent']['Tocopherol']==.75
    assert r['trade_grade_unresolved_mass_percent']==.75
    assert 'GRADE_COMPOSITION_UNRESOLVED' in codes(r)

def test_allantoin_pH_outside_reference():
    r=engine.evaluate(scenario(ph=3.2,water=50,items=[item('Allantoin',.2),item('Aqua',99.8)]))
    assert 'PH_OUTSIDE_SUPPLIER_REFERENCE' in codes(r)

def test_allantoin_pH_in_reference():
    r=engine.evaluate(scenario(ph=5.5,water=99.8,items=[item('Allantoin',.2),item('Aqua',99.8)]))
    assert 'PH_OUTSIDE_SUPPLIER_REFERENCE' not in codes(r)

def test_allantoin_relative_water_solubility_screen():
    r=engine.evaluate(scenario(ph=6,water=20,items=[item('Allantoin',.4),item('Aqua',99.6)]))
    assert 'ALLANTOIN_AQUEOUS_SOLUBILITY_SCREEN' in codes(r)

def test_allantoin_no_phase_denominator_does_not_fake_result():
    r=engine.evaluate(scenario(ph=6,items=[item('Allantoin',.4),item('Aqua',99.6)]))
    assert 'ALLANTOIN_AQUEOUS_SOLUBILITY_SCREEN' not in codes(r)
    assert 'WATER_PHASE_NOT_QUANTIFIED' in codes(r)

def test_bisabolol_needs_solubilization_screen():
    r=engine.evaluate(scenario(items=[item('Bisabolol',1),item('Aqua',99)]))
    assert 'OIL_SOLUBLE_IN_AQUEOUS_ONLY_SYSTEM' in codes(r)
    r2=engine.evaluate(scenario(items=[item('Bisabolol',1),item('Aqua',99)],solubilizer_system_confirmed=True))
    assert 'OIL_SOLUBLE_IN_AQUEOUS_ONLY_SYSTEM' not in codes(r2)

def test_anhydrous_panthenol_review_not_absolute_incompatibility():
    r=engine.evaluate(scenario(physical_form='anhydrous',items=[item('Panthenol',1),item('Cera Alba',99)]))
    assert 'ANHYDROUS_HYDROPHILIC_INGREDIENT' in codes(r)
    assert r['scientific_compatibility_status']=='REVIEW_REQUIRED'

def test_micobiology_is_review_not_legal_disapproval():
    r=engine.evaluate(scenario(water=70,items=[item('Aqua',100)]))
    assert 'PRESERVATION_ASSESSMENT_NEEDED' in codes(r)
    assert r['regulatory_status']=='NOT_ASSESSED'

def test_no_unverified_percent_ph_limits():
    for p in engine.properties:
        if p['property_status']=='not_assessed':
            assert not p['ph_min'] and not p['ph_max'] and not p['water_solubility_percent_25c']

def test_invalid_inputs_blocked():
    with pytest.raises(ValueError): engine.evaluate(scenario(items=[item('Aqua',float('nan'))]))
    with pytest.raises(ValueError): engine.evaluate(scenario(ph=19,items=[]))
    with pytest.raises(ValueError): engine.evaluate(scenario(items=[item('Aqua',-2)]))

def test_api_works():
    client=TestClient(app)
    assert client.get('/health').json()['ok']
    assert len(client.get('/api/v4.2/ingredients?q=Allantoin').json()['results'])==1
    s=json.loads((ROOT/'examples/serum_review.json').read_text(encoding='utf8'))
    response=client.post('/api/v4.2/evaluate',json=s)
    assert response.status_code==200
    assert response.json()['raw_material_mass_percent']==100
    assert response.json()['manufacturing_approval'] is False

def test_no_total_if_mass_not_100():
    r=engine.evaluate(scenario(items=[item('Aqua',60)]))
    assert 'MASS_BALANCE_FAILED' in codes(r)


def test_v41_template_actual_integration():
    s=json.loads((ROOT/'examples/lip_balm_v41.json').read_text(encoding='utf8'))
    r=engine.evaluate(s)
    assert r['v41_group_validation'] is not None
    assert r['v41_group_validation']['raw_material_total_percent']==100
    assert 'V41_GROUP_TEMPLATE_REVIEW' not in codes(r)

def test_template_endpoint():
    r=TestClient(app).get('/api/v4.2/templates')
    assert r.status_code==200
    assert len(r.json()['templates'])==33
