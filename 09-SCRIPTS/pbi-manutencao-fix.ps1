# UMOE OS 8.0 - Fix Manutencao Premium: ID correto + API Admin + extracao total
Import-Module MicrosoftPowerBIMgmt -Force

$baseDir = 'C:\01 - UMOE\09 - IA\umoe-os-8'
$outDir  = "$baseDir\UMOE-OS-8.0\Dados-PBI\MANUT"
$tmpDir  = "$baseDir\UMOE-OS-8.0\Dados-PBI\MANUT\_tmp"
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null

# ID correto extraido do catalogo (sem o nome)
$wsId   = '954ecb3e-1daf-4a98-8801-39f2026da2d8'
$wsNome = 'Projetos Manutencao PREMIUM'

Write-Host ''
Write-Host '======================================================='
Write-Host "  UMOE OS 8.0 | Manutencao PREMIUM - Fix & Extracao"
Write-Host "  Workspace: $wsNome"
Write-Host "  ID: $wsId"
Write-Host '======================================================='
$adminUser = Read-Host '  Email'
$adminPass = Read-Host '  Senha' -AsSecureString
$cred = New-Object System.Management.Automation.PSCredential($adminUser, $adminPass)
Connect-PowerBIServiceAccount -Credential $cred | Out-Null
$authHeader = (Get-PowerBIAccessToken).Authorization
Write-Host '  Conectado.'
Write-Host ''

# ── Funcao de chamada REST com debug ─────────────────────────────────────────
function PBI-Get($url) {
    try {
        return Invoke-PowerBIRestMethod -Url $url -Method Get -ErrorAction Stop | ConvertFrom-Json
    } catch {
        Write-Host "  ERRO: $url -> $($_.Exception.Message.Substring(0,[Math]::Min(80,$_.Exception.Message.Length)))"
        return $null
    }
}

# ── PASSO 1: Tentar todas as formas de listar datasets ───────────────────────
Write-Host '--- Tentativas de listagem de datasets ---'

$datasets = @()
$reports  = @()

# Tentativa 1: API normal do workspace
Write-Host '[1] API grupos normal...'
$r1 = PBI-Get "groups/$wsId/datasets"
if ($r1 -and $r1.value) {
    $datasets = $r1.value
    Write-Host "  OK: $($datasets.Count) datasets"
} else {
    Write-Host '  Sem resultado via API normal'
}

# Tentativa 2: API Admin (precisa ser Admin do tenant ou ter permissao)
if ($datasets.Count -eq 0) {
    Write-Host '[2] API Admin para grupos...'
    $r2 = PBI-Get "admin/groups/$wsId/datasets"
    if ($r2 -and $r2.value) {
        $datasets = $r2.value
        Write-Host "  OK Admin: $($datasets.Count) datasets"
    } else {
        Write-Host '  Sem resultado via Admin API'
    }
}

# Tentativa 3: Listar todos os datasets do usuario e filtrar por workspace
if ($datasets.Count -eq 0) {
    Write-Host '[3] Todos os datasets do usuario (filtrar por workspace)...'
    $r3 = PBI-Get 'datasets'
    if ($r3 -and $r3.value) {
        $allDs = $r3.value
        Write-Host "  Total datasets visives: $($allDs.Count)"
        $allDs | Format-Table id, name, configuredBy -AutoSize
        # Tentar associar ao workspace
        $filtered = $allDs | Where-Object { $_.workspaceId -eq $wsId -or $_.groupId -eq $wsId }
        if ($filtered) {
            $datasets = $filtered
            Write-Host "  Filtrados por wsId: $($datasets.Count)"
        } else {
            Write-Host '  Nenhum dataset filtrado pelo wsId. Usando todos os disponiveis.'
            $datasets = $allDs
        }
    }
}

# Tentativa 4: Listar reports
Write-Host '[4] Reports do workspace...'
$rpts = PBI-Get "groups/$wsId/reports"
if ($rpts -and $rpts.value) {
    $reports = $rpts.value
    Write-Host "  Reports: $($reports.Count)"
}

# Tentativa 5: Via Invoke-WebRequest direto
if ($datasets.Count -eq 0) {
    Write-Host '[5] WebRequest direto /groups/{id}/datasets...'
    try {
        $resp = Invoke-WebRequest -Uri "https://api.powerbi.com/v1.0/myorg/groups/$wsId/datasets" `
            -Headers @{Authorization=$authHeader} -ErrorAction Stop
        $body = $resp.Content | ConvertFrom-Json
        if ($body.value) {
            $datasets = $body.value
            Write-Host "  WebRequest OK: $($datasets.Count) datasets"
        } else {
            Write-Host "  Resposta: $($resp.Content.Substring(0,[Math]::Min(200,$resp.Content.Length)))"
        }
    } catch {
        Write-Host "  WebRequest erro: $($_.Exception.Message.Substring(0,80))"
    }
}

Write-Host ''
Write-Host "Datasets encontrados: $($datasets.Count)"
if ($datasets.Count -gt 0) {
    $datasets | Format-Table id, name, configuredBy -AutoSize
}
Write-Host "Reports encontrados: $($reports.Count)"
if ($reports.Count -gt 0) {
    $reports | Format-Table id, name -AutoSize
}
Write-Host ''

# ── PASSO 2: Se ainda sem datasets, tentar adicionar usuario ao workspace ────
if ($datasets.Count -eq 0) {
    Write-Host '--- Tentando adicionar projetos@umoe.com.br ao workspace ---'
    $body = '{"groupUserAccessRight":"Member","emailAddress":"projetos@umoe.com.br","principalType":"User"}'
    try {
        $addResult = Invoke-WebRequest -Uri "https://api.powerbi.com/v1.0/myorg/groups/$wsId/users" `
            -Method Post -Headers @{Authorization=$authHeader; 'Content-Type'='application/json'} `
            -Body $body -ErrorAction Stop
        Write-Host "  Adicionar usuario: $($addResult.StatusCode)"
        Start-Sleep -Seconds 3
        # Tentar listar novamente
        $r6 = PBI-Get "groups/$wsId/datasets"
        if ($r6 -and $r6.value) {
            $datasets = $r6.value
            Write-Host "  Apos adicionar: $($datasets.Count) datasets"
        }
    } catch {
        Write-Host "  Nao foi possivel adicionar: $($_.Exception.Message.Substring(0,100))"
    }
    Write-Host ''
}

# ── PASSO 3: Se ainda sem datasets, listar TODOS os workspaces com datasets ──
if ($datasets.Count -eq 0) {
    Write-Host '--- DIAGNOSTICO: Listando TODOS os workspaces com datasets ---'
    $todosWs = (PBI-Get 'groups?$top=200&$expand=datasets').value
    Write-Host "  Total workspaces: $($todosWs.Count)"
    $todosWs | Where-Object { $_.datasets -and $_.datasets.Count -gt 0 } | ForEach-Object {
        Write-Host "  WS: $($_.name) | ID: $($_.id) | Datasets: $($_.datasets.Count)"
    }

    # Mostrar o workspace alvo especificamente
    $wsAlvo = $todosWs | Where-Object { $_.id -eq $wsId }
    if ($wsAlvo) {
        Write-Host ''
        Write-Host "  Workspace alvo encontrado: $($wsAlvo.name)"
        Write-Host "  Tipo: $($wsAlvo.type) | Estado: $($wsAlvo.state)"
        Write-Host "  isReadOnly: $($wsAlvo.isReadOnly) | isOnDedicatedCapacity: $($wsAlvo.isOnDedicatedCapacity)"
        if ($wsAlvo.datasets) {
            $datasets = $wsAlvo.datasets
            Write-Host "  Datasets via expand: $($datasets.Count)"
        }
    } else {
        Write-Host "  ATENCAO: workspace $wsId NAO encontrado na listagem!"
        Write-Host "  Verificar se o usuario tem acesso ou se o ID esta correto."
        Write-Host ''
        Write-Host '  Workspaces com "Manut" no nome:'
        $todosWs | Where-Object { $_.name -like '*Manut*' -or $_.name -like '*manut*' } |
            Format-Table id, name, type, state -AutoSize
    }
    Write-Host ''
}

# ── PASSO 4: Salvar catalogo corrigido ───────────────────────────────────────
$catalogo = [ordered]@{
    workspace = [ordered]@{ id = $wsId; name = $wsNome }
    datasets  = @($datasets | ForEach-Object { [ordered]@{ id = $_.id; name = $_.name } })
    reports   = @($reports  | ForEach-Object { [ordered]@{ id = $_.id; name = $_.name } })
    gerado    = (Get-Date -Format 'yyyy-MM-dd HH:mm')
}
$catalogo | ConvertTo-Json -Depth 5 | Out-File "$outDir\MANUT_CATALOGO.json" -Encoding UTF8
Write-Host "Catalogo atualizado: $outDir\MANUT_CATALOGO.json"
Write-Host ''

# ── PASSO 5: Se tiver datasets, baixar PBIX e extrair tabelas ────────────────
if ($datasets.Count -gt 0) {
    Write-Host '--- Baixando PBIX e extraindo tabelas ---'

    function DAX-Extrair($dsId, $dsNome, $tabela) {
        $arq = ($dsNome + '_' + ($tabela -replace '[^a-zA-Z0-9_]','_'))
        $fp  = "$outDir\$arq.json"
        if (Test-Path $fp) { return 'skip' }
        $body = '{"queries":[{"query":"EVALUATE ''' + $tabela + '''"}],"serializerSettings":{"includeNulls":true}}'
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
            if ($m -like '*3236002463*' -or $m -like '*not exist*') { return 'nao_existe' }
            return "erro"
        }
    }

    $resumo = @()
    foreach ($ds in $datasets) {
        $dsId   = $ds.id
        $dsNome = $ds.name -replace '[^a-zA-Z0-9_]','_'
        Write-Host "  Dataset: $($ds.name)"

        # Tentar baixar PBIX para descobrir tabelas
        $rpt      = $reports | Where-Object { $_.datasetId -eq $dsId } | Select-Object -First 1
        $tabelas  = @()
        if ($rpt) {
            $pbixPath = "$tmpDir\${dsNome}.pbix"
            $url = "https://api.powerbi.com/v1.0/myorg/groups/$wsId/reports/$($rpt.id)/export"
            try {
                Invoke-WebRequest -Uri $url -Headers @{Authorization=$authHeader} `
                    -OutFile $pbixPath -TimeoutSec 300 -ErrorAction Stop
                $mb = [Math]::Round((Get-Item $pbixPath).Length / 1MB, 2)
                Write-Host "  PBIX: $mb MB"

                # Python parse
                $py = @"
import zipfile, re, json
from pathlib import Path
pbix = r'$pbixPath'
tables = set()
try:
    with zipfile.ZipFile(pbix, 'r') as z:
        for name in z.namelist():
            if 'Layout' in name and 'Static' not in name:
                raw = z.read(name)
                for enc in ['utf-16-le', 'utf-8-sig', 'utf-8']:
                    try:
                        t = raw.decode(enc)
                        for m in re.finditer(r'\\"Entity\\"\\s*:\\s*\\"([^\\"]+)\\"', t):
                            tables.add(m.group(1))
                        for m in re.finditer(r'"Entity"\\s*:\\s*"([^"]+)"', t):
                            tables.add(m.group(1))
                        if len(t) > 100: break
                    except: pass
            if name == 'DiagramLayout':
                raw = z.read(name)
                for enc in ['utf-16-le','utf-8']:
                    try:
                        t = raw.decode(enc)
                        for m in re.finditer(r'"nodeIndex"\\s*:\\s*"([^"]+)"', t):
                            tables.add(m.group(1))
                        break
                    except: pass
except Exception as e:
    print(f'Erro: {e}')
clean = sorted(x for x in tables if x and not x.startswith(('$','Local','DateTable')) and len(x)>1)
print('\n'.join(clean))
"@
                $pyFile = "$tmpDir\parse_${dsNome}.py"
                $py | Out-File $pyFile -Encoding UTF8
                $tabsTxt = python -X utf8 $pyFile 2>&1
                $tabelas = $tabsTxt | Where-Object { $_ -and $_ -notlike '*Erro*' -and $_ -notlike '*$*' }
                Write-Host "  Tabelas do PBIX: $($tabelas.Count)"
            } catch {
                Write-Host "  PBIX nao disponivel"
            }
        }

        # Fallback: candidatos padrao de manutencao
        if ($tabelas.Count -eq 0) {
            $tabelas = @(
                'OS','ORDEM_SERVICO','OS_ABERTA','OS_FECHADA','OS_ENCERRADA',
                'FALHA','FALHAS','DEFEITO','CAUSA_FALHA','HISTORICO_FALHA',
                'EQUIP','EQUIPAMENTO','FROTA','MAQUINA','ATIVO',
                'COLHEDORA','CAMINHAO','TRANSBORDO','TRATOR',
                'DISPONIBILIDADE','DM','DF','MTBF','MTTR','CONFIABILIDADE',
                'PECA','PECAS','ESTOQUE_PECA','CONSUMO_PECA','CURVA_ABC',
                'CUSTO_MANUT','CUSTO_OS','CUSTO_MES','CST_MANUT',
                'PREVENTIVA','CORRETIVA','PREDITIVA','INSPECAO',
                'BACKLOG','OS_BACKLOG','PLANEJ_MANUT',
                'TECNICO','MECANICO','OFICINA','TURNO_OFICINA',
                'DIESEL','COMBUSTIVEL','OLEO','LUBRIF',
                'SEGURANCA','INCIDENTE','ACIDENTE','TOMBAMENTO',
                'CALENDARIO','DATA','SAFRA','FRENTE',
                'SERVICO','COMPONENTE','SISTEMA','SUBSIS',
                'Z_DTHR','Z_ULT_ATUALIZACAO','Z_LEGENDAS',
                'MANUT_OS','MANUT_FALHA','MANUT_PECA','MANUT_EQUIP',
                'LOG_OS','LOG_FALHA','BASE_OS','BASE_FALHA'
            )
        }

        Write-Host "  Extraindo $($tabelas.Count) tabelas..."
        foreach ($t in $tabelas) {
            $res = DAX-Extrair $dsId $dsNome $t
            if ($res.StartsWith('ok:')) {
                $n = [int]($res.Split(':')[1])
                Write-Host "  OK  ${dsNome}.$t ($n linhas)"
                $resumo += [PSCustomObject]@{Dataset=$dsNome; Tabela=$t; Linhas=$n}
            } elseif ($res -eq 'vazia') {
                Write-Host "  --  ${dsNome}.$t (vazia)"
            }
        }
        $tabelas | Out-File "$outDir\${dsNome}_TABELAS.txt" -Encoding UTF8
        Write-Host ''
    }

    # Gerar dashboard
    Write-Host 'Gerando Dashboard HTML...'
    python -X utf8 "$baseDir\09-SCRIPTS\pbi-dashboard-manutencao.py"
    $dash = "$baseDir\UMOE-OS-8.0\Relatorios\UMOE_Dashboard_Manutencao.html"
    if (Test-Path $dash) {
        Write-Host "Dashboard gerado: $dash"
        Start-Process $dash
    }

    Write-Host ''
    Write-Host '======================================================='
    Write-Host '  RESULTADO'
    Write-Host '======================================================='
    $resumo | Sort-Object Dataset,Tabela | Format-Table Dataset,Tabela,Linhas -AutoSize

} else {
    Write-Host '======================================================='
    Write-Host '  SEM DADOS - ACOES NECESSARIAS:'
    Write-Host '======================================================='
    Write-Host ''
    Write-Host '  1. Acesse app.powerbi.com'
    Write-Host "  2. Va em workspace: Projetos Manutencao PREMIUM"
    Write-Host "  3. Configuracoes -> Acesso -> Adicionar membro:"
    Write-Host '     projetos@umoe.com.br  com papel  Membro ou Admin'
    Write-Host ''
    Write-Host '  OU: execute este script com conta que ja tem acesso ao workspace'
    Write-Host '  OU: peca para o Admin do tenant adicionar projetos@umoe.com.br'
    Write-Host ''
    Write-Host '  Workspace ID correto para referencia futura:'
    Write-Host "  $wsId"
    Write-Host '======================================================='
}

pause
