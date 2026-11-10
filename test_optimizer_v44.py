import copy,json
from pathlib import Path
import pytest
from optimizer_v44 import solve_scenario,solve_claim_alternatives,InputError
from formula_group_service import Catalog
from fastapi.testclient import TestClient
from api_v44 import app
ROOT=Path(__file__).resolve().parent
CATALOG=Catalog()

def read_example(name):return json.loads((ROOT/'examples'/name).read_text(encoding='utf8'))

def test_lip_balm_strict_structural_and_mass_100():
    out=solve_scenario(read_example('lip_balm_optimizer_v44.json'),CATALOG)
    assert out['status']=='FEASIBLE'
    assert out['raw_material_total_percent']==100
    assert abs(sum(g['percent_example'] for g in out['groups'])-100)<1e-3
    assert not out['approved_for_manufacturing']

def test_premix_unknown_is_not_fabricated_as_inci():
    out=solve_scenario(read_example('lip_balm_optimizer_v44.json'),CATALOG)
    assert out['fully_resolved_inci'] is False
    assert out['unresolved_composition_percent_example']>0
    inci={r['inci'] for r in out['inci_known_contributions']}
    assert 'unknown_base' not in inci

def test_claim_ambiguity_runs_both_bases():
    out=solve_claim_alternatives(read_example('pad_claim_ambiguity_v44.json'))
    assert out['scenario_count']==2
    assert [x['result']['status'] for x in out['scenarios']]==['FEASIBLE','FEASIBLE']
    raw,fin=out['scenarios']
    raw_pct=next(x['percent_example'] for x in raw['result']['items'] if x['item_id']=='pad_grade')
    fin_pct=next(x['percent_example'] for x in fin['result']['items'] if x['item_id']=='pad_grade')
    assert abs(raw_pct-8)<1e-5
    assert abs(fin_pct-8/0.3)<1e-4

def test_mass_is_raw_not_double_counting_inci():
    x=solve_claim_alternatives(read_example('pad_claim_ambiguity_v44.json'))['scenarios'][0]['result']
    assert x['raw_material_total_percent']==100
    assert abs(sum(z['percent_example_known_contribution'] for z in x['inci_known_contributions'])-100)<1e-3
    assert abs(next(z['percent_example_known_contribution'] for z in x['inci_known_contributions'] if z['inci']=='potassium azeloyl diglycinate')-2.4)<1e-5

def test_infeasible_conflicting_claims_return_diagnostic():
    d=read_example('pad_claim_ambiguity_v44.json');d.pop('ambiguous_claims')
    d['claims']=[{'basis':'raw_material','item_id':'pad_grade','percent':8},{'basis':'finished_inci','inci':'Potassium Azeloyl Diglycinate','percent':8}]
    out=solve_scenario(d)
    assert out['status']=='INFEASIBLE'
    assert out['diagnostic_single_constraint_removals']

def test_unresolved_premix_blocks_finished_inci_claim():
    d=read_example('lip_balm_optimizer_v44.json')
    d['claims']=[{'basis':'finished_inci','inci':'Cera Alba','percent':18}]
    out=solve_scenario(d,CATALOG)
    assert out['status']=='INSUFFICIENT_DATA_OR_SELECTION'
    assert 'FINISHED_CLAIM_INDETERMINATE' in [x['code'] for x in out['issues']]

def test_optional_template_is_advisory():
    d=read_example('lip_balm_optimizer_v44.json');d['template_mode']='advisory'
    d['items'][1]['percent_bounds']={'min':42,'max':42}
    out=solve_scenario(d,CATALOG)
    assert out['status']=='FEASIBLE'
    assert 'OUTSIDE_SCREENSHOT_REFERENCE' in [x['code'] for x in out['issues']]

def test_strict_template_is_hard():
    d=read_example('lip_balm_optimizer_v44.json')
    d['items'][1]['percent_bounds']={'min':42,'max':42}
    out=solve_scenario(d,CATALOG)
    assert out['status']=='INFEASIBLE'

def test_invalid_fraction_sum_rejected():
    d=read_example('lip_balm_optimizer_v44.json')
    d['items'][1]['composition']['components'][0]['fraction_min']=0.2
    d['items'][1]['composition']['components'][0]['fraction_max']=0.4
    with pytest.raises(InputError):solve_scenario(d,CATALOG)

def test_unknown_group_user_hard_error():
    d=read_example('lip_balm_optimizer_v44.json')
    d['group_limits']=[{'group_code':'does_not_exist','min_percent':10,'max_percent':20}]
    out=solve_scenario(d,CATALOG)
    assert out['status']=='INSUFFICIENT_DATA_OR_SELECTION'

def test_intervals_contain_example():
    out=solve_scenario(read_example('lip_balm_optimizer_v44.json'),CATALOG)
    for r in out['items']+out['groups']:
        lo,hi=r['feasible_interval_percent']
        assert lo-1e-4 <=r['percent_example']<=hi+1e-4

def test_json_api_and_previous_routes_available():
    c=TestClient(app)
    assert c.get('/health/v4.4').status_code==200
    assert c.get('/api/v4.3/grades').status_code==200
    assert c.get('/api/v4.4/templates').status_code==200
    assert c.post('/api/v4.4/optimize',json=read_example('lip_balm_optimizer_v44.json')).json()['status']=='FEASIBLE'
    assert c.post('/api/v4.4/compare-claims',json=read_example('pad_claim_ambiguity_v44.json')).json()['scenario_count']==2

def test_scientific_status_not_falsely_approved():
    out=solve_scenario(read_example('lip_balm_optimizer_v44.json'),CATALOG)
    assert out['regulatory_status']=='NOT_ASSESSED' and out['stability_status']=='NOT_TESTED'

def test_all_results_distinguish_known_contribution():
    out=solve_scenario(read_example('lip_balm_optimizer_v44.json'),CATALOG)
    assert all(r['basis']=='known_contributions_only' for r in out['inci_known_contributions'])

def test_inci_order_screening_does_not_claim_legal_pass():
    out=solve_claim_alternatives(read_example('pad_claim_ambiguity_v44.json'))
    assert all(s['result']['label_order_screening']['status'] in ('WARNING_ORDER_CONFLICT','CONSISTENT_WITH_BASIC_ORDER') for s in out['scenarios'])

def test_compare_claims_api_optional_scientific_screening():
    d=read_example('pad_claim_ambiguity_v44.json');d['include_scientific_screening']=True
    c=TestClient(app)
    out=c.post('/api/v4.4/compare-claims',json=d).json()
    assert all(s['result']['scientific_screening']['approved_for_manufacturing'] is False for s in out['scenarios'])

def test_fractional_grade_interval_is_not_point_assumption():
    d=read_example('pad_claim_ambiguity_v44.json');d.pop('ambiguous_claims')
    grade=next(x for x in d['items'] if x['item_id']=='pad_grade')
    grade['composition']['components'][0]['fraction_min']=0.28
    grade['composition']['components'][0]['fraction_max']=0.32
    grade['composition']['components'][1]['fraction_min']=0.68
    grade['composition']['components'][1]['fraction_max']=0.72
    d['claims'].append({'basis':'raw_material','item_id':'pad_grade','percent':8})
    out=solve_scenario(d)
    assert out['status']=='FEASIBLE'
    pad=next(x for x in out['inci_known_contributions'] if x['inci']=='potassium azeloyl diglycinate')
    assert abs(pad['feasible_known_contribution_interval_percent'][0]-2.24)<1e-4
    assert abs(pad['feasible_known_contribution_interval_percent'][1]-2.56)<1e-4
