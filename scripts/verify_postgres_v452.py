"""OPTIONAL disposable PostgreSQL smoke test (not run unless configured).

Requires TEST_POSTGRES_URL to a dedicated *_test database with 001 and 002 migrations
applied. Never targets an existing production database.

Install: pip install -r requirements-postgres.txt
Set TEST_POSTGRES_URL=postgresql+psycopg://user:password@localhost/formula_rd_test
Run: python scripts/verify_postgres_v452.py
"""
from __future__ import annotations
import json
import os
import sys
import uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    url=os.getenv('TEST_POSTGRES_URL','')
    if not url:
        print('SKIPPED: TEST_POSTGRES_URL chưa cấu hình; không có PostgreSQL để thử.')
        return 2
    from sqlalchemy.engine.url import make_url
    target=make_url(url)
    if not target.drivername.startswith('postgresql') or not (target.database or '').endswith('_test'):
        raise SystemExit('TỪ CHỐI: Chỉ cho phép database PostgreSQL có tên kết thúc bằng _test.')
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from experimental_repository_postgres_v451 import PostgresRepository
    repo=PostgresRepository(url)
    if not repo.ping():
        raise SystemExit('Cần cả migrations/001_v451_init.sql và 002_v452_traceability.sql trên DB thử riêng.')
    scenario=json.loads((ROOT/'examples'/'lip_balm_study_v45.json').read_text(encoding='utf-8'))
    serial=uuid.uuid4().hex[:8]
    scenario['title']=f'Test integration {serial}'
    created=repo.create_study({**scenario,'title':f'Postgres smoke {serial}','created_by':'automated_v452'})
    sid=created['study_id'];assert not created['approved_for_manufacturing']
    got=repo.get_study(sid)
    assert got['formula_sha256']==created['formula_sha256']
    candidate=repo.list_candidates(sid)[0]
    batch=repo.add_batch(sid,{'lot_code':f'PG-TEST-{serial}','operator':'automated_v452',
        'candidate_id':candidate['candidate_id'],
        'actual_weights_g':{k:float(v) for k,v in candidate['composition_percent'].items()},
        'raw_material_lots':{k:'TEST-LOT-'+k for k in candidate['composition_percent']},
        'weighed_by':'automated_v452','process':{'procedure_ref':'TEST-SOP'}})
    assert batch['traceability_status']=='LINKED_MATCHED'
    bid=batch['batch_id']
    obs=repo.add_measurement(sid,{
        'batch_id':bid,'metric_code':'HARDNESS','day':0,'value':3.2,'unit':'N',
        'method':'TEST-SOP','instrument_id':'TEST-INSTRUMENT','operator':'automated_v452',
        'evidence_uri':f'test://{serial}/hardness','data_kind':'DEMO_SYNTHETIC'})
    assert obs['data_kind']=='DEMO_SYNTHETIC'
    assert repo.report(sid)['observations_measured']==0
    assert repo.report(sid)['traceability']['all_batches_linked']
    with repo.engine.connect() as conn:
        row=conn.execute(text('SELECT candidate_sha256 FROM rnd_v452_batch_provenance WHERE batch_id=:id'),{'id':bid}).first()
        assert row[0]==candidate['candidate_sha256']
    rows=repo.list_measurements(sid); assert len(rows)==1
    try:
        with repo.engine.begin() as conn:
            conn.execute(text('UPDATE rnd_v451_measurements SET unit=:unit WHERE id=:id'),
                         {'unit':'WRONG','id':obs['measurement_id']})
    except DBAPIError:
        pass
    else:
        raise AssertionError('Append-only trigger must reject UPDATE')
    try:
        with repo.engine.begin() as conn:
            conn.execute(text('DELETE FROM rnd_v452_batch_provenance WHERE batch_id=:id'),{'id':bid})
    except DBAPIError:pass
    else:raise AssertionError('Traceability append-only trigger must reject DELETE')
    print(f'PASS PostgreSQL: study={sid}, candidate={candidate["candidate_id"]}, batch={bid}, append-only triggers verified.')
    print('Lưu ý: bản ghi DEMO thử nghiệm còn trong database *_test; không xóa dữ liệu tự động.')
    return 0

if __name__=='__main__':sys.exit(main())
