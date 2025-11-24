@echo off
REM Script de execução rápida - JETTAX Automation
REM ==============================================

cd /d "%~dp0"

echo.
echo ========================================
echo   JETTAX 360 - Sistema de Automacao
echo ========================================
echo.
echo Escolha uma opcao:
echo.
echo [1] Cadastro de novos clientes
echo [2] Atualizacao de clientes existentes
echo [3] Sync completo (cadastro + atualizacao + modulos)
echo [4] Comparar (apenas listar diferencas)
echo [5] Configurar modulos (Federal e Servicos)
echo [6] Modo DRY-RUN (cadastro - simulacao)
echo [7] Modo DRY-RUN (atualizacao - simulacao)
echo [8] Modo DRY-RUN (modulos - simulacao)
echo [0] Sair
echo.

set /p opcao="Digite a opcao: "

if "%opcao%"=="1" (
    echo.
    echo Executando CADASTRO...
    python main.py cadastro
    goto end
)

if "%opcao%"=="2" (
    echo.
    echo Executando ATUALIZACAO...
    python main.py atualizacao
    goto end
)

if "%opcao%"=="3" (
    echo.
    echo Executando SYNC COMPLETO...
    python main.py sync
    goto end
)

if "%opcao%"=="4" (
    echo.
    echo Executando COMPARACAO...
    python main.py comparar
    goto end
)

if "%opcao%"=="5" (
    echo.
    echo Executando CONFIGURACAO DE MODULOS...
    python main.py modulos
    goto end
)

if "%opcao%"=="6" (
    echo.
    echo Executando CADASTRO (DRY-RUN)...
    python main.py cadastro --dry-run
    goto end
)

if "%opcao%"=="7" (
    echo.
    echo Executando ATUALIZACAO (DRY-RUN)...
    python main.py atualizacao --dry-run
    goto end
)

if "%opcao%"=="8" (
    echo.
    echo Executando MODULOS (DRY-RUN)...
    python main.py modulos --dry-run
    goto end
)

if "%opcao%"=="0" (
    echo.
    echo Saindo...
    exit /b 0
)

echo.
echo Opcao invalida!

:end
echo.
echo ========================================
echo.
pause
