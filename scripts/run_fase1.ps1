# Scouter BI — run_fase1.ps1
# Roda a Fase 1 completa e grava tudo em logs\fase1_resultado.txt
# Uso, na pasta do projeto:  powershell -ExecutionPolicy Bypass -File scripts\run_fase1.ps1

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
New-Item -ItemType Directory -Force -Path logs | Out-Null
$out = Join-Path $root "logs\fase1_resultado.txt"
$py = Join-Path $root ".venv\Scripts\python.exe"
$env:PYTHONIOENCODING = "utf-8"

function Passo($msg) {
    $linha = "`n==> $msg"
    Write-Host $linha -ForegroundColor Cyan
    Add-Content -Path $out -Value $linha -Encoding UTF8
}
function Rodar([scriptblock]$cmd) {
    $res = & $cmd 2>&1 | Out-String
    Write-Host $res
    Add-Content -Path $out -Value $res -Encoding UTF8
    return $LASTEXITCODE
}

Set-Content -Path $out -Value "Fase 1 — $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -Encoding UTF8

Passo "1/5 Dependências"
Rodar { & $py -m pip install -r requirements.txt -q } | Out-Null

Passo "2/5 Tabelas de staging"
Rodar { sqlcmd -S localhost -E -C -b -i sql\01_stg_tables.sql } | Out-Null

Passo "3/5 Testes do parser de ki"
$testes = Rodar { & $py -m pytest -q }

Passo "4/5 Extração da API e carga no stg"
$carga = Rodar { & $py -m src.extract }

Passo "5/5 Conferência no banco"
Rodar { sqlcmd -S localhost -E -C -d DBZ_BI -W -s "|" -Q "SET NOCOUNT ON; SELECT * FROM stg.vw_qualidade_carga; SELECT TOP 3 id_execucao, etapa, status, linhas_afetadas, mensagem, duracao_seg FROM ctl.log_execucao ORDER BY id_execucao DESC; SELECT TOP 5 nome, ki_texto, ki_max_texto, ki_max_status FROM stg.personagem ORDER BY ki_max_valor DESC; SELECT nome, ki_max_texto, ki_max_status FROM stg.personagem WHERE ki_max_status <> 'numerico';" } | Out-Null

$status = if ($testes -eq 0 -and $carga -eq 0) { "SUCESSO" } else { "VERIFICAR" }
Passo "Resultado: $status"
Write-Host "`nSaída completa em $out" -ForegroundColor Green
