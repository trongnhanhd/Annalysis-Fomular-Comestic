#!/usr/bin/env bash
set -euo pipefail
mkdir -p var
export V45_DB_PATH="${V45_DB_PATH:-$(pwd)/var/experiments_v45.sqlite3}"
exec python -m uvicorn api_v45:app --host 127.0.0.1 --port 8000
