# UMOE OS 8.0 - Descobrir tabelas reais dos datasets Power BI via INFO.TABLES()
# Execute PRIMEIRO para mapear estrutura antes de extrair dados

Import-Module MicrosoftPowerBIMgmt -Force

$adminUser = Read-Host "  Email Power BI"
$adminPass = Read-Host "  Senha" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential($adminUser, $adminPass)
Connect-PowerBIServiceAccount -Credential $credential | Out-Null
Write-Host "  Conectado como: $adminUser"
Write-Host ""

$wsId    = "662a06b5-5579-4af6-b66a-7ac191a96674"
$outDir  = "C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Dados-PBI"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

$datasets = @{
    "BASE" = "06950719-48dc-403d-bd91-2e059cf1a25e"
    "CST"  = "a735ce0e-4234-42f8-bedd-5cbb07ce6364"
    "CTRL" = "4c81ea62-ef7f-4976-9aaa-bf7ab3727c0b"
}

foreach ($nome in $datasets.Keys) {
    $dsId = $datasets[$nome]
    Write-Host "======= $nome ======================================="

    # Listar tabelas
    $body = @{
        queries = @(@{ query = "EVALUATE INFO.TABLES()" })
        serializerSettings = @{ includeNulls = $true }
    } | ConvertTo-Json -Depth 10

    try {
        $r = Invoke-PowerBIRestMethod -Url "groups/$wsId/datasets/$dsId/executeQueries" -Method Post -Body $body | ConvertFrom-Json
        $rows = $r.results[0].tables[0].rows
        $rows | ConvertTo-Json -Depth 3 | Out-File "$outDir\${nome}_INFO_TABLES.json" -Encoding UTF8
        Write-Host "  Tabelas ($($rows.Count)):"
        foreach ($t in $rows) {
            $tName = $t.'[Name]'
            if ($tName -and -not $tName.StartsWith('$')) {
                Write-Host "    - $tName"

                # Listar colunas de cada tabela
                $bodyCol = @{
                    queries = @(@{ query = "EVALUATE SELECTCOLUMNS(FILTER(INFO.COLUMNS(), [TableID] = $($t.'[ID]')), `"Col`", [ExplicitName])" })
                    serializerSettings = @{ includeNulls = $true }
                } | ConvertTo-Json -Depth 10

                try {
                    $rc = Invoke-PowerBIRestMethod -Url "groups/$wsId/datasets/$dsId/executeQueries" -Method Post -Body $bodyCol | ConvertFrom-Json
                    $cols = $rc.results[0].tables[0].rows
                    if ($cols) {
                        foreach ($c in $cols) { Write-Host "        . $($c.'[Col]')" }
                    }
                } catch {}
            }
        }
    } catch {
        Write-Host "  ERRO: $_"
    }
    Write-Host ""
}

Write-Host "Estrutura salva em: $outDir\*_INFO_TABLES.json"
Write-Host "Use os nomes exatos das tabelas/colunas no script extrair-dados-pbi.ps1"
pause
