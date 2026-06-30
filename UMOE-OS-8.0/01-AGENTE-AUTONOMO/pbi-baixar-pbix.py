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
# Um por DATASET distinto (datasetId). Reports que compartilham o mesmo dataset
# nao se repetem (todo o DAX do umoe_dataset ja vem de MANUT_umoe_dataset).
WS_AGR = "662a06b5-5579-4af6-b66a-7ac191a96674"
WS_MAN = "954ecb3e-1daf-4a98-8801-39f2026da2d8"
RELATORIOS = {
    # Agricola
    "BI_AGR_01_BASE": (WS_AGR, "3be2f3d8-557a-4375-8f70-1e2694fbf95e"),
    "BI_AGR_01_CST":  (WS_AGR, "0881949a-a6b2-4b11-a030-b183f2e67651"),
    "BI_AGR_01_CTRL": (WS_AGR, "721b4394-4455-4bb6-971d-ef5244e66e07"),
    # Manutencao - dataset principal
    "MANUT_umoe_dataset": (WS_MAN, "23193f71-f14b-4e67-886a-17791a5af32b"),
    # Manutencao - datasets proprios (DAX que faltava)
    "MANUT_Materiais_Aplicados":  (WS_MAN, "b9b86992-61d8-4e07-8e92-f88e9616a357"),
    "MANUT_Capa":                 (WS_MAN, "631a95ed-619d-4ec2-a0e9-6982bd3f1121"),
    "MANUT_OS_Interna_Campo":     (WS_MAN, "e1002429-11f1-45a4-ab29-e54e9b609cf6"),
    "MANUT_OS_Transporte":        (WS_MAN, "9024f76f-cf91-4d0d-a77c-1f632d07ff70"),
    "MANUT_PARETOS_PROCESSOS":    (WS_MAN, "c8f63278-b526-4368-9a43-f1cef48f8693"),
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

import re as _re
_AUTO = _re.compile(r"DateTableTemplate|LocalDateTable")  # tabelas de data auto-geradas

def _col(r, *nomes):
    for n in nomes:
        if n in r and str(r.get(n, "")).strip() not in ("", "nan", "None"):
            return r.get(n)
    return ""

def _linhas(df, kind):
    """Normaliza um DataFrame do pbixray (measures/columns/tables) em registros DAX."""
    out = []
    if df is None or len(df) == 0:
        return out
    for _, r in df.iterrows():
        expr = str(_col(r, "Expression"))
        if not expr.strip():
            continue  # so DAX (ignora colunas/tabelas sem formula = vindas da fonte)
        tbl = str(_col(r, "TableName", "Table"))
        nm  = str(_col(r, "Name", "ColumnName", "MeasureName")) or tbl
        out.append({"Kind": kind, "Table": tbl, "Name": nm,
                    "Auto": bool(_AUTO.search(tbl)), "Expression": expr})
    return out

def extrair(nome, fp):
    try:
        m = PBIXRay(str(fp))
        med  = _linhas(getattr(m, "dax_measures", None), "Medida")
        cols = _linhas(getattr(m, "dax_columns",  None), "Coluna calculada")
        tabs = _linhas(getattr(m, "dax_tables",   None), "Tabela calculada")
        regs = med + cols + tabs
        # JSON: 100% (inclui auto date tables, marcadas com Auto=true)
        (PBIX_DIR.parent / f"MEDIDAS_DAX_{nome}.json").write_text(
            json.dumps(regs, ensure_ascii=False, indent=1), encoding="utf-8")
        # contagens de negocio (sem auto date tables)
        bmed  = [r for r in med  if not r["Auto"]]
        bcols = [r for r in cols if not r["Auto"]]
        btabs = [r for r in tabs if not r["Auto"]]
        nbiz = len(bmed) + len(bcols) + len(btabs); nauto = len(regs) - nbiz
        # markdown legivel = SO negocio
        md = [f"# DAX (negocio) — {nome}",
              f"Medidas: {len(bmed)} | Colunas calculadas: {len(bcols)} | Tabelas calculadas: {len(btabs)} "
              f"| Negocio: {nbiz} | Auto date tables omitidas: {nauto}", ""]
        for titulo, grupo in [("MEDIDAS", bmed), ("COLUNAS CALCULADAS", bcols), ("TABELAS CALCULADAS", btabs)]:
            if not grupo:
                continue
            md.append(f"\n## {titulo} ({len(grupo)})\n")
            for r in grupo:
                md.append(f"### {r['Table']}.{r['Name']}\n```dax\n{r['Expression']}\n```")
        (PBIX_DIR.parent / f"MEDIDAS_DAX_{nome}.md").write_text("\n".join(md), encoding="utf-8")
        print(f"  [{nome}] negocio={nbiz} (med={len(bmed)} col={len(bcols)} tab={len(btabs)}) | +{nauto} auto | total={len(regs)}")
        return nbiz
    except Exception as e:
        print(f"  [{nome}] erro pbixray: {e}"); return 0

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    alvo = args[0] if args else None
    force = "--force" in flags        # rebaixa mesmo se o PBIX ja existir
    tok = None
    tot = 0; catalogo = []
    for nome, (ws, rid) in RELATORIOS.items():
        if alvo and alvo.upper() not in nome.upper(): continue
        fp = PBIX_DIR / f"{nome}.pbix"
        if force or not fp.exists() or fp.stat().st_size < 1024:
            if tok is None:
                tok = get_token()
                if not tok: print("ERRO: sem token"); sys.exit(1)
            fp = baixar(tok, nome, ws, rid)
        else:
            print(f"  [{nome}] PBIX em cache ({fp.stat().st_size//1024} KB)")
        if fp and fp.exists():
            n = extrair(nome, fp)
            tot += n; catalogo.append((nome, n))
    # catalogo geral
    cat_md = ["# Catalogo DAX UMOE — todas as formulas de calculo do BI",
              "",
              "Fonte: PBIX dos datasets dos workspaces Agricola e Manutencao PREMIUM, extraido com pbixray.",
              "Contagem = formulas de NEGOCIO (medidas + colunas/tabelas calculadas), sem as tabelas de data auto-geradas.",
              "Os arquivos .json guardam 100% (auto date tables marcadas com Auto=true).",
              ""]
    for nome, n in catalogo:
        cat_md.append(f"- **{nome}**: {n} formulas DAX -> [MEDIDAS_DAX_{nome}.md](MEDIDAS_DAX_{nome}.md)")
    cat_md.append(f"\n**TOTAL: {tot} formulas DAX de negocio** em {len(catalogo)} datasets.")
    (PBIX_DIR.parent / "DAX_CATALOGO.md").write_text("\n".join(cat_md), encoding="utf-8")
    print(f"CONCLUIDO: {tot} formulas DAX de negocio em {len(catalogo)} datasets (Dados-PBI/DAX_CATALOGO.md)")

if __name__ == "__main__":
    main()
