"""FastAPI preview app. Run: uvicorn api:app --reload --port 8000"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel, Field, ConfigDict
from typing import Any
from compatibility_engine import KnowledgeEngine

engine=KnowledgeEngine()
app=FastAPI(title='Formula Intelligence V4.2',version='4.2.0',description='Ingredient knowledge and compatibility SCREENING; not manufacture approval')
allowed_origins=[x.strip() for x in os.getenv('RND_ALLOWED_ORIGINS','http://localhost:3000').split(',') if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=allowed_origins,allow_methods=['GET','POST'],allow_headers=['Content-Type'])

class Scenario(BaseModel):
    model_config = ConfigDict(extra='forbid')
    product_type:str='Chưa xác định'
    product_id:int|None=None
    ui_base_display_percent:float|None=None
    physical_form:str='unknown'
    pH:float|None=None
    water_phase_percent:float|None=None
    preservation_evidence:bool=False
    solubilizer_system_confirmed:bool=False
    items:list[dict[str,Any]]=Field(default_factory=list)

@app.get('/health')
def health():return {'ok':True,'version':'4.2.0','scientific_approval':False}

@app.get('/api/v4.2/ingredients')
def ingredients(q:str='', limit:int=Query(30,ge=1,le=100)):
    return {'results':engine.search(q,limit)}

@app.get('/api/v4.2/groups')
def groups(product_id:int|None=None):
    return {'groups': [r for r in engine.group_rules if product_id is None or r['product_id']==str(product_id)]}

@app.get('/api/v4.2/templates')
def templates():return {'templates':list(engine.v41_group_catalog.products.values())}

@app.get('/api/v4.2/grades')
def grades():return {'grades':engine.grades}

@app.post('/api/v4.2/evaluate')
def evaluate(payload:Scenario):
    try:return engine.evaluate(payload.model_dump())
    except ValueError as err:raise HTTPException(status_code=422,detail=str(err))
