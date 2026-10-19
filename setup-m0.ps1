# setup-m0.ps1  -  Automates M0 for the Personalized Travel Itinerary Planner
$ErrorActionPreference = "Stop"
$Root     = "D:\Personalized Travel Itenerary Planner"
$Backend  = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Check($what) { if ($LASTEXITCODE -ne 0) { throw "Failed: $what" } }
function Write-File($Path, $Content) {
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (Test-Path $Path) { Write-Host "  skip (exists): $Path" -ForegroundColor Yellow; return }
    [System.IO.File]::WriteAllText($Path, $Content, $utf8)
    Write-Host "  created: $Path" -ForegroundColor Green
}

# ---------- 1. Prerequisites ----------
Step "Checking prerequisites"
foreach ($tool in "node", "npm", "git") {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "$tool is not installed or not on PATH. Install it, reopen the terminal, and re-run."
    }
}
if (Get-Command python -ErrorAction SilentlyContinue) { $py = "python" }
elseif (Get-Command py -ErrorAction SilentlyContinue) { $py = "py" }
else { throw "Python is not installed or not on PATH." }
Write-Host ("  node " + (node --version) + " | npm " + (npm --version) + " | " + (& $py --version) + " | " + (git --version))

# ---------- 2. Folder structure ----------
Step "Creating folder structure"
Set-Location $Root
foreach ($d in "docs", "backend\app\core", "backend\app\routers", "backend\app\services",
               "backend\app\schemas", "backend\app\prompts", "backend\tests") {
    New-Item -ItemType Directory -Path (Join-Path $Root $d) -Force | Out-Null
}

# ---------- 3. .gitignore ----------
Step "Writing .gitignore"
Write-File (Join-Path $Root ".gitignore") @'
# secrets
.env
*.env.local

# python
venv/
__pycache__/
*.pyc
.pytest_cache/

# node
node_modules/
dist/

# os / editor
.DS_Store
Thumbs.db
.vscode/
'@

# ---------- 4. Backend ----------
Step "Setting up backend (venv + dependencies)"
$venvPy = Join-Path $Backend "venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    & $py -m venv (Join-Path $Backend "venv"); Check "create venv"
}
& $venvPy -m pip install --upgrade pip; Check "upgrade pip"
& $venvPy -m pip install fastapi "uvicorn[standard]" pydantic-settings supabase pyjwt httpx pytest; Check "pip install"
$freeze = & $venvPy -m pip freeze
[System.IO.File]::WriteAllLines((Join-Path $Backend "requirements.txt"), $freeze, $utf8)
Write-Host "  requirements.txt written" -ForegroundColor Green

foreach ($pkg in "app", "app\core", "app\routers", "app\services", "app\schemas") {
    Write-File (Join-Path $Backend "$pkg\__init__.py") ""
}
Write-File (Join-Path $Backend "app\main.py") @'
from fastapi import FastAPI

app = FastAPI(title="Travel Itinerary Planner API")


@app.get("/api/health")
def health():
    return {"status": "ok"}
'@

# ---------- 5. Frontend ----------
Step "Setting up frontend (Vite + React + TypeScript)"
if (-not (Test-Path (Join-Path $Frontend "package.json"))) {
    Set-Location $Root
    npm create vite@latest frontend -- --template react-ts --no-interactive
    if (-not (Test-Path (Join-Path $Frontend "package.json"))) {
        throw "Vite did not create the frontend. Run 'npm create vite@latest frontend -- --template react-ts' manually and re-run this script."
    }
}
Set-Location $Frontend
npm install; Check "npm install"
Set-Location $Root

# ---------- 6. Environment templates ----------
Step "Writing environment templates"
Write-File (Join-Path $Backend ".env.example") @'
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_JWT_SECRET=
LLM_PROVIDER=
LLM_API_KEY=
MAPS_API_KEY=
ALLOWED_ORIGINS=http://localhost:5173
'@
Write-File (Join-Path $Frontend ".env.example") @'
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_API_URL=http://localhost:8000
'@
foreach ($dir in $Backend, $Frontend) {
    $env = Join-Path $dir ".env"
    if (-not (Test-Path $env)) { Copy-Item (Join-Path $dir ".env.example") $env; Write-Host "  created: $env" -ForegroundColor Green }
}

# ---------- 7. Verify backend ----------
Step "Verifying backend health endpoint"
$proc = Start-Process -FilePath $venvPy -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "8000" `
        -WorkingDirectory $Backend -PassThru -WindowStyle Hidden
$health = $null
try {
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Seconds 1
        try { $health = Invoke-RestMethod "http://localhost:8000/api/health"; break } catch {}
    }
} finally {
    if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
}
if ($health.status -eq "ok") { Write-Host "  Backend health check passed" -ForegroundColor Green }
else { Write-Host "  Backend health check FAILED (is port 8000 in use?)" -ForegroundColor Red }

# ---------- 8. Git ----------
Step "Initialising Git and committing"
Set-Location $Root
if (-not (Test-Path (Join-Path $Root ".git"))) { git init; Check "git init" }
git add .
git commit -m "M0: project setup"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Commit skipped. If Git asked for your identity, run:" -ForegroundColor Yellow
    Write-Host '    git config --global user.name "Your Name"'
    Write-Host '    git config --global user.email "you@example.com"'
    Write-Host '  then run: git commit -m "M0: project setup"'
}

# ---------- Done ----------
Step "M0 automation finished"
Write-Host "Still manual (cannot be automated):" -ForegroundColor Cyan
Write-Host "  1. Create a Supabase project at supabase.com"
Write-Host "  2. Paste Project URL + anon key into backend\.env and frontend\.env (VITE_ variables)"
Write-Host "  3. Add your LLM API key to backend\.env"
Write-Host "To start: backend -> cd backend; .\venv\Scripts\python.exe -m uvicorn app.main:app --reload"
Write-Host "          frontend -> cd frontend; npm run dev"