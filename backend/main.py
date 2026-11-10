from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from engine import AnalysisRequest, RULES, analyze
from evidence_catalog import find_studies, find_limits, evidence_meta, regulatory_meta, find_preservation_systems, preservation_meta
from regulatory_check import RegulatoryCheckIn, check_limit
from suggest import analyze_with_suggestion

app = FastAPI(title='Cosmetic R&D Intelligence V2.2', version='2.2.0', description='Phân tích INCI 6 thị trường; đối chiếu thư viện nghiên cứu có nguồn và giới hạn pháp lý mẫu, không suy ra % đo được.')

@app.get('/')
def home():
    return FileResponse(Path(__file__).parent / 'static' / 'index.html')

@app.get('/api/v2/rules')
def rules():
    return RULES

@app.get('/api/v2/catalog')
def catalog_metadata():
    return {'research': evidence_meta(), 'regulatory': regulatory_meta(), 'preservation': preservation_meta(), 'warning': 'Không phải tập dữ liệu đầy đủ hoặc chứng nhận tuân thủ pháp lý.'}

@app.get('/api/v2/catalog/research')
def list_research(inci: str | None = None, category: str | None = None):
    return {'data': find_studies(inci=inci, category=category), 'metadata': evidence_meta()}

@app.get('/api/v2/catalog/regulatory')
def list_regulatory(inci: str | None = None, market: str | None = None):
    return {'data': find_limits(inci=inci, market=market), 'metadata': regulatory_meta()}

@app.get('/api/v2/catalog/preservation')
def preservation(inci: str | None = None):
    return {'data': find_preservation_systems(inci=inci), 'metadata': preservation_meta()}

@app.post('/api/v2/analyze')
def run(req: AnalysisRequest):
    try:
        return analyze_with_suggestion(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post('/api/v2/regulatory/check')
def regulatory_check(req: RegulatoryCheckIn):
    return check_limit(req)


# New R&D workspace API; V2.1 solver endpoints stay unchanged.
from workspace_api import router as workspace_router
from workspace_db import initialize_database
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    initialize_database()
    yield

app.router.lifespan_context = lifespan
app.include_router(workspace_router)
