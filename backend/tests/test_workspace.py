"""API contract and evidence integrity tests. Uses isolated SQLite, not production DB."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
from workspace_db import Base, get_db

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('WORKSPACE_API_KEY', 'test-secret')
    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    make = sessionmaker(bind=engine, expire_on_commit=False)
    def db_override():
        with make() as sess: yield sess
    app.dependency_overrides[get_db] = db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()

def test_protected_workspace(client):
    assert client.get('/api/workspace/products').status_code == 401
    assert client.get('/api/workspace/products',headers={'x-api-key':'wrong'}).status_code == 401
    assert client.get('/api/workspace/products',headers={'x-api-key':'test-secret'}).status_code == 200

def headers(): return {'x-api-key':'test-secret'}

def product(client):
    r=client.post('/api/workspace/products', headers=headers(), json={'name':'Serum niacinamide','brand':'Mẫu R&D','market':'EU','inci':'Aqua, Glycerin, Niacinamide, Phenoxyethanol'})
    assert r.status_code==201, r.text
    return r.json()

def test_product_analysis_and_snapshot(client):
    p=product(client)
    run=client.post(f"/api/workspace/products/{p['id']}/analyses",headers=headers(), json={'market':'CN','inci':'WRONG', 'known_pct':{'Niacinamide':{'value':5,'source':'Công bố công thức gốc'}}})
    assert run.status_code==201, run.text
    data=run.json()
    assert data['result']['status']=='feasible'
    assert data['input']['inci']==p['inci']
    assert data['input']['market']=='EU'
    ni=next(x for x in data['result']['results'] if x['ingredient']=='Niacinamide')
    assert ni['min_pct']==ni['max_pct']==5
    assert ni['estimated_pct'] is None
    assert len(client.get(f"/api/workspace/products/{p['id']}/analyses",headers=headers()).json()['data'])==1
    got=client.get(f"/api/workspace/analyses/{data['id']}",headers=headers()).json()
    assert got['result']['catalog_versions']==data['result']['catalog_versions']

def test_research_draft_not_used_as_scientific_constraint(client):
    r=client.post('/api/workspace/research',headers=headers(),json={'inci':'Niacinamide','title':'Tài liệu chưa kiểm chứng','study_type':'clinical','source_url':'https://example.org/unverified','min_pct':50,'max_pct':50})
    assert r.status_code==201, r.text
    rec=r.json(); assert rec['review_status']=='draft'
    a=client.post('/api/v2/analyze',json={'market':'EU','inci':'Aqua, Niacinamide'})
    assert a.status_code==200
    ni=next(x for x in a.json()['results'] if x['ingredient']=='Niacinamide')
    assert ni['max_pct']==50 and ni['min_pct']<1
    assert all(x.get('source_url')!='https://example.org/unverified' for x in ni['research_evidence'])
    review=client.post(f"/api/workspace/research/{rec['id']}/review",headers=headers(),json={'decision':'reviewed','reviewer':'Kỹ thuật viên','review_note':'Chỉ kiểm chứng tham chiếu; không đưa vào LP'})
    assert review.status_code==200
    assert client.post(f"/api/workspace/research/{rec['id']}/review",headers=headers(),json={'decision':'reviewed','reviewer':'Khác','review_note':'test lại'}).status_code==409
    b=client.post('/api/v2/analyze',json={'market':'EU','inci':'Aqua, Niacinamide'}).json()
    ni2=next(x for x in b['results'] if x['ingredient']=='Niacinamide')
    assert all(x.get('source_url')!='https://example.org/unverified' for x in ni2['research_evidence'])

def test_formula_hypothesis_versions_and_sum(client):
    p=product(client)
    endpoint=f"/api/workspace/products/{p['id']}/formulas"
    f={'name':'Bản thử 01','ingredients':[{'inci':'Aqua','pct':95},{'inci':'Niacinamide','pct':5}]}
    assert client.post(endpoint,headers=headers(),json={**f,'ingredients':[{'inci':'Aqua','pct':90}]}).status_code==422
    one=client.post(endpoint,headers=headers(),json=f)
    assert one.status_code==201 and one.json()['version']==1 and one.json()['status']=='hypothesis'
    two=client.post(endpoint,headers=headers(),json=f)
    assert two.status_code==201 and two.json()['version']==2
    assert len(client.get(endpoint,headers=headers()).json()['data'])==2

def test_invalid_input(client):
    assert client.post('/api/workspace/products',headers=headers(),json={'name':'X','inci':'Aqua,Aqua'}).status_code==422
    assert client.get('/api/workspace/products/missing',headers=headers()).status_code==404
    assert client.post('/api/workspace/research',headers=headers(),json={'inci':'Aqua','title':'Test','source_url':'not-url'}).status_code==422
