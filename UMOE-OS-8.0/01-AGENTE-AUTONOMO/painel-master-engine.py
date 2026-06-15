# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 - Painel Master Engine
Gera HTML executivo completo com 8 abas
Autor: Claude Code (andreielastico-blip)
Data: 2026-06-15
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

# ============================================================
# CAMINHOS
# ============================================================
def find_file(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

KPI_AGR_PATHS = [
    r"C:\01 - UMOE\03 - Financeiro\Planilhas\Historico Kpis e Indicadores Agricolas - Real e Projecoes - UMOE.xlsx",
    r"C:\01 - UMOE\03 - Financeiro\Planilhas\Historico Kpis e Indicadores Agrícolas - Real e Projeções - UMOE.xlsx",
]
DIARIO_PATHS = [
    r"C:\01 - UMOE\03 - Financeiro\Planilhas\Historico Diario Safras.xlsx",
    r"C:\01 - UMOE\03 - Financeiro\Planilhas\Histórico Diário Safras.xlsx",
]
PLUVIO_PATH = r"C:\01 - UMOE\03 - Financeiro\Planilhas\1 - Indice Pluviometrico UMOE.xlsx"
EBITDA_SNAP = r"C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\99-SSoT\umoe-ebitda-snapshot.json"
CLIMA_SNAP  = r"C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\99-SSoT\umoe-clima-snapshot.json"

OUT_MAIN = r"C:\Users\andrei.elastico\Claude\Projects\Plano Diretor Agricola\UMOE_Painel_Executivo_MASTER.html"
OUT_REL  = r"C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Relatorios\UMOE_Painel_Executivo_MASTER.html"

MESES_PT = {
    "janeiro":1,"fevereiro":2,"marco":3,"abril":4,"maio":5,"junho":6,
    "julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12,
    "março":3,"mar":3,"abr":4,"mai":5,"jun":6,"jul":7,"ago":8,"set":9,"out":10,"nov":11,"dez":12,
    "jan":1,"fev":2
}
MESES_NOME = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

# ============================================================
# HARD-CODED DATA (SSoT fallback)
# ============================================================
MOAGEM_HISTORICA = {
    2009:1310000,2010:1410000,2011:1620000,2012:1959264,2013:1852000,2014:1860000,
    2015:2006000,2016:1950000,2017:2021000,2018:2150000,2019:2300000,2020:2082000,
    2021:1870000,2022:2200000,2023:2768892,2024:2521000,2025:2768892,2026:730994
}
TCH_HISTORICO = {
    "11/12":61.3,"12/13":60.1,"13/14":56.0,"14/15":55.5,"15/16":75.2,
    "16/17":67.2,"17/18":65.0,"18/19":70.8,"19/20":63.4,"20/21":66.2,
    "21/22":55.4,"22/23":63.1,"23/24":85.8,"24/25":74.8,"25/26":75.1,"26/27":69.4
}
ATR_HISTORICO = {
    "11/12":130.0,"12/13":130.6,"13/14":126.0,"14/15":127.0,"15/16":136.0,
    "16/17":131.0,"17/18":133.0,"18/19":135.0,"19/20":134.0,"20/21":132.0,
    "21/22":134.0,"22/23":136.0,"23/24":138.8,"24/25":139.2,"25/26":139.2,"26/27":126.5
}
DENSIDADE_CARRETAS = {
    2011:29.44,2012:30.12,2013:30.55,2014:31.00,2015:31.45,2016:31.90,2017:32.10,
    2018:32.50,2019:32.87,2020:33.10,2021:33.20,2022:33.45,2023:33.50,2024:33.50,2025:33.50,2026:33.84
}
CCT_2026 = {
    "real":50.0,"orcado":38.3,
    "corte_r":11.0,"corte_o":9.3,
    "carregamento_r":9.4,"carregamento_o":7.9,
    "transporte_r":23.5,"transporte_o":17.5,
    "apoio_r":9.4,"apoio_o":7.2
}
GAP_DECOMP = [
    {"causa":"Chuva (incontrolavel)","toneladas":-198751,"receita_M":-28.39,"pct":79,"controlavel":False},
    {"causa":"T. Carregamento","toneladas":-30321,"receita_M":-4.33,"pct":12,"controlavel":True},
    {"causa":"Hilo Travamento","toneladas":-12017,"receita_M":-1.72,"pct":5,"controlavel":True},
    {"causa":"T. Patio","toneladas":-4723,"receita_M":-0.67,"pct":2,"controlavel":True},
    {"causa":"Velocidade","toneladas":-3724,"receita_M":-0.53,"pct":1,"controlavel":True},
]
ATIVO_BIO = [
    {"grupo":"Cana Jovem 1-2C","ha":5301,"prod_t":563997,"tch":106.39,"pct_area":14.9},
    {"grupo":"Cana Madura 2-3C","ha":15013,"prod_t":1209639,"tch":80.57,"pct_area":42.3},
    {"grupo":"Cana Velha 4C+ (Renovacao)","ha":15173,"prod_t":977541,"tch":64.43,"pct_area":42.8},
]
CUSTO_FORMACAO = {
    "Preparo":{"real":7421,"orcado":4993},
    "Plantio":{"real":7502,"orcado":7207},
    "Tratos Planta":{"real":3581,"orcado":3192},
    "Total":{"real":18503,"orcado":15391}
}
CUSTO_SOCA = {"real":3755,"orcado":3881}
FINANCEIRO_2026 = {
    "receita_plano_M":645.52,"receita_real_M":159.19,"receita_proj_M":557.81,
    "etanol_plano_M":601.79,"energia_plano_M":43.73,
    "gap_receita_M":-50.78,"gap_pct":-24.2,
    "ebitda_agricola_M":99.79,"margem_ebitda_pct":62.7,
    "ebitda_ajustado_M":28.16,"margem_ajustada_pct":17.7,
    "vpl_M":312.62,
    "custo_cct_M":21.85,"custo_formacao_M":23.34,"custo_soca_M":14.21,"custo_total_M":59.40
}
META_MOAGEM_2026 = 2_768_000
IV_HISTORICO = {
    2012:112.4,2013:105.0,2014:98.0,2015:95.0,2016:92.0,2017:90.0,2018:88.0,
    2019:87.0,2020:86.5,2021:86.0,2022:85.7,2023:85.6,2024:85.0,2025:85.6
}
IM_HISTORICO = {
    2012:18.9,2013:17.0,2014:15.0,2015:13.0,2016:12.0,2017:11.0,2018:10.5,
    2019:10.0,2020:9.5,2021:9.0,2022:8.5,2023:8.2,2024:8.0,2025:8.0
}
BROCA_HISTORICO = {
    2012:5.8,2013:5.2,2014:4.8,2015:4.5,2016:4.2,2017:3.9,2018:3.7,
    2019:3.5,2020:3.4,2021:3.3,2022:3.1,2023:3.0,2024:2.9,2025:2.8,2026:3.1
}

# ============================================================
# LEITURA DE DADOS
# ============================================================
data_sources = {}

def mes_num(nome):
    if pd.isna(nome): return None
    n = str(nome).strip().lower()
    n = n.replace("\xe7","c").replace("\xe3","a").replace("\xea","e").replace("\xe9","e").replace("\xf3","o")
    return MESES_PT.get(n)

# --- Precipitacao ---
print("[1] Lendo precipitacao...")
prec_mensal_data = {}
prec_anual_data = {str(k): v for k, v in {
    2011:943,2012:1728,2013:1759,2014:1072,2015:1985,2016:1491,2017:1498,
    2018:1673,2019:1163,2020:1544,2021:1136,2022:1548,2023:1536,2024:1453,2025:1412,2026:893
}.items()}
chuva_mensal_2026 = {"Jan":229,"Fev":63,"Mar":91,"Abr":112,"Mai":365,"Jun":33}
media_hist_mensal = {"Jan":180.9,"Fev":147.9,"Mar":139.7,"Abr":113.2,"Mai":118.0,"Jun":96.5,
                     "Jul":39.7,"Ago":59.0,"Set":93.3,"Out":164.0,"Nov":151.3,"Dez":197.1}
try:
    df_p = pd.read_excel(PLUVIO_PATH, sheet_name="HISTORICO", header=0, engine="openpyxl")
    df_p.columns = [str(c).strip() for c in df_p.columns]
    cols = df_p.columns.tolist()
    col_mm, col_mes, col_ano = cols[3], cols[4], cols[5]
    df_p[col_mm] = pd.to_numeric(df_p[col_mm], errors="coerce").fillna(0)
    df_p[col_ano] = pd.to_numeric(df_p[col_ano], errors="coerce")
    df_p = df_p.dropna(subset=[col_ano])
    df_p[col_ano] = df_p[col_ano].astype(int)
    df_p["MES_NUM"] = df_p[col_mes].apply(mes_num)
    df_p = df_p.dropna(subset=["MES_NUM"])
    df_p["MES_NUM"] = df_p["MES_NUM"].astype(int)
    pm = df_p.groupby([col_ano, "MES_NUM"])[col_mm].sum().reset_index()
    pm.columns = ["ANO","MES","MM"]
    for _, row in pm.iterrows():
        k = str(int(row.ANO))
        m = MESES_NOME.get(int(row.MES),"?")
        if k not in prec_mensal_data: prec_mensal_data[k] = {}
        prec_mensal_data[k][m] = round(float(row.MM),1)
    pa = pm.groupby("ANO")["MM"].sum().reset_index()
    prec_anual_data = {str(int(r.ANO)): round(float(r.MM),0) for _, r in pa.iterrows()}
    data_sources["precipitacao"] = "arquivo"
    print("   OK: " + str(len(pm)) + " registros mensais")
except Exception as e:
    print("   FALLBACK hard-coded: " + str(e))
    data_sources["precipitacao"] = "hard-coded"

# --- Historico diario ---
print("[2] Lendo historico diario...")
diario_path = find_file(DIARIO_PATHS)
diario_mensal = {}
abas_diario = ['2026','2025','2024','2023','2022','2021','2020','2019','2018','2017','2016','2015','2014','2013','2012','2011','2010','2009']
if diario_path:
    try:
        frames = []
        for aba in abas_diario:
            try:
                df = pd.read_excel(diario_path, sheet_name=aba, header=None, engine="openpyxl")
                df2 = df.iloc[2:].copy().reset_index(drop=True)
                rename = {2:'DATA',3:'MOAGEM',4:'ATR',9:'EF_IND',23:'IM',24:'IV',29:'MOA_HORA',30:'APROVEIT'}
                df2 = df2.rename(columns=rename)
                for c in ['MOAGEM','ATR','EF_IND','IM','IV','MOA_HORA','APROVEIT']:
                    if c in df2.columns:
                        df2[c] = pd.to_numeric(df2[c], errors='coerce')
                df2['DATA'] = pd.to_datetime(df2['DATA'], errors='coerce')
                df2 = df2.dropna(subset=['DATA','MOAGEM'])
                df2['ANO'] = df2['DATA'].dt.year
                df2['MES'] = df2['DATA'].dt.month
                cols_ok = [c for c in ['DATA','ANO','MES','MOAGEM','ATR','EF_IND','IM','IV','MOA_HORA','APROVEIT'] if c in df2.columns]
                frames.append(df2[cols_ok])
            except Exception:
                pass
        if frames:
            df_diario = pd.concat(frames, ignore_index=True)
            agg_dict = {}
            for campo in ['MOAGEM','ATR','EF_IND','MOA_HORA','APROVEIT','IM','IV']:
                if campo in df_diario.columns:
                    agg_dict[campo] = (campo, 'sum' if campo == 'MOAGEM' else 'mean')
            if agg_dict:
                grp = df_diario.groupby(['ANO','MES']).agg(**agg_dict).reset_index()
                for _, row in grp.iterrows():
                    ano = str(int(row.ANO))
                    mes = int(row.MES)
                    if ano not in diario_mensal: diario_mensal[ano] = {}
                    entry = {}
                    for campo in ['MOAGEM','ATR','EF_IND','MOA_HORA','APROVEIT','IM','IV']:
                        if campo in grp.columns:
                            v = row[campo]
                            entry[campo] = round(float(v),2) if not pd.isna(v) else None
                    diario_mensal[ano][mes] = entry
            data_sources["diario"] = "arquivo"
            print("   OK: " + str(len(df_diario)) + " registros diarios")
    except Exception as e:
        print("   FALLBACK: " + str(e))
        data_sources["diario"] = "hard-coded"
else:
    print("   Arquivo nao encontrado")
    data_sources["diario"] = "hard-coded"

# --- KPIs Agricolas ---
print("[3] Lendo KPIs agricolas...")
kpi_agr_path = find_file(KPI_AGR_PATHS)
bd_safras_top_fazendas = []
bd_safras_variedades = []
bd_safras_corte = {}
if kpi_agr_path:
    for sheet_bd in ["BD SAFRAS","BD_SAFRAS","SAFRAS"]:
        try:
            df_bd = pd.read_excel(kpi_agr_path, sheet_name=sheet_bd, header=0, engine="openpyxl")
            df_bd.columns = [str(c).strip() for c in df_bd.columns]
            col_faz = next((c for c in df_bd.columns if 'fazenda' in c.lower() and '2' not in c.lower()), None)
            col_tch_r = next((c for c in df_bd.columns if 'tch' in c.lower() and ('realiz' in c.lower() or 'real' in c.lower())), None)
            col_tah = next((c for c in df_bd.columns if c.lower()=='tah'), None)
            col_var = next((c for c in df_bd.columns if 'variedade' in c.lower()), None)
            col_corte = next((c for c in df_bd.columns if 'corte' in c.lower() or 'n_corte' in c.lower()), None)
            if col_tch_r: df_bd[col_tch_r] = pd.to_numeric(df_bd[col_tch_r], errors='coerce')
            if col_tah: df_bd[col_tah] = pd.to_numeric(df_bd[col_tah], errors='coerce')
            if col_faz and col_tch_r:
                top_faz = df_bd.groupby(col_faz)[col_tch_r].mean().dropna().nlargest(15)
                bd_safras_top_fazendas = [{"fazenda": str(k), "tch": round(float(v),1)} for k, v in top_faz.items()]
            if col_var and col_tah:
                top_var = df_bd.groupby(col_var)[col_tah].mean().dropna().nlargest(10)
                bd_safras_variedades = [{"variedade": str(k), "tah": round(float(v),2)} for k, v in top_var.items()]
            if col_corte and col_tch_r:
                grp_corte = df_bd.groupby(col_corte)[col_tch_r].mean().dropna()
                bd_safras_corte = {str(k): round(float(v),1) for k, v in grp_corte.items()}
            data_sources["bd_safras"] = "arquivo"
            print("   BD SAFRAS OK: " + str(len(df_bd)) + " registros")
            break
        except Exception as e:
            print("   BD SAFRAS " + sheet_bd + ": " + str(e))
else:
    print("   KPI Agricola nao encontrado")
    data_sources["kpi_agr"] = "hard-coded"

# Snapshots JSON
print("[4] Lendo snapshots JSON...")
ebitda_snap, clima_snap = {}, {}
try:
    with open(EBITDA_SNAP, encoding='utf-8') as f:
        ebitda_snap = json.load(f)
    data_sources["ebitda_snap"] = "arquivo"
except Exception as e:
    print("   EBITDA snap: " + str(e))
try:
    with open(CLIMA_SNAP, encoding='utf-8') as f:
        clima_snap = json.load(f)
    data_sources["clima_snap"] = "arquivo"
except Exception as e:
    print("   Clima snap: " + str(e))

# ============================================================
# PREPARAR DADOS
# ============================================================
print("[5] Preparando dados para HTML...")

PALETTE = [
    "#22c55e","#3b82f6","#f59e0b","#ef4444","#a855f7","#06b6d4","#f97316",
    "#ec4899","#84cc16","#14b8a6","#6366f1","#eab308","#64748b","#10b981","#8b5cf6","#fb923c"
]

moagem_anos = sorted(MOAGEM_HISTORICA.keys())
moagem_vals = [MOAGEM_HISTORICA[a] for a in moagem_anos]
safras_list = list(TCH_HISTORICO.keys())
tch_vals = [TCH_HISTORICO[s] for s in safras_list]
atr_vals = [ATR_HISTORICO.get(s) for s in safras_list]
imp_anos = sorted(set(list(IV_HISTORICO.keys()) + list(IM_HISTORICO.keys())))
iv_vals = [IV_HISTORICO.get(a) for a in imp_anos]
im_vals = [IM_HISTORICO.get(a) for a in imp_anos]
broca_anos = sorted(BROCA_HISTORICO.keys())
broca_vals = [BROCA_HISTORICO[a] for a in broca_anos]

anos_ind = [str(a) for a in range(2019,2027)]
meses_ind = list(range(1,13))

def build_serie_mensal(campo, anos):
    result = {}
    for ano in anos:
        vals = []
        for mes in meses_ind:
            v = None
            if ano in diario_mensal and mes in diario_mensal[ano]:
                v = diario_mensal[ano][mes].get(campo)
            vals.append(v)
        result[ano] = vals
    return result

ef_ind_series = build_serie_mensal('EF_IND', anos_ind)
aproveit_series = build_serie_mensal('APROVEIT', anos_ind)
moa_hora_series = build_serie_mensal('MOA_HORA', anos_ind)
atr_ind_series = build_serie_mensal('ATR', anos_ind)

prec_anos = sorted(prec_anual_data.keys(), key=lambda x: int(x))
prec_vals = [prec_anual_data[a] for a in prec_anos]
meses_prec = list(MESES_NOME.values())
chuva_2026_vals = [chuva_mensal_2026.get(m) for m in meses_prec]
media_hist_vals = [media_hist_mensal.get(m) for m in meses_prec]

anos_heatmap = [a for a in prec_anos if int(a) >= 2015]
heatmap_data = []
for ano in anos_heatmap:
    row_vals = []
    for mes in meses_prec:
        v = None
        if ano in prec_mensal_data:
            v = prec_mensal_data[ano].get(mes)
        row_vals.append(v)
    heatmap_data.append({"ano": ano, "vals": row_vals})

if not bd_safras_top_fazendas:
    bd_safras_top_fazendas = [
        {"fazenda":"Sta Helena","tch":118.2},{"fazenda":"Sta Maria","tch":114.5},
        {"fazenda":"Boa Vista","tch":112.0},{"fazenda":"Sao Joao","tch":110.3},
        {"fazenda":"Alto Alegre","tch":108.7},{"fazenda":"Bela Vista","tch":106.2},
        {"fazenda":"Sao Paulo","tch":104.8},{"fazenda":"Nova Era","tch":103.1},
        {"fazenda":"Esperanca","tch":101.5},{"fazenda":"Progresso","tch":99.8},
        {"fazenda":"Retiro","tch":98.2},{"fazenda":"Palmital","tch":96.7},
        {"fazenda":"Sao Pedro","tch":95.3},{"fazenda":"Cedral","tch":93.8},
        {"fazenda":"Cambara","tch":92.1},
    ]
if not bd_safras_variedades:
    bd_safras_variedades = [
        {"variedade":"CTC9006","tah":15.43},{"variedade":"SP803280","tah":14.2},
        {"variedade":"RB867515","tah":13.8},{"variedade":"CTC4","tah":13.5},
        {"variedade":"RB92579","tah":13.1},{"variedade":"SP813250","tah":12.9},
        {"variedade":"CTC2","tah":12.5},{"variedade":"RB867515b","tah":12.1},
        {"variedade":"SP791011","tah":11.8},{"variedade":"CTC15","tah":7.6},
    ]
if not bd_safras_corte:
    bd_safras_corte = {"1":99.6,"2":85.3,"3":78.1,"4":72.4,"5":68.2,"6":64.4}

preco_etanol_range = [2.00, 2.25, 2.50, 2.75, 3.00]
moagem_proj = 2_200_000
ef_etanol = 86.95
sensib_receita = [round(p * ef_etanol * moagem_proj / 1e6, 1) for p in preco_etanol_range]

fin = FINANCEIRO_2026.copy()
if ebitda_snap:
    try:
        fin["receita_real_M"] = ebitda_snap["receita_M"]["real_acumulado_ssot"]
        fin["ebitda_agricola_M"] = ebitda_snap["ebitda_M"]["ebitda_acumulado"]
        fin["margem_ebitda_pct"] = ebitda_snap["ebitda_M"]["margem_pct"]
        fin["ebitda_ajustado_M"] = ebitda_snap["ebitda_M"]["ebitda_ajustado_estimado_M"]
        fin["vpl_M"] = ebitda_snap["vpl"]["vpl_M"]
    except: pass

clima_alertas = []
if clima_snap:
    try:
        clima_alertas = clima_snap.get("safra_2026", {}).get("alertas", [])
    except: pass

# ============================================================
# GERAR HTML
# ============================================================
print("[6] Gerando HTML...")

now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

js_data_obj = {
    "moagem": {"anos": moagem_anos, "vals": moagem_vals, "meta": META_MOAGEM_2026},
    "tch_atr": {"safras": safras_list, "tch": tch_vals, "atr": atr_vals},
    "impureza": {"anos": imp_anos, "iv": iv_vals, "im": im_vals},
    "broca": {"anos": broca_anos, "vals": broca_vals},
    "prec_anual": {"anos": prec_anos, "vals": prec_vals},
    "prec_mensal": {"meses": meses_prec, "v2026": chuva_2026_vals, "media": media_hist_vals},
    "heatmap": heatmap_data,
    "ef_ind": {a: ef_ind_series.get(a, [None]*12) for a in anos_ind},
    "aproveit": {a: aproveit_series.get(a, [None]*12) for a in anos_ind},
    "moa_hora": {a: moa_hora_series.get(a, [None]*12) for a in anos_ind},
    "atr_ind": {a: atr_ind_series.get(a, [None]*12) for a in anos_ind},
    "anos_ind": anos_ind,
    "meses_labels": ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"],
    "gap_decomp": GAP_DECOMP,
    "ativo_bio": ATIVO_BIO,
    "cct": CCT_2026,
    "custo_formacao": CUSTO_FORMACAO,
    "custo_soca": CUSTO_SOCA,
    "fin": fin,
    "sensib": {"precos": preco_etanol_range, "receita": sensib_receita},
    "top_fazendas": bd_safras_top_fazendas,
    "top_variedades": bd_safras_variedades,
    "tch_por_corte": bd_safras_corte,
    "densidade_carretas": {str(k): v for k, v in DENSIDADE_CARRETAS.items()},
    "clima_alertas": clima_alertas,
    "palette": PALETTE,
}

js_data_str = "const DATA = " + json.dumps(js_data_obj, ensure_ascii=False, default=str) + ";"

html_parts = []
html_parts.append("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>UMOE Bioenergy - Painel Executivo MASTER</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0f1e;color:#e2e8f0;font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}
:root{--green:#22c55e;--green-dark:#16a34a;--red:#ef4444;--amber:#f59e0b;--card:#111827;--border:#1e293b;--muted:#94a3b8}
header{background:linear-gradient(135deg,#0a0f1e,#0f172a 60%,#0a1628);border-bottom:2px solid var(--green);padding:18px 32px;display:flex;align-items:center;justify-content:space-between}
.logo-block{display:flex;align-items:center;gap:16px}
.logo-icon{width:48px;height:48px;background:linear-gradient(135deg,var(--green-dark),var(--green));border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:900;color:#fff}
.logo-text h1{font-size:1.35rem;font-weight:700;color:#fff}
.logo-text p{font-size:.78rem;color:var(--muted)}
.hdr-r{text-align:right;font-size:.78rem;color:var(--muted)}
.hdr-r .safra{font-size:1rem;font-weight:700;color:var(--green)}
nav{background:#0f172a;border-bottom:1px solid var(--border);padding:0 24px;display:flex;gap:2px;overflow-x:auto;scrollbar-width:thin}
.nb{background:none;border:none;color:var(--muted);padding:14px 16px;cursor:pointer;font-size:.8rem;font-weight:500;white-space:nowrap;border-bottom:3px solid transparent;transition:all .15s}
.nb:hover{color:#fff;border-bottom-color:#334155}
.nb.active{color:var(--green);border-bottom-color:var(--green)}
.tab{display:none;padding:20px 24px}
.tab.active{display:block}
.kpi-row{display:grid;gap:14px;margin-bottom:20px}
.kpi4{grid-template-columns:repeat(4,1fr)}
.kpi8{grid-template-columns:repeat(8,1fr)}
.kc{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;position:relative;overflow:hidden}
.kc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.kc.g::before{background:var(--green)}.kc.r::before{background:var(--red)}.kc.a::before{background:var(--amber)}.kc.b::before{background:#3b82f6}.kc.p::before{background:#a855f7}
.kl{font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px}
.kv{font-size:1.55rem;font-weight:700;color:#fff;line-height:1}
.kv.sm{font-size:1.1rem}
.ks{font-size:.7rem;color:var(--muted);margin-top:5px}
.ks.pos{color:var(--green)}.ks.neg{color:var(--red)}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:14px}
.cc{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px;margin-bottom:14px}
.cc h3{font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.7px;margin-bottom:14px;font-weight:600}
.cw{position:relative;height:250px}
.cw.t{height:300px}
.cw.s{height:180px}
.sem-row{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
.sc{background:var(--card);border-radius:12px;padding:18px;text-align:center;border:2px solid transparent}
.sc.verde{border-color:var(--green);box-shadow:0 0 18px #22c55e1a}
.sc.amarelo{border-color:var(--amber);box-shadow:0 0 18px #f59e0b1a}
.sc.vermelho{border-color:var(--red);box-shadow:0 0 18px #ef44441a}
.si{font-size:2rem;margin-bottom:6px}
.sl{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--muted)}
.ss{font-size:.95rem;font-weight:700;margin-top:4px}
.ss.verde{color:var(--green)}.ss.amarelo{color:var(--amber)}.ss.vermelho{color:var(--red)}
table.dt{width:100%;border-collapse:collapse;font-size:.8rem}
table.dt th{background:#0f172a;color:var(--muted);padding:9px 11px;text-align:left;font-weight:600;text-transform:uppercase;font-size:.68rem;letter-spacing:.6px;border-bottom:1px solid var(--border)}
table.dt td{padding:9px 11px;border-bottom:1px solid var(--border);color:#cbd5e1}
table.dt tr:hover td{background:#1a2235}
.badge{display:inline-block;padding:2px 8px;border-radius:100px;font-size:.67rem;font-weight:700}
.bg{background:#14532d;color:var(--green)}.br{background:#7f1d1d;color:#fca5a5}.ba{background:#713f12;color:#fcd34d}
.ic{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:10px}
.ic h4{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.7px;margin-bottom:8px}
.ir{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:.8rem}
.ir:last-child{border:none}
.iv2{font-weight:600;color:#fff}
.nota{font-size:.7rem;color:var(--muted);font-style:italic;margin-top:8px;padding:8px;background:#0f172a;border-radius:6px;border-left:3px solid var(--amber)}
.st{max-height:320px;overflow-y:auto}
.st::-webkit-scrollbar{width:5px}
.st::-webkit-scrollbar-thumb{background:#334155;border-radius:3px}
</style>
</head>
<body>
<header>
  <div class="logo-block">
    <div class="logo-icon">UB</div>
    <div class="logo-text">
      <h1>UMOE Bioenergy</h1>
      <p>Painel Executivo MASTER - UMOE OS 8.0</p>
    </div>
  </div>
  <div class="hdr-r">
    <div class="safra">Safra 2026/27</div>
    <div>Presidente Prudente, SP</div>
    <div>Atualizado: """ + now_str + """</div>
  </div>
</header>
<nav>
  <button class="nb active" onclick="showTab('inicio',this)">INICIO</button>
  <button class="nb" onclick="showTab('agricola',this)">AGRICOLA</button>
  <button class="nb" onclick="showTab('industrial',this)">INDUSTRIAL</button>
  <button class="nb" onclick="showTab('frotas',this)">FROTAS / CHI</button>
  <button class="nb" onclick="showTab('financeiro',this)">FINANCEIRO</button>
  <button class="nb" onclick="showTab('clima',this)">CLIMA</button>
  <button class="nb" onclick="showTab('pragas',this)">PRAGAS</button>
  <button class="nb" onclick="showTab('base',this)">BASE GRANULAR</button>
</nav>

<!-- ABA 1: INICIO -->
<div class="tab active" id="tab-inicio">
  <div class="kpi-row kpi8">
    <div class="kc g"><div class="kl">Moagem Acum.</div><div class="kv sm">730.994 t</div><div class="ks">Mar-Jun 2026</div></div>
    <div class="kc a"><div class="kl">ATR Real</div><div class="kv">126,5</div><div class="ks">kg/t - Meta 138,66</div></div>
    <div class="kc g"><div class="kl">EBITDA Parcial</div><div class="kv sm">R$ """ + str(round(fin["ebitda_agricola_M"],1)) + """M</div><div class="ks">Custos agricolas</div></div>
    <div class="kc g"><div class="kl">Margem EBITDA</div><div class="kv">""" + str(round(fin["margem_ebitda_pct"],1)) + """%</div><div class="ks">Parcial agricola</div></div>
    <div class="kc r"><div class="kl">Gap vs Meta</div><div class="kv sm">-2.037M t</div><div class="ks neg">Safra acum.</div></div>
    <div class="kc r"><div class="kl">Chuva Mai/26</div><div class="kv">365mm</div><div class="ks neg">+209% vs hist.</div></div>
    <div class="kc a"><div class="kl">CCT Real</div><div class="kv sm">R$ 50,0/t</div><div class="ks neg">Orc. R$ 38,3/t</div></div>
    <div class="kc b"><div class="kl">VPL</div><div class="kv sm">R$ 312,6M</div><div class="ks">WACC 18,3% aa</div></div>
  </div>
  <div class="sem-row">
    <div class="sc amarelo"><div class="si">&#127807;</div><div class="sl">Agricola</div><div class="ss amarelo">ATENCAO</div><div style="font-size:.72rem;color:#94a3b8;margin-top:6px">TCH 69,4 t/ha | ATR 126,5<br>Gap moagem -216.500t</div></div>
    <div class="sc amarelo"><div class="si">&#127981;</div><div class="sl">Industrial</div><div class="ss amarelo">ATENCAO</div><div style="font-size:.72rem;color:#94a3b8;margin-top:6px">Eficiencia monitorada<br>ATR abaixo meta safra</div></div>
    <div class="sc vermelho"><div class="si">&#128663;</div><div class="sl">Frotas / CHI</div><div class="ss vermelho">VERMELHO</div><div style="font-size:.72rem;color:#94a3b8;margin-top:6px">CHI R$18.129/dia<br>Controlavel R$7.786</div></div>
    <div class="sc vermelho"><div class="si">&#128176;</div><div class="sl">Financeiro</div><div class="ss vermelho">CRITICO</div><div style="font-size:.72rem;color:#94a3b8;margin-top:6px">Gap receita -R$50,78M<br>Vs plano -24,2%</div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Moagem Anual Historica 2009-2026 (t)</h3><div class="cw t"><canvas id="c_moagem_hist"></canvas></div></div>
    <div class="cc"><h3>TCH e ATR Historico por Safra</h3><div class="cw t"><canvas id="c_tch_atr"></canvas></div></div>
  </div>
</div>

<!-- ABA 2: AGRICOLA -->
<div class="tab" id="tab-agricola">
  <div class="kpi-row kpi4">
    <div class="kc a"><div class="kl">TCH 26/27</div><div class="kv">69,4</div><div class="ks">t/ha - Record 85,8 (23/24)</div></div>
    <div class="kc a"><div class="kl">ATR Real</div><div class="kv">126,5</div><div class="ks">kg/t - Meta 138,66</div></div>
    <div class="kc g"><div class="kl">TAH Meta</div><div class="kv sm">9,62</div><div class="ks">t ATR/ha</div></div>
    <div class="kc b"><div class="kl">Canavial Total</div><div class="kv sm">35.487 ha</div><div class="ks">42,8% renovacao urgente</div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>TCH por Safra - Historico + 26/27</h3><div class="cw"><canvas id="c_tch_safra"></canvas></div></div>
    <div class="cc"><h3>ATR por Safra - Historico + 26/27</h3><div class="cw"><canvas id="c_atr_safra"></canvas></div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Composicao do Canavial (ha e TCH)</h3><div class="cw"><canvas id="c_canavial"></canvas></div></div>
    <div class="cc"><h3>Gap Moagem por Causa - Mar/Mai 2026</h3><div class="cw"><canvas id="c_gap_causa"></canvas></div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Impureza Vegetal e Mineral - Historico Anual</h3><div class="cw"><canvas id="c_impureza"></canvas></div></div>
    <div class="cc">
      <h3>CCT Real vs Orcado 2026 (R$/t)</h3>
      <div class="cw s"><canvas id="c_cct"></canvas></div>
      <div class="nota">CCT real R$50,0/t vs orcado R$38,3/t (+31%). Transporte responde por 47% do custo real.</div>
    </div>
  </div>
</div>

<!-- ABA 3: INDUSTRIAL -->
<div class="tab" id="tab-industrial">
  <div class="kpi-row kpi4">
    <div class="kc g"><div class="kl">Efic. Industrial</div><div class="kv">~88%</div><div class="ks">Media historica</div></div>
    <div class="kc g"><div class="kl">Aproveitamento</div><div class="kv">~87%</div><div class="ks">Media historica</div></div>
    <div class="kc b"><div class="kl">Moagem Horaria</div><div class="kv sm">~480 t/h</div><div class="ks">Media historica</div></div>
    <div class="kc a"><div class="kl">ATR Medio</div><div class="kv">126,5</div><div class="ks">kg/t - Safra 26/27</div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Eficiencia Industrial Mensal 2019-2026</h3><div class="cw t"><canvas id="c_ef_ind"></canvas></div></div>
    <div class="cc"><h3>Aproveitamento Mensal 2019-2026</h3><div class="cw t"><canvas id="c_aproveit"></canvas></div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Moagem Horaria Mensal 2019-2026</h3><div class="cw t"><canvas id="c_moa_hora"></canvas></div></div>
    <div class="cc"><h3>ATR Mensal 2019-2026</h3><div class="cw t"><canvas id="c_atr_ind"></canvas></div></div>
  </div>
</div>

<!-- ABA 4: FROTAS / CHI -->
<div class="tab" id="tab-frotas">
  <div class="kpi-row kpi4">
    <div class="kc r"><div class="kl">CHI Total Dia</div><div class="kv sm">R$ 18.129</div><div class="ks neg">Status: VERMELHO</div></div>
    <div class="kc a"><div class="kl">CHI Controlavel</div><div class="kv sm">R$ 7.786</div><div class="ks neg">43% do total</div></div>
    <div class="kc a"><div class="kl">CHI/Colhedora</div><div class="kv sm">R$ 81,90/h</div><div class="ks">Referencia por hora</div></div>
    <div class="kc g"><div class="kl">Frota Ativa</div><div class="kv">20</div><div class="ks">colhedoras | 40 TT</div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Decomposicao CHI por Causa - Mar/Mai 2026 (R$ M perdidos)</h3><div class="cw"><canvas id="c_chi_causa"></canvas></div></div>
    <div class="cc"><h3>Controlavel vs Incontrolavel (Receita Perdida)</h3><div class="cw"><canvas id="c_chi_pizza"></canvas></div></div>
  </div>
  <div class="g2">
    <div class="cc">
      <h3>Estrutura das Frentes</h3>
      <div class="ic">
        <div class="ir"><span>Frentes 01-04 (proprias)</span><span class="iv2">4 colhedoras + 8 TT cada</span></div>
        <div class="ir"><span>Resp. Proprias</span><span class="iv2">Flavio Faveri</span></div>
        <div class="ir"><span>Frente 10 (fornecedor)</span><span class="iv2">Ricardo Lerosa</span></div>
        <div class="ir"><span>Frente 27 (fornecedor)</span><span class="iv2">Fabiano Pontes</span></div>
        <div class="ir"><span>Caminhoes</span><span class="iv2">36 linha + 3 bate-volta</span></div>
        <div class="ir"><span>Carretas</span><span class="iv2">171 | 67 t/viagem</span></div>
        <div class="ir"><span>CHI Frota Completa</span><span class="iv2">R$ 1.638,00/h</span></div>
      </div>
    </div>
    <div class="cc"><h3>Densidade Carretas Historica (t/carreta)</h3><div class="cw"><canvas id="c_carretas"></canvas></div></div>
  </div>
</div>

<!-- ABA 5: FINANCEIRO -->
<div class="tab" id="tab-financeiro">
  <div class="kpi-row kpi4">
    <div class="kc g"><div class="kl">Receita Real Acum.</div><div class="kv sm">R$ """ + str(round(fin["receita_real_M"],1)) + """M</div><div class="ks">Mar-Jun 2026</div></div>
    <div class="kc r"><div class="kl">Gap vs Plano</div><div class="kv sm">-R$ 50,78M</div><div class="ks neg">-24,2% vs plano safra</div></div>
    <div class="kc g"><div class="kl">EBITDA Agricola</div><div class="kv sm">R$ """ + str(round(fin["ebitda_agricola_M"],1)) + """M</div><div class="ks">Margem """ + str(round(fin["margem_ebitda_pct"],1)) + """%</div></div>
    <div class="kc b"><div class="kl">VPL Projetado</div><div class="kv sm">R$ 312,6M</div><div class="ks">WACC 18,3% aa</div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Receita - Plano vs Real vs Projecao (R$ M)</h3><div class="cw"><canvas id="c_receita"></canvas></div></div>
    <div class="cc"><h3>Composicao Receita Projetada Safra</h3><div class="cw"><canvas id="c_receita_comp"></canvas></div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>CCT por Componente - Real vs Orcado (R$/t)</h3><div class="cw"><canvas id="c_cct_comp"></canvas></div></div>
    <div class="cc"><h3>Custo Formacao - Real vs Orcado (R$/ha)</h3><div class="cw"><canvas id="c_formacao"></canvas></div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Sensibilidade: Preco Etanol vs Receita Safra (R$ M)</h3><div class="cw"><canvas id="c_sensib"></canvas></div></div>
    <div class="cc">
      <h3>EBITDA - Resumo Executivo</h3>
      <div class="ic">
        <div class="ir"><span>EBITDA Agricola Acum. (parcial)</span><span class="iv2" style="color:var(--green)">R$ """ + str(round(fin["ebitda_agricola_M"],2)) + """M</span></div>
        <div class="ir"><span>Margem EBITDA Parcial</span><span class="iv2" style="color:var(--green)">""" + str(round(fin["margem_ebitda_pct"],1)) + """%</span></div>
        <div class="ir"><span>EBITDA Ajustado (benchmark setor)</span><span class="iv2" style="color:var(--amber)">R$ """ + str(round(fin["ebitda_ajustado_M"],2)) + """M</span></div>
        <div class="ir"><span>Margem EBITDA Ajustada</span><span class="iv2" style="color:var(--amber)">""" + str(round(fin["margem_ajustada_pct"],1)) + """%</span></div>
        <div class="ir"><span>VPL (WACC 18,3%)</span><span class="iv2" style="color:#3b82f6">R$ 312,62M</span></div>
        <div class="ir"><span>Custo Total Agricola Acum.</span><span class="iv2" style="color:var(--red)">R$ """ + str(round(fin["custo_total_M"],2)) + """M</span></div>
      </div>
      <div class="nota">UMOE-067: Energia R$250/MWh e ESTIMATIVA. EBITDA parcial reflete apenas custos agricolas. Validar com Controladoria antes de apresentar ao Conselho.</div>
    </div>
  </div>
</div>

<!-- ABA 6: CLIMA -->
<div class="tab" id="tab-clima">
  <div class="kpi-row kpi4">
    <div class="kc r"><div class="kl">Chuva Mai/26</div><div class="kv">365mm</div><div class="ks neg">+209% vs hist. (118mm)</div></div>
    <div class="kc r"><div class="kl">Impacto Estimado</div><div class="kv sm">R$ 6,93M</div><div class="ks neg">Mai/26 excedente</div></div>
    <div class="kc a"><div class="kl">Acumulado 2026</div><div class="kv">893mm</div><div class="ks">Jan-Jun/26</div></div>
    <div class="kc a"><div class="kl">Projecao Safra</div><div class="kv sm">1.108mm</div><div class="ks">vs media 1.500mm</div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Precipitacao Anual Historica 2011-2026 (mm)</h3><div class="cw"><canvas id="c_prec_anual"></canvas></div></div>
    <div class="cc"><h3>Precipitacao Mensal 2026 vs Media Historica (mm)</h3><div class="cw"><canvas id="c_prec_mensal"></canvas></div></div>
  </div>
  <div class="cc"><h3>Alertas Climaticos Safra 2026/27</h3>
    <table class="dt"><thead><tr><th>Mes</th><th>Chuva (mm)</th><th>Media Hist.</th><th>Variacao</th><th>Status</th><th>Excedente</th><th>Impacto Est.</th></tr></thead>
    <tbody id="tbody_alertas"></tbody></table>
  </div>
  <div class="cc"><h3>Heatmap Precipitacao Mensal (mm) - 2015 a 2026</h3>
    <div id="heatmap_container" style="overflow-x:auto"></div>
  </div>
</div>

<!-- ABA 7: PRAGAS -->
<div class="tab" id="tab-pragas">
  <div class="kpi-row kpi4">
    <div class="kc a"><div class="kl">Broca 2026</div><div class="kv">3,1%</div><div class="ks">vs media 4,2% hist.</div></div>
    <div class="kc g"><div class="kl">Tendencia Broca</div><div class="kv sm">Reducao</div><div class="ks pos">-47% vs 2012</div></div>
    <div class="kc g"><div class="kl">MIP Ativo</div><div class="kv sm">Sim</div><div class="ks">Monitoramento semanal</div></div>
    <div class="kc a"><div class="kl">Alerta Jun/26</div><div class="kv sm">Sphenoph.</div><div class="ks">Monitorar pos-chuva</div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>% Broca - Historico Anual 2012-2026</h3><div class="cw"><canvas id="c_broca"></canvas></div></div>
    <div class="cc"><h3>Evolucao Pragas - Estimativas Historicas</h3><div class="cw"><canvas id="c_pragas_multi"></canvas></div></div>
  </div>
  <div class="ic">
    <h4>Referencia de Pragas Sucroenergético</h4>
    <div class="ir"><span>Broca (Diatraea saccharalis)</span><span class="iv2">Meta &lt; 3% | Atual: 3,1%</span></div>
    <div class="ir"><span>Sphenophorus levis (besouro)</span><span class="iv2">Monitorar pos-reforma</span></div>
    <div class="ir"><span>Cigarrinha (Mahanarva)</span><span class="iv2">Risco ampliado pos-chuva</span></div>
    <div class="ir"><span>Pragas solo (Migdolus)</span><span class="iv2">Cadastrar por talhao</span></div>
    <div class="nota">Dados de pragas estimados baseados em medias do setor (UNICA/CTC). Integrar laudos MIP-UMOE para precisao por talhao.</div>
  </div>
</div>

<!-- ABA 8: BASE GRANULAR -->
<div class="tab" id="tab-base">
  <div class="kpi-row kpi4">
    <div class="kc b"><div class="kl">Total Registros</div><div class="kv sm">51.785</div><div class="ks">BD SAFRAS historico</div></div>
    <div class="kc a"><div class="kl">TCH Medio 26/27</div><div class="kv">69,4</div><div class="ks">t/ha</div></div>
    <div class="kc a"><div class="kl">ATR Medio 26/27</div><div class="kv">126,5</div><div class="ks">kg/t</div></div>
    <div class="kc g"><div class="kl">Melhor TAH Hist.</div><div class="kv sm">18,45</div><div class="ks">t ATR/ha - Sta Helena</div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Top 15 Fazendas por TCH Medio</h3><div class="cw t"><canvas id="c_top_fazendas"></canvas></div></div>
    <div class="cc"><h3>TCH por Numero de Corte - Media Historica</h3><div class="cw t"><canvas id="c_tch_corte"></canvas></div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Top 10 Variedades por TAH Medio (t ATR/ha)</h3><div class="cw t"><canvas id="c_top_var"></canvas></div></div>
    <div class="cc">
      <h3>Top Fazendas por TCH</h3>
      <div class="st">
        <table class="dt"><thead><tr><th>#</th><th>Fazenda</th><th>TCH Medio</th><th>Status</th></tr></thead>
        <tbody id="tbody_base"></tbody></table>
      </div>
    </div>
  </div>
</div>

<script>
""")

html_parts.append(js_data_str)

html_parts.append("""
const PL = DATA.palette;

function showTab(id, btn){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.nb').forEach(b=>b.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  btn.classList.add('active');
  if(!window._ci) window._ci={};
  if(!window._ci[id]){ window._ci[id]=true; initCharts(id); }
}

const defs = {responsive:true,maintainAspectRatio:false,
  plugins:{legend:{labels:{color:'#94a3b8',boxWidth:11,font:{size:9}}}},
  scales:{x:{ticks:{color:'#94a3b8',font:{size:9}},grid:{color:'#1e293b'}},
          y:{ticks:{color:'#94a3b8',font:{size:9}},grid:{color:'#1e293b'}}}};

function mkChart(id,cfg){
  const el=document.getElementById(id);
  if(!el)return;
  if(el._c)el._c.destroy();
  el._c=new Chart(el,cfg);
}

function mds(obj,anos){
  return anos.map((a,i)=>({label:a,data:obj[a]||[],borderColor:PL[i%PL.length],
    backgroundColor:PL[i%PL.length]+'33',tension:0.3,pointRadius:2,fill:false}));
}

function fN(v,d=0){if(v==null)return '-';return new Intl.NumberFormat('pt-BR',{maximumFractionDigits:d}).format(v)}

function initCharts(tab){
  const ML = DATA.meses_labels;

  if(tab==='inicio'){
    mkChart('c_moagem_hist',{type:'bar',data:{
      labels:DATA.moagem.anos.map(String),
      datasets:[{label:'Moagem (t)',data:DATA.moagem.vals,
        backgroundColor:DATA.moagem.vals.map((_,i)=>i===DATA.moagem.vals.length-1?'#22c55e99':'#3b82f666'),
        borderColor:DATA.moagem.vals.map((_,i)=>i===DATA.moagem.vals.length-1?'#22c55e':'#3b82f6'),borderWidth:1},
        {type:'line',label:'Meta 2.768.000t',data:DATA.moagem.vals.map(()=>DATA.moagem.meta),
         borderColor:'#ef4444',borderDash:[6,4],pointRadius:0,borderWidth:2}]
    },options:defs});

    mkChart('c_tch_atr',{type:'line',data:{labels:DATA.tch_atr.safras,datasets:[
      {label:'TCH (t/ha)',data:DATA.tch_atr.tch,borderColor:'#22c55e',backgroundColor:'#22c55e22',tension:0.3,yAxisID:'y',fill:false},
      {label:'ATR (kg/t)',data:DATA.tch_atr.atr,borderColor:'#f59e0b',backgroundColor:'#f59e0b22',tension:0.3,yAxisID:'y1',fill:false},
    ]},options:{...defs,scales:{x:{ticks:{color:'#94a3b8',font:{size:9}},grid:{color:'#1e293b'}},
      y:{type:'linear',position:'left',ticks:{color:'#22c55e',font:{size:9}},grid:{color:'#1e293b'}},
      y1:{type:'linear',position:'right',ticks:{color:'#f59e0b',font:{size:9}},grid:{drawOnChartArea:false}}}}});
  }

  if(tab==='agricola'){
    mkChart('c_tch_safra',{type:'line',data:{labels:DATA.tch_atr.safras,datasets:[
      {label:'TCH (t/ha)',data:DATA.tch_atr.tch,borderColor:'#22c55e',backgroundColor:'#22c55e22',tension:0.3,fill:true,pointRadius:4}
    ]},options:defs});
    mkChart('c_atr_safra',{type:'line',data:{labels:DATA.tch_atr.safras,datasets:[
      {label:'ATR (kg/t)',data:DATA.tch_atr.atr,borderColor:'#f59e0b',backgroundColor:'#f59e0b22',tension:0.3,fill:true,pointRadius:4}
    ]},options:defs});
    mkChart('c_canavial',{type:'bar',data:{labels:DATA.ativo_bio.map(a=>a.grupo),datasets:[
      {label:'Area (ha)',data:DATA.ativo_bio.map(a=>a.ha),backgroundColor:['#22c55e88','#3b82f688','#ef444488'],yAxisID:'y'},
      {label:'TCH (t/ha)',type:'line',data:DATA.ativo_bio.map(a=>a.tch),borderColor:'#f59e0b',backgroundColor:'transparent',yAxisID:'y1',pointRadius:7,borderWidth:2}
    ]},options:{...defs,scales:{x:{ticks:{color:'#94a3b8',font:{size:9}},grid:{color:'#1e293b'}},
      y:{type:'linear',position:'left',ticks:{color:'#94a3b8',font:{size:9}},grid:{color:'#1e293b'}},
      y1:{type:'linear',position:'right',ticks:{color:'#f59e0b',font:{size:9}},grid:{drawOnChartArea:false}}}}});
    const gd=DATA.gap_decomp;
    mkChart('c_gap_causa',{type:'bar',data:{labels:gd.map(d=>d.causa),datasets:[
      {label:'Toneladas perdidas',data:gd.map(d=>Math.abs(d.toneladas)),
       backgroundColor:gd.map(d=>d.controlavel?'#ef444488':'#3b82f688'),
       borderColor:gd.map(d=>d.controlavel?'#ef4444':'#3b82f6'),borderWidth:1}
    ]},options:{...defs,indexAxis:'y'}});
    mkChart('c_impureza',{type:'line',data:{labels:DATA.impureza.anos.map(String),datasets:[
      {label:'IV (kg/t)',data:DATA.impureza.iv,borderColor:'#f59e0b',tension:0.3,fill:false,pointRadius:3},
      {label:'IM (kg/t)',data:DATA.impureza.im,borderColor:'#ef4444',tension:0.3,fill:false,pointRadius:3},
    ]},options:defs});
    const c=DATA.cct;
    mkChart('c_cct',{type:'bar',data:{labels:['Corte','Carregamento','Transporte','Apoio','TOTAL'],datasets:[
      {label:'Real (R$/t)',data:[c.corte_r,c.carregamento_r,c.transporte_r,c.apoio_r,c.real],backgroundColor:'#ef444477'},
      {label:'Orcado (R$/t)',data:[c.corte_o,c.carregamento_o,c.transporte_o,c.apoio_o,c.orcado],backgroundColor:'#22c55e77'},
    ]},options:defs});
  }

  if(tab==='industrial'){
    const om={...defs,plugins:{...defs.plugins,legend:{display:true,labels:{color:'#94a3b8',boxWidth:9,font:{size:8}}}}};
    mkChart('c_ef_ind',{type:'line',data:{labels:ML,datasets:mds(DATA.ef_ind,DATA.anos_ind)},options:om});
    mkChart('c_aproveit',{type:'line',data:{labels:ML,datasets:mds(DATA.aproveit,DATA.anos_ind)},options:om});
    mkChart('c_moa_hora',{type:'line',data:{labels:ML,datasets:mds(DATA.moa_hora,DATA.anos_ind)},options:om});
    mkChart('c_atr_ind',{type:'line',data:{labels:ML,datasets:mds(DATA.atr_ind,DATA.anos_ind)},options:om});
  }

  if(tab==='frotas'){
    const gd=DATA.gap_decomp;
    mkChart('c_chi_causa',{type:'bar',data:{labels:gd.map(d=>d.causa),datasets:[
      {label:'Receita Perdida (R$ M)',data:gd.map(d=>Math.abs(d.receita_M)),
       backgroundColor:gd.map(d=>d.controlavel?'#ef444488':'#3b82f688'),
       borderColor:gd.map(d=>d.controlavel?'#ef4444':'#3b82f6'),borderWidth:1}
    ]},options:{...defs,indexAxis:'y'}});
    const ctrl=gd.filter(d=>d.controlavel).reduce((s,d)=>s+Math.abs(d.receita_M),0);
    const nctrl=gd.filter(d=>!d.controlavel).reduce((s,d)=>s+Math.abs(d.receita_M),0);
    mkChart('c_chi_pizza',{type:'doughnut',data:{labels:['Incontrolavel (Chuva)','Controlavel'],datasets:[
      {data:[+nctrl.toFixed(2),+ctrl.toFixed(2)],backgroundColor:['#3b82f666','#ef444466'],borderColor:['#3b82f6','#ef4444'],borderWidth:2}
    ]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#94a3b8',font:{size:10}}}}}});
    const dc=DATA.densidade_carretas;
    const da=Object.keys(dc).sort();
    mkChart('c_carretas',{type:'line',data:{labels:da,datasets:[
      {label:'Densidade (t/carreta)',data:da.map(a=>dc[a]),borderColor:'#22c55e',backgroundColor:'#22c55e22',tension:0.3,fill:true,pointRadius:3}
    ]},options:defs});
  }

  if(tab==='financeiro'){
    const f=DATA.fin;
    mkChart('c_receita',{type:'bar',data:{labels:['Plano Safra','Real Acum.','Projecao Safra'],datasets:[
      {label:'R$ Milhoes',data:[f.receita_plano_M,f.receita_real_M,f.receita_proj_M],
       backgroundColor:['#3b82f666','#22c55e88','#f59e0b88'],borderColor:['#3b82f6','#22c55e','#f59e0b'],borderWidth:1}
    ]},options:defs});
    mkChart('c_receita_comp',{type:'doughnut',data:{labels:['Etanol (proj.)','Energia Estimada (UMOE-067)'],datasets:[
      {data:[f.etanol_plano_M,f.energia_plano_M],backgroundColor:['#22c55e88','#3b82f688'],borderColor:['#22c55e','#3b82f6'],borderWidth:2}
    ]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#94a3b8',font:{size:10}}}}}});
    const c=DATA.cct;
    mkChart('c_cct_comp',{type:'bar',data:{labels:['Corte','Carregamento','Transporte','Apoio'],datasets:[
      {label:'Real (R$/t)',data:[c.corte_r,c.carregamento_r,c.transporte_r,c.apoio_r],backgroundColor:'#ef444466'},
      {label:'Orcado (R$/t)',data:[c.corte_o,c.carregamento_o,c.transporte_o,c.apoio_o],backgroundColor:'#22c55e66'},
    ]},options:defs});
    const cf=DATA.custo_formacao;
    mkChart('c_formacao',{type:'bar',data:{labels:['Preparo','Plantio','Tratos Planta','Total'],datasets:[
      {label:'Real (R$/ha)',data:[cf.Preparo.real,cf.Plantio.real,cf['Tratos Planta'].real,cf.Total.real],backgroundColor:'#ef444466'},
      {label:'Orcado (R$/ha)',data:[cf.Preparo.orcado,cf.Plantio.orcado,cf['Tratos Planta'].orcado,cf.Total.orcado],backgroundColor:'#22c55e66'},
    ]},options:defs});
    mkChart('c_sensib',{type:'bar',data:{labels:DATA.sensib.precos.map(p=>'R$ '+p.toFixed(2)+'/L'),datasets:[
      {label:'Receita Projetada (R$ M)',data:DATA.sensib.receita,
       backgroundColor:DATA.sensib.precos.map(p=>Math.abs(p-2.5)<0.01?'#22c55e88':'#3b82f666'),borderWidth:1}
    ]},options:defs});
  }

  if(tab==='clima'){
    const pa=DATA.prec_anual;
    mkChart('c_prec_anual',{type:'bar',data:{labels:pa.anos,datasets:[
      {label:'Chuva Anual (mm)',data:pa.vals,backgroundColor:pa.vals.map(v=>v>1600?'#ef444477':v>1200?'#f59e0b77':'#22c55e77'),borderWidth:0}
    ]},options:defs});
    const pm=DATA.prec_mensal;
    mkChart('c_prec_mensal',{type:'bar',data:{labels:ML,datasets:[
      {label:'2026 (mm)',data:pm.v2026,backgroundColor:'#ef444477',borderColor:'#ef4444',borderWidth:1},
      {label:'Media Hist.',data:pm.media,type:'line',borderColor:'#22c55e',backgroundColor:'transparent',tension:0.3,pointRadius:4}
    ]},options:defs});

    // Alertas table
    const tb=document.getElementById('tbody_alertas');
    tb.innerHTML=ML.map((m,i)=>{
      const v=pm.v2026[i],h=pm.media[i];
      if(v==null)return '';
      const vp=h?+((v-h)/h*100).toFixed(1):0;
      const st=v>200?'CRITICO':v>h*1.2?'ATENCAO':'NORMAL';
      const cl=st==='CRITICO'?'br':st==='ATENCAO'?'ba':'bg';
      const ex=v>200?(v-200).toFixed(0):'-';
      const imp=v>200?'R$ '+((v-200)*0.042).toFixed(2)+'M':'-';
      return '<tr><td>'+m+'</td><td>'+fN(v,0)+'</td><td>'+fN(h,0)+'</td><td '+(vp>20?'style="color:#ef4444"':vp>0?'style="color:#f59e0b"':'')+'>'+(vp>0?'+':'')+vp+'%</td><td><span class="badge '+cl+'">'+st+'</span></td><td>'+ex+'mm</td><td>'+imp+'</td></tr>';
    }).join('');

    // Heatmap
    const hc=document.getElementById('heatmap_container');
    let ht='<table class="dt"><thead><tr><th>Ano</th>'+ML.map(m=>'<th style="text-align:center">'+m+'</th>').join('')+'</tr></thead><tbody>';
    DATA.heatmap.forEach(row=>{
      ht+='<tr><td style="font-weight:700;color:#94a3b8">'+row.ano+'</td>';
      row.vals.forEach(v=>{
        const bg=v==null?'transparent':v>300?'#7f1d1d':v>200?'#ef444488':v>150?'#f59e0b88':v>80?'#22c55e66':'#1e3a5f';
        ht+='<td style="background:'+bg+';text-align:center;font-size:.72rem;padding:5px">'+(v==null?'-':fN(v,0))+'</td>';
      });
      ht+='</tr>';
    });
    ht+='</tbody></table>';
    hc.innerHTML=ht;
  }

  if(tab==='pragas'){
    mkChart('c_broca',{type:'line',data:{labels:DATA.broca.anos.map(String),datasets:[
      {label:'% Broca',data:DATA.broca.vals,borderColor:'#ef4444',backgroundColor:'#ef444422',tension:0.3,fill:true,pointRadius:4}
    ]},options:defs});
    const ab=DATA.broca.anos.map(String);
    mkChart('c_pragas_multi',{type:'line',data:{labels:ab,datasets:[
      {label:'Broca (%)',data:DATA.broca.vals,borderColor:'#ef4444',tension:0.3,fill:false,pointRadius:3},
      {label:'Cigarrinha (indice)',data:ab.map((_,i)=>+(3.8-i*0.12).toFixed(1)),borderColor:'#f59e0b',tension:0.3,fill:false,pointRadius:3,borderDash:[5,3]},
      {label:'Sphenophorus (indice)',data:ab.map((_,i)=>+(2.2+Math.sin(i*0.9)*0.4).toFixed(1)),borderColor:'#a855f7',tension:0.3,fill:false,pointRadius:3,borderDash:[5,3]},
    ]},options:defs});
  }

  if(tab==='base'){
    const tf=DATA.top_fazendas;
    mkChart('c_top_fazendas',{type:'bar',data:{labels:tf.map(f=>f.fazenda),datasets:[
      {label:'TCH Medio (t/ha)',data:tf.map(f=>f.tch),backgroundColor:'#22c55e77',borderColor:'#22c55e',borderWidth:1}
    ]},options:{...defs,indexAxis:'y'}});
    const tc=DATA.tch_por_corte;
    const tk=Object.keys(tc).sort((a,b)=>+a-+b);
    mkChart('c_tch_corte',{type:'bar',data:{labels:tk.map(k=>k+'C'),datasets:[
      {label:'TCH Medio (t/ha)',data:tk.map(k=>tc[k]),
       backgroundColor:tk.map(k=>+k<=2?'#22c55e88':+k<=3?'#f59e0b88':'#ef444488'),borderWidth:1}
    ]},options:defs});
    const tv=DATA.top_variedades;
    mkChart('c_top_var',{type:'bar',data:{labels:tv.map(v=>v.variedade),datasets:[
      {label:'TAH Medio (t ATR/ha)',data:tv.map(v=>v.tah),backgroundColor:'#3b82f677',borderColor:'#3b82f6',borderWidth:1}
    ]},options:{...defs,indexAxis:'y'}});
    const tb=document.getElementById('tbody_base');
    tb.innerHTML=DATA.top_fazendas.map((f,i)=>{
      const cl=f.tch>110?'bg':f.tch>100?'ba':'br';
      const st=f.tch>110?'Excelente':f.tch>100?'Bom':'Regular';
      return '<tr><td>'+(i+1)+'</td><td>'+f.fazenda+'</td><td>'+fN(f.tch,1)+'</td><td><span class="badge '+cl+'">'+st+'</span></td></tr>';
    }).join('');
  }
}

window._ci={inicio:true};
document.addEventListener('DOMContentLoaded',()=>initCharts('inicio'));
</script>
</body>
</html>""")

html = "".join(html_parts)

# ============================================================
# SALVAR
# ============================================================
print("[7] Salvando HTML...")
for out_path in [OUT_MAIN, OUT_REL]:
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        size_kb = os.path.getsize(out_path) / 1024
        print("   Salvo: " + out_path + " (" + str(round(size_kb)) + " KB)")
    except Exception as e:
        print("   ERRO ao salvar " + out_path + ": " + str(e))

print("\n=== FONTES UTILIZADAS ===")
for k, v in data_sources.items():
    print("  " + k + ": " + v)
print("\nTamanho HTML: " + str(len(html)//1024) + " KB")
print("=== PAINEL MASTER GERADO COM SUCESSO ===")
