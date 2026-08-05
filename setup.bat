@echo off
chcp 65001 > nul
title Imóveis Cascavel - Configuração Inicial
color 0B

set PYTHON="C:\Users\andre\AppData\Local\Programs\Python\Python312\python.exe"

echo.
echo ================================================================
echo   CONFIGURAÇÃO INICIAL - Imóveis Cascavel/PR
echo ================================================================
echo.

echo [1/3] Verificando Python 3.12...
%PYTHON% --version
if errorlevel 1 (
    echo ERRO: Python não encontrado. Por favor instale Python 3.12.
    pause
    exit /b 1
)

echo [2/3] Instalando Playwright e dependências...
%PYTHON% -m pip install playwright --quiet
if errorlevel 1 (
    echo ERRO ao instalar Playwright.
    pause
    exit /b 1
)

echo [3/3] Instalando navegadores Playwright (Chromium)...
%PYTHON% -m playwright install chromium
if errorlevel 1 (
    echo ERRO ao instalar Chromium.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   CONFIGURAÇÃO CONCLUÍDA! 
echo   Agora use o start_app.bat para iniciar o sistema.
echo ================================================================
echo.
pause
