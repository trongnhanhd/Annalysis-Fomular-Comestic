"""Unit and integration checks for non-fabricated R&D evidence workflow."""
import json, math, os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from experimental_validation_v45 import build_doe, verify_protocol, evaluate_study, InputError
from experimental_repository_v45 import Repository
from api_v45 import app
from formula_group_service import Catalog

BASE=Path(__file__).parent

def load(name):return json.loads((BASE/'examples'/name).read_text(encoding='utf-8'))

@pytest.fixture
def repo(tmp_path):return Repository(str(tmp_path/'exp.sqlite3'))

@pytest.fixture
def study(repo):return repo.create_study(load('lip_balm_study_v45.json'))['study_id']

def valid_m(repo,st,bid,**updates):
    body={'batch_id':bid,'metric_code':'HARDNESS','day':0,'value':3.4,'unit':'N',
          'method':'LAB-HARD-01','instrument_id':'TEXTURE-01','operator':'Tester',
          'evidence_uri':'labbook://project-1/measurement-001','data_kind':'MEASURED'}
    body.update(updates)
    return repo.add_measurement(st,body)

def test_protocol_requires_nonempty_metrics():
    with pytest.raises(InputError):verify_protocol({'metrics':[]})

def test_protocol_invalid_bounds():
    with pytest.raises(InputError):verify_protocol({'metrics':[{'code':'PH','unit':'pH','target_min':7,'target_max':3}]})

def test_protocol_duplicate_metric():
    with pytest.raises(InputError):verify_protocol({'metrics':[{'code':'PH','unit':'pH'}, {'code':'PH','unit':'pH'}]})

def test_protocol_nan_rejected():
    with pytest.raises(InputError):verify_protocol({'metrics':[{'code':'PH','unit':'pH','target_max':float('nan')}]})

def test_doe_five_feasible_candidates():
    result=build_doe(load('lip_balm_doe_v45.json'),Catalog())
    assert result['candidate_count']==5 and result['feasible_count']==5
    assert result['approved_for_manufacturing'] is False
    for c in result['results']:
        assert c['status']=='FEASIBLE'
        assert math.isclose(sum(c['composition_percent'].values()),100,abs_tol=1e-5)

def test_doe_factor_excess_rejected_by_constraint():
    body=load('lip_balm_doe_v45.json')
    body['variables']=[{'item_id':'beeswax','low':1,'high':50}]
    result=build_doe(body,Catalog())
    assert result['feasible_count']<result['candidate_count']

def test_doe_rejects_balance_factor_collision():
    body=load('lip_balm_doe_v45.json')
    body['balance_item_id']='beeswax'
    with pytest.raises(InputError):build_doe(body,Catalog())

def test_doe_claim_ambiguity_must_be_explicit_for_study(repo):
    body=load('lip_balm_study_v45.json')
    body['scenario']['ambiguous_claims']=[{'percent':8,'interpretations':[]}]
    with pytest.raises(InputError):repo.create_study(body)

def test_study_is_immutable_snapshot(repo,study):
    s=repo.get_study(study)
    assert len(s['formula_sha256'])==64
    assert s['protocol']['metrics'][0]['code']=='HARDNESS'
    assert repo.report(study)['status']=='NO_BATCH'

def test_missing_record_is_incomplete(repo,study):
    b=repo.add_batch(study,{'lot_code':'LAB-01','operator':'Researcher'})
    report=repo.report(study)
    assert report['status']=='NO_MEASUREMENTS'
    assert report['required_slots']==8 and report['completed_slots']==0

def test_real_measurement_requires_evidence(repo,study):
    b=repo.add_batch(study,{'lot_code':'LAB-02','operator':'Researcher'})['batch_id']
    with pytest.raises(InputError):valid_m(repo,study,b,evidence_uri='')

def test_fake_evidence_cannot_be_real(repo,study):
    b=repo.add_batch(study,{'lot_code':'LAB-02','operator':'Researcher'})['batch_id']
    with pytest.raises(InputError):valid_m(repo,study,b,evidence_uri='demo:placeholder')

def test_synthetic_evidence_not_counted(repo,study):
    b=repo.add_batch(study,{'lot_code':'LAB-03','operator':'Researcher'})['batch_id']
    valid_m(repo,study,b,data_kind='DEMO_SYNTHETIC',evidence_uri='demo:placeholder')
    rep=repo.report(study)
    assert rep['status']=='NO_MEASUREMENTS'
    assert rep['completed_slots']==0
    assert rep['observations_demo_excluded']==1

def test_one_real_measurement_is_incomplete(repo,study):
    b=repo.add_batch(study,{'lot_code':'LAB-04','operator':'Researcher'})['batch_id']
    valid_m(repo,study,b)
    rep=repo.report(study)
    assert rep['status']=='INCOMPLETE' and rep['completed_slots']==1
    assert rep['classified_measurements'][0]['classification']=='WITHIN_USER_SPEC'

def test_out_of_spec_triggers_flag(repo,study):
    b=repo.add_batch(study,{'lot_code':'LAB-05','operator':'Researcher'})['batch_id']
    valid_m(repo,study,b,value=9)
    rep=repo.report(study)
    assert rep['status']=='OUT_OF_USER_SPEC' and rep['out_of_user_spec_count']==1

def test_wrong_unit_rejected(repo,study):
    b=repo.add_batch(study,{'lot_code':'LAB-06','operator':'Researcher'})['batch_id']
    with pytest.raises(InputError):valid_m(repo,study,b,unit='kg')

def test_superseded_record_preserves_audit_without_counting_old(repo,study):
    b=repo.add_batch(study,{'lot_code':'LAB-07','operator':'Researcher'})['batch_id']
    old=valid_m(repo,study,b,value=9)['measurement_id']
    valid_m(repo,study,b,value=3,supersedes_measurement_id=old)
    rep=repo.report(study)
    assert rep['observations_measured']==1
    assert rep['out_of_user_spec_count']==0
    assert len(repo.list_measurements(study))==2

def test_three_batches_exploratory_trend(repo,study):
    for idx,v in enumerate([3,4,5],1):
        b=repo.add_batch(study,{'lot_code':f'LAB-{idx:02}','operator':'Researcher'})['batch_id']
        valid_m(repo,study,b,value=v,evidence_uri=f'labbook://study1/{idx}')
    rep=repo.report(study)
    trend=[t for t in rep['metric_trends'] if t['metric_code']=='HARDNESS' and t['day']==0][0]
    assert trend['independent_batches']==3 and trend['eligible_for_exploratory_trend']
    assert trend['mean_of_batch_means']==4
    assert rep['approved_for_manufacturing'] is False

def test_api_v45_roundtrip(tmp_path,monkeypatch):
    monkeypatch.setenv('V45_DB_PATH',str(tmp_path/'api.sqlite3'))
    client=TestClient(app)
    assert client.get('/health/v4.5').json()['ok']
    assert client.get('/health/v4.4').status_code==200
    resp=client.post('/api/v4.5/studies',json=load('lip_balm_study_v45.json'))
    assert resp.status_code==200,resp.text
    study_id=resp.json()['study_id']
    batch=client.post(f'/api/v4.5/studies/{study_id}/batches',json={'lot_code':'LAB-A','operator':'Lab Team'})
    assert batch.status_code==200
    measure=client.post(f'/api/v4.5/studies/{study_id}/measurements',json={'batch_id':batch.json()['batch_id'],
       'metric_code':'HARDNESS','day':0,'value':3.5,'method':'SOP-12','instrument_id':'INSTR-12',
       'operator':'Researcher A','evidence_uri':'labbook://lab/doc1','unit':'N'})
    assert measure.status_code==200,measure.text
    assessment=client.get(f'/api/v4.5/studies/{study_id}/assessment')
    assert assessment.status_code==200 and assessment.json()['completed_slots']==1
    assert client.get('/api/v4.5/studies').json()[0]['id']==study_id

def test_study_invalid_base_scenario(repo):
    body=load('lip_balm_study_v45.json')
    body['scenario']['items'][0]['percent_bounds']={'min':101,'max':110}
    with pytest.raises(InputError):repo.create_study(body)

def test_complete_measurement_is_only_ready_for_review(repo,study):
    b=repo.add_batch(study,{'lot_code':'LAB-FULL','operator':'Researcher'})['batch_id']
    specs=repo.get_study(study)['protocol']['metrics']
    counter=0
    for spec in specs:
        for day in spec['timepoints_days']:
            counter+=1
            is_numeric=spec['kind']=='numeric'
            value={'HARDNESS':4.1,'SOFTENING_TEMP':50.0}.get(spec['code'], 'Đồng nhất')
            repo.add_measurement(study,{'batch_id':b,'metric_code':spec['code'],'day':day,
                'value':value,'unit':spec['unit'],'method':f'LAB-SOP-{counter}',
                'instrument_id':'TEXTURE' if is_numeric else 'VISUAL','operator':'Researcher',
                'evidence_uri':f'labbook://full/{counter}'})
    report=repo.report(study)
    assert report['completed_slots']==report['required_slots']==8
    assert report['status']=='READY_FOR_RND_REVIEW'
    assert report['approved_for_manufacturing'] is False
    assert report['stability_confirmation']=='NOT_ESTABLISHED'


def test_missing_user_spec_never_passes(repo):
    body=load('lip_balm_study_v45.json')
    body['protocol']['metrics']=[{'code':'pH','unit':'pH','timepoints_days':[0]}]
    sid=repo.create_study(body)['study_id']
    b=repo.add_batch(sid,{'lot_code':'NSPEC','operator':'Researcher'})['batch_id']
    repo.add_measurement(sid,{'batch_id':b,'metric_code':'PH','day':0,'value':4,
       'unit':'pH','operator':'Researcher','method':'pH meter','instrument_id':'PH-01',
       'evidence_uri':'labbook://evidence/one'})
    report=repo.report(sid)
    assert report['status']=='NEEDS_SPECIFICATION'
    assert report['not_interpretable_count']==1


def test_demo_cannot_supersede_real_evidence(repo,study):
    b=repo.add_batch(study,{'lot_code':'LAB-08','operator':'Researcher'})['batch_id']
    original=valid_m(repo,study,b)['measurement_id']
    with pytest.raises(InputError):valid_m(repo,study,b,
        data_kind='DEMO_SYNTHETIC',evidence_uri='demo:placeholder',supersedes_measurement_id=original)


def test_doe_candidate_has_auditable_hash():
    result=build_doe(load('lip_balm_doe_v45.json'),Catalog())
    assert all(len(x['candidate_scenario_sha256'])==64 for x in result['results'] if x['status']=='FEASIBLE')


def test_api_rejects_measurement_without_lab_evidence(tmp_path,monkeypatch):
    monkeypatch.setenv('V45_DB_PATH',str(tmp_path/'blocked.sqlite3'))
    client=TestClient(app)
    sid=client.post('/api/v4.5/studies',json=load('lip_balm_study_v45.json')).json()['study_id']
    bid=client.post(f'/api/v4.5/studies/{sid}/batches',json={'lot_code':'M-01','operator':'Researcher'}).json()['batch_id']
    r=client.post(f'/api/v4.5/studies/{sid}/measurements',json={'batch_id':bid,'metric_code':'HARDNESS','day':0,
        'value':3,'unit':'N','method':'SOP','instrument_id':'T-1','operator':'Researcher','evidence_uri':''})
    assert r.status_code==422
