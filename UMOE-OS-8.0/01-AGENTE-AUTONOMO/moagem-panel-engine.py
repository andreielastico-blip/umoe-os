# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 - Moagem Panel Engine
Le Boletim Industrial PDF (mais recente) + TCH-BROCA xlsb
Gera UMOE_Painel_Moagem_Plano_Real_SF2526.html
Rodado diariamente as 10:00 via Task Scheduler
"""
import os, re, glob, json
from datetime import datetime

# Caminhos
BOLETIM_DIR  = r"C:\01 - UMOE\05 - Relatorios\PDF"
TCH_BROCA    = r"C:\01 - UMOE\99 - SSoT\TCH - BROCA - 22627.xlsb"
OUT_HTML     = r"C:\Users\andrei.elastico\Downloads\UMOE_Painel_Moagem_Plano_Real_SF2526.html"

# Plano BPC SF2627 v2 (imutavel)
PLANO = {
    "Abr/26": 279853, "Mai/26": 340481, "Jun/26": 295832,
    "Jul/26": 402622, "Ago/26": 360951, "Set/26": 342203,
    "Out/26": 279556, "Nov/26": 264527, "Mar/27": 202584,
}
PLANO_TOTAL = 2768608
PLANO_UMOE   = 2262435
PLANO_RICARD = 258321
PLANO_FABIAN = 247851

PLANO_DIAS   = {"Abr/26":20.66,"Mai/26":25.14,"Jun/26":21.84,"Jul/26":27.78,"Ago/26":24.90,"Set/26":23.61,"Out/26":19.29,"Nov/26":18.25,"Mar/27":18.84}
PLANO_EF     = {"Abr/26":68.9,"Mai/26":81.1,"Jun/26":72.8,"Jul/26":89.6,"Ago/26":80.3,"Set/26":78.7,"Out/26":62.2,"Nov/26":60.8,"Mar/27":60.8}
PLANO_CLIMA  = {"Abr/26":26.2,"Mai/26":15.4,"Jun/26":25.4,"Jul/26":5.6,"Ago/26":15.9,"Set/26":18.2,"Out/26":35.3,"Nov/26":36.6,"Mar/27":33.6}
PLANO_AGR    = {"Abr/26":1.6,"Mai/26":0.7,"Jun/26":0.5,"Jul/26":0.4,"Ago/26":1.6,"Set/26":0.5,"Out/26":0.3,"Nov/26":0.4,"Mar/27":2.2}
PLANO_IND    = {"Abr/26":3.3,"Mai/26":2.8,"Jun/26":1.3,"Jul/26":4.4,"Ago/26":2.2,"Set/26":2.6,"Out/26":2.1,"Nov/26":2.2,"Mar/27":3.4}
PLANO_ATR    = {"Abr/26":125.0,"Mai/26":130.0,"Jun/26":140.0,"Jul/26":145.0,"Ago/26":148.0,"Set/26":150.0,"Out/26":140.0,"Nov/26":136.5,"Mar/27":108.0}

# ─── LER BOLETIM PDF ───────────────────────────────────────────────────────────
def ler_boletim():
    """Encontra o boletim mais recente e extrai os dados."""
    pdfs = sorted(glob.glob(os.path.join(BOLETIM_DIR, "Boletim Industrial*.pdf")), reverse=True)
    if not pdfs:
        print("  AVISO: nenhum Boletim Industrial encontrado em", BOLETIM_DIR)
        return None
    pdf_path = pdfs[0]
    print(f"  Boletim: {os.path.basename(pdf_path)}")

    try:
        import pdfplumber
    except ImportError:
        print("  AVISO: pdfplumber nao instalado. pip install pdfplumber")
        return None

    texto = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texto += t + "\n"

    def num(padrao, txt=texto):
        m = re.search(padrao, txt)
        if not m:
            return None
        s = m.group(1).replace(".", "").replace(",", ".")
        try:
            return float(s)
        except:
            return None

    # Extrair campos — ordem: diario | semanal | mensal | acumulado
    # Exemplo de linha: "Moagem Total t 33.922,200 33.922,200 124.576,540 730.994,240"
    resultado = {
        "data_ref":    os.path.basename(pdf_path),
        # Acumulados safra (ultimo valor de cada linha)
        "moagem_acum":       num(r"Moagem Total t [\d\.,]+ [\d\.,]+ [\d\.,]+ ([\d\.]+,\d+)"),
        "moagem_mensal":     num(r"Moagem Total t [\d\.,]+ [\d\.,]+ ([\d\.]+,\d+) [\d\.]+,\d+"),
        "aproveit_mensal":   num(r"Aprov\. da Moagem - Geral % [\d,]+ [\d,]+ ([\d,]+) [\d,]+"),
        "aproveit_acum":     num(r"Aprov\. da Moagem - Geral % [\d,]+ [\d,]+ [\d,]+ ([\d,]+)"),
        "moa_hora_acum":     num(r"Moagem Hor.ria t/h [\d,]+ [\d,]+ [\d,]+ ([\d,]+)"),
        "moa_hora_mensal":   num(r"Moagem Hor.ria t/h [\d,]+ [\d,]+ ([\d,]+) [\d,]+"),
        "atr_acum":          num(r"ATR kg [\d,]+ [\d,]+ [\d,]+ ([\d,]+)"),
        "atr_mensal":        num(r"ATR kg [\d,]+ [\d,]+ ([\d,]+) [\d,]+"),
        "im_acum":           num(r"Impureza Mineral % [\d,]+ [\d,]+ ([\d,]+)"),
        "iv_acum":           num(r"Impureza Vegetal % [\d,]+ [\d,]+ ([\d,]+)"),
        "ef_ind_acum":       num(r"Efici.ncia Industrial Consec\. % [\d,]+ [\d,]+ [\d,]+ ([\d,]+)"),
        "ef_ind_mensal":     num(r"Efici.ncia Industrial Consec\. % [\d,]+ [\d,]+ ([\d,]+) [\d,]+"),
        "ef_extr_acum":      num(r"Efici.ncia Extra..o Consec\. % [\d,]+ [\d,]+ [\d,]+ ([\d,]+)"),
        "ef_ferm_acum":      num(r"Efici.ncia Fermenta..o % [\d,]+ [\d,]+ [\d,]+ ([\d,]+)"),
        "rtc_acum":          num(r"RTC Consecana % [\d,]+ [\d,]+ [\d,]+ ([\d,]+)"),
        "energia_prod_acum": num(r"Energia Produzida Total MW.h [\d\.,]+ [\d\.,]+ [\d\.,]+ ([\d\.]+,\d+)"),
        "energia_exp_acum":  num(r"Energia Exportada Total MW.h [\d\.,]+ [\d\.,]+ [\d\.,]+ ([\d\.]+,\d+)"),
        "aehc_acum":         num(r"AEHC Produzido L [\d\.,]+ [\d\.,]+ [\d\.,]+ ([\d\.]+)"),
        "aeac_acum":         num(r"AEAC Produzido L [\d\.,]+ [\d\.,]+ [\d\.,]+ ([\d\.]+)"),
        "par_clima_acum":    num(r"Parada Clima % [\d,]+ [\d,]+ [\d,]+ ([\d,]+)"),
        "dias_safra":        num(r"Dias de Safra \. 1 7 7 14 ([\d]+)"),
    }
    # Fallback: tenta capturar dias de safra simples
    if not resultado["dias_safra"]:
        m = re.search(r"Dias de Safra[:\s]+(\d+)", texto)
        if m:
            resultado["dias_safra"] = float(m.group(1))

    print(f"  Moagem acum: {resultado['moagem_acum']} t | ATR: {resultado['atr_acum']} | Aproveit.: {resultado['aproveit_acum']}%")
    return resultado


# ─── LER TCH-BROCA (aba MOAGEM) ───────────────────────────────────────────────
def ler_tch_broca():
    """Le aba MOAGEM do TCH-BROCA.xlsb e retorna moagem por fornecedor."""
    if not os.path.exists(TCH_BROCA):
        print("  AVISO: TCH-BROCA nao encontrado:", TCH_BROCA)
        return None
    try:
        import pyxlsb
    except ImportError:
        print("  AVISO: pyxlsb nao instalado. pip install pyxlsb")
        return None

    result = {}
    with pyxlsb.open_workbook(TCH_BROCA) as wb:
        with wb.get_sheet("MOAGEM") as sh:
            for row in sh.rows():
                vals = [c.v for c in row]
                if len(vals) < 7:
                    continue
                nome = vals[1]
                if nome in ("UMOE", "RICARDO", "FABIANO", "Total"):
                    try:
                        moagem = float(vals[5]) if vals[5] not in (None, "0x17") else None
                        posicao = float(vals[4]) if vals[4] not in (None, "0x17") else None
                        result[nome] = {"moagem": moagem, "posicao": posicao}
                    except:
                        pass
    print(f"  TCH-BROCA: {result}")
    return result


# ─── GERAR HTML ────────────────────────────────────────────────────────────────
def gerar_html(boletim, fornecedores):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Dados reais conhecidos
    REAL = {
        "Abr/26": 258410,
        "Mai/26": 178701,
    }
    # Adicionar junho parcial se tiver do boletim
    jun_parcial = None
    if boletim and boletim.get("moagem_mensal"):
        jun_parcial = int(round(boletim["moagem_mensal"]))
        REAL["Jun/26"] = jun_parcial

    # KPIs calculados
    total_real    = sum(REAL.values())
    meses_reais   = sorted(REAL.keys())
    ultimo_mes    = meses_reais[-1] if meses_reais else "Mai/26"

    # Plano proporcional para meses parciais
    # Jun/26 - 14 dias de 30
    dias_jun_reais = 14
    plano_jun_prop = int(round(PLANO["Jun/26"] * dias_jun_reais / 30))
    total_plano_prop = PLANO["Abr/26"] + PLANO["Mai/26"] + plano_jun_prop

    delta_acum      = total_real - total_plano_prop
    delta_pct       = delta_acum / total_plano_prop * 100
    execucao_pct    = total_real / PLANO_TOTAL * 100

    # Dias e eficiencia
    dias_ef_abr = 20.05
    dias_ef_mai = 13.77
    dias_ef_jun = round(boletim["aproveit_mensal"] / 100 * dias_jun_reais, 2) if boletim and boletim.get("aproveit_mensal") else 9.26
    total_dias_ef = dias_ef_abr + dias_ef_mai + dias_ef_jun

    ef_abr   = 66.8
    ef_mai   = 44.4
    ef_jun   = boletim.get("aproveit_mensal", 66.17) if boletim else 66.17
    ef_acum  = boletim.get("aproveit_acum",   57.25) if boletim else 57.25

    # ATR e qualidade
    atr_acum     = boletim.get("atr_acum", 126.51) if boletim else 126.51
    atr_jun      = boletim.get("atr_mensal", 131.68) if boletim else 131.68
    im_acum      = boletim.get("im_acum", 0.93) if boletim else 0.93
    iv_acum      = boletim.get("iv_acum", 9.12) if boletim else 9.12
    ef_ind_acum  = boletim.get("ef_ind_acum", 87.10) if boletim else 87.10
    ef_ind_jun   = boletim.get("ef_ind_mensal", 86.14) if boletim else 86.14
    rtc_acum     = boletim.get("rtc_acum", 94.67) if boletim else 94.67
    moa_hora     = boletim.get("moa_hora_acum", 526.78) if boletim else 526.78

    energia_exp  = boletim.get("energia_exp_acum", 35033.111) if boletim else 35033.111
    energia_prod = boletim.get("energia_prod_acum", 61499.590) if boletim else 61499.590
    aehc         = boletim.get("aehc_acum", 24994000) if boletim else 24994000
    aeac         = boletim.get("aeac_acum", 32935900) if boletim else 32935900

    # Fornecedores
    fn_umoe = fn_ric = fn_fab = None
    fn_label = "Posicao atual (colheita)"
    if fornecedores:
        def _fn(nome):
            d = fornecedores.get(nome, {})
            return d.get("moagem") or d.get("posicao")
        fn_umoe = _fn("UMOE")
        fn_ric  = _fn("RICARDO")
        fn_fab  = _fn("FABIANO")

    def fmt(v, dec=0):
        if v is None:
            return "N/D"
        if dec == 0:
            return f"{int(round(v)):,}".replace(",", ".")
        return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def sinal(v):
        return "+" if v and v > 0 else ""

    def cor_delta(v, inv=False):
        if v is None:
            return ""
        if inv:
            return "color:#C62828" if v > 0 else "color:#2E7D32"
        return "color:#C62828" if v < 0 else "color:#2E7D32"

    # Series do grafico
    import json as _json
    meses_g = ["Abr/26","Mai/26","Jun/26","Jul/26","Ago/26","Set/26","Out/26","Nov/26","Mar/27"]
    plano_g = [PLANO[m] for m in meses_g]
    real_g  = [REAL.get(m) for m in meses_g]
    real_g_js = [str(v) if v is not None else "null" for v in real_g]
    cor_real = [
        "rgba(198,40,40,0.75)" if v is not None else "rgba(21,101,192,0.35)"
        for v in real_g
    ]
    bdr_real = [
        "#C62828" if v is not None else "#1565C0"
        for v in real_g
    ]
    # Pre-calcular strings JS para inserir direto no f-string
    JS_MESES   = _json.dumps(meses_g, ensure_ascii=False)
    JS_PLANO   = str(plano_g)
    JS_REAL    = ",".join(real_g_js)
    JS_BGREAL  = str(cor_real)
    JS_BDRREAL = str(bdr_real)

    delta_abr = REAL["Abr/26"] - PLANO["Abr/26"]
    delta_mai = REAL["Mai/26"] - PLANO["Mai/26"]
    delta_jun = (jun_parcial - plano_jun_prop) if jun_parcial else None
    delta_jun_pct = (delta_jun / plano_jun_prop * 100) if delta_jun and plano_jun_prop else None

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Painel Moagem SF2526 - UMOE Bioenergy</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Calibri,Arial,sans-serif;background:#F0F4F0;color:#212121;padding:20px}}
.container{{max-width:1280px;margin:0 auto}}
.header{{background:linear-gradient(135deg,#1B5E20 0%,#2E7D32 100%);color:#fff;padding:16px 20px;border-radius:8px 8px 0 0;margin-bottom:2px}}
.header h1{{font-size:18px;font-weight:700;letter-spacing:.3px}}
.header p{{font-size:11px;color:#A5D6A7;margin-top:3px}}
.upd{{font-size:10px;color:#C8E6C9;margin-top:6px}}
.badges{{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}}
.badge{{font-size:10px;padding:2px 9px;border-radius:4px;font-weight:600}}
.br{{background:#FFEBEE;color:#B71C1C}}.bp{{background:#E3F2FD;color:#0D47A1}}.bg{{background:#E8F5E9;color:#1B5E20}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;padding:16px;background:#fff;margin-bottom:2px}}
.kpi{{background:#F5F5F5;border-radius:6px;padding:10px 13px;border-left:3px solid #81C784}}
.kpi.red{{border-left-color:#E57373}}
.kpi.yellow{{border-left-color:#FFB74D}}
.kl{{font-size:9.5px;color:#607D8B;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px}}
.kv{{font-size:20px;font-weight:700}}
.ks{{font-size:9.5px;color:#90A4AE;margin-top:2px}}
.panel{{background:#fff;padding:16px;margin-bottom:2px}}
.ph{{font-size:10px;font-weight:700;color:#2E7D32;text-transform:uppercase;letter-spacing:.06em;border-bottom:2px solid #A5D6A7;padding-bottom:6px;margin-bottom:12px}}
.chart-wrap{{height:230px;margin-bottom:4px}}
table{{width:100%;border-collapse:collapse;font-size:11px}}
th{{font-size:9.5px;font-weight:700;color:#fff;background:#2E7D32;text-align:right;padding:5px 7px;white-space:nowrap}}
th:first-child{{text-align:left}}
td{{padding:4px 7px;text-align:right;border-bottom:1px solid #F0F0F0;white-space:nowrap}}
td:first-child{{text-align:left;font-weight:500}}
.rr td{{background:#FFF5F5}}.rp td{{background:#FAFAFA}}.rf td{{background:#F5F9FF}}
.rt td{{font-weight:700;background:#E8F5E9;border-top:2px solid #81C784}}
.rd td{{font-size:10px;color:#9E9E9E;font-style:italic}}
.rjun td{{background:#FFF8E1}}
.sep-row td{{height:4px;border:none;background:transparent!important}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.three-col{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}}
.fn{{font-size:9px;color:#90A4AE;margin-top:6px;line-height:1.5}}
.nota-jun{{background:#FFF9C4;border-left:3px solid #F9A825;padding:6px 10px;font-size:10px;color:#5D4037;margin-bottom:10px;border-radius:0 4px 4px 0}}
.ind-kpi{{background:#F1F8E9;border-radius:8px;padding:12px;text-align:center}}
.ind-kpi .v{{font-size:22px;font-weight:700;color:#2E7D32}}
.ind-kpi .l{{font-size:9px;color:#607D8B;text-transform:uppercase;margin-top:3px}}
@media(max-width:600px){{.two-col,.three-col{{grid-template-columns:1fr}}.kpi-grid{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>Planejamento de Moagem x Real - Transportador Imediato</h1>
  <p>BPC Industria SF2627 v2 x Realizado Logistica Mensal - Safra 2025/26</p>
  <div class="upd">Atualizado automaticamente em: <b>{agora}</b> | Fonte: Boletim Industrial + TCH-BROCA 22627</div>
  <div class="badges">
    <span class="badge br">Realizado: Abr/26 - Jun/26 (ate 14/06)</span>
    <span class="badge bp">Planejado: Jul/26 - Mar/27</span>
    <span class="badge bg">Dados oficiais 14/06/2026</span>
  </div>
</div>

<div class="kpi-grid">
  <div class="kpi"><p class="kl">Plano total safra</p><p class="kv" style="color:#1B5E20">{fmt(PLANO_TOTAL)} t</p><p class="ks">Abr/26 a Mar/27 - BPC v2</p></div>
  <div class="kpi red"><p class="kl">Realizado Abr-Jun (14/06)</p><p class="kv" style="color:#C62828">{fmt(total_real)} t</p><p class="ks">Plano prop.: {fmt(total_plano_prop)} t</p></div>
  <div class="kpi red"><p class="kl">Delta acumulado</p><p class="kv" style="color:#C62828">{fmt(delta_acum)} t</p><p class="ks">{sinal(delta_pct)}{delta_pct:.1f}% vs plano proporcional</p></div>
  <div class="kpi yellow"><p class="kl">Execucao da safra</p><p class="kv" style="color:#E65100">{execucao_pct:.1f}%</p><p class="ks">{fmt(total_real)} de {fmt(PLANO_TOTAL)} t</p></div>
  <div class="kpi red"><p class="kl">Dias efetivos acum.</p><p class="kv" style="color:#C62828">{total_dias_ef:.2f} d</p><p class="ks">Plano: {PLANO_DIAS['Abr/26']+PLANO_DIAS['Mai/26']:.2f} + {dias_jun_reais*PLANO_EF['Jun/26']/100:.2f} d (prop.)</p></div>
  <div class="kpi yellow"><p class="kl">Eficiencia media acum.</p><p class="kv" style="color:#E65100">{ef_acum:.1f}%</p><p class="ks">Jun/26: {ef_jun:.1f}% (recuperacao)</p></div>
  <div class="kpi"><p class="kl">ATR acumulado safra</p><p class="kv" style="color:#1565C0">{fmt(atr_acum,2)} kg/t</p><p class="ks">Jun/26: {fmt(atr_jun,2)} kg/t (+{atr_jun-atr_acum:.2f})</p></div>
  <div class="kpi"><p class="kl">Ef. Industrial (Consec.)</p><p class="kv" style="color:#1B5E20">{fmt(ef_ind_acum,2)}%</p><p class="ks">Jun/26: {fmt(ef_ind_jun,2)}%</p></div>
</div>

<div class="panel">
  <p class="ph">Moagem mensal - plano BPC vs. real (toneladas)</p>
  <div class="nota-jun">Jun/26 PARCIAL: dados de 01 a 14/06/2026 (14 dias de 30). Plano proporcional: {fmt(plano_jun_prop)} t. Real: {fmt(jun_parcial)} t. Delta: {fmt(delta_jun)} t ({sinal(delta_jun_pct)}{delta_jun_pct:.1f}% vs proporcional).</div>
  <div class="chart-wrap"><canvas id="moaChart"></canvas></div>
</div>

<div class="panel">
  <p class="ph">Premissas operacionais - BPC x Realizado</p>
  <div style="overflow-x:auto">
  <table>
    <thead><tr>
      <th style="text-align:left;min-width:175px">Indicador</th><th>Un.</th>
      <th>Abr/26</th><th>Mai/26</th><th>Jun/26*</th><th>Jul/26</th><th>Ago/26</th><th>Set/26</th><th>Out/26</th><th>Nov/26</th><th>Mar/27</th><th>Total</th>
    </tr></thead>
    <tbody>
      <tr class="rp"><td>Dias corridos</td><td>d</td><td>30</td><td>31</td><td>14*</td><td>31</td><td>31</td><td>30</td><td>31</td><td>30</td><td>31</td><td>-</td></tr>
      <tr class="rp"><td>Dias efetivos - Plano</td><td>d</td>
        <td>{PLANO_DIAS['Abr/26']}</td><td>{PLANO_DIAS['Mai/26']}</td><td>{PLANO_DIAS['Jun/26']}</td><td>{PLANO_DIAS['Jul/26']}</td><td>{PLANO_DIAS['Ago/26']}</td><td>{PLANO_DIAS['Set/26']}</td><td>{PLANO_DIAS['Out/26']}</td><td>{PLANO_DIAS['Nov/26']}</td><td>{PLANO_DIAS['Mar/27']}</td>
        <td><b>200,3</b></td></tr>
      <tr class="rr"><td>Dias efetivos - Real</td><td>d</td>
        <td><b>{fmt(dias_ef_abr,2)}</b></td>
        <td style="color:#C62828"><b>{fmt(dias_ef_mai,2)}</b></td>
        <td class="rjun"><b>{fmt(dias_ef_jun,2)}</b></td>
        <td colspan="6" style="text-align:center;color:#9E9E9E">- a realizar -</td>
        <td><b>{fmt(total_dias_ef,2)}</b></td></tr>
      <tr class="rd"><td>Delta dias efetivos</td><td>d</td>
        <td style="color:#E65100">{fmt(dias_ef_abr - PLANO_DIAS['Abr/26'],2)}</td>
        <td style="color:#C62828"><b>{fmt(dias_ef_mai - PLANO_DIAS['Mai/26'],2)}</b></td>
        <td class="rjun">{fmt(dias_ef_jun - PLANO_DIAS['Jun/26']*dias_jun_reais/30,2)}</td>
        <td colspan="6" style="text-align:center">-</td>
        <td style="color:#C62828"><b>{fmt(total_dias_ef - (PLANO_DIAS['Abr/26']+PLANO_DIAS['Mai/26']+PLANO_DIAS['Jun/26']*dias_jun_reais/30),2)}</b></td></tr>
      <tr class="sep-row"><td colspan="12"></td></tr>
      <tr class="rp"><td>Indisp. Clima - Plano</td><td>%</td>
        <td>{PLANO_CLIMA['Abr/26']}%</td><td>{PLANO_CLIMA['Mai/26']}%</td><td>{PLANO_CLIMA['Jun/26']}%</td><td>{PLANO_CLIMA['Jul/26']}%</td><td>{PLANO_CLIMA['Ago/26']}%</td><td>{PLANO_CLIMA['Set/26']}%</td><td>{PLANO_CLIMA['Out/26']}%</td><td>{PLANO_CLIMA['Nov/26']}%</td><td>{PLANO_CLIMA['Mar/27']}%</td><td><b>23,5%</b></td></tr>
      <tr class="rp"><td>Indisp. Agricola - Plano</td><td>%</td>
        <td>{PLANO_AGR['Abr/26']}%</td><td>{PLANO_AGR['Mai/26']}%</td><td>{PLANO_AGR['Jun/26']}%</td><td>{PLANO_AGR['Jul/26']}%</td><td>{PLANO_AGR['Ago/26']}%</td><td>{PLANO_AGR['Set/26']}%</td><td>{PLANO_AGR['Out/26']}%</td><td>{PLANO_AGR['Nov/26']}%</td><td>{PLANO_AGR['Mar/27']}%</td><td><b>0,9%</b></td></tr>
      <tr class="rp"><td>Indisp. Industrial - Plano</td><td>%</td>
        <td>{PLANO_IND['Abr/26']}%</td><td>{PLANO_IND['Mai/26']}%</td><td>{PLANO_IND['Jun/26']}%</td><td>{PLANO_IND['Jul/26']}%</td><td>{PLANO_IND['Ago/26']}%</td><td>{PLANO_IND['Set/26']}%</td><td>{PLANO_IND['Out/26']}%</td><td>{PLANO_IND['Nov/26']}%</td><td>{PLANO_IND['Mar/27']}%</td><td><b>2,7%</b></td></tr>
      <tr class="sep-row"><td colspan="12"></td></tr>
      <tr class="rp"><td>Eficiencia - Plano</td><td>%</td>
        <td>{PLANO_EF['Abr/26']}%</td><td>{PLANO_EF['Mai/26']}%</td><td>{PLANO_EF['Jun/26']}%</td><td>{PLANO_EF['Jul/26']}%</td><td>{PLANO_EF['Ago/26']}%</td><td>{PLANO_EF['Set/26']}%</td><td>{PLANO_EF['Out/26']}%</td><td>{PLANO_EF['Nov/26']}%</td><td>{PLANO_EF['Mar/27']}%</td><td><b>72,8%</b></td></tr>
      <tr class="rr"><td>Eficiencia - Real (Aproveit.)</td><td>%</td>
        <td><b>{ef_abr}%</b></td>
        <td style="color:#C62828"><b>{ef_mai}%</b></td>
        <td class="rjun"><b>{ef_jun:.1f}%</b></td>
        <td colspan="6" style="text-align:center;color:#9E9E9E">-</td>
        <td><b style="color:#E65100">{ef_acum:.1f}%</b></td></tr>
      <tr class="rd"><td>Delta eficiencia</td><td>pp</td>
        <td style="color:#E65100">{fmt(ef_abr - PLANO_EF['Abr/26'],1)}</td>
        <td style="color:#C62828"><b>{fmt(ef_mai - PLANO_EF['Mai/26'],1)}</b></td>
        <td class="rjun">{fmt(ef_jun - PLANO_EF['Jun/26'],1)}</td>
        <td colspan="6" style="text-align:center">-</td>
        <td style="color:#C62828"><b>{fmt(ef_acum - 72.8,1)}</b></td></tr>
      <tr class="sep-row"><td colspan="12"></td></tr>
      <tr class="rp"><td>ATR - Plano (kg/tc)</td><td>kg/tc</td>
        <td>{PLANO_ATR['Abr/26']}</td><td>{PLANO_ATR['Mai/26']}</td><td>{PLANO_ATR['Jun/26']}</td><td>{PLANO_ATR['Jul/26']}</td><td>{PLANO_ATR['Ago/26']}</td><td>{PLANO_ATR['Set/26']}</td><td>{PLANO_ATR['Out/26']}</td><td>{PLANO_ATR['Nov/26']}</td><td>{PLANO_ATR['Mar/27']}</td><td><b>137,58</b></td></tr>
      <tr class="rr"><td>ATR - Real</td><td>kg/tc</td>
        <td><b>125,11</b></td><td><b>127,15</b></td>
        <td class="rjun"><b>{fmt(atr_jun,2)}</b></td>
        <td colspan="6" style="text-align:center;color:#9E9E9E">-</td>
        <td><b style="color:#1565C0">{fmt(atr_acum,2)}</b></td></tr>
    </tbody>
  </table>
  </div>
  <p class="fn">* Jun/26 parcial = 14 dias (1-14/06/2026). Eficiencia = Aproveitamento da Moagem Geral (Boletim Industrial).</p>
</div>

<div class="panel">
  <p class="ph">Moagem por fornecedor - plano BPC (t) x posicao real total safra</p>
  <div style="overflow-x:auto">
  <table>
    <thead><tr>
      <th style="text-align:left;min-width:155px">Fornecedor / Indicador</th><th>Un.</th>
      <th>Abr/26</th><th>Mai/26</th><th>Jun/26*</th><th>Jul/26</th><th>Ago/26</th><th>Set/26</th><th>Out/26</th><th>Nov/26</th><th>Mar/27</th><th>Total safra</th>
    </tr></thead>
    <tbody>
      <tr class="rp"><td>Moagem Propria UMOE</td><td>t</td><td>222.217</td><td>270.359</td><td>234.906</td><td>325.144</td><td>291.491</td><td>276.351</td><td>225.760</td><td>213.623</td><td>202.584</td><td><b>{fmt(PLANO_UMOE)}</b></td></tr>
      <tr class="rp"><td>Moagem Ricardo (Frente 10)</td><td>t</td><td>29.414</td><td>35.786</td><td>31.093</td><td>39.540</td><td>35.448</td><td>33.607</td><td>27.455</td><td>25.979</td><td>-</td><td><b>{fmt(PLANO_RICARD)}</b></td></tr>
      <tr class="rp"><td>Moagem Fabiano (Frente 27)</td><td>t</td><td>28.222</td><td>34.336</td><td>29.833</td><td>37.938</td><td>34.011</td><td>32.245</td><td>26.342</td><td>24.926</td><td>-</td><td><b>{fmt(PLANO_FABIAN)}</b></td></tr>
      <tr class="rt"><td>Total Plano BPC</td><td>t</td><td>279.853</td><td>340.481</td><td>295.832</td><td>402.622</td><td>360.951</td><td>342.203</td><td>279.556</td><td>264.527</td><td>202.584</td><td><b>{fmt(PLANO_TOTAL)}</b></td></tr>
      <tr class="sep-row"><td colspan="12"></td></tr>
      <tr class="rr"><td>Total Moagem Real (desde Abr)</td><td>t</td>
        <td><b>258.410</b></td>
        <td style="color:#C62828"><b>178.701</b></td>
        <td class="rjun"><b>{fmt(jun_parcial)}</b></td>
        <td colspan="6" style="text-align:center;color:#9E9E9E">- a realizar -</td>
        <td><b style="color:#C62828">{fmt(total_real)}</b></td></tr>
      <tr class="rd"><td>Delta Plano-Real</td><td>t</td>
        <td style="color:#E65100"><b>-21.443</b></td>
        <td style="color:#C62828"><b>-161.780</b></td>
        <td class="rjun">{fmt(delta_jun)}</td>
        <td colspan="6" style="text-align:center">-</td>
        <td style="color:#C62828"><b>{fmt(delta_acum)}</b></td></tr>
      <tr class="rd"><td>Delta % (vs plano proporcional)</td><td>%</td>
        <td style="color:#E65100">-7,7%</td>
        <td style="color:#C62828"><b>-47,5%</b></td>
        <td class="rjun">{sinal(delta_jun_pct)}{delta_jun_pct:.1f}%</td>
        <td colspan="6" style="text-align:center">-</td>
        <td style="color:#C62828"><b>{sinal(delta_pct)}{delta_pct:.1f}%</b></td></tr>
      <tr class="sep-row"><td colspan="12"></td></tr>
      {"<tr class='rf'><td>Real UMOE (total safra Mar-Jun)</td><td>t</td><td colspan='9' style='text-align:center;color:#607D8B'>Desde Mar/26 - TCH-BROCA 22627</td><td><b>" + fmt(fn_umoe) + "</b></td></tr>" if fn_umoe else ""}
      {"<tr class='rf'><td>Real Ricardo (total safra Mar-Jun)</td><td>t</td><td colspan='9' style='text-align:center;color:#607D8B'>Desde Mar/26</td><td><b>" + fmt(fn_ric) + "</b></td></tr>" if fn_ric else ""}
      {"<tr class='rf'><td>Real Fabiano (total safra Mar-Jun)</td><td>t</td><td colspan='9' style='text-align:center;color:#607D8B'>Desde Mar/26</td><td><b>" + fmt(fn_fab) + "</b></td></tr>" if fn_fab else ""}
    </tbody>
  </table>
  </div>
  <p class="fn">Moagem real por fornecedor: total safra desde Marco/26 (inclui marco que nao esta no BPC abr-mar). Fonte: TCH-BROCA 22627 aba MOAGEM.</p>
</div>

<div class="panel">
  <p class="ph">Indicadores industriais - acumulado safra ate 14/06/2026</p>
  <div class="three-col" style="margin-bottom:14px">
    <div class="ind-kpi"><div class="v">{fmt(atr_acum,2)}</div><div class="l">ATR Acumulado (kg/t)</div></div>
    <div class="ind-kpi"><div class="v">{fmt(ef_ind_acum,2)}%</div><div class="l">Ef. Industrial Consecana</div></div>
    <div class="ind-kpi"><div class="v">{fmt(rtc_acum,2)}%</div><div class="l">RTC Consecana</div></div>
    <div class="ind-kpi"><div class="v">{fmt(im_acum,2)}%</div><div class="l">Impureza Mineral</div></div>
    <div class="ind-kpi"><div class="v">{fmt(iv_acum,2)}%</div><div class="l">Impureza Vegetal</div></div>
    <div class="ind-kpi"><div class="v">{fmt(moa_hora,1)}</div><div class="l">Moagem Horaria (t/h)</div></div>
  </div>
  <div class="two-col">
    <table>
      <thead><tr><th style="text-align:left">Indicador Industrial</th><th>Un.</th><th>Jun/26 (1-14)</th><th>Acumulado Safra</th></tr></thead>
      <tbody>
        <tr class="rp"><td>ATR</td><td>kg/t</td><td><b style="color:#1565C0">{fmt(atr_jun,2)}</b></td><td>{fmt(atr_acum,2)}</td></tr>
        <tr class="rp"><td>Impureza Mineral</td><td>%</td><td>0,94</td><td>{fmt(im_acum,2)}</td></tr>
        <tr class="rp"><td>Impureza Vegetal</td><td>%</td><td>8,37</td><td>{fmt(iv_acum,2)}</td></tr>
        <tr class="rp"><td>Ef. Industrial Consecana</td><td>%</td><td>{fmt(ef_ind_jun,2)}</td><td><b style="color:#1B5E20">{fmt(ef_ind_acum,2)}</b></td></tr>
        <tr class="rp"><td>Ef. Extracao</td><td>%</td><td>96,17</td><td>95,48</td></tr>
        <tr class="rp"><td>Ef. Fermentacao</td><td>%</td><td>92,85</td><td>92,32</td></tr>
        <tr class="rp"><td>RTC Consecana</td><td>%</td><td>93,63</td><td>{fmt(rtc_acum,2)}</td></tr>
        <tr class="rp"><td>Moagem Horaria</td><td>t/h</td><td>560,32</td><td>{fmt(moa_hora,2)}</td></tr>
        <tr class="rp"><td>Aproveitamento Geral</td><td>%</td><td>{fmt(ef_jun,2)}</td><td>{fmt(ef_acum,2)}</td></tr>
      </tbody>
    </table>
    <table>
      <thead><tr><th style="text-align:left">Producao / Energia</th><th>Un.</th><th>Acumulado Safra</th></tr></thead>
      <tbody>
        <tr class="rp"><td>AEHC Hidratado</td><td>L</td><td><b>{fmt(aehc)}</b></td></tr>
        <tr class="rp"><td>AEAC Anidro</td><td>L</td><td><b>{fmt(aeac)}</b></td></tr>
        <tr class="rp"><td>Total Equiv. AEHC</td><td>L</td><td><b>59.356.023</b></td></tr>
        <tr class="sep-row"><td colspan="3"></td></tr>
        <tr class="rp"><td>Energia Produzida</td><td>MWh</td><td><b>{fmt(energia_prod,1)}</b></td></tr>
        <tr class="rp"><td>Energia Exportada</td><td>MWh</td><td><b style="color:#1B5E20">{fmt(energia_exp,1)}</b></td></tr>
        <tr class="rp"><td>Energia Consumida</td><td>MWh</td><td>26.466,5</td></tr>
        <tr class="sep-row"><td colspan="3"></td></tr>
        <tr class="rp"><td>Vapor Produzido</td><td>t</td><td>358.022</td></tr>
        <tr class="rp"><td>Horas Efetivas Moagem</td><td>h</td><td>1.387:40</td></tr>
      </tbody>
    </table>
  </div>
  <p class="fn">Fonte: Boletim Industrial Unidade 2 - 14/06/2026 (gerado 15/06/2026 08:59). Autor: Mayara Laiane Zampoli.</p>
</div>

<div class="panel">
  <p class="ph">Decomposicao do desvio acumulado Abr-Jun (14/06) - {fmt(delta_acum)} t vs plano proporcional</p>
  <div class="two-col">
    <table>
      <thead><tr><th style="text-align:left">Camada</th><th style="text-align:left">Responsavel</th><th>Toneladas</th><th>%</th></tr></thead>
      <tbody>
        <tr style="background:#EEEDFE22"><td>Plano - Recalc</td><td><span style="background:#EEEDFE;color:#534AB7;font-size:9px;padding:1px 5px;border-radius:3px;font-weight:600">Chuva</span></td><td style="color:#534AB7"><b>-198.751</b></td><td style="color:#534AB7">~101%</td></tr>
        <tr style="background:#FFEBEE22"><td>Recalc - Real</td><td><span style="background:#FAEEDA;color:#854F0B;font-size:9px;padding:1px 5px;border-radius:3px;font-weight:600">UMOE + Imediato</span></td><td style="color:#C62828"><b>-52.685</b></td><td style="color:#C62828">~27%</td></tr>
        <tr style="background:#E8F5E922"><td>Ganhos operacionais</td><td><span style="background:#E8F5E9;color:#1B5E20;font-size:9px;padding:1px 5px;border-radius:3px;font-weight:600">Compensacao</span></td><td style="color:#2E7D32"><b>+68.213</b></td><td style="color:#2E7D32">~-35%</td></tr>
        <tr class="rt"><td>Delta Abr+Mai (base)</td><td>-</td><td style="color:#C62828"><b>-183.223</b></td><td><b>100%</b></td></tr>
        <tr class="rjun"><td>+ Jun/26 parcial (1-14)</td><td><span style="background:#FFF9C4;color:#5D4037;font-size:9px;padding:1px 5px;border-radius:3px;font-weight:600">Parcial</span></td><td style="color:#C62828">{fmt(delta_jun)}</td><td>-</td></tr>
        <tr class="rt"><td><b>Total Acumulado</b></td><td>-</td><td style="color:#C62828"><b>{fmt(delta_acum)}</b></td><td><b>100%</b></td></tr>
      </tbody>
    </table>
    <table>
      <thead><tr><th style="text-align:left">Causa operacional (Abr+Mai)</th><th style="text-align:left">Veto principal</th><th>Toneladas</th><th>%</th></tr></thead>
      <tbody>
        <tr style="background:#E8F5E922"><td>UMOE</td><td>T.Carregamento + Dens</td><td style="color:#1B5E20"><b>31.587</b></td><td>60,7%</td></tr>
        <tr style="background:#FFF3E022"><td>Imediato (Transportador)</td><td>Hilo + Patio + Vel</td><td style="color:#E65100"><b>20.465</b></td><td>39,3%</td></tr>
        <tr class="rt"><td>Total controlavel</td><td>-</td><td><b>52.052</b></td><td><b>100%</b></td></tr>
      </tbody>
    </table>
  </div>
  <p class="fn">Decomposicao Abr+Mai conforme analise BPC v2. Jun/26 parcial: delta calculado vs plano proporcional (14/30 dias). Chuva Mai/26: +209% vs historico (365mm) - principal causa do desvio acumulado.</p>
</div>

<div class="panel">
  <p class="ph">Paradas industriais - acumulado safra (horas)</p>
  <div style="overflow-x:auto">
  <table>
    <thead><tr><th style="text-align:left">Tipo de Parada</th><th>Jun/26 (1-14) h</th><th>Acumulado Safra h</th><th>% tempo acum.</th></tr></thead>
    <tbody>
      <tr class="rr"><td><b>Parada Total</b></td><td><b>113:40</b></td><td><b>1.036:20</b></td><td style="color:#C62828"><b>57,25%</b></td></tr>
      <tr style="background:#EEEDFE22"><td>Parada Clima</td><td>106:16</td><td>933:53</td><td style="color:#534AB7">61,47%</td></tr>
      <tr class="rp"><td>Parada Industria</td><td>5:56</td><td>38:55</td><td>1,61%</td></tr>
      <tr class="rp"><td>Parada Agricola</td><td>1:28</td><td>39:41</td><td>1,64%</td></tr>
      <tr class="rp"><td>Parada Caminhao</td><td>0:00</td><td>31:41</td><td>1,31%</td></tr>
      <tr class="rp"><td>Parada Caminhao Hilo</td><td>1:28</td><td>7:50</td><td>0,32%</td></tr>
      <tr class="rp"><td>Parada Mult. Fermento</td><td>0:00</td><td>14:52</td><td>0,61%</td></tr>
      <tr class="rp"><td>Parada Moenda</td><td>5:56</td><td>20:44</td><td>0,86%</td></tr>
    </tbody>
  </table>
  </div>
  <p class="fn">Chuva responde por 90,1% das paradas totais acumuladas (933h de 1.036h). Fonte: Boletim Industrial 14/06/2026.</p>
</div>

</div>
<script>
var meses={JS_MESES};
var plano={JS_PLANO};
var real=[{JS_REAL}];
var bgReal={JS_BGREAL};
var bdrReal={JS_BDRREAL};
new Chart(document.getElementById('moaChart'),{{
  type:'bar',
  data:{{
    labels:meses,
    datasets:[
      {{label:'Plano BPC (t)',data:plano,backgroundColor:'rgba(46,125,50,0.18)',borderColor:'#2E7D32',borderWidth:1.5,order:2}},
      {{label:'Real (t)',data:real,backgroundColor:bgReal,borderColor:bdrReal,borderWidth:1.5,order:1}}
    ]
  }},
  options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{
      legend:{{display:true,position:'top',labels:{{boxWidth:10,boxHeight:10,font:{{size:10}},padding:12}}}},
      tooltip:{{callbacks:{{label:function(c){{if(c.parsed.y==null)return c.dataset.label+': - (a realizar)';var s=c.label.includes('Jun')?'*':'';return c.dataset.label+s+': '+c.parsed.y.toLocaleString('pt-BR')+' t';}}}}}}
    }},
    scales:{{
      y:{{ticks:{{callback:function(v){{return(v/1000).toFixed(0)+'k'}},font:{{size:10}}}},grid:{{color:'rgba(0,0,0,0.05)'}}}},
      x:{{ticks:{{font:{{size:10}}}},grid:{{display:false}}}}
    }}
  }}
}});
</script>
</body>
</html>"""

    return html


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[{datetime.now():%H:%M:%S}] UMOE Moagem Panel Engine iniciando...")

    print("[1] Lendo Boletim Industrial...")
    boletim = ler_boletim()

    print("[2] Lendo TCH-BROCA (fornecedores)...")
    fornecedores = ler_tch_broca()

    print("[3] Gerando HTML...")
    html = gerar_html(boletim, fornecedores)

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Salvo: {OUT_HTML} ({len(html)//1024}KB)")
    print(f"[{datetime.now():%H:%M:%S}] Concluido.")
