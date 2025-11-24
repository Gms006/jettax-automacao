@echo off
setlocal ENABLEDELAYEDEXPANSION

echo.
echo ============================================
echo   SUBIR PROJETO JETTAX PARA O GITHUB
echo ============================================
echo.

REM Pasta do repositório = pasta onde o .bat está
set "REPO_DIR=%~dp0"

echo Pasta do repositório:
echo   %REPO_DIR%
echo.

REM Vai para a pasta do projeto
cd /d "%REPO_DIR%"

REM Verifica se o Git está instalado
git --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Git nao encontrado no PATH.
    echo Instale o Git ou adicione-o ao PATH e tente novamente.
    echo.
    pause
    exit /b 1
)

REM Limpa qualquer repositório git quebrado
if exist ".git" (
    echo Removendo .git antigo para limpar historico...
    rmdir /s /q .git
    echo .git removido.
    echo.
)

REM Inicializa novo repositório
echo Inicializando novo repositório git...
git init

REM Configura usuario LOCAL do repositório (pode ajustar o nome/email se quiser)
echo Configurando usuario local do repositorio...
git config user.name "Gms006"
git config user.email "gptjoao01@gmail.com"

REM Configura remoto
set "REMOTE_URL=https://github.com/Gms006/jettax-automacao.git"
echo.
echo Configurando remoto origin:
echo   %REMOTE_URL%

REM Se já existir origin, altera a URL; se não, adiciona
git remote -v | find "origin" >nul 2>&1
if errorlevel 1 (
    git remote add origin "%REMOTE_URL%"
) else (
    git remote set-url origin "%REMOTE_URL%"
)

echo.
echo Adicionando arquivos ao commit...
git add .

echo.
echo Criando commit inicial...
git commit -m "Primeiro commit do projeto JETTAX automacao completa"

echo.
echo Garantindo que o nome da branch e 'main'...
git branch -M main

echo.
echo Enviando para o GitHub (main --force)...
git push -u origin main --force

echo.
echo ============================================
echo   PRONTO! Verifique o repositorio no GitHub.
echo ============================================
echo.
pause
endlocal
