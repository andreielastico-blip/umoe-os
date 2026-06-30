# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Dashboard Espelho do BI
Cada KPI e calculado com a REGRA DAX OFICIAL exata extraida do Power BI
(Dados-PBI/MEDIDAS_DAX_*.json) e exibe a propria formula ao lado. 100% fiel.

Regras-fonte (verbatim do BI):
  ATR safra  = SUM(KG_ACUCAR)/SUM(QT_CANA_ENT)  janela safra, denom KG_ACUCAR>0
  TAH        = (SUM(ACUCAR)/SUM(CANA_ACUCAR)) * (SUM(TON)/SUM(AREA_CTT)) / 1000
  TCH real   = SUM(PRD_REAL)/SUM(AREA_REESTIMADA3)
  TCH est    = SUM(PRD_ESTIMADA)/SUM(AREA_ESTIMADA)
  Moagem     = SUM(CTT_HISTPRD[QT_CANA_ENT]) janela safra
  Chuva med  = SUM(QTDE)/SUM(DIAS_COM_CHUVA)
  Disponib.  = medida oficial [Disponibilidade (%)] (json refresh mensal)

Saida: UMOE-OS-8.0/Relatorios/UMOE_Dashboard_BI.html (+ docs/)
"""
import json, glob, html
from pathlib import Path
from datetime import datetime, date

try:
    import pandas as pd
except ImportError:
    import os; os.system("pip install pandas -q"); import pandas as pd

ROOT = Path(__file__).parent.parent.parent
PBI  = ROOT / "UMOE-OS-8.0" / "Dados-PBI"
OUT  = ROOT / "UMOE-OS-8.0" / "Relatorios" / "UMOE_Dashboard_BI.html"
DOCS = ROOT / "docs"
HOJE = datetime.now().strftime("%d/%m/%Y %H:%M")
DT_SAFRA_INI = date(2026, 3, 6)   # DAX: DT_SAFRA_INI = DATE(2026,3,6)

# parametros SSoT
META_MOAGEM = 2_768_000
META_ATR    = 138.66
PRECO_ATR   = 1.03

def load(name, manut=False):
    p = (PBI / "MANUT" / f"{name}.json") if manut else (PBI / f"{name}.json")
    if not p.exists():
        return pd.DataFrame()
    try:
        d = json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return pd.DataFrame()
    if not d:
        return pd.DataFrame()
    df = pd.DataFrame(d)
    df.columns = [c.split("[")[-1].rstrip("]") if "[" in c else c for c in df.columns]
    return df

def num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)

def dts(s):
    return pd.to_datetime(s, errors="coerce")

def br(v, dec=0):
    try:
        s = f"{float(v):,.{dec}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "-"

def maxdate(df, col):
    if df.empty or col not in df.columns:
        return None
    d = dts(df[col]).dropna()
    d = d[d <= pd.Timestamp(date.today())]
    return d.max().date().isoformat() if len(d) else None

# ── KPIs calculados com a regra DAX oficial ──────────────────────────────────
print("[1/3] Calculando KPIs com regras DAX oficiais...")
KPIS = []   # cada item: (tema, label, valor_fmt, sub, dax, fonte, cor)

# --- MOAGEM (CTT_HISTPRD, janela safra) ---
his = load("BASE_CTT_HISTPRD")
moagem = atr_safra = None
if not his.empty:
    h = his.copy()
    h["DT"] = dts(h["DT_HISTORICO"])
    jan = h[(h["DT"] >= pd.Timestamp(DT_SAFRA_INI)) & (h["DT"] <= pd.Timestamp(date.today()))]
    moagem = num(jan["QT_CANA_ENT"]).sum()
    # ATR oficial: SUM(KG_ACUCAR)/SUM(QT_CANA_ENT com KG_ACUCAR>0)
    kg = num(jan["KG_ACUCAR"]).sum()
    den = num(jan.loc[num(jan["KG_ACUCAR"]) > 0, "QT_CANA_ENT"]).sum()
    atr_safra = (kg / den) if den else None

freshness = maxdate(his, "DT_HISTORICO")

if moagem is not None:
    pct = moagem / META_MOAGEM * 100
    KPIS.append(("Producao", "Moagem acumulada (safra)", br(moagem) + " t",
                 f"{br(pct,1)}% da meta {br(META_MOAGEM)} t",
                 "SUM(CTT_HISTPRD[QT_CANA_ENT])  // janela safra (DT>=06/03/2026)",
                 "CTT_HISTPRD", "verde" if pct >= 90 else ("amarelo" if pct >= 70 else "vermelho")))
if atr_safra is not None:
    KPIS.append(("Producao", "ATR safra (ponderado por t)", br(atr_safra, 2) + " kg/t",
                 f"meta safra {br(META_ATR,2)} kg/t",
                 "DIVIDE( SUM(CTT_HISTPRD[KG_ACUCAR]) , SUM(CTT_HISTPRD[QT_CANA_ENT]) )  // KG_ACUCAR>0, janela safra",
                 "CTT_HISTPRD", "verde" if atr_safra >= META_ATR*0.9 else "amarelo"))

# --- TCH (CTT_TCH) ---
tch = load("BASE_CTT_TCH")
if not tch.empty:
    tch_real = num(tch["PRD_REAL"]).sum() / max(num(tch["AREA_REESTIMADA3"]).sum(), 1e-9)
    tch_est  = num(tch["PRD_ESTIMADA"]).sum() / max(num(tch["AREA_ESTIMADA"]).sum(), 1e-9)
    KPIS.append(("Produtividade", "TCH real", br(tch_real, 1) + " t/ha",
                 f"estimado {br(tch_est,1)} t/ha",
                 "DIVIDE( SUM(CTT_TCH[PRD_REAL]) , SUM(CTT_TCH[AREA_REESTIMADA3]) )",
                 "CTT_TCH", "verde" if tch_real >= tch_est else "amarelo"))

# --- TAH (CTT_TAH) ---
tah = load("BASE_CTT_TAH")
if not tah.empty:
    conc = num(tah["ACUCAR"]).sum() / max(num(tah["CANA_ACUCAR"]).sum(), 1e-9)
    prod = num(tah["TON"]).sum() / max(num(tah["AREA_CTT"]).sum(), 1e-9)
    tah_val = conc * prod / 1000
    KPIS.append(("Produtividade", "TAH (t ATR/ha)", br(tah_val, 2),
                 f"produtividade {br(prod,1)} t/ha",
                 "( DIVIDE(SUM(CTT_TAH[ACUCAR]),SUM(CTT_TAH[CANA_ACUCAR])) * DIVIDE(SUM(CTT_TAH[TON]),SUM(CTT_TAH[AREA_CTT])) ) / 1000",
                 "CTT_TAH", "verde"))

# --- CHUVA: medida QTDE_CHUVA_MED existe no BI, mas a tabela CHUVA extraida vem
#     com QTDE zerado (a fonte OFICIAL de chuva e o Excel pluviometrico externo,
#     tratado pelo clima-engine). Nao exibimos aqui para nao mostrar valor falso. ---
chu = load("BASE_CHUVA")
if not chu.empty and "QTDE" in chu.columns and num(chu["QTDE"]).sum() > 0:
    dccol = "DIAS_COM_CHUVA" if "DIAS_COM_CHUVA" in chu.columns else None
    if dccol and num(chu[dccol]).sum() > 0:
        cmed = num(chu["QTDE"]).sum() / num(chu[dccol]).sum()
        KPIS.append(("Clima", "Chuva media por dia com chuva", br(cmed, 1) + " mm",
                     "fonte CHUVA (BI)",
                     "DIVIDE( SUM(CHUVA[QTDE]) , SUM(CHUVA[DIAS_COM_CHUVA]) )",
                     "CHUVA", "info"))

# --- DISPONIBILIDADE (medida oficial, json) ---
dispf = PBI / "MANUT" / "disponibilidade_oficial.json"
if dispf.exists():
    try:
        dj = json.load(open(dispf, encoding="utf-8-sig"))
        g = dj.get("geral", {})
        if g.get("disp") is not None:
            d = float(g["disp"]); m = float(g.get("meta") or 0)
            KPIS.append(("Frota", "Disponibilidade da frota", br(d, 1) + "%",
                         f"meta {br(m,1)}%",
                         "[Disponibilidade (%)] = HORAS_DISPONIVEIS / HORAS  (medida oficial Manutencao)",
                         "umoe_dataset", "verde" if d >= m else "vermelho"))
    except Exception:
        pass

# ── tabelas analiticas (mesma regra, por dimensao) ───────────────────────────
print("[2/3] Tabelas analiticas (variedades, maturacao)...")

# TAH por variedade (mesma formula, agrupada)
var_rows = ""
if not tah.empty:
    g = tah.groupby("DE_VARIED").agg(ac=("ACUCAR", lambda s: num(s).sum()),
        ca=("CANA_ACUCAR", lambda s: num(s).sum()), ton=("TON", lambda s: num(s).sum()),
        area=("AREA_CTT", lambda s: num(s).sum())).reset_index()
    g["TAH"] = (g["ac"]/g["ca"].replace(0, 1e-9)) * (g["ton"]/g["area"].replace(0, 1e-9)) / 1000
    g["TCH"] = g["ton"]/g["area"].replace(0, 1e-9)
    g = g[g["area"] > 0].sort_values("TAH", ascending=False).head(15)
    for _, r in g.iterrows():
        var_rows += (f"<tr><td>{html.escape(str(r['DE_VARIED']))}</td><td>{br(r['TAH'],2)}</td>"
                     f"<td>{br(r['TCH'],1)}</td><td>{br(r['area'],0)}</td></tr>")

# ATR por maturacao (mesma regra ATR, agrupada)
mat_rows = ""
if not his.empty and "DE_MATURAC" in his.columns:
    hj = his.copy(); hj["DT"] = dts(hj["DT_HISTORICO"])
    hj = hj[(hj["DT"] >= pd.Timestamp(DT_SAFRA_INI)) & (hj["DT"] <= pd.Timestamp(date.today()))]
    for mt, sub in hj.groupby("DE_MATURAC"):
        kg = num(sub["KG_ACUCAR"]).sum()
        den = num(sub.loc[num(sub["KG_ACUCAR"]) > 0, "QT_CANA_ENT"]).sum()
        ton = num(sub["QT_CANA_ENT"]).sum()
        if den:
            mat_rows += f"<tr><td>{html.escape(str(mt))}</td><td>{br(kg/den,2)}</td><td>{br(ton,0)}</td></tr>"

# ── HTML ─────────────────────────────────────────────────────────────────────
print("[3/3] Gerando HTML...")
try:
    fresh_fmt = datetime.strptime(freshness, "%Y-%m-%d").strftime("%d/%m/%Y") if freshness else "-"
except Exception:
    fresh_fmt = "-"
temas = {}
for tema, lab, val, sub, dax, fonte, cor in KPIS:
    temas.setdefault(tema, []).append((lab, val, sub, dax, fonte, cor))

cards_html = ""
for tema, items in temas.items():
    cards_html += f'<h2 class="tema">{tema}</h2><div class="kpis">'
    for lab, val, sub, dax, fonte, cor in items:
        cards_html += (
            f'<div class="kpi {cor}">'
            f'<div class="lab">{html.escape(lab)}</div>'
            f'<div class="val">{html.escape(val)}</div>'
            f'<div class="sub">{html.escape(sub)}</div>'
            f'<div class="dax"><span class="tag">regra do BI</span><code>{html.escape(dax)}</code></div>'
            f'</div>')
    cards_html += "</div>"

html_out = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UMOE — Dashboard Espelho do BI</title>
<style>
:root{{--bg:#0a0e1a;--surf:#121829;--line:#243049;--txt:#e7e7ea;--mut:#8b97b0;--gold:#d4af37;--blue:#3b82f6;--green:#22c55e;--red:#f43f5e}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px}}
header{{padding:22px 32px;border-bottom:1px solid var(--line)}}
h1{{font-size:1.3rem;color:#fff}} .sub{{color:var(--mut);font-size:.82rem;margin-top:4px}}
.banner{{margin-top:12px;background:rgba(212,175,55,.1);border:1px solid rgba(212,175,55,.35);border-radius:10px;padding:10px 14px;font-size:.82rem;color:#e6d28a}}
main{{padding:14px 32px 60px}}
.tema{{color:var(--gold);font-size:.95rem;text-transform:uppercase;letter-spacing:.8px;margin:26px 0 12px;border-bottom:1px solid var(--line);padding-bottom:8px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:16px}}
.kpi{{background:var(--surf);border:1px solid var(--line);border-radius:14px;padding:18px 20px;border-left:4px solid var(--blue)}}
.kpi.verde{{border-left-color:var(--green)}} .kpi.amarelo{{border-left-color:var(--gold)}} .kpi.vermelho{{border-left-color:var(--red)}} .kpi.info{{border-left-color:var(--blue)}}
.lab{{color:var(--mut);font-size:.75rem;text-transform:uppercase;letter-spacing:.6px;font-weight:600}}
.val{{font-size:2rem;font-weight:800;color:#fff;margin:6px 0 2px}}
.sub{{color:var(--mut);font-size:.8rem;margin-bottom:12px}}
.dax{{background:#0b1120;border:1px solid var(--line);border-radius:8px;padding:9px 11px}}
.dax .tag{{display:inline-block;font-size:.6rem;font-weight:700;color:#4ade80;background:rgba(34,197,94,.13);border-radius:10px;padding:2px 7px;margin-bottom:6px}}
.dax code{{display:block;font-family:'Cascadia Code','Consolas',monospace;font-size:.72rem;color:#cbd5e1;white-space:pre-wrap;word-break:break-word;line-height:1.45}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:18px}}
@media(max-width:760px){{.grid2{{grid-template-columns:1fr}}}}
.card{{background:var(--surf);border:1px solid var(--line);border-radius:14px;padding:18px 20px}}
.card h3{{font-size:.82rem;color:var(--gold);text-transform:uppercase;letter-spacing:.7px;margin-bottom:6px}}
.card .rule{{font-family:monospace;font-size:.68rem;color:var(--mut);margin-bottom:12px;word-break:break-word}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th{{text-align:left;color:var(--mut);font-size:.68rem;text-transform:uppercase;padding:7px 9px;border-bottom:1px solid var(--line)}}
td{{padding:7px 9px;border-bottom:1px solid #16213d}}
.foot{{color:var(--mut);font-size:.72rem;padding:18px 32px;border-top:1px solid var(--line);text-align:center}}
a{{color:var(--gold)}}
</style></head><body>
<header>
  <h1>UMOE BIOENERGY — Dashboard Espelho do BI</h1>
  <div class="sub">Safra 2026/27 | cada KPI usa a REGRA DAX OFICIAL extraida do Power BI | gerado {HOJE}</div>
  <div class="banner">100% fiel ao BI: todo numero abaixo e calculado com a formula DAX exata do modelo (mostrada em cada card).
     Dados ate <b>{fresh_fmt}</b> (origem). Catalogo completo: <a href="UMOE_Catalogo_DAX.html">UMOE_Catalogo_DAX.html</a></div>
</header>
<main>
  {cards_html}
  <div class="grid2">
    <div class="card"><h3>Top variedades por TAH</h3>
      <div class="rule">(ACUCAR/CANA_ACUCAR)*(TON/AREA_CTT)/1000 — por DE_VARIED</div>
      <table><tr><th>Variedade</th><th>TAH</th><th>TCH</th><th>Area (ha)</th></tr>{var_rows or '<tr><td colspan=4>sem dados</td></tr>'}</table></div>
    <div class="card"><h3>ATR por maturacao</h3>
      <div class="rule">SUM(KG_ACUCAR)/SUM(QT_CANA_ENT) — por DE_MATURAC, janela safra</div>
      <table><tr><th>Maturacao</th><th>ATR (kg/t)</th><th>Cana (t)</th></tr>{mat_rows or '<tr><td colspan=3>sem dados</td></tr>'}</table></div>
  </div>
</main>
<div class="foot">UMOE OS 8.0 | Dashboard Espelho do BI | regras DAX verbatim do modelo semantico | {len(KPIS)} KPIs oficiais</div>
</body></html>"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html_out, encoding="utf-8")
DOCS.mkdir(parents=True, exist_ok=True)
(DOCS / "UMOE_Dashboard_BI.html").write_text(html_out, encoding="utf-8")
print(f"OK -> {OUT} ({OUT.stat().st_size//1024} KB) | {len(KPIS)} KPIs oficiais | +docs/")
