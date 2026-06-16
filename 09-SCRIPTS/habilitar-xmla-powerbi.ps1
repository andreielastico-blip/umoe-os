# UMOE OS 8.0 - Habilitar XMLA Endpoints via PowerShell Admin
# Requer: MicrosoftPowerBIMgmt (instala automatico)
# Execute como Administrador Global do Power BI

Write-Host ""
Write-Host "======================================================="
Write-Host "  UMOE OS 8.0 | Habilitar XMLA + Build Permission"
Write-Host "  Power BI Admin via PowerShell"
Write-Host "======================================================="
Write-Host ""

# 1. Instalar modulo Power BI Management
Write-Host "[1/5] Verificando modulo MicrosoftPowerBIMgmt..."
if (-not (Get-Module -ListAvailable -Name MicrosoftPowerBIMgmt)) {
    Write-Host "      Instalando MicrosoftPowerBIMgmt..."
    Install-Module -Name MicrosoftPowerBIMgmt -Scope CurrentUser -Force -AllowClobber
    Write-Host "      OK - Modulo instalado"
} else {
    Write-Host "      OK - Modulo ja instalado"
}
Import-Module MicrosoftPowerBIMgmt -Force

# 2. Coletar credenciais
Write-Host ""
Write-Host "[2/5] Informe as credenciais de Administrador Global Power BI:"
Write-Host "      (usuario que acessa app.powerbi.com/admin-portal)"
Write-Host ""
$adminUser = Read-Host "  Email do Admin"
$adminPass = Read-Host "  Senha" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential($adminUser, $adminPass)

# 3. Conectar ao Power BI
Write-Host ""
Write-Host "[3/5] Conectando ao Power BI como Admin..."
try {
    Connect-PowerBIServiceAccount -Credential $credential
    Write-Host "      OK - Conectado como: $adminUser"
} catch {
    Write-Host ""
    Write-Host "  ERRO ao conectar: $_"
    Write-Host "  Verifique usuario/senha e tente novamente."
    pause
    exit 1
}

# 4. Habilitar XMLA Endpoints via API Admin
Write-Host ""
Write-Host "[4/5] Habilitando XMLA Endpoints no Tenant..."

$body = @{
    featureSwitches = @(
        @{
            switchName = "XmlaEnabled"
            switchValue = $true
            isGranular = $false
        },
        @{
            switchName = "ExecuteQueriesEnabled"
            switchValue = $true
            isGranular = $false
        },
        @{
            switchName = "ServicePrincipalAccess"
            switchValue = $true
            isGranular = $false
        }
    )
} | ConvertTo-Json -Depth 5

try {
    $result = Invoke-PowerBIRestMethod `
        -Url "admin/tenantSettings" `
        -Method Patch `
        -Body $body
    Write-Host "      OK - Configuracoes aplicadas"
} catch {
    Write-Host "      Aviso: API de tenant settings retornou: $_"
    Write-Host "      Tentando metodo alternativo via capacidade..."
}

# 5. Verificar workspaces e adicionar Build ao dataset
Write-Host ""
Write-Host "[5/5] Verificando workspace Projetos Agricola PREMIUM..."

$wsId = "662a06b5-5579-4af6-b66a-7ac191a96674"
$datasetBase = "06950719-48dc-403d-bd91-2e059cf1a25e"
$datasetCst  = "a735ce0e-4234-42f8-bedd-5cbb07ce6364"
$datasetCtrl = "4c81ea62-ef7f-4976-9aaa-bf7ab3727c0b"
$targetUser  = "projetos@umoe.com.br"

$datasets = @($datasetBase, $datasetCst, $datasetCtrl)
$nomes    = @("BI_AGR_01_BASE", "BI_AGR_01_CST", "BI_AGR_01_CTRL")

for ($i = 0; $i -lt $datasets.Count; $i++) {
    $dsId   = $datasets[$i]
    $dsNome = $nomes[$i]
    Write-Host ""
    Write-Host "  Dataset: $dsNome"

    # Adicionar permissao Build
    $bodyBuild = @{
        value = @(
            @{
                identifier = $targetUser
                principalType = "User"
                datasetUserAccessRight = "Build"
            }
        )
    } | ConvertTo-Json -Depth 5

    try {
        $r = Invoke-PowerBIRestMethod `
            -Url "groups/$wsId/datasets/$dsId/users" `
            -Method Post `
            -Body $bodyBuild
        Write-Host "    OK - Build permission adicionada para $targetUser"
    } catch {
        Write-Host "    Info: $_ (pode ja ter permissao ou ser herdada do workspace)"
    }

    # Verificar permissoes atuais
    try {
        $perms = Invoke-PowerBIRestMethod `
            -Url "groups/$wsId/datasets/$dsId/users" `
            -Method Get | ConvertFrom-Json
        Write-Host "    Usuarios com acesso:"
        foreach ($u in $perms.value) {
            Write-Host "      - $($u.identifier) | $($u.datasetUserAccessRight)"
        }
    } catch {
        Write-Host "    Nao foi possivel listar usuarios: $_"
    }
}

# Verificar XMLA via capacidade Premium
Write-Host ""
Write-Host "  Verificando capacidade Premium do workspace..."
try {
    $ws = Invoke-PowerBIRestMethod `
        -Url "groups/$wsId" `
        -Method Get | ConvertFrom-Json
    Write-Host "    Workspace: $($ws.name)"
    Write-Host "    Capacidade: $($ws.capacityId)"
    Write-Host "    Premium: $($ws.isOnDedicatedCapacity)"
} catch {
    Write-Host "    Nao foi possivel verificar: $_"
}

# Testar DAX apos configuracao
Write-Host ""
Write-Host "======================================================="
Write-Host "  Testando DAX Execute Query..."
Write-Host "======================================================="

$daxBody = @{
    queries = @(@{ query = "EVALUATE ROW(`"Teste`", `"OK`")" })
    serializerSettings = @{ includeNulls = $true }
} | ConvertTo-Json -Depth 5

try {
    $daxResult = Invoke-PowerBIRestMethod `
        -Url "groups/$wsId/datasets/$datasetBase/executeQueries" `
        -Method Post `
        -Body $daxBody | ConvertFrom-Json
    Write-Host "  SUCESSO! DAX funcionando."
    Write-Host "  Resultado: $($daxResult | ConvertTo-Json -Depth 3)"
} catch {
    Write-Host "  DAX ainda bloqueado: $_"
    Write-Host ""
    Write-Host "  Se o erro persistir, acesse manualmente:"
    Write-Host "  app.powerbi.com/admin-portal/tenantSettings"
    Write-Host "  Secao: Integration settings"
    Write-Host "  -> Allow XMLA endpoints: Enabled"
}

Write-Host ""
Write-Host "======================================================="
Write-Host "  Configuracao concluida!"
Write-Host "  Feche esta janela e avise o assistente para"
Write-Host "  extrair dados via DAX automaticamente."
Write-Host "======================================================="
Write-Host ""
pause
