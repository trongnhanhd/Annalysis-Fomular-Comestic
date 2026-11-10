"""V4.5.2 form preview & evidence flow: no fabricated data, no false sign-off."""
from __future__ import annotations
import json
from pathlib import Path
from fastapi.testclient import TestClient
from api_v45 import app

ROOT=Path(__file__).parent

def sample(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))


def test_v452_review_draft_lip_and_unresolved_premix():
    client=TestClient(app)
    scenario=sample('examples/lip_balm_optimizer_v44.json')
    r=client.post('/api/v4.5/review-draft',json={'scenario':scenario})
    assert r.status_code==200,r.text
    data=r.json()
    assert data['status']=='FEASIBLE'
    assert data['raw_material_total_percent']==100
    assert 'base_premix' in data['unresolved_grade_item_ids']
    assert data['approved_for_manufacturing'] is False
    assert data['stability_confirmation']=='NOT_ESTABLISHED'
    assert data['regulatory_status']=='NOT_ASSESSED'


def test_v452_review_pad_does_not_choose_claim_interpretation():
    scenario=sample('frontend/app/experiments/sample_pad.json')
    r=TestClient(app).post('/api/v4.5/review-draft',json={'scenario':scenario})
    assert r.status_code==200,r.text
    assert r.json()['status']=='REQUIRES_CLAIM_RESOLUTION'
    assert 'Claim' in ' '.join(r.json()['notes'])


def test_v452_invalid_draft_is_rejected():
    r=TestClient(app).post('/api/v4.5/review-draft',json={'scenario':{'items':'abc'}})
    assert r.status_code==422


def test_v452_draft_no_storage_side_effect(tmp_path,monkeypatch):
    monkeypatch.delenv('V45_DATABASE_URL',raising=False)
    monkeypatch.setenv('V45_DB_PATH',str(tmp_path/'draft.sqlite'))
    client=TestClient(app)
    assert client.get('/api/v4.5/studies').json()==[]
    scenario=sample('examples/lip_balm_optimizer_v44.json')
    assert client.post('/api/v4.5/review-draft',json={'scenario':scenario}).status_code==200
    assert client.get('/api/v4.5/studies').json()==[]


def test_v452_study_create_and_measurement_reopen(tmp_path,monkeypatch):
    monkeypatch.delenv('V45_DATABASE_URL',raising=False)
    monkeypatch.setenv('V45_DB_PATH',str(tmp_path/'measure.sqlite'))
    client=TestClient(app)
    data=sample('examples/lip_balm_study_v45.json')
    created=client.post('/api/v4.5/studies',json=data)
    assert created.status_code==200,created.text
    id=created.json()['study_id']
    batch=client.post(f'/api/v4.5/studies/{id}/batches',json={'lot_code':'V452-01','operator':'RD-LAB'})
    assert batch.status_code==200,batch.text
    bid=batch.json()['batch_id']
    measurement={'batch_id':bid,'metric_code':'HARDNESS','day':0,'value':4.2,'unit':'N',
                'method':'SOP-RD','instrument_id':'TESTER-01','operator':'RD-LAB',
                'data_kind':'MEASURED'}
    bad=client.post(f'/api/v4.5/studies/{id}/measurements',json=measurement)
    assert bad.status_code==422,'Must reject measured data without evidence URI'
    good=client.post(f'/api/v4.5/studies/{id}/measurements',json={**measurement,'evidence_uri':'labbook://V452-01/HARDNESS-D0'})
    assert good.status_code==200,good.text
    record=client.get(f'/api/v4.5/studies/{id}').json()
    assert record['scenario']==data['scenario']
    report=client.get(f'/api/v4.5/studies/{id}/assessment').json()
    assert report['completed_slots']==1
    assert report['approved_for_manufacturing'] is False
