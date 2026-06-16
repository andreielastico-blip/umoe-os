# UMOE OS 8.0 - Busca expandida de tabelas PBI
# Usa padroes reais descobertos: CD_, DE_, DT_, QT_ -> sistema SIGRA/SAP

Import-Module MicrosoftPowerBIMgmt -Force

$outDir = "C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Dados-PBI"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

$wsId = "662a06b5-5579-4af6-b66a-7ac191a96674"
$datasets = [ordered]@{
    BASE = "06950719-48dc-403d-bd91-2e059cf1a25e"
    CST  = "a735ce0e-4234-42f8-bedd-5cbb07ce6364"
    CTRL = "4c81ea62-ef7f-4976-9aaa-bf7ab3727c0b"
}

Write-Host "======================================================="
Write-Host "  UMOE OS 8.0 | Busca expandida de tabelas"
Write-Host "======================================================="
$adminUser = Read-Host "  Email Power BI"
$adminPass = Read-Host "  Senha" -AsSecureString
$cred = New-Object System.Management.Automation.PSCredential($adminUser, $adminPass)
Connect-PowerBIServiceAccount -Credential $cred | Out-Null
Write-Host "  Conectado.`n"

# Candidatos expandidos com padroes reais
$candidatos = @{
    BASE = @(
        # --- Producao / Log (paginas LOG_PRD*) ---
        "Log","LOG","LogPRD","LOG_PRD","Log_PRD",
        "LogProducao","Log_Producao","LOG_PRODUCAO",
        "Producao","PRODUCAO","PRD","Prd",
        "Apontamento","APONTAMENTO","Apontamentos",
        "LogPRDParcial","LogParcial","PRDParcial",
        "LogPRDHora","PRDHora","LogHora",
        "LogPRDCargas","PRDCargas","Cargas","CARGAS",
        "LogPRDAberto","PRDAberto","LogAberto",
        "LogPRDTurno","PRDTurno","Turno","TURNO",
        "Colheita","COLHEITA","Atividade","ATIVIDADE",
        "Lancamento","LANCAMENTO","Lancamentos",
        # --- Moagem (paginas MOAG_*) ---
        "Moagem","MOAGEM","Moag","MOAG",
        "MoagemEficiencia","Eficiencia","EFICIENCIA",
        "MoagemProducao","MoagemDia",
        "OrdemCorte","ORDEM_CORTE","OC","OC_CORTE",
        "MoagemAreas","Areas","AREAS",
        "MoagemFrentes","Frentes","FRENTES",
        "MoagemProjecao","Projecao","PROJECAO",
        # --- Qualidade Mineral/Vegetal (MOAG_QLD_*) ---
        "Qualidade","QUALIDADE","QLD","QLD_MIN","QLD_VEG",
        "QualidadeMineral","QualidadeVegetal","QualidadePerdas",
        "Perdas","PERDAS","Impureza","IMPUREZA",
        "Broca","BROCA","PerdaBroca",
        # --- ATR / MAtCH (paginas MAtCH_*) ---
        "ATR","Atr","atr",
        "Match","MATCH","MAtCH",
        "MatchATR","Match_ATR","ATR_Match",
        "AnaliseATR","AnaliseAtr","Analise",
        "TCH","tch","TCHReal",
        "TAH","tah","TAHReal",
        "Maturador","MATURADOR","PreAnalise","PRE_ANALISE",
        "AderenMaturador","AderenciaMaturador",
        "ATRSemanas","ATR_Semanas","SemanaATR",
        "TAHVariedade","TAHEstagio",
        # --- Preparo (paginas PREP_*) ---
        "Preparo",  # JA ENCONTRADA
        "PrepFazendas","Prep_Fazendas",
        "PrepProjecao","Prep_Projecao",
        # --- Plantio (paginas PLANT*) ---
        "Plantio","PLANTIO","Plant","PLANT",
        "PlantioApontamento","PlantaoMudas",
        "Mudas","MUDAS","Muda","MUDA",
        "PlantioProjecao","PlantioOC",
        "OCMuda","OC_MUDA",
        # --- Qualidade Campo (paginas QLD_*) ---
        "QLD_PP","QLD_Preparo","QLD_Plantio",
        "QLD_Muda","QLD_Tratos","QLD_Apontamentos",
        "QualidadePreparo","QualidadePlantio","QualidadeTratos",
        # --- Agronomia / Pragas (paginas AGRONO_*) ---
        "Praga","PRAGA","Pragas","PRAGAS",
        "Cigarrinha","CIGARRINHA",
        "Migdolus","MIGDOLUS",
        "Sphenophorus","SPHENOPHORUS",
        "EstriaVermelha","ESTRIA_VERMELHA",
        "OutrasPragas","OUTRAS_PRAGAS",
        "Agronomia","AGRONOMIA",
        # --- Aderencia (paginas ADEREN_*) ---
        "Aderencia","ADERENCIA","Aderen","ADEREN",
        "AderenciaInset","AderenciaFoliar","AderenciaHerbicida",
        "AderenciaAduba","AderenciaFertirri","AderenciaIrriga",
        "AderenciaCorretivo","AderenciaSaldo",
        "Herbi","Herbicida","HERBICIDA","Aduba","ADUBACAO",
        "Fertirri","FERTIRRIGACAO","Corretivo","CORRETIVO",
        "IrrigaSalva","IRRIGA_SALVA",
        # --- Controle (paginas CTRL_*) ---
        "Chuva",  # JA ENCONTRADA
        "Escala","ESCALA",
        "PainelSolar","PAINEL_SOLAR","Solar",
        "OrdemServico","OS","O_S","ORDEM_SERVICO",
        # --- Dimensoes ---
        "Fazenda","FAZENDA","Fazendas",
        "Talhao","TALHAO","Talhoes",
        "Variedade","VARIEDADE","Variedades",
        "Ambiente","AMBIENTE","Ambientes",
        "Frente","FRENTE",
        "Equipamento","EQUIPAMENTO","Colhedora","COLHEDORA",
        "Caminhao","CAMINHAO","Caminhoes",
        "Calendario","CALENDARIO","dCalendario","dData","Data",
        "Safra","SAFRA","Safras","dSafra",
        "Corte","CORTE","Ciclo","CICLO",
        "Funcionario","FUNCIONARIO","Operador","OPERADOR"
    )
    CST = @(
        # Paginas: R-Headcount, R-Custos, R-Insumos
        "Custo","CUSTO","Custos","CUSTOS",
        "CustoCC","Custo_CC","CC","CUSTO_CC",
        "R_Custos","R-Custos","RCustos",
        "Headcount","HEADCOUNT","Head_Count",
        "R_Headcount","R-Headcount","RHeadcount",
        "RH","Funcionario","FUNCIONARIO","Colaborador",
        "Insumo","INSUMO","Insumos","INSUMOS",
        "R_Insumos","R-Insumos","RInsumos",
        "Fertilizante","FERTILIZANTE","Defensivo","DEFENSIVO",
        "Produto","PRODUTO","Material","MATERIAL",
        "Orcamento","ORCAMENTO","Budget","BUDGET",
        "Lancamento","LANCAMENTO","Nota","NOTA",
        "CentroCusto","CENTRO_CUSTO","DCC","dCC",
        "CCusto","Centro_Custo",
        "Calendario","CALENDARIO","dData","Data","Safra",
        "Fazenda","FAZENDA","Frente","FRENTE"
    )
    CTRL = @(
        # Paginas: CTRL_ESTOQ_SALDO_POS, CTRL_ORDEM_CORTE, CTRL_OC_FORNEC
        # CTRL_PESAGEM_EQ_DIVERG, CTRL_FUNC_SEM_ESCALA, CTRL_FUNC_DIV
        # CTRL_OS_DOSE, CTRL_ORCAMENTO
        "Estoque","ESTOQUE","EstoqueSaldo","ESTOQUE_SALDO",
        "Saldo","SALDO","SaldoPos","SALDO_POS",
        "OrdemCorte","ORDEM_CORTE","OC","OC_CORTE",
        "OC_Fornec","OCFornec","Fornecedor","FORNECEDOR",
        "Pesagem","PESAGEM","Pesagem_Diverg","PesagemDiverg",
        "Divergencia","DIVERGENCIA","PesoDiverg",
        "Funcionario","FUNCIONARIO","Func","FUNC",
        "FuncSemEscala","Func_Escala","Escala","ESCALA",
        "FuncDiv","Func_Div",
        "OS","OrdemServico","ORDEM_SERVICO","OS_Dose","OsDose",
        "Dose","DOSE","Aplicacao","APLICACAO",
        "Orcamento","ORCAMENTO","Budget",
        "Calendario","CALENDARIO","dData","Data",
        "Fazenda","FAZENDA","Equipamento","EQUIPAMENTO",
        "Produto","PRODUTO","Material","MATERIAL",
        "Insumo","INSUMO"
    )
}

function Test-Table($dsId, $tabela) {
    $body = @{
        queries = @(@{ query = "EVALUATE TOPN(1, '$tabela')" })
        serializerSettings = @{ includeNulls = $true }
    } | ConvertTo-Json -Depth 5
    try {
        $r = Invoke-PowerBIRestMethod -Url "groups/$wsId/datasets/$dsId/executeQueries" -Method Post -Body $body -ErrorAction Stop | ConvertFrom-Json
        return $true
    } catch { return $false }
}

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

$resumo = @()

foreach ($dsNome in $datasets.Keys) {
    $dsId = $datasets[$dsNome]
    $lista = $candidatos[$dsNome] | Sort-Object -Unique
    Write-Host "[$dsNome] Testando $($lista.Count) nomes..."

    $encontradas = @()
    foreach ($tabela in $lista) {
        if (Test-Table $dsId $tabela) {
            Write-Host "  ACHEI: $tabela"
            $encontradas += $tabela
        }
    }

    Write-Host "  -> $($encontradas.Count) tabelas encontradas. Extraindo...`n"

    foreach ($tabela in $encontradas) {
        # Pular as que ja existem
        $arquivo = "${dsNome}_${tabela}" -replace '[^a-zA-Z0-9_]','_'
        if (Test-Path "$outDir\$arquivo.json") {
            Write-Host "  SKIP (ja existe): $tabela"
            continue
        }
        $rows = Get-TableData $dsId $tabela
        if ($rows -and $rows.Count -gt 0) {
            $rows | ConvertTo-Json -Depth 3 -Compress | Out-File "$outDir\$arquivo.json" -Encoding UTF8
            Write-Host "  OK: $tabela -> $($rows.Count) linhas -> $arquivo.json"
            $resumo += [PSCustomObject]@{ Dataset=$dsNome; Tabela=$tabela; Linhas=$rows.Count }
        } elseif ($rows -ne $null) {
            Write-Host "  VAZIA: $tabela"
            $resumo += [PSCustomObject]@{ Dataset=$dsNome; Tabela=$tabela; Linhas=0 }
        }
    }
    Write-Host ""
}

Write-Host "======================================================="
Write-Host "  CONCLUIDO!"
$total = ($resumo | Measure-Object -Property Linhas -Sum).Sum
Write-Host "  $($resumo.Count) tabelas novas | $total linhas"
$resumo | Format-Table Dataset, Tabela, Linhas -AutoSize
Write-Host "======================================================="
pause
