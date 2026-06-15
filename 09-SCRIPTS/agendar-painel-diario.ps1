# agendar-painel-diario.ps1
# Registra tarefa diaria no Windows Task Scheduler para executar painel-engine.py as 06:00
# Sem acentos neste arquivo conforme regra UMOE

$TaskName   = "UMOE-PainelDiario"
$ScriptPath = "C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\01-AGENTE-AUTONOMO\painel-engine.py"
$PythonExe  = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $PythonExe) {
    Write-Error "Python nao encontrado no PATH. Instale Python e tente novamente."
    exit 1
}

Write-Host "Python encontrado: $PythonExe"

# Remove tarefa existente se houver
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Tarefa anterior removida: $TaskName"
}

# Define a acao
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory "C:\01 - UMOE\09 - IA\umoe-os-8"

# Define o gatilho diario as 06:00
$Trigger = New-ScheduledTaskTrigger -Daily -At "06:00"

# Define configuracoes
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# Define o principal (usuario atual)
$Principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

# Registra a tarefa
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "UMOE OS 8.0 - Painel Executivo Agricola atualizado diariamente as 06:00" `
    -Force

Write-Host ""
Write-Host "Tarefa agendada com sucesso!"
Write-Host "  Nome:    $TaskName"
Write-Host "  Horario: 06:00 diariamente"
Write-Host "  Script:  $ScriptPath"
Write-Host ""
Write-Host "Para verificar: Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "Para executar agora: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Para remover: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
