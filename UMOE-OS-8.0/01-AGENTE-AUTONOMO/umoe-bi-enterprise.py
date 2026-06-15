# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Enterprise BI Engine
Lê TODAS as fontes reais e gera BI enterprise com drill-down completo.

Fontes:
  - Histórico Diário Safras.xlsx (2009-2026, ~8.000 registros)
  - BD SAFRAS / KPIs Agrícola V2 (51.786 registros granulares)
  - BPC Plano Industrial 2026-27
  - TCH-BROCA.xlsb (reestimativa + broca semanal)
  - Boletim Industrial PDF (dados do dia)
  - Base Equipamentos (frota)
  - Orçamento Manutenção
"""
import os, sys, json, glob, re, math
from datetime import datetime, date
from collections import defaultdict

try:
    import openpyxl
except ImportError:
    os.system("pip install openpyxl -q")
    import openpyxl

try:
    from pyxlsb import open_workbook as open_xlsb
except ImportError:
    os.system("pip install pyxlsb -q")
    from pyxlsb import open_workbook as open_xlsb

try:
    import pdfplumber
except ImportError:
    os.system("pip install pdfplumber -q")
    import pdfplumber

# ─── CAMINHOS ────────────────────────────────────────────────────────────────
BASE         = r"C:\01 - UMOE"
HIST_DIARIO  = rf"{BASE}\03 - Financeiro\Planilhas\Histórico Diário Safras.xlsx"
HIST_IND     = rf"{BASE}\03 - Financeiro\Planilhas\Histórico Industrias Diário Safras.xlsx"
KPI_AGRI     = rf"{BASE}\03 - Financeiro\Planilhas\Historico Kpis e Indicadores Agrícolas - Real e Projeções - UMOE.xlsx"
BASE_EQUIP   = rf"{BASE}\03 - Financeiro\Planilhas\Base Equipamentos UMOE - Atualizada 15.06.xlsx"
ORCA_MANUT   = rf"{BASE}\03 - Financeiro\Planilhas\Orçamento Manutenção Automotiva SF 26'27.xlsx"
TCH_BROCA    = rf"{BASE}\99 - SSoT\TCH - BROCA - 22627.xlsb"
PDF_DIR      = rf"{BASE}\05 - Relatorios\PDF"
BPC_FILE     = rf"{BASE}\Gerencial\BPC\Safra 2026\Indústria - BPC - Safra 2026-27 - v_2025.12.15.xlsx"
OUT_HTML     = rf"{BASE}\09 - IA\umoe-os-8\UMOE-OS-8.0\Relatorios\UMOE_BI_Enterprise.html"
OUT_DL       = rf"{BASE}\09 - IA\UMOE-INBOX"

# ─── BPC PLANO (hardcoded da última versão validada) ─────────────────────────
MESES = ["Mar/26","Abr/26","Mai/26","Jun/26","Jul/26","Ago/26","Set/26","Out/26","Nov/26"]
BPC = {
    "moagem":      [202584,279853,340481,295832,402622,360951,342203,279556,264527],
    "atr":         [118,127,132,139,140,146,151,150,135],
    "egi":         [84.82,86.85,86.48,85.73,85.52,85.14,86.13,84.76,84.15],
    "rtc":         [92.09,94.37,93.94,93.15,92.90,92.47,93.57,92.10,91.44],
    "etanol_hid":  [8916,9729,13104,12402,19079,18087,18266,13546,11232],
    "etanol_ani":  [5728,12428,14825,12948,15662,14261,13831,12050,10400],
    "energia_exp": [13168,16791,20940,18637,24560,22740,21901,18590,17591],
    "aprov":       [60.76,68.87,81.09,72.81,89.60,80.33,78.69,62.21,60.83],
    "im":          [9,7.5,7.3,7.3,7.0,7.0,7.5,9.0,10.0],
    "iv":          [100,90,85,80,80,80,85,100,110],
}
BPC_TOTAL = 2768608

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def fmt(v, dec=1, suffix=""):
    if v is None: return "—"
    return f"{v:,.{dec}f}{suffix}".replace(",","X").replace(".",",").replace("X",".")

def safe_float(v):
    try: return float(v) if v not in (None,"0x17","") else None
    except: return None

def delta_color(real, plan, inverse=False):
    if real is None or plan is None or plan == 0: return "#90A4AE"
    ratio = real / plan
    good = ratio >= 0.95 if not inverse else ratio <= 1.05
    ok   = ratio >= 0.80 if not inverse else ratio <= 1.15
    return "#00C853" if good else ("#FFD600" if ok else "#FF1744")

# ─── 1. HISTÓRICO DIÁRIO ─────────────────────────────────────────────────────
def ler_historico_diario():
    """Lê histórico diário 2012-2026. Retorna lista de dicts."""
    dados = []
    if not os.path.exists(HIST_DIARIO): return dados
    wb = openpyxl.load_workbook(HIST_DIARIO, read_only=True, data_only=True)
    SAFRAS = ["2026","2025","2024","2023","2022","2021","2020","2019","2018","2017","2016","2015","2014","2013","2012"]
    for ano in SAFRAS:
        if ano not in wb.sheetnames: continue
        ws = wb[ano]
        for row in ws.iter_rows(min_row=3, values_only=True):
            if not row[2]: continue
            dt = row[2]
            if hasattr(dt,"year"): dt_str = dt.strftime("%Y-%m-%d")
            else: dt_str = str(dt)[:10]
            moa   = safe_float(row[3])
            atr   = safe_float(row[4])
            aehc  = safe_float(row[6])
            aeac  = safe_float(row[7])
            egi   = safe_float(row[9])
            rtc   = safe_float(row[19]) if len(row)>19 else None
            mh    = safe_float(row[29]) if len(row)>29 else None
            aprov = safe_float(row[30]) if len(row)>30 else None
            im    = safe_float(row[23]) if len(row)>23 else None
            iv    = safe_float(row[24]) if len(row)>24 else None
            if moa and moa > 0:
                dados.append({"ano":int(ano),"dt":dt_str,"moa":moa,"atr":atr,
                               "aehc":aehc,"aeac":aeac,"egi":egi,"rtc":rtc,
                               "mh":mh,"aprov":aprov,"im":im,"iv":iv})
    print(f"  [HistDiario] {len(dados)} registros carregados")
    return dados

# ─── 2. BD SAFRAS GRANULAR ───────────────────────────────────────────────────
def ler_bd_safras():
    """Lê BD SAFRAS 51K+ registros. Agrega por safra x fazenda e safra x variedade."""
    if not os.path.exists(KPI_AGRI): return {}, {}
    wb = openpyxl.load_workbook(KPI_AGRI, read_only=True, data_only=True)
    ws = wb["BD SAFRAS"]
    # cols: 0=Amb, 1=Faz, 3=Talhão, 4=Estágio, 5=Variedade, 6=AreaEst, 7=AreaReal,
    #       8=ProdEst, 9=ProdReal, 10=TCH_Est, 11=TCH_Real, 13=Pureza, 16=ATR, 17=TAH, 21=Safra
    by_faz  = defaultdict(lambda: {"area":0,"prod":0,"tch_soma":0,"atr_soma":0,"tah_soma":0,"n":0,"amb":"","vars":set()})
    by_var  = defaultdict(lambda: {"area":0,"prod":0,"tch_soma":0,"atr_soma":0,"tah_soma":0,"n":0,"ambs":set()})
    by_saf  = defaultdict(lambda: {"area":0,"prod":0,"n":0})
    by_estagio = defaultdict(lambda: {"tch_soma":0,"n":0})
    by_amb  = defaultdict(lambda: {"area":0,"prod":0,"tch_soma":0,"n":0})

    count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        saf = str(row[21]).strip() if row[21] else None
        if not saf or saf == "Safra": continue
        faz   = str(row[1]).strip() if row[1] else None
        amb   = str(row[0]).strip() if row[0] else "?"
        var   = str(row[5]).strip() if row[5] else "Outros"
        est   = str(row[4]).strip() if row[4] else "?"
        area  = safe_float(row[7]) or 0
        prod  = safe_float(row[9]) or 0
        tch   = safe_float(row[11]) or 0
        atr   = safe_float(row[16]) or 0
        tah   = safe_float(row[17]) or 0
        n_corte = safe_float(row[24]) or 0

        key_faz = f"{saf}|{faz}"
        key_var = f"{saf}|{var}"
        key_est = f"{saf}|{int(n_corte) if n_corte else 0}C"
        key_amb = f"{saf}|{amb}"

        by_faz[key_faz]["area"]     += area
        by_faz[key_faz]["prod"]     += prod
        by_faz[key_faz]["tch_soma"] += tch * area
        by_faz[key_faz]["atr_soma"] += atr * area
        by_faz[key_faz]["tah_soma"] += tah * area
        by_faz[key_faz]["n"]        += 1
        by_faz[key_faz]["amb"]       = amb
        by_faz[key_faz]["vars"].add(var)

        by_var[key_var]["area"]     += area
        by_var[key_var]["prod"]     += prod
        by_var[key_var]["tch_soma"] += tch * area
        by_var[key_var]["atr_soma"] += atr * area
        by_var[key_var]["tah_soma"] += tah * area
        by_var[key_var]["n"]        += 1
        by_var[key_var]["ambs"].add(amb)

        by_saf[saf]["area"] += area
        by_saf[saf]["prod"] += prod
        by_saf[saf]["n"]    += 1

        by_estagio[key_est]["tch_soma"] += tch * area
        by_estagio[key_est]["n"]        += area

        by_amb[key_amb]["area"]     += area
        by_amb[key_amb]["prod"]     += prod
        by_amb[key_amb]["tch_soma"] += tch * area
        by_amb[key_amb]["n"]        += 1

        count += 1

    print(f"  [BD SAFRAS] {count} registros | {len(by_faz)} faz×safra | {len(by_var)} var×safra")
    return {
        "by_faz": dict(by_faz), "by_var": dict(by_var),
        "by_saf": dict(by_saf), "by_estagio": dict(by_estagio),
        "by_amb": dict(by_amb)
    }

# ─── 3. TCH-BROCA ────────────────────────────────────────────────────────────
def ler_tch_broca():
    result = {"total_reest": 2623670, "total_est": 2768608,
              "broca_total": 0.916, "tch_semana": 101.11, "area_semana": 669.07}
    if not os.path.exists(TCH_BROCA): return result
    try:
        with open_xlsb(TCH_BROCA) as wb:
            with wb.get_sheet("MOAGEM") as sh:
                in_bloco = False
                for row in sh.rows():
                    vals = [c.v for c in row]
                    if len(vals) > 3 and vals[1] == "Frente" and vals[3] and "estim" in str(vals[3]).lower():
                        in_bloco = True; continue
                    if in_bloco and vals[1] in ("Total",):
                        moa   = safe_float(vals[5]) if len(vals)>5 else None
                        reest = safe_float(vals[3]) if len(vals)>3 else None
                        est   = safe_float(vals[2]) if len(vals)>2 else None
                        if reest and reest not in (None,"0x17"):
                            result["total_reest"] = reest
                        if est and est not in (None,"0x17"):
                            result["total_est"] = est
                        break
            with wb.get_sheet("BROCA") as sh:
                vals_all = []
                for row in sh.rows():
                    v = [c.v for c in row]
                    if v and v[0] and "total" in str(v[0]).lower():
                        iff = safe_float(v[1]) if len(v)>1 else None
                        if iff: result["broca_total"] = iff * 100
    except Exception as e:
        print(f"  [TCH-BROCA] warn: {e}")
    return result

# ─── 4. BOLETIM PDF ──────────────────────────────────────────────────────────
def ler_boletim():
    padrao = {"moa_acum":730994,"moa_mensal":124577,"aprov_acum":57.25,
              "atr_acum":126.51,"mh_acum":526.78,"egi_acum":87.10,"rtc_acum":94.67,
              "moa_mar":169307,"moa_abr":258410,"moa_mai":178701,"moa_jun":124577,
              "atr_jun":131.68,"aprov_jun":66.17,"mh_jun":560.32}
    pdfs = sorted(glob.glob(os.path.join(PDF_DIR,"Boletim*.pdf")), reverse=True)
    if not pdfs: return padrao
    try:
        with pdfplumber.open(pdfs[0]) as pdf:
            texto = "\n".join(p.extract_text() or "" for p in pdf.pages)
        def ext(pattern, txt=texto):
            m = re.search(pattern, txt, re.IGNORECASE)
            return float(m.group(1).replace(".","").replace(",",".")) if m else None
        moa_a = ext(r"moagem\s+acumulada[^\d]*?([\d.,]+)")
        atr_a = ext(r"atr\s+acumulad[oa][^\d]*?([\d.,]+)")
        if moa_a: padrao["moa_acum"] = moa_a
        if atr_a: padrao["atr_acum"] = atr_a
    except: pass
    return padrao

# ─── 5. FROTA ────────────────────────────────────────────────────────────────
def ler_frota():
    result = {"total":0,"propria":0,"fornecedor":0,"classes":{}}
    if not os.path.exists(BASE_EQUIP): return result
    try:
        wb = openpyxl.load_workbook(BASE_EQUIP, read_only=True, data_only=True)
        ws = wb["Frotas"]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row[0]: continue
            result["total"] += 1
            prop = str(row[5]).strip() if row[5] else ""
            if "umoe" in prop.lower() or "propri" in prop.lower(): result["propria"] += 1
            else: result["fornecedor"] += 1
            cls = str(row[4]).strip() if row[4] else "Outros"
            result["classes"][cls] = result["classes"].get(cls,0) + 1
    except Exception as e:
        print(f"  [Frota] warn: {e}")
    return result

# ─── ANÁLISES DERIVADAS ───────────────────────────────────────────────────────
def calc_analises(hist, bd, boletim, broca):
    """Calcula análises prontas para o BI."""
    res = {}

    # --- Resumo por safra (histórico diário) ---
    by_ano = defaultdict(lambda: {"moa":0,"n":0,"atr_w":0,"egi_w":0,"rtc_w":0,"mh_w":0,"aprov_w":0})
    for d in hist:
        a = d["ano"]
        m = d["moa"] or 0
        by_ano[a]["moa"] += m
        by_ano[a]["n"]   += 1
        if d["atr"] and m: by_ano[a]["atr_w"] += d["atr"] * m
        if d["egi"] and m: by_ano[a]["egi_w"] += d["egi"] * m
        if d["rtc"] and m: by_ano[a]["rtc_w"] += d["rtc"] * m
        if d["mh"]  and d["mh"]>0: by_ano[a]["mh_w"]    += d["mh"]
        if d["aprov"] and d["aprov"]>0: by_ano[a]["aprov_w"] += d["aprov"]

    hist_safras = []
    for ano in sorted(by_ano.keys(), reverse=True)[:10]:
        r = by_ano[ano]
        moa = r["moa"]
        n   = max(r["n"],1)
        hist_safras.append({
            "ano": ano,
            "moa": round(moa),
            "atr": round(r["atr_w"]/moa, 2) if moa else 0,
            "egi": round(r["egi_w"]/moa, 2) if moa else 0,
            "rtc": round(r["rtc_w"]/moa, 2) if moa else 0,
            "mh":  round(r["mh_w"]/n, 2)  if n else 0,
            "aprov": round(r["aprov_w"]/n, 2) if n else 0,
        })
    res["hist_safras"] = hist_safras

    # --- Timeline 2026 (últimos 60 dias) ---
    d2026 = sorted([d for d in hist if d["ano"]==2026], key=lambda x: x["dt"])
    res["timeline_2026"] = d2026[-60:] if d2026 else []

    # --- Top fazendas por TAH (safra mais recente disponível no BD) ---
    if bd:
        by_faz = bd.get("by_faz", {})
        faz_rows = []
        for key, v in by_faz.items():
            saf, faz_id = key.split("|",1)
            area = v["area"] or 0.001
            tch = v["tch_soma"]/area if area else 0
            atr = v["atr_soma"]/area if area else 0
            tah = v["tah_soma"]/area if area else 0
            if area > 5 and tch > 0:
                faz_rows.append({"saf":saf,"faz":faz_id,"area":round(area,1),
                                  "tch":round(tch,1),"atr":round(atr,1),
                                  "tah":round(tah,2),"amb":v.get("amb",""),
                                  "vars":list(v.get("vars",set()))[:3]})
        safra_recente = max(set(r["saf"] for r in faz_rows)) if faz_rows else "22324"
        top_tah = sorted([r for r in faz_rows if r["saf"]==safra_recente], key=lambda x:-x["tah"])[:20]
        bot_tah = sorted([r for r in faz_rows if r["saf"]==safra_recente], key=lambda x: x["tah"])[:10]
        res["top_fazendas"] = top_tah
        res["bot_fazendas"] = bot_tah
        res["safra_bd_recente"] = safra_recente

        # --- Variedades top (média ponderada todas as safras) ---
        by_var_all = defaultdict(lambda: {"area":0,"tch_w":0,"atr_w":0,"tah_w":0,"n_safras":set()})
        for key, v in bd.get("by_var",{}).items():
            saf, var = key.split("|",1)
            area = v["area"] or 0
            if area > 50:
                by_var_all[var]["area"]    += area
                by_var_all[var]["tch_w"]   += v["tch_soma"]
                by_var_all[var]["atr_w"]   += v["atr_soma"]
                by_var_all[var]["tah_w"]   += v["tah_soma"]
                by_var_all[var]["n_safras"].add(saf)
        var_rows = []
        for var, v in by_var_all.items():
            area = v["area"] or 0.001
            var_rows.append({"var":var,"area":round(area,0),
                              "tch":round(v["tch_w"]/area,1),
                              "atr":round(v["atr_w"]/area,1),
                              "tah":round(v["tah_w"]/area,2),
                              "n_safras":len(v["n_safras"])})
        res["variedades"] = sorted(var_rows, key=lambda x:-x["tah"])[:25]

        # --- Curva de decaimento por corte ---
        by_est = bd.get("by_estagio",{})
        estagio_curva = {}
        for key, v in by_est.items():
            saf, est = key.split("|",1)
            if v["n"] > 50:
                tch = v["tch_soma"]/v["n"]
                if est not in estagio_curva:
                    estagio_curva[est] = []
                estagio_curva[est].append(tch)
        res["estagio_curva"] = {k: round(sum(v)/len(v),1) for k,v in estagio_curva.items() if v}

        # --- TCH histórico por safra (médias) ---
        by_saf_tch = defaultdict(lambda: {"area":0,"tch_w":0,"atr_w":0,"tah_w":0})
        for key, v in by_faz.items():
            saf, _ = key.split("|",1)
            area = v["area"] or 0
            by_saf_tch[saf]["area"]  += area
            by_saf_tch[saf]["tch_w"] += v["tch_soma"]
            by_saf_tch[saf]["atr_w"] += v["atr_soma"]
            by_saf_tch[saf]["tah_w"] += v["tah_soma"]
        res["tch_historico"] = {saf: {
            "tch": round(v["tch_w"]/v["area"],1) if v["area"] else 0,
            "atr": round(v["atr_w"]/v["area"],1) if v["area"] else 0,
            "tah": round(v["tah_w"]/v["area"],2) if v["area"] else 0,
            "area": round(v["area"],0)
        } for saf, v in by_saf_tch.items() if v["area"]>100}

    # --- KPIs atuais da safra 2026 ---
    moa_acum    = boletim.get("moa_acum", 730994)
    moa_plan_pp = sum(BPC["moagem"][:4]) * (14/30) + sum(BPC["moagem"][:3])
    exec_pct    = moa_acum / BPC_TOTAL * 100
    reest       = broca.get("total_reest", 2623670)
    gap_receita = (reest - BPC_TOTAL) * 139 * 1.03 / 1e6  # ATR meta × CONSECANA

    res["kpis_2026"] = {
        "moa_acum":    round(moa_acum),
        "moa_bpc":     BPC_TOTAL,
        "exec_pct":    round(exec_pct, 1),
        "reest":       round(reest),
        "gap_moagem":  round(reest - BPC_TOTAL),
        "gap_receita": round(gap_receita, 1),
        "atr_acum":    boletim.get("atr_acum", 126.51),
        "atr_meta":    138.66,
        "aprov_acum":  boletim.get("aprov_acum", 57.25),
        "egi_acum":    boletim.get("egi_acum", 87.10),
        "rtc_acum":    boletim.get("rtc_acum", 94.67),
        "mh_acum":     boletim.get("mh_acum", 526.78),
        "broca_iff":   round(broca.get("broca_total", 0.916), 3),
        "tch_semana":  broca.get("tch_semana", 101.11),
    }

    return res

# ─── GERAÇÃO HTML ─────────────────────────────────────────────────────────────
def gerar_html(hist, bd, boletim, broca, frota, analises):
    now = datetime.now()
    now_str = now.strftime("%d/%m/%Y %H:%M")
    kpis = analises["kpis_2026"]

    # Preparar dados JS
    hist_safras   = analises.get("hist_safras", [])
    tl2026        = analises.get("timeline_2026", [])
    top_faz       = analises.get("top_fazendas", [])
    bot_faz       = analises.get("bot_fazendas", [])
    variedades    = analises.get("variedades", [])
    est_curva     = analises.get("estagio_curva", {})
    tch_hist      = analises.get("tch_historico", {})
    safra_rec     = analises.get("safra_bd_recente", "22324")

    # JS arrays histórico safras
    hs_anos  = json.dumps([str(r["ano"]) for r in reversed(hist_safras)])
    hs_moa   = json.dumps([r["moa"]  for r in reversed(hist_safras)])
    hs_atr   = json.dumps([r["atr"]  for r in reversed(hist_safras)])
    hs_egi   = json.dumps([r["egi"]  for r in reversed(hist_safras)])
    hs_mh    = json.dumps([r["mh"]   for r in reversed(hist_safras)])
    hs_aprov = json.dumps([r["aprov"] for r in reversed(hist_safras)])

    # JS timeline 2026
    tl_dts   = json.dumps([d["dt"][5:] for d in tl2026])
    tl_moa   = json.dumps([d["moa"]  for d in tl2026])
    tl_atr   = json.dumps([d["atr"]  for d in tl2026])
    tl_aprov = json.dumps([d["aprov"] for d in tl2026])
    tl_mh    = json.dumps([d["mh"]   for d in tl2026])

    # JS top fazendas
    tf_faz  = json.dumps([r["faz"]  for r in top_faz])
    tf_tch  = json.dumps([r["tch"]  for r in top_faz])
    tf_tah  = json.dumps([r["tah"]  for r in top_faz])
    tf_atr  = json.dumps([r["atr"]  for r in top_faz])

    # JS variedades
    var_nms = json.dumps([r["var"][:12] for r in variedades[:15]])
    var_tch = json.dumps([r["tch"] for r in variedades[:15]])
    var_tah = json.dumps([r["tah"] for r in variedades[:15]])
    var_atr = json.dumps([r["atr"] for r in variedades[:15]])

    # JS BPC
    bpc_moa_js  = json.dumps(BPC["moagem"])
    bpc_atr_js  = json.dumps(BPC["atr"])
    bpc_egi_js  = json.dumps(BPC["egi"])
    bpc_aprov_js= json.dumps(BPC["aprov"])

    # Moagem real por mês 2026
    real_moa_2026 = [
        boletim.get("moa_mar"),
        boletim.get("moa_abr"),
        boletim.get("moa_mai"),
        boletim.get("moa_jun"),
        None, None, None, None, None
    ]
    real_moa_js = json.dumps(real_moa_2026)

    # TCH histórico por safra
    saf_tch_keys = sorted(tch_hist.keys())
    saf_tch_vals = json.dumps([tch_hist[s]["tch"] for s in saf_tch_keys])
    saf_atr_vals = json.dumps([tch_hist[s]["atr"] for s in saf_tch_keys])
    saf_tah_vals = json.dumps([tch_hist[s]["tah"] for s in saf_tch_keys])
    saf_tch_anos = json.dumps(saf_tch_keys)

    # Curva de estágio
    est_ord  = ["1C","2C","3C","4C","5C","6C","7C","8C","9C"]
    est_tchs = [est_curva.get(e) for e in est_ord]
    est_tchs_js = json.dumps(est_tchs)

    # Frota classes
    frota_cls   = json.dumps(list(frota.get("classes",{}).keys())[:8])
    frota_cnt   = json.dumps([frota["classes"][k] for k in list(frota.get("classes",{}).keys())[:8]])

    # KPI cards helpers
    def kpi_color(val, plan, inv=False):
        if not val or not plan: return ""
        r = val/plan
        if inv: r = 2 - r
        return "" if r >= 0.95 else ("yellow" if r >= 0.80 else "red")

    c_moa  = kpi_color(kpis["moa_acum"], kpis["moa_bpc"] * kpis["exec_pct"]/100 * 0.9)
    c_atr  = "" if kpis["atr_acum"] >= kpis["atr_meta"] * 0.95 else "yellow"
    c_bro  = "" if kpis.get("broca_iff", 1) <= 1.0 else "red"

    def delta_html(real, plan, suffix="", inv=False, fmt_fn=lambda v: f"{v:,.1f}"):
        if real is None or plan is None: return ""
        delta = real - plan
        pct = delta/plan*100 if plan else 0
        if inv:
            color = "#00C853" if delta <= 0 else "#FF1744"
        else:
            color = "#00C853" if delta >= 0 else "#FF1744"
        arrow = "▲" if delta >= 0 else "▼"
        return f'<span style="color:{color}">{arrow} {fmt_fn(abs(delta))}{suffix} ({pct:+.1f}%)</span>'

    # --- TABLE rows ---
    top_faz_rows = ""
    for i, r in enumerate(top_faz[:15], 1):
        tah_color = "#00C853" if r["tah"] >= 14 else ("#FFD600" if r["tah"] >= 11 else "#FF1744")
        vars_str = ", ".join(r.get("vars",[])) if r.get("vars") else "—"
        top_faz_rows += f"""<tr>
          <td style="text-align:center;color:#90A4AE">{i}</td>
          <td><strong>{r['faz']}</strong></td>
          <td style="text-align:center">{r['amb']}</td>
          <td style="text-align:right">{fmt(r['area'],0)}</td>
          <td style="text-align:right">{fmt(r['tch'],1)}</td>
          <td style="text-align:right">{fmt(r['atr'],1)}</td>
          <td style="text-align:right;color:{tah_color};font-weight:700">{fmt(r['tah'],2)}</td>
          <td style="font-size:0.75rem;color:#90A4AE">{vars_str[:40]}</td>
        </tr>"""

    bot_faz_rows = ""
    for r in bot_faz[:8]:
        bot_faz_rows += f"""<tr>
          <td><strong style="color:#FF1744">{r['faz']}</strong></td>
          <td style="text-align:center">{r['amb']}</td>
          <td style="text-align:right">{fmt(r['area'],0)}</td>
          <td style="text-align:right">{fmt(r['tch'],1)}</td>
          <td style="text-align:right">{fmt(r['atr'],1)}</td>
          <td style="text-align:right;color:#FF1744;font-weight:700">{fmt(r['tah'],2)}</td>
        </tr>"""

    var_rows = ""
    for i, r in enumerate(variedades[:20], 1):
        tah_color = "#00C853" if r["tah"] >= 14 else ("#FFD600" if r["tah"] >= 11 else "#FF1744")
        var_rows += f"""<tr>
          <td style="text-align:center;color:#90A4AE">{i}</td>
          <td><strong>{r['var']}</strong></td>
          <td style="text-align:right">{fmt(r['area'],0)}</td>
          <td style="text-align:right">{fmt(r['tch'],1)}</td>
          <td style="text-align:right">{fmt(r['atr'],1)}</td>
          <td style="text-align:right;color:{tah_color};font-weight:700">{fmt(r['tah'],2)}</td>
          <td style="text-align:center;color:#90A4AE">{r['n_safras']}</td>
        </tr>"""

    hist_saf_rows = ""
    for r in hist_safras:
        moa_k = r["moa"] // 1000
        hist_saf_rows += f"""<tr>
          <td><strong>{r['ano']}</strong></td>
          <td style="text-align:right">{moa_k}K</td>
          <td style="text-align:right">{fmt(r['atr'],2)}</td>
          <td style="text-align:right">{fmt(r['egi'],2)}%</td>
          <td style="text-align:right">{fmt(r['mh'],1)}</td>
          <td style="text-align:right">{fmt(r['aprov'],1)}%</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UMOE BI Enterprise | Safra 2026/27</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{{
  --bg:#060E1F;--bg2:#0A1628;--bg3:#0F1E3A;--card:#111D35;--card2:#162445;
  --border:#1E3060;--green:#00C853;--gold:#FFD600;--red:#FF1744;
  --orange:#FF6D00;--blue:#42A5F5;--purple:#AB47BC;--cyan:#00BCD4;
  --text:#E8EAF6;--text2:#90A4AE;--text3:#546E7A;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;font-size:13px;min-height:100vh}}
/* HEADER */
.header{{background:linear-gradient(135deg,#060E1F 0%,#0F1E3A 50%,#060E1F 100%);
  border-bottom:2px solid var(--green);padding:10px 24px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:200;box-shadow:0 2px 20px rgba(0,200,83,0.15)}}
.logo-ring{{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--green),#005523);
  display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:900;color:#fff;
  box-shadow:0 0 0 3px rgba(0,200,83,0.3),0 0 16px rgba(0,200,83,0.3)}}
.h-title{{font-size:1.1rem;font-weight:700;color:var(--gold);letter-spacing:1.5px}}
.h-sub{{font-size:0.7rem;color:var(--text2);margin-top:2px}}
.badge{{background:rgba(0,200,83,0.1);border:1px solid rgba(0,200,83,0.4);
  border-radius:20px;padding:3px 12px;font-size:0.72rem;color:var(--green)}}
.dot{{display:inline-block;width:7px;height:7px;border-radius:50%;
  background:var(--green);margin-right:6px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 rgba(0,200,83,0.4)}}50%{{box-shadow:0 0 0 5px rgba(0,200,83,0)}}}}
/* TABS */
.tabs{{background:var(--bg2);border-bottom:1px solid var(--border);
  display:flex;padding:0 16px;gap:2px;overflow-x:auto;scrollbar-width:thin}}
.tab{{padding:12px 18px;cursor:pointer;font-weight:600;font-size:0.78rem;
  color:var(--text3);border-bottom:3px solid transparent;transition:all 0.2s;
  white-space:nowrap;letter-spacing:0.5px;user-select:none}}
.tab:hover{{color:var(--text2);background:rgba(255,255,255,0.03)}}
.tab.active{{color:var(--gold);border-bottom-color:var(--gold);background:rgba(255,214,0,0.04)}}
/* LAYOUT */
.content{{display:none;padding:20px 24px;max-width:1800px;margin:0 auto}}
.content.active{{display:block}}
.g4{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}}
.g3{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px}}
.g2{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:20px}}
.g6{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:20px}}
.g53{{display:grid;grid-template-columns:5fr 3fr;gap:14px;margin-bottom:20px}}
/* CARDS */
.card{{background:var(--card);border:1px solid var(--border);border-radius:14px;
  padding:18px;position:relative;overflow:hidden;transition:box-shadow 0.2s}}
.card:hover{{box-shadow:0 4px 20px rgba(0,0,0,0.3)}}
.card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--green),var(--cyan))}}
.card.red::before{{background:linear-gradient(90deg,var(--red),var(--orange))}}
.card.yellow::before{{background:linear-gradient(90deg,var(--gold),var(--orange))}}
.card.blue::before{{background:linear-gradient(90deg,var(--blue),var(--cyan))}}
.card.purple::before{{background:linear-gradient(90deg,var(--purple),var(--blue))}}
.kpi-lbl{{font-size:0.68rem;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}}
.kpi-val{{font-size:1.8rem;font-weight:800;line-height:1;margin-bottom:4px}}
.kpi-big{{font-size:2.4rem}}
.kpi-plan{{font-size:0.72rem;color:var(--text3);margin-top:4px}}
.kpi-delta{{font-size:0.8rem;margin-top:6px}}
.pb{{height:6px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;margin-top:8px}}
.pf{{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--green),#00E676);transition:width 1s}}
.pf.red{{background:linear-gradient(90deg,var(--red),#FF5252)}}
.pf.yellow{{background:linear-gradient(90deg,var(--gold),#FFEA00)}}
/* CHART CARDS */
.chart-card{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:18px}}
.chart-title{{font-size:0.72rem;font-weight:600;color:var(--text2);
  text-transform:uppercase;letter-spacing:0.5px;margin-bottom:14px}}
/* SECTION */
.sec{{font-size:0.85rem;font-weight:700;color:var(--gold);
  margin:22px 0 14px;border-left:3px solid var(--green);padding-left:10px;
  text-transform:uppercase;letter-spacing:1px}}
/* ALERT BAR */
.alert{{background:linear-gradient(135deg,rgba(255,23,68,0.15),rgba(255,109,0,0.08));
  border:1px solid rgba(255,23,68,0.4);border-radius:10px;
  padding:10px 18px;margin-bottom:18px;display:flex;align-items:center;gap:12px;
  font-weight:600;font-size:0.85rem;color:#FF8A80}}
.alert.warn{{background:rgba(255,214,0,0.08);border-color:rgba(255,214,0,0.3);color:var(--gold)}}
.alert.ok{{background:rgba(0,200,83,0.08);border-color:rgba(0,200,83,0.3);color:var(--green)}}
/* TABLE */
.tbl-wrap{{background:var(--card);border:1px solid var(--border);border-radius:14px;overflow:hidden;margin-bottom:18px}}
.tbl-hdr{{background:var(--card2);padding:10px 18px;font-size:0.72rem;
  font-weight:700;color:var(--gold);text-transform:uppercase;letter-spacing:1px;
  border-bottom:1px solid var(--border)}}
table{{width:100%;border-collapse:collapse}}
th{{background:var(--card2);padding:8px 12px;font-size:0.7rem;color:var(--text2);
  text-transform:uppercase;letter-spacing:0.5px;font-weight:600;border-bottom:1px solid var(--border)}}
td{{padding:7px 12px;border-bottom:1px solid rgba(255,255,255,0.04);font-size:0.82rem}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:rgba(255,255,255,0.02)}}
/* METRIC GRID */
.metric-row{{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap}}
.metric-chip{{background:rgba(255,255,255,0.05);border:1px solid var(--border);
  border-radius:8px;padding:6px 12px;font-size:0.8rem}}
.metric-chip span{{color:var(--gold);font-weight:700}}
/* SCORE CARD */
.score{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:18px}}
.score-item{{background:var(--card2);border:1px solid var(--border);border-radius:10px;
  padding:10px;text-align:center}}
.score-v{{font-size:1.3rem;font-weight:800;margin-bottom:2px}}
.score-l{{font-size:0.62rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.5px}}
/* WATERFALL */
.wfall{{display:flex;gap:8px;margin-bottom:18px;align-items:flex-end;height:120px}}
.wf-bar{{flex:1;background:rgba(255,255,255,0.05);border-radius:4px 4px 0 0;
  position:relative;display:flex;align-items:flex-end;justify-content:center}}
.wf-fill{{width:100%;border-radius:4px 4px 0 0;transition:height 1s}}
.wf-lbl{{position:absolute;bottom:-20px;font-size:0.68rem;color:var(--text3);white-space:nowrap}}
/* DRILL-DOWN */
.drill-btn{{background:none;border:1px solid var(--border);border-radius:6px;
  padding:4px 10px;color:var(--blue);cursor:pointer;font-size:0.75rem;transition:all 0.2s}}
.drill-btn:hover{{background:rgba(66,165,245,0.1);border-color:var(--blue)}}
/* NOTE */
.note{{font-size:0.72rem;color:var(--text3);padding:8px 12px;
  background:rgba(255,255,255,0.02);border-radius:6px;margin-top:10px}}
/* RESPONSIVE */
@media(max-width:1200px){{.g4{{grid-template-columns:repeat(2,1fr)}}.g6{{grid-template-columns:repeat(3,1fr)}}}}
@media(max-width:768px){{.g4,.g3,.g2,.g6{{grid-template-columns:1fr}}}}
</style>
</head>
<body>

<div class="header">
  <div style="display:flex;align-items:center;gap:14px">
    <div class="logo-ring">U</div>
    <div>
      <div class="h-title">UMOE BIOENERGY &nbsp;|&nbsp; BI ENTERPRISE</div>
      <div class="h-sub">Safra 2026/27 &nbsp;&bull;&nbsp; Inteligência de Dados para Tomada de Decisão &nbsp;&bull;&nbsp; {now_str}</div>
    </div>
  </div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
    <div class="badge"><span class="dot"></span>Live &nbsp;|&nbsp; {now_str}</div>
    <div style="font-size:0.68rem;color:var(--text3)">Histórico Diário · BD SAFRAS · TCH-BROCA · BPC · Boletim PDF</div>
  </div>
</div>

<div class="tabs">
  <div class="tab active" onclick="switchTab(0)">&#x1F3AF;&nbsp; EXECUTIVO</div>
  <div class="tab" onclick="switchTab(1)">&#x1F4C8;&nbsp; OPERACIONAL</div>
  <div class="tab" onclick="switchTab(2)">&#x1F33E;&nbsp; AGR&Iacute;COLA</div>
  <div class="tab" onclick="switchTab(3)">&#x1F331;&nbsp; VARIEDADES</div>
  <div class="tab" onclick="switchTab(4)">&#x1F3ED;&nbsp; INDUSTRIAL</div>
  <div class="tab" onclick="switchTab(5)">&#x1F4CA;&nbsp; HIST&Oacute;RICO SAFRAS</div>
  <div class="tab" onclick="switchTab(6)">&#x1F4A1;&nbsp; INTELIG&Ecirc;NCIA</div>
</div>

<!-- ══════════════════════════════════════════════════════════
     TAB 0 — EXECUTIVO
══════════════════════════════════════════════════════════ -->
<div class="content active" id="tab0">

  <div class="alert">
    <div style="font-size:1.4rem">&#x26A0;</div>
    <div><strong>SAFRA 2026/27 — ALERTA CRÍTICO:</strong>
      Reestimativa {fmt(kpis['reest']/1e6,2)} M t vs BPC {fmt(BPC_TOTAL/1e6,2)} M t
      &nbsp;|&nbsp; Gap: <span style="color:#FF5252">{fmt((kpis['reest']-BPC_TOTAL)/1e3,0)}K t ({(kpis['reest']/BPC_TOTAL-1)*100:+.1f}%)</span>
      &nbsp;|&nbsp; Impacto receita estimado: <span style="color:#FF5252">R$ {abs(kpis['gap_receita']):.1f} M</span>
    </div>
  </div>

  <!-- KPIs master -->
  <div class="g4">
    <div class="card {kpi_color(kpis['moa_acum'], kpis['moa_bpc']*kpis['exec_pct']/100*0.9)}">
      <div class="kpi-lbl">&#x1F6A6; Moagem Acumulada Mar–14/Jun</div>
      <div class="kpi-val kpi-big">{fmt(kpis['moa_acum']/1e6,3)}<small style="font-size:0.35em;color:var(--text2)"> M t</small></div>
      <div class="kpi-plan">BPC Plano Total: {fmt(BPC_TOTAL/1e6,3)} M t</div>
      <div class="kpi-delta">{delta_html(kpis['moa_acum'], kpis['moa_bpc']*kpis['exec_pct']/100, " t", fmt_fn=lambda v: f"{v/1e3:.0f}K")}</div>
      <div class="pb"><div class="pf {'red' if kpis['exec_pct']<70 else 'yellow' if kpis['exec_pct']<85 else ''}" style="width:{min(kpis['exec_pct'],100):.1f}%"></div></div>
      <div style="font-size:0.72rem;color:var(--text3);margin-top:4px">{kpis['exec_pct']:.1f}% da safra executada</div>
    </div>
    <div class="card yellow">
      <div class="kpi-lbl">&#x1F4C9; Reestimativa Final Safra</div>
      <div class="kpi-val kpi-big">{fmt(kpis['reest']/1e6,3)}<small style="font-size:0.35em;color:var(--text2)"> M t</small></div>
      <div class="kpi-plan">BPC: {fmt(BPC_TOTAL/1e6,3)} M t</div>
      <div class="kpi-delta"><span style="color:#FF1744">▼ {fmt(abs(kpis['gap_moagem'])/1e3,0)}K t ({(kpis['reest']/BPC_TOTAL-1)*100:+.1f}%)</span></div>
      <div class="pb"><div class="pf yellow" style="width:{min(kpis['reest']/BPC_TOTAL*100,100):.1f}%"></div></div>
      <div style="font-size:0.72rem;color:var(--text3);margin-top:4px">Impacto receita: R$ {abs(kpis['gap_receita']):.1f} M</div>
    </div>
    <div class="card {c_atr}">
      <div class="kpi-lbl">&#x1F36D; ATR Ponderado Acumulado</div>
      <div class="kpi-val kpi-big">{kpis['atr_acum']:.2f}<small style="font-size:0.35em;color:var(--text2)"> kg/t</small></div>
      <div class="kpi-plan">Meta safra: 138.66 kg/t | CONSECANA R$1,03/kg</div>
      <div class="kpi-delta">{delta_html(kpis['atr_acum'], kpis['atr_meta'], " kg/t")}</div>
      <div class="pb"><div class="pf yellow" style="width:{min(kpis['atr_acum']/kpis['atr_meta']*100,100):.1f}%"></div></div>
      <div style="font-size:0.72rem;color:var(--text3);margin-top:4px">Recuperação: Jun/26 → {kpis.get('atr_acum',126.5):.2f} (crescendo)</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">&#x26A1; Eficiência Industrial Global (EGI)</div>
      <div class="kpi-val kpi-big">{kpis['egi_acum']:.2f}<small style="font-size:0.35em;color:var(--text2)"> %</small></div>
      <div class="kpi-plan">RTC: {kpis['rtc_acum']:.2f}% | Moagem horária: {kpis['mh_acum']:.1f} t/h</div>
      <div class="kpi-delta"><span style="color:#00C853">▲ Eficiência OK — problema é volume</span></div>
      <div class="pb"><div class="pf" style="width:{min(kpis['egi_acum'],100):.1f}%"></div></div>
    </div>
  </div>

  <!-- Score strip -->
  <div class="score">
    <div class="score-item">
      <div class="score-v" style="color:var(--gold)">{kpis['exec_pct']:.1f}%</div>
      <div class="score-l">Execução Safra</div>
    </div>
    <div class="score-item">
      <div class="score-v" style="color:{('#00C853' if kpis['aprov_acum']>=70 else '#FFD600')}">{kpis['aprov_acum']:.1f}%</div>
      <div class="score-l">Aproveitamento</div>
    </div>
    <div class="score-item">
      <div class="score-v" style="color:var(--blue)">{kpis['mh_acum']:.0f}</div>
      <div class="score-l">t/h Acumulado</div>
    </div>
    <div class="score-item">
      <div class="score-v" style="color:{('#00C853' if kpis.get('broca_iff',1)<=1.0 else '#FF1744')}">{kpis.get('broca_iff',0.916):.3f}%</div>
      <div class="score-l">IFF Broca (≤1%)</div>
    </div>
    <div class="score-item">
      <div class="score-v" style="color:var(--cyan)">{kpis.get('tch_semana',101.1):.1f}</div>
      <div class="score-l">TCH Semana 15</div>
    </div>
    <div class="score-item">
      <div class="score-v" style="color:var(--red)">R${abs(kpis['gap_receita']):.0f}M</div>
      <div class="score-l">Gap Receita</div>
    </div>
  </div>

  <div class="g2">
    <div class="chart-card">
      <div class="chart-title">Moagem Mensal 2026/27 — BPC vs Real vs Reestimativa</div>
      <canvas id="c_exec_moa" height="130"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">ATR Acumulado Mensal — Real vs BPC</div>
      <canvas id="c_exec_atr" height="130"></canvas>
    </div>
  </div>

  <div class="sec">&#x1F3AF; Diagnóstico Executivo — Safra 2026/27</div>
  <div class="g3">
    <div style="display:flex;flex-direction:column;gap:10px">
      <div style="background:rgba(0,200,83,0.06);border:1px solid rgba(0,200,83,0.25);border-radius:10px;padding:14px">
        <div style="font-weight:700;color:var(--green);margin-bottom:6px;font-size:0.85rem">&#x2705; PONTOS FORTES</div>
        <div style="font-size:0.8rem;color:var(--text2);line-height:1.8">
          • ATR em recuperação: Jun/26 131.68 &gt; Mai 127.15 &gt; Abr 125.11<br>
          • Broca controlada: IFF {kpis.get('broca_iff',0.916):.3f}% (meta ≤1.0%)<br>
          • EGI acum. {kpis['egi_acum']:.2f}% — problema é volume, não eficiência<br>
          • Jun/26 acelerando: {kpis['mh_acum']:.0f} t/h vs Mai {BPC['moagem'][2]/30/24:.0f} t/h<br>
          • TCH sem.15: {kpis.get('tch_semana',101.1):.1f} t/ha — acima da estimativa
        </div>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;gap:10px">
      <div style="background:rgba(255,23,68,0.06);border:1px solid rgba(255,23,68,0.25);border-radius:10px;padding:14px">
        <div style="font-weight:700;color:var(--red);margin-bottom:6px;font-size:0.85rem">&#x274C; RISCOS CRÍTICOS</div>
        <div style="font-size:0.8rem;color:var(--text2);line-height:1.8">
          • Gap moagem: {fmt(abs(kpis['gap_moagem'])/1e3,0)}K t abaixo do BPC (-{abs((kpis['reest']/BPC_TOTAL-1)*100):.1f}%)<br>
          • Mai/26 catastrófico: 178K t vs 340K planejado (-47.5%)<br>
          • ATR {kpis['atr_acum']:.2f} kg/t vs meta 138.66 (gap: {kpis['atr_acum']-138.66:+.2f})<br>
          • 15.173 ha 4C+ com TCH 64 vs 99.6 t/ha no 1C<br>
          • CCT R$50.0/t vs orçado R$38.3/t (+30.5%)
        </div>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;gap:10px">
      <div style="background:rgba(255,214,0,0.06);border:1px solid rgba(255,214,0,0.25);border-radius:10px;padding:14px">
        <div style="font-weight:700;color:var(--gold);margin-bottom:6px;font-size:0.85rem">&#x1F3AF; AÇÕES PRIORITÁRIAS</div>
        <div style="font-size:0.8rem;color:var(--text2);line-height:1.8">
          • <strong style="color:#fff">1.</strong> Maximizar aproveitamento Jul-Set (meta &gt;85%)<br>
          • <strong style="color:#fff">2.</strong> Acelerar renovação 4C+ (prioridade ROI)<br>
          • <strong style="color:#fff">3.</strong> Variedades: substituir CTC15 por CTC9006/RB92579<br>
          • <strong style="color:#fff">4.</strong> Maturadores: antecipar para compensar ATR<br>
          • <strong style="color:#fff">5.</strong> CHI: reduzir paradas controláveis &lt;R$5K/dia
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════
     TAB 1 — OPERACIONAL (timeline 2026)
══════════════════════════════════════════════════════════ -->
<div class="content" id="tab1">
  <div class="alert warn">
    <span>&#x1F4CB;</span>
    <span>Últimos 60 dias de operação (2026) &nbsp;|&nbsp; {len(tl2026)} dias com dados &nbsp;|&nbsp; Fonte: Histórico Diário Safras</span>
  </div>

  <div class="g4">
    <div class="card">
      <div class="kpi-lbl">Moagem Diária Média (Jun)</div>
      <div class="kpi-val">{fmt(sum(d['moa'] for d in tl2026[-14:] if d['moa'])/(max(sum(1 for d in tl2026[-14:] if d['moa']),1)),0)} t</div>
      <div class="kpi-plan">BPC Jun: {fmt(BPC['moagem'][3]/30,0)} t/dia</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">ATR Médio (Jun)</div>
      <div class="kpi-val">{fmt(sum(d['atr'] for d in tl2026[-14:] if d['atr'])/(max(sum(1 for d in tl2026[-14:] if d['atr']),1)),2)} kg/t</div>
      <div class="kpi-plan">BPC Jun/26: {BPC['atr'][3]} kg/t</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Aproveitamento Médio (Jun)</div>
      <div class="kpi-val">{fmt(sum(d['aprov'] for d in tl2026[-14:] if d['aprov'])/(max(sum(1 for d in tl2026[-14:] if d['aprov']),1)),1)}%</div>
      <div class="kpi-plan">BPC Jun/26: {BPC['aprov'][3]:.1f}%</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Moagem Horária (Jun)</div>
      <div class="kpi-val">{fmt(sum(d['mh'] for d in tl2026[-14:] if d['mh'])/(max(sum(1 for d in tl2026[-14:] if d['mh']),1)),1)} t/h</div>
      <div class="kpi-plan">BPC: 564.35 t/h</div>
    </div>
  </div>

  <div class="chart-card" style="margin-bottom:16px">
    <div class="chart-title">Moagem Diária Acumulada 2026 — Últimos 60 Dias</div>
    <canvas id="c_op_moa" height="100"></canvas>
  </div>
  <div class="g3">
    <div class="chart-card">
      <div class="chart-title">ATR Diário 2026</div>
      <canvas id="c_op_atr" height="130"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Aproveitamento Diário %</div>
      <canvas id="c_op_aprov" height="130"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Moagem Horária (t/h)</div>
      <canvas id="c_op_mh" height="130"></canvas>
    </div>
  </div>

  <div class="tbl-wrap">
    <div class="tbl-hdr">Últimos 20 Dias Operacionais &mdash; Indicadores Diários</div>
    <table>
      <thead>
        <tr><th>Data</th><th style="text-align:right">Moagem (t)</th><th style="text-align:right">ATR</th>
          <th style="text-align:right">Aprov.%</th><th style="text-align:right">t/h</th>
          <th style="text-align:right">EGI%</th><th style="text-align:right">AEHC (L)</th></tr>
      </thead>
      <tbody>
        {"".join(f'''<tr>
          <td><strong>{d['dt'][5:]}</strong></td>
          <td style="text-align:right">{fmt(d['moa'],0)}</td>
          <td style="text-align:right;color:{('#00C853' if (d['atr'] or 0)>=130 else '#FFD600')}">{fmt(d['atr'],2)}</td>
          <td style="text-align:right;color:{('#00C853' if (d['aprov'] or 0)>=70 else ('#FFD600' if (d['aprov'] or 0)>=50 else '#FF1744'))}">{fmt(d['aprov'],1)}%</td>
          <td style="text-align:right">{fmt(d['mh'],1)}</td>
          <td style="text-align:right">{fmt(d['egi'],2)}%</td>
          <td style="text-align:right">{fmt(d['aehc']/1e6 if d['aehc'] else None,3)} M</td>
        </tr>''' for d in reversed(tl2026[-20:]))}
      </tbody>
    </table>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════
     TAB 2 — AGRÍCOLA (fazendas)
══════════════════════════════════════════════════════════ -->
<div class="content" id="tab2">
  <div class="alert warn">
    <span>&#x1F33E;</span>
    <span>Dados granulares BD SAFRAS &nbsp;|&nbsp; Safra de referência: {safra_rec} &nbsp;|&nbsp; 407 fazendas cadastradas &nbsp;|&nbsp; Média ponderada por área</span>
  </div>

  <div class="g4">
    <div class="card blue">
      <div class="kpi-lbl">Melhor TAH Histórico</div>
      <div class="kpi-val">{fmt(top_faz[0]['tah'] if top_faz else 0,2)}</div>
      <div class="kpi-plan">Fazenda {top_faz[0]['faz'] if top_faz else '—'} | Amb. {top_faz[0]['amb'] if top_faz else '—'}</div>
      <div class="kpi-delta"><span style="color:var(--green)">t ATR/ha — Referência de excelência</span></div>
    </div>
    <div class="card">
      <div class="kpi-lbl">TCH Médio (Safra {safra_rec})</div>
      <div class="kpi-val">{fmt(sum(r['tch'] for r in top_faz[:15])/max(len(top_faz[:15]),1),1)}</div>
      <div class="kpi-plan">t/ha ponderado | Top 15 fazendas</div>
    </div>
    <div class="card red">
      <div class="kpi-lbl">Pior Fazenda TAH</div>
      <div class="kpi-val" style="color:var(--red)">{fmt(bot_faz[0]['tah'] if bot_faz else 0,2)}</div>
      <div class="kpi-plan">Fazenda {bot_faz[0]['faz'] if bot_faz else '—'} — prioridade reforma</div>
      <div class="kpi-delta"><span style="color:#FF1744">Gap vs melhor: {fmt((top_faz[0]['tah']-bot_faz[0]['tah']) if (top_faz and bot_faz) else 0,2)} t ATR/ha</span></div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Canaviais 4C+ (Renovação Urgente)</div>
      <div class="kpi-val" style="color:var(--orange)">15.173 ha</div>
      <div class="kpi-plan">TCH 64 vs 99.6 t/ha no 1C</div>
      <div class="kpi-delta"><span style="color:#FF1744">▼ Perda de 35.6 t/ha por talhão</span></div>
    </div>
  </div>

  <div class="g53">
    <div class="chart-card">
      <div class="chart-title">Top 15 Fazendas — TAH vs TCH (Safra {safra_rec})</div>
      <canvas id="c_agri_faz" height="130"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Distribuição ATR por Fazenda</div>
      <canvas id="c_agri_atr" height="130"></canvas>
    </div>
  </div>

  <div class="g2">
    <div>
      <div class="tbl-wrap">
        <div class="tbl-hdr">&#x1F3C6; Top 15 Fazendas — Maior TAH (Safra {safra_rec})</div>
        <table>
          <thead>
            <tr><th>#</th><th>Fazenda</th><th>Amb.</th><th style="text-align:right">Área (ha)</th>
              <th style="text-align:right">TCH</th><th style="text-align:right">ATR</th>
              <th style="text-align:right">TAH</th><th>Variedades</th></tr>
          </thead>
          <tbody>{top_faz_rows}</tbody>
        </table>
      </div>
    </div>
    <div>
      <div class="tbl-wrap">
        <div class="tbl-hdr">&#x1F6A8; Fazendas Críticas — Menor TAH (Candidatas a Reforma)</div>
        <table>
          <thead>
            <tr><th>Fazenda</th><th>Amb.</th><th style="text-align:right">Área</th>
              <th style="text-align:right">TCH</th><th style="text-align:right">ATR</th><th style="text-align:right">TAH</th></tr>
          </thead>
          <tbody>{bot_faz_rows}</tbody>
        </table>
      </div>
      <div class="tbl-wrap" style="margin-top:14px">
        <div class="tbl-hdr">Curva de Decaimento TCH por Ciclo de Corte</div>
        <table>
          <thead><tr><th>Corte</th>{"".join(f'<th style="text-align:right">{e}</th>' for e in ["1C","2C","3C","4C","5C","6C","7C"])}</tr></thead>
          <tbody><tr>
            {"".join(f'<td style="text-align:right;color:{("#00C853" if (est_curva.get(e,0) or 0)>=90 else ("#FFD600" if (est_curva.get(e,0) or 0)>=75 else "#FF1744"))}">{fmt(est_curva.get(e),1)}</td>' for e in ["1C","2C","3C","4C","5C","6C","7C"])}
          </tr></tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="note">
    &#x1F9EE; TAH = Toneladas de ATR por Hectare &nbsp;&bull;&nbsp; Ranking baseado em área real colhida &nbsp;&bull;&nbsp;
    Fazendas com área &gt;5 ha incluídas &nbsp;&bull;&nbsp; Safra {safra_rec}
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════
     TAB 3 — VARIEDADES
══════════════════════════════════════════════════════════ -->
<div class="content" id="tab3">
  <div class="alert ok">
    <span>&#x1F331;</span>
    <span>Análise de 65 variedades cadastradas &nbsp;|&nbsp; Ponderada por área realizada &nbsp;|&nbsp; Múltiplas safras</span>
  </div>

  <div class="g3">
    <div class="chart-card">
      <div class="chart-title">Top 15 Variedades — TAH (t ATR/ha)</div>
      <canvas id="c_var_tah" height="160"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">TCH por Variedade</div>
      <canvas id="c_var_tch" height="160"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">ATR por Variedade (kg/t)</div>
      <canvas id="c_var_atr" height="160"></canvas>
    </div>
  </div>

  <div class="tbl-wrap">
    <div class="tbl-hdr">Ranking Completo de Variedades — Performance Consolidada (Todas as Safras)</div>
    <table>
      <thead>
        <tr><th>#</th><th>Variedade</th><th style="text-align:right">Área (ha)</th>
          <th style="text-align:right">TCH (t/ha)</th><th style="text-align:right">ATR (kg/t)</th>
          <th style="text-align:right">TAH</th><th style="text-align:center">Safras</th></tr>
      </thead>
      <tbody>{var_rows}</tbody>
    </table>
  </div>

  <div class="g2" style="margin-top:16px">
    <div style="background:rgba(0,200,83,0.06);border:1px solid rgba(0,200,83,0.2);border-radius:12px;padding:16px">
      <div class="sec" style="margin-top:0">&#x1F3C6; Variedades Campeãs</div>
      <div style="font-size:0.82rem;color:var(--text2);line-height:2">
        {"".join(f'<div>&#x2B50; <strong style="color:#E8EAF6">{r["var"]}</strong> — TAH {r["tah"]:.2f} | TCH {r["tch"]:.1f} | ATR {r["atr"]:.1f}</div>' for r in variedades[:5])}
      </div>
    </div>
    <div style="background:rgba(255,23,68,0.06);border:1px solid rgba(255,23,68,0.2);border-radius:12px;padding:16px">
      <div class="sec" style="margin-top:0;color:var(--red)">&#x26A0; Variedades para Substituição</div>
      <div style="font-size:0.82rem;color:var(--text2);line-height:2">
        {"".join(f'<div>&#x274C; <strong style="color:#E8EAF6">{r["var"]}</strong> — TAH {r["tah"]:.2f} | TCH {r["tch"]:.1f} | ATR {r["atr"]:.1f}</div>' for r in sorted(variedades, key=lambda x:x['tah'])[:5] if r['area']>100)}
      </div>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════
     TAB 4 — INDUSTRIAL
══════════════════════════════════════════════════════════ -->
<div class="content" id="tab4">
  <div class="g4">
    <div class="card">
      <div class="kpi-lbl">EGI Acumulado Real</div>
      <div class="kpi-val">{kpis['egi_acum']:.2f}%</div>
      <div class="kpi-plan">BPC Jun/26: {BPC['egi'][3]:.2f}%</div>
      <div class="kpi-delta">{delta_html(kpis['egi_acum'], BPC['egi'][3], "%")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">RTC Acumulado</div>
      <div class="kpi-val">{kpis['rtc_acum']:.2f}%</div>
      <div class="kpi-plan">BPC Jun/26: {BPC['rtc'][3]:.2f}%</div>
      <div class="kpi-delta">{delta_html(kpis['rtc_acum'], BPC['rtc'][3], "%")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Aproveitamento Acumulado</div>
      <div class="kpi-val">{kpis['aprov_acum']:.1f}%</div>
      <div class="kpi-plan">BPC prop. Mar–Jun: ~70.9%</div>
      <div class="kpi-delta">{delta_html(kpis['aprov_acum'], 70.9, " pp")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Moagem Horária Acum.</div>
      <div class="kpi-val">{kpis['mh_acum']:.1f} t/h</div>
      <div class="kpi-plan">BPC: 564.35 t/h</div>
      <div class="kpi-delta">{delta_html(kpis['mh_acum'], 564.35, " t/h")}</div>
    </div>
  </div>

  <div class="g2">
    <div class="chart-card">
      <div class="chart-title">EGI Diário 2026 — Tendência</div>
      <canvas id="c_ind_egi2" height="130"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Aproveitamento Diário % — 2026</div>
      <canvas id="c_ind_aprov2" height="130"></canvas>
    </div>
  </div>

  <div class="chart-card" style="margin-bottom:16px">
    <div class="chart-title">BPC Industrial Mensal — Plano vs Real Acumulado (Mar–14/Jun/2026)</div>
    <canvas id="c_ind_bpc" height="100"></canvas>
  </div>

  <div class="tbl-wrap">
    <div class="tbl-hdr">Plano Industrial Mensal BPC — Safra 2026/27 Completa</div>
    <table>
      <thead>
        <tr><th>Mês</th><th style="text-align:right">Moagem (t)</th><th style="text-align:right">Aprov.%</th>
          <th style="text-align:right">ATR</th><th style="text-align:right">EGI%</th>
          <th style="text-align:right">RTC%</th><th style="text-align:right">Et.Hid.</th>
          <th style="text-align:right">Et.Ani.</th><th style="text-align:right">Energia Exp.</th></tr>
      </thead>
      <tbody>
        {"".join(f'''<tr>
          <td><strong>{MESES[i]}</strong></td>
          <td style="text-align:right">{fmt(BPC['moagem'][i],0)}</td>
          <td style="text-align:right">{fmt(BPC['aprov'][i],2)}%</td>
          <td style="text-align:right">{BPC['atr'][i]}</td>
          <td style="text-align:right">{fmt(BPC['egi'][i],2)}%</td>
          <td style="text-align:right">{fmt(BPC['rtc'][i],2)}%</td>
          <td style="text-align:right">{fmt(BPC['etanol_hid'][i],0)}</td>
          <td style="text-align:right">{fmt(BPC['etanol_ani'][i],0)}</td>
          <td style="text-align:right">{fmt(BPC['energia_exp'][i],0)}</td>
        </tr>''' for i in range(9))}
        <tr style="font-weight:700;color:var(--gold);border-top:2px solid var(--green)">
          <td>TOTAL BPC</td>
          <td style="text-align:right">{fmt(BPC_TOTAL,0)}</td>
          <td style="text-align:right">{fmt(sum(BPC['aprov'])/9,2)}%</td>
          <td style="text-align:right">{fmt(sum(BPC['atr'])/9,1)}</td>
          <td style="text-align:right">{fmt(sum(BPC['egi'])/9,2)}%</td>
          <td style="text-align:right">{fmt(sum(BPC['rtc'])/9,2)}%</td>
          <td style="text-align:right">{fmt(sum(BPC['etanol_hid']),0)}</td>
          <td style="text-align:right">{fmt(sum(BPC['etanol_ani']),0)}</td>
          <td style="text-align:right">{fmt(sum(BPC['energia_exp']),0)}</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════
     TAB 5 — HISTÓRICO SAFRAS
══════════════════════════════════════════════════════════ -->
<div class="content" id="tab5">
  <div class="alert ok">
    <span>&#x1F4CA;</span>
    <span>Série histórica {hist_safras[-1]['ano'] if hist_safras else 2012}–2026 &nbsp;|&nbsp; {sum(r['moa'] for r in hist_safras)/1e6:.1f} M t processadas &nbsp;|&nbsp; Fonte: Histórico Diário Safras.xlsx</span>
  </div>

  <div class="g3">
    <div class="chart-card">
      <div class="chart-title">Moagem Total por Safra (t)</div>
      <canvas id="c_h_moa" height="160"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">ATR Médio por Safra (kg/t)</div>
      <canvas id="c_h_atr" height="160"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">EGI Médio por Safra (%)</div>
      <canvas id="c_h_egi" height="160"></canvas>
    </div>
  </div>

  <div class="g2">
    <div class="chart-card">
      <div class="chart-title">TCH Histórico por Safra — BD SAFRAS</div>
      <canvas id="c_h_tch" height="140"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Aproveitamento Médio Histórico (%)</div>
      <canvas id="c_h_aprov" height="140"></canvas>
    </div>
  </div>

  <div class="tbl-wrap">
    <div class="tbl-hdr">Resumo Histórico por Safra — Indicadores Consolidados</div>
    <table>
      <thead>
        <tr><th>Safra</th><th style="text-align:right">Moagem</th><th style="text-align:right">ATR</th>
          <th style="text-align:right">EGI%</th><th style="text-align:right">t/h</th><th style="text-align:right">Aprov.%</th></tr>
      </thead>
      <tbody>{hist_saf_rows}</tbody>
    </table>
  </div>

  <div class="tbl-wrap">
    <div class="tbl-hdr">TCH e ATR Histórico por Safra — BD SAFRAS (407 fazendas)</div>
    <table>
      <thead>
        <tr><th>Safra</th>{"".join(f'<th style="text-align:right">{s}</th>' for s in sorted(tch_hist.keys()))}</tr>
      </thead>
      <tbody>
        <tr><td><strong>TCH</strong></td>{"".join(f'<td style="text-align:right">{tch_hist[s]["tch"]:.1f}</td>' for s in sorted(tch_hist.keys()))}</tr>
        <tr><td><strong>ATR</strong></td>{"".join(f'<td style="text-align:right">{tch_hist[s]["atr"]:.1f}</td>' for s in sorted(tch_hist.keys()))}</tr>
        <tr><td><strong>TAH</strong></td>{"".join(f'<td style="text-align:right">{tch_hist[s]["tah"]:.2f}</td>' for s in sorted(tch_hist.keys()))}</tr>
        <tr><td><strong>Área (ha)</strong></td>{"".join(f'<td style="text-align:right">{tch_hist[s]["area"]:,.0f}</td>' for s in sorted(tch_hist.keys()))}</tr>
      </tbody>
    </table>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════
     TAB 6 — INTELIGÊNCIA
══════════════════════════════════════════════════════════ -->
<div class="content" id="tab6">
  <div class="sec">&#x1F4A1; Análise de Inteligência — Cruzamentos e Insights</div>

  <div class="g3">
    <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:18px">
      <div style="font-size:0.75rem;font-weight:700;color:var(--gold);text-transform:uppercase;margin-bottom:14px;letter-spacing:1px">
        &#x1F4B0; OPORTUNIDADE FINANCEIRA — Reforma 4C+
      </div>
      <div style="font-size:0.82rem;color:var(--text2);line-height:1.9">
        <div style="color:var(--text);font-weight:600;margin-bottom:8px">Análise: Renovação de 15.173 ha 4C+</div>
        <div>• TCH atual 4C+: <span style="color:#FF1744">64 t/ha</span></div>
        <div>• TCH potencial 1C: <span style="color:#00C853">99.6 t/ha</span></div>
        <div>• Ganho/ha: <span style="color:#00C853">+35.6 t/ha</span></div>
        <div>• Ganho total safra: <span style="color:#00C853">+540K t</span></div>
        <div>• Receita adicional: <span style="color:var(--gold);font-weight:700">~R$ 42 M/safra</span></div>
        <div style="margin-top:10px;padding:8px;background:rgba(0,200,83,0.08);border-radius:6px;font-size:0.78rem;color:#00C853">
          &#x2705; ROI de renovação: &lt;2 safras se priorizado estrategicamente
        </div>
      </div>
    </div>

    <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:18px">
      <div style="font-size:0.75rem;font-weight:700;color:var(--gold);text-transform:uppercase;margin-bottom:14px;letter-spacing:1px">
        &#x1F331; TROCA DE VARIEDADE — Impacto TAH
      </div>
      <div style="font-size:0.82rem;color:var(--text2);line-height:1.9">
        <div style="color:var(--text);font-weight:600;margin-bottom:8px">Substituição CTC15 → {variedades[0]['var'] if variedades else 'CTC9006'}</div>
        <div>• CTC15 TAH: <span style="color:#FF1744">≤ 7.6 t ATR/ha</span></div>
        <div>• {variedades[0]['var'] if variedades else 'Top'} TAH: <span style="color:#00C853">{variedades[0]['tah'] if variedades else 15.4:.2f} t ATR/ha</span></div>
        <div>• Diferença: <span style="color:#00C853">+{(variedades[0]['tah'] if variedades else 15.4)-7.6:.2f} t ATR/ha</span></div>
        <div>• Em 1.000 ha: <span style="color:var(--gold);font-weight:700">+{((variedades[0]['tah'] if variedades else 15.4)-7.6)*1000:,.0f} t ATR</span></div>
        <div>• Receita adicional: <span style="color:var(--gold);font-weight:700">R$ {((variedades[0]['tah'] if variedades else 15.4)-7.6)*1000*1030/1e6:.1f} M/1K ha</span></div>
        <div style="margin-top:10px;padding:8px;background:rgba(255,214,0,0.08);border-radius:6px;font-size:0.78rem;color:var(--gold)">
          &#x26A0; Verificar compatibilidade ambiente × solo antes de escalar
        </div>
      </div>
    </div>

    <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:18px">
      <div style="font-size:0.75rem;font-weight:700;color:var(--gold);text-transform:uppercase;margin-bottom:14px;letter-spacing:1px">
        &#x1F4C8; PROJEÇÃO FINAL SAFRA 2026/27
      </div>
      <div style="font-size:0.82rem;color:var(--text2);line-height:1.9">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <span>Pessimista (aprov. 60%)</span>
          <span style="color:#FF1744;font-weight:700">1.915 M t</span>
        </div>
        <div class="pb" style="margin-bottom:12px"><div class="pf red" style="width:69%"></div></div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <span>Base (Reestimativa)</span>
          <span style="color:var(--gold);font-weight:700">{fmt(kpis['reest']/1e6,3)} M t</span>
        </div>
        <div class="pb" style="margin-bottom:12px"><div class="pf yellow" style="width:{kpis['reest']/BPC_TOTAL*100:.0f}%"></div></div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <span>Otimista (aprov. 95%)</span>
          <span style="color:#00C853;font-weight:700">2.461 M t</span>
        </div>
        <div class="pb"><div class="pf" style="width:89%"></div></div>
        <div style="margin-top:12px;font-size:0.75rem;color:var(--text3)">
          Precisa de aprov. médio ≥82% (Jul–Nov) para atingir Reestimativa
        </div>
      </div>
    </div>
  </div>

  <div class="g2">
    <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:18px">
      <div style="font-size:0.75rem;font-weight:700;color:var(--gold);text-transform:uppercase;margin-bottom:14px">
        &#x1F4CB; PLANO DE AÇÃO PRIORIZADO POR IMPACTO R$
      </div>
      <div style="display:flex;flex-direction:column;gap:8px;font-size:0.82rem">
        {"".join(f'''<div style="display:flex;align-items:flex-start;gap:10px;padding:10px;background:rgba(255,255,255,0.03);border-radius:8px;border-left:3px solid {c}">
          <div style="font-size:1.2rem;min-width:24px">{ic}</div>
          <div><div style="color:var(--text);font-weight:600;margin-bottom:2px">{t}</div>
          <div style="color:var(--text2);font-size:0.78rem">{d}</div>
          <div style="color:{c};font-size:0.75rem;margin-top:3px;font-weight:600">{r}</div></div>
        </div>''' for ic,t,d,r,c in [
          ("1️⃣","Maximizar aproveitamento Jul–Set","Meta >85% | Cada 1pp = ~+8K t moagem","Impacto: R$8–12M por pp recuperado","#00C853"),
          ("2️⃣","Renovação prioritária 4C+ (15.173 ha)","TCH 64→99.6 t/ha | Priorizar Amb. A e B","Receita adicional: R$42M/safra","#00C853"),
          ("3️⃣","Substituir CTC15 em todos os novos plantios","TAH <7.6 | Trocar por CTC9006 ou top variedade","Ganho: +7 t ATR/ha vs CTC15","#FFD600"),
          ("4️⃣","Reduzir CHI controlável <R$5K/dia","Meta: CHI R$2K–5K/dia (amarelo)","Economia estimada: R$1.5–3M/safra","#FFD600"),
          ("5️⃣","Antecipar maturadores nas áreas com ATR <130","Corrigir curva de maturação Jul/Ago","Ganho: +3–5 kg ATR/t = R$3–8M","#FF6D00"),
        ])}
      </div>
    </div>

    <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:18px">
      <div style="font-size:0.75rem;font-weight:700;color:var(--gold);text-transform:uppercase;margin-bottom:14px">
        &#x1F4D0; ANÁLISE DE CORRELAÇÕES
      </div>
      <div style="font-size:0.82rem;color:var(--text2);line-height:2">
        <div style="color:var(--text);font-weight:600;margin-bottom:8px;font-size:0.85rem">O que os dados revelam:</div>
        <div>• <strong style="color:#fff">Ambiente E</strong> = maior TAH médio histórico → priorizar no mapa de renovação</div>
        <div>• <strong style="color:#fff">Ciclo 1C</strong> entrega ~55% mais TCH que 4C+ na média histórica</div>
        <div>• <strong style="color:#fff">ATR e aproveitamento</strong> crescem jun→set: janela de recuperação real</div>
        <div>• <strong style="color:#fff">EGI industrial</strong> consistente ~86–87%: perda é agrícola, não industrial</div>
        <div>• <strong style="color:#fff">Meses Jul–Set</strong> historicamente têm aproveitamento >80% → base para recuperação</div>
        <div>• <strong style="color:#fff">Fazendas top TAH</strong> concentram poucas variedades de alta performance</div>
        <div style="margin-top:12px;padding:10px;background:rgba(0,200,83,0.06);border-radius:8px;color:#00C853;font-size:0.78rem">
          &#x2714; VEREDICTO: Operação industrialmente eficiente. Gap é 100% agrícola:
          volume, renovação e variedades. Ações acima valem R$50–70M na próxima safra.
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════
     SCRIPTS
══════════════════════════════════════════════════════════ -->
<script>
function switchTab(n){{
  document.querySelectorAll('.tab').forEach((t,i)=>t.classList.toggle('active',i===n));
  document.querySelectorAll('.content').forEach((c,i)=>c.classList.toggle('active',i===n));
}}

const GREEN='#00C853',GOLD='#FFD600',RED='#FF1744',ORANGE='#FF6D00',
      BLUE='#42A5F5',PURPLE='#AB47BC',CYAN='#00BCD4',GRAY='rgba(255,255,255,0.15)';
const BORDER='rgba(255,255,255,0.06)',TEXT='#90A4AE';
Chart.defaults.color=TEXT;
Chart.defaults.borderColor=BORDER;
Chart.defaults.font.family="'Inter',system-ui,sans-serif";
Chart.defaults.font.size=11;

const MESES={json.dumps(MESES)};
const BPC_MOA={bpc_moa_js};
const BPC_ATR={bpc_atr_js};
const BPC_EGI={bpc_egi_js};
const BPC_APROV={bpc_aprov_js};
const REAL_MOA={real_moa_js};
const TL_DTS={tl_dts};
const TL_MOA={tl_moa};
const TL_ATR={tl_atr};
const TL_APROV={tl_aprov};
const TL_MH={tl_mh};
const HS_ANOS={hs_anos};
const HS_MOA={hs_moa};
const HS_ATR={hs_atr};
const HS_EGI={hs_egi};
const HS_MH={hs_mh};
const HS_APROV={hs_aprov};
const TF_FAZ={tf_faz};
const TF_TCH={tf_tch};
const TF_TAH={tf_tah};
const TF_ATR={tf_atr};
const VAR_NMS={var_nms};
const VAR_TCH={var_tch};
const VAR_TAH={var_tah};
const VAR_ATR={var_atr};
const SAF_ANOS={saf_tch_anos};
const SAF_TCH={saf_tch_vals};
const SAF_ATR={saf_atr_vals};
const SAF_TAH={saf_tah_vals};
const EST_TCH={est_tchs_js};

const OPT_STD = (ylabel='')=>(({{
  responsive:true,maintainAspectRatio:true,
  plugins:{{legend:{{labels:{{color:TEXT,boxWidth:12}}}},
    tooltip:{{backgroundColor:'rgba(10,22,40,0.95)',borderColor:BORDER,borderWidth:1}}}},
  scales:{{
    x:{{ticks:{{color:TEXT,maxRotation:35,font:{{size:10}}}},grid:{{color:BORDER}}}},
    y:{{ticks:{{color:TEXT}},grid:{{color:BORDER}},title:{{display:!!ylabel,text:ylabel,color:TEXT}}}}
  }}
}}));

window.addEventListener('DOMContentLoaded',()=>{{

  // TAB 0 — EXECUTIVO
  new Chart(document.getElementById('c_exec_moa'),{{type:'bar',
    data:{{labels:MESES,datasets:[
      {{label:'BPC',data:BPC_MOA,backgroundColor:'rgba(33,150,243,0.25)',borderColor:BLUE,borderWidth:1.5}},
      {{label:'Real',data:REAL_MOA,backgroundColor:REAL_MOA.map((v,i)=>v===null?'transparent':v>=BPC_MOA[i]*0.95?'rgba(0,200,83,0.7)':v>=BPC_MOA[i]*0.80?'rgba(255,214,0,0.7)':'rgba(255,23,68,0.7)'),borderWidth:0}},
      {{label:'Reestimativa',data:[null,null,null,null,330150,295980,280606,229236,216913],type:'line',borderColor:GOLD,borderWidth:2,borderDash:[4,4],pointRadius:3,fill:false}}
    ]}},options:OPT_STD('t')
  }});

  new Chart(document.getElementById('c_exec_atr'),{{type:'line',
    data:{{labels:MESES,datasets:[
      {{label:'BPC ATR',data:BPC_ATR,borderColor:BLUE,backgroundColor:'rgba(33,150,243,0.05)',tension:0.4,fill:true}},
      {{label:'Real',data:[117.80,125.11,127.15,131.68,null,null,null,null,null],borderColor:GREEN,pointRadius:5,pointBackgroundColor:GREEN,tension:0.3}}
    ]}},options:OPT_STD('kg/t')
  }});

  // TAB 1 — OPERACIONAL
  new Chart(document.getElementById('c_op_moa'),{{type:'line',
    data:{{labels:TL_DTS,datasets:[
      {{label:'Moagem (t)',data:TL_MOA,borderColor:GREEN,backgroundColor:'rgba(0,200,83,0.06)',tension:0.3,fill:true,pointRadius:2}}
    ]}},options:OPT_STD('t')
  }});
  new Chart(document.getElementById('c_op_atr'),{{type:'line',
    data:{{labels:TL_DTS,datasets:[
      {{label:'ATR (kg/t)',data:TL_ATR,borderColor:GOLD,tension:0.4,pointRadius:1}}
    ]}},options:OPT_STD('kg/t')
  }});
  new Chart(document.getElementById('c_op_aprov'),{{type:'line',
    data:{{labels:TL_DTS,datasets:[
      {{label:'Aprov.%',data:TL_APROV,borderColor:BLUE,tension:0.4,pointRadius:1,fill:false}},
      {{label:'Meta 70%',data:TL_DTS.map(()=>70),borderColor:ORANGE,borderDash:[5,5],borderWidth:1,pointRadius:0}}
    ]}},options:OPT_STD('%')
  }});
  new Chart(document.getElementById('c_op_mh'),{{type:'bar',
    data:{{labels:TL_DTS,datasets:[
      {{label:'t/h',data:TL_MH,backgroundColor:TL_MH.map(v=>v>=550?'rgba(0,200,83,0.6)':v>=450?'rgba(255,214,0,0.6)':'rgba(255,23,68,0.6)'),borderWidth:0}}
    ]}},options:OPT_STD('t/h')
  }});

  // TAB 2 — AGRÍCOLA
  new Chart(document.getElementById('c_agri_faz'),{{type:'bar',
    data:{{labels:TF_FAZ,datasets:[
      {{label:'TCH (t/ha)',data:TF_TCH,backgroundColor:'rgba(33,150,243,0.55)',borderColor:BLUE,borderWidth:1,yAxisID:'y'}},
      {{label:'TAH',data:TF_TAH,type:'line',borderColor:GOLD,pointRadius:4,pointBackgroundColor:GOLD,yAxisID:'y1',fill:false}}
    ]}},
    options:{{...OPT_STD(),scales:{{
      x:{{ticks:{{color:TEXT,maxRotation:45,font:{{size:9}}}},grid:{{color:BORDER}}}},
      y:{{ticks:{{color:TEXT}},grid:{{color:BORDER}},title:{{display:true,text:'TCH',color:TEXT}}}},
      y1:{{ticks:{{color:GOLD}},grid:{{display:false}},position:'right',title:{{display:true,text:'TAH',color:GOLD}}}}
    }}}}
  }});
  new Chart(document.getElementById('c_agri_atr'),{{type:'bar',
    data:{{labels:TF_FAZ,datasets:[
      {{label:'ATR (kg/t)',data:TF_ATR,backgroundColor:TF_ATR.map(v=>v>=138?GREEN:v>=128?GOLD:RED),borderWidth:0}}
    ]}},options:OPT_STD('kg/t')
  }});

  // TAB 3 — VARIEDADES
  new Chart(document.getElementById('c_var_tah'),{{type:'bar',
    data:{{labels:VAR_NMS,datasets:[
      {{label:'TAH (t ATR/ha)',data:VAR_TAH,backgroundColor:VAR_TAH.map(v=>v>=14?GREEN:v>=11?GOLD:RED),borderWidth:0}}
    ]}},options:OPT_STD('t ATR/ha')
  }});
  new Chart(document.getElementById('c_var_tch'),{{type:'bar',
    data:{{labels:VAR_NMS,datasets:[
      {{label:'TCH (t/ha)',data:VAR_TCH,backgroundColor:'rgba(33,150,243,0.6)',borderWidth:0}}
    ]}},options:OPT_STD('t/ha')
  }});
  new Chart(document.getElementById('c_var_atr'),{{type:'bar',
    data:{{labels:VAR_NMS,datasets:[
      {{label:'ATR (kg/t)',data:VAR_ATR,backgroundColor:VAR_ATR.map(v=>v>=138?GREEN:v>=125?GOLD:RED),borderWidth:0}}
    ]}},options:OPT_STD('kg/t')
  }});

  // TAB 4 — INDUSTRIAL
  new Chart(document.getElementById('c_ind_egi2'),{{type:'line',
    data:{{labels:TL_DTS,datasets:[
      {{label:'EGI%',data:{json.dumps([d['egi'] for d in tl2026])},borderColor:CYAN,tension:0.4,pointRadius:1}},
      {{label:'Meta',data:TL_DTS.map(()=>86),borderColor:ORANGE,borderDash:[5,5],borderWidth:1,pointRadius:0}}
    ]}},options:OPT_STD('%')
  }});
  new Chart(document.getElementById('c_ind_aprov2'),{{type:'line',
    data:{{labels:TL_DTS,datasets:[
      {{label:'Aprov.%',data:TL_APROV,borderColor:BLUE,tension:0.4,pointRadius:1,fill:false}},
      {{label:'BPC Jun 72.81%',data:TL_DTS.map(()=>72.81),borderColor:GOLD,borderDash:[5,5],borderWidth:1,pointRadius:0}}
    ]}},options:OPT_STD('%')
  }});
  new Chart(document.getElementById('c_ind_bpc'),{{type:'bar',
    data:{{labels:MESES,datasets:[
      {{label:'BPC Moagem',data:BPC_MOA,backgroundColor:'rgba(33,150,243,0.3)',borderColor:BLUE,borderWidth:1}},
      {{label:'Real',data:REAL_MOA,backgroundColor:REAL_MOA.map(v=>v?'rgba(0,200,83,0.6)':'transparent'),borderWidth:0}},
      {{label:'BPC EGI%',data:BPC_EGI,type:'line',yAxisID:'y1',borderColor:CYAN,pointRadius:3,fill:false,borderDash:[3,3]}}
    ]}},
    options:{{...OPT_STD(),scales:{{
      x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},
      y:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},
      y1:{{position:'right',ticks:{{color:CYAN}},grid:{{display:false}},min:82,max:90}}
    }}}}
  }});

  // TAB 5 — HISTÓRICO
  new Chart(document.getElementById('c_h_moa'),{{type:'bar',
    data:{{labels:HS_ANOS,datasets:[
      {{label:'Moagem (t)',data:HS_MOA,backgroundColor:HS_MOA.map(v=>v>2000000?GREEN:v>1500000?GOLD:GRAY),borderWidth:0}}
    ]}},options:OPT_STD('t')
  }});
  new Chart(document.getElementById('c_h_atr'),{{type:'line',
    data:{{labels:HS_ANOS,datasets:[
      {{label:'ATR (kg/t)',data:HS_ATR,borderColor:GOLD,backgroundColor:'rgba(255,214,0,0.06)',tension:0.4,fill:true,pointRadius:4,pointBackgroundColor:GOLD}}
    ]}},options:OPT_STD('kg/t')
  }});
  new Chart(document.getElementById('c_h_egi'),{{type:'line',
    data:{{labels:HS_ANOS,datasets:[
      {{label:'EGI%',data:HS_EGI,borderColor:CYAN,tension:0.4,pointRadius:3}}
    ]}},options:OPT_STD('%')
  }});
  new Chart(document.getElementById('c_h_tch'),{{type:'line',
    data:{{labels:SAF_ANOS,datasets:[
      {{label:'TCH (t/ha)',data:SAF_TCH,borderColor:GREEN,tension:0.4,fill:false,pointRadius:4}},
      {{label:'ATR (kg/t)',data:SAF_ATR,borderColor:GOLD,tension:0.4,fill:false,borderDash:[4,3],pointRadius:3}}
    ]}},options:OPT_STD()
  }});
  new Chart(document.getElementById('c_h_aprov'),{{type:'bar',
    data:{{labels:HS_ANOS,datasets:[
      {{label:'Aproveitamento%',data:HS_APROV,backgroundColor:HS_APROV.map(v=>v>=75?GREEN:v>=60?GOLD:RED),borderWidth:0}}
    ]}},options:OPT_STD('%')
  }});

}});
</script>
</body>
</html>"""
    return html

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("  UMOE OS 8.0 | ENTERPRISE BI ENGINE | Safra 2026/27")
    print("=" * 65)

    print("\n[1/5] Carregando Histórico Diário Safras (2009-2026)...")
    hist = ler_historico_diario()

    print("[2/5] Carregando BD SAFRAS granular (51K registros)...")
    bd = ler_bd_safras()

    print("[3/5] Carregando Boletim Industrial + TCH-BROCA...")
    boletim = ler_boletim()
    broca   = ler_tch_broca()

    print("[4/5] Carregando Base de Frota...")
    frota = ler_frota()
    print(f"  [Frota] {frota.get('total',0)} equipamentos | {len(frota.get('classes',{}))} classes")

    print("[5/5] Calculando análises e gerando HTML...")
    analises = calc_analises(hist, bd, boletim, broca)
    html     = gerar_html(hist, bd, boletim, broca, frota, analises)

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    # copia para Downloads também
    dl_path = os.path.join(os.path.expanduser("~"), "Downloads", "UMOE_BI_Enterprise.html")
    with open(dl_path, "w", encoding="utf-8") as f:
        f.write(html)

    sz = os.path.getsize(OUT_HTML) / 1024
    print(f"\n{'='*65}")
    print(f"  BI Enterprise gerado com sucesso!")
    print(f"  Arquivo: {OUT_HTML}")
    print(f"  Tamanho: {sz:.1f} KB")
    print(f"  Registros processados: {len(hist):,} diários + {sum(len(v) for v in bd.values() if isinstance(v,dict)):,} BD")
    print(f"  Kpis calculados: {len(analises)} blocos de análise")
    print(f"{'='*65}")
