# Edge System Checker Web Deployment Script
# Simple version without special characters

$SERVER_USER = "koast-user"
$SERVER_HOST = "10.1.10.128"
$SERVER_PATH = "~/edge-system-checker-web"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Edge System Checker Web Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Git
Write-Host "Step 1: Checking Git..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "[OK] Git repository found" -ForegroundColor Green
    git status
} else {
    Write-Host "[INFO] Git not initialized" -ForegroundColor Yellow
    $response = Read-Host "Initialize Git? (y/n)"
    if ($response -eq "y") {
        git init
        git add .
        git commit -m "Initial commit"
    }
}

# Step 2: Check Remote
Write-Host ""
Write-Host "Step 2: Checking remote repository..." -ForegroundColor Yellow
$remotes = git remote 2>$null
if ($remotes -contains "origin") {
    $url = git remote get-url origin
    Write-Host "[OK] Remote found: $url" -ForegroundColor Green
    $response = Read-Host "Push to remote? (y/n)"
    if ($response -eq "y") {
        git push origin main 2>$null
        if ($LASTEXITCODE -ne 0) {
            git push origin master
        }
    }
} else {
    Write-Host "[INFO] No remote configured" -ForegroundColor Yellow
    Write-Host "Add remote with:" -ForegroundColor White
    Write-Host '  git remote add origin "YOUR_REPO_URL"' -ForegroundColor White
}

# Step 3: Deploy
Write-Host ""
Write-Host "Step 3: Deploying to server..." -ForegroundColor Yellow
Write-Host "Server: ${SERVER_USER}@${SERVER_HOST}" -ForegroundColor Cyan

$response = Read-Host "Continue with deployment? (y/n)"
if ($response -ne "y") {
    Write-Host "Deployment cancelled" -ForegroundColor Red
    exit
}

Write-Host "Creating archive..." -ForegroundColor Yellow
$tarFile = "edge-system-checker-web.tar.gz"

if (Get-Command tar -ErrorAction SilentlyContinue) {
    tar -czf $tarFile --exclude=".git" --exclude="__pycache__" --exclude="venv" --exclude=".env" --exclude="*.db" --exclude="*.log" .
    
    Write-Host "Uploading..." -ForegroundColor Yellow
    scp $tarFile "${SERVER_USER}@${SERVER_HOST}:~/"
    
    Write-Host "Extracting on server..." -ForegroundColor Yellow
    ssh "${SERVER_USER}@${SERVER_HOST}" "mkdir -p ${SERVER_PATH}; cd ${SERVER_PATH}; tar -xzf ~/${tarFile}; rm ~/${tarFile}"
    
    Remove-Item $tarFile
} else {
    Write-Host "[WARN] tar not found, using scp..." -ForegroundColor Yellow
    scp -r . "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/"
}

Write-Host "[OK] Deployment complete!" -ForegroundColor Green

# Instructions
Write-Host ""
Write-Host "Next steps on server:" -ForegroundColor Cyan
Write-Host "  ssh ${SERVER_USER}@${SERVER_HOST}" -ForegroundColor White
Write-Host "  cd ${SERVER_PATH}/backend" -ForegroundColor White
Write-Host "  python3 -m venv venv" -ForegroundColor White
Write-Host "  source venv/bin/activate" -ForegroundColor White
Write-Host "  pip install -r requirements.txt" -ForegroundColor White
Write-Host "  cp ../env.example .env" -ForegroundColor White
Write-Host "  nano .env" -ForegroundColor White
Write-Host "  uvicorn app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan

