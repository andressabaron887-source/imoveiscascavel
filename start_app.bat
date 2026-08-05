@echo off
chcp 65001 > nul
title Imóveis Cascavel/PR - Sistema de Busca Imobiliária
color 0A

set PYTHON="C:\Users\andre\AppData\Local\Programs\Python\Python312\python.exe"
set APP_DIR=%~dp0

echo.
echo ================================================================
echo   IMÓVEIS CASCAVEL/PR - Iniciando Sistema...
echo ================================================================
echo.

:: Verificar se Python está disponível
%PYTHON% --version > nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não encontrado.
    echo Execute o setup.bat primeiro para configurar o sistema.
    echo.
    pause
    exit /b 1
)

:: Verificar se Playwright está instalado
%PYTHON% -c "import playwright" > nul 2>&1
if errorlevel 1 (
    echo [AVISO] Playwright não instalado. Executando configuração...
    %PYTHON% -m pip install playwright --quiet
    %PYTHON% -m playwright install chromium
)

echo Iniciando servidor em http://localhost:8080 ...
echo.
echo Para encerrar: pressione Ctrl+C nesta janela.
echo.

:: Abrir navegador após 2 segundos
start /b cmd /c "timeout /t 2 > nul && start http://localhost:8080"

:: Iniciar servidor Python
%PYTHON% "%APP_DIR%server_py.py"

pause
