# UMOE OS 8.0 - PASSO 1 + PASSO 2: Descobrir tabelas e extrair dados PBI
# Credenciais solicitadas uma unica vez

Import-Module MicrosoftPowerBIMgmt -Force

$outDir = "C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Dados-PBI"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

$wsId     = "662a06b5-5579-4af6-b66a-7ac191a96674"
$datasets = [ordered]@{
    BASE = "06950719-48dc-403d-bd91-2e059cf1a25e"
    CST  = "a735ce0e-4234-42f8-bedd-5cbb07ce6364"
    CTRL = "4c81ea62-ef7f-4976-9aaa-bf7ab3727c0b"
}

Write-Host ""
Write-Host "======================================================="
Write-Host "  UMOE OS 8.0 | Descoberta + Extracao PBI"
Write-Host "======================================================="
Write-Host ""
$adminUser = Read-Host "  Email Power BI"
$adminPass = Read-Host "  Senha" -AsSecureString
$cred = New-Object System.Management.Automation.PSCredential($adminUser, $adminPass)
Connect-PowerBIServiceAccount -Credential $cred | Out-Null
Write-Host "  Conectado. Iniciando..."
Write-Host ""

# Funcao DAX generica
function Run-DAX($dsId, $query) {
    $body = @{
        queries = @(@{ query = $query })
        serializerSettings = @{ includeNulls = $true }
    } | ConvertTo-Json -Depth 10
    try {
        $r = Invoke-PowerBIRestMethod -Url "groups/$wsId/datasets/$dsId/executeQueries" -Method Post -Body $body | ConvertFrom-Json
        return $r.results[0].tables[0].rows
    } catch { return $null }
}

# ────────────────────────────────────────────────────────
# PASSO 1: Descobrir tabelas e colunas reais
# ────────────────────────────────────────────────────────
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  PASSO 1 - Mapeamento de tabelas"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

$estrutura = @{}

foreach ($nome in $datasets.Keys) {
    $dsId = $datasets[$nome]
    Write-Host ""
    Write-Host "  [$nome]"

    $tabelas = Run-DAX $dsId "EVALUATE SELECTCOLUMNS(INFO.TABLES(), `"ID`",[ID], `"Nome`",[Name], `"Hidden`",[IsHidden])"
    if (-not $tabelas) {
        Write-Host "    Sem acesso a INFO.TABLES"
        continue
    }

    $estrutura[$nome] = @{}
    $tabelasVisiveis = $tabelas | Where-Object { $_.'[Hidden]' -eq $false -and -not $_.'[Nome]'.StartsWith('$') -and -not $_.'[Nome]'.StartsWith('LocalDate') }

    foreach ($t in $tabelasVisiveis) {
        $tId   = $t.'[ID]'
        $tNome = $t.'[Nome]'

        $cols = Run-DAX $dsId "EVALUATE SELECTCOLUMNS(FILTER(INFO.COLUMNS(), [TableID] = $tId && NOT [IsHidden]), `"Col`",[ExplicitName], `"Tipo`",[ExplicitDataType])"

        $colNomes = @()
        if ($cols) { $colNomes = $cols | ForEach-Object { $_.'[Col]' } | Where-Object { $_ } }

        $estrutura[$nome][$tNome] = $colNomes
        Write-Host "    $tNome ($($colNomes.Count) colunas): $($colNomes -join ', ' | ForEach-Object { if ($_.Length -gt 80) { $_.Substring(0,80) + '...' } else { $_ } })"
    }
}

# Salvar estrutura
$estrutura | ConvertTo-Json -Depth 5 | Out-File "$outDir\ESTRUTURA_PBI.json" -Encoding UTF8
Write-Host ""
Write-Host "  Estrutura salva em ESTRUTURA_PBI.json"

# ────────────────────────────────────────────────────────
# PASSO 2: Extrair dados de cada tabela visivel
# ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  PASSO 2 - Extracao de dados"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

$resumo = @()

foreach ($nome in $estrutura.Keys) {
    $dsId = $datasets[$nome]
    Write-Host ""
    Write-Host "  [$nome]"

    foreach ($tabela in $estrutura[$nome].Keys) {
        $colunas = $estrutura[$nome][$tabela]
        if ($colunas.Count -eq 0) { continue }

        # Montar SELECT com colunas reais
        $selects = $colunas | ForEach-Object { "    `"$_`", '$tabela'[$_]" }
        $dax = "EVALUATE`nSELECTCOLUMNS( '$tabela',`n$($selects -join ",`n")`n)"

        $rows = Run-DAX $dsId $dax

        if ($rows -and $rows.Count -gt 0) {
            $arquivo = "${nome}_${tabela}" -replace '[^a-zA-Z0-9_]', '_'
            $rows | ConvertTo-Json -Depth 3 -Compress | Out-File "$outDir\$arquivo.json" -Encoding UTF8
            Write-Host "    $tabela`: $($rows.Count) linhas -> $arquivo.json"
            $resumo += [PSCustomObject]@{ Dataset=$nome; Tabela=$tabela; Linhas=$rows.Count; Arquivo="$arquivo.json" }
        } else {
            Write-Host "    $tabela`: vazia ou sem permissao"
        }
    }
}

# Salvar resumo
$resumo | ConvertTo-Json | Out-File "$outDir\RESUMO_EXTRACAO.json" -Encoding UTF8
$resumo | Format-Table -AutoSize

Write-Host ""
Write-Host "======================================================="
Write-Host "  CONCLUIDO!"
$totalLinhas = ($resumo | Measure-Object -Property Linhas -Sum).Sum
Write-Host "  $($resumo.Count) tabelas extraidas | $totalLinhas linhas totais"
Write-Host "  Dados em: $outDir"
Write-Host "======================================================="
Write-Host ""
pause
