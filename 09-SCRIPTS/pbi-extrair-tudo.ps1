# UMOE OS 8.0 - Extracao total: 115 tabelas dos 3 datasets via DAX
# Listas de tabelas extraidas do PBIX por parse-pbix.py
Import-Module MicrosoftPowerBIMgmt -Force

$wsId   = '662a06b5-5579-4af6-b66a-7ac191a96674'
$outDir = 'C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Dados-PBI'
$tabDir = $outDir

$ids = @{
    BASE = '06950719-48dc-403d-bd91-2e059cf1a25e'
    CST  = 'a735ce0e-4234-42f8-bedd-5cbb07ce6364'
    CTRL = '4c81ea62-ef7f-4976-9aaa-bf7ab3727c0b'
}

Write-Host '======================================================='
Write-Host '  UMOE OS 8.0 | Extracao Total via DAX - 115 tabelas'
Write-Host '======================================================='
$adminUser = Read-Host '  Email'
$adminPass = Read-Host '  Senha' -AsSecureString
$cred = New-Object System.Management.Automation.PSCredential($adminUser, $adminPass)
Connect-PowerBIServiceAccount -Credential $cred | Out-Null
Write-Host '  Conectado.'
Write-Host ''

function DAX-Extrair($dsId, $ds, $tabela) {
    $arq = ($ds + '_' + ($tabela -replace '[^a-zA-Z0-9_]','_'))
    $fp  = Join-Path $outDir "$arq.json"
    if (Test-Path $fp) { return 'skip' }

    $q    = "EVALUATE '$tabela'"
    $body = '{"queries":[{"query":"' + $q.Replace('"','\"') + '"}],"serializerSettings":{"includeNulls":true}}'
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
        if ($msg -like '*3236002463*' -or $msg -like '*TableNotFound*' -or $msg -like '*does not exist*') {
            return 'naoencontrada'
        }
        return "erro:$($msg.Substring(0,[Math]::Min(60,$msg.Length)))"
    }
}

$resumo = @()
$totalSkip = 0
$totalOk   = 0
$totalErro = 0
$totalVazia = 0

foreach ($ds in @('BASE','CST','CTRL')) {
    $dsId    = $ids[$ds]
    $arquivo = Join-Path $tabDir "${ds}_TABELAS.txt"
    if (-not (Test-Path $arquivo)) {
        Write-Host "  AVISO: $arquivo nao encontrado"
        continue
    }
    $tabelas = Get-Content $arquivo -Encoding UTF8 | Where-Object { $_ -and $_.Trim() -ne '' -and $_ -notlike '*$*' }
    Write-Host "[$ds] $($tabelas.Count) tabelas para extrair..."
    Write-Host ''

    foreach ($t in $tabelas) {
        $res = DAX-Extrair $dsId $ds $t
        if ($res -eq 'skip') {
            $totalSkip++
        } elseif ($res.StartsWith('ok:')) {
            $n = [int]($res.Split(':')[1])
            Write-Host "  OK  $ds.$t ($n linhas)"
            $resumo += [PSCustomObject]@{Dataset=$ds; Tabela=$t; Linhas=$n; Status='OK'}
            $totalOk++
        } elseif ($res -eq 'vazia') {
            Write-Host "  --  $ds.$t (vazia)"
            $resumo += [PSCustomObject]@{Dataset=$ds; Tabela=$t; Linhas=0; Status='Vazia'}
            $totalVazia++
        } elseif ($res -eq 'naoencontrada') {
            # silencioso - tabela de UI/medida sem linhas reais
            $totalErro++
        } else {
            Write-Host "  !! $ds.$t -> $res"
            $totalErro++
        }
    }
    Write-Host ''
}

Write-Host '======================================================='
Write-Host '  RESULTADO FINAL'
Write-Host '======================================================='
Write-Host "  Extraidas: $totalOk | Vazias: $totalVazia | Skip(existia): $totalSkip | Erro: $totalErro"
Write-Host ''
$resumo | Where-Object { $_.Linhas -gt 0 } | Sort-Object Dataset,Tabela | Format-Table Dataset,Tabela,Linhas -AutoSize
Write-Host ''
Write-Host '  Todos os JSONs em:'
Get-ChildItem "$outDir\*.json" | Sort-Object Name | ForEach-Object {
    $kb = [Math]::Round($_.Length/1KB,0)
    Write-Host "    $($_.Name) ($kb KB)"
}
Write-Host ''
Write-Host '  Gerando Dashboard HTML automaticamente...'
$dashScript = 'C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\01-AGENTE-AUTONOMO\pbi-dashboard-v2.py'
if (Test-Path $dashScript) {
    python -X utf8 $dashScript
    $dashOut = 'C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Relatorios\UMOE_PBI_Dashboard.html'
    if (Test-Path $dashOut) {
        Write-Host "  Dashboard gerado: $dashOut"
        Write-Host '  Abrindo no navegador...'
        Start-Process $dashOut
    }
} else {
    Write-Host "  Script dashboard nao encontrado: $dashScript"
}
Write-Host '======================================================='
pause
