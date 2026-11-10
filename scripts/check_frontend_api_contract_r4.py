"""Offline API/Frontend contract check: explicit surfaces used by the current Next.js UI.

This is a pre-build validation and DOES NOT replace npm build or Chromium E2E.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from api_v45 import app

ROOT=Path(__file__).resolve().parents[1]
# Each UI path is mapped to a source snippet: a contract failure must identify
# which frontend location needs to be updated. Templated paths use FastAPI notation.
REQUIRED=[
 ('GET','/api/v4.3/ingredients','frontend/app/page.tsx','/api/v4.3/ingredients'),
 ('GET','/api/v4.3/grades','frontend/app/page.tsx','/api/v4.3/grades'),
 ('GET','/api/v4.3/templates','frontend/app/page.tsx','/api/v4.3/templates'),
 ('GET','/api/v4.3/observations','frontend/app/page.tsx','/api/v4.3/observations'),
 ('POST','/api/v4.3/evaluate','frontend/app/page.tsx','/api/v4.3/evaluate'),
 ('POST','/api/v4.4/optimize','frontend/app/optimizer/page.tsx','"optimize"'),
 ('POST','/api/v4.4/compare-claims','frontend/app/optimizer/page.tsx','"compare-claims"'),
 ('GET','/health/v4.5','frontend/app/experiments/page.tsx','/health/v4.5'),
 ('GET','/api/v4.5/studies','frontend/app/experiments/page.tsx',"api('/api/v4.5/studies')"),
 ('POST','/api/v4.5/review-draft','frontend/app/experiments/page.tsx','/api/v4.5/review-draft'),
 ('POST','/api/v4.5/design-experiments','frontend/app/experiments/page.tsx','/api/v4.5/design-experiments'),
 ('POST','/api/v4.5/studies','frontend/app/experiments/page.tsx',"api('/api/v4.5/studies',{method:'POST'"),
 ('GET','/api/v4.5/studies/{study_id}','frontend/app/experiments/page.tsx','/api/v4.5/studies/${encodeURIComponent(id)}'),
 ('GET','/api/v4.5/studies/{study_id}/batches','frontend/app/experiments/page.tsx','/batches'),
 ('GET','/api/v4.5/studies/{study_id}/measurements','frontend/app/experiments/page.tsx','/measurements'),
 ('POST','/api/v4.5/studies/{study_id}/measurements','frontend/app/experiments/page.tsx',"/measurements`,{method:'POST'"),
 ('GET','/api/v4.5/studies/{study_id}/assessment','frontend/app/experiments/page.tsx','/assessment'),
 ('GET','/api/v4.5/studies/{study_id}/candidates','frontend/components/BatchTraceabilityEditor.tsx','/candidates'),
 ('POST','/api/v4.5/studies/{study_id}/batches','frontend/components/BatchTraceabilityEditor.tsx','/batches'),
 ('GET','/api/v4.5/auth/me','frontend/components/AuthBar.tsx','/api/v4.5/auth/me'),
 ('POST','/api/v4.5/auth/logout','frontend/components/AuthBar.tsx','/api/v4.5/auth/logout'),
 ('POST','/api/v4.5/auth/login','frontend/app/login/page.tsx','/api/v4.5/auth/login'),
]

def check():
    spec=app.openapi(); routes=spec['paths']
    problems=[]
    config=(ROOT/'frontend/next.config.ts').read_text(encoding='utf-8')
    if "source: '/backend/:path*'" not in config:
        problems.append('Missing /backend reverse proxy rewrite')
    if "const BASE_URL = '/backend'" not in (ROOT/'frontend/app/experiments/page.tsx').read_text(encoding='utf-8'):
        problems.append('Experiments API base is not same-origin /backend')
    for method,path,source,needle in REQUIRED:
        ops=routes.get(path, {})
        if method.lower() not in ops:
            problems.append(f'{method} {path} absent from OpenAPI')
        if needle not in (ROOT/source).read_text(encoding='utf-8'):
            problems.append(f'{source} no longer refers to expected {needle!r}')
    if problems:
        raise AssertionError('API contract mismatches:\n'+'\n'.join(problems))
    return {'status':'PASS','ui_api_contracts':len(REQUIRED),
            'openapi_paths':len(routes),'notes':'Static API contract only, not Next build or HTTP E2E'}

if __name__=='__main__':
    print(json.dumps(check(),indent=2,ensure_ascii=False))
