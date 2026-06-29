# UMOE OS 8.0 - Limpeza inteligente de storage (HD)
# Regra: manter apenas o arquivo canonico + N versoes datadas por grupo.
# Nunca deleta arquivos canonicos (sem prefixo de data) nem arquivos nao-datados.
# Encoding: ASCII puro (sem acentos).
param(
    [switch]$DryRun,          # mostra o que seria deletado, sem deletar
    [int]$MantarDias = 7      # versoes datadas a manter por grupo
)

$LogFile = "C:\01 - UMOE\09 - IA\umoe-os-8\logs\storage-cleanup.log"

function Log($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Write-Host $line
    try { Add-Content -Path $LogFile -Value $line -Encoding UTF8 } catch {}
}

function Limpar-Pasta($pasta, $padrao, $manterN, $descricao) {
    # Agrupa arquivos datados (prefixo AAAAMMDD_ ou sufixo _AAAAMMDD_HHMMSS) por nome-base
    $arquivos = Get-ChildItem -Path $pasta -File -Filter $padrao -ErrorAction SilentlyContinue
    if (-not $arquivos) { return }

    # Grupos: chave = nome sem o segmento de data
    $grupos = @{}
    foreach ($f in $arquivos) {
        # Prefixo: 20260629_NomeArquivo.ext
        $base = $f.Name -replace '^\d{8}_', ''
        # Sufixo: NomeArquivo_20260629_132106.ext
        $base = $base -replace '_\d{8}_\d{6}(\.\w+)$', '$1'
        if (-not $grupos[$base]) { $grupos[$base] = @() }
        $grupos[$base] += $f
    }

    $totalDeletados = 0
    foreach ($base in $grupos.Keys) {
        $grupo = $grupos[$base] | Sort-Object LastWriteTime -Descending
        # Pula se todos sao o arquivo canonico (sem data no nome)
        $datados = $grupo | Where-Object { $_.Name -match '^\d{8}_|_\d{8}_\d{6}\.' }
        if (-not $datados -or $datados.Count -le $manterN) { continue }

        $manter  = $datados | Select-Object -First $manterN
        $deletar = $datados | Select-Object -Skip  $manterN

        foreach ($d in $deletar) {
            if ($DryRun) {
                Log "  [DRY] deletaria: $($d.FullName)"
            } else {
                try {
                    Remove-Item -LiteralPath $d.FullName -Force
                    Log "  DEL  $($d.Name) ($([Math]::Round($d.Length/1KB)) KB)"
                    $totalDeletados++
                } catch { Log "  ERRO ao deletar $($d.Name): $($_.Exception.Message)" }
            }
        }
    }
    if ($totalDeletados -gt 0 -or $DryRun) {
        Log "[$descricao] $totalDeletados arquivo(s) removido(s), $manterN retido(s) por grupo"
    }
}

Log "==== Inicio limpeza storage (manter=$MantarDias, dryrun=$DryRun) ===="

# 1. UMOE-INBOX - historico de e-mails baixados (prefixo AAAAMMDD_)
Limpar-Pasta "C:\01 - UMOE\09 - IA\UMOE-INBOX" "*.*" $MantarDias "UMOE-INBOX"

# 2. Planilhas - versoes datadas do Historico Diario, Pluviometrico etc.
Limpar-Pasta "C:\01 - UMOE\03 - Financeiro\Planilhas" "*.xlsx" 3 "Planilhas"

# 3. 99-SSoT - versoes datadas de Moagem Fabiano/Lerosa
Limpar-Pasta "C:\01 - UMOE\99 - SSoT" "*.xlsb" 2 "99-SSoT xlsb"

# 4. Dados-PBI/MANUT - JSONs grandes ja sao regenerados a cada pipeline
# Nao ha versoes datadas aqui (pipeline sobrescreve). Nenhuma acao necessaria.

Log "==== Fim limpeza storage ===="
