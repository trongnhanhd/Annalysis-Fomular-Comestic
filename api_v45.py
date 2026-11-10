"""V4.5 R&D experiments API. Preserves all V4.4 and V4.3 endpoints."""
from fastapi import HTTPException, Request
from pydantic import BaseModel,ConfigDict
from api_v44 import app,catalog
from experimental_validation_v45 import build_doe
from storage_factory_v451 import open_repository, storage_name
from optimizer_v44 import InputError

app.title='Formula Intelligence V4.5.2 — R&D Experimental Validation'
app.version='4.5.2'

class FlexibleBody(BaseModel):
    model_config=ConfigDict(extra='allow')

def _repo():return open_repository()

def _handle(func,*args,**kwargs):
    try:return func(*args,**kwargs)
    except (InputError,ValueError) as e:raise HTTPException(status_code=422,detail=str(e))

@app.get('/health/v4.5')
def health():
    try:
        repo=_repo()
        ready=(not hasattr(repo,'ping')) or repo.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail='Cơ sở dữ liệu chưa sẵn sàng hoặc chưa có migration') from exc
    if not ready:
        raise HTTPException(status_code=503,detail='Cơ sở dữ liệu chưa có migration')
    return {'ok':True,'version':'4.5.2','storage':storage_name(),'approved_for_manufacturing':False}

@app.post('/api/v4.5/design-experiments')
def design_experiments(body:FlexibleBody):
    payload=body.model_dump()
    if len(str(payload))>200000:raise HTTPException(413,'Payload quá lớn')
    return _handle(build_doe,payload,catalog if payload.get('scenario',{}).get('product_id') else None)

@app.post('/api/v4.5/studies')
def create_study(body:FlexibleBody, request:Request):
    payload=body.model_dump()
    from auth_r3 import auth_mode
    if auth_mode() == 'required':
        # Persist the authenticated creator, not a client-supplied identity.
        payload['created_by']=request.state.rnd_user['username']
    return _handle(_repo().create_study,payload)

@app.get('/api/v4.5/studies')
def list_studies():return _repo().list_studies()

@app.get('/api/v4.5/studies/{study_id}')
def get_study(study_id:str):return _handle(_repo().get_study,study_id)

@app.get('/api/v4.5/studies/{study_id}/candidates')
def list_candidates(study_id:str):return _handle(_repo().list_candidates,study_id)

def _bind_actor(payload:dict, request:Request, fields:tuple[str,...]) -> dict:
    from auth_r3 import auth_mode
    if auth_mode() == 'required':
        # Traceability identity comes from the authenticated session, never from the browser.
        username = request.state.rnd_user['username']
        for field in fields:
            payload[field] = username
    return payload

@app.post('/api/v4.5/studies/{study_id}/batches')
def add_batch(study_id:str,body:FlexibleBody,request:Request):
    payload=_bind_actor(body.model_dump(), request, ('operator','weighed_by'))
    return _handle(_repo().add_batch,study_id,payload)

@app.get('/api/v4.5/studies/{study_id}/batches')
def list_batches(study_id:str):return _handle(_repo().list_batches,study_id)

@app.post('/api/v4.5/studies/{study_id}/measurements')
def add_measurement(study_id:str,body:FlexibleBody,request:Request):
    payload=_bind_actor(body.model_dump(), request, ('operator',))
    return _handle(_repo().add_measurement,study_id,payload)

@app.get('/api/v4.5/studies/{study_id}/measurements')
def list_measurements(study_id:str):return _handle(_repo().list_measurements,study_id)

@app.get('/api/v4.5/studies/{study_id}/assessment')
def assess(study_id:str):return _handle(_repo().report,study_id)

@app.post('/api/v4.5/review-draft')
def review_draft(body:FlexibleBody):
    """Read-only calculation; no storage, no laboratory/safety approval."""
    from draft_review_v452 import review_draft as run_review
    payload=body.model_dump()
    if len(str(payload))>200000:raise HTTPException(413,'Payload quá lớn')
    return _handle(run_review,payload)


# R3: opt-in local-prototype session authentication and persistent-write role gate.
# Off by default for local compatibility tests; must not expose demo mode publicly.
from auth_r3 import guard as auth_guard, register_auth_routes
app.middleware('http')(auth_guard)
register_auth_routes(app)
