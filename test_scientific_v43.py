import json
from pathlib import Path
from fastapi.testclient import TestClient
from scientific_engine_v43 import ScientificEngineV43
from api_v43 import app

BASE=Path(__file__).resolve().parent
engine=ScientificEngineV43()
def load():return json.loads((BASE/'examples/lip_balm_grades_v43.json').read_text(encoding='utf8'))
def codes(r):return [i['code'] for i in r['issues']]

def test_inherits_190_inci_390_rules():
    assert len(engine.v42.properties)==190
    assert len(engine.v42.group_rules)==390

def test_supplier_facts_scoped_not_global():
    assert len(engine.grades)==11
    assert len(engine.observations)==22
    assert all(o['source_id'] and o['source_url'] for o in engine.observations)
    assert not any(o['property_key']=='legal_maximum' for o in engine.observations)

def test_no_grade_means_no_assumed_use_range():
    s=load()
    s['items'][0].pop('grade_id');s['items'][1].pop('grade_id')
    r=engine.evaluate(s)
    assert r['v43_observation_count_used']==0
    assert 'OUTSIDE_SUPPLIER_USE_REFERENCE' not in codes(r)

def test_low_melting_process_warning_only_given_full_melt_intent():
    r=engine.evaluate(load())
    assert codes(r).count('PROCESS_TEMP_BELOW_GRADE_MELT_RANGE')==2
    s=load();s['process_intent']='unknown'
    assert 'PROCESS_TEMP_BELOW_GRADE_MELT_RANGE' not in codes(engine.evaluate(s))

def test_supplier_use_range_not_legality():
    s=load();s['items'][0]['percent']=22;s['items'][4]['percent']=26.5
    r=engine.evaluate(s)
    assert 'OUTSIDE_SUPPLIER_USE_REFERENCE' in codes(r)
    assert r['regulatory_status']=='NOT_ASSESSED'
    assert r['manufacturing_approval'] is False

def test_not_selected_grade_cannot_leak_to_other_beeswax_grade():
    s=load();s['items'][0]['grade_id']='S43-G-K8139';s['process_temperature_c']=61
    r=engine.evaluate(s)
    o=[x for x in r['issues'] if x['code']=='PROCESS_TEMP_BELOW_GRADE_MELT_RANGE' and x.get('grade_id')=='S43-G-K8139']
    assert len(o)==1 and o[0]['details']['grade_melting_point_c']==[62,65]

def test_premix_does_not_invent_component_percent():
    s={'product_type':'lipstick','physical_form':'anhydrous','items':[{'inci':'KahlBase 4074','grade_id':'S43-G-K4074','percent':88},{'inci':'Tocopherol','percent':12}]}
    r=engine.evaluate(s)
    assert r['raw_material_mass_percent']==100
    assert 'GRADE_COMPONENT_FRACTIONS_UNKNOWN' in codes(r)
    assert r['known_trade_grade_inci_contributions_percent']=={}
    assert r['manufacturing_approval'] is False

def test_premix_supplier_use_range_only_lipstick():
    s={'product_type':'lip_balm','items':[{'inci':'KahlBase 4074','grade_id':'S43-G-K4074','percent':50},{'inci':'Aqua','percent':50}]}
    r=engine.evaluate(s)
    assert 'GRADE_PRODUCT_SCOPE_NOT_MATCHED' in codes(r)
    assert 'OUTSIDE_SUPPLIER_USE_REFERENCE' not in codes(r)

def test_nipaguard_grade_ph_not_general_phenoxyethanol():
    s={'product_type':'aqueous_serum','physical_form':'aqueous','pH':13,'items':[{'inci':'Phenoxyethanol','grade_id':'S43-G-NIP9010','percent':1},{'inci':'Aqua','percent':99}]}
    assert 'PH_ABOVE_SUPPLIER_GRADE_STABILITY_REFERENCE' in codes(engine.evaluate(s))
    s['items'][0].pop('grade_id')
    assert 'PH_ABOVE_SUPPLIER_GRADE_STABILITY_REFERENCE' not in codes(engine.evaluate(s))

def test_qualitative_grade_component_unknown():
    s={'product_type':'aqueous_serum','physical_form':'aqueous','pH':6,'items':[{'inci':'Phenoxyethanol','grade_id':'S43-G-NIP9010','percent':1},{'inci':'Aqua','percent':99}]}
    r=engine.evaluate(s)
    component=[i for i in r['issues'] if i['code']=='GRADE_COMPONENT_FRACTIONS_UNKNOWN'][0]
    assert not component['details']['can_compute_final_inci_percent']
    assert len(component['details']['known_component_names'])==2

def test_api_health_grades_coverage_and_evaluate():
    c=TestClient(app)
    assert c.get('/health').json()['version']=='4.3.0'
    assert c.get('/api/v4.3/grades').json()['total']==21
    assert c.get('/api/v4.3/coverage').json()['v43_scientific_observations']==22
    assert c.post('/api/v4.3/evaluate',json=load()).json()['raw_material_mass_percent']==100

def test_invalid_process_intent_and_temp():
    s=load();s['process_intent']='magical';assert_raises_value(s)
    s=load();s['process_temperature_c']=250;assert_raises_value(s)

def assert_raises_value(s):
    try:engine.evaluate(s)
    except ValueError:return
    raise AssertionError('Expected ValueError')
