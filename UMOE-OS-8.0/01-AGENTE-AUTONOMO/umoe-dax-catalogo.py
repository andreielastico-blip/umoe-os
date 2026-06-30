# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Catalogo DAX navegavel — 100% das formulas do BI
Le Dados-PBI/MEDIDAS_DAX_*.json e gera UMA pagina HTML pesquisavel com todas
as formulas de negocio (medidas + colunas + tabelas calculadas), agrupadas por
dataset e tipo. Auto date tables (Auto=true) ficam de fora por padrao.

Saida: UMOE-OS-8.0/Relatorios/UMOE_Catalogo_DAX.html (+ copia em docs/)
"""
import json, glob, html
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
PBI  = ROOT / "UMOE-OS-8.0" / "Dados-PBI"
OUT  = ROOT / "UMOE-OS-8.0" / "Relatorios" / "UMOE_Catalogo_DAX.html"
DOCS = ROOT / "docs"
HOJE = datetime.now().strftime("%d/%m/%Y %H:%M")

# nomes amigaveis dos datasets
ROTULO = {
    "BI_AGR_01_BASE": "Agricola — BASE (producao, ATR, TCH, TAH, cargas)",
    "BI_AGR_01_CST":  "Agricola — Custo (CST)",
    "BI_AGR_01_CTRL": "Agricola — Controle (CTRL)",
    "MANUT_umoe_dataset": "Manutencao — dataset principal (frota, disponibilidade, diesel)",
    "MANUT_Materiais_Aplicados": "Manutencao — Materiais Aplicados",
    "MANUT_Capa": "Manutencao — Capa",
    "MANUT_OS_Interna_Campo": "Manutencao — OS Interna Campo",
    "MANUT_OS_Transporte": "Manutencao — OS Transporte",
    "MANUT_PARETOS_PROCESSOS": "Manutencao — Paretos Processos",
}
KIND_ORD = {"Medida": 0, "Coluna calculada": 1, "Tabela calculada": 2}
KIND_COR = {"Medida": "k-med", "Coluna calculada": "k-col", "Tabela calculada": "k-tab"}

def carregar():
    dados = {}
    for f in sorted(glob.glob(str(PBI / "MEDIDAS_DAX_*.json"))):
        ds = Path(f).stem.replace("MEDIDAS_DAX_", "")
        regs = [r for r in json.load(open(f, encoding="utf-8-sig")) if not r.get("Auto")]
        if regs:
            dados[ds] = regs
    return dados

def main():
    dados = carregar()
    total = sum(len(v) for v in dados.values())
    n_med = sum(1 for v in dados.values() for r in v if r["Kind"] == "Medida")
    n_col = sum(1 for v in dados.values() for r in v if r["Kind"] == "Coluna calculada")
    n_tab = sum(1 for v in dados.values() for r in v if r["Kind"] == "Tabela calculada")

    blocos = []
    nav_ds = []
    for ds in sorted(dados, key=lambda d: (0 if d.startswith("BI_AGR") else 1, d)):
        regs = sorted(dados[ds], key=lambda r: (KIND_ORD.get(r["Kind"], 9), r["Table"], r["Name"]))
        nav_ds.append(f'<button onclick="filtraDS(this,\'{ds}\')">{ds} <i>{len(regs)}</i></button>')
        cartoes = []
        for r in regs:
            nome = html.escape(f'{r["Table"]}.{r["Name"]}')
            expr = html.escape(r["Expression"])
            kcor = KIND_COR.get(r["Kind"], "")
            busca = html.escape(f'{r["Table"]} {r["Name"]} {r["Expression"]}'.lower(), quote=True)
            cartoes.append(
                f'<div class="f" data-ds="{ds}" data-kind="{r["Kind"]}" data-busca="{busca}">'
                f'<div class="fh"><span class="kk {kcor}">{r["Kind"]}</span>'
                f'<span class="fn">{nome}</span></div>'
                f'<pre><code>{expr}</code></pre></div>'
            )
        blocos.append(
            f'<section class="ds" id="ds-{ds}"><h2>{ROTULO.get(ds, ds)} '
            f'<span class="cnt">{len(regs)} formulas</span></h2>{"".join(cartoes)}</section>'
        )

    out = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UMOE — Catalogo DAX (100% das formulas)</title>
<style>
:root{{--bg:#0a0e1a;--surf:#121829;--surf2:#1a2236;--line:#243049;--txt:#e7e7ea;--mut:#8b97b0;--gold:#d4af37;--blue:#3b82f6;--green:#22c55e;--orange:#f97316}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px;line-height:1.5}}
header{{padding:22px 30px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:20}}
h1{{font-size:1.25rem;color:#fff}} .sub{{color:var(--mut);font-size:.82rem;margin-top:4px}}
.tot{{display:flex;gap:18px;margin-top:12px;flex-wrap:wrap}}
.tot div{{background:var(--surf);border:1px solid var(--line);border-radius:10px;padding:8px 14px;font-size:.8rem}}
.tot b{{font-size:1.2rem;color:var(--gold);display:block}}
.ctrl{{padding:14px 30px;border-bottom:1px solid var(--line);position:sticky;top:128px;background:var(--bg);z-index:19}}
#q{{width:100%;max-width:560px;padding:11px 14px;border-radius:10px;border:1px solid var(--line);background:var(--surf);color:#fff;font-size:.95rem}}
.chips{{margin-top:10px;display:flex;gap:7px;flex-wrap:wrap}}
.chips button{{background:var(--surf);border:1px solid var(--line);color:var(--mut);border-radius:18px;padding:5px 12px;font-size:.74rem;cursor:pointer}}
.chips button.on,.chips button:hover{{border-color:var(--gold);color:var(--gold)}}
.chips button i{{font-style:normal;opacity:.6;margin-left:4px}}
main{{padding:10px 30px 60px}}
.ds{{margin-top:26px}}
.ds h2{{font-size:.95rem;color:var(--gold);padding:10px 0;border-bottom:1px solid var(--line);position:sticky;top:210px;background:var(--bg)}}
.ds h2 .cnt{{color:var(--mut);font-size:.74rem;font-weight:400;margin-left:8px}}
.f{{background:var(--surf);border:1px solid var(--line);border-radius:10px;padding:13px 15px;margin:11px 0}}
.fh{{display:flex;align-items:center;gap:10px;margin-bottom:9px;flex-wrap:wrap}}
.fn{{font-weight:600;color:#fff;font-size:.9rem;word-break:break-word}}
.kk{{font-size:.62rem;font-weight:700;padding:2px 8px;border-radius:14px;white-space:nowrap}}
.k-med{{background:rgba(59,130,246,.16);color:#93c5fd}} .k-col{{background:rgba(34,197,94,.14);color:#4ade80}} .k-tab{{background:rgba(249,115,22,.15);color:#fb923c}}
pre{{background:#0b1120;border:1px solid var(--line);border-radius:8px;padding:12px;overflow-x:auto}}
code{{font-family:'Cascadia Code','Consolas',monospace;font-size:.82rem;color:#d6deeb;white-space:pre}}
.none{{color:var(--mut);padding:30px;text-align:center;display:none}}
.foot{{color:var(--mut);font-size:.72rem;padding:18px 30px;border-top:1px solid var(--line);text-align:center}}
</style></head><body>
<header>
  <h1>UMOE BIOENERGY — Catalogo DAX</h1>
  <div class="sub">100% das formulas de calculo do Power BI | extraido verbatim com pbixray | {HOJE}</div>
  <div class="tot">
    <div><b>{total}</b>formulas de negocio</div>
    <div><b>{n_med}</b>medidas</div>
    <div><b>{n_col}</b>colunas calculadas</div>
    <div><b>{n_tab}</b>tabelas calculadas</div>
    <div><b>{len(dados)}</b>datasets</div>
  </div>
</header>
<div class="ctrl">
  <input id="q" placeholder="Buscar formula, tabela, coluna... (ex: ATR, DIVIDE, disponibilidade)" oninput="filtra()">
  <div class="chips" id="chipsKind">
    <button class="on" data-k="" onclick="setKind(this,'')">Tudo</button>
    <button data-k="Medida" onclick="setKind(this,'Medida')">Medidas</button>
    <button data-k="Coluna calculada" onclick="setKind(this,'Coluna calculada')">Colunas calc.</button>
    <button data-k="Tabela calculada" onclick="setKind(this,'Tabela calculada')">Tabelas calc.</button>
  </div>
  <div class="chips" id="chipsDS">
    <button class="on" onclick="filtraDS(this,'')">Todos datasets</button>
    {''.join(nav_ds)}
  </div>
</div>
<main>{''.join(blocos)}<div class="none" id="none">Nenhuma formula encontrada.</div></main>
<div class="foot">UMOE OS 8.0 | fonte de verdade dos calculos | auto date tables omitidas (scaffolding do Power BI)</div>
<script>
var fKind="", fDS="", fQ="";
function setKind(b,k){{document.querySelectorAll('#chipsKind button').forEach(x=>x.classList.remove('on'));b.classList.add('on');fKind=k;filtra();}}
function filtraDS(b,ds){{fDS=ds;document.querySelectorAll('#chipsDS button').forEach(x=>x.classList.remove('on'));b.classList.add('on');filtra();}}
function filtra(){{
  fQ=(document.getElementById('q').value||'').toLowerCase().trim();
  var vis=0;
  document.querySelectorAll('.f').forEach(function(el){{
    var ok=true;
    if(fKind && el.dataset.kind!==fKind) ok=false;
    if(fDS && el.dataset.ds!==fDS) ok=false;
    if(fQ && el.dataset.busca.indexOf(fQ)<0) ok=false;
    el.style.display=ok?'':'none'; if(ok)vis++;
  }});
  document.querySelectorAll('.ds').forEach(function(s){{
    var any=s.querySelectorAll('.f:not([style*="none"])').length>0; s.style.display=any?'':'none';
  }});
  document.getElementById('none').style.display=vis?'none':'block';
}}
</script></body></html>"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "UMOE_Catalogo_DAX.html").write_text(out, encoding="utf-8")
    print(f"OK -> {OUT} ({OUT.stat().st_size//1024} KB) | {total} formulas ({n_med} med, {n_col} col, {n_tab} tab) | +docs/")

if __name__ == "__main__":
    main()
