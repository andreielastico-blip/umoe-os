# UMOE OS 8.0 - Configurar Service Principal Power BI
# Cria o App Registration (manual no portal), captura as credenciais e grava .env
# Execute como ADMINISTRADOR. Encoding: ASCII puro (sem acentos / box-drawing).

Write-Host ""
Write-Host "======================================================="
Write-Host "  UMOE OS 8.0 | Configurar Service Principal Power BI"
Write-Host "======================================================="
Write-Host ""

# 1. Instalar libs Python necessarias ao extrator
Write-Host "[1/5] Instalando bibliotecas Python (msal, dotenv, requests)..."
python -m pip install msal python-dotenv requests --quiet
Write-Host "      OK"

# 2. Instrucoes do portal Azure (here-string: imune a aspas/parenteses)
Write-Host ""
Write-Host "[2/5] Crie o App Registration no portal Azure:"
$instr = @'
  -----------------------------------------------------------
  a) Em "App registrations", clique "New registration"
  b) Nome: UMOE-OS-BI-Agent
  c) Supported account types: Single tenant
  d) Clique "Register"
  e) Copie o Application (client) ID e o Directory (tenant) ID
  f) Va em "Certificates & secrets" > "New client secret"
  g) Descricao: UMOE Pipeline | Expires: 24 months
  h) Copie o VALUE do secret (aparece so uma vez!)
  -----------------------------------------------------------
'@
Write-Host $instr

# 3. Abrir o portal
Write-Host "[3/5] Abrindo o portal Azure (App registrations)..."
Start-Process "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
Start-Sleep 2

# 4. Coletar credenciais
Write-Host ""
Write-Host "[4/5] Informe as credenciais criadas:"
$tenantId     = Read-Host "  Tenant ID (Directory ID)"
$clientId     = Read-Host "  Client ID (Application ID)"
$clientSecret = Read-Host "  Client Secret (VALUE)"

if (-not $tenantId -or -not $clientId -or -not $clientSecret) {
    Write-Host "  ERRO: Todos os campos sao obrigatorios"
    exit 1
}

# 5. Gravar .env (UTF-8) na raiz do repo
$envPath = "C:\01 - UMOE\09 - IA\umoe-os-8\.env"
$envContent = @"
# UMOE OS 8.0 - Credenciais (NAO commitar - ja esta no .gitignore)
PBI_TENANT_ID=$tenantId
PBI_CLIENT_ID=$clientId
PBI_CLIENT_SECRET=$clientSecret
"@
$envContent | Out-File $envPath -Encoding UTF8 -Force
Write-Host ""
Write-Host "[5/5] Credenciais salvas em: $envPath"
Write-Host ""

# Passo final - permissoes no Power BI
$perm = @'
  PASSO FINAL - Permissoes Power BI (abrindo o Admin portal):
  -----------------------------------------------------------
  1. Tenant settings > Developer settings
     "Allow service principals to use Power BI APIs" -> Enabled
     (aplicar a um grupo de seguranca que contenha o UMOE-OS-BI-Agent)
  2. No workspace 662a06b5-5579-4af6-b66a-7ac191a96674:
     Manage access > Add people > UMOE-OS-BI-Agent como Member
  -----------------------------------------------------------
'@
Write-Host $perm
Start-Process "https://app.powerbi.com/admin-portal/tenantSettings"

# Testar autenticacao
Write-Host ""
$test = Read-Host "Testar conexao agora? (s/n)"
if ($test -eq "s") {
    python "C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\01-AGENTE-AUTONOMO\pbi-extract.py" --discover
}

Write-Host ""
Write-Host "  Configuracao concluida. O pipeline usara o Service Principal automaticamente."
Write-Host ""
