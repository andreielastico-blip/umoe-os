# UMOE OS 8.0 - Busca diaria de anexos no e-mail corporativo (Outlook desktop / COM)
# Salva anexos que casam com as REGRAS em UMOE-INBOX. Roda como o usuario logado.
# Agendar no Agendador de Tarefas (ver final do arquivo). Encoding: ASCII puro.

# ============================ CONFIG =================================
$InboxDir = "C:\01 - UMOE\09 - IA\UMOE-INBOX"
$LogFile  = "C:\01 - UMOE\09 - IA\umoe-os-8\logs\email-fetch.log"
$DaysBack = 2          # janela de e-mails a varrer (dias). 2 = hoje + ontem (margem)
$PrefixarData = $true  # salva como AAAAMMDD_nomeoriginal (mantem historico, evita sobrescrever)

# REGRAS: um e-mail casa se (De contem) E (Assunto contem). Vazio = ignora aquele criterio.
# Para cada e-mail que casa, salva os anexos cujo nome casa com AnexoPattern (curinga -like).
# >>> PREENCHA/AJUSTE conforme seus e-mails. Exemplos abaixo:
$Regras = @(
    @{ Nome = "Solinftec diario"; DeContains = "solinftec";   AssuntoContains = "";          AnexoPattern = "*.csv"  }
    @{ Nome = "Boletim ATR";      DeContains = "";             AssuntoContains = "ATR";       AnexoPattern = "*.xlsx" }
    @{ Nome = "Exemplo PDF";      DeContains = "fornecedor.com"; AssuntoContains = "diario";  AnexoPattern = "*.pdf"  }
)
# ====================================================================

function Log($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Write-Host $line
    try { Add-Content -Path $LogFile -Value $line -Encoding UTF8 } catch {}
}

# Garante pastas
foreach ($d in @($InboxDir, (Split-Path $LogFile))) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

Log "==== Inicio busca de anexos (janela $DaysBack dia(s)) ===="

try {
    $ol = New-Object -ComObject Outlook.Application
    $ns = $ol.GetNamespace("MAPI")
    $inbox = $ns.GetDefaultFolder(6)   # 6 = olFolderInbox
} catch {
    Log "ERRO ao conectar ao Outlook: $($_.Exception.Message)"
    exit 1
}

$cutoff = (Get-Date).AddDays(-$DaysBack)
$items = $inbox.Items
$items.Sort("[ReceivedTime]", $true)
# Filtro DASL por data (formato US obrigatorio no Restrict)
$filtro = "[ReceivedTime] >= '" + $cutoff.ToString("MM/dd/yyyy HH:mm") + "'"
try { $items = $items.Restrict($filtro) } catch { Log "Aviso: Restrict por data falhou, varrendo tudo" }

$totSalvos = 0; $totCasou = 0
foreach ($mail in $items) {
    if ($mail.Class -ne 43) { continue }   # 43 = olMail
    $assunto = [string]$mail.Subject
    $de = ""
    try { $de = [string]$mail.SenderEmailAddress } catch {}
    if (-not $de) { try { $de = [string]$mail.SenderName } catch {} }

    foreach ($r in $Regras) {
        $okDe  = (-not $r.DeContains)      -or ($de      -match [regex]::Escape($r.DeContains))
        $okAss = (-not $r.AssuntoContains) -or ($assunto -match [regex]::Escape($r.AssuntoContains))
        if (-not ($okDe -and $okAss)) { continue }
        $totCasou++
        foreach ($att in $mail.Attachments) {
            $nome = [string]$att.FileName
            if ($nome -notlike $r.AnexoPattern) { continue }
            $alvo = if ($PrefixarData) {
                Join-Path $InboxDir (("{0}_{1}" -f $mail.ReceivedTime.ToString("yyyyMMdd"), $nome))
            } else { Join-Path $InboxDir $nome }
            if (Test-Path $alvo) { Log "  skip (ja existe): $(Split-Path $alvo -Leaf)"; continue }
            try {
                $att.SaveAsFile($alvo)
                Log "  OK [$($r.Nome)] $de | $assunto -> $(Split-Path $alvo -Leaf)"
                $totSalvos++
            } catch { Log "  ERRO ao salvar $nome : $($_.Exception.Message)" }
        }
    }
}

Log "==== Fim. E-mails que casaram: $totCasou | anexos salvos: $totSalvos ===="

# ============================ AGENDAR ===============================
# Rode UMA vez (PowerShell normal) para criar a tarefa diaria as 07:00:
#
#   $acao    = New-ScheduledTaskAction -Execute "powershell.exe" `
#       -Argument '-NoProfile -ExecutionPolicy Bypass -File "C:\01 - UMOE\09 - IA\umoe-os-8\09-SCRIPTS\email-fetch-anexos.ps1"'
#   $gatilho = New-ScheduledTaskTrigger -Daily -At 07:00
#   Register-ScheduledTask -TaskName "UMOE-Email-Fetch" -Action $acao -Trigger $gatilho `
#       -Description "Baixa anexos do e-mail UMOE para UMOE-INBOX" -RunLevel Limited
#
# Conferir:  Get-ScheduledTask -TaskName "UMOE-Email-Fetch"
# Remover:   Unregister-ScheduledTask -TaskName "UMOE-Email-Fetch" -Confirm:$false
# ====================================================================
