# UMOE OS 8.0 - Instala agendamento diario do Pipeline Master
# Roda pipeline completo + push GitHub toda segunda a sexta as 10:00

$TaskName   = "UMOE_Pipeline_Master"
$Python     = "C:\Users\andrei.elastico\AppData\Local\Programs\Python\Python312\python.exe"
$Script     = "C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\01-AGENTE-AUTONOMO\umoe-pipeline.py"
$WorkDir    = "C:\01 - UMOE\09 - IA\umoe-os-8"
$LogOut     = "C:\01 - UMOE\09 - IA\umoe-os-8\logs\pipeline-agendado.log"

$Action = New-ScheduledTaskAction `
    -Execute $Python `
    -Argument "`"$Script`"" `
    -WorkingDirectory $WorkDir

$Trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At "10:00AM"

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Tarefa anterior removida."
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "UMOE OS 8.0 - Pipeline BI automatico diario"

Write-Host ""
Write-Host "Tarefa '$TaskName' instalada com sucesso!"
Write-Host "Executa: Seg-Sex as 10:00"
Write-Host "Script:  $Script"
Write-Host "Log:     $LogOut"

# Teste imediato opcional
$resp = Read-Host "Executar pipeline agora para teste? (s/n)"
if ($resp -eq "s") {
    Write-Host "Executando pipeline..."
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 5
    Get-ScheduledTaskInfo -TaskName $TaskName | Select-Object LastRunTime, LastTaskResult, NextRunTime
}
