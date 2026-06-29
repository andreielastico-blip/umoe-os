# UMOE OS 8.0 - Busca diaria de anexos no e-mail corporativo (Outlook desktop / COM)
# Salva anexos que casam com as REGRAS em UMOE-INBOX. Roda como o usuario logado.
# Agendar no Agendador de Tarefas (ver final do arquivo). Encoding: ASCII puro.
#
# MODO DESCOBERTA: rode com  -Listar  para LISTAR (sem baixar) os e-mails com
# anexo dos ultimos N dias (data | remetente | assunto | anexos). Use a saida
# para montar as REGRAS. Aumente a janela com  -Dias 7 .
param(
    [switch]$Listar,
    [int]$Dias = 0,
    [switch]$NoPipeline   # nao encadear o pipeline ao final
)

# ============================ CONFIG =================================
$InboxDir = "C:\01 - UMOE\09 - IA\UMOE-INBOX"
$LogFile  = "C:\01 - UMOE\09 - IA\umoe-os-8\logs\email-fetch.log"
$DaysBack = 2          # janela de e-mails a varrer (dias). 2 = hoje + ontem (margem)
if ($Dias -gt 0) { $DaysBack = $Dias }   # override pela linha de comando (-Dias N)
$PrefixarData = $true  # salva como AAAAMMDD_nomeoriginal (mantem historico, evita sobrescrever)

# REGRAS: um e-mail casa se (De contem) OU (Assunto contem). Vazio = ignora aquele criterio.
# Para cada e-mail que casa, salva os anexos cujo nome casa com AnexoPattern (curinga -like).
# DeContains e AssuntoContains: basta UM dos dois casar (OR entre contas/assuntos).
# AssuntoOu: lista adicional de assuntos alternativos (OR).
$Regras = @(
    # Historico Diario Safras (Industrial - ATR/Moagem real)  [FONTE CANONICA]
    @{ Nome = "Hist Diario Safras";    AssuntoContains = "Safras 2009";     AnexoPattern = "*Hist*Safras*.xlsx"    }
    @{ Nome = "Hist Diario Safras v2"; AssuntoContains = "Historico Diario"; AnexoPattern = "*Hist*Safras*.xlsx"   }
    @{ Nome = "Hist Diario Safras v3"; AssuntoContains = "Boletim Industrial"; AnexoPattern = "*Hist*Safras*.xlsx" }

    # Moagem por Frente - Fabiano (Frente 27 / fornecedor)
    @{ Nome = "Moagem Fabiano";        AssuntoContains = "Moagem Fabiano";  AnexoPattern = "*Moagem*Fabiano*.xlsb" }
    @{ Nome = "Moagem Fabiano v2";     AssuntoContains = "SF2026";          AnexoPattern = "*Moagem*Fabiano*.xlsb" }
    @{ Nome = "Moagem Fabiano v3";     AssuntoContains = "Fabiano";         AnexoPattern = "*Moagem*Fabiano*.xlsb" }

    # Moagem por Frente - Lerosa (Frente 10 / fornecedor)
    @{ Nome = "Moagem Lerosa";         AssuntoContains = "Moagem Lerosa";   AnexoPattern = "*Moagem*Lerosa*.xlsb"  }
    @{ Nome = "Moagem Lerosa v2";      AssuntoContains = "SF2026";          AnexoPattern = "*Moagem*Lerosa*.xlsb"  }
    @{ Nome = "Moagem Lerosa v3";      AssuntoContains = "Lerosa";          AnexoPattern = "*Moagem*Lerosa*.xlsb"  }

    # RSO - Relatorio Semanal Operacional (Meta/Plano)
    @{ Nome = "RSO Semanal";           AssuntoContains = "RSO";             AnexoPattern = "RSO*.pptx"             }
    @{ Nome = "RSO Semanal v2";        AssuntoContains = "Relatorio Semanal"; AnexoPattern = "RSO*.pptx"           }

    # Indice Pluviometrico (chuva - fonte oficial)
    @{ Nome = "Indice Pluviometrico";  AssuntoContains = "Pluviom";         AnexoPattern = "*Pluviometrico*.xlsx"  }

    # Relatorio Industrial e Aguas (PDF)
    @{ Nome = "Rel Industrial";        AssuntoContains = "Industrial e";    AnexoPattern = "Relat*.pdf"            }

    # Previsao Climatica Alvean (PNG diario - caixa Fabio)
    @{ Nome = "Alvean Clima";          AssuntoContains = "Previsao Climatica"; AnexoPattern = "MillWeatherForecast_*.png" }
)

# DISTRIBUICAO: apos baixar, copia o arquivo mais recente que casa Pattern para
# DestDir sobrescrevendo a versao "atual" (pipeline le sempre o nome sem data).
# DestNome: se vazio, usa o nome original sem prefixo AAAAMMDD_
$Distribuir = @(
    @{ Pattern = "*Hist*Di*Safras*.xlsx";        DestDir = "C:\01 - UMOE\03 - Financeiro\Planilhas"; DestNome = "Historico Diario Safras.xlsx" }
    @{ Pattern = "*Indice*Pluviometrico*.xlsx";  DestDir = "C:\01 - UMOE\03 - Financeiro\Planilhas"; DestNome = "" }
    @{ Pattern = "*Moagem*Fabiano*.xlsb";        DestDir = "C:\01 - UMOE\99 - SSoT";                 DestNome = "SF2026 - Moagem Fabiano.xlsb" }
    @{ Pattern = "*Moagem*Lerosa*.xlsb";         DestDir = "C:\01 - UMOE\99 - SSoT";                 DestNome = "SF2026 - Moagem Lerosa.xlsb"  }
    @{ Pattern = "RSO*.pptx";                    DestDir = "C:\01 - UMOE\05 - Relatorios\Apresentacoes"; DestNome = "" }
    @{ Pattern = "MillWeatherForecast_*.png";    DestDir = "C:\01 - UMOE\09 - IA\UMOE-INBOX\Plano Diretor"; DestNome = "Alvean_Clima_HOJE.png" }
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

# Coleta recursiva de todas as pastas de e-mail (todas as contas/stores)
function Get-TodasPastas($folder, $caminho) {
    $lista = @()
    foreach ($sub in $folder.Folders) {
        $p = "$caminho\$($sub.Name)"
        $lista += [PSCustomObject]@{ Folder = $sub; Path = $p }
        $lista += Get-TodasPastas $sub $p
    }
    return $lista
}

# Retorna os itens de e-mail de uma pasta recebidos depois do cutoff.
# Filtra no PowerShell (a prova de locale) em vez de usar Restrict por data.
function Get-MailRecentes($folder, $cutoff) {
    $res = @()
    $it = $null
    try { $it = $folder.Items } catch { return $res }
    try { $it.Sort("[ReceivedTime]", $true) } catch {}   # mais novos primeiro
    try {
        foreach ($m in $it) {
            $rt = $null; try { $rt = $m.ReceivedTime } catch {}
            if ($rt -ne $null -and $rt -lt $cutoff) { break }   # ordenado desc: resto e mais antigo
            if ($m.Class -eq 43) { $res += $m }                 # 43 = olMail
        }
    } catch {}   # erro de RPC/COM numa pasta nao aborta o resto da varredura
    return $res
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

# Diagnostico: quais contas/caixas estao no perfil e qual e a padrao (usada no download)
Log "Contas configuradas no Outlook:"
try { foreach ($acc in $ns.Accounts) { Log ("  CONTA: {0} <{1}>" -f $acc.DisplayName, $acc.SmtpAddress) } } catch { Log "  (nao foi possivel listar Accounts)" }
Log "Caixas (stores) acessiveis:"
try { foreach ($st in $ns.Stores) { Log ("  STORE: {0}" -f $st.DisplayName) } } catch {}
try { Log ("Caixa de Entrada PADRAO (usada no download): {0}" -f $inbox.Store.DisplayName) } catch {}

$cutoff = (Get-Date).AddDays(-$DaysBack)

# ---- MODO DESCOBERTA: varre TODAS as pastas/contas e lista anexos, depois sai ----
if ($Listar) {
    Log "MODO DESCOBERTA - varrendo todas as pastas/contas (janela $DaysBack dia(s)):"
    $pastas = @()
    foreach ($store in $ns.Folders) { $pastas += Get-TodasPastas $store $store.Name }
    Log "Pastas a varrer: $($pastas.Count)"
    $n = 0
    foreach ($pf in $pastas) {
        foreach ($mail in (Get-MailRecentes $pf.Folder $cutoff)) {
            if ($mail.Attachments.Count -lt 1) { continue }
            $de = ""; try { $de = [string]$mail.SenderEmailAddress } catch {}
            if (-not $de) { try { $de = [string]$mail.SenderName } catch {} }
            $anexos = @(); foreach ($a in $mail.Attachments) { $anexos += [string]$a.FileName }
            $dt = $mail.ReceivedTime.ToString("yyyy-MM-dd HH:mm")
            Log ("  [{0}] {1} | DE: {2} | ASSUNTO: {3} | ANEXOS: {4}" -f $pf.Path, $dt, $de, $mail.Subject, ($anexos -join ", "))
            $n++
        }
    }
    Log "Total de e-mails com anexo: $n"
    exit 0
}
# ------------------------------------------------------------------------

# Download: varre TODAS as subpastas da SUA conta padrao (ignora caixas de colegas)
$raiz = $inbox.Store.GetRootFolder()
$pastasConta = @([PSCustomObject]@{ Folder = $raiz; Path = $raiz.Name })
$pastasConta += Get-TodasPastas $raiz $raiz.Name
Log "Varrendo $($pastasConta.Count) pasta(s) da conta: $($inbox.Store.DisplayName)"

$totSalvos = 0; $totCasou = 0
foreach ($pf in $pastasConta) {
  foreach ($mail in (Get-MailRecentes $pf.Folder $cutoff)) {
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
}

Log "==== Fim busca. E-mails que casaram: $totCasou | anexos salvos: $totSalvos ===="

# ---- DISTRIBUICAO: leva os arquivos baixados para onde o pipeline le ----
foreach ($d in $Distribuir) {
    $cand = Get-ChildItem -Path $InboxDir -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like $d.Pattern } |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $cand) { Log "  distribuir: nenhum arquivo casa '$($d.Pattern)'"; continue }
    if (-not (Test-Path $d.DestDir)) { New-Item -ItemType Directory -Path $d.DestDir -Force | Out-Null }
    # DestNome fixo ou nome original sem prefixo AAAAMMDD_
    if ($d.DestNome) {
        $nomeFinal = $d.DestNome
    } else {
        $nomeFinal = $cand.Name -replace '^\d{8}_', ''
    }
    $dest = Join-Path $d.DestDir $nomeFinal
    try {
        Copy-Item -LiteralPath $cand.FullName -Destination $dest -Force
        Log "  distribuido: $($cand.Name) -> $dest"
    } catch { Log "  ERRO distribuir $($cand.Name): $($_.Exception.Message)" }
}

# ---- ENCADEIA O PIPELINE (CHI/Clima/BI/Moagem + git push) ----
if (-not $NoPipeline) {
    $pipeline = "C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\01-AGENTE-AUTONOMO\umoe-pipeline.py"
    if (Test-Path $pipeline) {
        Log "Encadeando pipeline: umoe-pipeline.py"
        try {
            python -X utf8 "$pipeline" 2>&1 | ForEach-Object { Log "  [pipeline] $_" }
            Log "Pipeline finalizado (codigo $LASTEXITCODE)"
        } catch { Log "ERRO ao rodar pipeline: $($_.Exception.Message)" }
    } else {
        Log "Pipeline nao encontrado: $pipeline"
    }
} else {
    Log "Pipeline pulado (-NoPipeline)"
}
Log "==== Fim total ===="

# ============================ AGENDAR ===============================
# Rode UMA vez (PowerShell normal) para criar a tarefa diaria as 09:00:
#
#   $acao    = New-ScheduledTaskAction -Execute "powershell.exe" `
#       -Argument '-NoProfile -ExecutionPolicy Bypass -File "C:\01 - UMOE\09 - IA\umoe-os-8\09-SCRIPTS\email-fetch-anexos.ps1"'
#   $gatilho = New-ScheduledTaskTrigger -Daily -At 09:00
#   Register-ScheduledTask -TaskName "UMOE-Email-Fetch" -Action $acao -Trigger $gatilho `
#       -Description "Baixa anexos do e-mail UMOE para UMOE-INBOX" -RunLevel Limited
#
# Conferir:  Get-ScheduledTask -TaskName "UMOE-Email-Fetch"
# Remover:   Unregister-ScheduledTask -TaskName "UMOE-Email-Fetch" -Confirm:$false
# ====================================================================
