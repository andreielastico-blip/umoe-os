# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 - Dashboard Manutencao Premium
Carrega todos os JSONs extraidos de UMOE-OS-8.0/Dados-PBI/MANUT/
Gera HTML interativo com 8 abas de KPIs de manutencao
"""
import json, re
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / 'UMOE-OS-8.0' / 'Dados-PBI' / 'MANUT'
OUT_FILE = Path(__file__).parent.parent / 'UMOE-OS-8.0' / 'Relatorios' / 'UMOE_Dashboard_Manutencao.html'
OUT_FILE.parent.mkdir(exist_ok=True)

TODAY = '2026-06-16'

# ── Helpers ──────────────────────────────────────────────────────────────────

def load(fn):
    fp = DATA_DIR / fn
    if not fp.exists():
        return []
    data = json.loads(fp.read_bytes().decode('utf-8-sig'))
    if not isinstance(data, list) or not data:
        return []
    return [{
        (k.split('[')[-1].rstrip(']') if '[' in k else k): v
        for k, v in row.items()
    } for row in data]

def load_any(*names):
    for n in names:
        d = load(n)
        if d:
            return d
    return []

def fN(v, dec=0):
    if v is None: return '-'
    try:
        v = float(v)
        s = f'{v:,.{dec}f}'
        return s.replace(',', 'X').replace('.', ',').replace('X', '.') if dec > 0 else f'{v:,.0f}'.replace(',', '.')
    except: return str(v)

def fR(v):
    if v is None: return '-'
    try: return f'R$ {float(v):,.0f}'.replace(',', '.')
    except: return str(v)

# ── Descobrir todos os JSONs disponíveis ─────────────────────────────────────
all_jsons = sorted(DATA_DIR.glob('*.json'))
print(f'JSONs encontrados: {len(all_jsons)}')
for f in all_jsons:
    print(f'  {f.name} ({f.stat().st_size//1024} KB)')

# Inventario de todos os dados
inventario = {}
for fp in all_jsons:
    if fp.stat().st_size < 100:
        continue
    try:
        data = load(fp.name)
        if data:
            inventario[fp.stem] = data
            print(f'  Carregado: {fp.stem} ({len(data)} rows) cols={list(data[0].keys())[:6]}')
    except Exception as e:
        print(f'  Erro {fp.name}: {e}')

print(f'\nTotal tabelas carregadas: {len(inventario)}')

# ── Deteccao automatica de tabelas por padrao de nome ────────────────────────

def find_table(*patterns):
    for p in patterns:
        p_low = p.lower()
        for k, v in inventario.items():
            if p_low in k.lower():
                return k, v
    return None, []

def find_col(data, *names):
    if not data: return None
    row = data[0]
    for n in names:
        for k in row.keys():
            if n.lower() in k.lower():
                return k
    return None

# Detectar tabelas
os_key, os_data       = find_table('OS', 'ORDEM_SERV', 'ORDENS')
falha_key, falha_data = find_table('FALHA', 'FALHAS', 'DEFEITO')
equip_key, equip_data = find_table('EQUIP', 'FROTA', 'MAQUINA', 'COLHEDORA')
disp_key, disp_data   = find_table('DISPONIB', 'DM', 'DF', 'DISPONI')
peca_key, peca_data   = find_table('PECA', 'PECAS', 'PART', 'ESTOQUE')
custo_key, custo_data = find_table('CUSTO', 'CST', 'COST')
prev_key, prev_data   = find_table('PREVENTIV', 'PREV', 'PM')
seg_key, seg_data     = find_table('SEGUR', 'INCID', 'TOMBA', 'ACIDENTE')

# Catalogo
catalogo = {}
cat_fp = DATA_DIR / 'MANUT_CATALOGO.json'
if cat_fp.exists():
    catalogo = json.loads(cat_fp.read_bytes().decode('utf-8-sig'))

ws_nome = catalogo.get('workspace', {}).get('name', 'Manutencao Premium')
n_datasets = len(catalogo.get('datasets', []))
n_reports  = len(catalogo.get('reports', []))

# ── KPIs globais ─────────────────────────────────────────────────────────────

# Total registros
total_rows = sum(len(v) for v in inventario.values())

# OS: total, abertas, fechadas
os_total    = len(os_data)
col_status  = find_col(os_data, 'STATUS', 'SITUAC', 'SIT', 'ESTADO')
os_abertas  = len([r for r in os_data if col_status and 'ABER' in str(r.get(col_status,'')).upper()]) if col_status else 0
os_fechadas = len([r for r in os_data if col_status and 'FECH' in str(r.get(col_status,'')).upper()]) if col_status else 0

# DM medio
col_dm   = find_col(disp_data, 'DM', 'DISP', 'PERC', 'PCT')
dm_vals  = [float(r.get(col_dm,0) or 0) for r in disp_data if col_dm and r.get(col_dm)]
dm_medio = sum(dm_vals)/len(dm_vals) if dm_vals else 0

# MTBF / MTTR
col_mtbf = find_col(disp_data, 'MTBF')
col_mttr = find_col(disp_data, 'MTTR')
mtbf_med = (sum(float(r.get(col_mtbf,0) or 0) for r in disp_data) / max(1,len(disp_data))) if col_mtbf else 0
mttr_med = (sum(float(r.get(col_mttr,0) or 0) for r in disp_data) / max(1,len(disp_data))) if col_mttr else 0

# Top falhas
col_tipo_f = find_col(falha_data, 'CAUSA', 'TIPO', 'DEFEITO', 'DE_FALHA')
col_hrs_f  = find_col(falha_data, 'HRS', 'HORA', 'TEMPO')
falha_tipo = defaultdict(lambda: {'n': 0, 'hrs': 0})
for r in falha_data:
    tp = str(r.get(col_tipo_f,'?'))[:40] if col_tipo_f else '?'
    falha_tipo[tp]['n']   += 1
    falha_tipo[tp]['hrs'] += float(r.get(col_hrs_f,0) or 0) if col_hrs_f else 0

# Custo total
col_vlr = find_col(custo_data, 'VL_REAL', 'VALOR', 'CUSTO', 'VLR', 'VL_')
custo_tot = sum(float(r.get(col_vlr,0) or 0) for r in custo_data) if col_vlr else 0

# ── Tabela generica para qualquer dataset ────────────────────────────────────

def generic_table(data, max_cols=8, max_rows=50, title=''):
    if not data:
        return f'<div class="card"><h3>{title}</h3><p style="color:#888">Sem dados</p></div>'
    cols = list(data[0].keys())[:max_cols]
    hdrs = ''.join(f'<th>{c}</th>' for c in cols)
    rows = ''
    for r in data[:max_rows]:
        cells = ''.join(f'<td>{str(r.get(c,""))[:25]}</td>' for c in cols)
        rows += f'<tr>{cells}</tr>'
    return f"""
<div class="card">
  <h3>{title} ({len(data)} registros)</h3>
  <div class="tw"><table><thead><tr>{hdrs}</tr></thead><tbody>{rows}</tbody></table></div>
</div>"""

# ── CSS / JS ─────────────────────────────────────────────────────────────────
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Arial,sans-serif;background:#0d1b2a;color:#e0e0e0;font-size:13px}
h1{color:#f0a500;font-size:22px;padding:18px 24px 6px}
h2{color:#f0a500;font-size:15px;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid #333}
h3{color:#ffc947;font-size:13px;margin:14px 0 8px}
.tabs{display:flex;gap:2px;padding:0 24px;flex-wrap:wrap}
.tab{padding:7px 14px;cursor:pointer;background:#162033;color:#888;border-radius:6px 6px 0 0;font-size:12px;transition:.15s}
.tab:hover{color:#ccc}
.tab.active{background:#1a3a5c;color:#f0a500;font-weight:600}
.content{display:none;padding:18px 24px}
.content.active{display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(165px,1fr));gap:10px;margin-bottom:16px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
.kpi{background:#162033;border-radius:8px;padding:14px;border-left:3px solid #f0a500}
.kpi .val{font-size:24px;font-weight:700;color:#f0a500}
.kpi .lbl{font-size:11px;color:#888;margin-top:3px}
.kpi .sub{font-size:11px;color:#bbb;margin-top:3px}
.kpi.r{border-left-color:#e74c3c}.kpi.r .val{color:#e74c3c}
.kpi.y{border-left-color:#f39c12}.kpi.y .val{color:#f39c12}
.kpi.g{border-left-color:#27ae60}.kpi.g .val{color:#27ae60}
.card{background:#162033;border-radius:8px;padding:14px;margin-bottom:14px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#1a3a5c;color:#f0a500;padding:7px 9px;text-align:left;position:sticky;top:0;z-index:1}
td{padding:5px 9px;border-bottom:1px solid #222}
tr:hover td{background:#1e3050}
.tw{max-height:360px;overflow-y:auto;border-radius:6px;border:1px solid #333}
.red{color:#e74c3c}.green{color:#27ae60}.yellow{color:#f39c12}
.alert{background:#2d1b00;border-left:4px solid #f0a500;padding:10px 14px;border-radius:0 6px 6px 0;margin-bottom:12px;font-size:12px}
.bbar{background:#333;border-radius:3px;height:7px;width:100%;margin-top:5px}
.bf{height:7px;border-radius:3px}
.sub{color:#888;font-size:12px;padding:0 24px 12px}
.tag{display:inline-block;padding:2px 7px;border-radius:10px;font-size:11px;background:#1a3a5c;color:#f0a500;margin:2px}
"""

JS = """
function showTab(id,el){
  document.querySelectorAll('.content').forEach(c=>c.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  el.classList.add('active');
}
"""

# ── Tab builders ─────────────────────────────────────────────────────────────

def tab_cockpit():
    dm_c   = 'r' if dm_medio < 0.85 else 'y' if dm_medio < 0.90 else 'g'
    os_c   = 'r' if os_abertas > 50 else 'y' if os_abertas > 20 else 'g'

    # Lista de todos os datasets
    ds_rows = ''
    for ds in catalogo.get('datasets', []):
        ds_rows += f'<tr><td>{ds.get("name","")}</td><td>{ds.get("id","")[:20]}...</td></tr>'

    # Inventario de tabelas carregadas
    inv_rows = ''
    for k, v in sorted(inventario.items()):
        cols = list(v[0].keys())[:4] if v else []
        inv_rows += f'<tr><td>{k}</td><td>{len(v)}</td><td style="font-size:11px">{", ".join(cols)}</td></tr>'

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{ws_nome[:20]}</div><div class="lbl">Workspace</div><div class="sub">{n_datasets} datasets | {n_reports} reports</div></div>
  <div class="kpi"><div class="val">{len(inventario)}</div><div class="lbl">Tabelas Extraidas</div><div class="sub">{fN(total_rows)} registros total</div></div>
  <div class="kpi {os_c}"><div class="val">{os_total}</div><div class="lbl">Ordens de Servico</div><div class="sub">Abertas: {os_abertas} | Fechadas: {os_fechadas}</div></div>
  <div class="kpi {dm_c}"><div class="val">{fN(dm_medio*100,1)}%</div><div class="lbl">DM Medio</div><div class="sub">Meta: 90%</div>
    <div class="bbar"><div class="bf" style="width:{min(100,dm_medio*100):.1f}%;background:{'#27ae60' if dm_medio>=0.90 else '#f39c12' if dm_medio>=0.85 else '#e74c3c'}"></div></div>
  </div>
  <div class="kpi"><div class="val">{fN(mtbf_med,1)}</div><div class="lbl">MTBF Medio (h)</div></div>
  <div class="kpi y"><div class="val">{fN(mttr_med,2)}</div><div class="lbl">MTTR Medio (h)</div></div>
  <div class="kpi"><div class="val">{len(falha_data)}</div><div class="lbl">Registros Falhas</div></div>
  <div class="kpi"><div class="val">{fR(custo_tot)}</div><div class="lbl">Custo Total</div></div>
</div>

<div class="alert">
  <b>WORKSPACE: {ws_nome}</b> | Extraido em {TODAY} |
  {len(inventario)} tabelas | {fN(total_rows)} registros |
  DM: {fN(dm_medio*100,1)}% (meta 90%) |
  OS Abertas: {os_abertas}
</div>

<div class="g2">
  <div class="card">
    <h3>Datasets Encontrados</h3>
    <table><thead><tr><th>Nome</th><th>ID</th></tr></thead><tbody>{ds_rows}</tbody></table>
  </div>
  <div class="card">
    <h3>Tabelas Extraidas (Inventario)</h3>
    <div class="tw">
      <table><thead><tr><th>Tabela</th><th>Registros</th><th>Colunas (primeiras 4)</th></tr></thead>
      <tbody>{inv_rows}</tbody></table>
    </div>
  </div>
</div>
"""

def tab_os():
    if not os_data:
        return '<div class="card"><p style="color:#888;padding:20px">Tabela de Ordens de Servico nao encontrada.<br>Execute o pipeline para extrair dados do workspace.</p></div>'

    cols_os = list(os_data[0].keys())
    col_tipo = find_col(os_data, 'TIPO', 'TP_OS', 'CATEGORIA', 'MANUT')
    col_eq   = find_col(os_data, 'EQUIP', 'MAQUINA', 'FROTA', 'ATIVO')
    col_dt   = find_col(os_data, 'DATA', 'DT_', 'ABERTURA')
    col_hrs  = find_col(os_data, 'HRS', 'HORA', 'DURACAO', 'TEMPO')

    # Por tipo
    tipo_cnt = defaultdict(lambda: {'n': 0, 'hrs': 0})
    for r in os_data:
        tp = str(r.get(col_tipo,'N/A'))[:35] if col_tipo else 'N/A'
        tipo_cnt[tp]['n']   += 1
        tipo_cnt[tp]['hrs'] += float(r.get(col_hrs,0) or 0) if col_hrs else 0

    rows_tp = ''.join(
        f'<tr><td>{tp}</td><td>{v["n"]}</td><td>{fN(v["hrs"],1)}</td></tr>'
        for tp, v in sorted(tipo_cnt.items(), key=lambda x: x[1]['n'], reverse=True)[:12]
    )

    # Por equipamento
    eq_cnt = defaultdict(int)
    for r in os_data:
        eq = str(r.get(col_eq,'?'))[:30] if col_eq else '?'
        eq_cnt[eq] += 1
    rows_eq = ''.join(
        f'<tr><td>{eq}</td><td>{n}</td></tr>'
        for eq, n in sorted(eq_cnt.items(), key=lambda x: x[1], reverse=True)[:15]
    )

    # Tabela geral (primeiras colunas)
    show_cols = cols_os[:8]
    hdrs = ''.join(f'<th>{c}</th>' for c in show_cols)
    rows_gen = ''
    for r in os_data[:40]:
        rows_gen += '<tr>' + ''.join(f'<td>{str(r.get(c,""))[:20]}</td>' for c in show_cols) + '</tr>'

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{os_total}</div><div class="lbl">Total OS</div></div>
  <div class="kpi {'r' if os_abertas>20 else 'y'}"><div class="val">{os_abertas}</div><div class="lbl">Abertas</div></div>
  <div class="kpi g"><div class="val">{os_fechadas}</div><div class="lbl">Fechadas</div></div>
  <div class="kpi"><div class="val">{len(tipo_cnt)}</div><div class="lbl">Tipos de OS</div></div>
</div>
<div class="g2">
  <div class="card">
    <h3>OS por Tipo</h3>
    <div class="tw"><table><thead><tr><th>Tipo</th><th>Qtd</th><th>Horas</th></tr></thead><tbody>{rows_tp}</tbody></table></div>
  </div>
  <div class="card">
    <h3>OS por Equipamento (Top 15)</h3>
    <div class="tw"><table><thead><tr><th>Equipamento</th><th>OS</th></tr></thead><tbody>{rows_eq}</tbody></table></div>
  </div>
</div>
<div class="card">
  <h3>Ordens de Servico - Detalhe (40 registros)</h3>
  <div class="tw"><table><thead><tr>{hdrs}</tr></thead><tbody>{rows_gen}</tbody></table></div>
</div>
"""

def tab_falhas():
    if not falha_data:
        return '<div class="card"><p style="color:#888;padding:20px">Tabela de Falhas nao encontrada.</p></div>'

    top_falha = sorted(falha_tipo.items(), key=lambda x: x[1]['n'], reverse=True)[:15]
    rows_f = ''.join(
        f'<tr><td>{tp}</td><td>{v["n"]}</td><td>{fN(v["hrs"],1)}</td></tr>'
        for tp, v in top_falha
    )

    cols_f = list(falha_data[0].keys())[:8]
    hdrs_f = ''.join(f'<th>{c}</th>' for c in cols_f)
    rows_gen = ''
    for r in falha_data[:40]:
        rows_gen += '<tr>' + ''.join(f'<td>{str(r.get(c,""))[:20]}</td>' for c in cols_f) + '</tr>'

    return f"""
<div class="grid">
  <div class="kpi r"><div class="val">{len(falha_data)}</div><div class="lbl">Total Falhas</div></div>
  <div class="kpi"><div class="val">{len(falha_tipo)}</div><div class="lbl">Tipos de Falha</div></div>
  <div class="kpi y"><div class="val">{fN(sum(v["hrs"] for v in falha_tipo.values()),1)}</div><div class="lbl">Horas Paradas</div></div>
</div>
<div class="g2">
  <div class="card">
    <h3>Top 15 Causas de Falha (Pareto)</h3>
    <div class="tw"><table><thead><tr><th>Causa</th><th>Ocorr.</th><th>Horas</th></tr></thead><tbody>{rows_f}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Falhas - Detalhe</h3>
    <div class="tw"><table><thead><tr>{hdrs_f}</tr></thead><tbody>{rows_gen}</tbody></table></div>
  </div>
</div>
"""

def tab_disponibilidade():
    if not disp_data:
        return '<div class="card"><p style="color:#888;padding:20px">Tabela de Disponibilidade nao encontrada.</p></div>'

    cols_d = list(disp_data[0].keys())[:8]
    hdrs_d = ''.join(f'<th>{c}</th>' for c in cols_d)

    # Por equipamento
    col_eq_d = find_col(disp_data, 'EQUIP', 'MAQUINA', 'FROTA', 'ATIVO', 'DESC')
    eq_dm = defaultdict(lambda: {'dm': 0, 'n': 0})
    for r in disp_data:
        eq = str(r.get(col_eq_d,'?'))[:30] if col_eq_d else '?'
        dm = float(r.get(col_dm,0) or 0) if col_dm else 0
        eq_dm[eq]['dm'] += dm
        eq_dm[eq]['n']  += 1

    rows_eq = ''
    for eq, v in sorted(eq_dm.items(), key=lambda x: x[1]['dm']/max(1,x[1]['n'])):
        dm_v = v['dm'] / v['n']
        c    = 'r' if dm_v < 0.85 else 'y' if dm_v < 0.90 else 'green'
        rows_eq += f'<tr><td>{eq}</td><td class="{c}">{fN(dm_v*100,1)}%</td><td>{fN(mtbf_med,1) if col_mtbf else "-"}</td><td>{fN(mttr_med,2) if col_mttr else "-"}</td></tr>'

    rows_gen = ''
    for r in disp_data[:40]:
        rows_gen += '<tr>' + ''.join(f'<td>{str(r.get(c,""))[:20]}</td>' for c in cols_d) + '</tr>'

    return f"""
<div class="grid">
  <div class="kpi {'r' if dm_medio<0.85 else 'y' if dm_medio<0.90 else 'g'}">
    <div class="val">{fN(dm_medio*100,1)}%</div>
    <div class="lbl">DM Medio</div>
    <div class="sub">Meta: 90%</div>
    <div class="bbar"><div class="bf" style="width:{min(100,dm_medio*100):.1f}%;background:{'#27ae60' if dm_medio>=0.90 else '#f39c12'}"></div></div>
  </div>
  <div class="kpi"><div class="val">{fN(mtbf_med,1)}h</div><div class="lbl">MTBF Medio</div></div>
  <div class="kpi y"><div class="val">{fN(mttr_med,2)}h</div><div class="lbl">MTTR Medio</div></div>
  <div class="kpi"><div class="val">{len(disp_data)}</div><div class="lbl">Registros</div></div>
</div>
<div class="g2">
  <div class="card">
    <h3>DM por Equipamento</h3>
    <div class="tw"><table><thead><tr><th>Equipamento</th><th>DM%</th><th>MTBF</th><th>MTTR</th></tr></thead><tbody>{rows_eq}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Disponibilidade - Detalhe</h3>
    <div class="tw"><table><thead><tr>{hdrs_d}</tr></thead><tbody>{rows_gen}</tbody></table></div>
  </div>
</div>
"""

def tab_pecas():
    if not peca_data:
        return '<div class="card"><p style="color:#888;padding:20px">Tabela de Pecas/Estoque nao encontrada.</p></div>'

    col_peca = find_col(peca_data, 'DESC', 'NOME', 'PECA', 'COMPONENTE', 'DE_')
    col_qt   = find_col(peca_data, 'SALDO', 'QT', 'ESTOQUE', 'QTDE')
    col_vlr  = find_col(peca_data, 'VALOR', 'VLR', 'PRECO', 'CUSTO')
    col_abc  = find_col(peca_data, 'CURVA', 'ABC', 'CLASS')

    # Curva ABC
    abc_cnt = defaultdict(lambda: {'n': 0, 'vlr': 0})
    for r in peca_data:
        abc = str(r.get(col_abc,'?'))[:3] if col_abc else '?'
        abc_cnt[abc]['n']   += 1
        abc_cnt[abc]['vlr'] += float(r.get(col_vlr,0) or 0) if col_vlr else 0

    rows_abc = ''.join(
        f'<tr><td>{k}</td><td>{v["n"]}</td><td>{fR(v["vlr"])}</td></tr>'
        for k, v in sorted(abc_cnt.items())
    )

    # Top pecas por valor
    top_p = sorted(peca_data, key=lambda x: float(x.get(col_vlr,0) or 0), reverse=True)[:15] if col_vlr else peca_data[:15]
    cols_p = [c for c in [col_peca, col_qt, col_vlr, col_abc] if c][:6]
    if not cols_p:
        cols_p = list(peca_data[0].keys())[:6]
    hdrs_p = ''.join(f'<th>{c}</th>' for c in cols_p)
    rows_p = ''
    for r in top_p:
        rows_p += '<tr>' + ''.join(f'<td>{str(r.get(c,""))[:25]}</td>' for c in cols_p) + '</tr>'

    estq_tot = sum(float(r.get(col_vlr,0) or 0) for r in peca_data) if col_vlr else 0

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{len(peca_data)}</div><div class="lbl">Itens em Estoque</div></div>
  <div class="kpi"><div class="val">{fR(estq_tot)}</div><div class="lbl">Valor Total Estoque</div></div>
  <div class="kpi"><div class="val">{len(abc_cnt)}</div><div class="lbl">Classes ABC</div></div>
</div>
<div class="g2">
  <div class="card">
    <h3>Curva ABC</h3>
    <table><thead><tr><th>Classe</th><th>Itens</th><th>Valor</th></tr></thead><tbody>{rows_abc}</tbody></table>
  </div>
  <div class="card">
    <h3>Top Pecas por Valor</h3>
    <div class="tw"><table><thead><tr>{hdrs_p}</tr></thead><tbody>{rows_p}</tbody></table></div>
  </div>
</div>
"""

def tab_custos():
    if not custo_data:
        return '<div class="card"><p style="color:#888;padding:20px">Tabela de Custos nao encontrada.</p></div>'

    col_cc   = find_col(custo_data, 'CCUSTO', 'CC', 'CENTRO', 'DE_CC')
    col_grp  = find_col(custo_data, 'GRUPO', 'OPERACAO', 'ATIVIDADE')
    col_orc  = find_col(custo_data, 'ORC', 'BUDGET', 'PLANEJ')
    col_real = find_col(custo_data, 'REAL', 'REALIZ', 'VL_REAL', 'VALOR')

    cc_agg = defaultdict(lambda: {'orc': 0, 'real': 0, 'n': 0})
    for r in custo_data:
        cc   = str(r.get(col_cc,'?'))[:35] if col_cc else '?'
        cc_agg[cc]['orc']  += float(r.get(col_orc,0) or 0) if col_orc else 0
        cc_agg[cc]['real'] += float(r.get(col_real,0) or 0) if col_real else 0
        cc_agg[cc]['n']    += 1

    top_cc = sorted(cc_agg.items(), key=lambda x: x[1]['real'], reverse=True)[:12]
    rows_cc = ''
    for cc, v in top_cc:
        dif = v['real'] - v['orc']
        c = 'r' if dif > 0 else 'green'
        rows_cc += f'<tr><td>{cc}</td><td>{fR(v["orc"])}</td><td>{fR(v["real"])}</td><td class="{c}">{fR(dif)}</td></tr>'

    tot_orc  = sum(v['orc'] for v in cc_agg.values())
    tot_real = sum(v['real'] for v in cc_agg.values())

    cols_c = list(custo_data[0].keys())[:8]
    hdrs_c = ''.join(f'<th>{c}</th>' for c in cols_c)
    rows_gen = ''
    for r in custo_data[:30]:
        rows_gen += '<tr>' + ''.join(f'<td>{str(r.get(c,""))[:20]}</td>' for c in cols_c) + '</tr>'

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{fR(tot_orc)}</div><div class="lbl">Total Orcado</div></div>
  <div class="kpi {'r' if tot_real>tot_orc else 'g'}"><div class="val">{fR(tot_real)}</div><div class="lbl">Total Realizado</div></div>
  <div class="kpi {'r' if tot_real>tot_orc else 'g'}"><div class="val">{fR(tot_real-tot_orc)}</div><div class="lbl">Desvio</div></div>
  <div class="kpi"><div class="val">{len(cc_agg)}</div><div class="lbl">Centros de Custo</div></div>
</div>
<div class="g2">
  <div class="card">
    <h3>Top 12 CC - Custo Realizado</h3>
    <div class="tw"><table><thead><tr><th>Centro de Custo</th><th>Orcado</th><th>Realizado</th><th>Desvio</th></tr></thead><tbody>{rows_cc}</tbody></table></div>
  </div>
  <div class="card">
    <h3>Custos - Detalhe</h3>
    <div class="tw"><table><thead><tr>{hdrs_c}</tr></thead><tbody>{rows_gen}</tbody></table></div>
  </div>
</div>
"""

def tab_frota():
    if not equip_data:
        return '<div class="card"><p style="color:#888;padding:20px">Tabela de Frota/Equipamentos nao encontrada.</p></div>'

    col_tp_eq = find_col(equip_data, 'TIPO', 'TP_', 'CATEGORIA', 'GRUPO')
    col_sit   = find_col(equip_data, 'STATUS', 'SITUAC', 'ATIVO', 'SIT')

    tp_cnt  = defaultdict(int)
    sit_cnt = defaultdict(int)
    for r in equip_data:
        tp  = str(r.get(col_tp_eq,'?'))[:30] if col_tp_eq else '?'
        sit = str(r.get(col_sit,'?'))[:20] if col_sit else '?'
        tp_cnt[tp]   += 1
        sit_cnt[sit] += 1

    rows_tp  = ''.join(f'<tr><td>{tp}</td><td>{n}</td></tr>' for tp, n in sorted(tp_cnt.items(), key=lambda x: x[1], reverse=True)[:12])
    rows_sit = ''.join(f'<tr><td>{s}</td><td>{n}</td></tr>' for s, n in sorted(sit_cnt.items(), key=lambda x: x[1], reverse=True)[:10])

    cols_e = list(equip_data[0].keys())[:8]
    hdrs_e = ''.join(f'<th>{c}</th>' for c in cols_e)
    rows_gen = ''
    for r in equip_data[:40]:
        rows_gen += '<tr>' + ''.join(f'<td>{str(r.get(c,""))[:20]}</td>' for c in cols_e) + '</tr>'

    return f"""
<div class="grid">
  <div class="kpi"><div class="val">{len(equip_data)}</div><div class="lbl">Total Equipamentos</div></div>
  <div class="kpi"><div class="val">{len(tp_cnt)}</div><div class="lbl">Tipos</div></div>
  <div class="kpi"><div class="val">{len(sit_cnt)}</div><div class="lbl">Status</div></div>
</div>
<div class="g2">
  <div class="card">
    <h3>Por Tipo de Equipamento</h3>
    <table><thead><tr><th>Tipo</th><th>Qtd</th></tr></thead><tbody>{rows_tp}</tbody></table>
  </div>
  <div class="card">
    <h3>Por Status</h3>
    <table><thead><tr><th>Status</th><th>Qtd</th></tr></thead><tbody>{rows_sit}</tbody></table>
  </div>
</div>
<div class="card">
  <h3>Frota - Detalhe (40 registros)</h3>
  <div class="tw"><table><thead><tr>{hdrs_e}</tr></thead><tbody>{rows_gen}</tbody></table></div>
</div>
"""

def tab_all_tables():
    html = ''
    for k, v in sorted(inventario.items()):
        if not v: continue
        cols = list(v[0].keys())[:8]
        hdrs = ''.join(f'<th>{c}</th>' for c in cols)
        rows = ''
        for r in v[:30]:
            rows += '<tr>' + ''.join(f'<td>{str(r.get(c,""))[:22]}</td>' for c in cols) + '</tr>'
        html += f"""
<div class="card">
  <h3>{k} <span style="font-size:11px;color:#888">({len(v)} registros)</span></h3>
  <div class="tw"><table><thead><tr>{hdrs}</tr></thead><tbody>{rows}</tbody></table></div>
</div>"""
    if not html:
        html = '<p style="color:#888;padding:20px">Nenhum dado extraido ainda. Execute pbi-manutencao-pipeline.ps1 primeiro.</p>'
    return html

# ── Montar HTML ───────────────────────────────────────────────────────────────
tabs_defs = [
    ('cockpit',  'Cockpit',       tab_cockpit),
    ('os',       'Ordens Serv.',  tab_os),
    ('falhas',   'Falhas/Pareto', tab_falhas),
    ('disp',     'DM/MTBF/MTTR', tab_disponibilidade),
    ('pecas',    'Pecas/ABC',     tab_pecas),
    ('custos',   'Custos',        tab_custos),
    ('frota',    'Frota',         tab_frota),
    ('dados',    'Todos os Dados',tab_all_tables),
]

tab_nav = ''.join(
    f'<div class="tab {"active" if i==0 else ""}" onclick="showTab(\'{id}\',this)">{lbl}</div>'
    for i, (id, lbl, _) in enumerate(tabs_defs)
)

print('Construindo abas...')
tab_content = ''
for i, (id, lbl, fn) in enumerate(tabs_defs):
    try:
        content = fn()
        tab_content += f'<div id="tab-{id}" class="content {"active" if i==0 else ""}"><h2>{lbl}</h2>{content}</div>'
    except Exception as e:
        tab_content += f'<div id="tab-{id}" class="content {"active" if i==0 else ""}"><h2>{lbl}</h2><div class="card"><p style="color:#e74c3c">Erro: {e}</p></div></div>'

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>UMOE OS 8.0 | Dashboard Manutencao Premium</title>
<style>{CSS}</style>
</head>
<body>
<h1>UMOE OS 8.0 | Dashboard Manutencao Premium</h1>
<p class="sub">{ws_nome} | Extraido: {TODAY} | {len(inventario)} tabelas | {fN(total_rows)} registros</p>
<div class="tabs">{tab_nav}</div>
{tab_content}
<script>{JS}</script>
</body>
</html>"""

OUT_FILE.write_text(html, encoding='utf-8')
kb = OUT_FILE.stat().st_size // 1024
print(f'\nDashboard salvo: {OUT_FILE}')
print(f'Tamanho: {kb} KB')
