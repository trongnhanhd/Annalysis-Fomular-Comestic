"""PostgreSQL implementation of the V4.5 repository contract.

Requires: SQLAlchemy + psycopg3, plus migration 001_v451_init.sql.
This is a single-tenant R&D research prototype: no authentication or tenant isolation.
"""
from __future__ import annotations
import json
from datetime import datetime
from functools import lru_cache
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from experimental_repository_v45 import Repository, utcnow
from experimental_validation_v45 import verify_protocol, finite_float, canonical_hash, evaluate_study
from optimizer_v44 import InputError, solve_scenario
from formula_group_service import Catalog
from batch_provenance_v452 import freeze_candidates,verify_batch_provenance,apply_traceability_gate


def _dt(value):
    return value.isoformat() if isinstance(value, datetime) else str(value)

@lru_cache(maxsize=2)
def _engine(url):
    conn_url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return create_engine(conn_url, pool_pre_ping=True, pool_size=5, max_overflow=5)

class PostgresRepository:
    def __init__(self, url):
        self.engine = _engine(url)

    def ping(self):
        with self.engine.connect() as conn:
            return all(conn.execute(text('SELECT to_regclass(:name)'),{'name':name}).scalar_one() is not None
                       for name in ('public.rnd_v451_studies','public.rnd_v452_candidates','public.rnd_v452_batch_provenance'))

    def create_study(self, body):
        protocol = verify_protocol(body.get('protocol', {}))
        scenario = body.get('scenario')
        if not isinstance(scenario, dict) or not isinstance(scenario.get('items'), list):
            raise InputError('Thiếu snapshot scenario.items')
        if scenario.get('ambiguous_claims'):
            raise InputError('Chọn một cách hiểu claim trước khi khóa công thức thử nghiệm')
        optimized = solve_scenario(scenario, Catalog() if scenario.get('product_id') is not None else None)
        if optimized.get('status') != 'FEASIBLE':
            raise InputError('Công thức không có nghiệm khả thi theo bộ giải V4.4')
        title = str(body.get('title', '')).strip()
        creator = str(body.get('created_by', '')).strip()
        if not title or not creator:
            raise InputError('Thiếu title/created_by')
        candidates=freeze_candidates(scenario,body.get('doe_design'))
        study_id = Repository._id('STUDY')
        sha = canonical_hash(scenario)
        with self.engine.begin() as conn:
            conn.execute(text('''INSERT INTO rnd_v451_studies
              (id,title,created_by,product_type,formula_sha256,scenario,protocol)
              VALUES (:id,:title,:creator,:product,:sha,CAST(:scenario AS JSONB),CAST(:protocol AS JSONB))'''),
              dict(id=study_id,title=title,creator=creator,product=str(scenario.get('product_type') or 'unknown'),
                   sha=sha,scenario=json.dumps(scenario,ensure_ascii=False),protocol=json.dumps(protocol,ensure_ascii=False)))
            for point in candidates:
                conn.execute(text('''INSERT INTO rnd_v452_candidates
                   (study_id,candidate_id,candidate_sha256,composition,design)
                   VALUES (:study,:candidate,:sha,CAST(:composition AS JSONB),CAST(:design AS JSONB))'''),
                   dict(study=study_id,candidate=point['candidate_id'],sha=point['candidate_sha256'],
                        composition=json.dumps(point['composition_percent'],sort_keys=True),
                        design=json.dumps(point['design'],ensure_ascii=False,sort_keys=True)))
        return dict(study_id=study_id,formula_sha256=sha,protocol=protocol,created_at=utcnow(),
                    data_status='PROTOCOL_CREATED_NOT_TESTED',approved_for_manufacturing=False)

    def get_study(self, study_id):
        with self.engine.connect() as conn:
            row=conn.execute(text('SELECT * FROM rnd_v451_studies WHERE id=:id'),{'id':study_id}).mappings().first()
        if row is None:
            raise InputError('Không tìm thấy nghiên cứu')
        out=dict(row)
        out['scenario']=out.pop('scenario')
        out['protocol']=out.pop('protocol')
        out['created_at']=_dt(out['created_at'])
        return out

    def list_candidates(self, study_id):
        self.get_study(study_id)
        with self.engine.connect() as conn:
            rows=conn.execute(text('''SELECT candidate_id,candidate_sha256,composition,design
                FROM rnd_v452_candidates WHERE study_id=:study ORDER BY candidate_id'''),
                {'study':study_id}).mappings().all()
        return [dict(candidate_id=r['candidate_id'],candidate_sha256=r['candidate_sha256'],
                     composition_percent=r['composition'],design=r['design']) for r in rows]

    def list_studies(self):
        with self.engine.connect() as conn:
            rows=conn.execute(text('''SELECT id,title,product_type,formula_sha256,created_at
                                      FROM rnd_v451_studies ORDER BY created_at DESC,id DESC LIMIT 100''')).mappings().all()
        return [{**dict(r),'created_at':_dt(r['created_at'])} for r in rows]

    def add_batch(self, study_id, body):
        self.get_study(study_id)
        lot = str(body.get('lot_code','')).strip()
        operator = str(body.get('operator','')).strip()
        if not lot or not operator:
            raise InputError('Thiếu lot_code/operator')
        when = str(body.get('prepared_at') or utcnow())
        try:
            prepared = datetime.fromisoformat(when.replace('Z','+00:00'))
            if prepared.tzinfo is None: raise ValueError()
        except ValueError as exc:
            raise InputError('prepared_at phải là thời gian ISO 8601 có múi giờ') from exc
        batch_id=Repository._id('BATCH')
        provenance=None
        if body.get('candidate_id') is not None:
            point=next((x for x in self.list_candidates(study_id) if x['candidate_id']==body['candidate_id']),None)
            if point is None:raise InputError('Phương án DoE không thuộc nghiên cứu')
            provenance=verify_batch_provenance(point,body)
        try:
            with self.engine.begin() as conn:
                conn.execute(text('''INSERT INTO rnd_v451_batches (id,study_id,lot_code,operator,prepared_at)
                  VALUES (:id,:study,:lot,:operator,:prepared)'''),
                  dict(id=batch_id,study=study_id,lot=lot,operator=operator,prepared=prepared))
                if provenance:
                    conn.execute(text('''INSERT INTO rnd_v452_batch_provenance
                      (batch_id,study_id,candidate_id,candidate_sha256,actual_weights,raw_material_lots,
                       process,weighed_by,deviation_max_pp,traceability_status)
                      VALUES (:batch,:study,:candidate,:sha,CAST(:weights AS JSONB),CAST(:lots AS JSONB),
                              CAST(:process AS JSONB),:weighed,:deviation,:status)'''),
                      dict(batch=batch_id,study=study_id,candidate=provenance['candidate_id'],
                           sha=provenance['candidate_sha256'],weights=json.dumps(provenance['actual_weights_g']),
                           lots=json.dumps(provenance['raw_material_lots']),process=json.dumps(provenance['process']),
                           weighed=provenance['weighed_by'],deviation=provenance['deviation_max_pp'],
                           status=provenance['traceability_status']))
        except IntegrityError as exc:
            raise InputError('Mã mẻ đã tồn tại trong nghiên cứu') from exc
        return dict(batch_id=batch_id,study_id=study_id,lot_code=lot,prepared_at=when,
                    traceability_status=provenance['traceability_status'] if provenance else 'UNLINKED_LEGACY')

    def list_batches(self, study_id):
        self.get_study(study_id)
        with self.engine.connect() as conn:
            rows=conn.execute(text('''SELECT b.*,p.candidate_id,p.candidate_sha256,p.traceability_status,
                    p.actual_weights,p.raw_material_lots,p.process,p.weighed_by,p.deviation_max_pp
                    FROM rnd_v451_batches b LEFT JOIN rnd_v452_batch_provenance p ON p.batch_id=b.id
                    WHERE b.study_id=:study ORDER BY b.created_at,b.id'''),
                              {'study':study_id}).mappings().all()
        return [{**dict(r),'prepared_at':_dt(r['prepared_at']),'created_at':_dt(r['created_at']),
                 'traceability_status':r['traceability_status'] or 'UNLINKED_LEGACY',
                 'actual_weights_g':r['actual_weights'],'raw_material_lots':r['raw_material_lots'],
                 'process':r['process'],'weighed_by':r['weighed_by'],'deviation_max_pp':r['deviation_max_pp']} for r in rows]

    def add_measurement(self, study_id, body):
        study=self.get_study(study_id)
        batch_id=str(body.get('batch_id','')).strip()
        metric_code=str(body.get('metric_code','')).strip().upper()
        spec={x['code']:x for x in study['protocol']['metrics']}.get(metric_code)
        if not spec:raise InputError('Chỉ tiêu không tồn tại trong protocol')
        day=body.get('day',0)
        if type(day) != int or day not in spec['timepoints_days']:
            raise InputError('Ngày đo không thuộc protocol')
        operator=str(body.get('operator','')).strip()
        method=str(body.get('method','')).strip()
        instrument=str(body.get('instrument_id','')).strip()
        evidence_uri=str(body.get('evidence_uri','')).strip()
        if not all((operator,method,instrument)):
            raise InputError('Bắt buộc có operator, method, instrument_id')
        kind=body.get('data_kind','MEASURED')
        if kind not in ('MEASURED','DEMO_SYNTHETIC'):
            raise InputError('data_kind không hợp lệ')
        if kind=='MEASURED' and (not evidence_uri or evidence_uri.startswith(('demo:','synthetic:'))):
            raise InputError('Dữ liệu đo thực tế cần evidence_uri không phải DEMO')
        unit=str(body.get('unit',spec['unit']))
        if unit != spec['unit']:
            raise InputError('Đơn vị không khớp protocol')
        if spec['kind']=='numeric':
            numeric=finite_float(body.get('value'),'measurement.value')
            value_text=None
        else:
            numeric=None
            value_text=str(body.get('value','')).strip()
            if not value_text:raise InputError('Giá trị nhận xét rỗng')
        supersedes=body.get('supersedes_measurement_id')
        obs_id=Repository._id('OBS')
        try:
            with self.engine.begin() as conn:
                batch=conn.execute(text('SELECT 1 FROM rnd_v451_batches WHERE id=:id AND study_id=:study'),
                                   {'id':batch_id,'study':study_id}).first()
                if not batch:raise InputError('Mẻ không thuộc nghiên cứu')
                if supersedes:
                    old=conn.execute(text('''SELECT * FROM rnd_v451_measurements
                         WHERE id=:id AND study_id=:study FOR UPDATE'''),
                         {'id':supersedes,'study':study_id}).mappings().first()
                    if not old or (old['batch_id'],old['metric_code'],old['day'],old['data_kind'])!=(batch_id,metric_code,day,kind):
                        raise InputError('Bản chỉnh sửa phải cùng mẻ/chỉ tiêu/thời điểm')
                    replaced=conn.execute(text('SELECT 1 FROM rnd_v451_measurements WHERE supersedes_measurement_id=:id'),
                                          {'id':supersedes}).first()
                    if replaced:raise InputError('Quan sát đã được thay thế')
                conn.execute(text('''INSERT INTO rnd_v451_measurements
                      (id,study_id,batch_id,metric_code,day,value_numeric,value_text,unit,method,instrument_id,
                       operator,evidence_uri,data_kind,supersedes_measurement_id)
                      VALUES (:id,:study,:batch,:metric,:day,:numeric,:txt,:unit,:method,:instrument,
                              :operator,:evidence,:kind,:supersedes)'''),
                      dict(id=obs_id,study=study_id,batch=batch_id,metric=metric_code,day=day,numeric=numeric,txt=value_text,
                           unit=unit,method=method,instrument=instrument,operator=operator,evidence=evidence_uri,
                           kind=kind,supersedes=supersedes))
        except IntegrityError as exc:
            raise InputError('Quan sát chỉnh sửa đã tồn tại hoặc vi phạm ràng buộc') from exc
        return dict(measurement_id=obs_id,classification='RECORDED_APPEND_ONLY',data_kind=kind,
                    included_in_evidence=kind=='MEASURED')

    def list_measurements(self, study_id):
        self.get_study(study_id)
        with self.engine.connect() as conn:
            rows=conn.execute(text('''SELECT * FROM rnd_v451_measurements
                                       WHERE study_id=:study ORDER BY recorded_at,id'''),
                              {'study':study_id}).mappings().all()
        return [{**dict(r),'recorded_at':_dt(r['recorded_at'])} for r in rows]

    def report(self, study_id):
        batches=self.list_batches(study_id)
        return apply_traceability_gate(evaluate_study(self.get_study(study_id),batches,self.list_measurements(study_id)),batches)
