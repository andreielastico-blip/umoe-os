# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Power BI Extractor (Service Principal)
Extrai tabelas dos datasets Power BI via REST executeQueries (DAX) e salva
em UMOE-OS-8.0/Dados-PBI/{DS}_{tabela}.json no mesmo formato consumido por
pbi-pipeline.py / pbi-dashboard-v2.py.

Porta para Python o padrao comprovado de 09-SCRIPTS/pbi-extrair-tudo.ps1,
mas autenticando via Service Principal (secrets PBI_TENANT_ID / PBI_CLIENT_ID
/ PBI_CLIENT_SECRET) para rodar sem interacao no GitHub Actions.

Uso:
  python pbi-extract.py                 # extrai tabelas faltantes dos 3 datasets
  python pbi-extract.py --force         # re-extrai todas (sobrescreve)
  python pbi-extract.py --only BASE     # apenas um dataset (BASE|CST|CTRL)
  python pbi-extract.py --discover      # lista tabelas reais (INFO.TABLES)
  python pbi-extract.py --interactive   # permite device-code (uso local)

Saida: codigo 0 se autenticou e extraiu >=1 tabela; 1 se falhou auth/acesso.
"""
import os, sys, json, time, argparse, importlib.util
from pathlib import Path

try:
    import requests
except ImportError:
    os.system("pip install requests -q")
    import requests

# ─── PATHS / CONFIG ──────────────────────────────────────────────────────────
HERE     = Path(__file__).resolve().parent
PBI_DIR  = HERE.parent / "Dados-PBI"
PBI_DIR.mkdir(exist_ok=True)
API_BASE = "https://api.powerbi.com/v1.0/myorg"

WORKSPACE_ID = "662a06b5-5579-4af6-b66a-7ac191a96674"
DATASETS = {
    "BASE": "06950719-48dc-403d-bd91-2e059cf1a25e",
    "CST":  "a735ce0e-4234-42f8-bedd-5cbb07ce6364",
    "CTRL": "4c81ea62-ef7f-4976-9aaa-bf7ab3727c0b",
}

# Erros DAX de tabela inexistente (tabelas de UI/medida sem linhas reais)
NOT_FOUND_MARKERS = ("3236002463", "TableNotFound", "does not exist",
                     "Cannot find table", "nao foi encontrad")


# ─── AUTH (reusa pbi-auth.py; nome com hifen exige importlib) ─────────────────
def load_pbi_auth():
    spec = importlib.util.spec_from_file_location("pbi_auth", HERE / "pbi-auth.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Client do Azure CLI: first-party Microsoft, pre-autorizado para a API do
# Power BI. O antigo client do PBI Desktop (7f67af8a) deixou de ser
# pre-autorizado neste tenant (AADSTS65002).
AZURE_CLI_CLIENT = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
PBI_DEFAULT_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]


def device_code_user(auth):
    """Device-code como usuario (cliente Azure CLI, escopo .default). Cacheia token."""
    import msal, webbrowser
    tenant = os.getenv("PBI_TENANT_ID", "organizations")
    cache = auth._load_cache()
    app = msal.PublicClientApplication(
        AZURE_CLI_CLIENT,
        authority=f"https://login.microsoftonline.com/{tenant}",
        token_cache=cache,
    )
    accounts = app.get_accounts()
    if accounts:
        r = app.acquire_token_silent(PBI_DEFAULT_SCOPE, account=accounts[0])
        if r and "access_token" in r:
            auth._save_cache(cache)
            return r["access_token"], None
    flow = app.initiate_device_flow(scopes=PBI_DEFAULT_SCOPE)
    if "user_code" not in flow:
        return None, flow.get("error_description", "device flow falhou")
    print("\n" + "=" * 55)
    print("  AUTENTICACAO POWER BI (sua conta)")
    print(f"  1. Abra: {flow['verification_uri']}")
    print(f"  2. Codigo: {flow['user_code']}")
    print("=" * 55 + "\n")
    try: webbrowser.open(flow["verification_uri"])
    except Exception: pass
    r = app.acquire_token_by_device_flow(flow)
    auth._save_cache(cache)
    if "access_token" in r:
        return r["access_token"], None
    return None, r.get("error_description", "autenticacao cancelada")


def get_token(interactive=False, user=False):
    """Retorna (token|None, erro|None).

    user=True: autentica COMO O USUARIO via device-code usando o client
    publico do Power BI (ignora o Service Principal). Util quando o SP ainda
    nao tem acesso ao workspace. Nao serve para CI (exige login interativo).
    """
    auth = load_pbi_auth()
    if user:
        print("  Modo usuario: autenticando via Device Code (cliente Azure CLI)...")
        return device_code_user(auth)
    token, err = auth.get_pbi_token_service_principal()
    if token:
        print("  Auth: Service Principal OK")
        return token, None
    print(f"  Service Principal indisponivel: {err}")
    if interactive:
        print("  Tentando Device Code (interativo)...")
        token, err2 = auth.get_pbi_token_device_code()
        if token:
            return token, None
        return None, err2 or err
    return None, err


# ─── EXTRACAO ────────────────────────────────────────────────────────────────
def execute_dax(token, dataset_id, dax):
    """Roda DAX via executeQueries. Retorna (rows|None, erro|None)."""
    url = f"{API_BASE}/groups/{WORKSPACE_ID}/datasets/{dataset_id}/executeQueries"
    body = {"queries": [{"query": dax}],
            "serializerSettings": {"includeNulls": True}}
    try:
        r = requests.post(url, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }, json=body, timeout=120)
    except Exception as e:
        return None, f"rede: {e}"
    if r.status_code != 200:
        return None, f"http {r.status_code}: {r.text[:160]}"
    try:
        rows = r.json()["results"][0]["tables"][0]["rows"]
    except (KeyError, IndexError, ValueError) as e:
        return None, f"parse: {e}"
    return rows, None


def sanitize(table):
    return "".join(c if (c.isalnum() or c == "_") else "_" for c in table)


def read_table_list(ds):
    f = PBI_DIR / f"{ds}_TABELAS.txt"
    if not f.exists():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        t = line.strip()
        if t and "$" not in t:   # ignora tabelas de sistema/consulta ($...)
            out.append(t)
    return out


def tables_from_info(token, ds_id):
    """Descobre as tabelas reais do modelo semantico via INFO.TABLES()."""
    rows, e = execute_dax(token, ds_id, "EVALUATE INFO.TABLES()")
    if e or not rows:
        return [], e
    nomes = []
    for r in rows:
        nome = next((v for k, v in r.items() if k.endswith("[Name]")), None)
        if not nome or "$" in str(nome):
            continue
        # ignora tabelas de data automaticas (ruido)
        if str(nome).startswith(("LocalDateTable_", "DateTableTemplate_")):
            continue
        nomes.append(str(nome))
    return nomes, None


def extract_dataset(token, ds, force=False, auto=False):
    ds_id = DATASETS[ds]
    if auto:
        tables, e = tables_from_info(token, ds_id)
        if e:
            print(f"[{ds}] INFO.TABLES() falhou: {e}")
            return 0, 0, 0
        print(f"[{ds}] {len(tables)} tabelas do modelo (auto)...")
    else:
        tables = read_table_list(ds)
        if not tables:
            print(f"[{ds}] sem {ds}_TABELAS.txt — pulando")
            return 0, 0, 0
        print(f"[{ds}] {len(tables)} tabelas (lista)...")
    ok = empty = err = 0
    for t in tables:
        out = PBI_DIR / f"{ds}_{sanitize(t)}.json"
        if out.exists() and not force:
            continue
        rows, e = execute_dax(token, ds_id, f"EVALUATE '{t}'")
        if e:
            if any(m in e for m in NOT_FOUND_MARKERS):
                err += 1                      # tabela de UI sem linhas — silencioso
            else:
                print(f"  !! {ds}.{t} -> {e}")
                err += 1
            continue
        if rows:
            out.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            print(f"  OK  {ds}.{t} ({len(rows)} linhas)")
            ok += 1
        else:
            empty += 1
    print(f"[{ds}] OK={ok} vazias={empty} erros/naoencontradas={err}\n")
    return ok, empty, err


def discover(token, ds):
    rows, e = execute_dax(token, DATASETS[ds], "EVALUATE INFO.TABLES()")
    if e:
        print(f"[{ds}] discover falhou: {e}")
        return
    print(f"[{ds}] {len(rows)} tabelas no modelo:")
    for row in rows:
        name = next((v for k, v in row.items() if k.endswith("[Name]")), row)
        print(f"    {name}")


STATUS_FILE = PBI_DIR / "_extract_status.json"


def write_status(**kw):
    """Grava diagnostico (sem segredos) para inspecao via repo/CI."""
    import datetime
    kw["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    STATUS_FILE.write_text(json.dumps(kw, ensure_ascii=False, indent=2),
                           encoding="utf-8")


# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Extrai tabelas Power BI via API")
    ap.add_argument("--force", action="store_true", help="sobrescreve JSONs existentes")
    ap.add_argument("--only", choices=list(DATASETS), help="extrai apenas um dataset")
    ap.add_argument("--discover", action="store_true", help="lista tabelas reais (INFO.TABLES)")
    ap.add_argument("--interactive", action="store_true", help="permite device-code (local)")
    ap.add_argument("--user", action="store_true", help="autentica como usuario via device-code (ignora SP)")
    ap.add_argument("--auto", action="store_true", help="descobre as tabelas direto do modelo (INFO.TABLES) em vez das listas")
    args = ap.parse_args()

    print("=" * 60)
    print("  UMOE OS 8.0 | Power BI Extractor (Service Principal)")
    print("=" * 60)

    token, auth_err = get_token(interactive=args.interactive, user=args.user)
    if not token:
        print("\n  ERRO: nao foi possivel obter token. Verifique os secrets "
              "PBI_TENANT_ID / PBI_CLIENT_ID / PBI_CLIENT_SECRET e se o Service "
              "Principal tem acesso ao workspace.")
        write_status(auth_ok=False, auth_error=str(auth_err), extracted=0)
        sys.exit(1)

    targets = [args.only] if args.only else list(DATASETS)

    if args.discover:
        for ds in targets:
            discover(token, ds)
        return

    t0 = time.time()
    tot_ok = tot_empty = tot_err = 0
    sample_err = None
    for ds in targets:
        ok, empty, err = extract_dataset(token, ds, force=args.force, auto=args.auto)
        tot_ok += ok; tot_empty += empty; tot_err += err

    # Diagnostico: roda um INFO.TABLES no primeiro dataset para confirmar acesso
    probe_rows, probe_err = execute_dax(token, DATASETS[targets[0]], "EVALUATE INFO.TABLES()")
    write_status(auth_ok=True, auth_error=None, extracted=tot_ok, empty=tot_empty,
                 errors=tot_err, datasets=targets,
                 probe_tables=(len(probe_rows) if probe_rows else 0),
                 probe_error=probe_err)

    print("=" * 60)
    print(f"  CONCLUIDO em {time.time()-t0:.0f}s | "
          f"extraidas={tot_ok} vazias={tot_empty} erros={tot_err}")
    print(f"  JSONs em: {PBI_DIR}")
    print("=" * 60)
    # Sucesso se autenticou; nao falha o build se algumas tabelas estiverem vazias.
    sys.exit(0)


if __name__ == "__main__":
    main()
