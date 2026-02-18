@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%convert_xls_to_json.py"
set "OUT_DIR=%SCRIPT_DIR%..\data"
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"
if not exist "%PY_SCRIPT%" (
  echo Erro: convert_xls_to_json.py não encontrado em "%SCRIPT_DIR%"
  exit /b 1
)
if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
  "%SCRIPT_DIR%venv\Scripts\python.exe" "%PY_SCRIPT%" %* -o "%OUT_DIR%"
  call :write_att
  exit /b %errorlevel%
)
where py >nul 2>&1
if %errorlevel%==0 (
  py "%PY_SCRIPT%" %* -o "%OUT_DIR%"
  call :write_att
  exit /b %errorlevel%
)
where python >nul 2>&1
if %errorlevel%==0 (
  python "%PY_SCRIPT%" %* -o "%OUT_DIR%"
  call :write_att
  exit /b %errorlevel%
)
echo Erro: Python não encontrado no PATH. Instale Python ou o launcher 'py'.
exit /b 1

:write_att
for /f "usebackq tokens=*" %%I in (`powershell -NoProfile -Command "(Get-Date).ToString('o')"`) do set "ISO_DATE=%%I"
> "%OUT_DIR%\data_att.json" echo {"updated_at":"%ISO_DATE%"}
exit /b 0
