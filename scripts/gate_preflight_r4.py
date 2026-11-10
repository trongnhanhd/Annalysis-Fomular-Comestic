"""Non-destructive gate preflight. Reports blockers rather than fabricating PASS.

Use python scripts/gate_preflight_r4.py; output is JSON, no network requests.
"""
from __future__ import annotations
import json,shutil,subprocess,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FRONT=ROOT/'frontend'

def status():
    versions={}
    for exe in ('node','npm','psql','postgres','pg_ctl','docker'):
        versions[exe]=shutil.which(exe)
    node=versions['node']
    node_version=subprocess.run([node,'--version'],capture_output=True,text=True).stdout.strip() if node else None
    lock=FRONT/'package-lock.json'
    installed=FRONT/'node_modules/next/package.json'
    db=os.getenv('TEST_POSTGRES_URL','')
    return {
      'gate_a':{'node_version':node_version,'npm_available':bool(versions['npm']),
                'lockfile_present':lock.exists(),'next_installed':installed.exists(),
                'status':'NOT_VERIFIED','required':'npm ci; npm run build; Chromium E2E'},
      'gate_c':{'postgres_server_local':bool(versions['postgres'] or versions['pg_ctl'] or versions['docker']),
                'test_postgres_url_configured':bool(db),'status':'NOT_VERIFIED',
                'required':'migration 001/002 on *_test DB; read/write; backup/restore'},
      'gate_d':{'auth_mode':os.getenv('RND_AUTH_MODE','disabled'),
                'status':'PROTOTYPE_ONLY','required':'production RBAC/CSRF/audit/HTTPS and review'}
    }

if __name__=='__main__': print(json.dumps(status(),ensure_ascii=False,indent=2))
