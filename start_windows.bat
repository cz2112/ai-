@echo off
setlocal EnableExtensions EnableDelayedExpansion

if /I "%~1"=="run-backend" goto :run_backend
if /I "%~1"=="run-worker" goto :run_worker
if /I "%~1"=="run-frontend" goto :run_frontend

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

set "PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
set "PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn"
set "NPM_REGISTRY_URL=https://registry.npmmirror.com"
set "DOCKER_CONTEXT_NAME=desktop-linux"
set "DOCKER_DOCTOR_PS1=%ROOT_DIR%docker_wsl_doctor.ps1"
set "INSTALL_ONLY=0"

if /I "%~1"=="deps" set "INSTALL_ONLY=1"
if /I "%~1"=="doctor" set "DOCTOR_ONLY=1"

echo.
echo === Smart Study Assistant Windows Bootstrap ===
echo Root: %ROOT_DIR%
echo Pip mirror: %PIP_INDEX_URL%
echo NPM registry: %NPM_REGISTRY_URL%
if "%INSTALL_ONLY%"=="1" echo Mode: install dependencies only
if "%DOCTOR_ONLY%"=="1" echo Mode: Docker / WSL diagnostics only
echo.

if "%DOCTOR_ONLY%"=="1" (
    call :load_wsl_snapshot
    if errorlevel 1 goto :fail
    call :print_wsl_snapshot
    exit /b 0
)

call :require_cmd npm "Node.js / npm"
if errorlevel 1 goto :fail
call :find_python
if errorlevel 1 goto :fail

if not exist ".env" (
    echo [INFO] Creating root .env from .env.example
    copy /Y ".env.example" ".env" >nul
)

if not exist "backend\.env" (
    echo [INFO] Creating backend\.env from backend\.env.example
    copy /Y "backend\.env.example" "backend\.env" >nul
)

if not exist "backend\venv\Scripts\python.exe" (
    echo [INFO] Creating backend virtual environment
    %PYTHON_CMD% -m venv "backend\venv"
    if errorlevel 1 goto :fail
)

echo [INFO] Upgrading pip from mirror
call "backend\venv\Scripts\python.exe" -m pip install --upgrade pip -i "%PIP_INDEX_URL%" --trusted-host "%PIP_TRUSTED_HOST%"
if errorlevel 1 goto :fail

echo [INFO] Installing backend dependencies from mirror
call "backend\venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt" -i "%PIP_INDEX_URL%" --trusted-host "%PIP_TRUSTED_HOST%"
if errorlevel 1 goto :fail

echo [INFO] Installing frontend dependencies from mirror
pushd "frontend"
call npm install --registry="%NPM_REGISTRY_URL%"
if errorlevel 1 (
    popd
    goto :fail
)
popd

if "%INSTALL_ONLY%"=="1" (
    echo.
    echo Dependency installation finished.
    echo Run start_windows.bat to start the full local stack.
    echo.
    pause
    exit /b 0
)

call :require_cmd docker "Docker Desktop / docker"
if errorlevel 1 goto :fail
call :prepare_docker
if errorlevel 1 goto :fail

call :find_backend_port
if errorlevel 1 goto :fail

echo [INFO] Starting PostgreSQL and Redis with Docker Compose
call :start_infra
if errorlevel 1 (
    echo [WARN] Docker Compose failed. Trying automatic Docker repair...
    call :repair_docker
    if errorlevel 1 (
        call :docker_troubleshooting
        goto :fail
    )
    echo [INFO] Retrying Docker Compose
    call :start_infra
)
if errorlevel 1 (
    call :docker_troubleshooting
    goto :fail
)

echo [INFO] Starting backend API on http://127.0.0.1:%BACKEND_PORT%
start "SmartStudy Backend" cmd /k ""%~f0" run-backend %BACKEND_PORT%"

echo [INFO] Starting Celery worker
start "SmartStudy Worker" cmd /k ""%~f0" run-worker"

echo [INFO] Starting frontend on http://127.0.0.1:5173
start "SmartStudy Frontend" cmd /k ""%~f0" run-frontend"

echo.
echo Done.
echo Backend : http://127.0.0.1:%BACKEND_PORT%
echo Frontend: http://127.0.0.1:5173 ^(or the next Vite port if 5173 is busy^)
echo.
echo Notes:
echo 1. Fill in backend\.env before using DeepSeek or GLM features.
echo 2. Docker Desktop must be running before this script starts services.
echo 3. Re-run npm install manually if package.json changes.
echo.
pause
exit /b 0

:require_cmd
where %~1 >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Missing required command: %~2
    exit /b 1
)
exit /b 0

:find_python
where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.12"
    %PYTHON_CMD% --version >nul 2>nul
    if not errorlevel 1 exit /b 0
    set "PYTHON_CMD=py"
    %PYTHON_CMD% --version >nul 2>nul
    if not errorlevel 1 exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    python --version >nul 2>nul
    if not errorlevel 1 exit /b 0
)

echo [ERROR] Python was not found. Install Python 3.12 first.
exit /b 1

:prepare_docker
echo [INFO] Checking Docker Desktop engine
docker context use "%DOCKER_CONTEXT_NAME%" >nul 2>nul
docker info >nul 2>nul
if errorlevel 1 (
    echo [WARN] Docker Desktop is installed, but the Linux engine is not ready.
    call :load_wsl_snapshot
    if not errorlevel 1 call :print_wsl_snapshot
    call :repair_docker
    if errorlevel 1 (
        echo [ERROR] Docker Desktop could not be repaired automatically.
        echo [HINT] Open Docker Desktop and wait until the engine status is Running.
        exit /b 1
    )
)
exit /b 0

:start_infra
call docker compose up -d postgres redis
exit /b %errorlevel%

:repair_docker
echo [INFO] Attempting automatic Docker repair
call :auto_fix_wsl_prereqs
if errorlevel 1 exit /b 1

docker context use "%DOCKER_CONTEXT_NAME%" >nul 2>nul

where wsl >nul 2>nul
if not errorlevel 1 (
    echo [INFO] Resetting WSL backend
    wsl --shutdown >nul 2>nul
)

if /I "%DOCKER_SERVICE_STATE%"=="Stopped" (
    echo [INFO] Starting Docker Desktop service
    sc start com.docker.service >nul 2>nul
)

call :launch_docker_desktop
call :wait_for_docker 45
exit /b %errorlevel%

:launch_docker_desktop
set "DOCKER_DESKTOP_EXE="
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" set "DOCKER_DESKTOP_EXE=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
if "%DOCKER_DESKTOP_EXE%"=="" if exist "%LocalAppData%\Programs\Docker\Docker\Docker Desktop.exe" set "DOCKER_DESKTOP_EXE=%LocalAppData%\Programs\Docker\Docker\Docker Desktop.exe"
if not "%DOCKER_DESKTOP_EXE%"=="" (
    echo [INFO] Launching Docker Desktop
    start "" "%DOCKER_DESKTOP_EXE%" >nul 2>nul
)
exit /b 0

:wait_for_docker
set /a WAIT_LOOPS=%~1
if "%WAIT_LOOPS%"=="" set /a WAIT_LOOPS=30

:wait_for_docker_loop
docker info >nul 2>nul
if not errorlevel 1 exit /b 0
if %WAIT_LOOPS% LEQ 0 exit /b 1
timeout /t 2 /nobreak >nul
set /a WAIT_LOOPS-=1
goto :wait_for_docker_loop

:load_wsl_snapshot
if not exist "%DOCKER_DOCTOR_PS1%" (
    echo [ERROR] Missing helper script: %DOCKER_DOCTOR_PS1%
    exit /b 1
)

for %%V in (
    IS_ADMIN
    WSL_COMMAND
    WSL_STATUS
    WSL_FEATURE
    VMP_FEATURE
    HYPERV_FEATURE
    VIRTUALIZATION_FIRMWARE
    SLAT
    LOCALAPPDATA_DRIVE
    LOCALAPPDATA_FS
    VDS_SERVICE_STATE
    VDS_SERVICE_MODE
    DOCKER_SERVICE_STATE
    DOCKER_SERVICE_MODE
    DOCKER_DESKTOP_EXE
    DOCKER_INFO_OK
    DOCKER_CONTEXT
) do set "%%V="

for /f "usebackq tokens=1,* delims==" %%A in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%DOCKER_DOCTOR_PS1%"`) do (
    set "%%A=%%B"
)
exit /b 0

:print_wsl_snapshot
echo [INFO] Docker / WSL diagnostic snapshot
echo [INFO]   Admin token              : %IS_ADMIN%
echo [INFO]   WSL command              : %WSL_COMMAND%
echo [INFO]   WSL status               : %WSL_STATUS%
echo [INFO]   WSL feature              : %WSL_FEATURE%
echo [INFO]   VirtualMachinePlatform   : %VMP_FEATURE%
echo [INFO]   Hyper-V feature          : %HYPERV_FEATURE%
echo [INFO]   Docker context           : %DOCKER_CONTEXT%
echo [INFO]   Docker CLI info          : %DOCKER_INFO_OK%
echo [INFO]   Docker Desktop service   : %DOCKER_SERVICE_STATE% ^(%DOCKER_SERVICE_MODE%^)
echo [INFO]   Virtual Disk service     : %VDS_SERVICE_STATE% ^(%VDS_SERVICE_MODE%^)
echo [INFO]   Docker data drive        : %LOCALAPPDATA_DRIVE% ^(%LOCALAPPDATA_FS%^)
echo [INFO]   Firmware virtualization  : %VIRTUALIZATION_FIRMWARE%
echo [INFO]   SLAT                     : %SLAT%

if /I "%WSL_FEATURE%" NEQ "Enabled" (
    echo [WARN] Windows Subsystem for Linux is not enabled.
)
if /I "%VMP_FEATURE%" NEQ "Enabled" (
    echo [WARN] Virtual Machine Platform is not enabled.
)
if /I "%LOCALAPPDATA_FS%" NEQ "NTFS" (
    echo [WARN] Docker WSL storage is not on NTFS. VHDX creation can fail on non-NTFS volumes.
)
if /I "%VIRTUALIZATION_FIRMWARE%"=="Disabled" (
    echo [WARN] Firmware virtualization looks disabled. Check VT-x or AMD-V in BIOS/UEFI.
)
if /I "%VDS_SERVICE_STATE%"=="Stopped" (
    echo [WARN] Virtual Disk service is stopped. The VHDX provider error often points here or to missing WSL features.
)
echo.
exit /b 0

:auto_fix_wsl_prereqs
set "NEEDS_REBOOT=0"
set "REPAIR_BLOCKED=0"

call :load_wsl_snapshot
if errorlevel 1 exit /b 1

if /I "%WSL_COMMAND%"=="Missing" (
    echo [WARN] wsl.exe was not found in PATH.
)

call :ensure_feature_enabled "Microsoft-Windows-Subsystem-Linux" "Windows Subsystem for Linux" "%WSL_FEATURE%"
call :ensure_feature_enabled "VirtualMachinePlatform" "Virtual Machine Platform" "%VMP_FEATURE%"

if /I "%LOCALAPPDATA_FS%" NEQ "NTFS" (
    echo [ERROR] Docker Desktop WSL storage resolves to %LOCALAPPDATA_DRIVE%, but that drive is %LOCALAPPDATA_FS%.
    echo [HINT] The WSL backend needs an NTFS volume to create its VHDX files.
    set "REPAIR_BLOCKED=1"
)

if /I "%VDS_SERVICE_STATE%"=="Stopped" (
    echo [INFO] Starting Virtual Disk service
    sc start vds >nul 2>nul
)

if "%NEEDS_REBOOT%"=="1" (
    echo [ERROR] Windows optional features were enabled successfully.
    echo [HINT] Reboot Windows, then rerun start_windows.bat.
    exit /b 1
)

if "%REPAIR_BLOCKED%"=="1" (
    call :print_wsl_snapshot
    exit /b 1
)

exit /b 0

:ensure_feature_enabled
if /I "%~3"=="Enabled" exit /b 0

if /I "%~3"=="Missing" (
    echo [ERROR] %~2 is not available on this Windows installation.
    set "REPAIR_BLOCKED=1"
    exit /b 1
)

if "%IS_ADMIN%"=="1" (
    echo [WARN] %~2 is disabled. Enabling it now.
    dism.exe /online /Enable-Feature /FeatureName:%~1 /All /NoRestart >nul
    if errorlevel 1 (
        echo [ERROR] Failed to enable %~2 automatically.
        set "REPAIR_BLOCKED=1"
        exit /b 1
    )
    set "NEEDS_REBOOT=1"
    exit /b 0
)

echo [ERROR] %~2 is disabled.
echo [HINT] Re-run this script once from an Administrator terminal, or run:
echo [HINT]   dism.exe /online /Enable-Feature /FeatureName:%~1 /All /NoRestart
set "REPAIR_BLOCKED=1"
exit /b 1

:docker_troubleshooting
call :load_wsl_snapshot
if not errorlevel 1 call :print_wsl_snapshot
echo [HINT] Docker Compose failed while starting PostgreSQL or Redis.
echo [HINT] This is usually a Docker Desktop / Linux engine problem, not a project code problem.
echo [HINT] The VHDX-provider error usually means Windows cannot create Docker's WSL virtual disk yet.
echo [HINT] Ask your friend to try these steps in order:
echo [HINT]   1. Quit Docker Desktop completely and reopen it.
echo [HINT]   2. Wait until Docker Desktop shows the engine as Running.
echo [HINT]   3. Run: docker context use %DOCKER_CONTEXT_NAME%
echo [HINT]   4. Run: docker version
echo [HINT]   5. Run: docker pull postgres:16-alpine
echo [HINT]   6. If it still fails, run: wsl --shutdown
echo [HINT]      Then reopen Docker Desktop and try again.
echo [HINT]   7. If the error says VirtualMachinePlatform, WSL, or VHDX creation failed:
echo [HINT]      open an Administrator terminal and enable these features, then reboot:
echo [HINT]      dism.exe /online /Enable-Feature /FeatureName:Microsoft-Windows-Subsystem-Linux /All /NoRestart
echo [HINT]      dism.exe /online /Enable-Feature /FeatureName:VirtualMachinePlatform /All /NoRestart
echo [HINT]   8. Make sure %LOCALAPPDATA% is on an NTFS drive and BIOS virtualization is enabled.
echo [HINT]   9. If Docker is still broken, they can still install project dependencies with:
echo [HINT]      start_windows.bat deps
exit /b 0

:find_backend_port
for %%P in (8000 8001 8002 8003 8004 8005 8010) do (
    powershell -NoProfile -Command "$port=%%P; try { $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port); $listener.Start(); $listener.Stop(); exit 0 } catch { exit 1 }" >nul 2>nul
    if not errorlevel 1 (
        set "BACKEND_PORT=%%P"
        exit /b 0
    )
)
echo [ERROR] No free backend port found in 8000-8005 or 8010.
exit /b 1

:run_backend
cd /d "%~dp0backend"
set "BACKEND_PORT=%~2"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8000"
call "venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port %BACKEND_PORT%
exit /b %errorlevel%

:run_worker
cd /d "%~dp0backend"
call "venv\Scripts\celery.exe" -A app.workers.celery_app worker --loglevel=info --pool=solo
exit /b %errorlevel%

:run_frontend
cd /d "%~dp0frontend"
call npm run dev
exit /b %errorlevel%

:fail
echo.
echo [ERROR] Bootstrap failed.
pause
exit /b 1
