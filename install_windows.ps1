Write-Host ">>> 开始自动安装 Smart Study Assistant 开发环境..." -ForegroundColor Cyan

# 1. 安装 Git
Write-Host "1/5 正在安装 Git..." -ForegroundColor Green
winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements

# 2. 安装 Python 3.11
Write-Host "2/5 正在安装 Python 3.11..." -ForegroundColor Green
winget install -e --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements

# 3. 安装 Node.js (LTS版本)
Write-Host "3/5 正在安装 Node.js..." -ForegroundColor Green
winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements

# 4. 安装 VS Code
Write-Host "4/5 正在安装 VS Code..." -ForegroundColor Green
winget install -e --id Microsoft.VisualStudioCode --accept-source-agreements --accept-package-agreements

# 5. 安装 Docker Desktop (体积较大，需等待)
Write-Host "5/5 正在安装 Docker Desktop (这需要一点时间)..." -ForegroundColor Green
winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements

Write-Host ">>> ✅ 安装命令已发送完毕！" -ForegroundColor Cyan
Write-Host ">>> ⚠️ 重要提示：" -ForegroundColor Yellow
Write-Host "1. 如果安装过程中弹出“允许更改设备”的窗口，请点击【是】。"
Write-Host "2. 安装完成后，请【重启电脑】以确保环境变量生效。"
Write-Host "3. 重启后打开 Docker Desktop 并注册登录，确保左下角变绿。"
Pause
