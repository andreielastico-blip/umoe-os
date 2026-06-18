# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Refresh da Disponibilidade REAL (medida DAX oficial)
Consulta a medida [Disponibilidade (%)] do dataset de Manutencao MES A MES
(cada mes e leve -> rapido; o historico inteiro de uma vez da timeout).
Periodo: 2025-01 ate o mes atual.

Saida: UMOE-OS-8.0/Dados-PBI/MANUT/disponibilidade_oficial.json
  { geral:{disp,meta}, mensal:[{ym,disp,meta}], categoria:[{cat,disp,meta}] }
"""
import importlib.util, msal, requests, os, json, time, calendar
from datetime import date
from pathlib import Path
try:
    from dotenv import load_dotenv; load_dotenv(Path(__file__).parent.parent.parent / ".env")
except Exception: pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT  = ROOT / "UMOE-OS-8.0" / "Dados-PBI" / "MANUT" / "disponibilidade_oficial.json"
WS   = "954ecb3e-1daf-4a98-8801-39f2026da2d8"
DS   = "aaa8d842-2606-4e11-ab87-f44a7abe320f"
AZURE_CLI = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]

def get_token():
    spec = importlib.util.spec_from_file_location("pbi_auth", HERE / "pbi-auth.py")
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    # 1) Usuario em cache (Azure CLI) — tem acesso ao workspace de Manutencao.
    #    (o Service Principal autentica mas NAO tem acesso -> daria 404)
    cache = A._load_cache()
    app = msal.PublicClientApplication(AZURE_CLI, authority=f"https://login.microsoftonline.com/{os.getenv('PBI_TENANT_ID','organizations')}", token_cache=cache)
    accs = app.get_accounts()
    if accs:
        r = app.acquire_token_silent(SCOPE, account=accs[0])
        if r and "access_token" in r:
            A._save_cache(cache); return r["access_token"]
    # 2) fallback: Service Principal
    t, _ = A.get_pbi_token_service_principal()
    return t

def dax(tok, q, timeout=90):
    for _ in range(3):
        try:
            r = requests.post(f"https://api.powerbi.com/v1.0/myorg/groups/{WS}/datasets/{DS}/executeQueries",
                              headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                              json={"queries": [{"query": q}]}, timeout=timeout)
            return r
        except Exception:
            time.sleep(3)
    return None

def filtro(ini, fim):
    return (f"FILTER(ALL(d_calendar[DATA]), d_calendar[DATA] >= DATE({ini.year},{ini.month},{ini.day})"
            f" && d_calendar[DATA] <= DATE({fim.year},{fim.month},{fim.day}))")

def main():
    import sys
    atual = "--atual" in sys.argv   # diario: so o mes corrente (rapido), mescla no historico
    tok = get_token()
    if not tok:
        print("ERRO: sem token (SP ou cache)."); return
    hoje = date.today()
    mensal = []
    if atual:
        meses = [(hoje.year, hoje.month)]
        if OUT.exists():   # carrega historico existente p/ mesclar
            try: mensal = [r for r in json.load(open(OUT,encoding="utf-8")).get("mensal",[]) if r["ym"] != f"{hoje.year}-{hoje.month:02d}"]
            except Exception: pass
    else:
        meses = []
        y, m = 2025, 1
        while (y < hoje.year) or (y == hoje.year and m <= hoje.month):
            meses.append((y, m)); m += 1
            if m > 12: y += 1; m = 1
    def salvar(cat=None):
        g = mensal[-1] if mensal else {}
        OUT.write_text(json.dumps({"geral": {"disp": g.get("disp"), "meta": g.get("meta")},
                                   "mensal": mensal, "categoria": cat or []}, ensure_ascii=False, indent=1), encoding="utf-8")
    for (y, m) in meses:
        ini = date(y, m, 1)
        fim = date(y, m, min(hoje.day, calendar.monthrange(y, m)[1])) if (y == hoje.year and m == hoje.month) else date(y, m, calendar.monthrange(y, m)[1])
        q = f'DEFINE VAR _f = {filtro(ini, fim)} EVALUATE ROW("D", CALCULATE([Disponibilidade (%)],_f), "M", CALCULATE([Disponibilidade Meta (%)],_f))'
        r = dax(tok, q)
        if r is not None and r.status_code == 200:
            row = r.json()["results"][0]["tables"][0]["rows"][0]
            d = next((v for k, v in row.items() if k.endswith("[D]")), None)
            me = next((v for k, v in row.items() if k.endswith("[M]")), None)
            if d is not None:
                mensal.append({"ym": f"{y}-{m:02d}", "disp": float(d)*100, "meta": float(me or 0)*100})
                print(f"  {y}-{m:02d}: {float(d)*100:.1f}% (meta {float(me or 0)*100:.1f}%)", flush=True)
                salvar()   # salva incremental (nao perde se timeout)
        else:
            print(f"  {y}-{m:02d}: erro {getattr(r,'status_code','rede')}", flush=True)
    # por categoria (mes corrente)
    ini = date(hoje.year, hoje.month, 1); fim = date(hoje.year, hoje.month, hoje.day)
    q = f'DEFINE VAR _f = {filtro(ini, fim)} EVALUATE SUMMARIZECOLUMNS(d_equipamentos[CATEGORIA_M], _f, "D", [Disponibilidade (%)], "M", [Disponibilidade Meta (%)])'
    r = dax(tok, q, timeout=120)
    cat = []
    if r is not None and r.status_code == 200:
        for row in r.json()["results"][0]["tables"][0]["rows"]:
            c = next((v for k, v in row.items() if k.endswith("[CATEGORIA_M]")), None)
            d = next((v for k, v in row.items() if k.endswith("[D]")), None)
            me = next((v for k, v in row.items() if k.endswith("[M]")), None)
            if c and d is not None:
                cat.append({"cat": str(c), "disp": float(d)*100, "meta": float(me or 0)*100})
    salvar(cat)
    print(f"OK -> {OUT} | {len(mensal)} meses, {len(cat)} categorias")

if __name__ == "__main__":
    main()
