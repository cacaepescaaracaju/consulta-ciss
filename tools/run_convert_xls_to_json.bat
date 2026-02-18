@echo off
setlocal EnableDelayedExpansion
set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%convert_xls_to_json.py"
set "OUT_DIR=%SCRIPT_DIR%..\data"
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"
if not exist "%PY_SCRIPT%" (
  echo Erro: convert_xls_to_json.py não encontrado em "%SCRIPT_DIR%"
  exit /b 1
)
set "LOG=%SCRIPT_DIR%last_sync.log"
type nul > "%LOG%"
>> "%LOG%" echo Iniciando execucao em %date% %time%
if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
  "%SCRIPT_DIR%venv\Scripts\python.exe" "%PY_SCRIPT%" %* -o "%OUT_DIR%"
  set "EXITCODE=!errorlevel!"
  >> "%LOG%" echo Python retorno !EXITCODE!
  if "!EXITCODE!"=="0" call :write_att
  if "!EXITCODE!"=="0" call :git_push
  set "GITCODE=!errorlevel!"
  if not "!GITCODE!"=="0" call :git_fail
  exit /b !GITCODE!
)
where py >nul 2>&1
if %errorlevel%==0 (
  py "%PY_SCRIPT%" %* -o "%OUT_DIR%"
  set "EXITCODE=!errorlevel!"
  >> "%LOG%" echo Python retorno !EXITCODE!
  if "!EXITCODE!"=="0" call :write_att
  if "!EXITCODE!"=="0" call :git_push
  set "GITCODE=!errorlevel!"
  if not "!GITCODE!"=="0" call :git_fail
  exit /b !GITCODE!
)
where python >nul 2>&1
if %errorlevel%==0 (
  python "%PY_SCRIPT%" %* -o "%OUT_DIR%"
  set "EXITCODE=!errorlevel!"
  >> "%LOG%" echo Python retorno !EXITCODE!
  if "!EXITCODE!"=="0" call :write_att
  if "!EXITCODE!"=="0" call :git_push
  set "GITCODE=!errorlevel!"
  if not "!GITCODE!"=="0" call :git_fail
  exit /b !GITCODE!
)
echo Erro: Python não encontrado no PATH. Instale Python ou o launcher 'py'.
exit /b 1

:write_att
>> "%LOG%" echo Atualizando data_att.json
for /f "usebackq tokens=*" %%I in (`powershell -NoProfile -Command "(Get-Date).ToString('o')"`) do set "ISO_DATE=%%I"
> "%OUT_DIR%\data_att.json" echo {"updated_at":"%ISO_DATE%"}
>> "%LOG%" echo data_att.json atualizado em %ISO_DATE%
if not exist "%OUT_DIR%\data_att.json" >> "%LOG%" echo Falha ao escrever data_att.json
exit /b 0

:git_push
set "REPO_DIR=%SCRIPT_DIR%.."
for /f "usebackq tokens=*" %%I in (`powershell -NoProfile -Command "(Get-Date).ToString('yyyy-MM-dd HH:mm:ss')"`) do set "STAMP=%%I"
>> "%LOG%" echo Iniciando git sync em %STAMP%
where git >> "%LOG%" 2>&1
if not "%errorlevel%"=="0" exit /b 2
git -C "%REPO_DIR%" rev-parse --is-inside-work-tree >> "%LOG%" 2>&1
if not "%errorlevel%"=="0" exit /b 3
git -C "%REPO_DIR%" add -A >> "%LOG%" 2>&1
git -C "%REPO_DIR%" reset -- "%SCRIPT_DIR%last_sync.log" >> "%LOG%" 2>&1
git -C "%REPO_DIR%" diff --cached --quiet
if "%errorlevel%"=="0" (
  >> "%LOG%" echo Nenhuma mudanca para commit.
  exit /b 0
)
>> "%LOG%" echo Criando commit
git -C "%REPO_DIR%" commit -m "Atualiza dados %STAMP%" >> "%LOG%" 2>&1
if not "%errorlevel%"=="0" exit /b 4
>> "%LOG%" echo Enviando push
git -C "%REPO_DIR%" push >> "%LOG%" 2>&1
if not "%errorlevel%"=="0" exit /b 5
>> "%LOG%" echo Push concluido com sucesso.
exit /b 0

:git_fail
if not exist "%LOG%" type nul > "%LOG%"
echo Falha no git. Veja o log em "%SCRIPT_DIR%last_sync.log"
type "%SCRIPT_DIR%last_sync.log"
pause
exit /b 1
