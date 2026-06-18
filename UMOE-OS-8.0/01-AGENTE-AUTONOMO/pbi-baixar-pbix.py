# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Download de PBIX + extracao de medidas DAX (formula verbatim)
Exporta o .pbix de relatorios (modelos) via REST e extrai as medidas DAX,
colunas calculadas, tabelas e relacionamentos com pbixray.

Saida: Dados-PBI/PBIX/<nome>.pbix  +  Dados-PBI/MEDIDAS_DAX_<nome>.json/.md
Auth: token de USUARIO em cache (config/.token_cache.json) ou device-code.
"""
import importlib.util, msal, requests, os, sys, json, time
from pathlib import Path

try:
    from dotenv import load_dotenv; load_dotenv(Path(__file__).parent.parent.parent / ".env")
except Exception: pass
try:
    from pbixray import PBIXRay
except ImportError:
    os.system("pip install pbixray -q"); from pbixray import PBIXRay

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PBIX_DIR = ROOT / "UMOE-OS-8.0" / "Dados-PBI" / "PBIX"
PBIX_DIR.mkdir(parents=True, exist_ok=True)
AZURE_CLI = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]

# Relatorios-modelo a baixar: nome -> (workspace_id, report_id)
RELATORIOS = {
    "BI_AGR_01_BASE": ("662a06b5-5579-4af6-b66a-7ac191a96674", "3be2f3d8-557a-4375-8f70-1e2694fbf95e"),
    "BI_AGR_01_CST":  ("662a06b5-5579-4af6-b66a-7ac191a96674", "0881949a-a6b2-4b11-a030-b183f2e67651"),
    "BI_AGR_01_CTRL": ("662a06b5-5579-4af6-b66a-7ac191a96674", "721b4394-4455-4bb6-971d-ef5244e66e07"),
    "MANUT_umoe_dataset": ("954ecb3e-1daf-4a98-8801-39f2026da2d8", "23193f71-f14b-4e67-886a-17791a5af32b"),
}

def get_token():
    auth_path = HERE / "pbi-auth.py"
    spec = importlib.util.spec_from_file_location("pbi_auth", auth_path)
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    cache = A._load_cache()
    tenant = os.getenv("PBI_TENANT_ID", "organizations")
    app = msal.PublicClientApplication(AZURE_CLI, authority=f"https://login.microsoftonline.com/{tenant}", token_cache=cache)
    accs = app.get_accounts()
    if accs:
        r = app.acquire_token_silent(SCOPE, account=accs[0])
        if r and "access_token" in r:
            A._save_cache(cache); return r["access_token"]
    # device-code
    flow = app.initiate_device_flow(scopes=SCOPE)
    print(f"\n  Abra {flow['verification_uri']} e digite: {flow['user_code']}\n")
    r = app.acquire_token_by_device_flow(flow); A._save_cache(cache)
    return r.get("access_token")

def baixar(tok, nome, ws, rid):
    fp = PBIX_DIR / f"{nome}.pbix"
    H = {"Authorization": f"Bearer {tok}"}
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{ws}/reports/{rid}/Export"
    for i in range(5):
        try:
            ex = requests.get(url, headers=H, timeout=300)
            break
        except Exception as e:
            print(f"  [{nome}] rede tentativa {i+1}: {str(e)[:50]}"); time.sleep(5); ex = None
    if ex is None: return None
    if ex.status_code != 200:
        print(f"  [{nome}] export HTTP {ex.status_code}: {ex.text[:150]}"); return None
    fp.write_bytes(ex.content)
    print(f"  [{nome}] PBIX {fp.stat().st_size//1024} KB")
    return fp

def extrair(nome, fp):
    try:
        m = PBIXRay(str(fp))
        med = m.dax_measures
        regs = [{"Table": r.get("TableName", r.get("Table","")), "Name": r.get("Name"),
                 "Expression": str(r.get("Expression",""))} for _, r in med.iterrows()]
        (PBIX_DIR.parent / f"MEDIDAS_DAX_{nome}.json").write_text(json.dumps(regs, ensure_ascii=False, indent=1), encoding="utf-8")
        # markdown legivel
        md = [f"# Medidas DAX — {nome} ({len(regs)})", ""]
        for r in regs:
            md.append(f"### {r['Table']}.{r['Name']}\n```dax\n{r['Expression']}\n```")
        (PBIX_DIR.parent / f"MEDIDAS_DAX_{nome}.md").write_text("\n".join(md), encoding="utf-8")
        print(f"  [{nome}] {len(regs)} medidas DAX extraidas")
        return len(regs)
    except Exception as e:
        print(f"  [{nome}] erro pbixray: {e}"); return 0

def main():
    alvo = sys.argv[1] if len(sys.argv) > 1 else None
    tok = get_token()
    if not tok: print("ERRO: sem token"); sys.exit(1)
    tot = 0
    for nome, (ws, rid) in RELATORIOS.items():
        if alvo and alvo.upper() not in nome.upper(): continue
        fp = baixar(tok, nome, ws, rid)
        if fp: tot += extrair(nome, fp)
    print(f"CONCLUIDO: {tot} medidas DAX (em Dados-PBI/MEDIDAS_DAX_*.md)")

if __name__ == "__main__":
    main()
