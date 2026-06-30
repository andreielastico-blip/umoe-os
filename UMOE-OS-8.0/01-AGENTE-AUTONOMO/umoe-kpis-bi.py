# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Painel 100% dos KPIs do BI
Renderiza TODAS as medidas do modelo com o valor que a propria BI calcula
(Dados-PBI/MEDIDAS_VALORES.json) + a formula DAX oficial (MEDIDAS_DAX_*.json).
Pesquisavel, filtravel por dataset e por status. 100% fiel.

Saida: UMOE-OS-8.0/Relatorios/UMOE_KPIs_BI.html (+ docs/)
"""
import json, glob, html
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
PBI  = ROOT / "UMOE-OS-8.0" / "Dados-PBI"
VAL  = PBI / "MEDIDAS_VALORES.json"
OUT  = ROOT / "UMOE-OS-8.0" / "Relatorios" / "UMOE_KPIs_BI.html"
DOCS = ROOT / "docs"
HOJE = datetime.now().strftime("%d/%m/%Y %H:%M")

ROTULO = {
    "BI_AGR_01_BASE": "Agricola — BASE",
    "BI_AGR_01_CST":  "Agricola — Custo",
    "BI_AGR_01_CTRL": "Agricola — Controle",
    "MANUT_umoe_dataset": "Manutencao — principal",
    "MANUT_PARETOS_PROCESSOS": "Manutencao — Paretos",
}
STBADGE = {"ok": ("s-ok", "ao vivo"), "contexto": ("s-ctx", "precisa de filtro"),
           "pesada": ("s-pes", "medida pesada"), "erro": ("s-err", "nao avaliavel")}

def formulas():
    f = {}
    for fp in glob.glob(str(PBI / "MEDIDAS_DAX_*.json")):
        for r in json.load(open(fp, encoding="utf-8-sig")):
            if r.get("Kind") == "Medida":
                f[(r["Table"], r["Name"])] = r["Expression"]
    return f

def fmt(v):
    """Formata valor: numero BR, texto como veio, None -> '-'."""
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "Sim" if v else "Nao"
    if isinstance(v, (int, float)):
        av = abs(v)
        dec = 0 if (av >= 1000 or float(v).is_integer()) else (2 if av < 100 else 1)
        s = f"{float(v):,.{dec}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    return str(v)

def main():
    if not VAL.exists():
        print("ERRO: rode pbi-medidas-valores.py antes (falta MEDIDAS_VALORES.json)."); return
    dados = json.load(open(VAL, encoding="utf-8-sig"))
    fmap = formulas()
    n_ok = sum(1 for r in dados if r["status"] == "ok")

    porDS = {}
    for r in dados:
        porDS.setdefault(r["ds"], []).append(r)

    nav, blocos = [], []
    for ds in sorted(porDS, key=lambda d: (0 if d.startswith("BI_AGR") else 1, d)):
        regs = sorted(porDS[ds], key=lambda r: (r["status"] != "ok", r["table"], r["name"]))
        nav.append(f'<button onclick="fDS(this,\'{ds}\')">{ds} <i>{len(regs)}</i></button>')
        cards = ""
        for r in regs:
            scl, stxt = STBADGE.get(r["status"], ("s-err", r["status"]))
            dax = html.escape(fmap.get((r["table"], r["name"]), "(formula nao encontrada)"))
            nome = html.escape(f'{r["table"]}.{r["name"]}')
            busca = html.escape(f'{r["table"]} {r["name"]}'.lower(), quote=True)
            valfmt = html.escape(fmt(r["value"]))
            cards += (
                f'<div class="k" data-ds="{ds}" data-st="{r["status"]}" data-b="{busca}">'
                f'<div class="kh"><span class="kn">{nome}</span>'
                f'<span class="bdg {scl}">{stxt}</span></div>'
                f'<div class="kv">{valfmt}</div>'
                f'<details><summary>formula DAX</summary><pre><code>{dax}</code></pre></details>'
                f'</div>')
        blocos.append(f'<section class="ds" id="ds-{ds}"><h2>{ROTULO.get(ds, ds)} '
                      f'<span class="cnt">{len(regs)} medidas</span></h2><div class="kgrid">{cards}</div></section>')

    out = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UMOE — 100% dos KPIs do BI</title>
<style>
:root{{--bg:#0a0e1a;--surf:#121829;--line:#243049;--txt:#e7e7ea;--mut:#8b97b0;--gold:#d4af37;--blue:#3b82f6;--green:#22c55e;--red:#f43f5e;--orange:#f97316}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px}}
header{{padding:20px 30px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:20}}
h1{{font-size:1.25rem;color:#fff}} .sub{{color:var(--mut);font-size:.82rem;margin-top:4px}}
.tot{{display:flex;gap:14px;margin-top:10px;flex-wrap:wrap}}
.tot div{{background:var(--surf);border:1px solid var(--line);border-radius:9px;padding:7px 13px;font-size:.78rem}}
.tot b{{font-size:1.1rem;color:var(--gold);display:block}}
.ctrl{{padding:12px 30px;border-bottom:1px solid var(--line);position:sticky;top:120px;background:var(--bg);z-index:19}}
#q{{width:100%;max-width:520px;padding:10px 13px;border-radius:9px;border:1px solid var(--line);background:var(--surf);color:#fff}}
.chips{{margin-top:9px;display:flex;gap:6px;flex-wrap:wrap}}
.chips button{{background:var(--surf);border:1px solid var(--line);color:var(--mut);border-radius:16px;padding:4px 11px;font-size:.72rem;cursor:pointer}}
.chips button.on,.chips button:hover{{border-color:var(--gold);color:var(--gold)}}
.chips button i{{font-style:normal;opacity:.55;margin-left:3px}}
main{{padding:8px 30px 60px}}
.ds h2{{font-size:.92rem;color:var(--gold);text-transform:uppercase;letter-spacing:.7px;padding:14px 0 8px}}
.ds h2 .cnt{{color:var(--mut);font-size:.72rem;font-weight:400;margin-left:6px}}
.kgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:12px}}
.k{{background:var(--surf);border:1px solid var(--line);border-radius:11px;padding:13px 15px}}
.kh{{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:6px}}
.kn{{font-size:.74rem;color:var(--mut);word-break:break-word;line-height:1.3}}
.kv{{font-size:1.5rem;font-weight:800;color:#fff;margin:2px 0 8px;word-break:break-word}}
.bdg{{font-size:.58rem;font-weight:700;padding:2px 7px;border-radius:11px;white-space:nowrap;flex-shrink:0}}
.s-ok{{background:rgba(34,197,94,.14);color:#4ade80}} .s-ctx{{background:rgba(249,115,22,.14);color:#fb923c}}
.s-pes{{background:rgba(234,179,8,.14);color:#fde047}} .s-err{{background:rgba(244,63,94,.15);color:#fda4b4}}
details summary{{cursor:pointer;color:var(--mut);font-size:.68rem;user-select:none}}
details pre{{background:#0b1120;border:1px solid var(--line);border-radius:7px;padding:9px;margin-top:7px;overflow-x:auto}}
details code{{font-family:'Cascadia Code',monospace;font-size:.7rem;color:#cbd5e1;white-space:pre-wrap;word-break:break-word}}
.none{{color:var(--mut);padding:30px;text-align:center;display:none}}
.foot{{color:var(--mut);font-size:.72rem;padding:16px 30px;border-top:1px solid var(--line);text-align:center}}
</style></head><body>
<header>
  <h1>UMOE BIOENERGY — 100% dos KPIs do BI</h1>
  <div class="sub">Todas as medidas do modelo, com o valor que a propria BI calcula (ao vivo via API) | {HOJE}</div>
  <div class="tot">
    <div><b>{len(dados)}</b>medidas</div>
    <div><b>{n_ok}</b>com valor ao vivo</div>
    <div><b>{len(porDS)}</b>datasets</div>
  </div>
</header>
<div class="ctrl">
  <input id="q" placeholder="Buscar KPI... (ex: ATR, moagem, disponibilidade, custo)" oninput="filtra()">
  <div class="chips" id="cSt">
    <button class="on" onclick="fSt(this,'')">Todos status</button>
    <button onclick="fSt(this,'ok')">Ao vivo</button>
    <button onclick="fSt(this,'contexto')">Precisa filtro</button>
    <button onclick="fSt(this,'pesada')">Pesadas</button>
    <button onclick="fSt(this,'erro')">Nao avaliavel</button>
  </div>
  <div class="chips" id="cDS">
    <button class="on" onclick="fDS(this,'')">Todos datasets</button>
    {''.join(nav)}
  </div>
</div>
<main>{''.join(blocos)}<div class="none" id="none">Nenhum KPI encontrado.</div></main>
<div class="foot">UMOE OS 8.0 | 100% das medidas avaliadas ao vivo no Power BI | "precisa filtro" = medida desenhada p/ um visual especifico</div>
<script>
var fq="",fst="",fds="";
function fSt(b,s){{document.querySelectorAll('#cSt button').forEach(x=>x.classList.remove('on'));b.classList.add('on');fst=s;filtra();}}
function fDS(b,d){{document.querySelectorAll('#cDS button').forEach(x=>x.classList.remove('on'));b.classList.add('on');fds=d;filtra();}}
function filtra(){{
  fq=(document.getElementById('q').value||'').toLowerCase().trim();var vis=0;
  document.querySelectorAll('.k').forEach(function(el){{
    var ok=true;
    if(fst&&el.dataset.st!==fst)ok=false;
    if(fds&&el.dataset.ds!==fds)ok=false;
    if(fq&&el.dataset.b.indexOf(fq)<0)ok=false;
    el.style.display=ok?'':'none';if(ok)vis++;
  }});
  document.querySelectorAll('.ds').forEach(function(s){{
    s.style.display=s.querySelectorAll('.k:not([style*="none"])').length?'':'none';}});
  document.getElementById('none').style.display=vis?'none':'block';
}}
</script></body></html>"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "UMOE_KPIs_BI.html").write_text(out, encoding="utf-8")
    print(f"OK -> {OUT} ({OUT.stat().st_size//1024} KB) | {len(dados)} medidas ({n_ok} ao vivo) | +docs/")

if __name__ == "__main__":
    main()
