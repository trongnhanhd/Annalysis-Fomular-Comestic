"""Frontend API contract smoke test without Node; keeps the original solver intact."""
from __future__ import annotations
import os,sys,tempfile
from pathlib import Path
from fastapi.testclient import TestClient
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend'))

with tempfile.TemporaryDirectory() as tmp:
    os.environ['DATABASE_URL']='sqlite:///'+str(Path(tmp)/'contract.db')
    os.environ['WORKSPACE_API_KEY']='contract-test-key'
    from main import app
    headers={'x-api-key':'contract-test-key'}
    with TestClient(app) as client:
        r=client.get('/api/v2/catalog/research')
        assert r.status_code==200
        studies=r.json()['data']
        assert len(studies)==5, 'Do not replace V2.1 scientific catalog'
        print('PASS catalog research · 5 originals')
        r=client.get('/api/v2/catalog/regulatory')
        assert r.status_code==200 and len(r.json()['data'])==1
        print('PASS catalog regulatory · 1 curated source')
        sample={'inci':'Aqua, Glycerin, Niacinamide, Panthenol, Phenoxyethanol, Ethylhexylglycerin',
          'market':'EU','product_type':'leave_on','known_pct':{'Niacinamide':{'value':5,'source':'Dữ liệu giả định kiểm thử'}}}
        r=client.post('/api/v2/analyze',json=sample)
        assert r.status_code==200 and r.json()['status']=='feasible'
        niacinamide=next(x for x in r.json()['results'] if x['ingredient']=='Niacinamide')
        assert niacinamide['min_pct']==niacinamide['max_pct']==5
        assert niacinamide['estimated_pct'] is None
        print('PASS 5% exactly disclosed · estimated_pct still null')
        r=client.post('/api/v2/analyze',json={'market':'CN','inci':'Aqua, Glycerin, Niacinamide',
            'trace_inci':'Phenoxyethanol, Ethylhexylglycerin'})
        assert r.status_code==200 and r.json()['status']=='feasible'
        assert all(x['max_pct']<=.1+1e-8 for x in r.json()['results'] if x['section']=='trace')
        print('PASS CN trace micro group ≤0.1%')
        r=client.post('/api/v2/analyze',json={'market':'VN','inci':'Aqua, Niacinamide',
            'declared_concentrations':{'Niacinamide':{'value':50000,'unit':'ppm',
             'basis':'final_product_pure_inci','precision':'exact','source':'Giả định kiểm thử'}}})
        assert r.status_code==200 and r.json()['status']=='feasible'
        nia=next(x for x in r.json()['results'] if x['ingredient']=='Niacinamide')
        assert nia['min_pct']==nia['max_pct']==5
        print('PASS conversion 50000ppm = 5%')
        r=client.get('/api/workspace/products')
        assert r.status_code==401
        r=client.get('/api/workspace/products',headers=headers)
        assert r.status_code==200
        print('PASS workspace requires API key')
print('6/6 API contract checks passed')
