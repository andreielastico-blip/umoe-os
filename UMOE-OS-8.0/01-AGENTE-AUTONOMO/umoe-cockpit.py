# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Cockpit Executivo da Safra 2026/27
Dashboard executivo profissional: KPIs vs meta, tendencias, comparativos,
cruzamentos e conclusoes concretas — tudo a partir dos dados reais extraidos
do Power BI (UMOE-OS-8.0/Dados-PBI/*.json).

Saida: UMOE-OS-8.0/Relatorios/UMOE_Cockpit_Executivo.html (+ copia em docs/)
"""
import json, sys
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd, numpy as np
except ImportError:
    import os; os.system("pip install pandas numpy -q"); import pandas as pd, numpy as np
import warnings; warnings.filterwarnings("ignore")

ROOT    = Path(__file__).parent.parent.parent
PBI_DIR = ROOT / "UMOE-OS-8.0" / "Dados-PBI"
OUT     = ROOT / "UMOE-OS-8.0" / "Relatorios" / "UMOE_Cockpit_Executivo.html"
DOCS    = ROOT / "docs"
HOJE    = datetime.now().strftime("%d/%m/%Y")

# ── Metas / parametros (SSoT UMOE 2026/27) ───────────────────────────────────
META_MOAGEM   = 2_768_000      # t safra 26/27
META_ATR      = 138.66         # kg/t
PRECO_ATR     = 1.03           # R$/kg CONSECANA

def load(name):
    """Carrega BASE_/CST_/CTRL_ JSON em DataFrame, limpando prefixo Tabela[Col]."""
    p = PBI_DIR / f"{name}.json"
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

def br(v, dec=0):
    """Formata numero no padrao BR (1.234,5)."""
    try:
        s = f"{float(v):,.{dec}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "-"

print("[1/4] Carregando dados PBI...")
moa  = load("BASE_CTT_META_MOAGEM")
atrh = load("BASE_CTT_HISTPRD_ATR_HIST")
tch  = load("BASE_CTT_TCH")
tah  = load("BASE_CTT_TAH")
ind  = load("BASE_CTT_INDISPONIB")
cst  = load("CST_CST")
mat  = load("BASE_CTT_MATURADOR")
his  = load("BASE_CTT_HISTPRD")     # PRODUCAO REALIZADA (safra atual)
print(f"  realizado(HISTPRD)={len(his)} meta(MOAGEM)={len(moa)} tch={len(tch)} tah={len(tah)} indisp={len(ind)} custo={len(cst)}")

print("[2/4] Calculando metricas...")
K = {}   # KPIs
charts = {}
insights = []

# ── MOAGEM & ATR REALIZADOS (fonte: CTT_HISTPRD, safra 26/27) ───────────────
# Validado vs SSoT: mar-mai = 606.418 t e ATR ~126 kg/t.
moa_mensal = pd.DataFrame()
atr_mat = pd.DataFrame(); atr_var = pd.DataFrame(); atr_dia = pd.DataFrame(); atr_corte = pd.DataFrame()
if not his.empty:
    his["QT_CANA_ENT"] = num(his.get("QT_CANA_ENT", 0))
    his["KG_ACUCAR"]   = num(his.get("KG_ACUCAR", 0))
    his["DT"]          = pd.to_datetime(his.get("DT_HISTORICO"), errors="coerce")
    base = his[his["QT_CANA_ENT"] > 0].copy()
    tot_cana = base["QT_CANA_ENT"].sum()
    K["moagem_total"] = float(tot_cana)
    K["atend_meta"]   = tot_cana / META_MOAGEM * 100 if META_MOAGEM else 0
    K["atr_pond"]     = (base["KG_ACUCAR"].sum() / tot_cana) if tot_cana else 0
    K["dt_ini"] = str(base["DT"].min().date()) if base["DT"].notna().any() else ""
    K["dt_fim"] = str(base["DT"].max().date()) if base["DT"].notna().any() else ""

    # Tendencia mensal: moagem + ATR
    base["AM"] = base["DT"].dt.strftime("%Y-%m")
    g = base.dropna(subset=["DT"]).groupby("AM").agg(
        TON=("QT_CANA_ENT","sum"), AC=("KG_ACUCAR","sum")).reset_index()
    g["ATR"] = np.where(g["TON"]>0, g["AC"]/g["TON"], 0)
    moa_mensal = g.sort_values("AM")
    charts["moagem_mes"] = [{"MES": r["AM"], "TON": float(r["TON"]), "ATR": float(r["ATR"])} for _,r in moa_mensal.iterrows()]

    # ATR diario (todos os dias da safra)
    dd = base.dropna(subset=["DT"]).groupby(base["DT"].dt.date).apply(
        lambda x: x["KG_ACUCAR"].sum()/x["QT_CANA_ENT"].sum()).reset_index()
    dd.columns = ["dia","ATR"]; atr_dia = dd.sort_values("dia")
    charts["atr_dia"] = [{"dia": str(r["dia"]), "ATR": float(r["ATR"])} for _,r in atr_dia.iterrows()]

    def por(col):
        gg = base.groupby(col).apply(lambda x: pd.Series({
            "ATR": x["KG_ACUCAR"].sum()/x["QT_CANA_ENT"].sum(),
            "TON": x["QT_CANA_ENT"].sum()})).reset_index()
        return gg
    if "DE_MATURAC" in base.columns:
        atr_mat = por("DE_MATURAC").sort_values("ATR", ascending=False)
        charts["atr_mat"] = atr_mat.to_dict("records")
    if "DE_VARIED" in base.columns:
        av = por("DE_VARIED"); av = av[av["TON"] > tot_cana*0.005]
        atr_var = av.sort_values("ATR", ascending=False)
    if "ESTAGIO_CORTE" in base.columns:
        atr_corte = por("ESTAGIO_CORTE").sort_values("TON", ascending=False)

# ── TCH / TAH / VARIEDADES ──────────────────────────────────────────────────
tch_estagio = pd.DataFrame(); tah_var = pd.DataFrame()
if not tch.empty:
    tch["AREA_ESTIMADA"] = num(tch.get("AREA_ESTIMADA",0))
    tch["PRD_REAL"] = num(tch.get("PRD_REAL",0))
    tch["PRD_ESTIMADA"] = num(tch.get("PRD_ESTIMADA",0))
    col_est = "ESTAGIO_AGRUP" if "ESTAGIO_AGRUP" in tch.columns else ("ESTAGIO_CORTE" if "ESTAGIO_CORTE" in tch.columns else None)
    if col_est:
        g = tch.groupby(col_est).agg(AREA=("AREA_ESTIMADA","sum"),
                                     PRD_REAL=("PRD_REAL","sum"),
                                     PRD_EST=("PRD_ESTIMADA","sum")).reset_index()
        g["TCH_REAL"] = np.where(g["AREA"]>0, g["PRD_REAL"]/g["AREA"], 0)
        g["TCH_EST"]  = np.where(g["AREA"]>0, g["PRD_EST"]/g["AREA"], 0)
        tch_estagio = g[g["AREA"]>0].sort_values(col_est)
        tch_estagio = tch_estagio.rename(columns={col_est:"ESTAGIO"})
        charts["tch_estagio"] = tch_estagio.to_dict("records")
if not tah.empty:
    tah["AREA_CTT"] = num(tah.get("AREA_CTT",0))
    tah["ACUCAR"]   = num(tah.get("ACUCAR",0))
    tah["TON"]      = num(tah.get("TON",0))
    if "DE_VARIED" in tah.columns:
        g = tah.groupby("DE_VARIED").agg(AREA=("AREA_CTT","sum"),
                                         ACUCAR=("ACUCAR","sum"),
                                         TON=("TON","sum")).reset_index()
        g["TAH"] = np.where(g["AREA"]>0, g["ACUCAR"]/g["AREA"]/1000.0, 0)  # kg/ha -> t ATR/ha
        g["TCH"] = np.where(g["AREA"]>0, g["TON"]/g["AREA"], 0)
        g = g[g["AREA"] > g["AREA"].sum()*0.01]
        tah_var = g.sort_values("TAH", ascending=False)

# ── CUSTOS ──────────────────────────────────────────────────────────────────
cst_grupo = pd.DataFrame()
if not cst.empty:
    cst["VL_ORC"]  = num(cst.get("VL_ORC",0))
    cst["VL_REAL"] = num(cst.get("VL_REAL",0))
    if "DT_REFER" in cst.columns:   # foca no ano corrente (2026)
        _dt = pd.to_datetime(cst["DT_REFER"], errors="coerce")
        cst = cst[_dt.dt.year == 2026]
    if "DE_GRUPO" in cst.columns and not cst.empty:
        g = cst.groupby("DE_GRUPO").agg(ORC=("VL_ORC","sum"), REAL=("VL_REAL","sum")).reset_index()
        g["DESVIO"] = g["REAL"] - g["ORC"]
        g["DESVIO_PCT"] = np.where(g["ORC"]>0, g["DESVIO"]/g["ORC"]*100, 0)
        cst_grupo = g.sort_values("REAL", ascending=False).head(12)
        K["custo_real"] = float(g["REAL"].sum())
        K["custo_orc"]  = float(g["ORC"].sum())

# ── CHUVA (fonte oficial: Excel Indice Pluviometrico, aba HISTORICO) ─────────
import glob as _glob
chuva_ano = pd.DataFrame(); chuva_mes = pd.DataFrame()
try:
    pl = r"C:\01 - UMOE\03 - Financeiro\Planilhas\1 - Indice Pluviometrico UMOE.xlsx"
    if Path(pl).exists():
        ch = pd.read_excel(pl, sheet_name="HISTORICO")
        ch.columns = [str(c).strip().upper() for c in ch.columns]
        qt = next((c for c in ch.columns if "LEITURA" in c), None)
        if qt and "ANO" in ch.columns:
            ch[qt] = num(ch[qt])
            dcol = next((c for c in ch.columns if c=="DATA"), None)
            ch["_M"] = pd.to_datetime(ch[dcol], errors="coerce").dt.month if dcol else 0
            # total anual (para o grafico de tendencia)
            ga = ch.groupby("ANO")[qt].sum().reset_index().rename(columns={qt:"MM"})
            ga = ga[(ga["ANO"]>=2015) & (ga["ANO"]<=2030)]
            chuva_ano = ga.sort_values("ANO")
            charts["chuva_ano"] = [{"ANO": int(r["ANO"]), "MM": float(r["MM"])} for _,r in chuva_ano.iterrows()]
            # YTD: mesmo periodo (ate o ultimo mes com dado em 2026) para comparacao justa
            mes_atual = int(ch[ch["ANO"]==2026]["_M"].max()) if (ch["ANO"]==2026).any() else 12
            ytd = ch[ch["_M"]<=mes_atual].groupby("ANO")[qt].sum()
            K["chuva_ano_atual"] = float(ytd.get(2026, 0))
            hist_ytd = ytd[(ytd.index>=2015) & (ytd.index<2026)]
            K["chuva_media"] = float(hist_ytd.mean()) if len(hist_ytd) else 0
            K["chuva_ytd_mes"] = mes_atual
            mcol = next((c for c in ch.columns if c in ("MÊS","MES")), None)
            if mcol:
                gm = ch[ch["ANO"]==2026].groupby(mcol)[qt].sum().reset_index().rename(columns={qt:"MM",mcol:"MES"})
                chuva_mes = gm
                charts["chuva_mes"] = [{"MES": str(r["MES"]), "MM": float(r["MM"])} for _,r in gm.iterrows()]
except Exception as e:
    print("  chuva: erro", e)

# ── VARIEDADES (historico BD SAFRAS, 8 safras) ───────────────────────────────
var_hist = pd.DataFrame(); var_amb = pd.DataFrame()
try:
    bds = _glob.glob(r"C:\01 - UMOE\03 - Financeiro\Planilhas\Historico Kpis*Agr*.xlsx")
    if bds:
        wb = pd.ExcelFile(bds[0])
        sh = next((s for s in wb.sheet_names if "BD" in s.upper() and "SAFRA" in s.upper()), wb.sheet_names[0])
        bd = wb.parse(sh, header=0)
        # mapeamento por posicao (umoe-bi-enterprise): 0=Amb,1=Faz,5=Var,7=Area,11=TCH,16=ATR,17=TAH,21=Safra,24=Corte
        cols = list(bd.columns)
        def col(i): return cols[i] if i < len(cols) else None
        bd = bd.rename(columns={col(0):"AMB",col(1):"FAZ",col(5):"VAR",col(7):"AREA",
                                col(11):"TCH",col(16):"ATR",col(17):"TAH",col(21):"SAFRA",col(24):"CORTE"})
        for c in ["AREA","TCH","ATR","TAH"]:
            if c in bd.columns: bd[c] = num(bd[c])
        bd = bd[(bd.get("AREA",0)>0.5) & (bd.get("TCH",0)>10) & (bd.get("TAH",0)>0.5)]
        if "VAR" in bd.columns and not bd.empty:
            g = bd.groupby("VAR").apply(lambda x: pd.Series({
                "TAH": (x["TAH"]*x["AREA"]).sum()/x["AREA"].sum(),
                "TCH": (x["TCH"]*x["AREA"]).sum()/x["AREA"].sum(),
                "AREA": x["AREA"].sum()})).reset_index()
            g = g[g["AREA"] > g["AREA"].sum()*0.005]
            var_hist = g.sort_values("TAH", ascending=False)
            charts["var_hist"] = var_hist.head(15).to_dict("records")
        if "VAR" in bd.columns and "AMB" in bd.columns and not bd.empty:
            bd["AMB1"] = bd["AMB"].astype(str).str[:1]
            ga = bd[bd["AMB1"].str.len()==1].groupby(["VAR","AMB1"]).apply(
                lambda x: pd.Series({"TAH": (x["TAH"]*x["AREA"]).sum()/x["AREA"].sum(),
                                     "AREA": x["AREA"].sum()})).reset_index()
            var_amb = ga[ga["AREA"]>300].sort_values("TAH", ascending=False)
        K["var_safras"] = int(bd["SAFRA"].nunique()) if "SAFRA" in bd.columns else 0
        K["var_registros"] = int(len(bd))
except Exception as e:
    print("  bd_safras: erro", e)

# ── LOGISTICA / CARGAS (cana queimada, KM medio) ─────────────────────────────
carga_kpi = {}
try:
    cg = load("BASE_CTT_CARGAS_ENTRADA")
    if not cg.empty:
        cg["QT_CARGA"] = num(cg.get("QT_CARGA",0)); cg["KM_POND"] = num(cg.get("KM_POND",0)); cg["TON_ESTIM"]=num(cg.get("TON_ESTIM",0))
        tot = cg["TON_ESTIM"].sum()
        if "NO_QUEIMA" in cg.columns and tot:
            q = cg.copy(); q["queim"] = q["NO_QUEIMA"].astype(str).str.lower().str.contains("queim")
            carga_kpi["perc_queima"] = float(q[q["queim"]]["TON_ESTIM"].sum()/tot*100)
        if tot:
            carga_kpi["km_medio"] = float((cg["KM_POND"]*cg["TON_ESTIM"]).sum()/tot)
        carga_kpi["cargas"] = int(len(cg))
except Exception as e:
    print("  cargas: erro", e)

# ── PARADAS / INDISPONIBILIDADE ─────────────────────────────────────────────
paradas = pd.DataFrame()
if not ind.empty:
    ind["HORAS_DEC"] = num(ind.get("HORAS_DEC",0))
    col_g = "GRUPO_PARADA" if "GRUPO_PARADA" in ind.columns else ("AGRP_PARADA" if "AGRP_PARADA" in ind.columns else None)
    if col_g:
        g = ind.groupby(col_g)["HORAS_DEC"].sum().reset_index().rename(columns={col_g:"GRUPO","HORAS_DEC":"HORAS"})
        paradas = g[g["HORAS"]>0].sort_values("HORAS", ascending=False).head(10)
        charts["paradas"] = paradas.to_dict("records")

# ── INSIGHTS (conclusoes concretas) ─────────────────────────────────────────
def add(txt, tipo="info"): insights.append({"t": txt, "tipo": tipo})

if "moagem_total" in K:
    sit = "verde" if K["atend_meta"]>=95 else ("amarelo" if K["atend_meta"]>=80 else "vermelho")
    add(f"Moagem acumulada de {br(K['moagem_total'])} t = {br(K['atend_meta'],1)}% da meta safra ({br(META_MOAGEM)} t). "
        f"Gap de {br(META_MOAGEM-K['moagem_total'])} t para o objetivo.", sit)
if "atr_pond" in K and K["atr_pond"]>0:
    d = K["atr_pond"] - META_ATR
    add(f"ATR ponderado em {br(K['atr_pond'],2)} kg/t vs meta {br(META_ATR,2)} kg/t "
        f"({'+' if d>=0 else ''}{br(d,2)} kg/t). A R$ {br(PRECO_ATR,2)}/kg, cada kg/t vale ~R$ {br(K.get('moagem_total',0)*PRECO_ATR/1000)} no acumulado.",
        "verde" if d>=0 else "vermelho")
if not atr_mat.empty:
    top = atr_mat.iloc[0]
    add(f"Maturacao '{top['DE_MATURAC']}' concentra o maior ATR ({br(top['ATR'],1)} kg/t). "
        f"Priorizar colheita por janela de maturacao maximiza acucar.", "info")
if not tah_var.empty:
    b = tah_var.iloc[0]; w = tah_var.iloc[-1]
    add(f"Variedade lider em TAH: {b['DE_VARIED']} ({br(b['TAH'],2)} t ATR/ha). "
        f"Pior relevante: {w['DE_VARIED']} ({br(w['TAH'],2)}). Diferenca de {br(b['TAH']-w['TAH'],2)} t ATR/ha entre extremos.", "info")
if not cst_grupo.empty:
    est = cst_grupo[cst_grupo["DESVIO"]>0].sort_values("DESVIO", ascending=False)
    if not est.empty:
        e = est.iloc[0]
        add(f"Maior estouro de custo: grupo '{e['DE_GRUPO']}' com R$ {br(e['DESVIO'])} acima do orcado "
            f"({'+' if e['DESVIO_PCT']>=0 else ''}{br(e['DESVIO_PCT'],1)}%).", "vermelho")
if not paradas.empty:
    p = paradas.iloc[0]
    add(f"Maior ofensor de paradas: '{p['GRUPO']}' com {br(p['HORAS'],1)} h acumuladas. Foco de ganho de disponibilidade.", "amarelo")
if "chuva_ano_atual" in K and K.get("chuva_media",0)>0:
    d = (K["chuva_ano_atual"]/K["chuva_media"]-1)*100
    mm = K.get("chuva_ytd_mes",12)
    add(f"Chuva 2026 (jan-mes {mm}, YTD): {br(K['chuva_ano_atual'])} mm vs media historica do mesmo periodo {br(K['chuva_media'])} mm "
        f"({'+' if d>=0 else ''}{br(d,0)}%). Clima e o maior ofensor de paradas — correlacao direta com disponibilidade de moagem.",
        "info")
if not var_hist.empty:
    b = var_hist.iloc[0]; w = var_hist.iloc[-1]
    add(f"Historico (8 safras): {b['VAR']} lidera TAH ({br(b['TAH'],2)} t ATR/ha); {w['VAR']} e a pior relevante "
        f"({br(w['TAH'],2)}). Direcionar plantio para as variedades-topo eleva o ATR estrutural.", "info")
if not var_amb.empty:
    top = var_amb.iloc[0]
    add(f"Melhor combinacao variedade x ambiente: {top['VAR']} x Amb.{top['AMB1']} = {br(top['TAH'],2)} t ATR/ha. "
        f"Alocacao por aptidao de ambiente maximiza produtividade.", "verde")

print(f"  KPIs={len(K)} insights={len(insights)}")
print("[3/4] Gerando HTML...")

# ── HTML ─────────────────────────────────────────────────────────────────────
def kpi_card(label, valor, sub="", cor="verde", delta=""):
    return f"""<div class="kpi">
      <div class="kpi-top"><span class="dot {cor}"></span><span class="kpi-label">{label}</span></div>
      <div class="kpi-val">{valor}</div>
      <div class="kpi-sub">{sub} {('<span class=\"delta '+cor+'\">'+delta+'</span>') if delta else ''}</div>
    </div>"""

cards = []
if "moagem_total" in K:
    sit = "verde" if K["atend_meta"]>=95 else ("amarelo" if K["atend_meta"]>=80 else "vermelho")
    cards.append(kpi_card("Moagem acumulada", f"{br(K['moagem_total'])} t",
                          f"meta {br(META_MOAGEM)} t", sit, f"{br(K['atend_meta'],1)}% da meta"))
if "atr_pond" in K and K["atr_pond"]>0:
    d = K["atr_pond"]-META_ATR
    cards.append(kpi_card("ATR ponderado", f"{br(K['atr_pond'],2)} kg/t",
                          f"meta {br(META_ATR,2)} (sobe c/ maturacao)", "verde" if d>=-5 else "amarelo",
                          f"{'+' if d>=0 else ''}{br(d,2)} kg/t"))
if "moagem_total" in K:
    gap = META_MOAGEM - K["moagem_total"]
    cards.append(kpi_card("Gap para a meta", f"{br(gap)} t",
                          f"safra ate {K.get('dt_fim','')}", "amarelo", f"{br(100-K['atend_meta'],1)}% restante"))
if "custo_real" in K:
    dev = (K["custo_real"]-K["custo_orc"])/K["custo_orc"]*100 if K.get("custo_orc") else 0
    cards.append(kpi_card("Custo realizado 2026", f"R$ {br(K['custo_real']/1e6,1)} M",
                          f"orcado R$ {br(K['custo_orc']/1e6,1)} M", "vermelho" if dev>2 else "verde",
                          f"{'+' if dev>=0 else ''}{br(dev,1)}% vs orc"))
if "chuva_ano_atual" in K:
    d = (K["chuva_ano_atual"]/K["chuva_media"]-1)*100 if K.get("chuva_media") else 0
    cards.append(kpi_card("Chuva 2026", f"{br(K['chuva_ano_atual'])} mm",
                          f"media hist. {br(K.get('chuva_media',0))} mm", "info",
                          f"{'+' if d>=0 else ''}{br(d,0)}% vs media"))

def linhas_tabela(df, cols, fmts):
    out = []
    for _, r in df.iterrows():
        tds = "".join(f"<td>{fmts[i](r[c])}</td>" for i,c in enumerate(cols))
        out.append(f"<tr>{tds}</tr>")
    return "".join(out)

ins_html = "".join(
    f'<div class="insight {i["tipo"]}">{i["t"]}</div>' for i in insights
) or '<div class="insight info">Sem dados suficientes para conclusoes.</div>'

# Tabelas
tah_rows = linhas_tabela(tah_var.head(15), ["DE_VARIED","TAH","TCH","AREA"],
                         [str, lambda v:br(v,2), lambda v:br(v,1), lambda v:br(v,0)]) if not tah_var.empty else '<tr><td colspan=4>sem dados</td></tr>'
cst_rows = linhas_tabela(cst_grupo, ["DE_GRUPO","ORC","REAL","DESVIO_PCT"],
                         [str, lambda v:"R$ "+br(v), lambda v:"R$ "+br(v), lambda v:("+" if v>=0 else "")+br(v,1)+"%"]) if not cst_grupo.empty else '<tr><td colspan=4>sem dados</td></tr>'
atrmat_rows = linhas_tabela(atr_mat, ["DE_MATURAC","ATR","TON"],
                         [str, lambda v:br(v,2), lambda v:br(v,0)]) if not atr_mat.empty else '<tr><td colspan=3>sem dados</td></tr>'
varhist_rows = linhas_tabela(var_hist.head(15), ["VAR","TAH","TCH","AREA"],
                         [str, lambda v:br(v,2), lambda v:br(v,1), lambda v:br(v,0)]) if not var_hist.empty else '<tr><td colspan=4>sem dados</td></tr>'
varamb_rows = linhas_tabela(var_amb.head(15), ["VAR","AMB1","TAH","AREA"],
                         [str, str, lambda v:br(v,2), lambda v:br(v,0)]) if not var_amb.empty else '<tr><td colspan=4>sem dados</td></tr>'

html = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UMOE | Cockpit Executivo 2026/27</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#0A0F1E;--surf:#111A30;--surf2:#16213D;--line:#22325C;--txt:#E8EEFC;--mut:#8FA3C8;--green:#22C55E;--gold:#FACC15;--red:#F43F5E;--blue:#3B82F6;--cyan:#22D3EE}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px}}
header{{padding:22px 34px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;background:var(--surf)}}
header h1{{font-size:1.25rem;color:#fff;font-weight:700;letter-spacing:.3px}}
header .sub{{color:var(--mut);font-size:.8rem;margin-top:3px}}
.tag{{background:var(--green);color:#04210f;padding:3px 12px;border-radius:20px;font-size:.72rem;font-weight:700}}
nav{{display:flex;gap:2px;padding:0 28px;background:var(--surf);border-bottom:1px solid var(--line);overflow-x:auto}}
nav button{{background:none;border:0;color:var(--mut);padding:13px 18px;cursor:pointer;font-size:.84rem;font-weight:600;border-bottom:2px solid transparent;white-space:nowrap}}
nav button.on,nav button:hover{{color:#fff;border-bottom-color:var(--gold)}}
.tab{{display:none;padding:26px 34px;max-width:1500px;margin:0 auto}}
.tab.on{{display:block}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-bottom:26px}}
.kpi{{background:var(--surf);border:1px solid var(--line);border-radius:14px;padding:18px 20px}}
.kpi-top{{display:flex;align-items:center;gap:8px;margin-bottom:10px}}
.kpi-label{{color:var(--mut);font-size:.74rem;text-transform:uppercase;letter-spacing:.7px;font-weight:600}}
.kpi-val{{font-size:2rem;font-weight:800;color:#fff;line-height:1.1}}
.kpi-sub{{color:var(--mut);font-size:.78rem;margin-top:6px}}
.dot{{width:9px;height:9px;border-radius:50%}}
.dot.verde{{background:var(--green)}} .dot.amarelo{{background:var(--gold)}} .dot.vermelho{{background:var(--red)}} .dot.info{{background:var(--blue)}}
.delta{{font-weight:700}} .delta.verde{{color:var(--green)}} .delta.amarelo{{color:var(--gold)}} .delta.vermelho{{color:var(--red)}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}}
.grid.one{{grid-template-columns:1fr}}
@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
.card{{background:var(--surf);border:1px solid var(--line);border-radius:14px;padding:20px}}
.card h3{{font-size:.82rem;color:var(--gold);text-transform:uppercase;letter-spacing:.8px;margin-bottom:16px;font-weight:700}}
.chart{{position:relative;height:280px}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th{{text-align:left;color:var(--mut);font-size:.7rem;text-transform:uppercase;letter-spacing:.5px;padding:8px 10px;border-bottom:1px solid var(--line)}}
td{{padding:8px 10px;border-bottom:1px solid #16213d;color:var(--txt)}}
tr:hover td{{background:var(--surf2)}}
.insight{{background:var(--surf2);border-left:3px solid var(--blue);border-radius:0 10px 10px 0;padding:13px 16px;margin-bottom:12px;font-size:.9rem;line-height:1.5}}
.insight.verde{{border-left-color:var(--green)}} .insight.amarelo{{border-left-color:var(--gold)}} .insight.vermelho{{border-left-color:var(--red)}}
.foot{{color:var(--mut);font-size:.72rem;padding:20px 34px;border-top:1px solid var(--line);text-align:center}}
</style></head><body>
<header>
  <div><h1>UMOE BIOENERGY — Cockpit Executivo</h1><div class="sub">Plano Diretor Agricola | Safra 2026/27 | Dados reais Power BI</div></div>
  <div style="text-align:right"><span class="tag">{len(K)} KPIs | dados reais</span><div class="sub">Atualizado {HOJE}</div></div>
</header>
<nav>
  <button class="on" onclick="tab('cockpit',this)">Cockpit</button>
  <button onclick="tab('moagem',this)">Moagem & Eficiencia</button>
  <button onclick="tab('atr',this)">ATR & Qualidade</button>
  <button onclick="tab('varied',this)">Variedades</button>
  <button onclick="tab('chuva',this)">Chuva & Clima</button>
  <button onclick="tab('custos',this)">Custos</button>
  <button onclick="tab('paradas',this)">Disponibilidade</button>
  <button onclick="tab('intel',this)">Inteligencia</button>
</nav>

<div id="t-cockpit" class="tab on">
  <div class="kpis">{''.join(cards) or '<div class="kpi"><div class="kpi-val">sem dados</div></div>'}</div>
  <div class="grid">
    <div class="card"><h3>Moagem mensal (t)</h3><div class="chart"><canvas id="cMoa"></canvas></div></div>
    <div class="card"><h3>ATR por maturacao (kg/t)</h3><table><tr><th>Maturacao</th><th>ATR</th><th>Cana (t)</th></tr>{atrmat_rows}</table></div>
  </div>
  <div class="card"><h3>Conclusoes (calculadas dos dados)</h3>{ins_html}</div>
</div>

<div id="t-moagem" class="tab">
  <div class="grid one"><div class="card"><h3>Moagem mensal — toneladas</h3><div class="chart"><canvas id="cMoa2"></canvas></div></div></div>
</div>

<div id="t-atr" class="tab">
  <div class="grid one"><div class="card"><h3>ATR diario (kg/t) — ultimos 45 dias</h3><div class="chart"><canvas id="cAtr"></canvas></div></div></div>
  <div class="card"><h3>ATR por maturacao</h3><table><tr><th>Maturacao</th><th>ATR (kg/t)</th><th>Cana (t)</th></tr>{atrmat_rows}</table></div>
</div>

<div id="t-varied" class="tab">
  <div class="grid">
    <div class="card"><h3>TCH real vs estimado por estagio</h3><div class="chart"><canvas id="cTch"></canvas></div></div>
    <div class="card"><h3>Top variedades por TAH — safra atual (t ATR/ha)</h3><table><tr><th>Variedade</th><th>TAH</th><th>TCH</th><th>Area (ha)</th></tr>{tah_rows}</table></div>
  </div>
  <div class="grid">
    <div class="card"><h3>Ranking historico de variedades — 8 safras (t ATR/ha)</h3><table><tr><th>Variedade</th><th>TAH</th><th>TCH</th><th>Area (ha)</th></tr>{varhist_rows}</table></div>
    <div class="card"><h3>Melhor variedade x ambiente — historico</h3><table><tr><th>Variedade</th><th>Amb.</th><th>TAH</th><th>Area (ha)</th></tr>{varamb_rows}</table></div>
  </div>
</div>

<div id="t-chuva" class="tab">
  <div class="grid">
    <div class="card"><h3>Chuva anual (mm) — fonte oficial pluviometrica</h3><div class="chart"><canvas id="cChuvaA"></canvas></div></div>
    <div class="card"><h3>Chuva mensal 2026 (mm)</h3><div class="chart"><canvas id="cChuvaM"></canvas></div></div>
  </div>
  <div class="card"><h3>Paradas climaticas vs disponibilidade</h3><div class="chart"><canvas id="cPar2"></canvas></div></div>
</div>

<div id="t-custos" class="tab">
  <div class="card"><h3>Top 12 grupos de custo — orcado vs realizado</h3>
    <table><tr><th>Grupo</th><th>Orcado</th><th>Realizado</th><th>Desvio</th></tr>{cst_rows}</table></div>
</div>

<div id="t-paradas" class="tab">
  <div class="grid one"><div class="card"><h3>Horas de parada por grupo</h3><div class="chart"><canvas id="cPar"></canvas></div></div></div>
</div>

<div id="t-intel" class="tab">
  <div class="card"><h3>Inteligencia executiva — conclusoes baseadas em dados reais</h3>{ins_html}</div>
</div>

<div class="foot">UMOE OS 8.0 | Cockpit Executivo gerado automaticamente de {len(K)} indicadores e {sum(len(x) for x in [moa,atrh,tch,tah,ind,cst]):,} registros Power BI | {HOJE}</div>

<script>
const CT={json.dumps(charts, ensure_ascii=False, default=str)};
const G='#22C55E',O='#FACC15',B='#3B82F6',R='#F43F5E',C='#22D3EE',M='#8FA3C8';
const opt={{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:M,font:{{size:11}}}}}}}},scales:{{x:{{ticks:{{color:M}},grid:{{color:'#1b2848'}}}},y:{{ticks:{{color:M}},grid:{{color:'#1b2848'}}}}}}}};
function tab(id,b){{document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));document.querySelectorAll('nav button').forEach(x=>x.classList.remove('on'));document.getElementById('t-'+id).classList.add('on');b.classList.add('on');}}
function mkMoa(cid){{const d=CT.moagem_mes||[];if(!d.length)return;new Chart(document.getElementById(cid),{{type:'bar',data:{{labels:d.map(x=>x.MES),datasets:[{{label:'Toneladas',data:d.map(x=>x.TON),backgroundColor:B+'cc',borderColor:B,borderWidth:1}}]}},options:opt}});}}
mkMoa('cMoa'); mkMoa('cMoa2');
(()=>{{const d=CT.atr_dia||[];if(!d.length)return;new Chart(document.getElementById('cAtr'),{{type:'line',data:{{labels:d.map(x=>x.dia),datasets:[{{label:'ATR kg/t',data:d.map(x=>x.ATR),borderColor:O,backgroundColor:O+'22',fill:true,tension:.35,pointRadius:0}}]}},options:opt}});}})();
(()=>{{const d=CT.tch_estagio||[];if(!d.length)return;new Chart(document.getElementById('cTch'),{{type:'bar',data:{{labels:d.map(x=>x.ESTAGIO),datasets:[{{label:'TCH real',data:d.map(x=>x.TCH_REAL),backgroundColor:G+'cc'}},{{label:'TCH estimado',data:d.map(x=>x.TCH_EST),backgroundColor:O+'cc'}}]}},options:opt}});}})();
function mkPar(cid){{const d=CT.paradas||[];if(!d.length)return;new Chart(document.getElementById(cid),{{type:'bar',data:{{labels:d.map(x=>x.GRUPO),datasets:[{{label:'Horas',data:d.map(x=>x.HORAS),backgroundColor:R+'cc',borderColor:R,borderWidth:1}}]}},options:{{...opt,indexAxis:'y'}}}});}}
mkPar('cPar'); mkPar('cPar2');
(()=>{{const d=CT.chuva_ano||[];if(!d.length)return;new Chart(document.getElementById('cChuvaA'),{{type:'bar',data:{{labels:d.map(x=>x.ANO),datasets:[{{label:'Chuva (mm)',data:d.map(x=>x.MM),backgroundColor:C+'aa',borderColor:C,borderWidth:1}}]}},options:opt}});}})();
(()=>{{const d=CT.chuva_mes||[];if(!d.length)return;new Chart(document.getElementById('cChuvaM'),{{type:'bar',data:{{labels:d.map(x=>x.MES),datasets:[{{label:'mm 2026',data:d.map(x=>x.MM),backgroundColor:B+'aa',borderColor:B,borderWidth:1}}]}},options:opt}});}})();
</script></body></html>"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
DOCS.mkdir(exist_ok=True)
(DOCS / "UMOE_Cockpit_Executivo.html").write_text(html, encoding="utf-8")
print(f"[4/4] OK -> {OUT} ({len(html)//1024} KB) + docs/")
