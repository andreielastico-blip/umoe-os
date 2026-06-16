# UMOE OS 8.0 - Pipeline Manutencao Premium
# Descobre workspace "Projeto Manutencao Premium", mapeia tabelas, extrai via DAX, gera Dashboard HTML
# Encoding: sem acentos (UMOE-CLAUDE.md)

Import-Module MicrosoftPowerBIMgmt -Force

$baseDir  = 'C:\01 - UMOE\09 - IA\umoe-os-8'
$outDir   = "$baseDir\UMOE-OS-8.0\Dados-PBI\MANUT"
$tmpDir   = "$baseDir\UMOE-OS-8.0\Dados-PBI\MANUT\_tmp"
$relDir   = "$baseDir\UMOE-OS-8.0\Relatorios"

New-Item -ItemType Directory -Path $outDir  -Force | Out-Null
New-Item -ItemType Directory -Path $tmpDir  -Force | Out-Null
New-Item -ItemType Directory -Path $relDir  -Force | Out-Null

Write-Host ''
Write-Host '======================================================='
Write-Host '  UMOE OS 8.0 | Manutencao Premium - Pipeline Completo'
Write-Host '  1. Descobrir workspace  2. Mapear tabelas  3. Extrair'
Write-Host '  4. Gerar Dashboard HTML'
Write-Host '======================================================='
$adminUser = Read-Host '  Email Power BI'
$adminPass = Read-Host '  Senha' -AsSecureString
$cred = New-Object System.Management.Automation.PSCredential($adminUser, $adminPass)
Connect-PowerBIServiceAccount -Credential $cred | Out-Null
$authHeader = (Get-PowerBIAccessToken).Authorization
Write-Host '  Conectado.'
Write-Host ''

# ============================================================
# PASSO 1: Descobrir workspace "Manutencao Premium"
# ============================================================
Write-Host '[1/4] Buscando workspace Manutencao Premium...'

$wsListRaw = Invoke-PowerBIRestMethod -Url 'groups?$top=200' -Method Get | ConvertFrom-Json
$wsAll = $wsListRaw.value

$wsTarget = $wsAll | Where-Object {
    $_.name -like '*Manutencao*' -or $_.name -like '*Manutenção*' -or
    $_.name -like '*Manutencao Premium*' -or $_.name -like '*Manutencao*Premium*' -or
    $_.name -like '*Maintenance*'
}

if (-not $wsTarget) {
    Write-Host ''
    Write-Host '  Workspace nao encontrado pelo nome. Listando todos os workspaces disponiveis:'
    $wsAll | Sort-Object name | Format-Table id, name -AutoSize
    Write-Host ''
    $wsId = Read-Host '  Cole o ID do workspace de Manutencao acima'
    $wsNome = ($wsAll | Where-Object { $_.id -eq $wsId }).name
} else {
    if ($wsTarget.Count -gt 1) {
        Write-Host '  Multiplos workspaces encontrados:'
        $wsTarget | Format-Table id, name -AutoSize
        $wsId   = Read-Host '  Cole o ID correto'
        $wsNome = ($wsTarget | Where-Object { $_.id -eq $wsId }).name
    } else {
        $wsId   = $wsTarget.id
        $wsNome = $wsTarget.name
    }
}

Write-Host "  Workspace: $wsNome"
Write-Host "  ID: $wsId"
Write-Host ''

# ============================================================
# PASSO 2: Listar datasets e reports
# ============================================================
Write-Host '[2/4] Listando datasets e reports...'

$datasets = (Invoke-PowerBIRestMethod -Url "groups/$wsId/datasets" -Method Get | ConvertFrom-Json).value
$reports  = (Invoke-PowerBIRestMethod -Url "groups/$wsId/reports"  -Method Get | ConvertFrom-Json).value

Write-Host "  Datasets ($($datasets.Count)):"
$datasets | Format-Table id, name, configuredBy -AutoSize

Write-Host "  Reports ($($reports.Count)):"
$reports | Format-Table id, name -AutoSize

# Salvar catalogo
$catalogo = @{
    workspace = @{ id = $wsId; name = $wsNome }
    datasets  = $datasets | ForEach-Object { @{ id = $_.id; name = $_.name } }
    reports   = $reports  | ForEach-Object { @{ id = $_.id; name = $_.name } }
    gerado    = (Get-Date -Format 'yyyy-MM-dd HH:mm')
}
$catalogo | ConvertTo-Json -Depth 5 | Out-File "$outDir\MANUT_CATALOGO.json" -Encoding UTF8
Write-Host "  Catalogo salvo: $outDir\MANUT_CATALOGO.json"
Write-Host ''

# ============================================================
# FUNCAO: Download PBIX e extrair tabelas via Python
# ============================================================
function Get-TablesFromPBIX($rId, $dsNome) {
    $pbixPath = "$tmpDir\$dsNome.pbix"
    $exPath   = "$tmpDir\$dsNome"

    Write-Host "  Baixando PBIX $dsNome..."
    $url = "https://api.powerbi.com/v1.0/myorg/groups/$wsId/reports/$rId/export"
    try {
        Invoke-WebRequest -Uri $url -Headers @{Authorization=$authHeader} `
            -OutFile $pbixPath -TimeoutSec 300 -ErrorAction Stop
        $mb = [Math]::Round((Get-Item $pbixPath).Length / 1MB, 2)
        Write-Host "  OK: $mb MB"
    } catch {
        Write-Host "  AVISO: Download PBIX falhou ($_). Tentando tabelas via DAX brute-force."
        return @()
    }

    # Extrair PBIX via Python (parse-pbix.py ja existente)
    $parseScript = "$baseDir\09-SCRIPTS\parse-pbix.py"
    if (Test-Path $parseScript) {
        Write-Host "  Extraindo tabelas via Python (parse-pbix.py)..."
        $tmpParseDir = "$tmpDir\_parse"
        New-Item -ItemType Directory -Path $tmpParseDir -Force | Out-Null

        # Script python inline para este PBIX especifico
        $py = @"
import zipfile, re, json
from pathlib import Path

pbix = r'$pbixPath'
out  = r'$tmpParseDir\${dsNome}_tables.txt'

tables = set()
with zipfile.ZipFile(pbix, 'r') as z:
    for name in z.namelist():
        if 'Layout' in name and 'Static' not in name:
            raw = z.read(name)
            for enc in ['utf-16-le', 'utf-8-sig', 'utf-8']:
                try:
                    t = raw.decode(enc)
                    for m in re.finditer(r'\\\"Entity\\\"\\s*:\\s*\\\"([^\\\"]+)\\\"', t):
                        tables.add(m.group(1))
                    for m in re.finditer(r'"Entity"\\s*:\\s*"([^"]+)"', t):
                        tables.add(m.group(1))
                    if len(t) > 100: break
                except: pass
        if name == 'DiagramLayout':
            raw = z.read(name)
            for enc in ['utf-16-le', 'utf-8']:
                try:
                    t = raw.decode(enc)
                    for m in re.finditer(r'"nodeIndex"\\s*:\\s*"([^"]+)"', t):
                        tables.add(m.group(1))
                    break
                except: pass
        if name.endswith('.dax'):
            try:
                t = z.read(name).decode('utf-8-sig', errors='ignore')
                for m in re.finditer(r"EVALUATE\\s+'([^']+)'", t, re.I):
                    tables.add(m.group(1))
            except: pass

clean = sorted(t for t in tables if t and not t.startswith(('$','Local','DateTable')) and len(t) > 1)
Path(out).write_text('\n'.join(clean), encoding='utf-8')
print('\n'.join(clean))
"@
        $pyFile = "$tmpParseDir\parse_${dsNome}.py"
        $py | Out-File $pyFile -Encoding UTF8
        $tabsTxt = python -X utf8 $pyFile 2>&1
        $tabsFile = "$tmpParseDir\${dsNome}_tables.txt"
        if (Test-Path $tabsFile) {
            $tabelas = Get-Content $tabsFile -Encoding UTF8 | Where-Object { $_ -and $_ -notlike '*$*' }
            Write-Host "  Tabelas encontradas no PBIX: $($tabelas.Count)"
            return $tabelas
        }
    }
    return @()
}

# ============================================================
# FUNCAO: Extrair tabela via DAX
# ============================================================
function DAX-Extrair($dsId, $prefix, $tabela) {
    $arq = ($prefix + '_' + ($tabela -replace '[^a-zA-Z0-9_]','_'))
    $fp  = "$outDir\$arq.json"
    if (Test-Path $fp) { return 'skip' }

    $body = '{"queries":[{"query":"EVALUATE ''' + $tabela + '''"}],"serializerSettings":{"includeNulls":true}}'
    try {
        $r    = Invoke-PowerBIRestMethod -Url "groups/$wsId/datasets/$dsId/executeQueries" -Method Post -Body $body -ErrorAction Stop | ConvertFrom-Json
        $rows = $r.results[0].tables[0].rows
        if ($rows -and $rows.Count -gt 0) {
            $rows | ConvertTo-Json -Depth 3 -Compress | Out-File $fp -Encoding UTF8
            return "ok:$($rows.Count)"
        }
        return 'vazia'
    } catch {
        $msg = $_.Exception.Message
        if ($msg -like '*3236002463*' -or $msg -like '*not exist*' -or $msg -like '*TableNotFound*') { return 'nao_existe' }
        return "erro"
    }
}

# ============================================================
# PASSO 3: Para cada dataset — PBIX + DAX
# ============================================================
Write-Host '[3/4] Extraindo dados de cada dataset...'
Write-Host ''

$resumo     = @()
$tabelasMap = @{}   # dsNome -> lista de tabelas

foreach ($ds in $datasets) {
    $dsId   = $ds.id
    $dsNome = $ds.name -replace '[^a-zA-Z0-9_]','_'

    Write-Host "--- Dataset: $($ds.name) ---"

    # Procurar report correspondente para download PBIX
    $rpt = $reports | Where-Object { $_.datasetId -eq $dsId -or $_.name -like "*$($ds.name)*" } | Select-Object -First 1
    $tabelas = @()

    if ($rpt) {
        $tabelas = Get-TablesFromPBIX $rpt.id $dsNome
    }

    # Fallback: tentar nomes comuns de manutencao se nao achou tabelas
    if ($tabelas.Count -eq 0) {
        Write-Host "  Usando candidatos de manutencao padrao..."
        $tabelas = @(
            'OS','ORDEM_SERVICO','MANUT_OS','OS_ABERTA','OS_FECHADA',
            'FALHA','FALHAS','FALHA_EQUIP','TOP_FALHAS',
            'EQUIP','EQUIPAMENTO','FROTA','COLHEDORA','CAMINHAO','TRANSBORDO',
            'MTBF','MTTR','DISPONIBILIDADE','DM','DF',
            'PECAS','PECA','ESTOQUE_PECAS','CONSUMO_PECA','CURVA_ABC',
            'CUSTO_MANUT','CUSTO_OS','CUSTO_PECA',
            'PREVENTIVA','CORRETIVA','PREDITIVA',
            'BACKLOG','PLANEJAMENTO','CRONOGRAMA',
            'TECNICO','MECANICO','OFICINA',
            'DIESEL','COMBUSTIVEL','LUBRI','OLEO',
            'SEGURANCA','INCIDENTE','TOMBAMENTO',
            'CALENDARIO','DATA','SAFRA',
            'Z_DTHR','Z_ULT_ATUALIZACAO','Z_LEGENDAS'
        )
    }

    $tabelasMap[$dsNome] = $tabelas
    Write-Host "  Extraindo $($tabelas.Count) tabelas..."

    foreach ($t in $tabelas) {
        $res = DAX-Extrair $dsId $dsNome $t
        if ($res -eq 'skip') { }
        elseif ($res.StartsWith('ok:')) {
            $n = [int]($res.Split(':')[1])
            Write-Host "  OK  $dsNome.$t ($n linhas)"
            $resumo += [PSCustomObject]@{Dataset=$dsNome; Tabela=$t; Linhas=$n}
        }
        elseif ($res -eq 'vazia') {
            Write-Host "  --  $dsNome.$t (vazia)"
        }
        # nao_existe e erro: silencioso
    }

    # Salvar lista de tabelas do dataset
    if ($tabelas.Count -gt 0) {
        $tabelas | Out-File "$outDir\${dsNome}_TABELAS.txt" -Encoding UTF8
    }
    Write-Host ''
}

# ============================================================
# PASSO 4: Gerar Dashboard HTML
# ============================================================
Write-Host '[4/4] Gerando Dashboard HTML...'

$dashPy = "$baseDir\09-SCRIPTS\pbi-dashboard-manutencao.py"
python -X utf8 $dashPy 2>&1

# ============================================================
# RESULTADO FINAL
# ============================================================
Write-Host ''
Write-Host '======================================================='
Write-Host '  RESULTADO FINAL - MANUTENCAO PREMIUM'
Write-Host '======================================================='
Write-Host "  Datasets: $($datasets.Count) | Reports: $($reports.Count)"
Write-Host "  Tabelas extraidas: $($resumo.Count)"
Write-Host ''
$resumo | Sort-Object Dataset,Tabela | Format-Table Dataset,Tabela,Linhas -AutoSize
Write-Host ''
Write-Host '  JSONs em:'
Get-ChildItem "$outDir\*.json" | Where-Object { $_.Length -gt 500 } | Sort-Object Name | ForEach-Object {
    Write-Host "    $($_.Name) ($([Math]::Round($_.Length/1KB,0)) KB)"
}
Write-Host ''
Write-Host "  Dashboard: $relDir\UMOE_Dashboard_Manutencao.html"
Write-Host '======================================================='
pause
