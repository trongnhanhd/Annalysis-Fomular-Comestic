@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ===============================================
echo  Cosmetic R^&D Intelligence - Web App V2.4
echo ===============================================
echo Cai dat thu vien Python neu can...
python -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo Cai dat that bai. Kiem tra Python 3.11+ va ket noi Internet.
    pause
    exit /b 1
)
echo Mo http://127.0.0.1:8000/app trong trinh duyet
python run_webapp.py
pause
