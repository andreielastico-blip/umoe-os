# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Avalia 100% das MEDIDAS do BI ao vivo (valor que a propria BI calcula)
Para cada dataset, pega a lista de medidas (Dados-PBI/MEDIDAS_DAX_*.json, Kind=Medida)
e avalia via executeQueries em lotes (ROW com N medidas). Se um lote falha, bisecciona
ate isolar a medida que exige contexto/erra, marcando-a. 100% fiel: o numero vem da BI.

Saida: UMOE-OS-8.0/Dados-PBI/MEDIDAS_VALORES.json
  [{ds, table, name, value, status}]  status: ok | contexto | erro | pesada
Auth: token de usuario em cache (silencioso). Use --user p/ device-code se expirar.
"""
import importlib.util, msal, requests, os, sys, json, time
from pathlib import Path

try:
    from dotenv import load_dotenv; load_dotenv(Path(__file__).parent.parent.parent / ".env")
except Exception: pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PBI  = ROOT / "UMOE-OS-8.0" / "Dados-PBI"
OUT  = PBI / "MEDIDAS_VALORES.json"
AZURE_CLI = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]

# dataset -> (workspace_id, dataset_id)
DATASETS = {
    "BI_AGR_01_BASE": ("662a06b5-5579-4af6-b66a-7ac191a96674", "06950719-48dc-403d-bd91-2e059cf1a25e"),
    "BI_AGR_01_CST":  ("662a06b5-5579-4af6-b66a-7ac191a96674", "a735ce0e-4234-42f8-bedd-5cbb07ce6364"),
    "BI_AGR_01_CTRL": ("662a06b5-5579-4af6-b66a-7ac191a96674", "4c81ea62-ef7f-4976-9aaa-bf7ab3727c0b"),
    "MANUT_umoe_dataset": ("954ecb3e-1daf-4a98-8801-39f2026da2d8", "aaa8d842-2606-4e11-ab87-f44a7abe320f"),
    "MANUT_PARETOS_PROCESSOS": ("954ecb3e-1daf-4a98-8801-39f2026da2d8", "f5be77dd-1cc8-4daa-ad89-f7dc271854d4"),
}

def get_token(user=False):
    spec = importlib.util.spec_from_file_location("pbi_auth", HERE / "pbi-auth.py")
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    cache = A._load_cache()
    app = msal.PublicClientApplication(AZURE_CLI, authority=f"https://login.microsoftonline.com/{os.getenv('PBI_TENANT_ID','organizations')}", token_cache=cache)
    accs = app.get_accounts()
    if accs:
        r = app.acquire_token_silent(SCOPE, account=accs[0])
        if r and "access_token" in r:
            A._save_cache(cache); return r["access_token"]
    if user:
        flow = app.initiate_device_flow(scopes=SCOPE)
        print(f"\n  Abra {flow['verification_uri']} e digite: {flow['user_code']}\n")
        r = app.acquire_token_by_device_flow(flow); A._save_cache(cache)
        return r.get("access_token")
    return None

# Medidas pesadas conhecidas (SUMX hora-a-hora sobre d_data_hora): avaliar ao
# vivo daria timeout. Ja temos os valores pela medida oficial mensal
# (disponibilidade_oficial.json). Marcamos como 'pesada' sem consultar.
PESADAS_PADRAO = ("disponibilidade",)
def eh_pesada(nome):
    n = nome.lower()
    return any(p in n for p in PESADAS_PADRAO)

def medidas_do_dataset(ds):
    p = PBI / f"MEDIDAS_DAX_{ds}.json"
    if not p.exists(): return []
    regs = json.load(open(p, encoding="utf-8-sig"))
    return [(r["Table"], r["Name"]) for r in regs if r.get("Kind") == "Medida" and not r.get("Auto")]

def esc(nome):
    return nome.replace("]", "]]")

def consulta(tok, ws, ds, dax, timeout=30):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{ws}/datasets/{ds}/executeQueries"
    H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    try:
        return requests.post(url, headers=H, json={"queries": [{"query": dax}]}, timeout=timeout)
    except requests.exceptions.Timeout:
        return "timeout"
    except Exception:
        return None

def avalia_lote(tok, ws, ds, medidas, idx):
    """medidas: lista de (table,name). idx: indices originais. Retorna dict idx->(value,status).
    Bisecciona em caso de erro/timeout ate isolar a medida problematica."""
    if not medidas:
        return {}
    partes = ", ".join(f'"v{i}", [{esc(n)}]' for i, (_, n) in zip(idx, medidas))
    r = consulta(tok, ws, ds, f"EVALUATE ROW({partes})")
    if r == "timeout":
        if len(medidas) == 1:
            return {idx[0]: (None, "pesada")}
    elif r is not None and r.status_code == 200:
        try:
            rows = r.json()["results"][0]["tables"][0]["rows"]
        except Exception:
            rows = []
        row = rows[0] if rows else {}   # ROW() sem linha = todas as medidas em branco
        out = {}
        for i in idx:
            v = next((vv for k, vv in row.items() if k.endswith(f"[v{i}]") or k == f"[v{i}]" or k == f"v{i}"), None)
            out[i] = (v, "ok" if v is not None else "contexto")
        return out
    elif r is not None and r.status_code != 200 and len(medidas) == 1:
        txt = ""
        try: txt = r.json().get("error", {}).get("pbi.error", {}).get("details", [{}])[0].get("detail", {}).get("value", "")
        except Exception: pass
        return {idx[0]: (None, "contexto" if "context" in txt.lower() or "single value" in txt.lower() else "erro")}
    # bisecciona
    if len(medidas) > 1:
        meio = len(medidas) // 2
        a = avalia_lote(tok, ws, ds, medidas[:meio], idx[:meio])
        b = avalia_lote(tok, ws, ds, medidas[meio:], idx[meio:])
        a.update(b); return a
    return {idx[0]: (None, "erro")}

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    user = "--user" in sys.argv
    only = args[0].upper() if args else None   # ex: MANUT, BASE
    tok = get_token(user=user)
    if not tok:
        print("ERRO: sem token em cache. Rode com --user uma vez para autenticar."); sys.exit(1)
    # preserva resultados ja salvos de datasets fora do filtro
    resultado = []
    if only and OUT.exists():
        resultado = [r for r in json.load(open(OUT, encoding="utf-8-sig")) if only not in r["ds"].upper()]
    LOTE = 8
    for ds, (ws, dsid) in DATASETS.items():
        if only and only not in ds.upper():
            continue
        meds = medidas_do_dataset(ds)
        if not meds:
            continue
        # remove resultados antigos deste ds (vamos reescrever)
        resultado = [r for r in resultado if r["ds"] != ds]
        # separa pesadas conhecidas (nao consulta)
        avaliar = [(t, n) for (t, n) in meds if not eh_pesada(n)]
        pesadas = [(t, n) for (t, n) in meds if eh_pesada(n)]
        print(f"[{ds}] {len(meds)} medidas ({len(avaliar)} avaliar, {len(pesadas)} pesadas puladas)...", flush=True)
        valores = {}
        for i in range(0, len(avaliar), LOTE):
            bloco = avaliar[i:i+LOTE]
            idx = list(range(i, i+len(bloco)))
            valores.update(avalia_lote(tok, ws, dsid, bloco, idx))
            print(f"  {min(i+LOTE,len(avaliar))}/{len(avaliar)}", flush=True)
        for i, (tbl, nm) in enumerate(avaliar):
            v, st = valores.get(i, (None, "erro"))
            resultado.append({"ds": ds, "table": tbl, "name": nm, "value": v, "status": st})
        for tbl, nm in pesadas:
            resultado.append({"ds": ds, "table": tbl, "name": nm, "value": None, "status": "pesada"})
        OUT.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    c = Counter(r["status"] for r in resultado)
    print(f"\nCONCLUIDO: {len(resultado)} medidas | {dict(c)} -> {OUT}")

if __name__ == "__main__":
    main()
