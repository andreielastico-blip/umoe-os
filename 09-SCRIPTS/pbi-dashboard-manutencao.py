# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 - Dashboard Manutencao Premium
45 tabelas reais extraidas do workspace Projetos Manutencao PREMIUM
"""
import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / 'UMOE-OS-8.0' / 'Dados-PBI' / 'MANUT'
OUT_FILE = Path(__file__).parent.parent / 'UMOE-OS-8.0' / 'Relatorios' / 'UMOE_Dashboard_Manutencao.html'
OUT_FILE.parent.mkdir(exist_ok=True)

TODAY = '2026-06-16'

# ── Helpers ──────────────────────────────────────────────────────────────────

def load(stem):
    fp = DATA_DIR / f'{stem}.json'
    if not fp.exists() or fp.stat().st_size < 50:
        return []
    try:
        data = json.loads(fp.read_bytes().decode('utf-8-sig'))
        if not isinstance(data, list) or not data:
            return []
        return [{
            (k.split('[')[-1].rstrip(']') if '[' in k else k): v
            for k, v in row.items()
        } for row in data]
    except:
        return []

def fN(v, dec=0):
    if v is None: return '-'
    try:
        v = float(v)
        if dec > 0:
            s = f'{v:,.{dec}f}'
            return s.replace(',','X').replace('.',',').replace('X','.')
        return f'{v:,.0f}'.replace(',','.')
    except: return str(v)

def fR(v):
    if v is None: return '-'
    try: return f'R$ {float(v):,.0f}'.replace(',','.')
    except: return str(v)

def find_col(data, *names):
    if not data: return None
    row = data[0]
    for n in names:
        for k in row.keys():
            if n.lower() in k.lower():
                return k
    return None

def tbl_html(data, cols=None, max_rows=50):
    if not data: return '<p style="color:#888">Sem dados</p>'
    cols = cols or list(data[0].keys())[:8]
    hdrs = ''.join(f'<th>{c}</th>' for c in cols)
    rows = ''
    for r in data[:max_rows]:
        rows += '<tr>' + ''.join(f'<td>{str(r.get(c,""))[:28]}</td>' for c in cols) + '</tr>'
    return f'<div class="tw"><table><thead><tr>{hdrs}</tr></thead><tbody>{rows}</tbody></table></div>'

# ── Carregar tabelas principais ───────────────────────────────────────────────
print('Carregando dados...')

# Fatos manutencao
manfro   = load('umoe_dataset_f_manfro')
afast    = load('umoe_dataset_f_abastecimento')
lubri    = load('umoe_dataset_f_lubrificante')
produt   = load('umoe_dataset_f_produtividade')
tch      = load('umoe_dataset_f_tch')
req      = load('umoe_dataset_f_requisicao')
oc       = load('umoe_dataset_f_ordem_compra')
receb    = load('umoe_dataset_f_recebimento')
pend     = load('umoe_dataset_f_pend_aprov')

# Dim equipamentos e disponibilidade
equip    = load('umoe_dataset_d_equipamentos')
equip_s  = load('umoe_dataset_d_equipamentos_sistema')
disp_eq  = load('umoe_dataset_d_disponibilidade_eqp_data')
d_meta_e = load('umoe_dataset_d_meta_equipamentos')
d_meta_f = load('umoe_dataset_d_meta_frente')
d_meta_u = load('umoe_dataset_d_meta_unidade')
crit_dm  = load('umoe_dataset_d_criterio_disponibilidade')

# Orcamentos / custos
orc_r    = load('umoe_dataset_d_orcamento_reais')
orc_d    = load('umoe_dataset_d_orcamento_diesel')
orc_kmh  = load('umoe_dataset_d_orcamento_km_h')
orc_eq   = load('umoe_dataset_d_orcamento_equipamentos')
preco    = load('umoe_dataset_d_preco_unit')
ajustes  = load('umoe_dataset_ajustes_consumos')

# Itens / pecas
itens    = load('umoe_dataset_d_item')
recurso  = load('umoe_dataset_d_recurso_eqp')

# Pessoal e logistica
func     = load('umoe_dataset_d_funcionario')
transp   = load('umoe_dataset_d_transportadoras')
aprovad  = load('umoe_dataset_d_aprovadores')
comprad  = load('umoe_dataset_d_compradores')
emiten   = load('umoe_dataset_d_emitente')
sit_oc   = load('umoe_dataset_d_situacao_oc')
sit_req  = load('umoe_dataset_d_situacao_req')

# OS abertas
os_campo = load('Ordem_de_Servicos_Abertas_Interna_Campo_Base_O_S')
os_trans = load('Ordem_de_Servicos_Abertas_Interna_Campo_Transporte_Base_O_S')
forneced = load('Ordem_de_Servicos_Abertas_Interna_Campo_Tabela_Fornecedores')

# Paretos e materiais
paretos  = load('PARETOS_PROCESSOS_Paretos')
peq_par  = load('PARETOS_PROCESSOS_d_equipamento')
materiais= load('Materiais_Aplicados___Por_Equipamento_Materiais_Aplicados')

# Catalogo
catalogo = {}
cat_fp = DATA_DIR / 'MANUT_CATALOGO.json'
if cat_fp.exists():
    catalogo = json.loads(cat_fp.read_bytes().decode('utf-8-sig'))

ws_nome    = catalogo.get('workspace', {}).get('name', 'Manutencao Premium')
n_datasets = len(catalogo.get('datasets', []))
n_reports  = len(catalogo.get('reports', []))

# Todas as tabelas com dados
inventario = {
    'f_manfro':             manfro,
    'f_abastecimento':      afast,
    'f_lubrificante':       lubri,
    'f_produtividade':      produt,
    'f_tch':                tch,
    'f_requisicao':         req,
    'f_ordem_compra':       oc,
    'f_recebimento':        receb,
    'f_pend_aprov':         pend,
    'd_equipamentos':       equip,
    'd_disponibilidade':    disp_eq,
    'd_orcamento_reais':    orc_r,
    'd_orcamento_diesel':   orc_d,
    'd_item (pecas)':       itens,
    'd_funcionario':        func,
    'OS_campo':             os_campo,
    'OS_transporte':        os_trans,
    'Paretos':              paretos,
    'Materiais_Aplicados':  materiais,
}
inventario = {k: v for k, v in inventario.items() if v}
total_rows = sum(len(v) for v in inventario.values())

print(f'Tabelas carregadas: {len(inventario)} | Total registros: {total_rows:,}')

# ── KPIs globais ─────────────────────────────────────────────────────────────

# OS total
os_all   = os_campo + os_trans
os_total = len(os_all)
col_st   = find_col(os_campo, 'STATUS', 'SITUAC', 'ESTAT')
os_ab    = len([r for r in os_campo if col_st and 'ABER' in str(r.get(col_st,'')).upper()])
os_fe    = len([r for r in os_campo if col_st and 'FECH' in str(r.get(col_st,'')).upper()])

# DM medio
col_dm_v  = find_col(disp_eq, 'DM', 'DISPONIB', 'PERC_DM', 'PCT')
dm_vals   = [float(r.get(col_dm_v,0) or 0) for r in disp_eq if col_dm_v and r.get(col_dm_v)] if col_dm_v else []
dm_medio  = sum(dm_vals)/len(dm_vals) if dm_vals else 0

col_mtbf  = find_col(disp_eq, 'MTBF')
col_mttr  = find_col(disp_eq, 'MTTR')
mtbf_med  = (sum(float(r.get(col_mtbf,0) or 0) for r in disp_eq)/max(1,len(disp_eq))) if col_mtbf and disp_eq else 0
mttr_med  = (sum(float(r.get(col_mttr,0) or 0) for r in disp_eq)/max(1,len(disp_eq))) if col_mttr and disp_eq else 0

# Custo orcado vs realizado
col_orc_v  = find_col(orc_r, 'ORC', 'BUDGET', 'PLANEJ', 'VL_ORC')
col_real_v = find_col(orc_r, 'REAL', 'REALIZ', 'VL_REAL')
orc_tot    = sum(float(r.get(col_orc_v,0) or 0) for r in orc_r) if col_orc_v else 0
real_tot   = sum(float(r.get(col_real_v,0) or 0) for r in orc_r) if col_real_v else 0

# Paretos top causas
col_causa  = find_col(paretos, 'CAUSA', 'DESC', 'FALHA', 'DE_')
col_hrs_p  = find_col(paretos, 'HRS', 'HORA', 'TEMPO', 'PARADA')
col_occ_p  = find_col(paretos, 'QTDE', 'QT', 'NR', 'OCORR')
pareto_agg = defaultdict(lambda: {'n': 0, 'hrs': 0})
for r in paretos:
    tp = str(r.get(col_causa,'?'))[:45] if col_causa else '?'
    pareto_agg[tp]['n']   += 1
    try: pareto_agg[tp]['hrs'] += float(r.get(col_hrs_p,0) or 0) if col_hrs_p else 0
    except: pass

# Abastecimento / diesel
col_vol   = find_col(afast, 'VOL', 'LT', 'LITRO', 'QUANT')
col_vlr_a = find_col(afast, 'VL', 'VALOR', 'CUSTO', 'R$')
vol_tot   = sum(float(r.get(col_vol,0) or 0) for r in afast) if col_vol and afast else 0
vlr_afast = sum(float(r.get(col_vlr_a,0) or 0) for r in afast) if col_vlr_a and afast else 0

# Materiais aplicados
col_vlr_m  = find_col(materiais, 'VL', 'VALOR', 'CUSTO', 'PRECO', 'TOTAL')
vlr_mat    = sum(float(r.get(col_vlr_m,0) or 0) for r in materiais) if col_vlr_m and materiais else 0

# ── CSS / JS ─────────────────────────────────────────────────────────────────
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Arial,sans-serif;background:#0d1b2a;color:#e0e0e0;font-size:13px}
h1{color:#f0a500;font-size:22px;padding:18px 24px 6px}
h2{color:#f0a500;font-size:15px;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid #333}
h3{color:#ffc947;font-size:13px;margin:12px 0 7px}
.tabs{display:flex;gap:2px;padding:0 24px;flex-wrap:wrap}
.tab{padding:7px 14px;cursor:pointer;background:#162033;color:#888;border-radius:6px 6px 0 0;font-size:12px;transition:.15s}
.tab:hover{color:#ccc}
.tab.active{background:#1a3a5c;color:#f0a500;font-weight:600}
.content{display:none;padding:18px 24px}
.content.active{display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;margin-bottom:16px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
.kpi{background:#162033;border-radius:8px;padding:14px;border-left:3px solid #f0a500}
.kpi .val{font-size:22px;font-weight:700;color:#f0a500}
.kpi .lbl{font-size:11px;color:#888;margin-top:3px}
.kpi .sub{font-size:11px;color:#bbb;margin-top:3px}
.kpi.r{border-left-color:#e74c3c}.kpi.r .val{color:#e74c3c}
.kpi.y{border-left-color:#f39c12}.kpi.y .val{color:#f39c12}
.kpi.g{border-left-color:#27ae60}.kpi.g .val{color:#27ae60}
.kpi.b{border-left-color:#3498db}.kpi.b .val{color:#3498db}
.card{background:#162033;border-radius:8px;padding:14px;margin-bottom:14px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#1a3a5c;color:#f0a500;padding:7px 9px;text-align:left;position:sticky;top:0;z-index:1}
td{padding:5px 9px;border-bottom:1px solid #222}
tr:hover td{background:#1e3050}
.tw{max-height:380px;overflow-y:auto;border-radius:6px;border:1px solid #333}
.red{color:#e74c3c}.green{color:#27ae60}.yellow{color:#f39c12}
.alert{background:#2d1b00;border-left:4px solid #f0a500;padding:10px 14px;border-radius:0 6px 6px 0;margin-bottom:12px;font-size:12px}
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

# ── Abas ─────────────────────────────────────────────────────────────────────

def tab_cockpit():
    dm_c = 'r' if dm_medio < 0.85 else 'y' if dm_medio < 0.90 else 'g'
    ds_rows = ''.join(f'<tr><td>{d.get("name","")}</td><td style="font-size:11px;color:#888">{d.get("id","")}</td></tr>'
                      for d in catalogo.get('datasets',[]))
    inv_rows = ''.join(
        f'<tr><td>{k}</td><td style="text-align:right">{len(v):,}</td><td style="font-size:11px;color:#888">{", ".join(list(v[0].keys())[:4]) if v else ""}</td></tr>'
        for k, v in sorted(inventario.items(), key=lambda x: len(x[1]), reverse=True)
    )
    dev = real_tot - orc_tot
    dev_c = 'r' if dev > 0 else 'g'
    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{len(inventario)}</div><div class="lbl">Tabelas com Dados</div><div class="sub">{fN(total_rows)} registros</div></div>
  <div class="kpi {('r' if os_ab > 50 else 'y' if os_ab > 20 else 'g')}"><div class="val">{os_ab}</div><div class="lbl">OS Abertas</div><div class="sub">Total: {os_total}</div></div>
  <div class="kpi {dm_c}"><div class="val">{fN(dm_medio*100,1)}%</div><div class="lbl">DM Medio</div><div class="sub">Meta: 90%</div>
    <div class="bbar"><div class="bf" style="width:{min(100,dm_medio*100):.1f}%;background:{'#27ae60' if dm_medio>=0.90 else '#f39c12' if dm_medio>=0.85 else '#e74c3c'}"></div></div>
  </div>
  <div class="kpi b"><div class="val">{fN(mtbf_med,1)}h</div><div class="lbl">MTBF Medio</div></div>
  <div class="kpi y"><div class="val">{fN(mttr_med,2)}h</div><div class="lbl">MTTR Medio</div></div>
  <div class="kpi"><div class="val">{len(paretos):,}</div><div class="lbl">Registros Pareto</div></div>
  <div class="kpi {dev_c}"><div class="val">{fR(dev)}</div><div class="lbl">Desvio Orcamento</div><div class="sub">Orc: {fR(orc_tot)} | Real: {fR(real_tot)}</div></div>
  <div class="kpi"><div class="val">{fN(vol_tot,0)} L</div><div class="lbl">Diesel Total</div><div class="sub">{fR(vlr_afast)}</div></div>
  <div class="kpi"><div class="val">{fR(vlr_mat)}</div><div class="lbl">Materiais Aplicados</div></div>
</div>
<div class="alert">
  <b>WORKSPACE: {ws_nome}</b> | Extraido: {TODAY} | {n_datasets} datasets | {n_reports} reports |
  {len(inventario)} tabelas | {fN(total_rows)} registros
</div>
<div class="g2">
  <div class="card">
    <h3>Datasets do Workspace</h3>
    <table><thead><tr><th>Nome</th><th>ID</th></tr></thead><tbody>{ds_rows}</tbody></table>
  </div>
  <div class="card">
    <h3>Inventario de Tabelas</h3>
    <div class="tw"><table><thead><tr><th>Tabela</th><th>Linhas</th><th>Colunas</th></tr></thead><tbody>{inv_rows}</tbody></table></div>
  </div>
</div>
"""

def tab_manfro():
    if not manfro:
        return '<div class="card"><p style="color:#888;padding:20px">f_manfro nao carregada</p></div>'
    cols = list(manfro[0].keys())
    col_eq  = find_col(manfro, 'EQUIP', 'NR_EQUIP', 'CD_', 'MAQUINA')
    col_tp  = find_col(manfro, 'TIPO', 'TP_', 'CAT', 'OS', 'ATIV')
    col_hrs = find_col(manfro, 'HRS', 'HR_', 'HORA', 'TEMPO')
    col_dt  = find_col(manfro, 'DT_', 'DATA', 'DATE')

    # Agrupamento por tipo
    tp_agg = defaultdict(lambda: {'n': 0, 'hrs': 0})
    for r in manfro:
        tp = str(r.get(col_tp,'?'))[:40] if col_tp else '?'
        tp_agg[tp]['n']   += 1
        tp_agg[tp]['hrs'] += float(r.get(col_hrs,0) or 0) if col_hrs else 0
    rows_tp = ''.join(
        f'<tr><td>{tp}</td><td style="text-align:right">{v["n"]:,}</td><td style="text-align:right">{fN(v["hrs"],1)}</td></tr>'
        for tp, v in sorted(tp_agg.items(), key=lambda x: x[1]['hrs'], reverse=True)[:15]
    )

    # Por equipamento (top 20 por horas)
    eq_agg = defaultdict(lambda: {'n': 0, 'hrs': 0})
    for r in manfro:
        eq = str(r.get(col_eq,'?'))[:25] if col_eq else '?'
        eq_agg[eq]['n']   += 1
        eq_agg[eq]['hrs'] += float(r.get(col_hrs,0) or 0) if col_hrs else 0
    rows_eq = ''.join(
        f'<tr><td>{eq}</td><td style="text-align:right">{v["n"]:,}</td><td style="text-align:right">{fN(v["hrs"],1)}</td></tr>'
        for eq, v in sorted(eq_agg.items(), key=lambda x: x[1]['hrs'], reverse=True)[:20]
    )

    tot_hrs = sum(float(r.get(col_hrs,0) or 0) for r in manfro) if col_hrs else 0

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{len(manfro):,}</div><div class="lbl">Registros f_manfro</div></div>
  <div class="kpi y"><div class="val">{fN(tot_hrs,0)}h</div><div class="lbl">Total Horas</div></div>
  <div class="kpi"><div class="val">{len(tp_agg)}</div><div class="lbl">Tipos de Atividade</div></div>
  <div class="kpi"><div class="val">{len(eq_agg)}</div><div class="lbl">Equipamentos</div></div>
</div>
<div class="g2">
  <div class="card">
    <h3>Por Tipo de Atividade (Top 15 - horas)</h3>
    <div class="tw"><table><thead><tr><th>Tipo</th><th>Qtd</th><th>Horas</th></tr></thead><tbody>{rows_tp}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Por Equipamento (Top 20 - horas)</h3>
    <div class="tw"><table><thead><tr><th>Equipamento</th><th>Qtd</th><th>Horas</th></tr></thead><tbody>{rows_eq}</tbody></table></div>
  </div>
</div>
<div class="card">
  <h3>f_manfro - Detalhe (50 registros)</h3>
  {tbl_html(manfro, cols[:9], 50)}
</div>
"""

def tab_os():
    os_data = os_campo + os_trans
    if not os_data:
        return '<div class="card"><p style="color:#888;padding:20px">OS nao encontradas</p></div>'

    cols_c = list(os_campo[0].keys()) if os_campo else []
    cols_t = list(os_trans[0].keys()) if os_trans else []

    col_tp  = find_col(os_campo, 'TIPO', 'TP_OS', 'CAT', 'MANUT', 'ATIV')
    col_eq  = find_col(os_campo, 'EQUIP', 'MAQUINA', 'FROTA', 'NR_', 'CD_')
    col_sit = find_col(os_campo, 'STATUS', 'SITUAC', 'ESTAT', 'SIT')
    col_pr  = find_col(os_campo, 'PRIORIDADE', 'PRIOR', 'URGENT', 'CRITICA')

    # Por tipo
    tp_cnt = defaultdict(int)
    sit_cnt = defaultdict(int)
    eq_cnt  = defaultdict(int)
    for r in os_campo:
        tp  = str(r.get(col_tp,'?'))[:40] if col_tp else '?'
        sit = str(r.get(col_sit,'?'))[:30] if col_sit else '?'
        eq  = str(r.get(col_eq,'?'))[:25] if col_eq else '?'
        tp_cnt[tp]   += 1
        sit_cnt[sit] += 1
        eq_cnt[eq]   += 1

    rows_tp  = ''.join(f'<tr><td>{tp}</td><td style="text-align:right">{n:,}</td></tr>' for tp, n in sorted(tp_cnt.items(), key=lambda x: x[1], reverse=True)[:12])
    rows_sit = ''.join(f'<tr><td>{s}</td><td style="text-align:right">{n:,}</td></tr>' for s, n in sorted(sit_cnt.items(), key=lambda x: x[1], reverse=True)[:10])
    rows_eq  = ''.join(f'<tr><td>{eq}</td><td style="text-align:right">{n:,}</td></tr>' for eq, n in sorted(eq_cnt.items(), key=lambda x: x[1], reverse=True)[:15])

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{len(os_campo):,}</div><div class="lbl">OS Campo</div></div>
  <div class="kpi"><div class="val">{len(os_trans):,}</div><div class="lbl">OS Transporte</div></div>
  <div class="kpi {'r' if os_ab>20 else 'y'}"><div class="val">{os_ab}</div><div class="lbl">Abertas</div></div>
  <div class="kpi g"><div class="val">{os_fe}</div><div class="lbl">Fechadas</div></div>
  <div class="kpi"><div class="val">{len(tp_cnt)}</div><div class="lbl">Tipos</div></div>
  <div class="kpi"><div class="val">{len(forneced):,}</div><div class="lbl">Fornecedores</div></div>
</div>
<div class="g3">
  <div class="card">
    <h3>Por Tipo</h3>
    <div class="tw"><table><thead><tr><th>Tipo OS</th><th>Qtd</th></tr></thead><tbody>{rows_tp}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Por Situacao</h3>
    <div class="tw"><table><thead><tr><th>Situacao</th><th>Qtd</th></tr></thead><tbody>{rows_sit}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Top Equipamentos</h3>
    <div class="tw"><table><thead><tr><th>Equipamento</th><th>OS</th></tr></thead><tbody>{rows_eq}</tbody></table></div>
  </div>
</div>
<div class="g2">
  <div class="card">
    <h3>OS Campo ({len(os_campo):,} registros)</h3>
    {tbl_html(os_campo, cols_c[:9], 40)}
  </div>
  <div class="card">
    <h3>OS Transporte ({len(os_trans):,} registros)</h3>
    {tbl_html(os_trans, cols_t[:9], 40)}
  </div>
</div>
"""

def tab_pareto():
    if not paretos:
        return '<div class="card"><p style="color:#888;padding:20px">Paretos nao encontrados</p></div>'
    top = sorted(pareto_agg.items(), key=lambda x: x[1]['hrs'], reverse=True)[:20]
    tot_p = sum(v['hrs'] for v in pareto_agg.values())
    rows_p = ''
    acum = 0
    for tp, v in top:
        acum += v['hrs']
        pct   = v['hrs']/tot_p*100 if tot_p else 0
        pct_a = acum/tot_p*100 if tot_p else 0
        c = 'red' if pct_a <= 80 else 'yellow' if pct_a <= 95 else ''
        rows_p += f'<tr><td class="{c}">{tp}</td><td style="text-align:right">{v["n"]:,}</td><td style="text-align:right">{fN(v["hrs"],1)}</td><td style="text-align:right">{fN(pct,1)}%</td><td style="text-align:right">{fN(pct_a,1)}%</td></tr>'

    cols_par = list(paretos[0].keys())[:9]
    return f"""
<div class="grid">
  <div class="kpi r"><div class="val">{len(paretos):,}</div><div class="lbl">Registros Pareto</div></div>
  <div class="kpi"><div class="val">{len(pareto_agg)}</div><div class="lbl">Causas Distintas</div></div>
  <div class="kpi y"><div class="val">{fN(tot_p,0)}h</div><div class="lbl">Total Horas Parada</div></div>
  <div class="kpi"><div class="val">{len(peq_par):,}</div><div class="lbl">Equipamentos Pareto</div></div>
</div>
<div class="card">
  <h3>Pareto de Falhas - Top 20 por Horas (legenda: vermelho=80% das horas)</h3>
  <div class="tw">
    <table><thead><tr><th>Causa</th><th>Ocorr.</th><th>Horas</th><th>%</th><th>%Acum</th></tr></thead>
    <tbody>{rows_p}</tbody></table>
  </div>
</div>
<div class="card">
  <h3>Paretos - Todos os registros ({len(paretos):,})</h3>
  {tbl_html(paretos, cols_par, 50)}
</div>
"""

def tab_disponibilidade():
    if not disp_eq:
        return '<div class="card"><p style="color:#888;padding:20px">d_disponibilidade_eqp_data nao carregada</p></div>'
    cols_d = list(disp_eq[0].keys())[:9]

    col_eq_d = find_col(disp_eq, 'EQUIP', 'NR_', 'CD_', 'DESC', 'NOME')
    col_dt_d = find_col(disp_eq, 'DT_', 'DATA', 'MES', 'ANO')
    col_hd   = find_col(disp_eq, 'HD', 'HORAS_DISP', 'HRS_DISP', 'HR_DISP')
    col_hm   = find_col(disp_eq, 'HM', 'HORAS_MAN', 'HRS_MAN', 'MANUT')

    # DM por equipamento (media)
    eq_dm = defaultdict(lambda: {'dm': [], 'mtbf': [], 'mttr': []})
    for r in disp_eq:
        eq = str(r.get(col_eq_d,'?'))[:25] if col_eq_d else '?'
        if col_dm_v and r.get(col_dm_v):
            eq_dm[eq]['dm'].append(float(r.get(col_dm_v,0) or 0))
        if col_mtbf and r.get(col_mtbf):
            eq_dm[eq]['mtbf'].append(float(r.get(col_mtbf,0) or 0))
        if col_mttr and r.get(col_mttr):
            eq_dm[eq]['mttr'].append(float(r.get(col_mttr,0) or 0))

    rows_eq = ''
    for eq, v in sorted(eq_dm.items(), key=lambda x: sum(x[1]['dm'])/max(1,len(x[1]['dm'])) if x[1]['dm'] else 0)[:25]:
        dm  = sum(v['dm'])/len(v['dm']) if v['dm'] else 0
        mbf = sum(v['mtbf'])/len(v['mtbf']) if v['mtbf'] else 0
        mtr = sum(v['mttr'])/len(v['mttr']) if v['mttr'] else 0
        c   = 'red' if dm < 0.85 else 'yellow' if dm < 0.90 else 'green'
        rows_eq += f'<tr><td>{eq}</td><td class="{c}">{fN(dm*100,1)}%</td><td>{fN(mbf,1)}</td><td>{fN(mtr,2)}</td></tr>'

    return f"""
<div class="grid">
  <div class="kpi {'r' if dm_medio<0.85 else 'y' if dm_medio<0.90 else 'g'}">
    <div class="val">{fN(dm_medio*100,1)}%</div><div class="lbl">DM Medio Frota</div><div class="sub">Meta: 90%</div>
    <div class="bbar"><div class="bf" style="width:{min(100,dm_medio*100):.1f}%;background:{'#27ae60' if dm_medio>=0.90 else '#f39c12' if dm_medio>=0.85 else '#e74c3c'}"></div></div>
  </div>
  <div class="kpi b"><div class="val">{fN(mtbf_med,1)}h</div><div class="lbl">MTBF Medio</div><div class="sub">Meta: 90%DM</div></div>
  <div class="kpi y"><div class="val">{fN(mttr_med,2)}h</div><div class="lbl">MTTR Medio</div></div>
  <div class="kpi"><div class="val">{len(disp_eq):,}</div><div class="lbl">Registros</div></div>
  <div class="kpi"><div class="val">{len(eq_dm)}</div><div class="lbl">Equipamentos</div></div>
</div>
<div class="g2">
  <div class="card">
    <h3>DM por Equipamento (menor DM primeiro)</h3>
    <div class="tw"><table><thead><tr><th>Equipamento</th><th>DM%</th><th>MTBF(h)</th><th>MTTR(h)</th></tr></thead><tbody>{rows_eq}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Disponibilidade - Detalhe ({len(disp_eq):,} registros)</h3>
    {tbl_html(disp_eq, cols_d, 50)}
  </div>
</div>
"""

def tab_orcamento():
    def bloco(titulo, data, icon=''):
        if not data: return f'<div class="card"><h3>{titulo}</h3><p style="color:#888">Sem dados</p></div>'
        col_o = find_col(data, 'ORC', 'BUDGET', 'PLANEJ', 'VL_ORC')
        col_r = find_col(data, 'REAL', 'REALIZ', 'VL_REAL', 'VALOR')
        col_g = find_col(data, 'GRUPO', 'CC', 'CENTRO', 'CAT', 'DESC', 'DE_')
        grp   = defaultdict(lambda: {'o': 0, 'r': 0})
        for row in data:
            g = str(row.get(col_g,'?'))[:40] if col_g else '?'
            grp[g]['o'] += float(row.get(col_o,0) or 0) if col_o else 0
            grp[g]['r'] += float(row.get(col_r,0) or 0) if col_r else 0
        top = sorted(grp.items(), key=lambda x: x[1]['r'], reverse=True)[:12]
        tot_o = sum(v['o'] for v in grp.values())
        tot_r = sum(v['r'] for v in grp.values())
        rows  = ''
        for g, v in top:
            dev = v['r'] - v['o']
            c   = 'red' if dev > 0 else 'green'
            rows += f'<tr><td>{g}</td><td style="text-align:right">{fR(v["o"])}</td><td style="text-align:right">{fR(v["r"])}</td><td class="{c}" style="text-align:right">{fR(dev)}</td></tr>'
        dev_tot = tot_r - tot_o
        return f"""
<div class="card">
  <h3>{icon} {titulo} — Orc: {fR(tot_o)} | Real: {fR(tot_r)} | Desvio: <span class="{'red' if dev_tot>0 else 'green'}">{fR(dev_tot)}</span></h3>
  <div class="tw"><table><thead><tr><th>Grupo</th><th>Orcado</th><th>Realizado</th><th>Desvio</th></tr></thead><tbody>{rows}</tbody></table></div>
</div>"""

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{fR(orc_tot)}</div><div class="lbl">Total Orcado (R$)</div></div>
  <div class="kpi {'r' if real_tot>orc_tot else 'g'}"><div class="val">{fR(real_tot)}</div><div class="lbl">Total Realizado</div></div>
  <div class="kpi {'r' if real_tot>orc_tot else 'g'}"><div class="val">{fR(real_tot-orc_tot)}</div><div class="lbl">Desvio</div><div class="sub">{'ACIMA do orcamento' if real_tot>orc_tot else 'ABAIXO do orcamento'}</div></div>
  <div class="kpi"><div class="val">{len(orc_r):,}</div><div class="lbl">Linhas Orc. Reais</div></div>
  <div class="kpi"><div class="val">{len(orc_d):,}</div><div class="lbl">Linhas Orc. Diesel</div></div>
</div>
{bloco('Orcamento Reais', orc_r, 'R$')}
{bloco('Orcamento Diesel (L)', orc_d, '⛽')}
{bloco('Orcamento Km/h', orc_kmh, '🚜')}
"""

def tab_diesel():
    if not afast:
        return '<div class="card"><p style="color:#888;padding:20px">f_abastecimento nao carregada</p></div>'
    cols_a = list(afast[0].keys())[:9]
    col_eq_a  = find_col(afast, 'EQUIP', 'NR_', 'CD_', 'MAQUINA')
    col_dt_a  = find_col(afast, 'DT_', 'DATA', 'DATE')
    col_tp_a  = find_col(afast, 'TIPO', 'PRODUTO', 'COMB', 'LUBRIF')

    eq_vol = defaultdict(lambda: {'vol': 0, 'vlr': 0, 'n': 0})
    for r in afast:
        eq = str(r.get(col_eq_a,'?'))[:25] if col_eq_a else '?'
        eq_vol[eq]['vol'] += float(r.get(col_vol,0) or 0) if col_vol else 0
        eq_vol[eq]['vlr'] += float(r.get(col_vlr_a,0) or 0) if col_vlr_a else 0
        eq_vol[eq]['n']   += 1

    rows_eq = ''.join(
        f'<tr><td>{eq}</td><td style="text-align:right">{fN(v["vol"],0)}</td><td style="text-align:right">{fR(v["vlr"])}</td><td style="text-align:right">{v["n"]}</td></tr>'
        for eq, v in sorted(eq_vol.items(), key=lambda x: x[1]['vol'], reverse=True)[:20]
    )
    tp_vol = defaultdict(float)
    for r in afast:
        tp = str(r.get(col_tp_a,'?'))[:30] if col_tp_a else '?'
        tp_vol[tp] += float(r.get(col_vol,0) or 0) if col_vol else 0
    rows_tp = ''.join(f'<tr><td>{tp}</td><td style="text-align:right">{fN(v,0)} L</td></tr>' for tp, v in sorted(tp_vol.items(), key=lambda x: x[1], reverse=True)[:12])

    # Lubrificante
    lubri_rows = tbl_html(lubri, list(lubri[0].keys())[:8] if lubri else [], 30)

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{len(afast):,}</div><div class="lbl">Abastecimentos</div></div>
  <div class="kpi y"><div class="val">{fN(vol_tot,0)} L</div><div class="lbl">Volume Total Diesel</div></div>
  <div class="kpi"><div class="val">{fR(vlr_afast)}</div><div class="lbl">Valor Total</div></div>
  <div class="kpi"><div class="val">{len(lubri):,}</div><div class="lbl">Registros Lubrificante</div></div>
  <div class="kpi"><div class="val">{len(eq_vol)}</div><div class="lbl">Equipamentos</div></div>
</div>
<div class="g2">
  <div class="card">
    <h3>Abastecimento por Equipamento (Top 20 - volume)</h3>
    <div class="tw"><table><thead><tr><th>Equipamento</th><th>Volume (L)</th><th>Valor</th><th>Qt</th></tr></thead><tbody>{rows_eq}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Por Tipo de Produto</h3>
    <div class="tw"><table><thead><tr><th>Tipo</th><th>Volume</th></tr></thead><tbody>{rows_tp}</tbody></table></div>
  </div>
</div>
<div class="card">
  <h3>Lubrificantes ({len(lubri):,} registros)</h3>
  {lubri_rows}
</div>
"""

def tab_materiais():
    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{len(materiais):,}</div><div class="lbl">Materiais Aplicados</div></div>
  <div class="kpi"><div class="val">{fR(vlr_mat)}</div><div class="lbl">Valor Total</div></div>
  <div class="kpi"><div class="val">{len(itens):,}</div><div class="lbl">Itens Cadastrados</div></div>
  <div class="kpi"><div class="val">{len(req):,}</div><div class="lbl">Requisicoes</div></div>
  <div class="kpi"><div class="val">{len(oc):,}</div><div class="lbl">Ordens de Compra</div></div>
  <div class="kpi"><div class="val">{len(receb):,}</div><div class="lbl">Recebimentos</div></div>
</div>
<div class="g2">
  <div class="card">
    <h3>Materiais Aplicados ({len(materiais):,} registros)</h3>
    {tbl_html(materiais, list(materiais[0].keys())[:8] if materiais else [], 40)}
  </div>
  <div class="card">
    <h3>Itens Cadastrados ({len(itens):,})</h3>
    {tbl_html(itens, list(itens[0].keys())[:7] if itens else [], 40)}
  </div>
</div>
<div class="g2">
  <div class="card">
    <h3>Requisicoes ({len(req):,})</h3>
    {tbl_html(req, list(req[0].keys())[:8] if req else [], 30)}
  </div>
  <div class="card">
    <h3>Ordens de Compra ({len(oc):,})</h3>
    {tbl_html(oc, list(oc[0].keys())[:8] if oc else [], 30)}
  </div>
</div>
"""

def tab_all():
    todas = {
        'f_manfro': manfro, 'f_abastecimento': afast, 'f_lubrificante': lubri,
        'f_produtividade': produt, 'f_tch': tch, 'f_requisicao': req,
        'f_ordem_compra': oc, 'f_recebimento': receb, 'f_pend_aprov': pend,
        'd_equipamentos': equip, 'd_disponibilidade': disp_eq,
        'd_orcamento_reais': orc_r, 'd_orcamento_diesel': orc_d,
        'd_orcamento_kmh': orc_kmh, 'd_orcamento_eqp': orc_eq,
        'd_item': itens, 'd_funcionario': func, 'd_recurso_eqp': recurso,
        'd_meta_equip': d_meta_e, 'd_meta_frente': d_meta_f,
        'd_meta_unidade': d_meta_u, 'd_criterio_dm': crit_dm,
        'd_emitente': emiten, 'd_aprovadores': aprovad, 'd_compradores': comprad,
        'd_transportadoras': transp, 'd_sit_oc': sit_oc, 'd_sit_req': sit_req,
        'd_preco_unit': preco, 'ajustes_consumos': ajustes,
        'OS_campo': os_campo, 'OS_transporte': os_trans, 'fornecedores': forneced,
        'Paretos': paretos, 'd_equipamento_pareto': peq_par,
        'Materiais_Aplicados': materiais,
    }
    html = ''
    for k, v in sorted(todas.items()):
        if not v: continue
        cols = list(v[0].keys())[:8]
        html += f"""
<div class="card">
  <h3>{k} <span style="font-size:11px;color:#888">({len(v):,} registros | {len(v[0])} colunas)</span></h3>
  {tbl_html(v, cols, 25)}
</div>"""
    return html or '<p style="color:#888;padding:20px">Sem dados</p>'

# ── Montar HTML ───────────────────────────────────────────────────────────────
tabs = [
    ('cockpit', 'Cockpit',         tab_cockpit),
    ('manfro',  'Manut.Frota',     tab_manfro),
    ('os',      'Ordens Serv.',    tab_os),
    ('pareto',  'Pareto Falhas',   tab_pareto),
    ('disp',    'DM/MTBF/MTTR',   tab_disponibilidade),
    ('orc',     'Orcamento',       tab_orcamento),
    ('diesel',  'Diesel/Lubrif.',  tab_diesel),
    ('mat',     'Materiais/OC',    tab_materiais),
    ('dados',   'Todos os Dados',  tab_all),
]

nav = ''.join(
    f'<div class="tab {"active" if i==0 else ""}" onclick="showTab(\'{id}\',this)">{lbl}</div>'
    for i, (id, lbl, _) in enumerate(tabs)
)

conteudo = ''
for i, (id, lbl, fn) in enumerate(tabs):
    try:
        c = fn()
    except Exception as e:
        c = f'<div class="card"><p style="color:#e74c3c">Erro: {e}</p></div>'
    conteudo += f'<div id="tab-{id}" class="content {"active" if i==0 else ""}"><h2>{lbl}</h2>{c}</div>'

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>UMOE | Dashboard Manutencao Premium</title>
<style>{CSS}</style>
</head>
<body>
<h1>UMOE OS 8.0 | Dashboard Manutencao Premium</h1>
<p class="sub">{ws_nome} | Extraido: {TODAY} | {len(inventario)} tabelas | {fN(total_rows)} registros</p>
<div class="tabs">{nav}</div>
{conteudo}
<script>{JS}</script>
</body>
</html>"""

OUT_FILE.write_text(html, encoding='utf-8')
kb = OUT_FILE.stat().st_size // 1024
print(f'Dashboard: {OUT_FILE}  ({kb} KB)')
