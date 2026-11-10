"""REST library for products, immutable LP snapshots, research drafts and formula hypotheses."""
from __future__ import annotations
import os
import secrets
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, Field, HttpUrl, model_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from engine import AnalysisRequest, parse_inci
from suggest import analyze_with_suggestion
from workspace_db import get_db, Product, AnalysisRun, ResearchRecord, FormulaVersion, utcnow

router = APIRouter(prefix='/api/workspace', tags=['Thư viện R&D'])
MARKETS = ('EU', 'US', 'KR', 'CN', 'VN', 'ASEAN')


def authenticate(x_api_key: str | None = Header(default=None)):
    token = os.getenv('WORKSPACE_API_KEY', '')
    if token and (not x_api_key or not secrets.compare_digest(x_api_key, token)):
        raise HTTPException(status_code=401, detail='Thiếu hoặc sai khóa API cho thư viện R&D')
    # Without token allowed only in local development; never deploy this configuration publicly.


router.dependencies.append(Depends(authenticate))

class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=220)
    brand: str = Field(default='', max_length=160)
    market: Literal['EU','US','KR','CN','VN','ASEAN'] = 'VN'
    product_type: str = Field(default='leave_on', min_length=1, max_length=60)
    inci: str = Field(min_length=1)
    notes: str = ''

    @model_validator(mode='after')
    def validate_inci(self):
        parse_inci(self.inci)
        return self

class ResearchIn(BaseModel):
    inci: str = Field(min_length=1, max_length=220)
    title: str = Field(min_length=1, max_length=350)
    study_type: str = 'unspecified'
    source_url: HttpUrl
    doi: str = ''
    min_pct: float | None = Field(default=None, ge=0, le=100)
    max_pct: float | None = Field(default=None, ge=0, le=100)
    product_type: str = 'unspecified'
    matrix: str = ''
    notes: str = ''

    @model_validator(mode='after')
    def valid_range(self):
        if self.min_pct is not None and self.max_pct is not None and self.min_pct > self.max_pct:
            raise ValueError('min_pct không được lớn hơn max_pct')
        return self

class ReviewIn(BaseModel):
    decision: Literal['reviewed', 'rejected']
    reviewer: str = Field(min_length=2, max_length=150)
    review_note: str = Field(min_length=4)

class FormulaItem(BaseModel):
    inci: str = Field(min_length=1)
    pct: float = Field(ge=0, le=100)

class FormulaIn(BaseModel):
    name: str = Field(default='Công thức giả thuyết', min_length=1, max_length=200)
    ingredients: list[FormulaItem] = Field(min_length=1)
    notes: str = ''
    @model_validator(mode='after')
    def validated(self):
        items = [i.inci.casefold() for i in self.ingredients]
        if len(set(items)) != len(items):
            raise ValueError('INCI bị trùng trong công thức')
        if abs(sum(i.pct for i in self.ingredients) - 100) > 0.0001:
            raise ValueError('Tổng công thức phải bằng 100% ±0,0001%')
        return self


def as_product(p: Product) -> dict:
    return {'id':p.id,'name':p.name,'brand':p.brand,'market':p.market,'product_type':p.product_type,'inci':p.inci,'notes':p.notes,'created_at':p.created_at,'updated_at':p.updated_at}

def as_analysis(a: AnalysisRun, full: bool = False) -> dict:
    x = {'id': a.id,'product_id': a.product_id,'status':a.result_status,'created_at':a.created_at}
    if full:
        x.update({'input':a.input_snapshot,'result':a.result_snapshot})
    return x

def as_research(r: ResearchRecord) -> dict:
    return {k: getattr(r,k) for k in ('id','inci','title','study_type','source_url','doi','min_pct','max_pct','product_type','matrix','notes','review_status','reviewed_by','review_note','reviewed_at','created_at')}

def as_formula(f: FormulaVersion) -> dict:
    return {'id':f.id,'product_id':f.product_id,'version':f.version,'name':f.name,'ingredients':f.ingredients,'notes':f.notes,'status':f.status,'created_at':f.created_at}

@router.get('/health')
def health(db: Session=Depends(get_db)):
    db.execute(select(func.count()).select_from(Product)).scalar_one()
    return {'status':'ok','database':'connected', 'evidence_policy':'reviewed_catalog_only'}

@router.get('/products')
def products(q: str = '', limit: int = Query(default=50, ge=1, le=200), db:Session=Depends(get_db)):
    stmt = select(Product).order_by(Product.created_at.desc()).limit(limit)
    if q.strip():
        stmt = stmt.where(Product.name.ilike(f'%{q.strip()}%'))
    return {'data':[as_product(x) for x in db.scalars(stmt).all()]}

@router.post('/products', status_code=201)
def create_product(payload: ProductIn, db: Session=Depends(get_db)):
    p = Product(**payload.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return as_product(p)

@router.get('/products/{product_id}')
def get_product(product_id: str, db:Session=Depends(get_db)):
    p = db.get(Product, product_id)
    if p is None: raise HTTPException(status_code=404, detail='Không tìm thấy sản phẩm')
    return as_product(p)

@router.post('/products/{product_id}/analyses', status_code=201)
def create_analysis(product_id: str, request: AnalysisRequest, db: Session=Depends(get_db)):
    p = db.get(Product, product_id)
    if p is None: raise HTTPException(status_code=404, detail='Không tìm thấy sản phẩm')
    # Product identity is authoritative; request still contains explicit claims/premix etc.
    payload = request.model_copy(update={'inci':p.inci, 'market':p.market, 'product_type':p.product_type})
    try: result = analyze_with_suggestion(payload)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    a = AnalysisRun(product_id=p.id, input_snapshot=payload.model_dump(mode='json'), result_snapshot=result, result_status=result['status'])
    db.add(a); db.commit(); db.refresh(a)
    return as_analysis(a, full=True)

@router.get('/products/{product_id}/analyses')
def list_analyses(product_id:str, db:Session=Depends(get_db)):
    if db.get(Product, product_id) is None: raise HTTPException(status_code=404, detail='Không tìm thấy sản phẩm')
    return {'data':[as_analysis(x) for x in db.scalars(select(AnalysisRun).where(AnalysisRun.product_id == product_id).order_by(AnalysisRun.created_at.desc())).all()]}

@router.get('/analyses/{analysis_id}')
def get_analysis(analysis_id:str, db:Session=Depends(get_db)):
    a = db.get(AnalysisRun, analysis_id)
    if a is None: raise HTTPException(status_code=404, detail='Không tìm thấy phân tích')
    return as_analysis(a, full=True)

@router.get('/research')
def research(inci: str='', status: str='', limit:int=Query(default=100,ge=1,le=500), db:Session=Depends(get_db)):
    stmt = select(ResearchRecord).order_by(ResearchRecord.created_at.desc()).limit(limit)
    if inci.strip(): stmt = stmt.where(ResearchRecord.inci.ilike(f'%{inci.strip()}%'))
    if status: stmt = stmt.where(ResearchRecord.review_status==status)
    return {'data':[as_research(x) for x in db.scalars(stmt).all()], 'disclaimer':'Bản ghi người dùng độc lập với catalog đã tuyển chọn; không tham gia bộ giải.'}

@router.post('/research', status_code=201)
def add_research(payload:ResearchIn, db:Session=Depends(get_db)):
    data = payload.model_dump(mode='json')
    r = ResearchRecord(**data, review_status='draft')
    db.add(r); db.commit(); db.refresh(r)
    return as_research(r)

@router.post('/research/{research_id}/review')
def review_research(research_id:str, payload:ReviewIn, db:Session=Depends(get_db)):
    r = db.get(ResearchRecord, research_id)
    if r is None: raise HTTPException(status_code=404, detail='Không tìm thấy nghiên cứu')
    if r.review_status != 'draft': raise HTTPException(status_code=409, detail='Đã có quyết định kiểm duyệt; không thể ghi đè')
    r.review_status=payload.decision
    r.reviewed_by=payload.reviewer
    r.review_note=payload.review_note
    r.reviewed_at=utcnow()
    db.commit(); db.refresh(r)
    return as_research(r)

@router.get('/products/{product_id}/formulas')
def list_formulas(product_id:str, db:Session=Depends(get_db)):
    if db.get(Product, product_id) is None: raise HTTPException(status_code=404, detail='Không tìm thấy sản phẩm')
    stmt=select(FormulaVersion).where(FormulaVersion.product_id==product_id).order_by(FormulaVersion.version.desc())
    return {'data':[as_formula(x) for x in db.scalars(stmt).all()]}

@router.post('/products/{product_id}/formulas', status_code=201)
def save_formula(product_id:str, payload:FormulaIn, db:Session=Depends(get_db)):
    if db.get(Product, product_id) is None: raise HTTPException(status_code=404, detail='Không tìm thấy sản phẩm')
    last = db.scalar(select(func.max(FormulaVersion.version)).where(FormulaVersion.product_id==product_id)) or 0
    f=FormulaVersion(product_id=product_id, version=last+1, ingredients=[x.model_dump() for x in payload.ingredients], name=payload.name, notes=payload.notes, status='hypothesis')
    db.add(f)
    try: db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail='Xung đột phiên bản: vui lòng thử lưu lại') from exc
    db.refresh(f)
    return as_formula(f)
