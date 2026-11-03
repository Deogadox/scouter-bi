# Scouter BI — aplicar_relatorio.ps1
# Fase 4: deixa no relatório só as páginas listadas em pages.json (remove as páginas antigas).
# Rode com o Power BI Desktop FECHADO, na pasta do projeto:
#   powershell -ExecutionPolicy Bypass -File scripts\aplicar_relatorio.ps1

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$root = Split-Path -Parent $PSScriptRoot
$paginas = Join-Path $root "powerbi\DBZ_BI.Report\definition\pages"

if (Get-Process PBIDesktop -ErrorAction SilentlyContinue) {
    Write-Host "O Power BI Desktop está aberto. Feche sem salvar e rode o script de novo." -ForegroundColor Yellow
    exit 1
}

$meta = Get-Content (Join-Path $paginas "pages.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$manter = @($meta.pageOrder)
$removidas = 0
Get-ChildItem $paginas -Directory | Where-Object { $manter -notcontains $_.Name } | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
    Write-Host "  página antiga removida: $($_.Name)"
    $removidas++
}

$faltando = @($manter | Where-Object { -not (Test-Path (Join-Path $paginas "$_\page.json")) })
if ($faltando.Count -gt 0) {
    Write-Host "Faltam páginas novas: $($faltando -join ', '). Atualize os arquivos do projeto antes de abrir." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Relatório pronto: $($manter.Count) páginas (Scouter, Arena, Escalada, Quiz, Radar, Bastidores). Antigas removidas: $removidas" -ForegroundColor Green
Write-Host "Agora abra powerbi\DBZ_BI.pbip no Power BI Desktop e clique em Atualizar."
