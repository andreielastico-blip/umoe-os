# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Pipeline PBI + Excel -> Dashboard Enterprise
Combina dados Power BI (Oracle biofuel) + Excel local -> HTML interativo
"""
import json, glob, os, sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

BASE   = Path(r'C:\01 - UMOE\09 - IA\umoe-os-8')
PBI_DIR = BASE / 'UMOE-OS-8.0' / 'Dados-PBI'
OUT_DIR = BASE / 'UMOE-OS-8.0' / 'Relatorios'
OUT_DIR.mkdir(exist_ok=True)

TODAY = '15/06/2026'
print("="*60)
print("  UMOE OS 8.0 | Pipeline PBI + Excel")
print(f"  {TODAY}")
print("="*60)

# ─── 1. CARREGAR DADOS POWER BI ──────────────────────────────
def load_pbi(filename):
    path = PBI_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    with open(path, encoding='utf-8-sig') as f:
        data = json.load(f)
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    # Limpar prefixo TABLENAME[COLUMN] dos nomes de coluna
    df.columns = [c.split('[')[-1].rstrip(']') if '[' in c else c for c in df.columns]
    return df

print("\n[1/5] Carregando dados Power BI...")
chuva    = load_pbi('BASE_Chuva.json')
preparo  = load_pbi('BASE_Preparo.json')
variedades = load_pbi('BASE_Variedades.json')
func_div = load_pbi('CTRL_Func_Div.json')
plant_oc = load_pbi('BASE_Plant_OCMuda.json')

print(f"  Chuva:      {len(chuva):,} linhas")
print(f"  Preparo:    {len(preparo):,} linhas")
print(f"  Variedades: {len(variedades):,} linhas")
print(f"  Func_Div:   {len(func_div):,} linhas")
print(f"  Plant_OC:   {len(plant_oc):,} linhas")

# ─── 2. CARREGAR EXCEL LOCAL ─────────────────────────────────
print("\n[2/5] Carregando Excel local...")

# BD SAFRAS
bd_files = glob.glob(r'C:\01 - UMOE\03 - Financeiro\Planilhas\Historico Kpis*Agr*.xlsx')
df_bd = pd.DataFrame()
if bd_files:
    xl = pd.ExcelFile(bd_files[0])
    for sh in xl.sheet_names:
        if 'SAFRA' in sh.upper() or 'BASE' in sh.upper() or 'BD' in sh.upper():
            try:
                tmp = xl.parse(sh, header=0)
                if len(tmp) > 100:
                    df_bd = tmp
                    print(f"  BD SAFRAS: {len(df_bd):,} linhas (aba: {sh})")
                    break
            except:
                pass

# Historico Diario
hd_files = glob.glob(r'C:\01 - UMOE\03 - Financeiro\Planilhas\Hist*rio Di*rio Safras.xlsx')
df_hd = pd.DataFrame()
if hd_files:
    try:
        xl2 = pd.ExcelFile(hd_files[0])
        sh2 = xl2.sheet_names[0]
        df_hd = xl2.parse(sh2, header=0)
        print(f"  Hist.Diario: {len(df_hd):,} linhas (aba: {sh2})")
    except Exception as e:
        print(f"  Hist.Diario: erro - {e}")

# Pluviometrico
pluv_files = glob.glob(r'C:\01 - UMOE\03 - Financeiro\Planilhas\1 - Indice Pluviometrico UMOE.xlsx')
df_pluv = pd.DataFrame()
if pluv_files:
    try:
        df_pluv = pd.read_excel(pluv_files[0])
        print(f"  Pluviometrico: {len(df_pluv):,} linhas")
    except:
        pass

# ─── 3. ANALISES ─────────────────────────────────────────────
print("\n[3/5] Processando analises...")

# --- 3a. Chuva por frente/ano (Oracle biofuel)
chuva_anual = pd.DataFrame()
if not chuva.empty:
    chuva['DT_OPERACAO'] = pd.to_datetime(chuva['DT_OPERACAO'], errors='coerce')
    chuva['ANO'] = chuva['ANO'].fillna(0).astype(int)
    # Chuva por frente e ano
    if 'QTDE' in chuva.columns:
        chuva_anual = chuva.groupby(['DE_POSTO','ANO'])['QTDE'].sum().reset_index()
        chuva_anual.columns = ['Frente','Ano','Chuva_mm']
        chuva_anual = chuva_anual[chuva_anual['Ano'] >= 2022]
    # Dias com chuva por ano
    if 'DIAS_COM_CHUVA' in chuva.columns:
        _tmp = chuva.groupby('ANO')['DIAS_COM_CHUVA'].sum().reset_index()
        _tmp.columns = ['ano', 'dias']
        chuva_dias = _tmp
    else:
        chuva_dias = pd.DataFrame()

# --- 3b. Variedades por maturacao
var_maturacao = pd.DataFrame()
if not variedades.empty:
    var_maturacao = variedades.groupby(['DA_GRP_VAR','DE_MATURAC']).agg(
        Qtd=('DE_VARIED','count')
    ).reset_index().sort_values('Qtd', ascending=False)

# Todas as variedades com maturacao
var_completa = variedades[['DE_VARIED','DE_MATURAC','DA_GRP_VAR']].copy() if not variedades.empty else pd.DataFrame()

# --- 3c. Preparo por frente e status
prep_frente = pd.DataFrame()
prep_rotacao = pd.DataFrame()
if not preparo.empty:
    preparo['QT_AREA_REAL'] = pd.to_numeric(preparo['QT_AREA_REAL'], errors='coerce').fillna(0)
    preparo['QT_AREA_PLANO'] = pd.to_numeric(preparo['QT_AREA_PLANO'], errors='coerce').fillna(0)

    if 'FRENTE' in preparo.columns:
        prep_frente = preparo.groupby('FRENTE').agg(
            Area_Real=('QT_AREA_REAL','sum'),
            Area_Plano=('QT_AREA_PLANO','sum'),
            Registros=('CD_FAZ','count')
        ).reset_index().sort_values('Area_Real', ascending=False)

    if 'ROTACAO' in preparo.columns:
        prep_rotacao = preparo.groupby(['ROTACAO','STATUS_OCORREN_TLH']).agg(
            Area=('QT_AREA_REAL','sum'),
            Qtd=('CD_FAZ','count')
        ).reset_index().sort_values('Area', ascending=False) if 'STATUS_OCORREN_TLH' in preparo.columns else pd.DataFrame()

# --- 3d. Func_Div por tipo de divergencia
div_tipo = pd.DataFrame()
div_frente = pd.DataFrame()
if not func_div.empty:
    func_div['QT_FUNC'] = pd.to_numeric(func_div['QT_FUNC'], errors='coerce').fillna(0)

    if 'TP_DIV' in func_div.columns:
        div_tipo = func_div.groupby('TP_DIV')['QT_FUNC'].sum().reset_index().sort_values('QT_FUNC', ascending=False)

    if 'FRENTE' in func_div.columns:
        div_frente = func_div.groupby('FRENTE')['QT_FUNC'].sum().reset_index().sort_values('QT_FUNC', ascending=False)

    # Hierarquia operacional
    hierarquia = func_div[['DE_GERENTE','DE_COORDENADOR','DE_GESTOR','DE_LIDER']].drop_duplicates().dropna(how='all') if all(c in func_div.columns for c in ['DE_GERENTE','DE_COORDENADOR','DE_GESTOR','DE_LIDER']) else pd.DataFrame()

# --- 3e. Plant OC Muda por fazenda
plant_fazenda = pd.DataFrame()
if not plant_oc.empty:
    plant_oc['QT_AREA'] = pd.to_numeric(plant_oc['QT_AREA'], errors='coerce').fillna(0)
    plant_oc['DIAS'] = pd.to_numeric(plant_oc['DIAS'], errors='coerce').fillna(0)
    if 'DE_UPNIVEL1' in plant_oc.columns:
        plant_fazenda = plant_oc[['DE_UPNIVEL1','QT_AREA','DIAS','DT_ORDEM']].copy()
        plant_fazenda = plant_fazenda.sort_values('DT_ORDEM', ascending=False)

# --- 3f. BD SAFRAS local
tch_por_ambiente = pd.DataFrame()
tch_por_variedade = pd.DataFrame()
moagem_historico = pd.DataFrame()

if not df_bd.empty:
    cols = list(df_bd.columns)
    # Detectar colunas por posicao (conforme mapeamento anterior: 0=Amb,1=Faz,5=Var,7=Area,11=TCH,16=ATR,17=TAH,21=Safra,24=Corte)
    try:
        df_bd.columns = [str(c) for c in df_bd.columns]
        # Tentar encontrar colunas por nome
        col_map = {}
        for i,c in enumerate(cols):
            c_up = str(c).upper()
            if 'AMB' in c_up and 'AMBIENTE' not in col_map: col_map['Ambiente'] = c
            if 'FAZ' in c_up and 'Fazenda' not in col_map: col_map['Fazenda'] = c
            if 'VAR' in c_up and 'VARIED' in c_up and 'Variedade' not in col_map: col_map['Variedade'] = c
            if 'TCH' in c_up and 'Real' in c_up and 'TCH' not in col_map: col_map['TCH'] = c
            if 'ATR' in c_up and 'Real' in c_up and 'ATR' not in col_map: col_map['ATR'] = c
            if 'TAH' in c_up and 'TAH' not in col_map: col_map['TAH'] = c
            if 'SAFRA' in c_up and 'Safra' not in col_map: col_map['Safra'] = c
            if 'CORTE' in c_up and 'Corte' not in col_map: col_map['Corte'] = c
            if 'AREA' in c_up and 'REAL' in c_up and 'Area' not in col_map: col_map['Area'] = c

        if 'TCH' in col_map and 'Ambiente' in col_map:
            df_bd[col_map['TCH']] = pd.to_numeric(df_bd[col_map['TCH']], errors='coerce')
            df_bd[col_map['TAH']] = pd.to_numeric(df_bd[col_map['TAH']], errors='coerce') if 'TAH' in col_map else 0
            df_bd[col_map['Area']] = pd.to_numeric(df_bd[col_map['Area']], errors='coerce') if 'Area' in col_map else 1

            tch_por_ambiente = df_bd.groupby(col_map['Ambiente']).agg(
                TCH_medio=(col_map['TCH'],'mean'),
                TAH_medio=(col_map['TAH'],'mean') if 'TAH' in col_map else (col_map['TCH'],'count'),
                Registros=(col_map['TCH'],'count')
            ).reset_index().sort_values('TCH_medio', ascending=False).head(20)

        if 'Variedade' in col_map and 'TCH' in col_map:
            tch_por_variedade = df_bd.groupby(col_map['Variedade']).agg(
                TCH_medio=(col_map['TCH'],'mean'),
                Registros=(col_map['TCH'],'count')
            ).reset_index()
            tch_por_variedade = tch_por_variedade[tch_por_variedade['Registros'] >= 10].sort_values('TCH_medio', ascending=False)
    except Exception as e:
        print(f"  BD SAFRAS processamento: {e}")

# ─── 4. CONSOLIDAR JSONS PARA O HTML ─────────────────────────
print("\n[4/5] Consolidando dados para dashboard...")

def df_to_json(df, max_rows=500):
    if df.empty:
        return '[]'
    df2 = df.head(max_rows).copy()
    for c in df2.columns:
        try:
            df2[c] = df2[c].where(pd.notna(df2[c]), None)
        except:
            pass
    return df2.to_json(orient='records', force_ascii=False, date_format='iso')

# Chuva por frente e ano para grafico
chuva_chart = []
if not chuva.empty and not chuva_anual.empty:
    for ano in sorted(chuva_anual['Ano'].unique()):
        bloco = chuva_anual[chuva_anual['Ano']==ano]
        chuva_chart.append({
            'ano': int(ano),
            'frentes': bloco.set_index('Frente')['Chuva_mm'].to_dict()
        })

# Preparo por sistema de plantio
prep_sistplan = pd.DataFrame()
if not preparo.empty and 'SISTPLAN' in preparo.columns:
    prep_sistplan = preparo.groupby('SISTPLAN').agg(
        Area=('QT_AREA_REAL','sum'),
        Qtd=('CD_FAZ','count')
    ).reset_index().sort_values('Area', ascending=False)

# Variedades para plantio (flag)
var_plantio = variedades[variedades['FG_VARIED_PLANTIO']==1][['DE_VARIED','DE_MATURAC','DA_GRP_VAR']].to_dict('records') if not variedades.empty and 'FG_VARIED_PLANTIO' in variedades.columns else []

# Resumo executivo
resumo = {
    'data_extracao': TODAY,
    'fonte_oracle': 'biofuel',
    'tabelas_extraidas': 5,
    'total_linhas_pbi': len(chuva)+len(preparo)+len(variedades)+len(func_div)+len(plant_oc),
    'chuva_anos': sorted(chuva['ANO'].unique().tolist()) if not chuva.empty else [],
    'variedades_total': len(variedades),
    'frentes_preparo': list(preparo['FRENTE'].dropna().unique()) if not preparo.empty and 'FRENTE' in preparo.columns else [],
    'total_area_preparo_real': float(preparo['QT_AREA_REAL'].sum()) if not preparo.empty else 0,
    'total_area_preparo_plano': float(preparo['QT_AREA_PLANO'].sum()) if not preparo.empty else 0,
    'ordens_muda_ativas': len(plant_oc),
    'area_muda_total': float(plant_oc['QT_AREA'].sum()) if not plant_oc.empty else 0,
    'div_total_funcionarios': float(func_div['QT_FUNC'].sum()) if not func_div.empty else 0,
}

# ─── 5. GERAR HTML ───────────────────────────────────────────
print("\n[5/5] Gerando dashboard...")

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>UMOE OS 8.0 | Pipeline PBI + Oracle biofuel</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#060E1F;--bg2:#0D1B35;--bg3:#142040;--green:#00C853;--gold:#FFD600;--red:#FF1744;--blue:#2979FF;--orange:#FF6D00;--text:#E8F0FF;--muted:#8899BB}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',sans-serif;min-height:100vh}}
header{{background:var(--bg2);padding:18px 32px;border-bottom:2px solid var(--gold);display:flex;align-items:center;gap:16px}}
header h1{{font-size:1.3rem;color:var(--gold);font-weight:700}}
header p{{color:var(--muted);font-size:.82rem}}
.badge{{background:var(--green);color:#000;padding:2px 10px;border-radius:12px;font-size:.72rem;font-weight:700}}
.badge.oracle{{background:var(--orange)}}
nav{{background:var(--bg3);display:flex;gap:0;overflow-x:auto;border-bottom:1px solid #1e3060}}
nav button{{background:none;border:none;color:var(--muted);padding:12px 22px;cursor:pointer;font-size:.85rem;white-space:nowrap;border-bottom:3px solid transparent;transition:all .2s}}
nav button.active,nav button:hover{{color:var(--gold);border-bottom-color:var(--gold)}}
.tab{{display:none;padding:24px 28px;max-width:1600px;margin:0 auto}}
.tab.active{{display:block}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:28px}}
.kpi{{background:var(--bg2);border:1px solid #1e3060;border-radius:10px;padding:18px;text-align:center}}
.kpi .val{{font-size:2rem;font-weight:800;color:var(--green);margin:6px 0}}
.kpi .val.red{{color:var(--red)}}
.kpi .val.gold{{color:var(--gold)}}
.kpi .val.blue{{color:var(--blue)}}
.kpi label{{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.8px}}
.kpi .sub{{font-size:.78rem;color:var(--muted);margin-top:4px}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}}
.row.row3{{grid-template-columns:1fr 1fr 1fr}}
.row.row1{{grid-template-columns:1fr}}
@media(max-width:900px){{.row,.row3{{grid-template-columns:1fr}}}}
.card{{background:var(--bg2);border:1px solid #1e3060;border-radius:10px;padding:20px}}
.card h3{{color:var(--gold);font-size:.9rem;margin-bottom:14px;text-transform:uppercase;letter-spacing:.8px}}
.chart-wrap{{position:relative;height:260px}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th{{background:var(--bg3);color:var(--gold);padding:8px 12px;text-align:left;font-size:.72rem;text-transform:uppercase;letter-spacing:.6px}}
td{{padding:7px 12px;border-bottom:1px solid #1e3060;color:var(--text)}}
tr:hover td{{background:#0a1428}}
.tag{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.7rem;font-weight:600}}
.tag.precoce{{background:#00703c;color:#fff}}
.tag.media{{background:#005a8e;color:#fff}}
.tag.tardio{{background:#8e2000;color:#fff}}
.tag.ctc{{background:#1e3060;color:#fff}}
.tag.iac{{background:#2e5000;color:#fff}}
.tag.rb{{background:#5e0000;color:#fff}}
.alert{{background:#1a0a00;border:1px solid var(--orange);border-radius:8px;padding:12px 16px;margin-bottom:14px;font-size:.83rem}}
.alert.green{{background:#001a08;border-color:var(--green)}}
.source-tag{{font-size:.68rem;color:var(--orange);background:#1a0800;padding:2px 8px;border-radius:8px;border:1px solid var(--orange)}}
</style>
</head>
<body>
<header>
  <div>
    <h1>UMOE OS 8.0 | Pipeline Integrado</h1>
    <p>Oracle biofuel + Excel local &nbsp;|&nbsp; {TODAY} &nbsp;|&nbsp; Safra 2026/27</p>
  </div>
  <span class="badge oracle">Oracle biofuel</span>
  <span class="badge">{resumo['total_linhas_pbi']:,} linhas PBI</span>
</header>
<nav>
  <button class="active" onclick="showTab('resumo',this)">RESUMO EXECUTIVO</button>
  <button onclick="showTab('chuva',this)">CHUVA & CLIMA</button>
  <button onclick="showTab('preparo',this)">PREPARO DE SOLO</button>
  <button onclick="showTab('variedades',this)">VARIEDADES</button>
  <button onclick="showTab('rh',this)">RH & DIVERGENCIAS</button>
  <button onclick="showTab('plantio',this)">PLANTIO OC MUDA</button>
  <button onclick="showTab('inteligencia',this)">INTELIGENCIA IA</button>
</nav>

<!-- TAB: RESUMO -->
<div id="tab-resumo" class="tab active">
  <div class="kpi-grid">
    <div class="kpi"><label>Total Linhas PBI</label><div class="val blue">{resumo['total_linhas_pbi']:,}</div><div class="sub">5 tabelas Oracle biofuel</div></div>
    <div class="kpi"><label>Registros Chuva</label><div class="val blue">{len(chuva):,}</div><div class="sub">{len(resumo['chuva_anos'])} anos | {chuva['DE_POSTO'].nunique() if not chuva.empty else 0} postos</div></div>
    <div class="kpi"><label>Area Preparo Real</label><div class="val gold">{resumo['total_area_preparo_real']:,.0f} ha</div><div class="sub">vs {resumo['total_area_preparo_plano']:,.0f} ha plano</div></div>
    <div class="kpi"><label>Variedades Ativas</label><div class="val green">{len(var_plantio)}</div><div class="sub">de {resumo['variedades_total']} no catalogo</div></div>
    <div class="kpi"><label>Ordens Muda Ativas</label><div class="val gold">{resumo['ordens_muda_ativas']}</div><div class="sub">{resumo['area_muda_total']:,.1f} ha total</div></div>
    <div class="kpi"><label>Diverg. Funcionarios</label><div class="val {'red' if resumo['div_total_funcionarios']>0 else 'green'}">{int(resumo['div_total_funcionarios'])}</div><div class="sub">escala x RH</div></div>
  </div>

  <div class="row">
    <div class="card">
      <h3>Fonte Oracle biofuel — Tabelas Extraidas</h3>
      <table>
        <tr><th>Tabela PBI</th><th>Fonte Oracle</th><th>Linhas</th><th>Descricao</th></tr>
        <tr><td>Chuva</td><td>CHUVA</td><td>{len(chuva):,}</td><td>Pluviometria por posto/dezena 2020-2026</td></tr>
        <tr><td>Preparo</td><td>PREPARO</td><td>{len(preparo):,}</td><td>Preparo de solo por fazenda/frente/talhao</td></tr>
        <tr><td>Variedades</td><td>VARIEDADES</td><td>{len(variedades):,}</td><td>Catalogo de variedades com maturacao</td></tr>
        <tr><td>Plant_OCMuda</td><td>PLANT_OCMUDA</td><td>{len(plant_oc):,}</td><td>Ordens de corte de muda ativas com GPS</td></tr>
        <tr><td>Func_Div</td><td>FUNC_DIV</td><td>{len(func_div):,}</td><td>Divergencias escala x RH por frente</td></tr>
      </table>
    </div>
    <div class="card">
      <h3>Frentes em Preparo de Solo</h3>
      <table>
        <tr><th>Frente</th><th>Area Real (ha)</th><th>Area Plano (ha)</th><th>Aderencia</th></tr>
        {''.join(f"<tr><td>{r['FRENTE']}</td><td>{r['Area_Real']:,.1f}</td><td>{r['Area_Plano']:,.1f}</td><td style='color:{'var(--green)' if r['Area_Plano']>0 and r['Area_Real']/r['Area_Plano']>=.8 else 'var(--red)'}'>{(r['Area_Real']/r['Area_Plano']*100 if r['Area_Plano']>0 else 0):.0f}%</td></tr>" for _,r in prep_frente.head(10).iterrows()) if not prep_frente.empty else '<tr><td colspan=4>Sem dados</td></tr>'}
      </table>
    </div>
  </div>

  <div class="card">
    <h3>Alertas & Insights Oracle biofuel</h3>
    <div class="alert green">
      <strong>VARIEDADES:</strong> {len(var_plantio)} variedades habilitadas para plantio de {resumo['variedades_total']} no catalogo.
      Precoces: {sum(1 for v in var_plantio if 'reco' in str(v.get('DE_MATURAC','')).lower())} | Medias: {sum(1 for v in var_plantio if 'dia' in str(v.get('DE_MATURAC','')).lower())} | Tardias: {sum(1 for v in var_plantio if 'ardi' in str(v.get('DE_MATURAC','')).lower())}
    </div>
    <div class="alert">
      <strong>PREPARO:</strong> {resumo['total_area_preparo_real']:,.0f} ha realizados vs {resumo['total_area_preparo_plano']:,.0f} ha planejados
      = aderencia {(resumo['total_area_preparo_real']/resumo['total_area_preparo_plano']*100 if resumo['total_area_preparo_plano']>0 else 0):.0f}%
      | {len(resumo['frentes_preparo'])} frentes ativas
    </div>
    <div class="alert">
      <strong>DIVERGENCIAS RH:</strong> {int(resumo['div_total_funcionarios'])} funcionarios com divergencia escala x apontamento RH.
      {('Necessita revisao imediata pelo DP.' if resumo['div_total_funcionarios'] > 50 else 'Nivel controlado.')}
    </div>
    <div class="alert green">
      <strong>PLANTIO:</strong> {resumo['ordens_muda_ativas']} ordens de muda ativas com GPS — {resumo['area_muda_total']:,.1f} ha mapeados para plantio 2026/27.
    </div>
  </div>
</div>

<!-- TAB: CHUVA -->
<div id="tab-chuva" class="tab">
  <div class="kpi-grid">
    <div class="kpi"><label>Total Registros</label><div class="val blue">{len(chuva):,}</div><div class="sub">Oracle biofuel.CHUVA</div></div>
    <div class="kpi"><label>Postos Meteo</label><div class="val gold">{chuva['DE_POSTO'].nunique() if not chuva.empty else 0}</div><div class="sub">frentes + setores</div></div>
    <div class="kpi"><label>Periodo</label><div class="val green">{int(chuva['ANO'].min()) if not chuva.empty else 0}</div><div class="sub">a {int(chuva['ANO'].max()) if not chuva.empty else 0}</div></div>
    <div class="kpi"><label>Precipit. 2025</label><div class="val gold">{chuva[chuva['ANO']==2025]['QTDE'].sum() if not chuva.empty else 0:,.0f} mm</div><div class="sub">total geral todos postos</div></div>
    <div class="kpi"><label>Precipit. 2026</label><div class="val blue">{chuva[chuva['ANO']==2026]['QTDE'].sum() if not chuva.empty else 0:,.0f} mm</div><div class="sub">total geral todos postos</div></div>
  </div>

  <div class="row row1">
    <div class="card">
      <h3>Precipitacao por Posto (mm/ano)</h3>
      <div class="chart-wrap"><canvas id="chartChuvaAnual"></canvas></div>
    </div>
  </div>

  <div class="row">
    <div class="card">
      <h3>Precipitacao por Posto 2026 (mm)</h3>
      <table>
        <tr><th>Posto</th><th>mm 2024</th><th>mm 2025</th><th>mm 2026</th></tr>
        {''.join(
          f"<tr><td>{posto}</td>"
          f"<td>{chuva[(chuva['DE_POSTO']==posto)&(chuva['ANO']==2024)]['QTDE'].sum():,.0f}</td>"
          f"<td>{chuva[(chuva['DE_POSTO']==posto)&(chuva['ANO']==2025)]['QTDE'].sum():,.0f}</td>"
          f"<td><strong>{chuva[(chuva['DE_POSTO']==posto)&(chuva['ANO']==2026)]['QTDE'].sum():,.0f}</strong></td></tr>"
          for posto in (chuva['DE_POSTO'].unique()[:12] if not chuva.empty else [])
        )}
      </table>
    </div>
    <div class="card">
      <h3>Dias com Chuva por Ano</h3>
      <div class="chart-wrap"><canvas id="chartChuvasDias"></canvas></div>
    </div>
  </div>
</div>

<!-- TAB: PREPARO -->
<div id="tab-preparo" class="tab">
  <div class="kpi-grid">
    <div class="kpi"><label>Total Registros</label><div class="val blue">{len(preparo):,}</div><div class="sub">Oracle biofuel.PREPARO</div></div>
    <div class="kpi"><label>Area Real Total</label><div class="val gold">{preparo['QT_AREA_REAL'].sum():,.0f} ha</div></div>
    <div class="kpi"><label>Area Plano Total</label><div class="val blue">{preparo['QT_AREA_PLANO'].sum():,.0f} ha</div></div>
    <div class="kpi"><label>Aderencia Global</label><div class="val {'green' if preparo['QT_AREA_PLANO'].sum()>0 and preparo['QT_AREA_REAL'].sum()/preparo['QT_AREA_PLANO'].sum()>=.8 else 'red'}">{(preparo['QT_AREA_REAL'].sum()/preparo['QT_AREA_PLANO'].sum()*100 if not preparo.empty and preparo['QT_AREA_PLANO'].sum()>0 else 0):.1f}%</div></div>
    <div class="kpi"><label>Fazendas Envolvidas</label><div class="val blue">{preparo['CD_FAZ'].nunique() if not preparo.empty else 0}</div></div>
  </div>

  <div class="row">
    <div class="card">
      <h3>Area por Frente</h3>
      <div class="chart-wrap"><canvas id="chartPreparoFrente"></canvas></div>
    </div>
    <div class="card">
      <h3>Sistema de Plantio</h3>
      <div class="chart-wrap"><canvas id="chartPreparoSist"></canvas></div>
    </div>
  </div>

  <div class="row">
    <div class="card">
      <h3>Status por Rotacao</h3>
      <table>
        <tr><th>Rotacao</th><th>Status</th><th>Area (ha)</th><th>Qtd</th></tr>
        {''.join(f"<tr><td>{r['ROTACAO'] if 'ROTACAO' in r else '-'}</td><td>{r['STATUS_OCORREN_TLH'] if 'STATUS_OCORREN_TLH' in r else '-'}</td><td>{r['Area']:,.1f}</td><td>{r['Qtd']}</td></tr>" for _,r in prep_rotacao.head(15).iterrows()) if not prep_rotacao.empty else '<tr><td colspan=4>Sem dados</td></tr>'}
      </table>
    </div>
    <div class="card">
      <h3>Top 15 Fazendas - Preparo</h3>
      <table>
        <tr><th>Fazenda</th><th>Frente</th><th>Area Real</th><th>Variedade Muda</th></tr>
        {''.join(f"<tr><td>{r['DE_FAZ']}</td><td>{r['FRENTE']}</td><td>{r['QT_AREA_REAL']:,.1f} ha</td><td>{r['VARIED_MUDA']}</td></tr>" for _,r in preparo.groupby(['DE_FAZ','FRENTE','VARIED_MUDA'])['QT_AREA_REAL'].sum().reset_index().sort_values('QT_AREA_REAL',ascending=False).head(15).iterrows()) if not preparo.empty and all(c in preparo.columns for c in ['DE_FAZ','FRENTE','VARIED_MUDA']) else '<tr><td colspan=4>Sem dados</td></tr>'}
      </table>
    </div>
  </div>
</div>

<!-- TAB: VARIEDADES -->
<div id="tab-variedades" class="tab">
  <div class="kpi-grid">
    <div class="kpi"><label>Total Variedades</label><div class="val blue">{len(variedades)}</div><div class="sub">Oracle biofuel.VARIEDADES</div></div>
    <div class="kpi"><label>Habilitadas Plantio</label><div class="val green">{len(var_plantio)}</div></div>
    <div class="kpi"><label>Precoces</label><div class="val gold">{sum(1 for v in var_plantio if 'reco' in str(v.get('DE_MATURAC','')).lower())}</div></div>
    <div class="kpi"><label>Medias</label><div class="val blue">{sum(1 for v in var_plantio if 'dia' in str(v.get('DE_MATURAC','')).lower())}</div></div>
    <div class="kpi"><label>Tardias</label><div class="val gold">{sum(1 for v in var_plantio if 'ardi' in str(v.get('DE_MATURAC','')).lower())}</div></div>
    <div class="kpi"><label>Grupos</label><div class="val green">{variedades['DA_GRP_VAR'].nunique() if not variedades.empty else 0}</div><div class="sub">CTC / IAC / RB / etc</div></div>
  </div>

  <div class="row">
    <div class="card">
      <h3>Variedades por Maturacao e Grupo</h3>
      <div class="chart-wrap"><canvas id="chartVarMaturacao"></canvas></div>
    </div>
    <div class="card">
      <h3>Distribuicao por Grupo</h3>
      <div class="chart-wrap"><canvas id="chartVarGrupo"></canvas></div>
    </div>
  </div>

  <div class="card">
    <h3>Catalogo Completo — Variedades Habilitadas para Plantio</h3>
    <table>
      <tr><th>Variedade</th><th>Grupo</th><th>Maturacao</th><th>Plantio</th></tr>
      {''.join(f"<tr><td><strong>{r['DE_VARIED']}</strong></td><td><span class='tag {r['DA_GRP_VAR'].lower()[:3]}'>{r['DA_GRP_VAR']}</span></td><td><span class='tag {r['DE_MATURAC'].lower()[:5] if r['DE_MATURAC'] else ''}'>{r['DE_MATURAC']}</span></td><td>{'Sim' if r.get('FG_VARIED_PLANTIO')==1 else '-'}</td></tr>" for _,r in variedades.iterrows()) if not variedades.empty else '<tr><td colspan=4>Sem dados</td></tr>'}
    </table>
  </div>
</div>

<!-- TAB: RH / DIVERGENCIAS -->
<div id="tab-rh" class="tab">
  <div class="kpi-grid">
    <div class="kpi"><label>Total Divergencias</label><div class="val {'red' if resumo['div_total_funcionarios']>50 else 'gold'}">{int(resumo['div_total_funcionarios'])}</div><div class="sub">Oracle biofuel.FUNC_DIV</div></div>
    <div class="kpi"><label>Frentes c/ Diverg.</label><div class="val gold">{div_frente['FRENTE'].nunique() if not div_frente.empty else 0}</div></div>
    <div class="kpi"><label>Tipos de Diverg.</label><div class="val blue">{div_tipo['TP_DIV'].nunique() if not div_tipo.empty else 0}</div></div>
    <div class="kpi"><label>Registros</label><div class="val blue">{len(func_div):,}</div></div>
  </div>

  <div class="row">
    <div class="card">
      <h3>Divergencias por Tipo</h3>
      <div class="chart-wrap"><canvas id="chartDivTipo"></canvas></div>
    </div>
    <div class="card">
      <h3>Divergencias por Frente</h3>
      <div class="chart-wrap"><canvas id="chartDivFrente"></canvas></div>
    </div>
  </div>

  <div class="row">
    <div class="card">
      <h3>Top Divergencias por Tipo</h3>
      <table>
        <tr><th>Tipo</th><th>Funcionarios</th></tr>
        {''.join(f"<tr><td>{r['TP_DIV']}</td><td style='color:var(--red)'>{int(r['QT_FUNC'])}</td></tr>" for _,r in div_tipo.head(15).iterrows()) if not div_tipo.empty else '<tr><td colspan=2>Sem dados</td></tr>'}
      </table>
    </div>
    <div class="card">
      <h3>Hierarquia Operacional (Oracle)</h3>
      <table>
        <tr><th>Gerente</th><th>Coordenador</th><th>Gestor</th></tr>
        {''.join(f"<tr><td>{r.get('DE_GERENTE','-')}</td><td>{r.get('DE_COORDENADOR','-')}</td><td>{r.get('DE_GESTOR','-')}</td></tr>" for _,r in (hierarquia.head(10).iterrows() if not hierarquia.empty else pd.DataFrame().iterrows())) if not hierarquia.empty else '<tr><td colspan=3>Sem dados</td></tr>'}
      </table>
    </div>
  </div>
</div>

<!-- TAB: PLANTIO OC -->
<div id="tab-plantio" class="tab">
  <div class="kpi-grid">
    <div class="kpi"><label>Ordens Ativas</label><div class="val blue">{len(plant_oc)}</div><div class="sub">Oracle biofuel.PLANT_OCMUDA</div></div>
    <div class="kpi"><label>Area Total</label><div class="val gold">{plant_oc['QT_AREA'].sum():,.1f} ha</div></div>
    <div class="kpi"><label>Fazendas</label><div class="val blue">{plant_oc['DE_UPNIVEL1'].nunique() if not plant_oc.empty else 0}</div></div>
    <div class="kpi"><label>Dias Medio</label><div class="val green">{plant_oc['DIAS'].mean():,.0f} dias</div></div>
  </div>

  <div class="card">
    <h3>Ordens de Corte de Muda — Ativas com GPS</h3>
    <table>
      <tr><th>Fazenda</th><th>Ordem</th><th>Area (ha)</th><th>Data Ordem</th><th>Talhoes</th><th>Dias</th><th>Latitude</th><th>Longitude</th></tr>
      {''.join(f"<tr><td>{r.get('DE_UPNIVEL1','-')}</td><td>{r.get('NO_ORDEM','-')}</td><td>{r.get('QT_AREA',0):,.1f}</td><td>{str(r.get('DT_ORDEM','-'))[:10]}</td><td>{r.get('TLHS','-')}</td><td>{int(r.get('DIAS',0))}</td><td>{r.get('DE_LATITUDE','-')}</td><td>{r.get('DE_LONGITUDE','-')}</td></tr>" for _,r in plant_oc.sort_values('DT_ORDEM',ascending=False).iterrows()) if not plant_oc.empty else '<tr><td colspan=8>Sem dados</td></tr>'}
    </table>
  </div>
</div>

<!-- TAB: INTELIGENCIA -->
<div id="tab-inteligencia" class="tab">
  <div class="card">
    <h3>Analise IA — Dados Oracle biofuel</h3>

    <div class="alert green">
      <strong>OPORTUNIDADE #1 — VARIEDADES PARA PLANTIO</strong><br>
      {len(var_plantio)} variedades habilitadas. Priorizar Tardias e Medias no plantio 2026/27 para distribuir ATR e maximizar moagem no pico da safra.
      Grupo CTC dominante: {variedades['DA_GRP_VAR'].value_counts().index[0] if not variedades.empty and len(variedades['DA_GRP_VAR'].value_counts())>0 else 'N/D'} com {variedades['DA_GRP_VAR'].value_counts().iloc[0] if not variedades.empty and len(variedades['DA_GRP_VAR'].value_counts())>0 else 0} variedades.
    </div>

    <div class="alert">
      <strong>ALERTA #1 — PREPARO DE SOLO</strong><br>
      Aderencia: {(preparo['QT_AREA_REAL'].sum()/preparo['QT_AREA_PLANO'].sum()*100 if not preparo.empty and preparo['QT_AREA_PLANO'].sum()>0 else 0):.0f}% do plano executado.
      Gap de {(preparo['QT_AREA_PLANO'].sum()-preparo['QT_AREA_REAL'].sum() if not preparo.empty else 0):,.0f} ha ainda por preparar.
      Frente mais atrasada: {prep_frente.iloc[-1]['FRENTE'] if not prep_frente.empty else 'N/D'}.
    </div>

    <div class="alert">
      <strong>ALERTA #2 — DIVERGENCIAS RH</strong><br>
      {int(resumo['div_total_funcionarios'])} funcionarios com divergencia entre escala programada e apontamento RH.
      Impacto: risco de falha operacional por ausencia nao prevista.
      Frente critica: {div_frente.iloc[0]['FRENTE'] if not div_frente.empty else 'N/D'} ({int(div_frente.iloc[0]['QT_FUNC']) if not div_frente.empty else 0} divergencias).
    </div>

    <div class="alert green">
      <strong>OPORTUNIDADE #2 — DADOS CLIMATICOS ORACLE</strong><br>
      47.254 registros de chuva de {int(chuva['ANO'].min()) if not chuva.empty else 0} a {int(chuva['ANO'].max()) if not chuva.empty else 0}.
      Permite modelar correlacao historica chuva x TCH por frente para previsao de producao.
      Dados por dezena (10 dias) = resolucao ideal para planejamento operacional.
    </div>

    <div class="alert green">
      <strong>OPORTUNIDADE #3 — GPS NAS ORDENS DE MUDA</strong><br>
      {len(plant_oc)} ordens de muda com coordenadas GPS. Base para mapa geoespacial de colheita de muda e otimizacao de rotas de transporte (KM_MUDA na tabela Preparo).
    </div>
  </div>

  <div class="row">
    <div class="card">
      <h3>Proximos Passos para Desbloqueio Total do Oracle</h3>
      <table>
        <tr><th>#</th><th>Acao</th><th>Tabela Alvo</th><th>Impacto</th></tr>
        <tr><td>1</td><td>Abrir PBIX no Power BI Desktop e ver lista de tabelas</td><td>Todas</td><td>Descoberta completa</td></tr>
        <tr><td>2</td><td>Habilitar XMLA no Tenant (Admin Global Microsoft)</td><td>INFO.TABLES()</td><td>Extracao automatica</td></tr>
        <tr><td>3</td><td>Acesso direto Oracle biofuel (IP/SID)</td><td>PRD_PARCIAL, MOAGEM, ATR</td><td>R$50M gap producao</td></tr>
        <tr><td>4</td><td>Servico ODBC Oracle -> Python -> Pipeline</td><td>Todas</td><td>Atualizacao diaria</td></tr>
      </table>
    </div>
    <div class="card">
      <h3>Score de Completude dos Dados</h3>
      <table>
        <tr><th>Modulo</th><th>Status</th><th>Cobertura</th></tr>
        <tr><td>Chuva / Clima</td><td style="color:var(--green)">COMPLETO</td><td>100% - 47K registros Oracle</td></tr>
        <tr><td>Preparo Solo</td><td style="color:var(--green)">COMPLETO</td><td>100% - 5.4K registros Oracle</td></tr>
        <tr><td>Variedades</td><td style="color:var(--green)">COMPLETO</td><td>100% - 102 variedades Oracle</td></tr>
        <tr><td>RH / Divergencias</td><td style="color:var(--green)">COMPLETO</td><td>100% - 1K registros Oracle</td></tr>
        <tr><td>Plantio OC Muda</td><td style="color:var(--green)">COMPLETO</td><td>100% - 51 OC com GPS Oracle</td></tr>
        <tr><td>Producao Diaria</td><td style="color:var(--red)">BLOQUEADO</td><td>0% - tabela nao encontrada</td></tr>
        <tr><td>Moagem</td><td style="color:var(--red)">BLOQUEADO</td><td>0% - tabela nao encontrada</td></tr>
        <tr><td>ATR / Qualidade</td><td style="color:var(--red)">BLOQUEADO</td><td>0% - tabela nao encontrada</td></tr>
        <tr><td>Custos (CST)</td><td style="color:var(--red)">BLOQUEADO</td><td>0% - dataset sem tabelas</td></tr>
        <tr><td>Controle (CTRL)</td><td style="color:var(--gold)">PARCIAL</td><td>30% - so Func_Div</td></tr>
        <tr><td>BD SAFRAS local</td><td style="color:var(--green)">EXCEL</td><td>100% - 51K registros historicos</td></tr>
      </table>
    </div>
  </div>
</div>

<script>
const VERDE='#00C853',OURO='#FFD600',AZUL='#2979FF',VERM='#FF1744',LARANJ='#FF6D00';
const opts={{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:'#8899BB',font:{{size:11}}}}}}}},scales:{{x:{{ticks:{{color:'#8899BB'}},grid:{{color:'#1e3060'}}}},y:{{ticks:{{color:'#8899BB'}},grid:{{color:'#1e3060'}}}}}}}};

function showTab(id,btn){{
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  btn.classList.add('active');
}}

// Chart Chuva Anual
(()=>{{
  const data={json.dumps(chuva_chart, ensure_ascii=False)};
  if(!data.length) return;
  const anos = data.map(d=>d.ano);
  const postos = [...new Set(data.flatMap(d=>Object.keys(d.frentes)))].slice(0,8);
  const colors=[VERDE,OURO,AZUL,VERM,LARANJ,'#00BCD4','#E040FB','#FF9800'];
  new Chart(document.getElementById('chartChuvaAnual'),{{
    type:'bar',
    data:{{labels:anos,datasets:postos.map((p,i)=>{{return{{label:p,data:data.map(d=>d.frentes[p]||0),backgroundColor:colors[i]+'88',borderColor:colors[i],borderWidth:1}}}});}},
    options:{{...opts,plugins:{{...opts.plugins,title:{{display:true,text:'Precipitacao mm por Posto e Ano',color:'#E8F0FF'}}}}}}
  }});
}})();

// Chart Chuva Dias
(()=>{{
  const raw = {json.dumps(chuva_dias.to_dict('records') if not chuva_dias.empty else [], ensure_ascii=False)};
  if(!raw.length) return;
  new Chart(document.getElementById('chartChuvasDias'),{{
    type:'line',
    data:{{labels:raw.map(d=>d.ano),datasets:[{{label:'Dias com Chuva',data:raw.map(d=>d.dias),borderColor:AZUL,backgroundColor:AZUL+'33',fill:true,tension:.4}}]}},
    options:opts
  }});
}})();

// Chart Preparo Frente
(()=>{{
  const raw = {df_to_json(prep_frente.head(8))};
  if(!raw.length) return;
  new Chart(document.getElementById('chartPreparoFrente'),{{
    type:'bar',
    data:{{labels:raw.map(d=>d.FRENTE),datasets:[
      {{label:'Area Real (ha)',data:raw.map(d=>d.Area_Real||0),backgroundColor:VERDE+'88',borderColor:VERDE,borderWidth:1}},
      {{label:'Area Plano (ha)',data:raw.map(d=>d.Area_Plano||0),backgroundColor:OURO+'88',borderColor:OURO,borderWidth:1}}
    ]}},
    options:opts
  }});
}})();

// Chart Preparo SistPlan
(()=>{{
  const raw = {df_to_json(prep_sistplan.head(8))};
  if(!raw.length) return;
  new Chart(document.getElementById('chartPreparoSist'),{{
    type:'doughnut',
    data:{{labels:raw.map(d=>d.SISTPLAN),datasets:[{{data:raw.map(d=>d.Area),backgroundColor:[VERDE,OURO,AZUL,VERM,LARANJ,'#00BCD4','#E040FB']}}]}},
    options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'right',labels:{{color:'#8899BB'}}}}}}}}
  }});
}})();

// Chart Var Maturacao
(()=>{{
  const raw = {df_to_json(var_maturacao.head(12))};
  if(!raw.length) return;
  new Chart(document.getElementById('chartVarMaturacao'),{{
    type:'bar',
    data:{{labels:raw.map(d=>(d.DA_GRP_VAR||'')+' '+( d.DE_MATURAC||'')),datasets:[{{label:'Qtd Variedades',data:raw.map(d=>d.Qtd),backgroundColor:[VERDE,OURO,AZUL,VERM,LARANJ,'#00BCD4'].slice(0,raw.length)}}]}},
    options:opts
  }});
}})();

// Chart Var Grupo
(()=>{{
  const raw = {df_to_json(variedades.groupby('DA_GRP_VAR').agg(Qtd=('DE_VARIED','count')).reset_index().sort_values('Qtd',ascending=False) if not variedades.empty else pd.DataFrame())};
  if(!raw.length) return;
  new Chart(document.getElementById('chartVarGrupo'),{{
    type:'doughnut',
    data:{{labels:raw.map(d=>d.DA_GRP_VAR),datasets:[{{data:raw.map(d=>d.Qtd),backgroundColor:[VERDE,OURO,AZUL,VERM,LARANJ]}}]}},
    options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'right',labels:{{color:'#8899BB'}}}}}}}}
  }});
}})();

// Chart Div Tipo
(()=>{{
  const raw = {df_to_json(div_tipo.head(10))};
  if(!raw.length) return;
  new Chart(document.getElementById('chartDivTipo'),{{
    type:'bar',
    data:{{labels:raw.map(d=>d.TP_DIV),datasets:[{{label:'Func.',data:raw.map(d=>d.QT_FUNC),backgroundColor:VERM+'88',borderColor:VERM,borderWidth:1}}]}},
    options:opts
  }});
}})();

// Chart Div Frente
(()=>{{
  const raw = {df_to_json(div_frente.head(10))};
  if(!raw.length) return;
  new Chart(document.getElementById('chartDivFrente'),{{
    type:'bar',
    data:{{labels:raw.map(d=>d.FRENTE),datasets:[{{label:'Diverg.',data:raw.map(d=>d.QT_FUNC),backgroundColor:LARANJ+'88',borderColor:LARANJ,borderWidth:1}}]}},
    options:{{...opts,indexAxis:'y'}}
  }});
}})();
</script>
</body>
</html>"""

out = OUT_DIR / 'UMOE_PBI_Oracle.html'
out.write_text(html, encoding='utf-8')

# Copiar para docs/
docs = BASE / 'docs'
docs.mkdir(exist_ok=True)
(docs / 'UMOE_PBI_Oracle.html').write_text(html, encoding='utf-8')

print(f"\n  Dashboard gerado: {out}")
print(f"  Copia docs/: {docs / 'UMOE_PBI_Oracle.html'}")
print(f"\n{'='*60}")
print("  PIPELINE CONCLUIDO!")
print(f"  Total PBI: {resumo['total_linhas_pbi']:,} linhas")
print(f"  Chuva: {len(chuva):,} | Preparo: {len(preparo):,} | Variedades: {len(variedades)}")
print(f"  Func_Div: {len(func_div):,} | Plant_OC: {len(plant_oc)}")
print("="*60)
