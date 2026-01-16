@echo off
echo Fazendo setup completo da aplicacao...
powershell -Command "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass" >nul 2>&1
cd backend

echo Removendo virtual environment antigo se existir...
if exist .venv rmdir /s /q .venv

echo Criando novo virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo Erro ao criar virtual environment. Verifique se Python esta instalado.
    pause
    exit /b 1
)

echo Ativando virtual environment...
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Erro ao ativar virtual environment.
    pause
    exit /b 1
)

echo Instalando dependencias...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Erro ao instalar dependencias.
    pause
    exit /b 1
)

echo Verificando .env...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo .env criado a partir de .env.example.
        echo IMPORTANTE: Edite o arquivo .env com suas chaves reais antes de executar novamente!
        echo Pressione qualquer tecla para continuar ou Ctrl+C para cancelar...
        pause
    ) else (
        echo AVISO: Arquivo .env nao encontrado e .env.example nao existe.
        echo Crie manualmente um arquivo .env com as variaveis necessarias.
        echo Pressione qualquer tecla para continuar ou Ctrl+C para cancelar...
        pause
    )
)

echo Iniciando aplicacao...
python app.py
pause
