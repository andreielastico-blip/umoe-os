# UMOE OS 8.0 - Descobrir tabelas por nome + extrair dados PBI
# Usa TOPN(1) para testar nomes, depois extrai tudo sem INFO.TABLES()

Import-Module MicrosoftPowerBIMgmt -Force

$outDir = "C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Dados-PBI"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

$wsId = "662a06b5-5579-4af6-b66a-7ac191a96674"
$datasets = [ordered]@{
    BASE = "06950719-48dc-403d-bd91-2e059cf1a25e"
    CST  = "a735ce0e-4234-42f8-bedd-5cbb07ce6364"
    CTRL = "4c81ea62-ef7f-4976-9aaa-bf7ab3727c0b"
}

Write-Host ""
Write-Host "======================================================="
Write-Host "  UMOE OS 8.0 | Extracao PBI por descoberta de nomes"
Write-Host "======================================================="
$adminUser = Read-Host "  Email Power BI"
$adminPass = Read-Host "  Senha" -AsSecureString
$cred = New-Object System.Management.Automation.PSCredential($adminUser, $adminPass)
Connect-PowerBIServiceAccount -Credential $cred | Out-Null
Write-Host "  Conectado. Iniciando...`n"

# Nomes de tabelas candidatas por dataset (baseado nos nomes das paginas do relatorio)
$candidatos = @{
    BASE = @(
        # Producao / Log
        "fProducao","Producao","fPRD","PRD","Log","fLog","fAtividades","Atividades",
        "PRDParcial","LogPRD","fLogPRD","Colheita","fColheita",
        # Moagem
        "fMoagem","Moagem","fMoag","Moag",
        # ATR / Qualidade
        "fATR","ATR","fQualidade","Qualidade","MAtCH","fMAtCH","fAtr",
        # Chuva / Clima
        "fChuva","Chuva","fClima","Clima","fPrecipitacao","Precipitacao","fMeteo",
        # Disponibilidade
        "fDisponibilidade","Disponibilidade","fDM","DM","fDF",
        # Frentes / Frota
        "fFrente","Frente","Frentes","fFrota","Frota","fColhedora","Colhedora",
        # Estoque / Organizacao
        "fEstoque","Estoque","fLeira","Leira","Leiras","fOrg","ORG",
        # Plantio / Preparo
        "fPlantio","Plantio","fPreparo","Preparo","fMuda","Muda",
        # Qualidade campo
        "fQLD","QLD","fQualidadeCampo",
        # Agronomia / Pragas
        "fPraga","Praga","Pragas","fBroca","Broca","fCigarrinha","Cigarrinha",
        # Aderencia
        "fAderencia","Aderencia","fAdher","ADEREN",
        # Ordem de Corte
        "fOrdemCorte","OrdemCorte","fOC","OC","fOrdem","Ordem",
        # Dimensoes
        "dFazenda","Fazenda","Fazendas","dTalhao","Talhao","dVariedade","Variedade",
        "dCalendario","Calendario","dData","dDatas","Calendario",
        "dFrente","dEquipamento","Equipamento","dAmbiente","Ambiente",
        "dColhedora","dCaminhao","Caminhao"
    )
    CST = @(
        "fCusto","Custo","Custos","fOpex","Opex","fDRE","DRE",
        "fHeadcount","Headcount","fRH","RH","fFuncionario","Funcionario",
        "fInsumo","Insumo","Insumos","fFertilizante","Fertilizante",
        "fOrcamento","Orcamento","fBudget","Budget",
        "dCC","CentroCusto","dCentroCusto","fCC",
        "dCalendario","Calendario","dData","dDatas"
    )
    CTRL = @(
        "fOrdemCorte","OrdemCorte","fOC","OC",
        "fEstoque","Estoque","fSaldo","Saldo",
        "fPesagem","Pesagem","fPeso","fBalanca",
        "fDivergencia","Divergencia","fOS","OS","OrdemServico",
        "fEscala","Escala","fFuncionario","Funcionario",
        "fOrcamento","Orcamento","fBudget",
        "dCalendario","Calendario","dData",
        "dFazenda","Fazenda","dEquipamento"
    )
}

# Funcao: testar se tabela existe com TOPN(1)
function Test-Table($dsId, $tabela) {
    $body = @{
        queries = @(@{ query = "EVALUATE TOPN(1, '$tabela')" })
        serializerSettings = @{ includeNulls = $true }
    } | ConvertTo-Json -Depth 5
    try {
        $r = Invoke-PowerBIRestMethod -Url "groups/$wsId/datasets/$dsId/executeQueries" -Method Post -Body $body -ErrorAction Stop | ConvertFrom-Json
        $rows = $r.results[0].tables[0].rows
        return $rows  # retorna primeira linha (pode ser null se tabela vazia)
    } catch { return $false }
}

# Funcao: extrair tabela completa
function Get-TableData($dsId, $tabela) {
    $body = @{
        queries = @(@{ query = "EVALUATE '$tabela'" })
        serializerSettings = @{ includeNulls = $true }
    } | ConvertTo-Json -Depth 5
    try {
        $r = Invoke-PowerBIRestMethod -Url "groups/$wsId/datasets/$dsId/executeQueries" -Method Post -Body $body -ErrorAction Stop | ConvertFrom-Json
        return $r.results[0].tables[0].rows
    } catch { return $null }
}

$resumo  = @()
$estrutura = @{}

foreach ($dsNome in $datasets.Keys) {
    $dsId = $datasets[$dsNome]
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "  [$dsNome] Testando $($candidatos[$dsNome].Count) nomes de tabela..."
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    $tabelasEncontradas = @()
    $estrutura[$dsNome] = @{}

    foreach ($tabela in $candidatos[$dsNome]) {
        $teste = Test-Table $dsId $tabela
        if ($teste -ne $false) {
            # Tabela existe! Pegar colunas da primeira linha
            if ($teste -and $teste.Count -gt 0) {
                $colunas = ($teste[0] | Get-Member -MemberType NoteProperty).Name
            } else {
                $colunas = @("(vazia)")
            }
            Write-Host "  ENCONTRADA: $tabela ($($colunas.Count) colunas)"
            $tabelasEncontradas += $tabela
            $estrutura[$dsNome][$tabela] = $colunas
        }
    }

    Write-Host "  -> $($tabelasEncontradas.Count) tabelas encontradas`n"

    # Extrair dados de cada tabela encontrada
    foreach ($tabela in $tabelasEncontradas) {
        Write-Host "  Extraindo: $tabela..."
        $rows = Get-TableData $dsId $tabela

        if ($rows -and $rows.Count -gt 0) {
            # Limpar nomes de coluna (Power BI retorna "[NomeTabela]NomeColuna")
            $rowsLimpos = $rows | ForEach-Object {
                $obj = @{}
                $_.PSObject.Properties | ForEach-Object {
                    $colNome = $_.Name -replace "^\[.*?\]", "" -replace "^\w+\[", "" -replace "\]$", ""
                    $obj[$colNome] = $_.Value
                }
                [PSCustomObject]$obj
            }
            $arquivo = "${dsNome}_${tabela}" -replace '[^a-zA-Z0-9_]', '_'
            $rowsLimpos | ConvertTo-Json -Depth 3 -Compress | Out-File "$outDir\$arquivo.json" -Encoding UTF8
            Write-Host "    OK: $($rows.Count) linhas -> $arquivo.json"
            $resumo += [PSCustomObject]@{ Dataset=$dsNome; Tabela=$tabela; Linhas=$rows.Count; Arquivo="$arquivo.json" }
        } elseif ($rows -ne $null) {
            Write-Host "    OK: tabela vazia (0 linhas)"
        } else {
            Write-Host "    ERRO ao extrair dados completos"
        }
    }
    Write-Host ""
}

# Salvar estrutura e resumo
$estrutura | ConvertTo-Json -Depth 5 | Out-File "$outDir\ESTRUTURA_PBI.json" -Encoding UTF8
$resumo    | ConvertTo-Json           | Out-File "$outDir\RESUMO_EXTRACAO.json" -Encoding UTF8

Write-Host "======================================================="
Write-Host "  CONCLUIDO!"
$totalLinhas = ($resumo | Measure-Object -Property Linhas -Sum).Sum
Write-Host "  $($resumo.Count) tabelas extraidas | $totalLinhas linhas totais"
Write-Host ""
$resumo | Format-Table Dataset, Tabela, Linhas -AutoSize
Write-Host "  Dados em: $outDir"
Write-Host "======================================================="
pause
