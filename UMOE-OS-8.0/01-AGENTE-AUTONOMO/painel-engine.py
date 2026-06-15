# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 - Painel Engine
Gera UMOE_Painel_Executivo_MASTER.html com dados historicos agricolas
Autor: Claude Code (andreielastico-blip)
"""

import pandas as pd
import numpy as np
import json
import os
import subprocess
from datetime import datetime
from scipy.stats import pearsonr

# CAMINHOS
PLUVIO_PATH     = r"C:\01 - UMOE\03 - Financeiro\Planilhas\1 - Indice Pluviometrico UMOE.xlsx"
ATR_HIST_PATH   = r"C:\01 - UMOE\09 - IA\umoe-os-8\Plano Diretor\Apresentacoes UMOE\ATR-TCH-TAH\Historico ATR-Imp. Vegetal e Mineral Safra 2011 a 2025.xlsx"
DIARIO_PATH     = r"C:\01 - UMOE\03 - Financeiro\Planilhas\Historico Diario Safras.xlsx"
EBITDA_SNAP     = r"C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\99-SSoT\umoe-ebitda-snapshot.json"
CLIMA_SNAP      = r"C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\99-SSoT\umoe-clima-snapshot.json"

OUT_HTML_MAIN   = r"C:\Users\andrei.elastico\Claude\Projects\Plano Diretor Agricola\UMOE_Painel_Executivo_MASTER.html"
OUT_HTML_REL    = r"C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Relatorios\UMOE_Painel_Executivo_MASTER.html"

# Caminhos com acentos (fallback)
ATR_HIST_PATHS = [
    ATR_HIST_PATH,
    r"C:\01 - UMOE\09 - IA\umoe-os-8\Plano Diretor\Apresentações UMOE\ATR-TCH-TAH\Historico ATR-Imp. Vegetal e Mineral Safra 2011 a 2025.xlsx",
]
DIARIO_PATHS = [
    DIARIO_PATH,
    r"C:\01 - UMOE\03 - Financeiro\Planilhas\Histórico Diário Safras.xlsx",
]

# PARAMETROS HARD-CODED
META_MOAGEM = 2_768_000
PRECO_ATR   = 1.03
WACC        = 18.30

TCH_HISTORICO = {
    "11/12":61.3,"12/13":60.1,"13/14":56.0,"14/15":55.5,"15/16":75.2,
    "16/17":67.2,"17/18":65.0,"18/19":70.8,"19/20":63.4,"20/21":66.2,
    "21/22":55.4,"22/23":63.1,"23/24":85.8,"24/25":74.8,"25/26":75.1,"26/27":69.4
}

MESES_PT = {
    "janeiro":1,"fevereiro":2,"marco":3,"marco":3,"abril":4,"maio":5,"junho":6,
    "julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12
}
# incluir variante com acento
MESES_PT["março"] = 3

MESES_NOME = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
               7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}


def find_file(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


# 1. PRECIPITACAO
print("[1/6] Lendo precipitacao...")
df_pluvio = pd.read_excel(PLUVIO_PATH, sheet_name="HISTORICO", header=0, engine="openpyxl")
df_pluvio.columns = [str(c).strip() for c in df_pluvio.columns]
col_names = df_pluvio.columns.tolist()
col_mm  = col_names[3]
col_mes = col_names[4]
col_ano = col_names[5]

df_pluvio[col_mm]  = pd.to_numeric(df_pluvio[col_mm], errors="coerce").fillna(0)
df_pluvio[col_ano] = pd.to_numeric(df_pluvio[col_ano], errors="coerce")
df_pluvio = df_pluvio.dropna(subset=[col_ano])
df_pluvio[col_ano] = df_pluvio[col_ano].astype(int)

def mes_num(nome):
    if pd.isna(nome):
        return None
    n = str(nome).strip().lower()
    # normaliza acento
    n = n.replace("\xe7","c").replace("\xe3","a").replace("\xea","e")
    return MESES_PT.get(n)

df_pluvio["MES_NUM"] = df_pluvio[col_mes].apply(mes_num)
df_pluvio = df_pluvio.dropna(subset=["MES_NUM"])
df_pluvio["MES_NUM"] = df_pluvio["MES_NUM"].astype(int)

prec_mensal = df_pluvio.groupby([col_ano, "MES_NUM"])[col_mm].sum().reset_index()
prec_mensal.columns = ["ANO","MES","CHUVA_MM"]
prec_anual  = prec_mensal.groupby("ANO")["CHUVA_MM"].sum().reset_index()
prec_anual.columns  = ["ANO","CHUVA_ANUAL"]
print(f"   Precipitacao: {prec_mensal.ANO.min()}-{prec_mensal.ANO.max()}, {len(prec_mensal)} registros mensais")


# 2. ATR HISTORICO MENSAL (2011-2025)
print("[2/6] Lendo ATR historico mensal...")
atr_path = find_file(ATR_HIST_PATHS)
if atr_path:
    df_atr_raw = pd.read_excel(atr_path, sheet_name="Planilha1", header=None, engine="openpyxl")
    anos_atr = []
    for c in range(2, 17):
        try:
            v = df_atr_raw.iloc[1, c]
            anos_atr.append(int(float(str(v).replace(",","."))) if pd.notna(v) else None)
        except:
            anos_atr.append(None)

    def extrair_bloco(df, row_start, indicador):
        rows = []
        for m_idx, mes_n in enumerate(range(1, 13)):
            row = row_start + m_idx
            for col_idx, ano in enumerate(anos_atr):
                if ano is None:
                    continue
                try:
                    val = df.iloc[row, 2 + col_idx]
                    val = float(str(val).replace(",",".")) if pd.notna(val) else 0.0
                except:
                    val = 0.0
                if val > 0:
                    rows.append({"ANO": ano, "MES": mes_n, indicador: val})
        return pd.DataFrame(rows)

    df_atr_hist   = extrair_bloco(df_atr_raw, 3,  "ATR")
    df_terra_hist = extrair_bloco(df_atr_raw, 16, "IM")
    df_veg_hist   = extrair_bloco(df_atr_raw, 29, "IV")
    df_qual_hist  = df_atr_hist.merge(df_terra_hist, on=["ANO","MES"], how="outer")\
                               .merge(df_veg_hist,   on=["ANO","MES"], how="outer")
    print(f"   ATR hist: {len(df_qual_hist)} registros ano-mes")
else:
    print("   AVISO: arquivo ATR historico nao encontrado")
    df_qual_hist = pd.DataFrame(columns=["ANO","MES","ATR","IM","IV"])


# 3. HISTORICO DIARIO (2019-2026)
print("[3/6] Lendo historico diario...")
diario_path = find_file(DIARIO_PATHS)
frames_diario = []
if diario_path:
    abas_diario = ["2026","2025","2024","2023","2022","2021","2020","2019"]
    for aba in abas_diario:
        try:
            df_d = pd.read_excel(diario_path, sheet_name=aba, header=None, engine="openpyxl")
            df_d = df_d.iloc[2:].copy()
            df_d = df_d.rename(columns={
                2:"DATA", 3:"MOAGEM", 4:"ATR", 23:"IM", 24:"IV",
                29:"MOA_HORA", 30:"APROVEIT"
            })
            for c in ["MOAGEM","ATR","IM","IV","MOA_HORA","APROVEIT"]:
                df_d[c] = pd.to_numeric(df_d[c], errors="coerce")
            df_d["DATA"] = pd.to_datetime(df_d["DATA"], errors="coerce")
            df_d = df_d.dropna(subset=["DATA","MOAGEM"])
            df_d["ANO"] = df_d["DATA"].dt.year
            df_d["MES"] = df_d["DATA"].dt.month
            frames_diario.append(df_d[["DATA","ANO","MES","MOAGEM","ATR","IM","IV","MOA_HORA","APROVEIT"]])
            print(f"   Aba {aba}: {len(df_d)} dias")
        except Exception as e:
            print(f"   AVISO aba {aba}: {e}")
else:
    print("   AVISO: arquivo historico diario nao encontrado")

df_diario = pd.concat(frames_diario, ignore_index=True) if frames_diario else pd.DataFrame()

def agg_mensal_diario(df):
    rows = []
    for (ano, mes), g in df.groupby(["ANO","MES"]):
        moagem_tot = g["MOAGEM"].sum()
        mask_atr = g["ATR"].notna() & (g["ATR"] > 0) & g["MOAGEM"].notna()
        if mask_atr.sum() > 0:
            atr_pond = (g.loc[mask_atr,"ATR"] * g.loc[mask_atr,"MOAGEM"]).sum() / g.loc[mask_atr,"MOAGEM"].sum()
        else:
            atr_pond = np.nan
        im_med    = g["IM"].replace(0, np.nan).mean()
        iv_med    = g["IV"].replace(0, np.nan).mean()
        aprov_med = g["APROVEIT"].replace(0, np.nan).mean()
        rows.append({"ANO":ano,"MES":mes,"MOAGEM":moagem_tot,"ATR":atr_pond,
                     "IM":im_med,"IV":iv_med,"APROVEIT":aprov_med})
    return pd.DataFrame(rows)

df_mensal_d = agg_mensal_diario(df_diario) if not df_diario.empty else pd.DataFrame()
print(f"   Diario agregado: {len(df_mensal_d)} registros mes-ano")


# 4. CORRELACOES
print("[4/6] Calculando correlacoes...")

def calc_pearson(x, y):
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    mask = (~np.isnan(x)) & (~np.isnan(y)) & (x > 0) & (y > 0)
    if mask.sum() < 3:
        return None, None, int(mask.sum())
    r, p = pearsonr(x[mask], y[mask])
    return round(float(r), 4), round(float(p), 4), int(mask.sum())

def interpret_r(r):
    if r is None: return "insuficiente"
    a = abs(r)
    if a >= 0.7: return "forte"
    if a >= 0.4: return "moderado"
    return "fraco"

correlacoes = {}
scatter_data = {}

if not df_mensal_d.empty:
    df_corr = df_mensal_d.merge(prec_mensal, on=["ANO","MES"], how="inner")
    df_corr = df_corr[df_corr["ANO"] <= 2025]

    for ind, label in [("ATR","ATR vs Chuva"),("IM","Imp.Mineral vs Chuva"),
                        ("IV","Imp.Vegetal vs Chuva"),("APROVEIT","Aproveitamento vs Chuva")]:
        if ind not in df_corr.columns:
            continue
        x = df_corr["CHUVA_MM"].values.astype(float)
        y = df_corr[ind].values.astype(float)
        r, p, n = calc_pearson(x, y)
        correlacoes[ind] = {"r": r, "p": p, "n": n, "label": label, "interp": interpret_r(r)}
        print(f"   {label}: r={r}, n={n}, interp={interpret_r(r)}")

        mask = (~pd.isna(df_corr["CHUVA_MM"])) & (~pd.isna(df_corr[ind])) & \
               (df_corr["CHUVA_MM"] > 0) & (df_corr[ind] > 0)
        pts = df_corr[mask][["CHUVA_MM", ind, "ANO", "MES"]].copy()
        pts.columns = ["x","y","ano","mes"]
        scatter_data[ind] = pts.to_dict(orient="records")

# TCH vs chuva anual
tch_anos = {}
for safra, tch in TCH_HISTORICO.items():
    try:
        yy = int(safra[:2])
        ano_ini = 2000 + yy if yy < 50 else 1900 + yy
        ano_fin = ano_ini + 1
        tch_anos[ano_fin] = tch
    except:
        continue

anos_tch = sorted(tch_anos.keys())
prec_anual_dict = prec_anual.set_index("ANO")["CHUVA_ANUAL"].to_dict()
tch_vals  = np.array([tch_anos[a] for a in anos_tch], dtype=float)
prec_vals = np.array([prec_anual_dict.get(a, np.nan) for a in anos_tch], dtype=float)
r_tch, p_tch, n_tch = calc_pearson(prec_vals, tch_vals)
correlacoes["TCH"] = {"r": r_tch, "p": p_tch, "n": n_tch, "label":"TCH vs Chuva Anual", "interp": interpret_r(r_tch)}
print(f"   TCH vs Chuva anual: r={r_tch}, n={n_tch}, interp={interpret_r(r_tch)}")

tch_scatter = [{"x": prec_anual_dict.get(a), "y": tch_anos[a], "ano": a}
               for a in anos_tch if prec_anual_dict.get(a)]


# 5. TOP/BOTTOM MESES
print("[5/6] Calculando top/bottom meses...")
media_mes_atr   = {}
media_mes_aprov = {}
media_mes_im    = {}
media_mes_iv    = {}
media_mes_chuva = {}

if not df_mensal_d.empty:
    df_hist_mes = df_mensal_d[df_mensal_d["ANO"] <= 2025]
    media_mes_atr   = {int(k): round(v,2) for k,v in df_hist_mes.groupby("MES")["ATR"].mean().to_dict().items()}
    media_mes_aprov = {int(k): round(v,2) for k,v in df_hist_mes.groupby("MES")["APROVEIT"].mean().to_dict().items()}
    media_mes_im    = {int(k): round(v,4) for k,v in df_hist_mes.groupby("MES")["IM"].mean().to_dict().items()}
    media_mes_iv    = {int(k): round(v,4) for k,v in df_hist_mes.groupby("MES")["IV"].mean().to_dict().items()}

media_mes_chuva = {int(k): round(v,1) for k,v in
                   prec_mensal[prec_mensal["ANO"]<=2025].groupby("MES")["CHUVA_MM"].mean().to_dict().items()}

top3_atr   = sorted([(k,v) for k,v in media_mes_atr.items() if v and not np.isnan(v)], key=lambda x: x[1], reverse=True)[:3]
bot3_atr   = sorted([(k,v) for k,v in media_mes_atr.items() if v and not np.isnan(v)], key=lambda x: x[1])[:3]
top3_aprov = sorted([(k,v) for k,v in media_mes_aprov.items() if v and not np.isnan(v)], key=lambda x: x[1], reverse=True)[:3]
bot3_aprov = sorted([(k,v) for k,v in media_mes_aprov.items() if v and not np.isnan(v)], key=lambda x: x[1])[:3]


# 6. DADOS 2026 + SNAPSHOTS
print("[6/6] Montando dados 2026 e snapshots...")
ebitda_snap = {}
if os.path.exists(EBITDA_SNAP):
    with open(EBITDA_SNAP, encoding="utf-8") as f:
        ebitda_snap = json.load(f)

clima_snap = {}
if os.path.exists(CLIMA_SNAP):
    with open(CLIMA_SNAP, encoding="utf-8") as f:
        clima_snap = json.load(f)

df_2026 = df_mensal_d[df_mensal_d["ANO"] == 2026] if not df_mensal_d.empty else pd.DataFrame()
moagem_acum_2026 = float(df_2026["MOAGEM"].sum()) if not df_2026.empty else 0
atr_real_2026 = None
if not df_2026.empty and df_2026["MOAGEM"].sum() > 0:
    mask = df_2026["ATR"].notna() & (df_2026["ATR"] > 0)
    if mask.any():
        atr_real_2026 = round(float((df_2026.loc[mask,"ATR"] * df_2026.loc[mask,"MOAGEM"]).sum() / df_2026.loc[mask,"MOAGEM"].sum()), 2)

ebitda_acum   = ebitda_snap.get("ebitda_acumulado_R$", ebitda_snap.get("ebitda_R$", None))
margem_ebitda = ebitda_snap.get("margem_ebitda_%", None)
gap_meta_pct  = round((moagem_acum_2026 / META_MOAGEM - 1) * 100, 1) if moagem_acum_2026 else None
chuva_safra_2026 = float(prec_mensal[(prec_mensal["ANO"]==2026) & (prec_mensal["MES"]>=3)]["CHUVA_MM"].sum())

# Series para graficos
def serie_por_ano_mes(df, col, anos_lista):
    result = {}
    for ano in anos_lista:
        sub = df[df["ANO"]==ano][["MES",col]].dropna()
        result[str(ano)] = {int(r.MES): round(float(r[col]),4) for _,r in sub.iterrows() if not np.isnan(r[col])}
    return result

anos_graf = [2019,2020,2021,2022,2023,2024,2025,2026]
serie_atr  = serie_por_ano_mes(df_mensal_d, "ATR",    anos_graf) if not df_mensal_d.empty else {}
serie_im   = serie_por_ano_mes(df_mensal_d, "IM",     anos_graf) if not df_mensal_d.empty else {}
serie_iv   = serie_por_ano_mes(df_mensal_d, "IV",     anos_graf) if not df_mensal_d.empty else {}

serie_prec = {}
for ano in range(2011, 2027):
    sub = prec_mensal[prec_mensal["ANO"]==ano]
    if not sub.empty:
        serie_prec[str(ano)] = {int(r.MES): round(float(r.CHUVA_MM),1) for _,r in sub.iterrows()}

prec_anual_list = [{"ano": int(r.ANO), "mm": round(float(r.CHUVA_ANUAL),1)}
                   for _,r in prec_anual.sort_values("ANO").iterrows()]
prec_anual_media = round(float(prec_anual["CHUVA_ANUAL"].mean()), 1)

heatmap_prec = {}
for _,r in prec_mensal.iterrows():
    m = int(r.MES); a = int(r.ANO)
    heatmap_prec.setdefault(m, {})[a] = round(float(r.CHUVA_MM), 1)

# Alertas 2026
def status_alerta(val_2026, media_hist, campo):
    if val_2026 is None or media_hist is None:
        return "sem-dados"
    try:
        v = float(val_2026); m = float(media_hist)
        if np.isnan(v) or np.isnan(m): return "sem-dados"
    except:
        return "sem-dados"
    diff = (v - m) / m * 100 if m != 0 else 0
    if campo == "ATR":
        return "critico" if diff < -5 else "atencao" if diff < -2 else "normal"
    elif campo in ["IM","IV"]:
        return "critico" if diff > 20 else "atencao" if diff > 10 else "normal"
    elif campo == "CHUVA":
        return "critico" if diff > 50 else "atencao" if diff > 20 else "normal"
    return "normal"

alertas_2026 = []
for mes in range(3, 13):
    rows_26 = df_2026[df_2026["MES"]==mes] if not df_2026.empty else pd.DataFrame()
    row_26  = rows_26.iloc[0] if len(rows_26) > 0 else None
    atr_26  = float(row_26["ATR"])    if row_26 is not None and not pd.isna(row_26["ATR"])    else None
    im_26   = float(row_26["IM"])     if row_26 is not None and not pd.isna(row_26["IM"])     else None
    iv_26   = float(row_26["IV"])     if row_26 is not None and not pd.isna(row_26["IV"])     else None
    moa_26  = float(row_26["MOAGEM"]) if row_26 is not None and not pd.isna(row_26["MOAGEM"]) else None
    chuva_26= heatmap_prec.get(mes, {}).get(2026)

    alertas_2026.append({
        "mes": mes, "nome": MESES_NOME[mes],
        "atr_26":   round(atr_26, 2) if atr_26 else None,
        "atr_med":  media_mes_atr.get(mes),
        "im_26":    round(im_26, 4)  if im_26  else None,
        "im_med":   media_mes_im.get(mes),
        "iv_26":    round(iv_26, 4)  if iv_26  else None,
        "iv_med":   media_mes_iv.get(mes),
        "chuva_26": chuva_26,
        "chuva_med": media_mes_chuva.get(mes),
        "moagem_26": round(moa_26, 0) if moa_26 else None,
        "status_atr":   status_alerta(atr_26, media_mes_atr.get(mes), "ATR"),
        "status_im":    status_alerta(im_26,  media_mes_im.get(mes),  "IM"),
        "status_iv":    status_alerta(iv_26,  media_mes_iv.get(mes),  "IV"),
        "status_chuva": status_alerta(chuva_26, media_mes_chuva.get(mes), "CHUVA"),
    })

# Rankings
ranking_atr = [
    {"mes": mes, "nome": MESES_NOME[mes], "atr": val, "chuva": media_mes_chuva.get(mes)}
    for mes, val in media_mes_atr.items() if val and not np.isnan(val)
]
ranking_atr.sort(key=lambda x: x["atr"], reverse=True)

ranking_aprov = [
    {"mes": mes, "nome": MESES_NOME[mes], "aprov": val, "atr": media_mes_atr.get(mes)}
    for mes, val in media_mes_aprov.items() if val and not np.isnan(val)
]
ranking_aprov.sort(key=lambda x: x["aprov"], reverse=True)

# Empacota dados JSON
dados = {
    "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "kpis": {
        "moagem_acum": round(moagem_acum_2026, 0),
        "atr_real": atr_real_2026,
        "ebitda_acum_M": round(ebitda_acum/1e6, 1) if ebitda_acum else None,
        "margem_ebitda": margem_ebitda,
        "chuva_safra_mm": round(chuva_safra_2026, 1),
        "gap_meta_pct": gap_meta_pct,
        "meta_moagem": META_MOAGEM,
    },
    "prec_anual": prec_anual_list,
    "prec_anual_media": prec_anual_media,
    "serie_prec": serie_prec,
    "serie_atr": serie_atr,
    "serie_im": serie_im,
    "serie_iv": serie_iv,
    "heatmap_prec": {str(k): v for k,v in heatmap_prec.items()},
    "correlacoes": correlacoes,
    "scatter": scatter_data,
    "tch_scatter": tch_scatter,
    "tch_historico": [{"safra": k, "tch": v} for k,v in TCH_HISTORICO.items()],
    "media_mes_atr":   {str(k): v for k,v in media_mes_atr.items()},
    "media_mes_aprov": {str(k): v for k,v in media_mes_aprov.items()},
    "media_mes_chuva": {str(k): v for k,v in media_mes_chuva.items()},
    "ranking_atr":   ranking_atr,
    "ranking_aprov": ranking_aprov,
    "alertas_2026":  alertas_2026,
    "meses_nome": {str(k): v for k,v in MESES_NOME.items()},
}

dados_json = json.dumps(dados, ensure_ascii=False, default=str)

# GERA HTML
print("[HTML] Gerando painel executivo...")

CORES_ANOS = {
    "2019":"#64748b","2020":"#8b5cf6","2021":"#f59e0b","2022":"#06b6d4",
    "2023":"#f97316","2024":"#a3e635","2025":"#e879f9","2026":"#22c55e"
}
CORES_JSON = json.dumps(CORES_ANOS)

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UMOE Bioenergy | Painel Executivo Agricola</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0a0f1e; --card: #111827; --card2: #1f2937;
    --green: #16a34a; --green-l: #22c55e; --green-xl: #4ade80;
    --yellow: #f59e0b; --red: #ef4444; --blue: #3b82f6;
    --text: #f1f5f9; --text2: #94a3b8; --border: #1e3a5f;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Segoe UI',sans-serif; }}
  header {{
    background: linear-gradient(135deg,#0d1b2a 0%,#1a3a2a 100%);
    border-bottom: 2px solid var(--green);
    padding: 18px 32px;
    display: flex; justify-content: space-between; align-items: center;
  }}
  header h1 {{ font-size:1.4rem; font-weight:700; letter-spacing:2px; color:var(--green-xl); }}
  header .sub {{ font-size:.75rem; color:var(--text2); margin-top:3px; }}
  header .upd {{ font-size:.72rem; color:var(--text2); text-align:right; }}
  nav {{
    background:#0d1b2a; border-bottom:1px solid var(--border);
    display:flex; gap:0; overflow-x:auto;
  }}
  nav button {{
    background:none; border:none; color:var(--text2); padding:14px 22px;
    cursor:pointer; font-size:.85rem; font-weight:500; white-space:nowrap;
    border-bottom:3px solid transparent; transition:.2s;
  }}
  nav button:hover {{ color:var(--text); }}
  nav button.active {{ color:var(--green-xl); border-bottom-color:var(--green); }}
  .tab {{ display:none; padding:28px 32px; }}
  .tab.active {{ display:block; }}
  .grid-kpi {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-bottom:28px; }}
  .kpi-card {{
    background:var(--card); border:1px solid var(--border);
    border-radius:12px; padding:20px; position:relative; overflow:hidden;
  }}
  .kpi-card::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background:var(--green);
  }}
  .kpi-label {{ font-size:.72rem; color:var(--text2); text-transform:uppercase; letter-spacing:1px; }}
  .kpi-val {{ font-size:1.9rem; font-weight:700; color:var(--green-xl); margin:6px 0 4px; }}
  .kpi-sub {{ font-size:.75rem; color:var(--text2); }}
  .kpi-card.red::before {{ background:var(--red); }}
  .kpi-card.red .kpi-val {{ color:#fca5a5; }}
  .kpi-card.yellow::before {{ background:var(--yellow); }}
  .kpi-card.yellow .kpi-val {{ color:#fde68a; }}
  .chart-card {{
    background:var(--card); border:1px solid var(--border);
    border-radius:12px; padding:20px; margin-bottom:20px;
  }}
  .chart-card h3 {{ font-size:.9rem; color:var(--text2); margin-bottom:16px; text-transform:uppercase; letter-spacing:1px; }}
  .chart-wrap {{ position:relative; }}
  .grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  @media(max-width:900px) {{ .grid-2 {{ grid-template-columns:1fr; }} }}
  .corr-badge {{
    display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:.75rem; font-weight:700; margin-left:8px;
  }}
  .corr-forte {{ background:#15803d; color:#bbf7d0; }}
  .corr-moderado {{ background:#92400e; color:#fde68a; }}
  .corr-fraco {{ background:#1e3a5f; color:#bfdbfe; }}
  .corr-insuficiente {{ background:#374151; color:#9ca3af; }}
  table.rank {{
    width:100%; border-collapse:collapse; font-size:.85rem;
  }}
  table.rank th {{ background:#1f2937; color:var(--text2); padding:10px 14px; text-align:left; font-size:.75rem; text-transform:uppercase; }}
  table.rank td {{ padding:10px 14px; border-bottom:1px solid var(--border); }}
  table.rank tr:hover td {{ background:#1a2535; }}
  .rank-pos {{ font-weight:700; color:var(--green-xl); width:36px; }}
  .bar-bg {{ background:#1f2937; border-radius:4px; height:8px; margin-top:4px; }}
  .bar-fill {{ background:var(--green); border-radius:4px; height:8px; }}
  .heatmap-wrap {{ overflow-x:auto; }}
  table.heatmap {{ border-collapse:collapse; font-size:.75rem; white-space:nowrap; }}
  table.heatmap th {{ background:#1f2937; color:var(--text2); padding:6px 10px; }}
  table.heatmap td {{ padding:6px 10px; text-align:center; border:1px solid #0a0f1e; }}
  .alerta-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; }}
  .alerta-card {{
    background:var(--card); border:1px solid var(--border);
    border-radius:10px; padding:16px;
  }}
  .alerta-card.normal {{ border-left:4px solid var(--green); }}
  .alerta-card.atencao {{ border-left:4px solid var(--yellow); }}
  .alerta-card.critico {{ border-left:4px solid var(--red); }}
  .alerta-card.sem-dados {{ border-left:4px solid #374151; }}
  .alerta-mes {{ font-weight:700; font-size:1rem; margin-bottom:10px; }}
  .alerta-row {{ display:flex; justify-content:space-between; font-size:.78rem; margin-bottom:4px; }}
  .alerta-row .lbl {{ color:var(--text2); }}
  .status-icon {{ font-size:.9rem; }}
  .ins-card {{
    background:linear-gradient(135deg,#0d2818,#1a3a2a);
    border:1px solid var(--green); border-radius:12px; padding:20px;
    margin-bottom:16px;
  }}
  .ins-card h4 {{ color:var(--green-xl); margin-bottom:8px; font-size:.95rem; }}
  .ins-card p {{ color:var(--text2); font-size:.83rem; line-height:1.6; }}
  .section-title {{
    font-size:.75rem; color:var(--text2); text-transform:uppercase;
    letter-spacing:2px; margin-bottom:16px; padding-bottom:8px;
    border-bottom:1px solid var(--border);
  }}
</style>
</head>
<body>
<header>
  <div>
    <h1>UMOE BIOENERGY | PAINEL EXECUTIVO AGRICOLA</h1>
    <div class="sub">Safra 2026/27 | Sistema OS 8.0 | Presidente Prudente SP</div>
  </div>
  <div class="upd">
    <div>Atualizado em</div>
    <div id="upd-time" style="color:var(--green-xl);font-weight:600"></div>
  </div>
</header>

<nav>
  <button class="active" onclick="showTab('inicio',this)">Inicio</button>
  <button onclick="showTab('clima',this)">Clima</button>
  <button onclick="showTab('qualidade',this)">Qualidade</button>
  <button onclick="showTab('correlacoes',this)">Correlacoes</button>
  <button onclick="showTab('melhores',this)">Melhores Meses</button>
  <button onclick="showTab('alerta2026',this)">Alerta 2026</button>
</nav>

<div id="tab-inicio" class="tab active">
  <div class="grid-kpi" id="kpi-grid"></div>
  <div class="chart-card">
    <h3>Precipitacao vs ATR - 2026 vs Media Historica</h3>
    <div class="chart-wrap" style="height:280px"><canvas id="ch-inicio-dual"></canvas></div>
  </div>
</div>

<div id="tab-clima" class="tab">
  <div class="chart-card">
    <h3>Precipitacao Anual Total (2011-2026)</h3>
    <div class="chart-wrap" style="height:250px"><canvas id="ch-prec-anual"></canvas></div>
  </div>
  <div class="chart-card">
    <h3>Precipitacao Mensal - Comparativo por Ano</h3>
    <div class="chart-wrap" style="height:280px"><canvas id="ch-prec-mensal"></canvas></div>
  </div>
  <div class="chart-card">
    <h3>Heatmap: Precipitacao por Mes x Ano (mm)</h3>
    <div class="heatmap-wrap" id="heatmap-container"></div>
  </div>
</div>

<div id="tab-qualidade" class="tab">
  <div class="chart-card">
    <h3>ATR Medio por Mes (2019-2026)</h3>
    <div class="chart-wrap" style="height:280px"><canvas id="ch-atr-multi"></canvas></div>
  </div>
  <div class="grid-2">
    <div class="chart-card">
      <h3>Impureza Mineral por Mes/Ano</h3>
      <div class="chart-wrap" style="height:260px"><canvas id="ch-im-multi"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>Impureza Vegetal por Mes/Ano</h3>
      <div class="chart-wrap" style="height:260px"><canvas id="ch-iv-multi"></canvas></div>
    </div>
  </div>
</div>

<div id="tab-correlacoes" class="tab">
  <div class="grid-2">
    <div class="chart-card">
      <h3>Chuva vs ATR <span id="r-atr-badge"></span></h3>
      <div class="chart-wrap" style="height:240px"><canvas id="sc-atr"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>Chuva vs Impureza Mineral <span id="r-im-badge"></span></h3>
      <div class="chart-wrap" style="height:240px"><canvas id="sc-im"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>Chuva vs Impureza Vegetal <span id="r-iv-badge"></span></h3>
      <div class="chart-wrap" style="height:240px"><canvas id="sc-iv"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>Chuva vs Aproveitamento (%) <span id="r-aprov-badge"></span></h3>
      <div class="chart-wrap" style="height:240px"><canvas id="sc-aprov"></canvas></div>
    </div>
  </div>
  <div class="chart-card">
    <h3>TCH Anual vs Precipitacao Anual <span id="r-tch-badge"></span></h3>
    <div class="chart-wrap" style="height:280px"><canvas id="ch-tch-prec"></canvas></div>
  </div>
</div>

<div id="tab-melhores" class="tab">
  <div class="ins-card">
    <h4>Insight Operacional</h4>
    <p id="insight-texto"></p>
  </div>
  <div class="grid-2">
    <div class="chart-card">
      <h3>Ranking por ATR Medio Historico (kg/t)</h3>
      <table class="rank" id="tab-rank-atr"></table>
    </div>
    <div class="chart-card">
      <h3>Ranking por Aproveitamento Medio (%)</h3>
      <table class="rank" id="tab-rank-aprov"></table>
    </div>
  </div>
</div>

<div id="tab-alerta2026" class="tab">
  <p class="section-title">Status por Mes da Safra 2026/27 vs Media Historica</p>
  <div class="alerta-grid" id="alerta-grid"></div>
  <div class="chart-card" style="margin-top:20px">
    <h3>Comparativo 2026 vs Media Historica - ATR e Chuva Mensal</h3>
    <div class="chart-wrap" style="height:280px"><canvas id="ch-alerta-comp"></canvas></div>
  </div>
</div>

<script>
const D = {dados_json};
const CORES = {CORES_JSON};
const MESES = ['','Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];

function fmt(v, dec) {{
  dec = dec === undefined ? 1 : dec;
  if (v === null || v === undefined || isNaN(+v)) return 'N/D';
  return Number(v).toLocaleString('pt-BR', {{minimumFractionDigits: dec, maximumFractionDigits: dec}});
}}

function showTab(id, btn) {{
  document.querySelectorAll('.tab').forEach(function(t) {{ t.classList.remove('active'); }});
  document.querySelectorAll('nav button').forEach(function(b) {{ b.classList.remove('active'); }});
  document.getElementById('tab-' + id).classList.add('active');
  btn.classList.add('active');
}}

document.getElementById('upd-time').textContent = D.gerado_em;

var k = D.kpis;
var kpis = [
  {{ label:'Moagem Acumulada', val: k.moagem_acum ? fmt(k.moagem_acum,0)+' t' : 'N/D', sub: k.meta_moagem ? 'Meta: '+fmt(k.meta_moagem,0)+' t' : '', cls:'' }},
  {{ label:'ATR Real Acum.', val: k.atr_real ? fmt(k.atr_real,2)+' kg/t' : 'N/D', sub:'Meta: 138,66 kg/t', cls: k.atr_real && k.atr_real < 130 ? 'red' : k.atr_real && k.atr_real < 136 ? 'yellow' : '' }},
  {{ label:'EBITDA Acumulado', val: k.ebitda_acum_M ? 'R$ '+fmt(k.ebitda_acum_M,1)+'M' : 'N/D', sub:'Ref. SSoT', cls:'' }},
  {{ label:'Margem EBITDA', val: k.margem_ebitda ? fmt(k.margem_ebitda,1)+'%' : 'N/D', sub:'Referencia SSoT', cls: k.margem_ebitda && k.margem_ebitda < 50 ? 'yellow' : '' }},
  {{ label:'Chuva Safra 2026', val: k.chuva_safra_mm !== null && k.chuva_safra_mm !== undefined ? fmt(k.chuva_safra_mm,0)+' mm' : 'N/D', sub:'Mar-Jun 2026', cls:'' }},
  {{ label:'Gap vs Meta', val: k.gap_meta_pct !== null && k.gap_meta_pct !== undefined ? (k.gap_meta_pct>0?'+':'')+fmt(k.gap_meta_pct,1)+'%' : 'N/D', sub:'Volume moagem', cls: k.gap_meta_pct && k.gap_meta_pct < -5 ? 'red' : k.gap_meta_pct && k.gap_meta_pct < 0 ? 'yellow' : '' }},
];
var kgrid = document.getElementById('kpi-grid');
kpis.forEach(function(kpi) {{
  kgrid.innerHTML += '<div class="kpi-card '+kpi.cls+'"><div class="kpi-label">'+kpi.label+'</div><div class="kpi-val">'+kpi.val+'</div><div class="kpi-sub">'+kpi.sub+'</div></div>';
}});

var DEF_SCALES = {{
  x: {{ ticks: {{ color:'#64748b', maxRotation:45 }}, grid: {{ color:'#1e3a5f' }} }},
  y: {{ ticks: {{ color:'#94a3b8' }}, grid: {{ color:'#1e3a5f' }} }}
}};

function mkLabels(meses) {{ return meses.map(function(m){{ return MESES[m]||m; }}); }}

// INICIO: dual axis
(function() {{
  var meses = [1,2,3,4,5,6,7,8,9,10,11,12];
  var prec26 = meses.map(function(m) {{ return (D.serie_prec['2026']||{{}})[m] !== undefined ? (D.serie_prec['2026']||{{}})[m] : null; }});
  var precHist = meses.map(function(m) {{
    var anos = Object.entries(D.serie_prec).filter(function(e) {{ return +e[0]>=2011 && +e[0]<=2025; }});
    var vals = anos.map(function(e) {{ return e[1][m]; }}).filter(function(v) {{ return v!=null && v>0; }});
    return vals.length ? vals.reduce(function(a,b){{return a+b;}},0)/vals.length : null;
  }});
  var atr26 = meses.map(function(m) {{ return (D.serie_atr['2026']||{{}})[m] !== undefined ? (D.serie_atr['2026']||{{}})[m] : null; }});
  var atrHist = meses.map(function(m) {{ return D.media_mes_atr[m] !== undefined ? D.media_mes_atr[m] : null; }});
  new Chart(document.getElementById('ch-inicio-dual'), {{
    type:'bar',
    data: {{ labels: mkLabels(meses), datasets: [
      {{ label:'Chuva 2026 (mm)', data: prec26, backgroundColor:'rgba(59,130,246,0.5)', borderColor:'#3b82f6', yAxisID:'y' }},
      {{ label:'Chuva Hist. Media (mm)', data: precHist, type:'line', borderColor:'#93c5fd', borderDash:[5,5], fill:false, pointRadius:3, yAxisID:'y' }},
      {{ label:'ATR 2026 (kg/t)', data: atr26, type:'line', borderColor:'#22c55e', borderWidth:2, fill:false, pointRadius:4, yAxisID:'y2' }},
      {{ label:'ATR Hist. Media (kg/t)', data: atrHist, type:'line', borderColor:'#4ade80', borderDash:[4,4], fill:false, pointRadius:3, yAxisID:'y2' }},
    ]}},
    options: {{ responsive:true, maintainAspectRatio:false,
      plugins: {{ legend: {{ labels: {{ color:'#94a3b8', font:{{size:11}} }} }}, tooltip: {{ mode:'index' }} }},
      scales: {{
        x: {{ ticks:{{ color:'#64748b' }}, grid:{{ color:'#1e3a5f' }} }},
        y: {{ ticks:{{ color:'#94a3b8' }}, grid:{{ color:'#1e3a5f' }}, title:{{ display:true, text:'Chuva (mm)', color:'#94a3b8' }} }},
        y2: {{ position:'right', ticks:{{ color:'#22c55e' }}, grid:{{ drawOnChartArea:false }}, title:{{ display:true, text:'ATR (kg/t)', color:'#22c55e' }} }}
      }}
    }}
  }});
}})();

// CLIMA: Precipitacao anual
(function() {{
  var anos = D.prec_anual.map(function(d){{return d.ano;}});
  var mms  = D.prec_anual.map(function(d){{return d.mm;}});
  var media= D.prec_anual_media;
  new Chart(document.getElementById('ch-prec-anual'), {{
    type:'bar',
    data: {{ labels: anos, datasets: [
      {{ label:'Precipitacao Total (mm)', data: mms, backgroundColor: mms.map(function(v){{return v>=media?'rgba(22,163,74,0.7)':'rgba(239,68,68,0.6)'}}), borderRadius:4 }},
      {{ label:'Media '+media+' mm', data: anos.map(function(){{return media;}}), type:'line', borderColor:'#f59e0b', borderWidth:2, pointRadius:0, fill:false }}
    ]}},
    options: {{ responsive:true, maintainAspectRatio:false, plugins:{{ legend:{{ labels:{{ color:'#94a3b8' }} }} }}, scales: DEF_SCALES }}
  }});
}})();

// CLIMA: Precipitacao mensal multi-ano
(function() {{
  var anosShow = ['2024','2025','2026'];
  var meses = [1,2,3,4,5,6,7,8,9,10,11,12];
  var histMed = meses.map(function(m) {{
    var anos = Object.entries(D.serie_prec).filter(function(e) {{ return +e[0]>=2011 && +e[0]<=2023; }});
    var vals = anos.map(function(e) {{ return e[1][m]; }}).filter(function(v) {{ return v!=null; }});
    return vals.length ? vals.reduce(function(a,b){{return a+b;}},0)/vals.length : null;
  }});
  var ds = [{{ label:'Media 2011-2023', data: histMed, borderColor:'#64748b', borderDash:[4,4], borderWidth:2, fill:false, pointRadius:3 }}];
  anosShow.forEach(function(a) {{
    ds.push({{ label:a, data: meses.map(function(m){{ return (D.serie_prec[a]||{{}})[m] !== undefined ? (D.serie_prec[a]||{{}})[m] : null; }}),
      borderColor: CORES[a]||'#fff', borderWidth: a==='2026'?3:1.5, fill:false, pointRadius: a==='2026'?5:3 }});
  }});
  new Chart(document.getElementById('ch-prec-mensal'), {{
    type:'line', data:{{ labels: mkLabels(meses), datasets: ds }},
    options: {{ responsive:true, maintainAspectRatio:false, plugins:{{ legend:{{ labels:{{ color:'#94a3b8' }} }} }}, scales: DEF_SCALES }}
  }});
}})();

// CLIMA: Heatmap
(function() {{
  var anos = []; for(var a=2011;a<=2026;a++) anos.push(a);
  var allVals = [];
  Object.values(D.heatmap_prec).forEach(function(v) {{ Object.values(v).forEach(function(x) {{ allVals.push(x); }}); }});
  var maxV = Math.max.apply(null, allVals);
  var html = '<table class="heatmap"><thead><tr><th>Mes</th>';
  anos.forEach(function(a) {{ html += '<th>'+a+'</th>'; }});
  html += '</tr></thead><tbody>';
  var MESES_N = ['','Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
  for(var m=1;m<=12;m++) {{
    html += '<tr><th>'+MESES_N[m]+'</th>';
    anos.forEach(function(a) {{
      var v = (D.heatmap_prec[m]||{{}})[a];
      if(v==null) {{ html += '<td style="color:#374151">-</td>'; return; }}
      var ratio = v/maxV;
      var r = Math.round(10 + ratio*30);
      var g = Math.round(58 + ratio*100);
      var b2 = Math.round(10 + ratio*30);
      var tc = ratio > 0.5 ? '#fff' : '#94a3b8';
      html += '<td style="background:rgb('+r+','+g+','+b2+');color:'+tc+'">'+v+'</td>';
    }});
    html += '</tr>';
  }}
  html += '</tbody></table>';
  document.getElementById('heatmap-container').innerHTML = html;
}})();

// QUALIDADE: ATR multi-ano
(function() {{
  var meses=[1,2,3,4,5,6,7,8,9,10,11,12];
  var anos=['2019','2020','2021','2022','2023','2024','2025','2026'];
  var ds = anos.map(function(a) {{
    return {{ label:a, data: meses.map(function(m){{ return (D.serie_atr[a]||{{}})[m] !== undefined ? (D.serie_atr[a]||{{}})[m] : null; }}),
      borderColor: CORES[a]||'#fff', borderWidth: a==='2026'?3:1.5, fill:false, pointRadius: a==='2026'?5:3 }};
  }});
  new Chart(document.getElementById('ch-atr-multi'), {{
    type:'line', data:{{ labels:mkLabels(meses), datasets:ds }},
    options: {{ responsive:true, maintainAspectRatio:false, plugins:{{ legend:{{ labels:{{ color:'#94a3b8' }} }} }}, scales: DEF_SCALES }}
  }});
}})();

['im','iv'].forEach(function(ind) {{
  var meses=[1,2,3,4,5,6,7,8,9,10,11,12];
  var anos=['2019','2020','2021','2022','2023','2024','2025','2026'];
  var src = ind === 'im' ? D.serie_im : D.serie_iv;
  var ds = anos.map(function(a) {{
    return {{ label:a, data: meses.map(function(m){{ return (src[a]||{{}})[m] !== undefined ? (src[a]||{{}})[m] : null; }}),
      borderColor: CORES[a]||'#fff', borderWidth: a==='2026'?3:1.5, fill:false, pointRadius: a==='2026'?5:3 }};
  }});
  new Chart(document.getElementById('ch-'+ind+'-multi'), {{
    type:'line', data:{{ labels:mkLabels(meses), datasets:ds }},
    options: {{ responsive:true, maintainAspectRatio:false, plugins:{{ legend:{{ labels:{{ color:'#94a3b8' }} }} }}, scales: DEF_SCALES }}
  }});
}});

// CORRELACOES: badges
function corrBadge(corr, elId) {{
  var c = D.correlacoes[corr];
  if(!c) return;
  var cls = 'corr-'+c.interp;
  var sign = c.r > 0 ? '+' : '';
  document.getElementById(elId).innerHTML = '<span class="corr-badge '+cls+'">r='+sign+c.r+' ('+c.interp+') n='+c.n+'</span>';
}}
corrBadge('ATR','r-atr-badge');
corrBadge('IM','r-im-badge');
corrBadge('IV','r-iv-badge');
corrBadge('APROVEIT','r-aprov-badge');
corrBadge('TCH','r-tch-badge');

function mkScatter(canvasId, scKey, xlabel, ylabel) {{
  var pts = D.scatter[scKey] || [];
  var data = pts.map(function(p) {{ return {{ x: p.x, y: p.y, ano: p.ano, mes: p.mes }}; }});
  new Chart(document.getElementById(canvasId), {{
    type:'scatter',
    data:{{ datasets: [{{ label: scKey, data: data, backgroundColor:'rgba(22,163,74,0.6)', borderColor:'#16a34a', pointRadius:5 }}] }},
    options:{{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{ display:false }}, tooltip:{{
        callbacks:{{ label: function(ctx) {{ return (MESES[ctx.raw.mes||0]||'')+'/'+( ctx.raw.ano||'')+' x='+fmt(ctx.raw.x,1)+' y='+fmt(ctx.raw.y,2); }} }}
      }} }},
      scales:{{
        x:{{ ticks:{{ color:'#64748b' }}, grid:{{ color:'#1e3a5f' }}, title:{{ display:true, text:xlabel, color:'#94a3b8' }} }},
        y:{{ ticks:{{ color:'#94a3b8' }}, grid:{{ color:'#1e3a5f' }}, title:{{ display:true, text:ylabel, color:'#94a3b8' }} }}
      }}
    }}
  }});
}}
mkScatter('sc-atr',   'ATR',    'Chuva Mensal (mm)', 'ATR (kg/t)');
mkScatter('sc-im',    'IM',     'Chuva Mensal (mm)', 'Imp. Mineral (kg/t)');
mkScatter('sc-iv',    'IV',     'Chuva Mensal (mm)', 'Imp. Vegetal (kg/t)');
mkScatter('sc-aprov', 'APROVEIT','Chuva Mensal (mm)', 'Aproveitamento (%)');

// TCH vs Prec anual
(function() {{
  var pts = D.tch_scatter;
  var anos2 = pts.map(function(p){{return p.ano;}});
  var tch2  = pts.map(function(p){{return p.y;}});
  var prec2 = pts.map(function(p){{return p.x;}});
  new Chart(document.getElementById('ch-tch-prec'), {{
    type:'bar',
    data:{{ labels: anos2, datasets:[
      {{ label:'TCH (t/ha)', data: tch2, backgroundColor:'rgba(22,163,74,0.6)', yAxisID:'y' }},
      {{ label:'Chuva Anual (mm)', data: prec2, type:'line', borderColor:'#3b82f6', borderWidth:2, fill:false, pointRadius:4, yAxisID:'y2' }}
    ]}},
    options:{{ responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{ labels:{{ color:'#94a3b8' }} }} }},
      scales:{{
        x:{{ ticks:{{ color:'#64748b' }}, grid:{{ color:'#1e3a5f' }} }},
        y:{{ ticks:{{ color:'#94a3b8' }}, grid:{{ color:'#1e3a5f' }}, title:{{ display:true, text:'TCH (t/ha)', color:'#94a3b8' }} }},
        y2:{{ position:'right', ticks:{{ color:'#3b82f6' }}, grid:{{ drawOnChartArea:false }}, title:{{ display:true, text:'Chuva (mm)', color:'#3b82f6' }} }}
      }}
    }}
  }});
}})();

// MELHORES MESES: Rankings
function mkRankTable(elId, data, valKey, valLabel) {{
  var maxVal = Math.max.apply(null, data.map(function(d){{ return d[valKey]||0; }}));
  var h = '<thead><tr><th>#</th><th>Mes</th><th>'+valLabel+'</th><th>Chuva Hist. (mm)</th></tr></thead><tbody>';
  data.forEach(function(d,i) {{
    var pct = maxVal > 0 ? Math.round((d[valKey]||0)/maxVal*100) : 0;
    var clr = i<3 ? 'style="color:var(--green-xl)"' : i>=data.length-3 ? 'style="color:#fca5a5"' : '';
    h += '<tr><td class="rank-pos" '+clr+'>'+(i+1)+'</td><td>'+d.nome+'</td><td>'+fmt(d[valKey],2)+'<div class="bar-bg"><div class="bar-fill" style="width:'+pct+'%"></div></div></td><td>'+(d.chuva!==undefined&&d.chuva!==null?fmt(d.chuva,0)+' mm':'—')+'</td></tr>';
  }});
  h += '</tbody>';
  document.getElementById(elId).innerHTML = h;
}}
mkRankTable('tab-rank-atr',   D.ranking_atr,   'atr',   'ATR Medio (kg/t)');
mkRankTable('tab-rank-aprov', D.ranking_aprov, 'aprov', 'Aproveitamento (%)');

(function() {{
  var top = D.ranking_atr[0];
  var t3  = D.ranking_atr.slice(0,3).map(function(d){{return d.nome;}}).join(', ');
  var chuva3 = D.ranking_atr.slice(0,3).map(function(d){{return d.chuva;}}).filter(function(v){{return v!=null;}});
  var chuvaM = chuva3.length ? Math.round(chuva3.reduce(function(a,b){{return a+b;}},0)/chuva3.length) : null;
  var atrTop = top ? fmt(top.atr,1) : 'N/D';
  document.getElementById('insight-texto').textContent =
    'Melhor periodo para moagem: '+t3+' - ATR medio: '+atrTop+' kg/t'+(chuvaM?' | Chuva media: '+chuvaM+' mm/mes.':'.')+
    ' Periodo seco coincide com maior qualidade da materia-prima: menor diluicao dos acucares pela agua de chuva, reducao de impurezas vegetais e melhor aproveitamento industrial.';
}})();

// ALERTA 2026
(function() {{
  var grid = document.getElementById('alerta-grid');
  D.alertas_2026.forEach(function(a) {{
    var statuses = [a.status_atr,a.status_im,a.status_iv,a.status_chuva];
    var overall = 'sem-dados';
    if(statuses.indexOf('critico')>=0) overall='critico';
    else if(statuses.indexOf('atencao')>=0) overall='atencao';
    else if(statuses.indexOf('normal')>=0) overall='normal';
    var icons = {{ normal:'OK', atencao:'ATENCAO', critico:'CRITICO', 'sem-dados':'—' }};
    var semDados = a.atr_26 === null && a.moagem_26 === null;
    var inner = semDados ? '<div style="color:#64748b;font-size:.8rem">Sem dados - mes nao iniciado</div>' :
      '<div class="alerta-row"><span class="lbl">Moagem</span><span>'+(a.moagem_26?fmt(a.moagem_26,0)+' t':'—')+'</span></div>'+
      '<div class="alerta-row"><span class="lbl">ATR</span><span>'+(a.atr_26??'—')+' / '+(a.atr_med??'—')+' kg/t</span></div>'+
      '<div class="alerta-row"><span class="lbl">Chuva</span><span>'+(a.chuva_26??'—')+' / '+(a.chuva_med?fmt(a.chuva_med,0):'—')+' mm</span></div>'+
      '<div class="alerta-row"><span class="lbl">Imp.Min.</span><span>'+(a.im_26??'—')+'</span></div>'+
      '<div class="alerta-row"><span class="lbl">Imp.Veg.</span><span>'+(a.iv_26??'—')+'</span></div>';
    grid.innerHTML += '<div class="alerta-card '+overall+'"><div class="alerta-mes">'+icons[overall]+' '+a.nome+' 2026</div>'+inner+'</div>';
  }});
}})();

// ALERTA comparativo chart
(function() {{
  var meses = D.alertas_2026.map(function(a){{return a.nome;}});
  var atr26  = D.alertas_2026.map(function(a){{return a.atr_26;}});
  var atrMed = D.alertas_2026.map(function(a){{return a.atr_med;}});
  var c26    = D.alertas_2026.map(function(a){{return a.chuva_26;}});
  var cMed   = D.alertas_2026.map(function(a){{return a.chuva_med;}});
  new Chart(document.getElementById('ch-alerta-comp'), {{
    type:'bar',
    data:{{ labels: meses, datasets:[
      {{ label:'ATR 2026', data:atr26, backgroundColor:'rgba(34,197,94,0.7)', yAxisID:'y' }},
      {{ label:'ATR Hist. Med.', data:atrMed, type:'line', borderColor:'#4ade80', borderDash:[5,5], fill:false, pointRadius:4, yAxisID:'y' }},
      {{ label:'Chuva 2026 (mm)', data:c26, backgroundColor:'rgba(59,130,246,0.4)', yAxisID:'y2' }},
      {{ label:'Chuva Hist. Med. (mm)', data:cMed, type:'line', borderColor:'#93c5fd', borderDash:[4,4], fill:false, pointRadius:3, yAxisID:'y2' }},
    ]}},
    options:{{ responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{ labels:{{ color:'#94a3b8', font:{{size:11}} }} }} }},
      scales:{{
        x:{{ ticks:{{ color:'#64748b' }}, grid:{{ color:'#1e3a5f' }} }},
        y:{{ ticks:{{ color:'#94a3b8' }}, grid:{{ color:'#1e3a5f' }}, title:{{ display:true, text:'ATR (kg/t)', color:'#94a3b8' }} }},
        y2:{{ position:'right', ticks:{{ color:'#3b82f6' }}, grid:{{ drawOnChartArea:false }}, title:{{ display:true, text:'Chuva (mm)', color:'#3b82f6' }} }}
      }}
    }}
  }});
}})();
</script>
</body>
</html>"""

# SALVA HTML
os.makedirs(os.path.dirname(OUT_HTML_MAIN), exist_ok=True)
os.makedirs(os.path.dirname(OUT_HTML_REL),  exist_ok=True)

with open(OUT_HTML_MAIN, "w", encoding="utf-8") as f:
    f.write(html)
print(f"[OK] HTML salvo: {OUT_HTML_MAIN}")

with open(OUT_HTML_REL, "w", encoding="utf-8") as f:
    f.write(html)
print(f"[OK] HTML salvo: {OUT_HTML_REL}")

# GIT ADD + COMMIT + PUSH
print("[GIT] Fazendo commit...")
REPO = r"C:\01 - UMOE\09 - IA\umoe-os-8"
now_str = datetime.now().strftime("%Y%m%d-%H%M")

def git(cmd):
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, shell=True)
    if r.stdout.strip(): print("   ", r.stdout.strip()[:160])
    if r.stderr.strip(): print("   STDERR:", r.stderr.strip()[:160])
    return r.returncode

git('git add "UMOE-OS-8.0/01-AGENTE-AUTONOMO/painel-engine.py"')
git('git add "UMOE-OS-8.0/Relatorios/UMOE_Painel_Executivo_MASTER.html"')
msg = f"Painel Engine {now_str} -- Painel Executivo Master com correlacoes clima/qualidade"
git(f'git commit -m "{msg}"')
git("git push")
print("[GIT] Concluido.")

print("\n" + "="*60)
print("RESUMO FINAL")
print("="*60)
print(f"Moagem 2026 acumulada: {moagem_acum_2026:,.0f} t")
print(f"ATR 2026 ponderado:    {atr_real_2026} kg/t")
print(f"Chuva safra 2026:      {chuva_safra_2026:.0f} mm")
print(f"Gap vs meta:           {gap_meta_pct}%")
print()
print("CORRELACOES:")
for k2, v in correlacoes.items():
    print(f"  {v['label']}: r={v['r']} ({v['interp']}) n={v['n']}")
print()
if top3_atr:
    print("TOP 3 MESES ATR:")
    for pos, (mes, val) in enumerate(top3_atr, 1):
        print(f"  {pos}. {MESES_NOME[mes]}: {val} kg/t")
    print("BOTTOM 3 MESES ATR:")
    for pos, (mes, val) in enumerate(bot3_atr, 1):
        print(f"  {pos}. {MESES_NOME[mes]}: {val} kg/t")
print("="*60)
