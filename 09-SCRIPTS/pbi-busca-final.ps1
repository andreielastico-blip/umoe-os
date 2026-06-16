# UMOE OS 8.0 - Busca final: nomes exatos das paginas dos relatorios
# Padrao descoberto: Func_Div vem de CTRL_FUNC_DIV
# Regra: remove prefixo de modulo (LOG_, MOAG_, MAtCH_, etc.) -> nome da tabela

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
Write-Host "  UMOE OS 8.0 | Busca final por nome de pagina"
Write-Host "======================================================="
$adminUser = Read-Host "  Email Power BI"
$adminPass = Read-Host "  Senha" -AsSecureString
$cred = New-Object System.Management.Automation.PSCredential($adminUser, $adminPass)
Connect-PowerBIServiceAccount -Credential $cred | Out-Null
Write-Host "  Conectado.`n"

# Candidatos derivados DIRETAMENTE dos nomes das paginas dos 3 relatorios
# Regra: remover prefixo modulo (LOG_, MOAG_, MAtCH_, PREP_, PLANT_, QLD_, AGRONO_, ADEREN_, CTRL_, ORG_)
# E tambem tentar o nome completo da pagina

$candidatos = @{
    BASE = @(
        # Paginas LOG_PRD*
        "PRDParcial","PRD_Parcial","LogPRDParcial",
        "PRDParcialTurno","PRD_Parcial_Turno",
        "PRDParcialFazenda","PRD_Parcial_Fazenda",
        "PRDAberto","PRD_Aberto","LogPRDAberto",
        "PRDHora","PRD_Hora","LogPRDHora",
        "PRDCargas","PRD_Cargas","LogPRDCargas",
        # Paginas ORG_
        "Estoque","Leiras","ORG_Estoque","ORG_Leiras",
        # Paginas MOAG_
        "Eficiencia","Producao","PRDDia","PRD_Dia",
        "Frentes","Projecao",
        "QLD_Mineral","QLD_Vegetal","QLD_Perdas","QLD_Broca",
        "OrdemCorte","Ordem_Corte","Areas",
        "MOAG_Eficiencia","MOAG_Producao","MOAG_PRDDia",
        "MOAG_Frentes","MOAG_Projecao","MOAG_OrdemCorte","MOAG_Areas",
        # Paginas MAtCH_
        "ATR","ATRSemanas","ATR_Semanas",
        "AderenMaturador","Maturador","TCH","PreAnalise","Pre_Analise",
        "TAH","TAHVariedade","TAH_Variedade","TAHEstagio","TAH_Estagio",
        "MAtCH_ATR","MAtCH_TCH","MAtCH_TAH","MAtCH_Maturador",
        # Paginas PREP_
        "Prep_Fazendas","PrepFazendas","Prep_Projecao","PrepProjecao",
        "PREP_Fazendas","PREP_Projecao",
        # Paginas PLANT_
        "PlantPRD","Plant_PRD","PLANT_PRD",
        "PlantApontamento","Plant_Apontamento","PLANT_Apontamento",
        "PlantMudas","Plant_Mudas","PLANT_Mudas",
        "PlantProjecao","Plant_Projecao",
        "PlantOCMuda","Plant_OCMuda","PLANT_OCMuda",
        # Paginas QLD_
        "QLD_PP","QLD_PP_Fazendas",
        "QLD_Preparo","QLD_Plantio","QLD_PlantioENG",
        "QLD_PlantioGemas","QLD_Muda","QLD_Tratos","QLD_Apontamentos",
        # Paginas AGRONO_
        "AgronoBroca","Agrono_Broca","AGRONO_Broca",
        "AgronoCigarrinha","Agrono_Cigarrinha",
        "AgronoMigdolus","Agrono_Migdolus",
        "AgronoSphenophorus","Agrono_Sphenophorus",
        "AgronoOutrasPragas","Agrono_OutrasPragas","AgronoOutrasPrgas",
        "AgronoEstriaVermelha","Agrono_EstriaVermelha",
        # Paginas ADEREN_
        "AderenInset1","Aderen_Inset1",
        "AderenInset2","Aderen_Inset2",
        "AderenFoliar1","Aderen_Foliar1",
        "AderenFoliar2","Aderen_Foliar2",
        "AderenPreMaturador","Aderen_PreMaturador",
        "AderenMaturador","Aderen_Maturador",
        "AderenTSEnleira","Aderen_TSEnleira",
        "AderenTPHerb","Aderen_TPHerb",
        "AderenTSHerb","Aderen_TSHerb",
        "AderenCarreador","Aderen_Carreador",
        "AderenCatacao","Aderen_Catacao",
        "AderenTPQLombo","Aderen_TPQLombo",
        "AderenTPAduba","Aderen_TPAduba",
        "AderenTSAduba","Aderen_TSAduba",
        "AderenTPFertirri","Aderen_TPFertirri",
        "AderenTSFertirri","Aderen_TSFertirri",
        "AderenIrrigaSalva","Aderen_IrrigaSalva",
        "AderenTPComposto","Aderen_TPComposto",
        "AderenTSCorretivo","Aderen_TSCorretivo",
        "AderenSaldo","Aderen_Saldo",
        # Paginas CTRL_ do relatorio BASE
        "Escala","PainelSolar","Painel_Solar",
        "OrdemServico","Ordem_Servico","OS_Dose",
        # Dimensoes
        "Fazenda","Talhao","Variedade","Ambiente","Frente",
        "Equipamento","Caminhao","Calendario","Safra","Corte",
        "Funcionario","Operador"
    )
    CST = @(
        # Paginas: UMOE, R-Headcount, R-Custos, R-Insumos
        "R_Headcount","R-Headcount","Headcount",
        "R_Custos","R-Custos","Custos","Custo",
        "R_Insumos","R-Insumos","Insumos","Insumo",
        # Variantes com hifem -> sublinhado
        "Headcount","Head_Count","HeadCount",
        "CustosCC","Custo_CC","Lancamento","Nota",
        "CentroCusto","Centro_Custo","CC",
        # Outros nomes comuns
        "RH","Funcionario","Colaborador",
        "Fertilizante","Defensivo","Produto","Material",
        "Orcamento","Budget",
        "Calendario","Safra","Fazenda","Frente"
    )
    CTRL = @(
        # Derivados das paginas (remove CTRL_, mantém o resto)
        # CTRL_ESTOQ_SALDO_POS
        "Estoq_Saldo_Pos","Estoq_Saldo","Estoque_Saldo","EstoqueSaldo",
        "Saldo_Pos","SaldoPos","Saldo",
        # CTRL_ORDEM_CORTE
        "Ordem_Corte","OrdemCorte","OC",
        # CTRL_OC_FORNEC
        "OC_Fornec","OCFornec","Fornecedor",
        # CTRL_PESAGEM_EQ_DIVERG
        "Pesagem_Eq_Diverg","Pesagem_Diverg","PesagemDiverg","Pesagem",
        # CTRL_FUNC_SEM_ESCALA
        "Func_Sem_Escala","FuncSemEscala","FuncEscala",
        # CTRL_FUNC_DIV -> JA ENCONTRADA
        "Func_Div",
        # CTRL_OS_DOSE
        "Os_Dose","OS_Dose","OsDose","OS",
        # CTRL_ORCAMENTO
        "Orcamento","Budget",
        # Dimensoes
        "Fazenda","Equipamento","Produto","Material","Insumo",
        "Calendario","Safra","Frente","Funcionario"
    )
}

function Test-Extract($dsId, $dsNome, $tabela) {
    $arquivo = "${dsNome}_${tabela}" -replace '[^a-zA-Z0-9_]','_'
    if (Test-Path "$outDir\$arquivo.json") { return "skip" }

    $body = @{
        queries = @(@{ query = "EVALUATE '$tabela'" })
        serializerSettings = @{ includeNulls = $true }
    } | ConvertTo-Json -Depth 5
    try {
        $r = Invoke-PowerBIRestMethod -Url "groups/$wsId/datasets/$dsId/executeQueries" -Method Post -Body $body -ErrorAction Stop | ConvertFrom-Json
        $rows = $r.results[0].tables[0].rows
        if ($rows -and $rows.Count -gt 0) {
            $rows | ConvertTo-Json -Depth 3 -Compress | Out-File "$outDir\$arquivo.json" -Encoding UTF8
            return "ok:$($rows.Count)"
        }
        return "vazia"
    } catch { return "erro" }
}

$resumo = @()

foreach ($dsNome in $datasets.Keys) {
    $dsId = $datasets[$dsNome]
    $lista = $candidatos[$dsNome] | Sort-Object -Unique
    Write-Host "[$dsNome] $($lista.Count) candidatos..."

    foreach ($tabela in $lista) {
        $res = Test-Extract $dsId $dsNome $tabela
        if ($res -eq "skip") {
            # silencioso
        } elseif ($res.StartsWith("ok:")) {
            $n = $res.Split(":")[1]
            Write-Host "  ACHEI: $tabela ($n linhas)"
            $resumo += [PSCustomObject]@{ Dataset=$dsNome; Tabela=$tabela; Linhas=[int]$n }
        } elseif ($res -eq "vazia") {
            Write-Host "  VAZIA: $tabela"
        }
        # erros sao silenciosos (tabela nao existe)
    }
    Write-Host "  Concluido $dsNome`n"
}

# Listar datasources para entender a origem
Write-Host "Consultando datasources dos datasets..."
foreach ($dsNome in $datasets.Keys) {
    $dsId = $datasets[$dsNome]
    try {
        $ds = Invoke-PowerBIRestMethod -Url "groups/$wsId/datasets/$dsId/datasources" -Method Get | ConvertFrom-Json
        Write-Host "  [$dsNome] Fonte: $($ds.value[0].datasourceType) | $($ds.value[0].connectionDetails | ConvertTo-Json -Compress)"
    } catch {
        Write-Host "  [$dsNome] Datasource: nao acessivel"
    }
}

Write-Host ""
Write-Host "======================================================="
Write-Host "  NOVAS TABELAS EXTRAIDAS:"
if ($resumo.Count -gt 0) {
    $resumo | Format-Table Dataset, Tabela, Linhas -AutoSize
} else {
    Write-Host "  Nenhuma tabela nova encontrada."
    Write-Host "  -> Os nomes das tabelas usam convencao especifica."
    Write-Host "  -> Verifique o datasource acima para identificar a origem."
}
Write-Host "======================================================="
pause
