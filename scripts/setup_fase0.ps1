# Scouter BI — setup_fase0.ps1
# Executa a Fase 0 na sua máquina (Windows + PowerShell).
# Uso, na pasta do projeto:  powershell -ExecutionPolicy Bypass -File scripts\setup_fase0.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Passo($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

Passo "1/5 Verificando pré-requisitos"
foreach ($cmd in @("git", "python", "sqlcmd")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) { Write-Host "  [OK] $cmd" -ForegroundColor Green }
    else { Write-Host "  [FALTA] $cmd" -ForegroundColor Yellow }
}

Passo "2/5 Criando ambiente Python"
if (-not (Test-Path ".venv")) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip -q
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt -q
if (-not (Test-Path ".env")) { Copy-Item .env.example .env; Write-Host "  .env criado a partir do exemplo" }

Passo "3/5 Criando banco DBZ_BI"
if (Get-Command sqlcmd -ErrorAction SilentlyContinue) {
    sqlcmd -S localhost -E -C -i sql\00_create_database.sql
} else {
    Write-Host "  sqlcmd não encontrado: rode sql\00_create_database.sql no SSMS" -ForegroundColor Yellow
}

Passo "4/5 Conferindo campos da API"
& .\.venv\Scripts\python.exe src\check_api.py

Passo "5/5 Inicializando Git"
if (-not (Test-Path ".git")) {
    git init -b main
    git add .
    git commit -m "chore: estrutura inicial do Scouter BI (Fase 0)"
    Write-Host "  Agora crie o repositório 'scouter-bi' no GitHub e rode:" -ForegroundColor Cyan
    Write-Host "  git remote add origin https://github.com/Deogadox/scouter-bi.git"
    Write-Host "  git push -u origin main"
}

Write-Host "`nFase 0 automatizada concluída. Falta o teste do 'Publicar na web' (manual)." -ForegroundColor Green
