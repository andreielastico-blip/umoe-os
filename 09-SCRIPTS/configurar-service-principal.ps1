# UMOE OS 8.0 - Configurar Service Principal Power BI
# Instala MSAL, abre portal Azure e guia o usuario
# Execute como ADMINISTRADOR

Write-Host ""
Write-Host "======================================================="
Write-Host "  UMOE OS 8.0 | Configurar Service Principal Power BI"
Write-Host "======================================================="
Write-Host ""

# 1. Instalar msal para Python
Write-Host "[1/5] Instalando biblioteca msal (Python)..."
python -m pip install msal python-dotenv requests --quiet
Write-Host "      OK"

# 2. Coletar Tenant ID automaticamente (via token ja salvo no browser)
Write-Host ""
Write-Host "[2/5] Detectando Tenant ID do Power BI..."
$tenantId = ""
try {
    $resp = Invoke-RestMethod "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration" -ErrorAction Stop
    Write-Host "      Use o Tenant ID da sua organizacao (ver passo 3)"
} catch {
    Write-Host "      Nao foi possivel detectar automaticamente"
}

# 3. Abrir portal Azure para criar App Registration
Write-Host ""
Write-Host "[3/5] Abrindo portal Azure para criar App Registration..."
Write-Host ""
Write-Host "  INSTRUCOES NO PORTAL AZURE:"
Write-Host "  ─────────────────────────────────────────────────────"
Write-Host "  a) Em 'App registrations', clique 'New registration'"
Write-Host "  b) Nome: 'UMOE-OS-BI-Agent'"
Write-Host "  c) Supported account types: Single tenant"
Write-Host "  d) Clique 'Register'"
Write-Host "  e) Copie o 'Application (client) ID' e o 'Directory (tenant) ID'"
Write-Host "  f) Va em 'Certificates & secrets' > 'New client secret'"
Write-Host "  g) Descricao: 'UMOE Pipeline' | Expires: 24 months"
Write-Host "  h) Copie o VALUE do secret (aparece so uma vez!)"
Write-Host "  ─────────────────────────────────────────────────────"
Write-Host ""
Start-Process "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
Start-Sleep 3

# 4. Coletar credenciais
Write-Host "[4/5] Informe as credenciais criadas:"
$tenantId     = Read-Host "  Tenant ID (Directory ID)"
$clientId     = Read-Host "  Client ID (Application ID)"
$clientSecret = Read-Host "  Client Secret (VALUE)"

if (-not $tenantId -or -not $clientId -or -not $clientSecret) {
    Write-Host "  ERRO: Todos os campos sao obrigatorios"
    exit 1
}

# 5. Salvar no .env
$envPath = "C:\01 - UMOE\09 - IA\umoe-os-8\.env"
$envContent = @"
# UMOE OS 8.0 - Credenciais (NAO commitar!)
PBI_TENANT_ID=$tenantId
PBI_CLIENT_ID=$clientId
PBI_CLIENT_SECRET=$clientSecret
GITHUB_TOKEN=
ANTHROPIC_API_KEY=
"@

$envContent | Out-File $envPath -Encoding UTF8 -Force
Write-Host ""
Write-Host "[5/5] Credenciais salvas em .env"
Write-Host ""

# Agora configurar permissoes no Power BI Admin portal
Write-Host "  PASSO FINAL - Permissoes Power BI:"
Write-Host "  ─────────────────────────────────────────────────────"
Write-Host "  1. Abra: app.powerbi.com/admin-portal"
Write-Host "  2. Va em 'Tenant settings'"
Write-Host "  3. 'Developer settings' > 'Allow service principals to use Power BI APIs'"
Write-Host "     -> Enable -> Apply to: Specific security groups"
Write-Host "     -> Adicione o app 'UMOE-OS-BI-Agent'"
Write-Host "  4. Adicione o Service Principal como Membro em cada workspace:"
Write-Host "     - Projetos Industria, Agricola PREMIUM, Manutencao PREMIUM"
Write-Host "     - Seguranca, Fiscal, Compras"
Write-Host "  ─────────────────────────────────────────────────────"
Write-Host ""
Start-Process "https://app.powerbi.com/admin-portal/tenantSettings"

# Testar autenticacao
Write-Host ""
$test = Read-Host "Testar conexao agora? (s/n)"
if ($test -eq "s") {
    python "C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\01-AGENTE-AUTONOMO\pbi-auth.py"
}

Write-Host ""
Write-Host "  Configuracao concluida!"
Write-Host "  Pipeline vai usar Service Principal automaticamente."
Write-Host ""
pause
