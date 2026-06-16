# UMOE OS 8.0 - Extrair dados via DAX dos 3 datasets Power BI
# Requer: MicrosoftPowerBIMgmt (ja instalado)
# Salva JSONs em UMOE-OS-8.0/Dados-PBI/

Write-Host ""
Write-Host "======================================================="
Write-Host "  UMOE OS 8.0 | Extracao DAX - Power BI"
Write-Host "  3 datasets: BASE, CST, CTRL"
Write-Host "======================================================="
Write-Host ""

Import-Module MicrosoftPowerBIMgmt -Force

# Credenciais
$adminUser = Read-Host "  Email Power BI"
$adminPass = Read-Host "  Senha" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential($adminUser, $adminPass)

Write-Host ""
Write-Host "  Conectando..."
Connect-PowerBIServiceAccount -Credential $credential | Out-Null
Write-Host "  OK - Conectado como: $adminUser"

# Config
$wsId = "662a06b5-5579-4af6-b66a-7ac191a96674"
$outDir = "C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Dados-PBI"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

Write-Host "  Saida: $outDir"
Write-Host ""

# Funcao para executar DAX e salvar JSON
function Invoke-DAX {
    param($datasetId, $nomeArquivo, $daxQuery)
    $body = @{
        queries = @(@{ query = $daxQuery })
        serializerSettings = @{ includeNulls = $true }
    } | ConvertTo-Json -Depth 10
    try {
        $r = Invoke-PowerBIRestMethod `
            -Url "groups/$wsId/datasets/$datasetId/executeQueries" `
            -Method Post -Body $body | ConvertFrom-Json
        $rows = $r.results[0].tables[0].rows
        if ($rows) {
            $rows | ConvertTo-Json -Depth 5 | Out-File "$outDir\$nomeArquivo.json" -Encoding UTF8
            Write-Host "    OK - $nomeArquivo`: $($rows.Count) linhas"
        } else {
            Write-Host "    VAZIO - $nomeArquivo"
        }
        return $rows
    } catch {
        Write-Host "    ERRO - $nomeArquivo`: $_"
        return $null
    }
}

# ============================================================
# DATASET 1: BI_AGR_01_BASE
# ============================================================
$dsBase = "06950719-48dc-403d-bd91-2e059cf1a25e"
Write-Host "[BASE] Descobrindo tabelas..."

# Listar tabelas do modelo
$tabelasBase = Invoke-DAX $dsBase "BASE_tabelas" "EVALUATE INFO.TABLES()"
Write-Host ""
Write-Host "[BASE] Extraindo tabelas principais..."

# Producao diaria
Invoke-DAX $dsBase "BASE_producao_diaria" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('Producao', NOT ISBLANK('Producao'[Data])),
    "Data", 'Producao'[Data],
    "Frente", 'Producao'[Frente],
    "Colhedora", 'Producao'[Colhedora],
    "Fazenda", 'Producao'[Fazenda],
    "Talhao", 'Producao'[Talhao],
    "TCH", 'Producao'[TCH],
    "Toneladas", 'Producao'[Toneladas],
    "Cargas", 'Producao'[Cargas],
    "HorasTrabalhadas", 'Producao'[HorasTrabalhadas],
    "Eficiencia", 'Producao'[Eficiencia],
    "DMT", 'Producao'[DMT]
)
ORDER BY 'Producao'[Data] DESC
"@ | Out-Null

# ATR / Qualidade
Invoke-DAX $dsBase "BASE_atr_qualidade" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('ATR', NOT ISBLANK('ATR'[Data])),
    "Data", 'ATR'[Data],
    "Fazenda", 'ATR'[Fazenda],
    "Variedade", 'ATR'[Variedade],
    "ATR", 'ATR'[ATR],
    "Pol", 'ATR'[Pol],
    "Fibra", 'ATR'[Fibra],
    "Umidade", 'ATR'[Umidade],
    "Pureza", 'ATR'[Pureza]
)
ORDER BY 'ATR'[Data] DESC
"@ | Out-Null

# Moagem
Invoke-DAX $dsBase "BASE_moagem" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('Moagem', NOT ISBLANK('Moagem'[Data])),
    "Data", 'Moagem'[Data],
    "ToneladasDia", 'Moagem'[ToneladasDia],
    "ToneladasAcumulado", 'Moagem'[ToneladasAcumulado],
    "MetaDia", 'Moagem'[MetaDia],
    "MetaAcumulada", 'Moagem'[MetaAcumulada]
)
ORDER BY 'Moagem'[Data] DESC
"@ | Out-Null

# Disponibilidade mecanica
Invoke-DAX $dsBase "BASE_disponibilidade" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('Disponibilidade', NOT ISBLANK('Disponibilidade'[Data])),
    "Data", 'Disponibilidade'[Data],
    "Equipamento", 'Disponibilidade'[Equipamento],
    "Tipo", 'Disponibilidade'[Tipo],
    "DM", 'Disponibilidade'[DM],
    "DF", 'Disponibilidade'[DF],
    "HorasDisponiveis", 'Disponibilidade'[HorasDisponiveis],
    "HorasParadas", 'Disponibilidade'[HorasParadas]
)
ORDER BY 'Disponibilidade'[Data] DESC
"@ | Out-Null

# Pragas e agronomia
Invoke-DAX $dsBase "BASE_pragas" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('Pragas', NOT ISBLANK('Pragas'[Data])),
    "Data", 'Pragas'[Data],
    "Fazenda", 'Pragas'[Fazenda],
    "Talhao", 'Pragas'[Talhao],
    "TipoPraga", 'Pragas'[TipoPraga],
    "Incidencia", 'Pragas'[Incidencia],
    "Area", 'Pragas'[Area]
)
"@ | Out-Null

# Chuvas
Invoke-DAX $dsBase "BASE_chuvas" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('Chuvas', NOT ISBLANK('Chuvas'[Data])),
    "Data", 'Chuvas'[Data],
    "Estacao", 'Chuvas'[Estacao],
    "Precipitacao", 'Chuvas'[Precipitacao],
    "HorasChuva", 'Chuvas'[HorasChuva]
)
ORDER BY 'Chuvas'[Data] DESC
"@ | Out-Null

# Calendario / Escala
Invoke-DAX $dsBase "BASE_escala" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('Escala', NOT ISBLANK('Escala'[Data])),
    "Data", 'Escala'[Data],
    "Frente", 'Escala'[Frente],
    "ColhedorasAtivas", 'Escala'[ColhedorasAtivas],
    "TurnoA", 'Escala'[TurnoA],
    "TurnoB", 'Escala'[TurnoB]
)
ORDER BY 'Escala'[Data] DESC
"@ | Out-Null

# Aderencia tratos
Invoke-DAX $dsBase "BASE_aderencia" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('Aderencia', NOT ISBLANK('Aderencia'[Fazenda])),
    "Fazenda", 'Aderencia'[Fazenda],
    "Trato", 'Aderencia'[Trato],
    "Safra", 'Aderencia'[Safra],
    "AreaPrevista", 'Aderencia'[AreaPrevista],
    "AreaRealizada", 'Aderencia'[AreaRealizada],
    "Aderencia", 'Aderencia'[Aderencia]
)
"@ | Out-Null

# ============================================================
# DATASET 2: BI_AGR_01_CST - Custos
# ============================================================
$dsCst = "a735ce0e-4234-42f8-bedd-5cbb07ce6364"
Write-Host ""
Write-Host "[CST] Descobrindo tabelas..."
Invoke-DAX $dsCst "CST_tabelas" "EVALUATE INFO.TABLES()" | Out-Null

Write-Host "[CST] Extraindo custos..."

Invoke-DAX $dsCst "CST_custos_cc" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('Custos', NOT ISBLANK('Custos'[CentroCusto])),
    "CentroCusto", 'Custos'[CentroCusto],
    "Descricao", 'Custos'[Descricao],
    "Mes", 'Custos'[Mes],
    "Ano", 'Custos'[Ano],
    "Orcado", 'Custos'[Orcado],
    "Realizado", 'Custos'[Realizado],
    "Desvio", 'Custos'[Desvio],
    "CustoTon", 'Custos'[CustoTon]
)
ORDER BY 'Custos'[Ano] DESC, 'Custos'[Mes] DESC
"@ | Out-Null

Invoke-DAX $dsCst "CST_headcount" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('Headcount', NOT ISBLANK('Headcount'[Cargo])),
    "Cargo", 'Headcount'[Cargo],
    "Setor", 'Headcount'[Setor],
    "Quantidade", 'Headcount'[Quantidade],
    "CustoTotal", 'Headcount'[CustoTotal],
    "Mes", 'Headcount'[Mes],
    "Ano", 'Headcount'[Ano]
)
"@ | Out-Null

Invoke-DAX $dsCst "CST_insumos" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('Insumos', NOT ISBLANK('Insumos'[Produto])),
    "Produto", 'Insumos'[Produto],
    "Categoria", 'Insumos'[Categoria],
    "Quantidade", 'Insumos'[Quantidade],
    "PrecoUnitario", 'Insumos'[PrecoUnitario],
    "ValorTotal", 'Insumos'[ValorTotal],
    "Mes", 'Insumos'[Mes],
    "Ano", 'Insumos'[Ano]
)
ORDER BY 'Insumos'[ValorTotal] DESC
"@ | Out-Null

# ============================================================
# DATASET 3: BI_AGR_01_CTRL - Controle
# ============================================================
$dsCtrl = "4c81ea62-ef7f-4976-9aaa-bf7ab3727c0b"
Write-Host ""
Write-Host "[CTRL] Descobrindo tabelas..."
Invoke-DAX $dsCtrl "CTRL_tabelas" "EVALUATE INFO.TABLES()" | Out-Null

Write-Host "[CTRL] Extraindo controle..."

Invoke-DAX $dsCtrl "CTRL_ordem_corte" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('OrdemCorte', NOT ISBLANK('OrdemCorte'[Fazenda])),
    "Fazenda", 'OrdemCorte'[Fazenda],
    "Talhao", 'OrdemCorte'[Talhao],
    "DataPrevista", 'OrdemCorte'[DataPrevista],
    "DataRealizada", 'OrdemCorte'[DataRealizada],
    "Variedade", 'OrdemCorte'[Variedade],
    "AreaPrevista", 'OrdemCorte'[AreaPrevista],
    "AreaRealizada", 'OrdemCorte'[AreaRealizada],
    "TCHPrevisto", 'OrdemCorte'[TCHPrevisto],
    "Status", 'OrdemCorte'[Status]
)
"@ | Out-Null

Invoke-DAX $dsCtrl "CTRL_estoque_saldo" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('EstoqueSaldo', NOT ISBLANK('EstoqueSaldo'[Produto])),
    "Produto", 'EstoqueSaldo'[Produto],
    "Categoria", 'EstoqueSaldo'[Categoria],
    "SaldoAtual", 'EstoqueSaldo'[SaldoAtual],
    "SaldoMinimo", 'EstoqueSaldo'[SaldoMinimo],
    "Situacao", 'EstoqueSaldo'[Situacao],
    "ValorEstoque", 'EstoqueSaldo'[ValorEstoque]
)
ORDER BY 'EstoqueSaldo'[Situacao]
"@ | Out-Null

Invoke-DAX $dsCtrl "CTRL_orcamento" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('Orcamento', NOT ISBLANK('Orcamento'[CentroCusto])),
    "CentroCusto", 'Orcamento'[CentroCusto],
    "Descricao", 'Orcamento'[Descricao],
    "OrcadoAnual", 'Orcamento'[OrcadoAnual],
    "RealizadoAcumulado", 'Orcamento'[RealizadoAcumulado],
    "Saldo", 'Orcamento'[Saldo],
    "PercExecutado", 'Orcamento'[PercExecutado]
)
ORDER BY 'Orcamento'[RealizadoAcumulado] DESC
"@ | Out-Null

Invoke-DAX $dsCtrl "CTRL_pesagem_divergencia" @"
EVALUATE
SELECTCOLUMNS(
    FILTER('PesagemDivergencia', NOT ISBLANK('PesagemDivergencia'[Data])),
    "Data", 'PesagemDivergencia'[Data],
    "Veiculo", 'PesagemDivergencia'[Veiculo],
    "PesoEntrada", 'PesagemDivergencia'[PesoEntrada],
    "PesoSaida", 'PesagemDivergencia'[PesoSaida],
    "Divergencia", 'PesagemDivergencia'[Divergencia],
    "PercDivergencia", 'PesagemDivergencia'[PercDivergencia]
)
ORDER BY 'PesagemDivergencia'[Data] DESC
"@ | Out-Null

# ============================================================
# Resumo final
# ============================================================
Write-Host ""
Write-Host "======================================================="
Write-Host "  EXTRACAO CONCLUIDA"
Write-Host "======================================================="
Write-Host ""
$arquivos = Get-ChildItem "$outDir\*.json"
Write-Host "  Arquivos gerados em: $outDir"
Write-Host ""
foreach ($f in $arquivos) {
    $tam = [math]::Round($f.Length / 1KB, 1)
    Write-Host "    $($f.Name) ($tam KB)"
}
Write-Host ""
Write-Host "  Total: $($arquivos.Count) arquivos"
Write-Host ""
Write-Host "  Proximo passo: python extrair-pbi-pipeline.py"
Write-Host "  Para consolidar dados e atualizar dashboards."
Write-Host ""
pause
