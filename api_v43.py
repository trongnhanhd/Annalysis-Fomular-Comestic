"""Independent FastAPI app for V4.3. Existing V4.2 API preserved separately."""
import os
from typing import Any
from fastapi import FastAPI,Query,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field,ConfigDict
from scientific_engine_v43 import ScientificEngineV43
eng=ScientificEngineV43()
app=FastAPI(title='Formula Intelligence V4.3 — Scientific Grade Evidence',version='4.3.0')
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in os.getenv('RND_ALLOWED_ORIGINS','http://localhost:3000').split(',') if x.strip()],allow_methods=['GET','POST'],allow_headers=['Content-Type'])
class ScenarioV43(BaseModel):
    model_config=ConfigDict(extra='forbid')
    product_type:str='Chưa xác định'
    product_profile:str|None=None
    product_id:int|None=None
    ui_base_display_percent:float|None=None
    physical_form:str='unknown'
    pH:float|None=None
    water_phase_percent:float|None=None
    preservation_evidence:bool=False
    solubilizer_system_confirmed:bool=False
    process_temperature_c:float|None=None
    process_intent:str='unknown'
    items:list[dict[str,Any]]=Field(default_factory=list)
@app.get('/health')
def health():return {'ok':True,'version':'4.3.0','manufacturing_approval':False}
@app.get('/api/v4.3/grades')
def grades():return {'total':len(eng.grades)+len(eng.v42.grades),'results':[{**g,'display_name':g['grade_name'],'expected_inci':g['inci_declared'],'catalog_version':'V4.3'} for g in eng.grades]+[{**g,'catalog_version':'V4.2'} for g in eng.v42.grades]}
@app.get('/api/v4.3/observations')
def observations(inci:str='',grade_id:str='',limit:int=Query(100,ge=1,le=200)):
    return {'results':eng.find_properties(inci,grade_id,limit)}
@app.get('/api/v4.3/coverage')
def coverage():
    return {'v42_inci_count':len(eng.coverage),'v43_supplier_grades':len(eng.grades),'v43_scientific_observations':len(eng.observations),'v43_qualitative_components':len(eng.grade_components),'coverage_claim':'supplier grade-specific, not 190 fully verified ingredients'}
@app.post('/api/v4.3/evaluate')
def evaluate(scenario:ScenarioV43):
    try:return eng.evaluate(scenario.model_dump())
    except ValueError as exc:raise HTTPException(status_code=422,detail=str(exc))

@app.get('/api/v4.3/ingredients')
def ingredients(q:str='', limit:int=Query(30,ge=1,le=100)):
    return {'results':eng.v42.search(q,limit)}

@app.get('/api/v4.3/templates')
def templates():
    return {'templates':list(eng.v42.v41_group_catalog.products.values())}

@app.get('/api/v4.3/groups')
def groups(product_id:int|None=None):
    return {'groups':[r for r in eng.v42.group_rules if product_id is None or r['product_id']==str(product_id)]}
