Write-Host "Installing Smart Study Assistant development prerequisites..." -ForegroundColor Cyan

$packages = @(
    @{ Label = "Git"; Id = "Git.Git" },
    @{ Label = "Python 3.12"; Id = "Python.Python.3.12" },
    @{ Label = "Node.js LTS"; Id = "OpenJS.NodeJS.LTS" },
    @{ Label = "Visual Studio Code"; Id = "Microsoft.VisualStudioCode" },
    @{ Label = "Docker Desktop"; Id = "Docker.DockerDesktop" }
)

$step = 1
foreach ($package in $packages) {
    Write-Host ("{0}/{1} Installing {2}..." -f $step, $packages.Count, $package.Label) -ForegroundColor Green
    winget install -e --id $package.Id --accept-source-agreements --accept-package-agreements
    $step++
}

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
Write-Host "Notes:" -ForegroundColor Yellow
Write-Host "1. Restart the machine if Python, Node, or Docker do not appear in a new terminal."
Write-Host "2. Docker Desktop is the recommended way to run PostgreSQL and Redis locally."
Write-Host "3. After installation, follow README.md for backend, frontend, and Celery setup."

Pause
