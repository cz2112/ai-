# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "Right-click this script and select 'Run as Administrator'" -ForegroundColor Yellow
    Pause
    exit 1
}

Write-Host "Installing Smart Study Assistant development prerequisites..." -ForegroundColor Cyan
Write-Host ""

# Check if winget is available
try {
    $wingetVersion = winget --version
    Write-Host "Found winget version: $wingetVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: winget is not installed or not available." -ForegroundColor Red
    Write-Host "Please install App Installer from Microsoft Store or update Windows 10/11." -ForegroundColor Yellow
    Write-Host "Download: https://aka.ms/getwinget" -ForegroundColor Cyan
    Pause
    exit 1
}

Write-Host ""

$packages = @(
    @{ Label = "Git"; Id = "Git.Git" },
    @{ Label = "Python 3.12"; Id = "Python.Python.3.12" },
    @{ Label = "Node.js LTS"; Id = "OpenJS.NodeJS.LTS" },
    @{ Label = "Visual Studio Code"; Id = "Microsoft.VisualStudioCode" },
    @{ Label = "Docker Desktop"; Id = "Docker.DockerDesktop" }
)

$step = 1
$failed = @()

foreach ($package in $packages) {
    Write-Host ("{0}/{1} Installing {2}..." -f $step, $packages.Count, $package.Label) -ForegroundColor Green

    try {
        $result = winget install -e --id $package.Id --accept-source-agreements --accept-package-agreements 2>&1

        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Warning: Installation may have failed or package already exists" -ForegroundColor Yellow
            $failed += $package.Label
        } else {
            Write-Host "  Success!" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Error: $_" -ForegroundColor Red
        $failed += $package.Label
    }

    Write-Host ""
    $step++
}

Write-Host "Installation complete!" -ForegroundColor Cyan
Write-Host ""

if ($failed.Count -gt 0) {
    Write-Host "Failed or skipped packages:" -ForegroundColor Yellow
    foreach ($pkg in $failed) {
        Write-Host "  - $pkg" -ForegroundColor Yellow
    }
    Write-Host ""
}

Write-Host "Important Notes:" -ForegroundColor Yellow
Write-Host "1. Restart your computer if Python, Node, or Docker do not appear in a new terminal."
Write-Host "2. Docker Desktop requires WSL2 on Windows 10/11. Enable it if prompted."
Write-Host "3. After restart, verify installations by running:"
Write-Host "   git --version"
Write-Host "   python --version"
Write-Host "   node --version"
Write-Host "4. Follow README.md for backend, frontend, and Celery setup."
Write-Host ""

Pause
