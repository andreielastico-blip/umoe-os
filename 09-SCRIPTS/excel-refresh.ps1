# UMOE OS 8.0 - Atualiza (RefreshAll) uma planilha Excel e salva. Via Excel COM.
# Abre o arquivo, atualiza conexoes/consultas/tabelas dinamicas, recalcula e salva.
# Agendar no Agendador de Tarefas. Encoding: ASCII puro.
#
# Uso:  excel-refresh.ps1 -Arquivo "C:\caminho\planilha.xlsb"
param(
    [string]$Arquivo = "C:\01 - UMOE\Historico Umoe\Ranking UMOE.xlsb"
)

$LogFile = "C:\01 - UMOE\09 - IA\umoe-os-8\logs\excel-refresh.log"
function Log($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Write-Host $line
    try { Add-Content -Path $LogFile -Value $line -Encoding UTF8 } catch {}
}
if (-not (Test-Path (Split-Path $LogFile))) { New-Item -ItemType Directory -Path (Split-Path $LogFile) -Force | Out-Null }

Log "==== Refresh: $Arquivo ===="
if (-not (Test-Path $Arquivo)) { Log "ERRO: arquivo nao encontrado"; exit 1 }

$excel = $null; $wb = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AskToUpdateLinks = $false
    $excel.EnableEvents = $false

    # UpdateLinks=3 (atualiza todos os vinculos externos)
    $wb = $excel.Workbooks.Open($Arquivo, 3, $false)
    Log "Aberto. ReadOnly=$($wb.ReadOnly)"

    $wb.RefreshAll()
    # Aguarda consultas assincronas (Power Query) terminarem
    try { $excel.CalculateUntilAsyncQueriesDone() } catch {}
    Start-Sleep -Seconds 20
    try { $excel.CalculateUntilAsyncQueriesDone() } catch {}
    $excel.CalculateFull()
    Log "RefreshAll + recalculo concluidos"

    if ($wb.ReadOnly) {
        Log "AVISO: arquivo aberto somente-leitura (provavelmente em uso). NAO salvo."
    } else {
        $wb.Save()
        Log "Salvo com sucesso"
    }
} catch {
    Log "ERRO: $($_.Exception.Message)"
} finally {
    if ($wb)    { try { $wb.Close($false) } catch {} }
    if ($excel) { try { $excel.Quit() } catch {} }
    # Libera COM
    if ($wb)    { try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($wb) } catch {} }
    if ($excel) { try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } catch {} }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
Log "==== Fim refresh ===="

# ============================ AGENDAR ===============================
# Rode UMA vez (PowerShell normal) para criar a tarefa diaria as 10:00:
#
#   $acao    = New-ScheduledTaskAction -Execute "powershell.exe" `
#       -Argument '-NoProfile -ExecutionPolicy Bypass -File "C:\01 - UMOE\09 - IA\umoe-os-8\09-SCRIPTS\excel-refresh.ps1"'
#   $gatilho = New-ScheduledTaskTrigger -Daily -At 10:00
#   Register-ScheduledTask -TaskName "UMOE-Ranking-Refresh" -Action $acao -Trigger $gatilho `
#       -Description "Atualiza (RefreshAll) a planilha Ranking UMOE" -RunLevel Limited
# ====================================================================
