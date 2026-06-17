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


def get_token(interactive=False):
    auth = load_pbi_auth()
    token, err = auth.get_pbi_token_service_principal()
    if token:
        print("  Auth: Service Principal OK")
        return token
    print(f"  Service Principal indisponivel: {err}")
    if interactive:
        print("  Tentando Device Code (interativo)...")
        token, err = auth.get_pbi_token_device_code()
        if token:
            return token
    return None


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


def extract_dataset(token, ds, force=False):
    ds_id = DATASETS[ds]
    tables = read_table_list(ds)
    if not tables:
        print(f"[{ds}] sem {ds}_TABELAS.txt — pulando")
        return 0, 0, 0
    print(f"[{ds}] {len(tables)} tabelas...")
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


# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Extrai tabelas Power BI via API")
    ap.add_argument("--force", action="store_true", help="sobrescreve JSONs existentes")
    ap.add_argument("--only", choices=list(DATASETS), help="extrai apenas um dataset")
    ap.add_argument("--discover", action="store_true", help="lista tabelas reais (INFO.TABLES)")
    ap.add_argument("--interactive", action="store_true", help="permite device-code (local)")
    args = ap.parse_args()

    print("=" * 60)
    print("  UMOE OS 8.0 | Power BI Extractor (Service Principal)")
    print("=" * 60)

    token = get_token(interactive=args.interactive)
    if not token:
        print("\n  ERRO: nao foi possivel obter token. Verifique os secrets "
              "PBI_TENANT_ID / PBI_CLIENT_ID / PBI_CLIENT_SECRET e se o Service "
              "Principal tem acesso ao workspace.")
        sys.exit(1)

    targets = [args.only] if args.only else list(DATASETS)

    if args.discover:
        for ds in targets:
            discover(token, ds)
        return

    t0 = time.time()
    tot_ok = tot_empty = tot_err = 0
    for ds in targets:
        ok, empty, err = extract_dataset(token, ds, force=args.force)
        tot_ok += ok; tot_empty += empty; tot_err += err

    print("=" * 60)
    print(f"  CONCLUIDO em {time.time()-t0:.0f}s | "
          f"extraidas={tot_ok} vazias={tot_empty} erros={tot_err}")
    print(f"  JSONs em: {PBI_DIR}")
    print("=" * 60)
    # Sucesso se autenticou; nao falha o build se algumas tabelas estiverem vazias.
    sys.exit(0)


if __name__ == "__main__":
    main()
