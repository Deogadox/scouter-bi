# Scouter BI — run_fase2.ps1
# Curadoria -> stg -> dw. Grava tudo em logs\fase2_resultado.txt
# Uso, na pasta do projeto:  powershell -ExecutionPolicy Bypass -File scripts\run_fase2.ps1

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
New-Item -ItemType Directory -Force -Path logs | Out-Null
$out = Join-Path $root "logs\fase2_resultado.txt"
$py = Join-Path $root ".venv\Scripts\python.exe"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

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

Set-Content -Path $out -Value "Fase 2 — $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -Encoding UTF8

Passo "1/5 Tabelas de curadoria (stg) e modelo dw"
$ddl = Rodar { sqlcmd -S localhost -E -C -b -f 65001 -i sql\02_curadoria_stg.sql,sql\03_dw.sql }

Passo "2/5 Validação e carga dos CSVs de curadoria"
$cur = Rodar { & $py -m src.load_curadoria }

Passo "3/5 Carga stg -> dw (dw.sp_carga_dw)"
$dw = if ($cur -eq 0) { Rodar { sqlcmd -S localhost -E -C -b -f 65001 -d DBZ_BI -Q "EXEC dw.sp_carga_dw;" } } else { 1 }

Passo "4/5 Conferência"
Rodar { sqlcmd -S localhost -E -C -f 65001 -d DBZ_BI -W -s "|" -Q "SET NOCOUNT ON; SELECT * FROM dw.vw_resumo_carga; SELECT TOP 4 id_execucao, etapa, status, linhas_afetadas, LEFT(mensagem, 200) AS mensagem FROM ctl.log_execucao ORDER BY id_execucao DESC; SELECT * FROM dw.vw_mais_forte_por_saga ORDER BY ordem_cronologica; SELECT id_luta, zebra, poder_vencedor, poder_perdedor, observacao FROM dw.fato_luta WHERE zebra = 1;" } | Out-Null

Passo "5/5 Testes Python"
$testes = Rodar { & $py -m pytest -q }

$status = if ($ddl -eq 0 -and $cur -eq 0 -and $dw -eq 0 -and $testes -eq 0) { "SUCESSO" } else { "VERIFICAR" }
Passo "Resultado: $status"
Write-Host "`nSaída completa em $out" -ForegroundColor Green
