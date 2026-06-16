# UMOE OS 8.0 - Extracao DAX Manutencao Premium
# 54 tabelas mapeadas dos 6 datasets do workspace Projetos Manutencao PREMIUM
Import-Module MicrosoftPowerBIMgmt -Force

$wsId   = '954ecb3e-1daf-4a98-8801-39f2026da2d8'
$outDir = 'C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Dados-PBI\MANUT'
$tabDir = $outDir

New-Item -ItemType Directory -Path $outDir -Force | Out-Null

Write-Host ''
Write-Host '======================================================='
Write-Host '  UMOE OS 8.0 | Manutencao Premium - Extracao DAX'
Write-Host '  Workspace: Projetos Manutencao PREMIUM'
Write-Host '  54 tabelas | 6 datasets'
Write-Host '======================================================='
$adminUser = Read-Host '  Email'
$adminPass = Read-Host '  Senha' -AsSecureString
$cred = New-Object System.Management.Automation.PSCredential($adminUser, $adminPass)
Connect-PowerBIServiceAccount -Credential $cred | Out-Null
Write-Host '  Conectado.'
Write-Host ''

# ── Dataset IDs (do MANUT_CATALOGO.json) ─────────────────────────────────────
$dsIds = @{
    umoe_dataset                                             = 'aaa8d842-2606-4e11-ab87-f44a7abe320f'
    Materiais_Aplicados___Por_Equipamento                    = '2289f7dd-4b32-4b95-a481-5742a778bd91'
    Ordem_de_Servicos_Abertas_Interna_Campo                  = '31b3252e-d3a8-41bd-b3e5-f6bdd4ecd244'
    Ordem_de_Servicos_Abertas_Interna_Campo_Transporte       = 'a067cd0b-106c-47f4-ae3e-b2c6024ebbaf'
    PARETOS_PROCESSOS                                        = 'f5be77dd-1cc8-4daa-ad89-f7dc271854d4'
}

# ── Tabelas por dataset (parse-pbix.py) ───────────────────────────────────────
$tabelas = @{

    # umoe_dataset (44 tabelas) — dataset principal com toda mecanica
    umoe_dataset = @(
        'f_manfro',          # fatos manutencao frota (principal)
        'f_abastecimento',   # abastecimento combustivel
        'f_lubrificante',    # lubrificacao
        'f_produtividade',   # produtividade equipamentos
        'f_tch',             # TCH colhedoras
        'f_atualizado',      # data ultima atualizacao
        'f_ordem_compra',    # ordens de compra
        'f_requisicao',      # requisicoes de material
        'f_recebimento',     # recebimento de materiais
        'f_pend_aprov',      # pendentes aprovacao
        'd_equipamentos',    # dim equipamentos
        'd_equipamentos_sistema', # dim equip por sistema
        'd_disponibilidade_eqp_data', # disponibilidade por equip/data
        'd_calendar',        # dim calendario
        'd_calendar_metas',  # calendario metas
        'd_data_hora',       # dim data/hora
        'd_hora',            # dim hora
        'd_inicio_turno',    # dim inicio turno
        'd_meses',           # dim meses
        'd_funcionario',     # dim funcionarios
        'd_item',            # dim itens/pecas
        'd_recurso_eqp',     # dim recursos por equip
        'd_meta_equipamentos',   # metas por equipamento
        'd_meta_frente',     # metas por frente
        'd_meta_unidade',    # metas por unidade
        'd_criterio_disponibilidade', # criterios DM
        'd_situacao_oc',     # situacao ordens compra
        'd_situacao_req',    # situacao requisicoes
        'd_emitente',        # dim emitente
        'd_aprovadores',     # dim aprovadores
        'd_compradores',     # dim compradores
        'd_transportadoras', # dim transportadoras
        'd_orcamento_diesel',      # orcamento diesel
        'd_orcamento_km_h',        # orcamento km/h
        'd_orcamento_reais',       # orcamento em R$
        'd_orcamento_equipamentos',# orcamento por equip
        'd_periodo',         # dim periodo
        'd_preco_unit',      # dim preco unitario
        'd_base_calc',       # base de calculo
        'd_datas_ignorar',   # datas a ignorar
        'ajustes_consumos',  # ajustes consumos
        'medidas',           # tabela de medidas DAX
        'Ano Safra',         # dim ano safra
        'dFrotaFrenteBase'   # dim frota/frente/base
    )

    # Materiais Aplicados
    Materiais_Aplicados___Por_Equipamento = @(
        'Materiais Aplicados',
        'f_atualizado'
    )

    # OS Abertas Campo
    Ordem_de_Servicos_Abertas_Interna_Campo = @(
        'Base O.S',
        'Origem',
        'Tabela Fornecedores'
    )

    # OS Transport Imediato
    Ordem_de_Servicos_Abertas_Interna_Campo_Transporte = @(
        'Base O.S',
        'Origem',
        'Tabela Fornecedores'
    )

    # Paretos
    PARETOS_PROCESSOS = @(
        'Paretos',
        'd_equipamento'
    )
}

# ── Funcao DAX extrair ────────────────────────────────────────────────────────
function DAX-Extrair($dsId, $prefix, $tabela) {
    $arq = ($prefix + '_' + ($tabela -replace '[^a-zA-Z0-9_]','_'))
    $fp  = "$outDir\$arq.json"
    if (Test-Path $fp) { return 'skip' }

    # DAX simples
    $q    = "EVALUATE '$tabela'"
    $body = '{"queries":[{"query":"' + ($q -replace '"','\"') + '"}],"serializerSettings":{"includeNulls":true}}'
    try {
        $r    = Invoke-PowerBIRestMethod -Url "groups/$wsId/datasets/$dsId/executeQueries" `
                -Method Post -Body $body -ErrorAction Stop | ConvertFrom-Json
        $rows = $r.results[0].tables[0].rows
        if ($rows -and $rows.Count -gt 0) {
            $rows | ConvertTo-Json -Depth 3 -Compress | Out-File $fp -Encoding UTF8
            return "ok:$($rows.Count)"
        }
        return 'vazia'
    } catch {
        $m = $_.Exception.Message
        if ($m -like '*3236002463*' -or $m -like '*not exist*' -or $m -like '*TableNotFound*') {
            return 'nao_existe'
        }
        return "erro:$($m.Substring(0,[Math]::Min(60,$m.Length)))"
    }
}

# ── Loop principal ────────────────────────────────────────────────────────────
$resumo   = @()
$totalOk  = 0
$totalErro = 0

foreach ($dsNome in $tabelas.Keys) {
    $dsId  = $dsIds[$dsNome]
    if (-not $dsId) {
        Write-Host "  [SKIP] $dsNome - sem ID mapeado"
        continue
    }
    $lista = $tabelas[$dsNome]
    Write-Host "[$dsNome] $($lista.Count) tabelas..."

    foreach ($t in $lista) {
        $res = DAX-Extrair $dsId $dsNome $t
        if ($res -eq 'skip') {
            Write-Host "  skip $t"
        } elseif ($res.StartsWith('ok:')) {
            $n = [int]($res.Split(':')[1])
            Write-Host "  OK   $t ($n linhas)"
            $resumo += [PSCustomObject]@{Dataset=$dsNome; Tabela=$t; Linhas=$n}
            $totalOk++
        } elseif ($res -eq 'vazia') {
            Write-Host "  --   $t (vazia)"
        } elseif ($res -eq 'nao_existe') {
            # silencioso
        } else {
            Write-Host "  !!   $t -> $res"
            $totalErro++
        }
    }
    Write-Host ''
}

# ── Dashboard ────────────────────────────────────────────────────────────────
Write-Host 'Gerando Dashboard HTML...'
python -X utf8 'C:\01 - UMOE\09 - IA\umoe-os-8\09-SCRIPTS\pbi-dashboard-manutencao.py'

$dash = 'C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Relatorios\UMOE_Dashboard_Manutencao.html'
if (Test-Path $dash) {
    Write-Host "Dashboard: $dash"
    Start-Process $dash
}

# ── Resultado ────────────────────────────────────────────────────────────────
Write-Host ''
Write-Host '======================================================='
Write-Host '  RESULTADO FINAL - MANUTENCAO PREMIUM'
Write-Host '======================================================='
Write-Host "  Extraidas: $totalOk | Erros: $totalErro"
Write-Host ''
$resumo | Sort-Object Dataset,Tabela | Format-Table Dataset,Tabela,Linhas -AutoSize
Write-Host ''
Write-Host '  JSONs em:'
Get-ChildItem "$outDir\*.json" | Where-Object { $_.Length -gt 200 } | Sort-Object Name | ForEach-Object {
    Write-Host "    $($_.Name) ($([Math]::Round($_.Length/1KB,0)) KB)"
}
Write-Host '======================================================='
pause
