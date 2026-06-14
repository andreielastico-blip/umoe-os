# UMOE OS 8.0 — Wrapper PowerShell para CHI Engine (Automação 6)
# Agendado: diariamente às 09h00
# Coloca: Tarefa Agendada Windows > "UMOE-CHI-Engine"

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe  = "python"           # altere para o path completo se necessário
$ChiScript  = Join-Path $ScriptDir "chi-engine.py"
$LogDir     = Join-Path (Split-Path $ScriptDir -Parent) "..\logs"
$LogFile    = Join-Path $LogDir "chi-wrapper.log"

# Garantir pasta de logs
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content $LogFile "[$Timestamp] Run-ChiEngine.ps1 iniciado"

try {
    $result = & $PythonExe $ChiScript 2>&1
    $result | ForEach-Object { Add-Content $LogFile "  $_" }
    $Timestamp2 = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $LogFile "[$Timestamp2] CHI Engine concluído com sucesso"
    Write-Host "[OK] CHI Engine executado às $Timestamp2"
}
catch {
    $ErrMsg = $_.Exception.Message
    $Timestamp3 = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $LogFile "[$Timestamp3] ERRO: $ErrMsg"
    Write-Host "[ERRO] $ErrMsg"
    exit 1
}
