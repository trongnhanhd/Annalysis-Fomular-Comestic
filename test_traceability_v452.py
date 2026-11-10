"""P0 DoE -> study -> candidate -> weighing lot -> measurement lineage."""
import json
import sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from experimental_repository_v45 import Repository
from optimizer_v44 import InputError
from api_v45 import app

ROOT=Path(__file__).parent

def load(filename):
    return json.loads((ROOT/'examples'/filename).read_text(encoding='utf-8'))

def provenance(candidate,scale=1.0):
    return {
      'candidate_id':candidate['candidate_id'],
      'actual_weights_g':{k:round(v*scale,5) for k,v in candidate['composition_percent'].items()},
      'raw_material_lots':{k:'LOT-CHECK-'+k for k in candidate['composition_percent']},
      'process':{'procedure_ref':'SOP-DEMO-01','operator_note':'không phải số đo thực tế'},
      'weighed_by':'researcher-001'
    }

def test_baseline_candidate_is_frozen_and_retrievable(tmp_path):
    repo=Repository(str(tmp_path/'test.db'))
    body=load('lip_balm_study_v45.json')
    st=repo.create_study(body)['study_id']
    candidates=repo.list_candidates(st)
    assert len(candidates)==1 and candidates[0]['candidate_id']=='BASELINE'
    assert abs(sum(candidates[0]['composition_percent'].values())-100)<1e-6
    assert len(candidates[0]['candidate_sha256'])==64
    assert repo.report(st)['traceability']['total_batches']==0
    with repo._conn() as c:
        with pytest.raises(sqlite3.DatabaseError):
            c.execute("UPDATE doe_candidates SET candidate_id='X' WHERE study_id=?",(st,))

def test_doe_candidates_are_stored_against_original_study_snapshot(tmp_path):
    repo=Repository(str(tmp_path/'test.db'))
    body=load('lip_balm_study_v45.json')
    design=load('lip_balm_doe_v45.json')
    design['scenario']=json.loads(json.dumps(body['scenario']))
    body['doe_design']=design
    st=repo.create_study(body)['study_id']
    candidates=repo.list_candidates(st)
    assert len(candidates)==5
    assert {x['candidate_id'] for x in candidates}=={'DOE-001','DOE-002','DOE-003','DOE-004','DOE-005'}
    for x in candidates:
        assert abs(sum(x['composition_percent'].values())-100)<1e-5
    body['doe_design']['scenario']['title']='tampered different snapshot'
    with pytest.raises(InputError,match='snapshot'):
        repo.create_study(body)

def test_batch_weighing_provenance_is_immutable(tmp_path):
    repo=Repository(str(tmp_path/'test.db'))
    st=repo.create_study(load('lip_balm_study_v45.json'))['study_id']
    candidate=repo.list_candidates(st)[0]
    batch=repo.add_batch(st,{'lot_code':'RND-01','operator':'researcher',**provenance(candidate)})
    assert batch['traceability_status']=='LINKED_MATCHED'
    stored=repo.list_batches(st)[0]
    assert stored['candidate_id']=='BASELINE'
    assert stored['candidate_sha256']==candidate['candidate_sha256']
    assert stored['actual_weights_g']==provenance(candidate)['actual_weights_g']
    assert repo.report(st)['traceability']['all_batches_linked'] is True
    with repo._conn() as c:
        with pytest.raises(sqlite3.DatabaseError):
            c.execute('DELETE FROM batch_provenance WHERE batch_id=?',(batch['batch_id'],))

def test_batch_rejects_unmatched_candidate_lot_or_weight(tmp_path):
    repo=Repository(str(tmp_path/'test.db'))
    st=repo.create_study(load('lip_balm_study_v45.json'))['study_id']
    p=provenance(repo.list_candidates(st)[0])
    with pytest.raises(InputError):
        repo.add_batch(st,{'lot_code':'X','operator':'A','candidate_id':'DOE-999',**{k:v for k,v in p.items() if k!='candidate_id'}})
    p['actual_weights_g'].pop('beeswax')
    with pytest.raises(InputError,match='item_id'):
        repo.add_batch(st,{'lot_code':'X','operator':'A',**p})
    assert repo.list_batches(st)==[]

def test_legacy_batch_is_marked_unlinked(tmp_path):
    repo=Repository(str(tmp_path/'test.db'))
    st=repo.create_study(load('lip_balm_study_v45.json'))['study_id']
    b=repo.add_batch(st,{'lot_code':'OLD','operator':'Researcher'})
    assert b['traceability_status']=='UNLINKED_LEGACY'
    r=repo.report(st)
    assert r['traceability']['unlinked_batch_ids']==[b['batch_id']]
    assert r['traceability']['review_readiness']=='INCOMPLETE'
    assert r['eligible_for_model_training'] is False

def test_api_roundtrip_candidates_and_batches(tmp_path,monkeypatch):
    monkeypatch.setenv('V45_DB_PATH',str(tmp_path/'test.db'))
    c=TestClient(app)
    body=load('lip_balm_study_v45.json');body['doe_design']=load('lip_balm_doe_v45.json');body['doe_design']['scenario']=json.loads(json.dumps(body['scenario']))
    response=c.post('/api/v4.5/studies',json=body)
    assert response.status_code==200,response.text
    st=response.json()['study_id']
    candidates=c.get(f'/api/v4.5/studies/{st}/candidates')
    assert candidates.status_code==200
    assert len(candidates.json())==5
    candidate=candidates.json()[1]
    response=c.post(f'/api/v4.5/studies/{st}/batches',json={'lot_code':'RND-02','operator':'A',**provenance(candidate)})
    assert response.status_code==200,response.text
    result=c.get(f'/api/v4.5/studies/{st}/batches').json()
    assert result[0]['candidate_id']==candidate['candidate_id']
    assert c.get(f'/api/v4.5/studies/{st}/assessment').json()['traceability']['all_batches_linked']

def test_traceability_deviation_is_flagged_not_silently_approved(tmp_path):
    repo=Repository(str(tmp_path/'test.db'))
    st=repo.create_study(load('lip_balm_study_v45.json'))['study_id']
    candidate=repo.list_candidates(st)[0]
    p=provenance(candidate)
    p['actual_weights_g']['beeswax']+=6.5
    record=repo.add_batch(st,{'lot_code':'DEVIATION-1','operator':'Researcher',**p})
    assert record['traceability_status']=='LINKED_DEVIATED'
    report=repo.report(st)
    assert report['traceability']['deviated_batch_ids']==[record['batch_id']]
    assert report['traceability']['review_readiness']=='DEVIATION_REVIEW_REQUIRED'
    assert report['approved_for_manufacturing'] is False


def test_openapi_has_no_duplicate_endpoints():
    from collections import Counter
    from api_v45 import app
    counts=Counter((r.path,','.join(sorted(getattr(r,'methods',[])))) for r in app.routes)
    assert all(count==1 for count in counts.values())
    spec=app.openapi()
    assert '/api/v4.5/studies/{study_id}/candidates' in spec['paths']
