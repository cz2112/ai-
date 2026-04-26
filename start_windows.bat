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
set "INSTALL_ONLY=0"

if /I "%~1"=="deps" set "INSTALL_ONLY=1"

echo.
echo === Smart Study Assistant Windows Bootstrap ===
echo Root: %ROOT_DIR%
echo Pip mirror: %PIP_INDEX_URL%
echo NPM registry: %NPM_REGISTRY_URL%
if "%INSTALL_ONLY%"=="1" echo Mode: install dependencies only
echo.

call :require_cmd docker "Docker Desktop / docker"
if errorlevel 1 goto :fail
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

call :find_backend_port
if errorlevel 1 goto :fail

echo [INFO] Starting PostgreSQL and Redis with Docker Compose
call docker compose up -d postgres redis
if errorlevel 1 goto :fail

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
