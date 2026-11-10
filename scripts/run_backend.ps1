# Run from the project root on Windows PowerShell.
$env:V45_DB_PATH = Join-Path (Get-Location) "var\experiments_v45.sqlite3"
if (!(Test-Path "var")) { New-Item -ItemType Directory -Path "var" | Out-Null }
python -m uvicorn api_v45:app --host 127.0.0.1 --port 8000
