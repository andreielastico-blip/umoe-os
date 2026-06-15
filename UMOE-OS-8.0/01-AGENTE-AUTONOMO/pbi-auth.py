# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Power BI Auth Module
Autenticacao via Service Principal (Client Credentials) OU Device Code Flow.

Uso:
  from pbi-auth import get_pbi_token
  token = get_pbi_token()
"""
import os, sys, json, time, webbrowser
from pathlib import Path
from datetime import datetime, timedelta

try:
    import msal
except ImportError:
    os.system("pip install msal -q")
    import msal

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

# ─── CONFIG ──────────────────────────────────────────────────────────────────
PBI_SCOPE     = ["https://analysis.windows.net/powerbi/api/.default"]
PBI_AUTHORITY = "https://login.microsoftonline.com/{tenant_id}"
TOKEN_CACHE   = Path(__file__).parent.parent.parent / "config" / ".token_cache.json"
TOKEN_CACHE.parent.mkdir(exist_ok=True)

def _load_cache():
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE.exists():
        cache.deserialize(TOKEN_CACHE.read_text(encoding="utf-8"))
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        TOKEN_CACHE.write_text(cache.serialize(), encoding="utf-8")

def get_pbi_token_service_principal():
    """Autentica via Service Principal (ideal para automacao)."""
    tenant_id     = os.getenv("PBI_TENANT_ID")
    client_id     = os.getenv("PBI_CLIENT_ID")
    client_secret = os.getenv("PBI_CLIENT_SECRET")

    if not all([tenant_id, client_id, client_secret]):
        return None, "Variaveis PBI_TENANT_ID / PBI_CLIENT_ID / PBI_CLIENT_SECRET nao definidas"

    cache = _load_cache()
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=PBI_AUTHORITY.format(tenant_id=tenant_id),
        client_credential=client_secret,
        token_cache=cache
    )
    result = app.acquire_token_silent(PBI_SCOPE, account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=PBI_SCOPE)
    _save_cache(cache)
    if "access_token" in result:
        return result["access_token"], None
    return None, result.get("error_description", "Erro desconhecido")

def get_pbi_token_device_code():
    """Autentica via Device Code Flow (para uso interativo / primeiro setup)."""
    tenant_id = os.getenv("PBI_TENANT_ID", "common")
    client_id = os.getenv("PBI_CLIENT_ID")

    if not client_id:
        # Usar client ID publico do Power BI Desktop como fallback
        client_id = "7f67af8a-fedc-4b08-8b4e-37c4d127b6cf"

    cache = _load_cache()
    app = msal.PublicClientApplication(
        client_id,
        authority=PBI_AUTHORITY.format(tenant_id=tenant_id),
        token_cache=cache
    )

    # Tentar token em cache primeiro
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(
            ["https://analysis.windows.net/powerbi/api/Dataset.ReadWrite.All",
             "https://analysis.windows.net/powerbi/api/Report.Read.All"],
            account=accounts[0]
        )
        if result and "access_token" in result:
            _save_cache(cache)
            return result["access_token"], None

    # Device code flow
    flow = app.initiate_device_flow(
        scopes=["https://analysis.windows.net/powerbi/api/Dataset.ReadWrite.All",
                "https://analysis.windows.net/powerbi/api/Report.Read.All",
                "https://analysis.windows.net/powerbi/api/Workspace.Read.All"]
    )
    if "user_code" not in flow:
        return None, f"Erro no device flow: {flow.get('error_description')}"

    print(f"\n{'='*55}")
    print(f"  AUTENTICACAO POWER BI")
    print(f"  1. Abra: {flow['verification_uri']}")
    print(f"  2. Digite o codigo: {flow['user_code']}")
    print(f"{'='*55}\n")
    webbrowser.open(flow["verification_uri"])

    result = app.acquire_token_by_device_flow(flow)
    _save_cache(cache)

    if "access_token" in result:
        print("  Token obtido com sucesso!")
        return result["access_token"], None
    return None, result.get("error_description", "Autenticacao cancelada")

def get_pbi_token():
    """
    Tenta Service Principal primeiro; fallback para Device Code.
    Retorna token string ou None.
    """
    # 1. Tentar Service Principal
    token, err = get_pbi_token_service_principal()
    if token:
        return token

    # 2. Fallback: Device Code (interativo)
    print(f"  Service Principal nao configurado ({err})")
    print("  Usando Device Code Flow (autenticacao pelo browser)...")
    token, err = get_pbi_token_device_code()
    if token:
        return token

    print(f"  Erro de autenticacao: {err}")
    return None

def test_connection(token):
    """Testa conexao com a API do Power BI."""
    import urllib.request
    req = urllib.request.Request(
        "https://api.powerbi.com/v1.0/myorg/groups",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        ws = data.get("value", [])
        print(f"\n  Conectado! {len(ws)} workspaces acessiveis:")
        for w in ws[:5]:
            print(f"    - {w['name']} ({w['id']})")
        return True

# ─── EXECUCAO DIRETA (SETUP/TESTE) ──────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  UMOE OS 8.0 | Power BI Auth Setup")
    print("=" * 55)

    # Verificar .env
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        print(f"  .env encontrado: {env_path}")
    else:
        print(f"  .env nao encontrado. Criando template...")
        env_path.write_text(
            "PBI_TENANT_ID=\nPBI_CLIENT_ID=\nPBI_CLIENT_SECRET=\n"
            "GITHUB_TOKEN=\nANTHROPIC_API_KEY=\n",
            encoding="utf-8"
        )

    token = get_pbi_token()
    if token:
        test_connection(token)
        print("\n  Auth OK! Token salvo em config/.token_cache.json")
    else:
        print("\n  Falha na autenticacao.")
        sys.exit(1)
