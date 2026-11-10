"""Append-only, local SQLite demo storage. PostgreSQL migration blueprint shipped separately."""
from __future__ import annotations
import json, os, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from optimizer_v44 import InputError, solve_scenario
from formula_group_service import Catalog
from experimental_validation_v45 import verify_protocol, finite_float, canonical_hash, evaluate_study
from batch_provenance_v452 import freeze_candidates as _freeze_candidates, verify_batch_provenance as _verify_batch_provenance, apply_traceability_gate as _apply_traceability_gate


def utcnow():return datetime.now(timezone.utc).isoformat(timespec='seconds')

SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS studies (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, created_by TEXT NOT NULL,
  product_type TEXT NOT NULL, formula_sha256 TEXT NOT NULL,
  scenario_json TEXT NOT NULL, protocol_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS batches (
  id TEXT PRIMARY KEY, study_id TEXT NOT NULL REFERENCES studies(id), lot_code TEXT NOT NULL,
  operator TEXT NOT NULL, prepared_at TEXT NOT NULL, created_at TEXT NOT NULL,
  UNIQUE(study_id,lot_code)
);
CREATE TABLE IF NOT EXISTS measurements (
  id TEXT PRIMARY KEY, study_id TEXT NOT NULL REFERENCES studies(id),
  batch_id TEXT NOT NULL REFERENCES batches(id), metric_code TEXT NOT NULL, day INTEGER NOT NULL,
  value_numeric REAL, value_text TEXT, unit TEXT NOT NULL, method TEXT NOT NULL,
  instrument_id TEXT NOT NULL, operator TEXT NOT NULL, evidence_uri TEXT NOT NULL,
  data_kind TEXT NOT NULL CHECK(data_kind IN ('MEASURED','DEMO_SYNTHETIC')),
  supersedes_measurement_id TEXT REFERENCES measurements(id), recorded_at TEXT NOT NULL,
  CHECK ((value_numeric IS NULL) <> (value_text IS NULL))
);
CREATE INDEX IF NOT EXISTS measurements_by_study ON measurements(study_id,batch_id,metric_code,day);
CREATE TABLE IF NOT EXISTS doe_candidates (
  study_id TEXT NOT NULL REFERENCES studies(id),
  candidate_id TEXT NOT NULL, candidate_sha256 TEXT NOT NULL,
  composition_json TEXT NOT NULL, design_json TEXT NOT NULL,
  PRIMARY KEY(study_id,candidate_id)
);
CREATE TABLE IF NOT EXISTS batch_provenance (
  batch_id TEXT PRIMARY KEY REFERENCES batches(id),
  study_id TEXT NOT NULL REFERENCES studies(id),
  candidate_id TEXT NOT NULL,
  candidate_sha256 TEXT NOT NULL,
  actual_weights_json TEXT NOT NULL,
  raw_material_lots_json TEXT NOT NULL,
  process_json TEXT NOT NULL,
  weighed_by TEXT NOT NULL,
  deviation_max_pp REAL NOT NULL,
  traceability_status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(study_id,candidate_id) REFERENCES doe_candidates(study_id,candidate_id)
);
CREATE TRIGGER IF NOT EXISTS deny_candidate_update BEFORE UPDATE ON doe_candidates BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS deny_candidate_delete BEFORE DELETE ON doe_candidates BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS deny_provenance_update BEFORE UPDATE ON batch_provenance BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS deny_provenance_delete BEFORE DELETE ON batch_provenance BEGIN SELECT RAISE(ABORT,'immutable'); END;
'''

class Repository:
    def __init__(self,path=None):
        self.path=path or os.environ.get('V45_DB_PATH','/tmp/formula_v45_experiments.sqlite3')
        if self.path!=':memory:':Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self._conn() as c:c.executescript(SCHEMA)
    def _conn(self):
        db=sqlite3.connect(self.path, timeout=15)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db
    @staticmethod
    def _id(prefix):return f'{prefix}-{uuid.uuid4().hex[:16]}'
    def create_study(self,body):
        protocol=verify_protocol(body.get('protocol',{}))
        scenario=body.get('scenario')
        if not isinstance(scenario,dict) or not isinstance(scenario.get('items'),list):raise InputError('Thiếu snapshot scenario.items')
        if scenario.get('ambiguous_claims'):
            raise InputError('Chọn một cách hiểu claim trước khi khóa công thức thử nghiệm')
        optimized=solve_scenario(scenario,Catalog() if scenario.get('product_id') is not None else None)
        if optimized.get('status')!='FEASIBLE':
            raise InputError('Công thức không có nghiệm khả thi theo bộ giải V4.4, chưa thể lập mẻ nghiên cứu')
        title=str(body.get('title','')).strip();creator=str(body.get('created_by','')).strip()
        if not title or not creator:raise InputError('Thiếu title/created_by')
        # A stored DoE is always recalculated server-side from the immutable snapshot.
        candidates = _freeze_candidates(scenario, body.get('doe_design'))
        ident=self._id('STUDY');now=utcnow();sha=canonical_hash(scenario)
        with self._conn() as conn:
            conn.execute('INSERT INTO studies VALUES(?,?,?,?,?,?,?,?)',
                (ident,title,creator,str(scenario.get('product_type') or 'unknown'),sha,
                 json.dumps(scenario,ensure_ascii=False),json.dumps(protocol,ensure_ascii=False),now))
            for point in candidates:
                conn.execute('INSERT INTO doe_candidates VALUES (?,?,?,?,?)',
                    (ident, point['candidate_id'], point['candidate_sha256'],
                     json.dumps(point['composition_percent'], ensure_ascii=False,sort_keys=True),
                     json.dumps(point['design'],ensure_ascii=False,sort_keys=True)))
        return {'study_id':ident,'formula_sha256':sha,'protocol':protocol,'created_at':now,
                'data_status':'PROTOCOL_CREATED_NOT_TESTED','approved_for_manufacturing':False}
    def get_study(self,study_id):
        with self._conn() as conn:
            row=conn.execute('SELECT * FROM studies WHERE id=?',(study_id,)).fetchone()
        if not row:raise InputError('Không tìm thấy nghiên cứu')
        out=dict(row);out['scenario']=json.loads(out.pop('scenario_json'));out['protocol']=json.loads(out.pop('protocol_json'))
        return out
    def list_candidates(self,study_id):
        self.get_study(study_id)
        with self._conn() as conn:
            rows=conn.execute('SELECT * FROM doe_candidates WHERE study_id=? ORDER BY candidate_id',(study_id,)).fetchall()
        return [dict(candidate_id=r['candidate_id'], candidate_sha256=r['candidate_sha256'],
                     composition_percent=json.loads(r['composition_json']),
                     design=json.loads(r['design_json'])) for r in rows]
    def list_studies(self):
        with self._conn() as conn:
            rows=conn.execute('SELECT id,title,product_type,formula_sha256,created_at FROM studies ORDER BY created_at DESC LIMIT 100').fetchall()
        return [dict(r) for r in rows]
    def add_batch(self,study_id,body):
        self.get_study(study_id)
        lot=str(body.get('lot_code','')).strip();operator=str(body.get('operator','')).strip()
        if not lot or not operator:raise InputError('Thiếu lot_code/operator')
        when=str(body.get('prepared_at') or utcnow())
        ident=self._id('BATCH')
        provenance = None
        if body.get('candidate_id') is not None:
            point = next((x for x in self.list_candidates(study_id) if x['candidate_id']==body['candidate_id']),None)
            if point is None: raise InputError('Phương án DoE không thuộc nghiên cứu')
            provenance = _verify_batch_provenance(point,body)
        try:
            with self._conn() as conn:
                conn.execute('INSERT INTO batches VALUES(?,?,?,?,?,?)',(ident,study_id,lot,operator,when,utcnow()))
                if provenance is not None:
                    conn.execute('INSERT INTO batch_provenance VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                        (ident,study_id,provenance['candidate_id'],provenance['candidate_sha256'],
                         json.dumps(provenance['actual_weights_g'],sort_keys=True),
                         json.dumps(provenance['raw_material_lots'],sort_keys=True),
                         json.dumps(provenance['process'],ensure_ascii=False,sort_keys=True),
                         provenance['weighed_by'],provenance['deviation_max_pp'],provenance['traceability_status'],utcnow()))
        except sqlite3.IntegrityError as e:raise InputError('Mã mẻ đã tồn tại trong nghiên cứu') from e
        return {'batch_id':ident,'study_id':study_id,'lot_code':lot,'prepared_at':when, 'traceability_status':provenance['traceability_status'] if provenance else 'UNLINKED_LEGACY'}
    def list_batches(self,study_id):
        self.get_study(study_id)
        with self._conn() as conn:
            rows=conn.execute('''SELECT b.*,p.candidate_id,p.candidate_sha256,p.traceability_status,
                         p.actual_weights_json,p.raw_material_lots_json,p.process_json,p.weighed_by,p.deviation_max_pp
                         FROM batches b LEFT JOIN batch_provenance p ON p.batch_id=b.id
                         WHERE b.study_id=? ORDER BY b.created_at,b.id''',(study_id,)).fetchall()
        output=[]
        for r in rows:
            d=dict(r);d['traceability_status']=d['traceability_status'] or 'UNLINKED_LEGACY'
            for col,key in [('actual_weights_json','actual_weights_g'),('raw_material_lots_json','raw_material_lots'),('process_json','process')]:
                d[key]=json.loads(d.pop(col)) if d[col] is not None else None
            output.append(d)
        return output
    def add_measurement(self,study_id,body):
        study=self.get_study(study_id)
        batch_id=str(body.get('batch_id',''))
        metric_code=str(body.get('metric_code','')).strip().upper()
        specs={s['code']:s for s in study['protocol']['metrics']}
        spec=specs.get(metric_code)
        if not spec:raise InputError('Chỉ tiêu không tồn tại trong protocol')
        day=body.get('day',0)
        if type(day)!=int or day not in spec['timepoints_days']:raise InputError('Ngày đo không thuộc protocol')
        operator=str(body.get('operator','')).strip();method=str(body.get('method','')).strip()
        instrument_id=str(body.get('instrument_id','')).strip()
        evidence_uri=str(body.get('evidence_uri','')).strip()
        if not operator or not method or not instrument_id:raise InputError('Bắt buộc có operator, method, instrument_id')
        kind=body.get('data_kind','MEASURED')
        if kind not in ('MEASURED','DEMO_SYNTHETIC'):raise InputError('data_kind không hợp lệ')
        if kind=='MEASURED' and not evidence_uri:raise InputError('Dữ liệu đo phải có evidence_uri để truy vết')
        if kind=='MEASURED' and evidence_uri.startswith(('demo:','synthetic:')):
            raise InputError('Không dùng nguồn giả làm bằng chứng đo thực tế')
        unit=str(body.get('unit',spec['unit']))
        if unit != spec['unit']:raise InputError('Đơn vị không khớp protocol, phải quy đổi trước khi nhập')
        if spec['kind']=='numeric':
            value_num=finite_float(body.get('value'),'measurement.value');value_text=None
        else:
            value_text=str(body.get('value','')).strip();value_num=None
            if not value_text:raise InputError('Giá trị nhận xét rỗng')
        supersedes=body.get('supersedes_measurement_id')
        with self._conn() as conn:
            if not conn.execute('SELECT 1 FROM batches WHERE id=? AND study_id=?',(batch_id,study_id)).fetchone():
                raise InputError('Mẻ không thuộc nghiên cứu')
            if supersedes:
                old=conn.execute('SELECT * FROM measurements WHERE id=? AND study_id=?',(supersedes,study_id)).fetchone()
                if not old or old['batch_id']!=batch_id or old['metric_code']!=metric_code or old['day']!=day or old['data_kind']!=kind:
                    raise InputError('Bản chỉnh sửa phải cùng mẻ/chỉ tiêu/thời điểm')
                if conn.execute('SELECT 1 FROM measurements WHERE supersedes_measurement_id=?',(supersedes,)).fetchone():
                    raise InputError('Quan sát đã được thay thế')
            ident=self._id('OBS')
            conn.execute('INSERT INTO measurements VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                        (ident,study_id,batch_id,metric_code,day,value_num,value_text,unit,method,
                         instrument_id,operator,evidence_uri,kind,supersedes,utcnow()))
        return {'measurement_id':ident,'classification':'RECORDED_APPEND_ONLY',
                'data_kind':kind,'included_in_evidence':kind=='MEASURED'}
    def list_measurements(self,study_id):
        self.get_study(study_id)
        with self._conn() as conn:return [dict(x) for x in conn.execute('SELECT * FROM measurements WHERE study_id=? ORDER BY recorded_at,id',(study_id,))]
    def report(self,study_id):
        result=evaluate_study(self.get_study(study_id),self.list_batches(study_id),self.list_measurements(study_id))
        return _apply_traceability_gate(result,self.list_batches(study_id))
