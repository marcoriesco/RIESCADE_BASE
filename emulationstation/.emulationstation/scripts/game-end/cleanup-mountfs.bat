@echo off
REM Script de limpeza centralizado para remover a pasta .mountfs
REM Executado após o término de um jogo para garantir que o temp está limpo

setlocal enabledelayedexpansion

REM Obter o caminho do temp
for /f "tokens=*" %%A in ('powershell -NoProfile -Command "[System.IO.Path]::GetTempPath()"') do set TEMP_DIR=%%A

REM Remover quebra de linha/espaços extras
set TEMP_DIR=!TEMP_DIR:~0,-2!

REM Definir o caminho da pasta .mountfs
set MOUNTFS_PATH=!TEMP_DIR!.mountfs

REM Verificar se a pasta existe
if not exist "!MOUNTFS_PATH!" (
    exit /b 0
)

REM Aguardar um pouco para liberar locks
timeout /t 1 /nobreak >nul 2>&1

REM Tentar remover com PowerShell (mais confiável)
powershell -NoProfile -Command "Remove-Item -Path '!MOUNTFS_PATH!' -Recurse -Force -ErrorAction SilentlyContinue" 2>nul

REM Se ainda existir, tentar remover com comando DOS
if exist "!MOUNTFS_PATH!" (
    REM Tentar remover todos os arquivos dentro da pasta
    for /r "!MOUNTFS_PATH!" %%F in (*) do (
        del /f /q "%%F" 2>nul
    )
    
    REM Tentar remover todas as subpastas
    for /d /r "!MOUNTFS_PATH!" %%D in (*) do (
        rmdir /s /q "%%D" 2>nul
    )
    
    REM Tentar remover a pasta principal
    rmdir /s /q "!MOUNTFS_PATH!" 2>nul
)

exit /b 0
