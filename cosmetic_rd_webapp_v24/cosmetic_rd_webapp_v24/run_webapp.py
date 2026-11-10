"""Start the local research web app; defaults to localhost for safety."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parent / 'backend'
env = os.environ.copy()
env.setdefault('DATABASE_URL', 'sqlite:///' + str((root/'cosmetic_rd_local.db').resolve()))
print('Cosmetic R&D Web App: http://127.0.0.1:8000/app', flush=True)
print('Backend API: http://127.0.0.1:8000/docs', flush=True)
raise SystemExit(subprocess.call([sys.executable, '-m','uvicorn','main:app','--host','127.0.0.1','--port','8000'], cwd=root, env=env))
