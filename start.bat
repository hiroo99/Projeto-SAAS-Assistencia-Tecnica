@echo off
echo Iniciando aplicacao...
cd backend
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Erro ao ativar virtual environment. Execute setup_and_start.bat primeiro.
    pause
    exit /b 1
)
python app.py
pause
