"""Real API SQLite smoke, preservation of V4.3/4.4, and config contract."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from api_v45 import app
from storage_factory_v451 import open_repository

ROOT=Path(__file__).resolve().parent


def _sample(name):
    return json.loads((ROOT/'examples'/name).read_text(encoding='utf-8'))


def test_v451_full_http_workflow(tmp_path, monkeypatch):
    monkeypatch.delenv('V45_DATABASE_URL', raising=False)
    monkeypatch.setenv('V45_DB_PATH', str(tmp_path/'v451.sqlite3'))
    client=TestClient(app)
    health=client.get('/health/v4.5')
    assert health.status_code==200 and health.json()['storage']=='sqlite_demo'
    assert client.get('/api/v4.5/studies').json()==[]
    doe=client.post('/api/v4.5/design-experiments', json=_sample('lip_balm_doe_v45.json'))
    assert doe.status_code==200,doe.text
    assert doe.json()['feasible_count']>=1
    payload=_sample('lip_balm_study_v45.json')
    created=client.post('/api/v4.5/studies',json=payload)
    assert created.status_code==200,created.text
    study_id=created.json()['study_id']
    assert created.json()['approved_for_manufacturing'] is False
    assert len(client.get('/api/v4.5/studies').json())==1
    record=client.get(f'/api/v4.5/studies/{study_id}')
    assert record.status_code==200 and record.json()['formula_sha256']==created.json()['formula_sha256']
    new_batch=client.post(f'/api/v4.5/studies/{study_id}/batches',json={'lot_code':'LAB-001','operator':'R&D 01'})
    assert new_batch.status_code==200,new_batch.text
    batch_id=new_batch.json()['batch_id']
    measure={'batch_id':batch_id,'metric_code':'HARDNESS','day':0,'value':4.2,'unit':'N',
             'method':'LAB-HARD-01','instrument_id':'INSTR-01','operator':'R&D 01'}
    demo=client.post(f'/api/v4.5/studies/{study_id}/measurements',json={**measure,'data_kind':'DEMO_SYNTHETIC'})
    assert demo.status_code==200,demo.text
    report=client.get(f'/api/v4.5/studies/{study_id}/assessment')
    assert report.json()['observations_measured']==0
    assert report.json()['observations_demo_excluded']==1
    measured=client.post(f'/api/v4.5/studies/{study_id}/measurements',json={**measure,'data_kind':'MEASURED','evidence_uri':'labbook://LAB-001/HARDNESS-D0'})
    assert measured.status_code==200,measured.text
    report=client.get(f'/api/v4.5/studies/{study_id}/assessment')
    assert report.status_code==200 and report.json()['observations_measured']==1
    assert report.json()['approved_for_manufacturing'] is False
    assert report.json()['status']!='READY_FOR_RND_REVIEW'
    assert len(client.get(f'/api/v4.5/studies/{study_id}/batches').json())==1
    assert len(client.get(f'/api/v4.5/studies/{study_id}/measurements').json())==2


def test_v451_rejects_unsupported_database_urls(monkeypatch):
    monkeypatch.setenv('V45_DATABASE_URL','sqlite:///unexpected.db')
    try:
        open_repository()
    except RuntimeError as exc:
        assert 'PostgreSQL' in str(exc)
    else:
        raise AssertionError('Unexpected database type accepted')


def test_v451_frontend_proxy_and_migration():
    path=ROOT/'frontend'/'next.config.ts'
    text=path.read_text(encoding='utf-8')
    assert '/backend/:path*' in text
    assert 'RND_API_INTERNAL_URL' in text
    for page in ('page.tsx','optimizer/page.tsx','experiments/page.tsx'):
        s=(ROOT/'frontend'/'app'/page).read_text(encoding='utf-8')
        assert 'const API="/backend";' in s or "const BASE_URL = '/backend';" in s or 'const API = "/backend";' in s
        assert 'NEXT_PUBLIC_API_BASE_URL' not in s
    migration=(ROOT/'migrations'/'001_v451_init.sql').read_text(encoding='utf-8')
    assert 'CREATE TABLE IF NOT EXISTS rnd_v451_studies' in migration
    assert 'rnd_v451_measurements_immutable' in migration
    assert 'supersedes_measurement_id TEXT UNIQUE' in migration


def test_v451_legacy_optimizer_api():
    client=TestClient(app)
    response=client.post('/api/v4.4/optimize',json=_sample('lip_balm_optimizer_v44.json'))
    assert response.status_code==200,response.text
    assert response.json()['status']=='FEASIBLE'
