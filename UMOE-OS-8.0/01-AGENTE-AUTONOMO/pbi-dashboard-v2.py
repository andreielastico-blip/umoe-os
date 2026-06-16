# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 - Pipeline BI Agricola - Dashboard HTML Executivo
Dados: 95 tabelas extraidas dos datasets BASE / CST / CTRL do Power BI
Safra 2026/27 | Gerado automaticamente
"""
import json, os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / 'Dados-PBI'
OUT_FILE = DATA_DIR.parent / 'Relatorios' / 'UMOE_PBI_Dashboard.html'
OUT_FILE.parent.mkdir(exist_ok=True)

TODAY = '2026-06-15'

# ── Helpers ─────────────────────────────────────────────────────────────────

def load(fn):
    fp = DATA_DIR / fn
    if not fp.exists():
        return []
    raw = fp.read_bytes()
    data = json.loads(raw.decode('utf-8-sig'))
    if isinstance(data, list):
        cleaned = []
        for row in data:
            cleaned.append({
                (k.split('[')[-1].rstrip(']') if '[' in k else k): v
                for k, v in row.items()
            })
        return cleaned
    return []

def fmtN(v, dec=0):
    if v is None: return '-'
    try:
        v = float(v)
        if dec == 0: return f'{v:,.0f}'.replace(',', '.')
        return f'{v:,.{dec}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return str(v)

def fmtR(v):
    if v is None: return '-'
    try:
        v = float(v)
        return f'R$ {v:,.0f}'.replace(',', '.')
    except: return str(v)

# ── Load data ────────────────────────────────────────────────────────────────
print('Carregando dados...')

ctt_histprd       = load('BASE_CTT_HISTPRD.json')
ctt_histprd_atr   = load('BASE_CTT_HISTPRD_ATR_HIST.json')
ctt_tch           = load('BASE_CTT_TCH.json')
ctt_tah           = load('BASE_CTT_TAH.json')
ctt_meta_moagem   = load('BASE_CTT_META_MOAGEM.json')
ctt_dthrfren      = load('BASE_CTT_DTHRFREN.json')
ctt_maturador     = load('BASE_CTT_MATURADOR.json')
ctt_ordemcorte    = load('BASE_CTT_ORDEMCORTE.json')
ctt_pre_analise   = load('BASE_CTT_PRE_ANALISE.json')
ctt_indisponib    = load('BASE_CTT_INDISPONIB.json')
ctt_cargas_ent    = load('BASE_CTT_CARGAS_ENTRADA.json')

cst_cst           = load('CST_CST.json')
cst_func          = load('CST_FUNC_10_FUNC.json')
cst_ccusto        = load('CST_FUNC_10_CCUSTO.json')
cst_afast         = load('CST_FUNC_10_AFAST.json')
cst_func_99       = load('CST_FUNC_99_BI.json')

ctrl_orc          = load('CTRL_CST_ORCAMENTO.json')
ctrl_estoq        = load('CTRL_CTRL_ESTOQ_SALDO.json')

insumo_consumo    = load('BASE_INSUMO_CONSUMO.json')
insumo_estoq      = load('BASE_INSUMO_SLD_ESTOQ.json')

agro_broca        = load('BASE_INSETIC_BROCA.json')
agro_cigarrinha   = load('BASE_AGRO_CIGARRINHA.json')
agro_migdolus     = load('BASE_AGRO_MIGDOLUS.json')
chuva             = load('BASE_Chuva.json')

preparo           = load('BASE_Preparo.json')
plant_real        = load('BASE_PLANT_REAL.json')
plant_meta        = load('BASE_PLANT_META.json')
variedades        = load('BASE_Variedades.json')
func_div          = load('CTRL_Func_Div.json')

print(f'  HISTPRD:{len(ctt_histprd)} ATR_HIST:{len(ctt_histprd_atr)} CST:{len(cst_cst)} FUNC:{len(cst_func)}')

# ── Aggregations ─────────────────────────────────────────────────────────────

# Producao 2026
prod26 = [r for r in ctt_histprd if str(r.get('DT_HISTORICO',''))[:4] == '2026']
tot_ton_26 = sum(float(r.get('QT_CANA_ENT') or 0) for r in prod26)
tot_atr_kg_26 = sum(float(r.get('KG_ACUCAR') or 0) for r in prod26)
atr_med_26 = (tot_atr_kg_26 / tot_ton_26) if tot_ton_26 > 0 else 0

prod_mensal = defaultdict(lambda: {'ton': 0, 'atr': 0})
for r in prod26:
    mes = str(r.get('DT_HISTORICO',''))[:7]
    prod_mensal[mes]['ton'] += float(r.get('QT_CANA_ENT') or 0)
    prod_mensal[mes]['atr'] += float(r.get('KG_ACUCAR') or 0)

prod_frente = defaultdict(lambda: {'ton': 0, 'atr': 0})
for r in prod26:
    f = r.get('CD_FREN_TRAN', '?')
    prod_frente[f]['ton'] += float(r.get('QT_CANA_ENT') or 0)
    prod_frente[f]['atr'] += float(r.get('KG_ACUCAR') or 0)

# ATR historico por safra
atr_safra = defaultdict(lambda: {'ton': 0, 'atr': 0})
for r in ctt_histprd_atr:
    yr = str(r.get('DT_HISTORICO',''))[:4]
    if yr >= '2023':
        atr_safra[yr]['ton'] += float(r.get('QT_CANA_ENT') or 0)
        atr_safra[yr]['atr'] += float(r.get('KG_ACUCAR') or 0)

# TCH por estagio 26/27
tch_estagio = defaultdict(lambda: {'area': 0, 'prd': 0, 'n': 0})
for r in ctt_tch:
    if str(r.get('CD_SAFRA','')) == '22627':
        est = r.get('ESTAGIO_AGRUP') or r.get('ESTAGIO', 'N/A')
        tch_estagio[est]['area'] += float(r.get('AREA_ESTIMADA') or 0)
        tch_estagio[est]['prd']  += float(r.get('PRD_ESTIMADA') or 0)
        tch_estagio[est]['n']    += 1

# Custos 2026
cst_cc = defaultdict(lambda: {'orc': 0, 'real': 0})
cst_grp = defaultdict(lambda: {'orc': 0, 'real': 0})
for r in cst_cst:
    if str(r.get('DT_REFER',''))[:4] == '2026':
        cc = r.get('DE_CCUSTO','N/A')
        g  = r.get('DE_GRUPO','N/A')
        o  = float(r.get('VL_ORC') or 0)
        re = float(r.get('VL_REAL') or 0)
        cst_cc[cc]['orc']  += o;  cst_cc[cc]['real']  += re
        cst_grp[g]['orc']  += o;  cst_grp[g]['real']  += re

top_cst  = sorted(cst_cc.items(),  key=lambda x: x[1]['real'], reverse=True)[:12]
top_grp  = sorted(cst_grp.items(), key=lambda x: x[1]['real'], reverse=True)[:10]
tot_orc_2026  = sum(v['orc']  for v in cst_cc.values())
tot_real_2026 = sum(v['real'] for v in cst_cc.values())

# RH
mes_atual = '2026-06'
func_ativos = [r for r in cst_func
               if str(r.get('MESINI',''))[:7] == mes_atual
               and (not r.get('DAT_DESLIGTO_FUNC') or str(r.get('DAT_DESLIGTO_FUNC'))[:4] == '9999')]
headcount = len(func_ativos)
dias_afast = sum(float(r.get('DIAS_AFAST') or 0)
                 for r in cst_afast if str(r.get('MESINI',''))[:7] == mes_atual)

hc_cc = defaultdict(int)
for r in cst_ccusto:
    if str(r.get('MESINI',''))[:7] == mes_atual:
        hc_cc[r.get('DESC_CCUSTO','?')] += 1

# Insumos
ins_grupo = defaultdict(float)
ins_det   = defaultdict(lambda: {'qt': 0, 'n': 0})
for r in insumo_consumo:
    if str(r.get('DTSEMANA',''))[:4] == '2026':
        g    = r.get('DE_GRUPO','?')
        nome = (r.get('DE_COMPO') or r.get('DE_RECURSO','?'))[:40]
        qt   = float(r.get('QT_REAL') or 0)
        ins_grupo[g] += qt
        ins_det[nome]['qt'] += qt
        ins_det[nome]['n']  += 1

# Agronomia
broca_faz = defaultdict(lambda: {'n': 0, 'pct': 0})
for r in agro_broca:
    faz = (r.get('DE_UPNIVEL1') or str(r.get('CD_UPNIVEL1','?')))[:40]
    broca_faz[faz]['n']   += 1
    broca_faz[faz]['pct'] += float(r.get('PCT_INFEST') or r.get('INFEST') or 0)

cig_mensal = defaultdict(int)
for r in agro_cigarrinha:
    m = str(r.get('SEMANA') or r.get('DT_AVALIACAO') or '')[:7]
    cig_mensal[m] += 1

chuva_mensal = defaultdict(float)
for r in chuva:
    if str(r.get('ANO','')) in ('2025','2026'):
        m = f"{r.get('ANO','')}-{str(r.get('AGRUP_MES','')).zfill(2)}"
        chuva_mensal[m] += float(r.get('QTDE') or 0)

# Plantio
plant_tot_real = sum(float(r.get('QT_AREA') or r.get('AREA_REAL') or 0) for r in plant_real)
plant_tot_meta = sum(float(r.get('QT_AREA') or r.get('AREA') or 0) for r in plant_meta)

oc_estagio = defaultdict(lambda: {'area': 0, 'n': 0})
for r in ctt_ordemcorte:
    corte = r.get('NO_CORTE', 0)
    est = f'{int(corte) if corte else 0}C'
    oc_estagio[est]['area'] += float(r.get('AREA_PRD') or 0)
    oc_estagio[est]['n']    += 1

# Parametros SSoT
META_MOAGEM = 2_768_000
MOAGEM_ACUM = 606_418
GAP_MOAGEM  = META_MOAGEM - MOAGEM_ACUM
ATR_META    = 138.66
ATR_REAL    = float(atr_med_26) if atr_med_26 else 126.49
CCT_REAL    = 50.0
CCT_ORC     = 38.3

print('Calculado. Gerando HTML...')

# ── CSS / JS ─────────────────────────────────────────────────────────────────
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Arial,sans-serif;background:#1a1a2e;color:#e0e0e0;font-size:13px}
h1{color:#00d4aa;font-size:22px;padding:18px 24px 6px}
h2{color:#00d4aa;font-size:15px;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid #333}
h3{color:#7ecfd4;font-size:13px;margin:14px 0 8px}
.tabs{display:flex;gap:2px;padding:0 24px;flex-wrap:wrap;margin-bottom:2px}
.tab{padding:7px 14px;cursor:pointer;background:#16213e;color:#888;border-radius:6px 6px 0 0;font-size:12px;transition:.15s}
.tab:hover{color:#ccc}
.tab.active{background:#0f3460;color:#00d4aa;font-weight:600}
.content{display:none;padding:18px 24px}
.content.active{display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;margin-bottom:16px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
.kpi{background:#16213e;border-radius:8px;padding:14px;border-left:3px solid #00d4aa}
.kpi .val{font-size:24px;font-weight:700;color:#00d4aa}
.kpi .lbl{font-size:11px;color:#888;margin-top:3px}
.kpi .sub{font-size:11px;color:#bbb;margin-top:3px}
.kpi.r{border-left-color:#e74c3c}.kpi.r .val{color:#e74c3c}
.kpi.y{border-left-color:#f39c12}.kpi.y .val{color:#f39c12}
.kpi.g{border-left-color:#27ae60}.kpi.g .val{color:#27ae60}
.card{background:#16213e;border-radius:8px;padding:14px;margin-bottom:14px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#0f3460;color:#00d4aa;padding:7px 9px;text-align:left;position:sticky;top:0;z-index:1}
td{padding:5px 9px;border-bottom:1px solid #222}
tr:hover td{background:#1e2d50}
.tw{max-height:350px;overflow-y:auto;border-radius:6px;border:1px solid #333}
.red{color:#e74c3c}.green{color:#27ae60}.yellow{color:#f39c12}
.alert{background:#2d1b1b;border-left:4px solid #e74c3c;padding:10px 14px;border-radius:0 6px 6px 0;margin-bottom:12px;font-size:12px}
.bbar{background:#333;border-radius:3px;height:7px;width:100%;margin-top:5px}
.bf{height:7px;border-radius:3px}
.sub{color:#888;font-size:12px;padding:0 24px 12px}
"""

JS = """
function showTab(id,el){
  document.querySelectorAll('.content').forEach(c=>c.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  el.classList.add('active');
}
"""

# ── Tab builders ──────────────────────────────────────────────────────────────

def tab_cockpit():
    gap_pct = MOAGEM_ACUM / META_MOAGEM * 100
    ac = 'r' if gap_pct < 80 else 'y'
    atr_c = 'r' if ATR_REAL < ATR_META * 0.95 else 'y' if ATR_REAL < ATR_META else 'g'
    cct_c = 'r' if CCT_REAL > CCT_ORC * 1.1 else 'y'

    rows_m = ''
    for m in sorted(prod_mensal):
        ton = prod_mensal[m]['ton']
        atr = prod_mensal[m]['atr']
        a   = atr / ton if ton > 0 else 0
        rows_m += f'<tr><td>{m}</td><td>{fmtN(ton)}</td><td>{fmtN(a,2)}</td></tr>'

    rows_f = ''
    for f, v in sorted(prod_frente.items(), key=lambda x: x[1]['ton'], reverse=True):
        a = v['atr'] / v['ton'] if v['ton'] > 0 else 0
        rows_f += f'<tr><td>Frente {f}</td><td>{fmtN(v["ton"])}</td><td>{fmtN(a,2)}</td></tr>'

    desvio_cct = CCT_REAL - CCT_ORC
    atr_gap    = ATR_REAL - ATR_META

    return f"""
<div class="grid">
  <div class="kpi {ac}">
    <div class="val">{fmtN(MOAGEM_ACUM)}</div>
    <div class="lbl">Moagem Acumulada (t)</div>
    <div class="sub">Meta: {fmtN(META_MOAGEM)} t</div>
    <div class="bbar"><div class="bf" style="width:{gap_pct:.1f}%;background:#f39c12"></div></div>
  </div>
  <div class="kpi r"><div class="val">{fmtN(GAP_MOAGEM)}</div><div class="lbl">Gap Moagem (t)</div><div class="sub">-R$ 50,78 M impacto</div></div>
  <div class="kpi {atr_c}"><div class="val">{fmtN(ATR_REAL,2)}</div><div class="lbl">ATR Real (kg/t)</div><div class="sub">Meta {ATR_META} | Gap {fmtN(atr_gap,2)}</div></div>
  <div class="kpi {cct_c}"><div class="val">R${CCT_REAL}/t</div><div class="lbl">CCT Real</div><div class="sub">Orc R${CCT_ORC}/t | +R${desvio_cct:.1f}/t</div></div>
  <div class="kpi"><div class="val">{fmtN(tot_ton_26)}</div><div class="lbl">Ton 2026 (HISTPRD)</div></div>
  <div class="kpi"><div class="val">{headcount}</div><div class="lbl">Headcount Jun/26</div></div>
  <div class="kpi"><div class="val">{len(set(r.get('DE_CCUSTO') for r in cst_cst))}</div><div class="lbl">Centros de Custo</div></div>
  <div class="kpi"><div class="val">{len(agro_broca)}</div><div class="lbl">Aval. Broca</div></div>
</div>
<div class="alert">
  <b>ALERTA SAFRA 2026/27:</b>
  Gap moagem {fmtN(GAP_MOAGEM)} t (89% volume / 11% custo).
  ATR {fmtN(ATR_REAL,2)} kg/t vs meta {ATR_META} kg/t ({atr_gap:+.2f}).
  CCT R$ {CCT_REAL}/t vs orc R$ {CCT_ORC}/t ({((CCT_REAL/CCT_ORC)-1)*100:+.1f}%).
  Dias afastamento Jun/26: {fmtN(dias_afast)}.
</div>
<div class="g2">
  <div class="card">
    <h3>Producao Mensal 2026</h3>
    <div class="tw"><table><thead><tr><th>Mes</th><th>Ton</th><th>ATR kg/t</th></tr></thead><tbody>{rows_m}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Producao por Frente 2026</h3>
    <div class="tw"><table><thead><tr><th>Frente</th><th>Ton</th><th>ATR kg/t</th></tr></thead><tbody>{rows_f}</tbody></table></div>
  </div>
</div>
"""

def tab_producao():
    faz_prod = defaultdict(lambda: {'ton': 0, 'n': 0})
    for r in prod26:
        faz = r.get('CD_UPNIVEL1','?')
        faz_prod[faz]['ton'] += float(r.get('QT_CANA_ENT') or 0)
        faz_prod[faz]['n']   += 1
    top_faz = sorted(faz_prod.items(), key=lambda x: x[1]['ton'], reverse=True)[:20]

    rows_est = ''.join(
        f'<tr><td>{e}</td><td>{v["n"]}</td><td>{fmtN(v["area"],0)}</td>'
        f'<td class="{"r" if (v["prd"]/v["area"] if v["area"] else 0)<70 else "y" if (v["prd"]/v["area"] if v["area"] else 0)<90 else "green"}">'
        f'{fmtN(v["prd"]/v["area"] if v["area"] else 0,1)}</td></tr>'
        for e, v in sorted(tch_estagio.items())
    )

    rows_faz = ''.join(
        f'<tr><td style="font-size:11px">{faz[:45]}</td><td>{fmtN(v["ton"])}</td><td>{v["n"]}</td></tr>'
        for faz, v in top_faz
    )

    indisp_tp = defaultdict(lambda: {'hrs': 0, 'n': 0})
    for r in ctt_indisponib:
        tp = (r.get('DE_CAUSA') or r.get('TP_CAUSA','?'))[:35]
        indisp_tp[tp]['hrs'] += float(r.get('QT_HRS') or r.get('HORAS') or 0)
        indisp_tp[tp]['n']   += 1
    rows_ind = ''.join(
        f'<tr><td>{t}</td><td>{fmtN(v["hrs"],1)}</td><td>{v["n"]}</td></tr>'
        for t, v in sorted(indisp_tp.items(), key=lambda x: x[1]['hrs'], reverse=True)[:10]
    )

    cargas_f = defaultdict(lambda: {'ton': 0, 'n': 0})
    for r in ctt_cargas_ent:
        f = r.get('CD_FREN_TRAN', r.get('FRENTE','?'))
        cargas_f[f]['n']   += 1
        cargas_f[f]['ton'] += float(r.get('QT_CANA') or r.get('TON') or 0)
    rows_cg = ''.join(
        f'<tr><td>Frente {f}</td><td>{fmtN(v["ton"])}</td><td>{v["n"]}</td></tr>'
        for f, v in sorted(cargas_f.items(), key=lambda x: x[1]['ton'], reverse=True)[:10]
    )

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{fmtN(tot_ton_26)}</div><div class="lbl">Ton Moidas 2026</div></div>
  <div class="kpi"><div class="val">{len(set(r.get('CD_UPNIVEL1') for r in prod26))}</div><div class="lbl">Fazendas Ativas</div></div>
  <div class="kpi"><div class="val">{len(ctt_cargas_ent)}</div><div class="lbl">Cargas Registradas</div></div>
  <div class="kpi"><div class="val">{len(ctt_indisponib)}</div><div class="lbl">Reg. Indisponibilidade</div></div>
</div>
<div class="g3">
  <div class="card">
    <h3>TCH Estimado por Estagio (26/27)</h3>
    <div class="tw"><table><thead><tr><th>Estagio</th><th>Talhoes</th><th>Area ha</th><th>TCH</th></tr></thead><tbody>{rows_est}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Top 20 Fazendas - Ton 2026</h3>
    <div class="tw"><table><thead><tr><th>Fazenda</th><th>Ton</th><th>Dias</th></tr></thead><tbody>{rows_faz}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Indisponibilidade por Causa</h3>
    <div class="tw"><table><thead><tr><th>Causa</th><th>Horas</th><th>Ocorr.</th></tr></thead><tbody>{rows_ind}</tbody></table></div>
  </div>
</div>
<div class="card">
  <h3>Cargas por Frente</h3>
  <table><thead><tr><th>Frente</th><th>Ton</th><th>Cargas</th></tr></thead><tbody>{rows_cg}</tbody></table>
</div>
"""

def tab_atr():
    rows_safra = ''
    for yr, v in sorted(atr_safra.items()):
        a = v['atr'] / v['ton'] if v['ton'] > 0 else 0
        c = 'r' if a < 125 else 'y' if a < 135 else 'green'
        rows_safra += f'<tr><td>{yr}</td><td>{fmtN(v["ton"])}</td><td class="{c}">{fmtN(a,2)}</td></tr>'

    atr_sem = defaultdict(lambda: {'ton': 0, 'atr': 0})
    for r in ctt_histprd_atr:
        if str(r.get('DT_HISTORICO',''))[:4] == '2026':
            d = str(r.get('DT_HISTORICO',''))[:10]
            atr_sem[d]['ton'] += float(r.get('QT_CANA_ENT') or 0)
            atr_sem[d]['atr'] += float(r.get('KG_ACUCAR') or 0)
    rows_sem = ''
    for dt, v in sorted(atr_sem.items())[-30:]:
        a = v['atr'] / v['ton'] if v['ton'] > 0 else 0
        c = 'r' if a < 125 else 'y' if a < 135 else 'green'
        rows_sem += f'<tr><td>{dt}</td><td>{fmtN(v["ton"])}</td><td class="{c}">{fmtN(a,2)}</td></tr>'

    mat_f = defaultdict(int)
    for r in ctt_maturador:
        mat_f[r.get('CD_FREN_TRAN','?')] += 1
    rows_mat = ''.join(f'<tr><td>Frente {f}</td><td>{n}</td></tr>' for f, n in sorted(mat_f.items()))

    pre_cols = list(ctt_pre_analise[0].keys())[:7] if ctt_pre_analise else []
    hdrs_pre = ''.join(f'<th>{c}</th>' for c in pre_cols)
    rows_pre = ''.join(
        '<tr>' + ''.join(f'<td>{str(r.get(c,""))[:20]}</td>' for c in pre_cols) + '</tr>'
        for r in ctt_pre_analise[:25]
    )

    return f"""
<div class="grid">
  <div class="kpi y"><div class="val">{fmtN(ATR_REAL,2)}</div><div class="lbl">ATR Real 2026 (kg/t)</div><div class="sub">Meta {ATR_META} kg/t</div></div>
  <div class="kpi"><div class="val">{len(ctt_histprd_atr)}</div><div class="lbl">Registros ATR Historico</div></div>
  <div class="kpi"><div class="val">{len(ctt_maturador)}</div><div class="lbl">Registros Maturador</div></div>
  <div class="kpi"><div class="val">{len(ctt_pre_analise)}</div><div class="lbl">Pre-Analises</div></div>
</div>
<div class="g3">
  <div class="card">
    <h3>ATR por Safra (2023-2026)</h3>
    <table><thead><tr><th>Safra</th><th>Ton</th><th>ATR kg/t</th></tr></thead><tbody>{rows_safra}</tbody></table>
  </div>
  <div class="card">
    <h3>ATR Diario 2026 (ultimos 30)</h3>
    <div class="tw"><table><thead><tr><th>Data</th><th>Ton</th><th>ATR kg/t</th></tr></thead><tbody>{rows_sem}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Maturador por Frente</h3>
    <table><thead><tr><th>Frente</th><th>Aplicacoes</th></tr></thead><tbody>{rows_mat}</tbody></table>
  </div>
</div>
<div class="card">
  <h3>Pre-Analise ATR</h3>
  <div class="tw"><table><thead><tr>{hdrs_pre}</tr></thead><tbody>{rows_pre}</tbody></table></div>
</div>
"""

def tab_custos():
    rows_cc = ''.join(
        f'<tr><td>{cc[:35]}</td><td>{fmtR(v["orc"])}</td><td>{fmtR(v["real"])}</td>'
        f'<td class="{"r" if v["real"]>v["orc"] else "green"}">{fmtR(v["real"]-v["orc"])}</td></tr>'
        for cc, v in top_cst
    )
    rows_grp = ''.join(
        f'<tr><td>{g[:30]}</td><td>{fmtR(v["orc"])}</td><td>{fmtR(v["real"])}</td>'
        f'<td class="{"r" if v["real"]>v["orc"] else "green"}">{fmtR(v["real"]-v["orc"])}</td></tr>'
        for g, v in top_grp
    )
    rows_orc = ''.join(
        f'<tr><td>{r.get("DE_GRUPO","")[:35]}</td><td>{r.get("TP","")}</td>'
        f'<td>{fmtR(r.get("VLR_YTD"))}</td><td>{fmtR(r.get("VLR_YTD_R"))}</td></tr>'
        for r in ctrl_orc[:25]
    )
    desvio = tot_real_2026 - tot_orc_2026

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{fmtR(tot_orc_2026)}</div><div class="lbl">Total Orcado 2026</div></div>
  <div class="kpi {"r" if desvio>0 else "g"}"><div class="val">{fmtR(tot_real_2026)}</div><div class="lbl">Total Realizado 2026</div></div>
  <div class="kpi {"r" if desvio>0 else "g"}"><div class="val">{fmtR(desvio)}</div><div class="lbl">Desvio</div></div>
  <div class="kpi"><div class="val">{len(cst_cc)}</div><div class="lbl">Centros de Custo</div></div>
</div>
<div class="g2">
  <div class="card">
    <h3>Top 12 CC - Realizado 2026</h3>
    <div class="tw"><table><thead><tr><th>Centro de Custo</th><th>Orcado</th><th>Realizado</th><th>Desvio</th></tr></thead><tbody>{rows_cc}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Top 10 Grupos de Custo 2026</h3>
    <div class="tw"><table><thead><tr><th>Grupo</th><th>Orcado</th><th>Realizado</th><th>Desvio</th></tr></thead><tbody>{rows_grp}</tbody></table></div>
  </div>
</div>
<div class="card">
  <h3>Orcamento vs Realizado YTD (CTRL)</h3>
  <div class="tw"><table><thead><tr><th>Grupo</th><th>Tipo</th><th>Vlr Orc YTD</th><th>Vlr Real YTD</th></tr></thead><tbody>{rows_orc}</tbody></table></div>
</div>
"""

def tab_rh():
    rows_hc  = ''.join(f'<tr><td>{cc[:40]}</td><td>{n}</td></tr>'
                       for cc, n in sorted(hc_cc.items(), key=lambda x: x[1], reverse=True)[:12])

    afast_tp = defaultdict(lambda: {'n': 0, 'dias': 0})
    for r in cst_afast:
        if str(r.get('MESINI',''))[:7] == mes_atual:
            tp = (r.get('MOTIVO') or r.get('TP_AFASTAMENTO') or r.get('DE_MOTIVO','?'))[:35]
            afast_tp[tp]['n']    += 1
            afast_tp[tp]['dias'] += float(r.get('DIAS_AFAST') or 0)
    rows_af = ''.join(
        f'<tr><td>{t}</td><td>{v["n"]}</td><td>{fmtN(v["dias"])}</td></tr>'
        for t, v in sorted(afast_tp.items(), key=lambda x: x[1]['dias'], reverse=True)[:12]
    )

    div_setor = defaultdict(int)
    for r in func_div:
        div_setor[(r.get('SETOR') or r.get('DE_SETOR','?'))[:40]] += 1
    rows_div = ''.join(f'<tr><td>{s}</td><td>{n}</td></tr>'
                       for s, n in sorted(div_setor.items(), key=lambda x: x[1], reverse=True)[:15])

    f99_cols = list(cst_func_99[0].keys())[:6] if cst_func_99 else []
    rows_f99 = ''.join(
        '<tr>' + ''.join(f'<td>{str(r.get(c,""))[:25]}</td>' for c in f99_cols) + '</tr>'
        for r in cst_func_99[:30]
    )
    hdrs_f99 = ''.join(f'<th>{c}</th>' for c in f99_cols)

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{headcount}</div><div class="lbl">Headcount Ativo Jun/26</div></div>
  <div class="kpi y"><div class="val">{fmtN(dias_afast)}</div><div class="lbl">Dias Afastamento Jun/26</div></div>
  <div class="kpi"><div class="val">{len(cst_func)}</div><div class="lbl">Historico Func</div></div>
  <div class="kpi"><div class="val">{len(func_div)}</div><div class="lbl">Func Div (CTRL)</div></div>
</div>
<div class="g3">
  <div class="card">
    <h3>Headcount por CC (Jun/26)</h3>
    <div class="tw"><table><thead><tr><th>Centro de Custo</th><th>Qtd</th></tr></thead><tbody>{rows_hc}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Afastamentos Jun/26</h3>
    <div class="tw"><table><thead><tr><th>Motivo</th><th>Func.</th><th>Dias</th></tr></thead><tbody>{rows_af}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Divisao por Setor</h3>
    <div class="tw"><table><thead><tr><th>Setor</th><th>Qtd</th></tr></thead><tbody>{rows_div}</tbody></table></div>
  </div>
</div>
<div class="card">
  <h3>FUNC_99_BI - Quadro RH Completo (amostra 30)</h3>
  <div class="tw"><table><thead><tr>{hdrs_f99}</tr></thead><tbody>{rows_f99}</tbody></table></div>
</div>
"""

def tab_insumos():
    rows_grp = ''.join(
        f'<tr><td>{g[:40]}</td><td>{fmtN(v,1)}</td></tr>'
        for g, v in sorted(ins_grupo.items(), key=lambda x: x[1], reverse=True)[:15]
    )
    rows_det = ''.join(
        f'<tr><td>{n}</td><td>{fmtN(v["qt"],1)}</td><td>{v["n"]}</td></tr>'
        for n, v in sorted(ins_det.items(), key=lambda x: x[1]['qt'], reverse=True)[:15]
    )
    estoq_cols = list(ctrl_estoq[0].keys())[:6] if ctrl_estoq else []
    rows_estoq = ''.join(
        '<tr>' + ''.join(f'<td>{str(r.get(c,""))[:25]}</td>' for c in estoq_cols) + '</tr>'
        for r in ctrl_estoq[:25]
    )
    hdrs_estoq = ''.join(f'<th>{c}</th>' for c in estoq_cols)

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{len(insumo_consumo)}</div><div class="lbl">Registros Consumo 2026</div></div>
  <div class="kpi"><div class="val">{len(insumo_estoq)}</div><div class="lbl">Registros Estoque</div></div>
  <div class="kpi"><div class="val">{len(ctrl_estoq)}</div><div class="lbl">Saldo CTRL</div></div>
</div>
<div class="g3">
  <div class="card">
    <h3>Consumo por Grupo 2026</h3>
    <div class="tw"><table><thead><tr><th>Grupo</th><th>Qtd</th></tr></thead><tbody>{rows_grp}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Top Componentes 2026</h3>
    <div class="tw"><table><thead><tr><th>Componente</th><th>Qtd</th><th>Reg</th></tr></thead><tbody>{rows_det}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Estoque Saldo (CTRL)</h3>
    <div class="tw"><table><thead><tr>{hdrs_estoq}</tr></thead><tbody>{rows_estoq}</tbody></table></div>
  </div>
</div>
"""

def tab_agronomia():
    rows_chuva = ''.join(
        f'<tr><td>{m}</td><td class="{"r" if v<50 else "y" if v<100 else "green"}">{fmtN(v,1)}</td></tr>'
        for m, v in sorted(chuva_mensal.items())[-24:]
    )
    top_broca = sorted(broca_faz.items(), key=lambda x: x[1]['pct']/max(1,x[1]['n']), reverse=True)[:15]
    rows_br = ''.join(
        f'<tr><td>{faz}</td><td>{v["n"]}</td><td>{fmtN(v["pct"]/v["n"],2)}%</td></tr>'
        for faz, v in top_broca
    )
    rows_cig = ''.join(f'<tr><td>{m}</td><td>{n}</td></tr>'
                       for m, n in sorted(cig_mensal.items())[-18:])
    mig_faz = defaultdict(int)
    for r in agro_migdolus:
        mig_faz[(r.get('DE_UPNIVEL1') or str(r.get('CD_UPNIVEL1','?')))[:40]] += 1
    rows_mig = ''.join(f'<tr><td>{faz}</td><td>{n}</td></tr>'
                       for faz, n in sorted(mig_faz.items(), key=lambda x: x[1], reverse=True)[:10])

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{len(chuva)}</div><div class="lbl">Registros Chuva</div></div>
  <div class="kpi r"><div class="val">{len(agro_broca)}</div><div class="lbl">Aval. Broca</div></div>
  <div class="kpi y"><div class="val">{len(agro_cigarrinha)}</div><div class="lbl">Aval. Cigarrinha</div></div>
  <div class="kpi"><div class="val">{len(agro_migdolus)}</div><div class="lbl">Aval. Migdolus</div></div>
</div>
<div class="g3">
  <div class="card">
    <h3>Chuva Mensal (mm acum postos)</h3>
    <div class="tw"><table><thead><tr><th>Mes</th><th>mm</th></tr></thead><tbody>{rows_chuva}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Broca - Top Fazendas (% infest.)</h3>
    <div class="tw"><table><thead><tr><th>Fazenda</th><th>Aval</th><th>% Infest</th></tr></thead><tbody>{rows_br}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Cigarrinha Mensal</h3>
    <div class="tw"><table><thead><tr><th>Mes</th><th>Ocorr.</th></tr></thead><tbody>{rows_cig}</tbody></table></div>
  </div>
</div>
<div class="card">
  <h3>Migdolus por Fazenda</h3>
  <table><thead><tr><th>Fazenda</th><th>Registros</th></tr></thead><tbody>{rows_mig}</tbody></table>
</div>
"""

def tab_plantio():
    plant_mes = defaultdict(lambda: {'area': 0, 'n': 0})
    for r in plant_real:
        m = str(r.get('DT_PLANTIO') or r.get('DT_REAL') or '')[:7]
        if m >= '2026':
            plant_mes[m]['area'] += float(r.get('QT_AREA') or r.get('AREA_REAL') or 0)
            plant_mes[m]['n']    += 1
    rows_pm = ''.join(f'<tr><td>{m}</td><td>{fmtN(v["area"],1)}</td><td>{v["n"]}</td></tr>'
                      for m, v in sorted(plant_mes.items()))

    rows_oc = ''.join(
        f'<tr><td>{e}</td><td>{v["n"]}</td><td>{fmtN(v["area"],1)}</td></tr>'
        for e, v in sorted(oc_estagio.items(), key=lambda x: int(x[0][:-1]) if x[0][:-1].isdigit() else 99)
    )

    prep_tp = defaultdict(lambda: {'area': 0, 'n': 0})
    for r in preparo:
        tp = (r.get('ROTACAO') or r.get('TIPO_PREPARO','?'))[:35]
        prep_tp[tp]['area'] += float(r.get('QT_AREA_REAL') or 0)
        prep_tp[tp]['n']    += 1
    rows_prep = ''.join(
        f'<tr><td>{tp}</td><td>{v["n"]}</td><td>{fmtN(v["area"],1)}</td></tr>'
        for tp, v in sorted(prep_tp.items(), key=lambda x: x[1]['area'], reverse=True)[:12]
    )

    rows_var = ''.join(
        f'<tr><td>{r.get("CD_VARIED","")}</td><td>{r.get("DE_VARIED","")}</td><td>{r.get("DE_MATURAC","")}</td></tr>'
        for r in variedades[:25]
    )

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{fmtN(plant_tot_real,0)}</div><div class="lbl">Area Plantio Real (ha)</div></div>
  <div class="kpi"><div class="val">{fmtN(plant_tot_meta,0)}</div><div class="lbl">Meta Plantio (ha)</div></div>
  <div class="kpi"><div class="val">{len(ctt_ordemcorte)}</div><div class="lbl">Talhoes Ordem Corte</div></div>
  <div class="kpi"><div class="val">{len(preparo)}</div><div class="lbl">Registros Preparo</div></div>
</div>
<div class="g3">
  <div class="card">
    <h3>Plantio Real 2026 por Mes</h3>
    <table><thead><tr><th>Mes</th><th>Area ha</th><th>Reg</th></tr></thead><tbody>{rows_pm}</tbody></table>
  </div>
  <div class="card">
    <h3>Ordem de Corte por Estagio</h3>
    <table><thead><tr><th>Estagio</th><th>Talhoes</th><th>Area ha</th></tr></thead><tbody>{rows_oc}</tbody></table>
  </div>
  <div class="card">
    <h3>Preparo de Solo por Tipo</h3>
    <div class="tw"><table><thead><tr><th>Tipo</th><th>Talhoes</th><th>Area ha</th></tr></thead><tbody>{rows_prep}</tbody></table></div>
  </div>
</div>
<div class="card">
  <h3>Variedades</h3>
  <table><thead><tr><th>Codigo</th><th>Variedade</th><th>Maturacao</th></tr></thead><tbody>{rows_var}</tbody></table>
</div>
"""

# ── Montar HTML ───────────────────────────────────────────────────────────────
print('Montando HTML...')
tabs_defs = [
    ('cockpit',   'Cockpit',   tab_cockpit),
    ('producao',  'Producao',  tab_producao),
    ('atr',       'ATR/Qual.', tab_atr),
    ('custos',    'Custos',    tab_custos),
    ('rh',        'RH',        tab_rh),
    ('insumos',   'Insumos',   tab_insumos),
    ('agronomia', 'Agronomia', tab_agronomia),
    ('plantio',   'Plantio',   tab_plantio),
]

tab_nav = ''.join(
    f'<div class="tab {"active" if i==0 else ""}" onclick="showTab(\'{id}\',this)">{lbl}</div>'
    for i, (id, lbl, _) in enumerate(tabs_defs)
)
tab_content = ''.join(
    f'<div id="tab-{id}" class="content {"active" if i==0 else ""}"><h2>{lbl}</h2>{fn()}</div>'
    for i, (id, lbl, fn) in enumerate(tabs_defs)
)

total_linhas = (len(ctt_histprd) + len(ctt_histprd_atr) + len(cst_cst) +
                len(cst_func) + len(insumo_consumo) + len(ctt_cargas_ent))

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>UMOE OS 8.0 | Dashboard BI Agricola 2026/27</title>
<style>{CSS}</style>
</head>
<body>
<h1>UMOE OS 8.0 | Dashboard BI Agricola</h1>
<p class="sub">Safra 2026/27 | {TODAY} | BASE+CST+CTRL: 95 tabelas / {fmtN(total_linhas)} registros principais</p>
<div class="tabs">{tab_nav}</div>
{tab_content}
<script>{JS}</script>
</body>
</html>"""

OUT_FILE.write_text(html, encoding='utf-8')
kb = OUT_FILE.stat().st_size // 1024
print(f'Dashboard salvo: {OUT_FILE}')
print(f'Tamanho: {kb} KB')
