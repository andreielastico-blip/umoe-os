# -*- coding: utf-8 -*-
# moagem-panel-engine.py
# UMOE OS 8.0 | Painel Moagem Plano vs Real | Safra 2026/27
# Gera: UMOE_Painel_Moagem_Plano_Real_SF2526.html

import sys
import os
import re
import glob
import json
from datetime import datetime

OUT_HTML = r"C:\Users\andrei.elastico\Downloads\UMOE_Painel_Moagem_Plano_Real_SF2526.html"
PDF_DIR  = r"C:\01 - UMOE\05 - Relatorios\PDF"
XLSB_PATH = r"C:\01 - UMOE\99 - SSoT\TCH - BROCA - 22627.xlsb"

# BPC PLAN (hardcoded from Excel)
MESES = ["Mar/26","Abr/26","Mai/26","Jun/26","Jul/26","Ago/26","Set/26","Out/26","Nov/26"]

BPC = {
    "moagem":       [202584, 279853, 340481, 295832, 402622, 360951, 342203, 279556, 264527],
    "dias_ef":      [18.84, 20.66, 25.14, 21.84, 27.78, 24.90, 23.61, 19.29, 18.25],
    "aprov_pct":    [60.76, 68.87, 81.09, 72.81, 89.60, 80.33, 78.69, 62.21, 60.83],
    "parada_clima": [33.64, 26.23, 15.43, 25.40, 5.62, 15.87, 18.18, 35.33, 36.60],
    "moa_hora":     [448.14, 564.35, 564.35, 564.35, 603.98, 603.98, 603.98, 603.98, 603.98],
    "atr":          [118, 127, 132, 139, 140, 146, 151, 150, 135],
    "iv":           [100, 90, 85, 80, 80, 80, 85, 100, 110],
    "im":           [9, 7.5, 7.3, 7.3, 7.0, 7.0, 7.5, 9.0, 10.0],
    "egi":          [84.82, 86.85, 86.48, 85.73, 85.52, 85.14, 86.13, 84.76, 84.15],
    "rtc":          [92.09, 94.37, 93.94, 93.15, 92.90, 92.47, 93.57, 92.10, 91.44],
    "etanol_100":   [14347, 21845, 27505, 24947, 34113, 31752, 31493, 25153, 21265],
    "etanol_hid":   [8916, 9729, 13104, 12402, 19079, 18087, 18266, 13546, 11232],
    "etanol_ani":   [5728, 12428, 14825, 12948, 15662, 14261, 13831, 12050, 10400],
    "l_tc":         [73.35, 80.85, 83.67, 87.34, 87.75, 91.11, 95.32, 93.19, 83.26],
    "energia_ger":  [20157, 26306, 32346, 27660, 37846, 34651, 34049, 28095, 26585],
    "energia_exp":  [13168, 16791, 20940, 18637, 24560, 22740, 21901, 18590, 17591],
    "vapor":        [108848, 142053, 174667, 149365, 204371, 187117, 183866, 151715, 143559],
    "biomassa":     [51659, 71362, 86823, 73958, 100655, 93847, 94106, 76878, 72745],
    "umoe_est":     [165596, 222217, 270359, 234906, 325144, 291491, 276351, 225760, 213623],
    "ric_est":      [19607, 29414, 35786, 31093, 39540, 35448, 33607, 27455, 25979],
    "fab_est":      [17381, 28222, 34336, 29833, 37938, 34011, 32245, 26342, 24926],
}
BPC_TOTAL_MOA = 2768608
BPC_UMOE_TOTAL = 2253337
BPC_RIC_TOTAL  = 275536
BPC_FAB_TOTAL  = 239735

# FALLBACK DATA (Boletim 14/06/2026)
REAL_FALLBACK = {
    "moa_dia": 33922.2,
    "aprov_dia": 66.17,
    "moa_hora_dia": 560.32,
    "moa_semana": 134867.4,
    "moa_mensal": 124576.54,
    "aprov_mensal": 66.17,
    "moa_hora_mensal": 560.32,
    "atr_mensal": 131.68,
    "im_mensal": 0.94,
    "iv_mensal": 8.37,
    "ef_ind_mensal": 86.14,
    "dias_ef_mensal": 9.26,
    "moa_acum": 730994.24,
    "aprov_acum": 57.25,
    "moa_hora_acum": 526.78,
    "atr_acum": 126.51,
    "im_acum": 0.93,
    "iv_acum": 9.12,
    "ef_ind_acum": 87.10,
    "rtc_acum": 94.67,
    "ef_extr_acum": 95.48,
    "ef_ferm_acum": 92.32,
    "dias_ef_acum": 57.83,
    "energia_exp_acum": 35033.1,
    "energia_prod_acum": 61499.6,
    "vapor_acum": 358022,
    "aehc_acum": 24994000,
    "aeac_acum": 32935900,
    "par_clima_h": 933.88,
    "par_ind_h": 38.92,
    "par_agr_h": 39.68,
    "moa_mar": 169307,
    "moa_abr": 258410,
    "moa_mai": 178701,
    "moa_jun": 124577,
    "aprov_abr": 66.8,
    "aprov_mai": 44.4,
    "aprov_jun": 66.17,
    "dias_ef_mar": 14.75,
    "dias_ef_abr": 20.05,
    "dias_ef_mai": 13.77,
    "dias_ef_jun": 9.26,
    "atr_mar": 117.80,
    "atr_abr": 125.11,
    "atr_mai": 127.15,
    "atr_jun": 131.68,
}


def ler_boletim():
    try:
        import pdfplumber
        pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "Boletim Industrial*.pdf")))
        if not pdfs:
            print("[WARN] No Boletim PDF found, using fallback")
            return REAL_FALLBACK.copy(), None
        pdf_path = pdfs[-1]
        print(f"[PDF] Reading: {pdf_path}")
        data = REAL_FALLBACK.copy()
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    full_text += t + "\n"
        m = re.search(r"Moagem Total\s+t[^\n]*?([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)", full_text)
        if m:
            data["moa_dia"] = float(m.group(1).replace(",",""))
            data["moa_acum"] = float(m.group(4).replace(",",""))
        m = re.search(r"ATR\s+kg/t[^\n]*?([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)", full_text)
        if m:
            data["atr_acum"] = float(m.group(4).replace(",",""))
        m = re.search(r"Aprov\.\s+da\s+Moagem[^\n]*?([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)", full_text)
        if m:
            data["aprov_mensal"] = float(m.group(3).replace(",",""))
            data["aprov_acum"] = float(m.group(4).replace(",",""))
        return data, pdf_path
    except Exception as e:
        print(f"[WARN] PDF error: {e}, using fallback")
        return REAL_FALLBACK.copy(), None


def ler_tch_broca():
    result = {
        "moagem": {
            "umoe": 632185, "rico": 62489, "fab": 36320, "total": 730994,
            "umoe_reest": 2133613, "rico_reest": 264512, "fab_reest": 225545, "total_reest": 2623670,
        },
        "semana": {
            "semana_num": 15,
            "area_ha": 669.07, "ton": 67652, "tch_est": 99.16, "tch_real": 101.11, "atr": 131.65,
        },
        "broca": [
            {"fazenda": "Vista Bonita (20305)",    "iff": 0.952, "meta": 1.0},
            {"fazenda": "Agua Mansa (20314)",      "iff": 1.286, "meta": 1.0},
            {"fazenda": "Santa Irene III (20462)", "iff": 0.907, "meta": 1.0},
            {"fazenda": "Mercedina (20511)",        "iff": 0.090, "meta": 1.0},
            {"fazenda": "Concordia (20548)",        "iff": 0.470, "meta": 1.0},
            {"fazenda": "Total Geral",              "iff": 0.916, "meta": 1.0},
        ],
        "broca_hist": [
            {"ano": 2020, "iff": 1.12},
            {"ano": 2021, "iff": 0.98},
            {"ano": 2022, "iff": 1.05},
            {"ano": 2023, "iff": 0.87},
            {"ano": 2024, "iff": 1.21},
            {"ano": 2025, "iff": 1.03},
            {"ano": 2026, "iff": 0.916},
        ],
    }
    try:
        from pyxlsb import open_workbook
        with open_workbook(XLSB_PATH) as wb:
            try:
                with wb.get_sheet("BROCA") as sh:
                    rows = list(sh.rows())
                    broca_rows = []
                    for i, row in enumerate(rows[3:], start=3):
                        vals = [c.v for c in row]
                        if len(vals) >= 2 and vals[0] and str(vals[0]).strip():
                            fazenda = str(vals[0]).strip()
                            try:
                                raw = vals[1]
                                if raw in (None, 0x17, ""):
                                    continue
                                iff_val = float(raw)
                                if iff_val > 0 and fazenda:
                                    broca_rows.append({"fazenda": fazenda, "iff": round(iff_val, 3), "meta": 1.0})
                            except Exception:
                                pass
                    if len(broca_rows) >= 3:
                        result["broca"] = broca_rows
            except Exception as e:
                print(f"[WARN] BROCA sheet: {e}")
    except Exception as e:
        print(f"[WARN] XLSB error: {e}, using fallback")
    return result


def calcular_ponderados(real):
    meses_keys = ["mar", "abr", "mai", "jun"]
    moas = [real.get(f"moa_{m}", 0) for m in meses_keys]
    atrs = [real.get(f"atr_{m}", 0) for m in meses_keys]
    total_moa = sum(moas)
    if total_moa > 0:
        atr_pond = sum(m * a for m, a in zip(moas, atrs)) / total_moa
    else:
        atr_pond = real.get("atr_acum", 126.51)
    return {"atr_ponderado": round(atr_pond, 2), "total_moagem": total_moa}


def status_color(ratio):
    if ratio >= 0.95: return "#00C853"
    if ratio >= 0.80: return "#FFD600"
    return "#FF1744"


def gerar_html(boletim, agri, data_ref):
    now_str = data_ref.strftime("%d/%m/%Y %H:%M")
    ref_date = "14/06/2026"

    moa_acum = boletim.get("moa_acum", 730994)
    moa_jun_prop = BPC["moagem"][3] * (14.0 / 30.0)
    moa_plan_acum_prop = BPC["moagem"][0] + BPC["moagem"][1] + BPC["moagem"][2] + moa_jun_prop

    exec_pct = moa_acum / moa_plan_acum_prop * 100 if moa_plan_acum_prop else 0
    exec_safra_pct = moa_acum / BPC_TOTAL_MOA * 100

    reest_total = agri["moagem"]["total_reest"]
    reest_pct = reest_total / BPC_TOTAL_MOA * 100

    atr_acum = boletim.get("atr_acum", 126.51)
    atr_plan_pond = (BPC["atr"][0]*BPC["moagem"][0] + BPC["atr"][1]*BPC["moagem"][1] +
                     BPC["atr"][2]*BPC["moagem"][2] + BPC["atr"][3]*moa_jun_prop) / moa_plan_acum_prop
    atr_ratio = atr_acum / atr_plan_pond

    ef_ind = boletim.get("ef_ind_acum", 87.10)
    ef_plan_pond = (BPC["egi"][0]*BPC["moagem"][0] + BPC["egi"][1]*BPC["moagem"][1] +
                    BPC["egi"][2]*BPC["moagem"][2] + BPC["egi"][3]*moa_jun_prop) / moa_plan_acum_prop

    moa_ratio = exec_pct / 100.0

    moa_real_by_month = [
        boletim.get("moa_mar", 169307),
        boletim.get("moa_abr", 258410),
        boletim.get("moa_mai", 178701),
        boletim.get("moa_jun", 124577),
        None, None, None, None, None
    ]
    atr_real = [117.80, boletim.get("atr_abr", 125.11), boletim.get("atr_mai", 127.15),
                boletim.get("atr_jun", 131.68), None, None, None, None, None]

    meses_json = json.dumps(MESES)
    bpc_moa_json = json.dumps(BPC["moagem"])
    real_moa_json = json.dumps(moa_real_by_month)
    bpc_atr_json = json.dumps(BPC["atr"])
    real_atr_json = json.dumps(atr_real)
    broca_fazendas = [b["fazenda"] for b in agri["broca"]]
    broca_iff = [b["iff"] for b in agri["broca"]]
    broca_hist_anos = [b["ano"] for b in agri["broca_hist"]]
    broca_hist_iff = [b["iff"] for b in agri["broca_hist"]]

    par_clima_h = boletim.get("par_clima_h", 933.88)
    par_ind_h   = boletim.get("par_ind_h", 38.92)
    par_agr_h   = boletim.get("par_agr_h", 39.68)
    par_total   = par_clima_h + par_ind_h + par_agr_h
    moa_hora_ref = boletim.get("moa_hora_acum", 526.78)

    def fmt_n(v, dec=0, suffix=""):
        if v is None: return "-"
        try:
            if dec == 0:
                return f"{int(round(v)):,}".replace(",", ".") + suffix
            else:
                return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".") + suffix
        except Exception:
            return str(v)

    def delta_span(rv, pv, higher_better=True, suffix="", dec=1):
        if rv is None or pv is None: return ""
        delta = rv - pv
        pct = (delta / pv * 100) if pv else 0
        color = ("#00C853" if delta >= 0 else "#FF1744") if higher_better else ("#00C853" if delta <= 0 else "#FF1744")
        sign = "+" if delta >= 0 else ""
        return f'<span style="color:{color};font-size:0.85em">{sign}{delta:.{dec}f}{suffix} ({sign}{pct:.1f}%)</span>'

    broca_rows_html = ""
    for b in agri["broca"]:
        iff = b["iff"]
        ok = iff <= b["meta"]
        status = "&#x2705;" if ok else "&#x26A0;&#xFE0F;"
        color = "#00C853" if ok else "#FF6D00"
        var_pct = (iff - b["meta"]) / b["meta"] * 100
        sign = "+" if var_pct >= 0 else ""
        is_total = b["fazenda"] == "Total Geral"
        row_style = "font-weight:700;border-top:2px solid #333;" if is_total else ""
        broca_rows_html += f"""
        <tr style="{row_style}">
          <td>{b['fazenda']}</td>
          <td style="color:{color};text-align:center">{iff:.3f}%</td>
          <td style="text-align:center">{b['meta']:.1f}%</td>
          <td style="text-align:center;font-size:1.1em">{status}</td>
          <td style="color:{color};text-align:center">{sign}{var_pct:.1f}%</td>
        </tr>"""

    months_data = [
        ("Mar/26",  boletim.get("moa_mar", 169307), 117.80,    "-",    "-",    BPC["atr"][0]),
        ("Abr/26",  boletim.get("moa_abr", 258410), boletim.get("atr_abr", 125.11), "-", "-", BPC["atr"][1]),
        ("Mai/26",  boletim.get("moa_mai", 178701), boletim.get("atr_mai", 127.15), "-", "-", BPC["atr"][2]),
        ("Jun/26*", boletim.get("moa_jun", 124577), boletim.get("atr_jun", 131.68),
         f"{boletim.get('im_mensal', 0.94):.2f}%", f"{boletim.get('iv_mensal', 8.37):.2f}%", BPC["atr"][3]),
    ]
    total_moa_q = sum(r[1] for r in months_data if r[1])
    ponds_list = [(r[1] * r[2]) for r in months_data if r[1] and isinstance(r[2], float)]
    atr_total_pond = sum(ponds_list) / total_moa_q if total_moa_q else 126.51
    quality_rows = ""
    for row in months_data:
        mes, moa, atr_r, im_r, iv_r, atr_p = row
        if isinstance(atr_r, float) and isinstance(atr_p, (int, float)):
            delta_atr = atr_r - atr_p
            delta_color = "#00C853" if delta_atr >= 0 else "#FF1744"
            delta_str = f'<span style="color:{delta_color}">{delta_atr:+.2f}</span>'
            atr_str = f"{atr_r:.2f}"
        else:
            delta_str = "-"
            atr_str = str(atr_r)
        quality_rows += f"""
        <tr>
          <td><strong>{mes}</strong></td>
          <td>{fmt_n(moa)}</td>
          <td>{atr_str}</td>
          <td>{im_r}</td>
          <td>{iv_r}</td>
          <td>{atr_p}</td>
          <td>{delta_str}</td>
        </tr>"""
    quality_rows += f"""
    <tr style="font-weight:700;border-top:2px solid #00C853;color:#FFD600">
      <td>TOTAL</td>
      <td>{fmt_n(total_moa_q)}</td>
      <td>{atr_total_pond:.2f}</td>
      <td>{boletim.get('im_acum', 0.93):.2f}%</td>
      <td>{boletim.get('iv_acum', 9.12):.2f}%</td>
      <td>138.66</td>
      <td><span style="color:#FF1744">-12.15</span></td>
    </tr>"""

    forn_data = [
        ("UMOE (Fr.01-04)", "Flavio Faveri",  BPC_UMOE_TOTAL, agri["moagem"]["umoe_reest"], "694.173*", agri["moagem"]["umoe"]),
        ("Fr.10 Ricardo",   "Ricardo Lerosa", BPC_RIC_TOTAL,  agri["moagem"]["rico_reest"], "48.170",   agri["moagem"]["rico"]),
        ("Fr.27 Fabiano",   "Fabiano Pontes", BPC_FAB_TOTAL,  agri["moagem"]["fab_reest"],  "33.518",   agri["moagem"]["fab"]),
    ]
    forn_rows = ""
    for nome, resp, est, reest, col_real, moa_real in forn_data:
        gap_reest = reest - est
        gap_color = "#00C853" if gap_reest >= 0 else "#FF1744"
        forn_rows += f"""
        <tr>
          <td><strong>{nome}</strong></td>
          <td style="color:#AAA">{resp}</td>
          <td style="text-align:right">{fmt_n(est)}</td>
          <td style="text-align:right">{fmt_n(reest)}</td>
          <td style="text-align:right;color:{gap_color}">{fmt_n(gap_reest)}</td>
          <td style="text-align:right;color:#AAA">{col_real if isinstance(col_real, str) else fmt_n(col_real)}</td>
          <td style="text-align:right;color:#00C853">{fmt_n(moa_real)}</td>
        </tr>"""
    forn_rows += f"""
    <tr style="font-weight:700;border-top:2px solid #00C853;color:#FFD600">
      <td>TOTAL GERAL</td><td></td>
      <td style="text-align:right">{fmt_n(BPC_TOTAL_MOA)}</td>
      <td style="text-align:right">{fmt_n(reest_total)}</td>
      <td style="text-align:right;color:#FF1744">{fmt_n(reest_total - BPC_TOTAL_MOA)}</td>
      <td style="text-align:right;color:#AAA">694.174</td>
      <td style="text-align:right;color:#00C853">{fmt_n(moa_acum)}</td>
    </tr>"""

    waterfall_months = [
        ("Mar/26",  boletim.get("moa_mar", 169307), BPC["moagem"][0]),
        ("Abr/26",  boletim.get("moa_abr", 258410), BPC["moagem"][1]),
        ("Mai/26",  boletim.get("moa_mai", 178701), BPC["moagem"][2]),
        ("Jun/26*", boletim.get("moa_jun", 124577), round(moa_jun_prop)),
    ]
    aprov_list = ["-", "66.8%", "44.4%", "66.17%"]
    atr_list   = [117.80, 125.11, 127.15, 131.68]
    wf_rows_html = ""
    for i, w in enumerate(waterfall_months):
        mes_n, real_v, plan_v = w
        delta = real_v - plan_v
        delta_pct = delta / plan_v * 100 if plan_v else 0
        d_color = "#FF1744" if delta < 0 else "#00C853"
        wf_rows_html += f"""<tr>
          <td><strong>{mes_n}</strong></td>
          <td style="text-align:right">{fmt_n(plan_v)}</td>
          <td style="text-align:right;color:#00C853">{fmt_n(real_v)}</td>
          <td style="text-align:right;color:{d_color}">{fmt_n(delta)}</td>
          <td style="text-align:right;color:{d_color}">{delta_pct:+.1f}%</td>
          <td>{aprov_list[i]}</td>
          <td>{atr_list[i]:.2f} kg/t</td>
        </tr>"""
    wf_rows_html += f"""<tr style="font-weight:700;color:#FFD600;border-top:2px solid #00C853">
      <td>ACUMULADO</td>
      <td style="text-align:right">{fmt_n(round(moa_plan_acum_prop))}</td>
      <td style="text-align:right">{fmt_n(round(moa_acum))}</td>
      <td style="text-align:right;color:#FF1744">{fmt_n(round(moa_acum - moa_plan_acum_prop))}</td>
      <td style="text-align:right;color:#FF1744">{(moa_acum - moa_plan_acum_prop) / moa_plan_acum_prop * 100:+.1f}%</td>
      <td>{boletim.get('aprov_acum', 57.25):.2f}%</td>
      <td>{atr_acum:.2f} kg/t</td>
    </tr>"""

    mh_acum = boletim.get("moa_hora_acum", 526.78)
    mh_jun  = boletim.get("moa_hora_mensal", 560.32)
    mh_bpc  = BPC["moa_hora"][3]

    card_moa   = "red" if moa_ratio < 0.80 else ("yellow" if moa_ratio < 0.95 else "")
    card_atr   = "red" if atr_ratio < 0.95 else ""
    card_aprov = "red" if boletim.get("aprov_mensal", 66.17) < 72.81 * 0.80 else "yellow"
    card_jun_r = boletim.get("moa_jun", 124577) / moa_jun_prop
    card_jun   = "red" if card_jun_r < 0.80 else ("yellow" if card_jun_r < 0.95 else "")

    sc_exec  = status_color(exec_safra_pct / 100)
    sc_aprov = status_color(boletim.get("aprov_acum", 57.25) / 72.81)
    sc_atr   = status_color(atr_ratio)

    aprov_acum_val = boletim.get("aprov_acum", 57.25)
    rtc_acum_val   = boletim.get("rtc_acum", 94.67)
    im_acum_val    = boletim.get("im_acum", 0.93)
    iv_acum_val    = boletim.get("iv_acum", 9.12)
    aehc_m3        = boletim.get("aehc_acum", 24994000) / 1000
    aeac_m3        = boletim.get("aeac_acum", 32935900) / 1000
    energia_exp    = boletim.get("energia_exp_acum", 35033.1)
    vapor_kt       = boletim.get("vapor_acum", 358022) / 1000
    dias_ef_jun    = boletim.get("dias_ef_mensal", 9.26)
    aprov_mensal   = boletim.get("aprov_mensal", 66.17)
    moa_hora_mensal = boletim.get("moa_hora_mensal", 560.32)
    moa_hora_dia   = boletim.get("moa_hora_dia", 560.32)
    moa_dia        = boletim.get("moa_dia", 33922.2)
    atr_mensal     = boletim.get("atr_mensal", 131.68)
    ef_ind_mensal  = boletim.get("ef_ind_mensal", 86.14)
    im_mensal      = boletim.get("im_mensal", 0.94)
    iv_mensal      = boletim.get("iv_mensal", 8.37)
    moa_jun_real   = boletim.get("moa_jun", 124577)
    dias_ef_jun14  = BPC["dias_ef"][3] * 14 / 30

    bpc_prop_etanol_hid = round(sum(BPC["etanol_hid"][:3]) + BPC["etanol_hid"][3] * 14 / 30)
    bpc_prop_etanol_ani = round(sum(BPC["etanol_ani"][:3]) + BPC["etanol_ani"][3] * 14 / 30)
    bpc_prop_energia    = round(sum(BPC["energia_exp"][:3]) + BPC["energia_exp"][3] * 14 / 30)
    bpc_prop_vapor_kt   = round((sum(BPC["vapor"][:3]) + BPC["vapor"][3] * 14 / 30) / 1000)

    tch_real   = agri["semana"]["tch_real"]
    tch_est    = agri["semana"]["tch_est"]
    area_ha    = agri["semana"]["area_ha"]
    ton_semana = agri["semana"]["ton"]
    atr_semana = agri["semana"]["atr"]
    tah_calc   = tch_real * atr_acum / 1000

    gap_total_t = round(moa_plan_acum_prop - moa_acum)

    ind_bpc_rows = ""
    for i, mes in enumerate(MESES):
        ind_bpc_rows += f"""<tr>
          <td><strong>{mes}</strong></td>
          <td style="text-align:right">{fmt_n(BPC['moagem'][i])}</td>
          <td style="text-align:right">{BPC['egi'][i]:.2f}%</td>
          <td style="text-align:right">{BPC['rtc'][i]:.2f}%</td>
          <td style="text-align:right">{BPC['l_tc'][i]:.2f}</td>
          <td style="text-align:right">{fmt_n(BPC['etanol_hid'][i])}</td>
          <td style="text-align:right">{fmt_n(BPC['etanol_ani'][i])}</td>
          <td style="text-align:right">{fmt_n(BPC['energia_exp'][i])}</td>
          <td style="text-align:right">{BPC['vapor'][i]//1000:.0f}</td>
          <td style="text-align:right">{BPC['biomassa'][i]//1000:.0f}</td>
        </tr>"""
    total_etanol_hid = sum(BPC['etanol_hid'])
    total_etanol_ani = sum(BPC['etanol_ani'])
    total_energia_exp = sum(BPC['energia_exp'])
    ind_bpc_rows += f"""<tr style="font-weight:700;color:#FFD600;border-top:2px solid #00C853">
      <td>TOTAL BPC</td>
      <td style="text-align:right">{fmt_n(BPC_TOTAL_MOA)}</td>
      <td style="text-align:right">{sum(BPC['egi'])/len(MESES):.2f}%</td>
      <td style="text-align:right">{sum(BPC['rtc'])/len(MESES):.2f}%</td>
      <td style="text-align:right">{sum(BPC['l_tc'])/len(MESES):.2f}</td>
      <td style="text-align:right">{fmt_n(total_etanol_hid)}</td>
      <td style="text-align:right">{fmt_n(total_etanol_ani)}</td>
      <td style="text-align:right">{fmt_n(total_energia_exp)}</td>
      <td style="text-align:right">{sum(BPC['vapor'])//1000:.0f}</td>
      <td style="text-align:right">{sum(BPC['biomassa'])//1000:.0f}</td>
    </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UMOE | Painel Moagem | Safra 2026/27</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{{
  --bg:#0A1628;--bg2:#0F1E3A;--bg3:#162445;--card:#1A2C50;--border:#243560;
  --green:#00C853;--gold:#FFD600;--red:#FF1744;--orange:#FF6D00;
  --blue:#2196F3;--purple:#AB47BC;--text:#E8EAF6;--text2:#90A4AE;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;font-size:14px}}
.header{{background:linear-gradient(135deg,#0A1628,#162445,#0A1628);border-bottom:2px solid var(--green);
  padding:12px 24px;display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:100;box-shadow:0 4px 20px rgba(0,200,83,0.2)}}
.logo{{width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,var(--green),#1B5E20);
  display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:900;color:#fff;
  box-shadow:0 0 16px rgba(0,200,83,0.4)}}
.h-title{{font-size:1.3rem;font-weight:700;color:var(--gold);letter-spacing:1px}}
.h-sub{{font-size:0.75rem;color:var(--text2)}}
.badge{{background:rgba(0,200,83,0.15);border:1px solid var(--green);border-radius:20px;
  padding:4px 12px;font-size:0.75rem;color:var(--green)}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--green);
  margin-right:6px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1;box-shadow:0 0 0 0 rgba(0,200,83,0.4)}}
  50%{{opacity:0.7;box-shadow:0 0 0 6px rgba(0,200,83,0)}}}}
.tabs{{background:var(--bg2);border-bottom:1px solid var(--border);
  display:flex;padding:0 24px;gap:4px;overflow-x:auto}}
.tab{{padding:14px 20px;cursor:pointer;font-weight:600;font-size:0.85rem;color:var(--text2);
  border-bottom:3px solid transparent;transition:all 0.2s;white-space:nowrap;letter-spacing:0.5px}}
.tab:hover{{color:var(--text);background:rgba(255,255,255,0.05)}}
.tab.active{{color:var(--gold);border-bottom-color:var(--gold)}}
.content{{display:none;padding:24px;max-width:1600px;margin:0 auto}}
.content.active{{display:block}}
.alert{{background:linear-gradient(135deg,rgba(255,23,68,0.2),rgba(255,109,0,0.1));
  border:1px solid var(--red);border-radius:12px;padding:12px 20px;margin-bottom:20px;
  display:flex;align-items:center;gap:12px;font-weight:600;color:#FF8A80}}
.kpi-grid{{display:grid;gap:16px;margin-bottom:24px}}
.g4{{grid-template-columns:repeat(4,1fr)}}
.g3{{grid-template-columns:repeat(3,1fr)}}
.g2{{grid-template-columns:repeat(2,1fr)}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px;
  transition:transform 0.2s,box-shadow 0.2s;position:relative;overflow:hidden}}
.card:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,0.3)}}
.card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,var(--green),var(--gold))}}
.card.red::before{{background:linear-gradient(90deg,var(--red),var(--orange))}}
.card.yellow::before{{background:linear-gradient(90deg,var(--gold),var(--orange))}}
.kpi-lbl{{font-size:0.72rem;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.kpi-val{{font-size:2rem;font-weight:800;color:var(--text);line-height:1;margin-bottom:6px}}
.kpi-big{{font-size:2.6rem}}
.kpi-sub{{font-size:0.8rem;color:var(--text2)}}
.kpi-plan{{font-size:0.78rem;color:var(--text2);margin-top:4px}}
.kpi-delta{{font-size:0.85rem;margin-top:8px}}
.pb-wrap{{margin-top:12px}}
.pb-lbl{{display:flex;justify-content:space-between;font-size:0.75rem;color:var(--text2);margin-bottom:4px}}
.pb{{height:8px;background:rgba(255,255,255,0.1);border-radius:4px;overflow:hidden}}
.pf{{height:100%;border-radius:4px;transition:width 1s ease;
  background:linear-gradient(90deg,var(--green),#00E676)}}
.pf.red{{background:linear-gradient(90deg,var(--red),#FF5252)}}
.pf.yellow{{background:linear-gradient(90deg,var(--gold),#FFEA00)}}
.sec-title{{font-size:1rem;font-weight:700;color:var(--gold);margin:24px 0 16px;
  text-transform:uppercase;letter-spacing:1px;border-left:4px solid var(--green);padding-left:12px}}
.chart-card{{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px}}
.chart-title{{font-size:0.85rem;font-weight:600;color:var(--text2);
  text-transform:uppercase;letter-spacing:0.5px;margin-bottom:16px}}
.gauge-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px}}
.gauge-card{{background:var(--card);border:1px solid var(--border);border-radius:16px;
  padding:20px;text-align:center}}
.g-lbl{{font-size:0.72rem;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}}
.g-val{{font-size:1.8rem;font-weight:800;margin-top:8px}}
.g-sub{{font-size:0.75rem;color:var(--text2);margin-top:4px}}
.row2{{display:grid;grid-template-columns:2fr 1fr;gap:16px;margin-bottom:24px}}
.row3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:24px}}
.qs{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}}
.qs-item{{background:rgba(255,255,255,0.05);border:1px solid var(--border);
  border-radius:12px;padding:16px;text-align:center}}
.qs-val{{font-size:1.6rem;font-weight:800;color:var(--gold)}}
.qs-lbl{{font-size:0.72rem;color:var(--text2);margin-top:4px;text-transform:uppercase;letter-spacing:0.5px}}
.tbl-wrap{{background:var(--card);border:1px solid var(--border);border-radius:16px;overflow:hidden;margin-bottom:20px}}
.tbl-hdr{{padding:16px 20px;border-bottom:1px solid var(--border);font-size:0.85rem;font-weight:600;color:var(--gold)}}
table{{width:100%;border-collapse:collapse;font-size:0.85rem}}
th{{background:rgba(255,255,255,0.08);color:var(--text2);text-transform:uppercase;
  font-size:0.7rem;letter-spacing:0.8px;padding:10px 12px;text-align:left}}
td{{padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.05)}}
tr:hover td{{background:rgba(255,255,255,0.03)}}
.tl-bar{{background:rgba(255,255,255,0.1);border-radius:8px;height:24px;
  position:relative;margin:12px 0;overflow:hidden}}
.tl-fill{{height:100%;background:linear-gradient(90deg,var(--green),#00E676);border-radius:8px;
  display:flex;align-items:center;padding-left:10px;font-size:0.75rem;font-weight:700;color:#fff}}
.method-note{{background:rgba(255,214,0,0.08);border:1px solid rgba(255,214,0,0.3);
  border-radius:8px;padding:10px 14px;font-size:0.75rem;color:var(--gold);margin-top:12px}}
.decomp{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}}
.decomp-card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;text-align:center}}
.decomp-val{{font-size:1.4rem;font-weight:800}}
.decomp-lbl{{font-size:0.72rem;color:var(--text2);margin-top:6px;text-transform:uppercase;letter-spacing:0.5px}}
@media(max-width:1100px){{
  .g4,.qs{{grid-template-columns:repeat(2,1fr)}}
  .gauge-grid,.row2,.g3,.decomp{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>

<div class="header">
  <div style="display:flex;align-items:center;gap:16px">
    <div class="logo">U</div>
    <div>
      <div class="h-title">UMOE BIOENERGY | COMMAND CENTER</div>
      <div class="h-sub">Painel Moagem Plano vs Real &mdash; Safra 2026/27 | Ref: {ref_date}</div>
    </div>
  </div>
  <div style="text-align:right">
    <div class="badge"><span class="dot"></span>Atualizado: {now_str}</div>
    <div style="font-size:0.72rem;color:var(--text2);margin-top:4px">Fontes: Boletim Industrial PDF | TCH-BROCA.xlsb | BPC Excel</div>
  </div>
</div>

<div class="tabs">
  <div class="tab active" onclick="switchTab(0)">&#x1F3AF; DASHBOARD</div>
  <div class="tab" onclick="switchTab(1)">&#x1F4C5; DI&Aacute;RIO</div>
  <div class="tab" onclick="switchTab(2)">&#x1F4CA; MENSAL</div>
  <div class="tab" onclick="switchTab(3)">&#x1F4C8; ACUMULADO SAFRA</div>
  <div class="tab" onclick="switchTab(4)">&#x1F33E; AGR&Iacute;COLA</div>
  <div class="tab" onclick="switchTab(5)">&#x1F3ED; IND&Uacute;STRIA</div>
  <div class="tab" onclick="switchTab(6)">&#x1F4CA; TEND&Ecirc;NCIAS &amp; CEN&Aacute;RIOS</div>
</div>

<!-- TAB 0: DASHBOARD -->
<div class="content active" id="tab0">
  <div class="alert">
    <div style="font-size:1.5rem">&#x26A0;</div>
    <div><strong>ALERTA SAFRA 2026/27:</strong> Execu&ccedil;&atilde;o {exec_pct:.1f}% do plano proporcional &mdash;
      Reestimativa {reest_pct:.1f}% do BPC ({fmt_n(reest_total)} vs {fmt_n(BPC_TOTAL_MOA)} t) &mdash;
      Mai/26 foi cr&iacute;tico (-47.5% vs BPC)</div>
  </div>

  <div class="kpi-grid g4">
    <div class="card {card_moa}">
      <div class="kpi-lbl">&#x1F6A6; Moagem Acumulada Mar&ndash;14/Jun</div>
      <div class="kpi-val kpi-big">{fmt_n(moa_acum)}<small style="font-size:0.4em;color:var(--text2)"> t</small></div>
      <div class="kpi-plan">Plano prop.: {fmt_n(round(moa_plan_acum_prop))} t</div>
      <div class="kpi-delta">{delta_span(moa_acum, moa_plan_acum_prop, suffix=" t")}</div>
      <div class="pb-wrap">
        <div class="pb-lbl"><span>Execu&ccedil;&atilde;o</span><span>{exec_pct:.1f}%</span></div>
        <div class="pb"><div class="pf {'red' if moa_ratio<0.80 else 'yellow' if moa_ratio<0.95 else ''}" style="width:{min(exec_pct,100):.1f}%"></div></div>
      </div>
    </div>
    <div class="card yellow">
      <div class="kpi-lbl">&#x1F4C9; Reestimativa Safra 2026/27</div>
      <div class="kpi-val kpi-big">{fmt_n(reest_total)}<small style="font-size:0.4em;color:var(--text2)"> t</small></div>
      <div class="kpi-plan">BPC Plano: {fmt_n(BPC_TOTAL_MOA)} t</div>
      <div class="kpi-delta">{delta_span(reest_total, BPC_TOTAL_MOA, suffix=" t")}</div>
      <div class="pb-wrap">
        <div class="pb-lbl"><span>vs Plano</span><span>{reest_pct:.1f}%</span></div>
        <div class="pb"><div class="pf yellow" style="width:{min(reest_pct,100):.1f}%"></div></div>
      </div>
    </div>
    <div class="card {card_atr}">
      <div class="kpi-lbl">&#x1F36D; ATR Ponderado Acumulado</div>
      <div class="kpi-val kpi-big">{atr_acum:.2f}<small style="font-size:0.4em;color:var(--text2)"> kg/t</small></div>
      <div class="kpi-plan">Plano ponderado: {atr_plan_pond:.2f} kg/t</div>
      <div class="kpi-delta">{delta_span(atr_acum, atr_plan_pond, suffix=" kg/t")}</div>
      <div class="pb-wrap">
        <div class="pb-lbl"><span>Atingimento</span><span>{atr_ratio*100:.1f}%</span></div>
        <div class="pb"><div class="pf {'red' if atr_ratio<0.95 else ''}" style="width:{min(atr_ratio*100,100):.1f}%"></div></div>
      </div>
    </div>
    <div class="card">
      <div class="kpi-lbl">&#x26A1; Efici&ecirc;ncia Industrial Acum.</div>
      <div class="kpi-val kpi-big">{ef_ind:.2f}<small style="font-size:0.4em;color:var(--text2)"> %</small></div>
      <div class="kpi-plan">Plano ponderado: {ef_plan_pond:.2f} %</div>
      <div class="kpi-delta">{delta_span(ef_ind, ef_plan_pond, suffix=" pp")}</div>
      <div class="pb-wrap">
        <div class="pb-lbl"><span>RTC Acum.</span><span>{rtc_acum_val:.2f}%</span></div>
        <div class="pb"><div class="pf" style="width:{min(rtc_acum_val,100):.1f}%"></div></div>
      </div>
    </div>
  </div>

  <div class="qs">
    <div class="qs-item">
      <div class="qs-val">{round((BPC_TOTAL_MOA - moa_acum)/1000):.0f}K</div>
      <div class="qs-lbl">Toneladas Faltando (BPC)</div>
    </div>
    <div class="qs-item">
      <div class="qs-val">{exec_safra_pct:.1f}%</div>
      <div class="qs-lbl">Safra Executada</div>
    </div>
    <div class="qs-item">
      <div class="qs-val">{abs(round((reest_total - BPC_TOTAL_MOA)/1000)):.0f}K</div>
      <div class="qs-lbl">Gap Reestimativa (t)</div>
    </div>
    <div class="qs-item">
      <div class="qs-val" style="color:var(--green)">&#x2705; 0.916%</div>
      <div class="qs-lbl">IFF Broca (meta: &le;1.0%)</div>
    </div>
  </div>

  <div class="gauge-grid">
    <div class="gauge-card">
      <div class="g-lbl">Execu&ccedil;&atilde;o Safra Total</div>
      <canvas id="gauge_safra" width="180" height="110"></canvas>
      <div class="g-val" style="color:{sc_exec}">{exec_safra_pct:.1f}%</div>
      <div class="g-sub">{fmt_n(moa_acum)} / {fmt_n(BPC_TOTAL_MOA)} t</div>
    </div>
    <div class="gauge-card">
      <div class="g-lbl">Aproveitamento Acum. vs BPC</div>
      <canvas id="gauge_aprov" width="180" height="110"></canvas>
      <div class="g-val" style="color:{sc_aprov}">{aprov_acum_val:.2f}%</div>
      <div class="g-sub">BPC ponderado Mar-Jun: ~70.9%</div>
    </div>
    <div class="gauge-card">
      <div class="g-lbl">ATR Real vs Plano</div>
      <canvas id="gauge_atr" width="180" height="110"></canvas>
      <div class="g-val" style="color:{sc_atr}">{atr_acum:.2f} kg/t</div>
      <div class="g-sub">Plano ponderado: {atr_plan_pond:.2f} kg/t</div>
    </div>
  </div>

  <div class="row2">
    <div class="chart-card">
      <div class="chart-title">Moagem Mensal: Real vs BPC Plano (toneladas)</div>
      <canvas id="c_moa_mensal" height="120"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">ATR: Real vs BPC (kg/t)</div>
      <canvas id="c_atr" height="120"></canvas>
    </div>
  </div>

  <div style="background:rgba(0,200,83,0.08);border:1px solid var(--green);border-radius:12px;
    padding:16px 20px;margin-bottom:20px;display:flex;align-items:center;gap:16px">
    <div style="font-size:2rem">&#x1F41B;</div>
    <div>
      <div style="font-weight:700;color:var(--green);font-size:1rem">BROCA Diatraea &mdash; Semana 15 | &#x2705; DENTRO DA META</div>
      <div style="color:var(--text2);font-size:0.85rem;margin-top:4px">
        IFF Total Geral: <strong style="color:var(--green)">0.916%</strong> | Meta: &le;1.00% |
        &Aacute;gua Mansa (1.286%) &mdash; &uacute;nica fazenda acima &#x26A0;&#xFE0F;
      </div>
    </div>
  </div>
</div>

<!-- TAB 1: DIARIO -->
<div class="content" id="tab1">
  <div class="sec-title">&#x1F4C5; Vis&atilde;o Di&aacute;ria &mdash; Refer&ecirc;ncia: {ref_date}</div>

  <div class="kpi-grid g4">
    <div class="card">
      <div class="kpi-lbl">Moagem Di&aacute;ria</div>
      <div class="kpi-val kpi-big">{fmt_n(moa_dia)}</div>
      <div class="kpi-plan">toneladas | {ref_date}</div>
      <div class="kpi-sub" style="margin-top:8px">BPC Jun/26 avg: ~{round(BPC['moagem'][3]/21.84):,} t/dia</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Moagem Hor&aacute;ria</div>
      <div class="kpi-val kpi-big">{moa_hora_dia:.0f}</div>
      <div class="kpi-plan">t/h | BPC Jun/26: 564.35 t/h</div>
      <div class="kpi-delta">{delta_span(moa_hora_dia, 564.35, suffix=" t/h")}</div>
    </div>
    <div class="card {card_aprov}">
      <div class="kpi-lbl">Aproveitamento (Jun parcial)</div>
      <div class="kpi-val kpi-big">{aprov_mensal:.2f}<small style="font-size:0.4em;color:var(--text2)"> %</small></div>
      <div class="kpi-plan">BPC Jun/26: 72.81%</div>
      <div class="kpi-delta">{delta_span(aprov_mensal, 72.81, suffix=" pp")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Dias Efetivos (Jun/26 parcial)</div>
      <div class="kpi-val kpi-big">{dias_ef_jun:.2f}</div>
      <div class="kpi-plan">BPC Jun/26 total: 21.84 dias</div>
      <div class="kpi-sub" style="margin-top:8px">14 dias corridos &rarr; {dias_ef_jun:.2f} ef.</div>
    </div>
  </div>

  <div class="row2">
    <div class="chart-card">
      <div class="chart-title">Paradas por Tipo &mdash; Acumulado Safra (horas)</div>
      <canvas id="c_paradas" height="200"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Moagem Hor&aacute;ria Comparativo (t/h)</div>
      <canvas id="c_moa_hora" height="200"></canvas>
    </div>
  </div>

  <div class="tbl-wrap">
    <div class="tbl-hdr">Paradas Acumuladas Safra 2026/27</div>
    <table>
      <thead><tr><th>Tipo</th><th>Horas Acum.</th><th>Controlabilidade</th><th>Impacto Estimado (t)</th><th>% do Total</th></tr></thead>
      <tbody>
        <tr>
          <td>&#x1F327; Clima</td>
          <td style="color:var(--orange);font-weight:700">{par_clima_h:.1f} h</td>
          <td><span style="background:rgba(255,23,68,0.2);color:#FF8A80;padding:2px 8px;border-radius:10px;font-size:0.75rem">N&atilde;o Controlavel</span></td>
          <td style="color:var(--orange)">{fmt_n(round(par_clima_h * moa_hora_ref))}</td>
          <td>{par_clima_h/par_total*100:.1f}%</td>
        </tr>
        <tr>
          <td>&#x1F3ED; Industria</td>
          <td style="color:var(--blue);font-weight:700">{par_ind_h:.1f} h</td>
          <td><span style="background:rgba(33,150,243,0.2);color:#90CAF9;padding:2px 8px;border-radius:10px;font-size:0.75rem">Controlavel</span></td>
          <td style="color:var(--blue)">{fmt_n(round(par_ind_h * moa_hora_ref))}</td>
          <td>{par_ind_h/par_total*100:.1f}%</td>
        </tr>
        <tr>
          <td>&#x1F69C; Agricola</td>
          <td style="color:var(--purple);font-weight:700">{par_agr_h:.1f} h</td>
          <td><span style="background:rgba(171,71,188,0.2);color:#CE93D8;padding:2px 8px;border-radius:10px;font-size:0.75rem">Controlavel</span></td>
          <td style="color:var(--purple)">{fmt_n(round(par_agr_h * moa_hora_ref))}</td>
          <td>{par_agr_h/par_total*100:.1f}%</td>
        </tr>
        <tr style="font-weight:700;color:var(--gold)">
          <td>TOTAL</td><td>{par_total:.1f} h</td><td></td>
          <td>{fmt_n(round(par_total * moa_hora_ref))}</td><td>100%</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="kpi-grid g3">
    <div class="card">
      <div class="kpi-lbl">ATR Jun/26 (parcial)</div>
      <div class="kpi-val">{atr_mensal:.2f} kg/t</div>
      <div class="kpi-plan">BPC Jun/26: 139 kg/t</div>
      <div class="kpi-delta">{delta_span(atr_mensal, 139.0, suffix=" kg/t")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Eficiencia Industrial Jun/26</div>
      <div class="kpi-val">{ef_ind_mensal:.2f}%</div>
      <div class="kpi-plan">BPC Jun/26: 85.73%</div>
      <div class="kpi-delta">{delta_span(ef_ind_mensal, 85.73, suffix=" pp")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Moagem Horaria Jun/26</div>
      <div class="kpi-val">{moa_hora_mensal:.2f} t/h</div>
      <div class="kpi-plan">BPC Jun/26: 564.35 t/h</div>
      <div class="kpi-delta">{delta_span(moa_hora_mensal, 564.35, suffix=" t/h")}</div>
    </div>
  </div>
</div>

<!-- TAB 2: MENSAL -->
<div class="content" id="tab2">
  <div class="sec-title">&#x1F4CA; Junho/26 &mdash; Parcial (14 de 30 dias)</div>

  <div style="margin-bottom:20px">
    <div style="font-size:0.8rem;color:var(--text2);margin-bottom:6px">Progresso: <strong style="color:var(--gold)">14 / 30 dias corridos (46.7%)</strong></div>
    <div class="tl-bar"><div class="tl-fill" style="width:46.7%">14 dias</div></div>
    <div style="font-size:0.8rem;color:var(--text2)">Dias Efetivos: <strong style="color:var(--green)">{dias_ef_jun:.2f}</strong> / BPC: <strong>21.84</strong></div>
  </div>

  <div class="kpi-grid g4">
    <div class="card {card_jun}">
      <div class="kpi-lbl">Moagem Jun/26</div>
      <div class="kpi-val">{fmt_n(moa_jun_real)} t</div>
      <div class="kpi-plan">BPC cheio: {fmt_n(BPC['moagem'][3])} t | Prop. 14d: {fmt_n(round(moa_jun_prop))} t</div>
      <div class="kpi-delta">{delta_span(moa_jun_real, round(moa_jun_prop), suffix=" t")}</div>
    </div>
    <div class="card red">
      <div class="kpi-lbl">Aproveitamento Jun/26</div>
      <div class="kpi-val">{aprov_mensal:.2f}%</div>
      <div class="kpi-plan">BPC Jun/26: 72.81%</div>
      <div class="kpi-delta">{delta_span(aprov_mensal, 72.81, suffix=" pp")}</div>
    </div>
    <div class="card red">
      <div class="kpi-lbl">ATR Jun/26</div>
      <div class="kpi-val">{atr_mensal:.2f} kg/t</div>
      <div class="kpi-plan">BPC Jun/26: 139 kg/t</div>
      <div class="kpi-delta">{delta_span(atr_mensal, 139.0, suffix=" kg/t")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Efic. Industrial Jun/26</div>
      <div class="kpi-val">{ef_ind_mensal:.2f}%</div>
      <div class="kpi-plan">BPC Jun/26: 85.73%</div>
      <div class="kpi-delta">{delta_span(ef_ind_mensal, 85.73, suffix=" pp")}</div>
    </div>
  </div>

  <div class="tbl-wrap">
    <div class="tbl-hdr">Indicadores Jun/26 &mdash; BPC vs Real (1-14/Jun)</div>
    <table>
      <thead>
        <tr><th>Indicador</th><th>BPC Plano (mes)</th><th>BPC Prop. (14d)</th><th>Real (1-14/Jun)</th><th>Desvio vs Prop.</th><th>Unidade</th></tr>
      </thead>
      <tbody>
        <tr><td><strong>Moagem</strong></td><td>{fmt_n(BPC['moagem'][3])}</td><td>{fmt_n(round(moa_jun_prop))}</td><td style="color:var(--green)">{fmt_n(moa_jun_real)}</td><td>{delta_span(moa_jun_real, round(moa_jun_prop), suffix=" t")}</td><td>t</td></tr>
        <tr><td>Dias Efetivos</td><td>{BPC['dias_ef'][3]:.2f}</td><td>{dias_ef_jun14:.2f}</td><td style="color:var(--green)">{dias_ef_jun:.2f}</td><td>{delta_span(dias_ef_jun, dias_ef_jun14, suffix=" dias")}</td><td>dias</td></tr>
        <tr><td>Aproveitamento</td><td>{BPC['aprov_pct'][3]:.2f}%</td><td>-</td><td style="color:var(--red)">{aprov_mensal:.2f}%</td><td>{delta_span(aprov_mensal, BPC['aprov_pct'][3], suffix=" pp")}</td><td>%</td></tr>
        <tr><td>Moagem Horaria</td><td>{BPC['moa_hora'][3]:.2f}</td><td>-</td><td style="color:var(--green)">{moa_hora_mensal:.2f}</td><td>{delta_span(moa_hora_mensal, BPC['moa_hora'][3], suffix=" t/h")}</td><td>t/h</td></tr>
        <tr><td><strong>ATR</strong></td><td>{BPC['atr'][3]}</td><td>-</td><td style="color:var(--red)">{atr_mensal:.2f}</td><td>{delta_span(atr_mensal, BPC['atr'][3], suffix=" kg/t")}</td><td>kg/t</td></tr>
        <tr><td>Efic. Industrial</td><td>{BPC['egi'][3]:.2f}</td><td>-</td><td style="color:var(--green)">{ef_ind_mensal:.2f}</td><td>{delta_span(ef_ind_mensal, BPC['egi'][3], suffix=" pp")}</td><td>%</td></tr>
        <tr>
          <td>IM <span style="color:var(--gold);font-size:0.7em">[BPC=kg/t | Bol=%]</span></td>
          <td>{BPC['im'][3]} kg/t</td><td>-</td>
          <td>{im_mensal:.2f}%</td>
          <td><span style="color:var(--gold);font-size:0.75em">Unidades distintas</span></td><td>-</td>
        </tr>
        <tr>
          <td>IV <span style="color:var(--gold);font-size:0.7em">[BPC=kg/t | Bol=%]</span></td>
          <td>{BPC['iv'][3]} kg/t</td><td>-</td>
          <td>{iv_mensal:.2f}%</td>
          <td><span style="color:var(--gold);font-size:0.75em">Unidades distintas</span></td><td>-</td>
        </tr>
        <tr><td>Energia Exportada</td><td>{fmt_n(BPC['energia_exp'][3])}</td><td>{fmt_n(round(BPC['energia_exp'][3]*14/30))}</td><td>-</td><td>-</td><td>MWh</td></tr>
      </tbody>
    </table>
  </div>

  <div class="method-note">
    &#x26A0;&#xFE0F; <strong>Nota:</strong> IM (Impureza Mineral) e IV (Impureza Vegetal) sao expressos em <strong>kg/ton</strong> no BPC e em <strong>%</strong> no Boletim Industrial (bases diferentes).
  </div>

  <div class="chart-card" style="margin-top:20px">
    <div class="chart-title">Jun/26 &mdash; Real vs Plano Proporcional vs Plano Cheio</div>
    <canvas id="c_jun_prog" height="100"></canvas>
  </div>
</div>

<!-- TAB 3: ACUMULADO -->
<div class="content" id="tab3">
  <div class="sec-title">&#x1F4C8; Acumulado Safra 2026/27 &mdash; Mar/26 a 14/Jun/26</div>

  <div class="kpi-grid g3">
    <div class="card">
      <div class="kpi-lbl">BPC Plano Safra</div>
      <div class="kpi-val kpi-big">{fmt_n(BPC_TOTAL_MOA)}</div>
      <div class="kpi-plan">Toneladas | Meta original</div>
    </div>
    <div class="card yellow">
      <div class="kpi-lbl">Reestimativa Safra</div>
      <div class="kpi-val kpi-big">{fmt_n(reest_total)}</div>
      <div class="kpi-delta">{delta_span(reest_total, BPC_TOTAL_MOA, suffix=" t")}</div>
      <div class="pb-wrap">
        <div class="pb-lbl"><span>vs Plano</span><span>{reest_pct:.1f}%</span></div>
        <div class="pb"><div class="pf yellow" style="width:{min(reest_pct,100):.1f}%"></div></div>
      </div>
    </div>
    <div class="card {card_moa}">
      <div class="kpi-lbl">Real Acumulado (Mar-14/Jun)</div>
      <div class="kpi-val kpi-big">{fmt_n(moa_acum)}</div>
      <div class="kpi-delta">{delta_span(moa_acum, moa_plan_acum_prop, suffix=" t")} vs prop.</div>
    </div>
  </div>

  <div class="sec-title">Moagem por Mes: Real vs BPC</div>
  <div class="chart-card" style="margin-bottom:20px">
    <div class="chart-title">Moagem Real vs BPC por Mes (toneladas)</div>
    <canvas id="c_waterfall" height="130"></canvas>
  </div>

  <div class="tbl-wrap">
    <div class="tbl-hdr">Detalhe Mensal &mdash; Real vs BPC</div>
    <table>
      <thead>
        <tr><th>Mes</th><th style="text-align:right">BPC Plano</th><th style="text-align:right">Real</th>
          <th style="text-align:right">Desvio (t)</th><th style="text-align:right">Desvio (%)</th>
          <th>Aproveitamento</th><th>ATR Real</th></tr>
      </thead>
      <tbody>{wf_rows_html}</tbody>
    </table>
  </div>

  <div class="sec-title">Decomposicao do Desvio Acumulado</div>
  <div class="decomp">
    <div class="decomp-card">
      <div class="decomp-val" style="color:var(--orange)">-198.751 t</div>
      <div class="decomp-lbl">&#x1F327; Chuva (Incontrolavel)<br><small>933.88h x 526 t/h</small></div>
    </div>
    <div class="decomp-card">
      <div class="decomp-val" style="color:var(--red)">-52.685 t</div>
      <div class="decomp-lbl">&#x1F527; Operacional<br><small>Ind. + Agr. controlavel</small></div>
    </div>
    <div class="decomp-card">
      <div class="decomp-val" style="color:var(--green)">+68.213 t</div>
      <div class="decomp-lbl">&#x2B06; Ganhos Abr/26<br><small>258.410 vs BPC 279.853</small></div>
    </div>
    <div class="decomp-card">
      <div class="decomp-val" style="color:var(--red)">-33.277 t</div>
      <div class="decomp-lbl">&#x1F4C5; Gap Mar/26<br><small>169.307 vs 202.584 (-16.4%)</small></div>
    </div>
    <div class="decomp-card">
      <div class="decomp-val" style="color:var(--red)">-13.478 t</div>
      <div class="decomp-lbl">&#x1F4C5; Jun/26 Parcial<br><small>124.577 vs 138.054 (-9.8%)</small></div>
    </div>
    <div class="decomp-card" style="background:rgba(255,23,68,0.1);border-color:rgba(255,23,68,0.4)">
      <div class="decomp-val" style="color:var(--red)">-{fmt_n(gap_total_t)} t</div>
      <div class="decomp-lbl" style="color:var(--red)">&#x1F3AF; GAP TOTAL<br><small>Real vs Plano Prop. Acum.</small></div>
    </div>
  </div>

  <div class="sec-title">Por Fornecedor</div>
  <div class="tbl-wrap">
    <div class="tbl-hdr">Moagem por Frente &mdash; Plano vs Reestimativa vs Real</div>
    <table>
      <thead>
        <tr><th>Frente</th><th>Responsavel</th><th style="text-align:right">BPC Estimativa</th>
          <th style="text-align:right">Reestimativa</th><th style="text-align:right">Gap Reest.</th>
          <th style="text-align:right">Real Colhida</th><th style="text-align:right">Real Moagem</th></tr>
      </thead>
      <tbody>{forn_rows}</tbody>
    </table>
  </div>

  <div class="sec-title">Indicadores Industriais Acumulados</div>
  <div class="kpi-grid g4">
    <div class="card">
      <div class="kpi-lbl">Etanol Hidratado (AEHC)</div>
      <div class="kpi-val">{aehc_m3:.0f} m3</div>
      <div class="kpi-plan">BPC prop.: {bpc_prop_etanol_hid:,} m3</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Etanol Anidro (AEAC)</div>
      <div class="kpi-val">{aeac_m3:.0f} m3</div>
      <div class="kpi-plan">BPC prop.: {bpc_prop_etanol_ani:,} m3</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Energia Exportada</div>
      <div class="kpi-val">{energia_exp:.0f} MWh</div>
      <div class="kpi-plan">BPC prop.: {bpc_prop_energia:,} MWh</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Vapor de Processo</div>
      <div class="kpi-val">{vapor_kt:.0f} kt</div>
      <div class="kpi-plan">BPC prop.: {bpc_prop_vapor_kt:.0f} kt</div>
    </div>
  </div>
</div>

<!-- TAB 4: AGRICOLA -->
<div class="content" id="tab4">

  <div class="sec-title">&#x1F69C; A: Estimativa vs Real vs Reestimativa</div>
  <div class="tbl-wrap">
    <div class="tbl-hdr">Moagem por Fornecedor &mdash; Safra 2026/27 Completa</div>
    <table>
      <thead>
        <tr><th>Frente</th><th>Responsavel</th><th style="text-align:right">BPC Estimativa</th>
          <th style="text-align:right">Reestimativa</th><th style="text-align:right">Gap Reest.</th>
          <th style="text-align:right">Real Colhida*</th><th style="text-align:right">Real Moagem</th></tr>
      </thead>
      <tbody>{forn_rows}</tbody>
    </table>
  </div>
  <div style="font-size:0.75rem;color:var(--text2);margin-bottom:20px">* Real Colhida = posicao de campo estimada</div>

  <div class="sec-title">&#x1F4CA; B: Qualidade Materia-Prima (Ponderado por Toneladas)</div>

  <div class="kpi-grid g4">
    <div class="card {card_atr}">
      <div class="kpi-lbl">ATR Ponderado Acumulado</div>
      <div class="kpi-val">{atr_acum:.2f} kg/t</div>
      <div class="kpi-plan">Plano ponderado: {atr_plan_pond:.2f} kg/t</div>
      <div class="kpi-delta">{delta_span(atr_acum, atr_plan_pond, suffix=" kg/t")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">TCH Real (Semana 15)</div>
      <div class="kpi-val">{tch_real:.2f} t/ha</div>
      <div class="kpi-plan">TCH Estimado: {tch_est:.2f} t/ha</div>
      <div class="kpi-delta">{delta_span(tch_real, tch_est, suffix=" t/ha")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">TAH = TCH x ATR / 1000</div>
      <div class="kpi-val">{tah_calc:.2f} t/ha</div>
      <div class="kpi-plan">TCH {tch_real:.2f} x ATR {atr_acum:.2f} / 1000</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">IM% / IV% Acumulado</div>
      <div class="kpi-val">{im_acum_val:.2f}% / {iv_acum_val:.2f}%</div>
      <div class="kpi-plan">IM% | IV% (base boletim = %)</div>
    </div>
  </div>

  <div class="method-note">
    &#x1F9EE; <strong>Ponderacao:</strong> ATR Ponderado = Sigma(ATR_mes x Moagem_mes) / Sigma(Moagem_mes)<br>
    &#x26A0;&#xFE0F; IM e IV no BPC = <strong>kg/ton</strong> | no Boletim = <strong>%</strong> &mdash; bases diferentes.
  </div>

  <div class="tbl-wrap" style="margin-top:20px">
    <div class="tbl-hdr">Qualidade por Mes &mdash; Real vs BPC</div>
    <table>
      <thead>
        <tr><th>Mes</th><th style="text-align:right">Moagem (t)</th><th style="text-align:right">ATR Real</th>
          <th style="text-align:right">IM% Real</th><th style="text-align:right">IV% Real</th>
          <th style="text-align:right">ATR BPC</th><th style="text-align:right">Delta ATR</th></tr>
      </thead>
      <tbody>{quality_rows}</tbody>
    </table>
  </div>

  <div class="sec-title">&#x1F41B; C: BROCA &mdash; Infestacao Diatraea saccharalis</div>

  <div style="background:rgba(0,200,83,0.08);border:1px solid var(--green);border-radius:12px;
    padding:16px 24px;margin-bottom:20px;display:flex;align-items:center;gap:20px">
    <div style="font-size:3rem">&#x2705;</div>
    <div>
      <div style="font-size:1.1rem;font-weight:700;color:var(--green)">DENTRO DA META | Semana 15</div>
      <div style="font-size:0.9rem;color:var(--text2);margin-top:4px">
        IFF Total Geral: <strong style="color:var(--green);font-size:1.1rem">0.916%</strong>
        | Meta: &le; <strong>1.00%</strong> | Desvio: <strong style="color:var(--green)">-8.4%</strong>
      </div>
      <div style="font-size:0.8rem;color:var(--orange);margin-top:4px">
        &#x26A0;&#xFE0F; Agua Mansa (20314): 1.286% &mdash; unica fazenda acima da meta
      </div>
    </div>
  </div>

  <div class="row2">
    <div class="chart-card">
      <div class="chart-title">IFF Broca % por Fazenda (Semana 15)</div>
      <canvas id="c_broca_faz" height="160"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Historico IFF Broca % por Safra</div>
      <canvas id="c_broca_hist" height="160"></canvas>
    </div>
  </div>

  <div class="tbl-wrap">
    <div class="tbl-hdr">IFF Broca por Fazenda &mdash; Semana 15</div>
    <table>
      <thead>
        <tr><th>Fazenda</th><th style="text-align:center">IFF Broca %</th><th style="text-align:center">Meta</th>
          <th style="text-align:center">Status</th><th style="text-align:center">Variacao vs Meta</th></tr>
      </thead>
      <tbody>{broca_rows_html}</tbody>
    </table>
  </div>

  <div class="sec-title">&#x1F33E; TCH &mdash; Semana 15</div>
  <div class="kpi-grid g4">
    <div class="card">
      <div class="kpi-lbl">Area Colhida</div>
      <div class="kpi-val">{area_ha:.2f} ha</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Toneladas (Semana)</div>
      <div class="kpi-val">{fmt_n(ton_semana)}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">TCH Real</div>
      <div class="kpi-val">{tch_real:.2f} t/ha</div>
      <div class="kpi-plan">Estimado: {tch_est:.2f}</div>
      <div class="kpi-delta">{delta_span(tch_real, tch_est, suffix=" t/ha")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">ATR Medio (Semana)</div>
      <div class="kpi-val">{atr_semana:.2f} kg/t</div>
      <div class="kpi-plan">BPC Jun/26: 139 kg/t</div>
    </div>
  </div>
</div>

<!-- TAB 5: INDUSTRIA -->
<div class="content" id="tab5">
  <div class="sec-title">&#x26A1; EFICI&Ecirc;NCIA INDUSTRIAL &mdash; Acumulado Mar&ndash;14/Jun vs BPC</div>

  <div class="kpi-grid g4">
    <div class="card">
      <div class="kpi-lbl">EGI &mdash; Efic. Global Industrial</div>
      <div class="kpi-val">{ef_ind:.2f}<small style="font-size:0.4em;color:var(--text2)"> %</small></div>
      <div class="kpi-plan">BPC ponderado: {ef_plan_pond:.2f} %</div>
      <div class="kpi-delta">{delta_span(ef_ind, ef_plan_pond, suffix=" pp")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">RTC &mdash; Rendimento Total de Cana</div>
      <div class="kpi-val">{rtc_acum_val:.2f}<small style="font-size:0.4em;color:var(--text2)"> %</small></div>
      <div class="kpi-plan">BPC Jun/26: {BPC['rtc'][3]:.2f} %</div>
      <div class="kpi-delta">{delta_span(rtc_acum_val, BPC['rtc'][3], suffix=" pp")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">&#x1F6E2; Etanol Total Acum. (m&sup3;)</div>
      <div class="kpi-val">{(aehc_m3+aeac_m3):.0f}<small style="font-size:0.4em;color:var(--text2)"> m&sup3;</small></div>
      <div class="kpi-plan">BPC prop. acum.: {bpc_prop_etanol_hid+bpc_prop_etanol_ani:.0f} m&sup3;</div>
      <div class="kpi-delta">{delta_span(aehc_m3+aeac_m3, bpc_prop_etanol_hid+bpc_prop_etanol_ani, suffix=" m³")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">&#x26A1; Energia Exportada Acum. (MWh)</div>
      <div class="kpi-val">{energia_exp:.0f}<small style="font-size:0.4em;color:var(--text2)"> MWh</small></div>
      <div class="kpi-plan">BPC prop. acum.: {bpc_prop_energia:.0f} MWh</div>
      <div class="kpi-delta">{delta_span(energia_exp, bpc_prop_energia, suffix=" MWh")}</div>
    </div>
  </div>

  <div class="kpi-grid g4" style="margin-bottom:24px">
    <div class="card">
      <div class="kpi-lbl">Etanol Hidr. (m&sup3;)</div>
      <div class="kpi-val">{aehc_m3:.0f}</div>
      <div class="kpi-plan">BPC: {bpc_prop_etanol_hid:.0f}</div>
      <div class="kpi-delta">{delta_span(aehc_m3, bpc_prop_etanol_hid, suffix=" m³")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Etanol Anid. (m&sup3;)</div>
      <div class="kpi-val">{aeac_m3:.0f}</div>
      <div class="kpi-plan">BPC: {bpc_prop_etanol_ani:.0f}</div>
      <div class="kpi-delta">{delta_span(aeac_m3, bpc_prop_etanol_ani, suffix=" m³")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">Vapor Gerado (kt)</div>
      <div class="kpi-val">{vapor_kt:.1f}</div>
      <div class="kpi-plan">BPC prop.: {bpc_prop_vapor_kt:.0f} kt</div>
      <div class="kpi-delta">{delta_span(vapor_kt, bpc_prop_vapor_kt, suffix=" kt")}</div>
    </div>
    <div class="card">
      <div class="kpi-lbl">L / Ton Cana (Acum.)</div>
      <div class="kpi-val">{((aehc_m3+aeac_m3)*1000/moa_acum if moa_acum else 0):.2f}</div>
      <div class="kpi-plan">BPC Jun/26: {BPC['l_tc'][3]:.2f} l/t</div>
    </div>
  </div>

  <div class="row2">
    <div class="chart-card">
      <div class="chart-title">Efici&ecirc;ncia Industrial (EGI%) BPC &mdash; Curva Mensal Safra 2026/27</div>
      <canvas id="c_ind_egi" height="120"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Energia Exportada (MWh) &mdash; BPC Mensal</div>
      <canvas id="c_ind_energia" height="120"></canvas>
    </div>
  </div>

  <div class="row2" style="margin-top:16px">
    <div class="chart-card">
      <div class="chart-title">Etanol Hidratado + Anidro (m&sup3;) &mdash; BPC Mensal</div>
      <canvas id="c_ind_etanol" height="120"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Vapor + Biomassa (kt) &mdash; BPC Mensal</div>
      <canvas id="c_ind_vapor" height="120"></canvas>
    </div>
  </div>

  <div class="tbl-wrap" style="margin-top:20px">
    <div class="tbl-hdr">Plano Mensal Industrial BPC &mdash; Safra 2026/27</div>
    <table>
      <thead>
        <tr>
          <th>M&ecirc;s</th>
          <th style="text-align:right">Moagem (t)</th>
          <th style="text-align:right">EGI (%)</th>
          <th style="text-align:right">RTC (%)</th>
          <th style="text-align:right">L/TC</th>
          <th style="text-align:right">Et.Hid. (m&sup3;)</th>
          <th style="text-align:right">Et.Ani. (m&sup3;)</th>
          <th style="text-align:right">Energia Exp. (MWh)</th>
          <th style="text-align:right">Vapor (kt)</th>
          <th style="text-align:right">Biomassa (kt)</th>
        </tr>
      </thead>
      <tbody>
        {ind_bpc_rows}
      </tbody>
    </table>
  </div>

  <div class="method-note" style="margin-top:16px">
    &#x26A0;&#xFE0F; UMOE-067: Energia R$250/MWh &eacute; ESTIMATIVA &mdash; aguarda contrato ACR/spot &bull;
    Dados reais mensais industriais dispon&iacute;veis apenas no Boletim Industrial PDF (acumulado).
  </div>
</div>

<!-- TAB 6: TENDENCIAS & CENARIOS -->
<div class="content" id="tab6">
  <div class="alert">
    <div style="font-size:1.5rem">&#x1F4CA;</div>
    <div><strong>PROJE&Ccedil;&Atilde;O FINAL DE SAFRA:</strong>
      Moagem acumulada {fmt_n(round(moa_acum))} t &mdash;
      Reestimativa total {fmt_n(reest_total)} t vs BPC {fmt_n(BPC_TOTAL_MOA)} t &mdash;
      Gap: <span style="color:#FF1744">{fmt_n(round(reest_total - BPC_TOTAL_MOA))} t ({((reest_total/BPC_TOTAL_MOA-1)*100):+.1f}%)</span>
    </div>
  </div>

  <div class="sec-title">&#x1F3AF; CENA&#x0301;RIOS PROJETADOS &mdash; Final de Safra 2026/27</div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:24px">
    <div class="card red" style="text-align:center;padding:24px">
      <div style="font-size:2rem;margin-bottom:8px">&#x1F534;</div>
      <div style="font-size:0.75rem;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">Pessimista</div>
      <div style="font-size:0.7rem;color:var(--text2);margin-bottom:8px">Aproveitamento restante ~60% (como Mai/26)</div>
      <div style="font-size:2.2rem;font-weight:800;color:var(--red)">1.914.718 t</div>
      <div style="font-size:0.8rem;color:var(--text2);margin:8px 0">vs BPC: <span style="color:var(--red)">-30.8%</span></div>
      <div style="background:rgba(255,23,68,0.1);border-radius:8px;padding:12px;margin-top:12px;font-size:0.8rem">
        <div>&#x1F6E2; Etanol: ~1.890 m&sup3;</div>
        <div style="margin-top:4px">&#x26A1; Energia: ~68.000 MWh</div>
        <div style="margin-top:4px">&#x1F4B0; Receita: ~R$ 380 M</div>
      </div>
    </div>
    <div class="card yellow" style="text-align:center;padding:24px">
      <div style="font-size:2rem;margin-bottom:8px">&#x1F7E1;</div>
      <div style="font-size:0.75rem;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">Base (Reestimativa)</div>
      <div style="font-size:0.7rem;color:var(--text2);margin-bottom:8px">Aproveitamento restante ~82% (hist&oacute;rico)</div>
      <div style="font-size:2.2rem;font-weight:800;color:var(--gold)">{fmt_n(reest_total)} t</div>
      <div style="font-size:0.8rem;color:var(--text2);margin:8px 0">vs BPC: <span style="color:var(--gold)">{((reest_total/BPC_TOTAL_MOA-1)*100):+.1f}%</span></div>
      <div style="background:rgba(255,214,0,0.1);border-radius:8px;padding:12px;margin-top:12px;font-size:0.8rem">
        <div>&#x1F6E2; Etanol: ~2.580 m&sup3;</div>
        <div style="margin-top:4px">&#x26A1; Energia: ~88.000 MWh</div>
        <div style="margin-top:4px">&#x1F4B0; Receita: ~R$ 520 M</div>
      </div>
    </div>
    <div class="card" style="text-align:center;padding:24px;border-color:var(--green)">
      <div style="font-size:2rem;margin-bottom:8px">&#x1F7E2;</div>
      <div style="font-size:0.75rem;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">Otimista</div>
      <div style="font-size:0.7rem;color:var(--text2);margin-bottom:8px">Aproveitamento restante ~95% (m&aacute;ximo operacional)</div>
      <div style="font-size:2.2rem;font-weight:800;color:var(--green)">2.461.052 t</div>
      <div style="font-size:0.8rem;color:var(--text2);margin:8px 0">vs BPC: <span style="color:var(--green)">-11.1%</span></div>
      <div style="background:rgba(0,200,83,0.1);border-radius:8px;padding:12px;margin-top:12px;font-size:0.8rem">
        <div>&#x1F6E2; Etanol: ~3.050 m&sup3;</div>
        <div style="margin-top:4px">&#x26A1; Energia: ~104.000 MWh</div>
        <div style="margin-top:4px">&#x1F4B0; Receita: ~R$ 615 M</div>
      </div>
    </div>
  </div>

  <div class="tbl-wrap">
    <div class="tbl-hdr">Proje&ccedil;&atilde;o Mensal Restante &mdash; 3 Cen&aacute;rios vs BPC</div>
    <table>
      <thead>
        <tr>
          <th>M&ecirc;s</th>
          <th style="text-align:right">BPC Plano (t)</th>
          <th style="text-align:right">Real/Atual (t)</th>
          <th style="text-align:right">Pessimista (t)</th>
          <th style="text-align:right">Base (t)</th>
          <th style="text-align:right">Otimista (t)</th>
          <th style="text-align:center">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr><td><strong>Mar/26</strong></td><td style="text-align:right">202.584</td>
          <td style="text-align:right;color:#FF1744">169.307</td>
          <td colspan="3" style="text-align:center;color:var(--text2)">Conclu&iacute;do</td>
          <td style="text-align:center"><span style="color:#FF1744">&#x274C; -16.4%</span></td></tr>
        <tr><td><strong>Abr/26</strong></td><td style="text-align:right">279.853</td>
          <td style="text-align:right;color:#00C853">258.410</td>
          <td colspan="3" style="text-align:center;color:var(--text2)">Conclu&iacute;do</td>
          <td style="text-align:center"><span style="color:#FF1744">&#x274C; -7.7%</span></td></tr>
        <tr><td><strong>Mai/26</strong></td><td style="text-align:right">340.481</td>
          <td style="text-align:right;color:#FF1744">178.701</td>
          <td colspan="3" style="text-align:center;color:var(--text2)">Conclu&iacute;do</td>
          <td style="text-align:center"><span style="color:#FF1744">&#x274C; -47.5%</span></td></tr>
        <tr style="background:rgba(255,214,0,0.05)"><td><strong>Jun/26 (em curso)</strong></td>
          <td style="text-align:right">295.832</td>
          <td style="text-align:right;color:#FFD600">{fmt_n(boletim.get('moa_jun',124577))}*</td>
          <td style="text-align:right">220.000</td>
          <td style="text-align:right;color:#FFD600">242.581</td>
          <td style="text-align:right">280.000</td>
          <td style="text-align:center"><span style="color:#FFD600">&#x23F3; Em curso</span></td></tr>
        <tr><td><strong>Jul/26</strong></td><td style="text-align:right">402.622</td>
          <td style="text-align:right;color:var(--text2)">—</td>
          <td style="text-align:right">241.573</td>
          <td style="text-align:right">330.150</td>
          <td style="text-align:right">382.491</td>
          <td style="text-align:center"><span style="color:var(--text2)">Futuro</span></td></tr>
        <tr><td><strong>Ago/26</strong></td><td style="text-align:right">360.951</td>
          <td style="text-align:right;color:var(--text2)">—</td>
          <td style="text-align:right">216.571</td>
          <td style="text-align:right">295.980</td>
          <td style="text-align:right">342.903</td>
          <td style="text-align:center"><span style="color:var(--text2)">Futuro</span></td></tr>
        <tr><td><strong>Set/26</strong></td><td style="text-align:right">342.203</td>
          <td style="text-align:right;color:var(--text2)">—</td>
          <td style="text-align:right">205.322</td>
          <td style="text-align:right">280.606</td>
          <td style="text-align:right">325.093</td>
          <td style="text-align:center"><span style="color:var(--text2)">Futuro</span></td></tr>
        <tr><td><strong>Out/26</strong></td><td style="text-align:right">279.556</td>
          <td style="text-align:right;color:var(--text2)">—</td>
          <td style="text-align:right">167.734</td>
          <td style="text-align:right">229.236</td>
          <td style="text-align:right">265.578</td>
          <td style="text-align:center"><span style="color:var(--text2)">Futuro</span></td></tr>
        <tr><td><strong>Nov/26</strong></td><td style="text-align:right">264.527</td>
          <td style="text-align:right;color:var(--text2)">—</td>
          <td style="text-align:right">158.716</td>
          <td style="text-align:right">216.913</td>
          <td style="text-align:right">251.297</td>
          <td style="text-align:center"><span style="color:var(--text2)">Futuro</span></td></tr>
        <tr style="font-weight:700;color:#FFD600;border-top:2px solid #00C853">
          <td>TOTAL SAFRA</td>
          <td style="text-align:right">2.768.608</td>
          <td style="text-align:right;color:#FFD600">{fmt_n(round(moa_acum))}*</td>
          <td style="text-align:right;color:#FF1744">1.914.718</td>
          <td style="text-align:right;color:#FFD600">{fmt_n(reest_total)}</td>
          <td style="text-align:right;color:#00C853">2.461.052</td>
          <td style="text-align:center">—</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:24px">
    <div>
      <div class="sec-title" style="color:var(--green)">&#x2705; PONTOS POSITIVOS</div>
      <div style="display:flex;flex-direction:column;gap:10px">
        <div style="background:rgba(0,200,83,0.08);border:1px solid rgba(0,200,83,0.3);border-radius:10px;padding:14px 16px">
          <div style="font-weight:700;color:var(--green);margin-bottom:4px">&#x1F4C8; ATR em Recupera&ccedil;&atilde;o</div>
          <div style="font-size:0.85rem;color:var(--text2)">ATR real Jun/26 (131.68) superior a Mai/26 (127.15) e Abr/26 (125.11). Curva de matura&ccedil;&atilde;o dentro do esperado — tendencia de alta at&eacute; Set/26 (meta 151 kg/t).</div>
        </div>
        <div style="background:rgba(0,200,83,0.08);border:1px solid rgba(0,200,83,0.3);border-radius:10px;padding:14px 16px">
          <div style="font-weight:700;color:var(--green);margin-bottom:4px">&#x1F41B; Broca Controlada</div>
          <div style="font-size:0.85rem;color:var(--text2)">IFF Total 0.916% — dentro da meta (&le;1.0%). Apenas 1 fazenda acima (Agua Mansa: 1.286%). A&ccedil;&otilde;es de controle preventivo mantendo o quadro sob controle.</div>
        </div>
        <div style="background:rgba(0,200,83,0.08);border:1px solid rgba(0,200,83,0.3);border-radius:10px;padding:14px 16px">
          <div style="font-weight:700;color:var(--green);margin-bottom:4px">&#x26A1; Efici&ecirc;ncia Industrial Superior</div>
          <div style="font-size:0.85rem;color:var(--text2)">RTC acumulado 94.67% (acima de alguns meses BPC). Efici&ecirc;ncia industrial {ef_ind:.2f}% pr&oacute;xima do plano — problema &eacute; volume, n&atilde;o efici&ecirc;ncia.</div>
        </div>
        <div style="background:rgba(0,200,83,0.08);border:1px solid rgba(0,200,83,0.3);border-radius:10px;padding:14px 16px">
          <div style="font-weight:700;color:var(--green);margin-bottom:4px">&#x1F680; Jun/26 Acelerando</div>
          <div style="font-size:0.85rem;color:var(--text2)">Moagem hora Jun/26: 560.32 t/h vs acumulado 526.78 t/h. Aproveitamento 66.17% vs Mai/26 cr&iacute;tico (44.4%). Recupera&ccedil;&atilde;o clara em andamento.</div>
        </div>
        <div style="background:rgba(0,200,83,0.08);border:1px solid rgba(0,200,83,0.3);border-radius:10px;padding:14px 16px">
          <div style="font-weight:700;color:var(--green);margin-bottom:4px">&#x1F33E; TCH Semana Acima da Estimativa</div>
          <div style="font-size:0.85rem;color:var(--text2)">TCH real semana 15: {tch_real:.2f} t/ha vs estimado {tch_est:.2f} t/ha. Canaviais 1C apresentando excelente rendimento para o per&iacute;odo.</div>
        </div>
      </div>
    </div>
    <div>
      <div class="sec-title" style="color:var(--red)">&#x274C; PONTOS NEGATIVOS &amp; RISCOS</div>
      <div style="display:flex;flex-direction:column;gap:10px">
        <div style="background:rgba(255,23,68,0.08);border:1px solid rgba(255,23,68,0.3);border-radius:10px;padding:14px 16px">
          <div style="font-weight:700;color:var(--red);margin-bottom:4px">&#x1F6A8; Gap Cr&iacute;tico de Moagem</div>
          <div style="font-size:0.85rem;color:var(--text2)">Moagem acumulada {fmt_n(round(moa_acum))} t vs plano proporcional {fmt_n(round(moa_plan_acum_prop))} t. Gap de {fmt_n(abs(round(gap_total_t)))} t ({abs((moa_acum/moa_plan_acum_prop-1)*100):.1f}%). Reestimativa j&aacute; abaixo do BPC em {fmt_n(abs(round(reest_total-BPC_TOTAL_MOA)))} t.</div>
        </div>
        <div style="background:rgba(255,23,68,0.08);border:1px solid rgba(255,23,68,0.3);border-radius:10px;padding:14px 16px">
          <div style="font-weight:700;color:var(--red);margin-bottom:4px">&#x1F327; Mai/26 Cr&iacute;tico (47.5% abaixo)</div>
          <div style="font-size:0.85rem;color:var(--text2)">Maio foi catastrófico: 178.701 t vs plano 340.481 t. Aproveitamento 44.4%. Principal causador do gap acumulado. Risco: se condi&ccedil;&otilde;es repetirem em Out/Nov o cen&aacute;rio pessimista se materializa.</div>
        </div>
        <div style="background:rgba(255,109,0,0.08);border:1px solid rgba(255,109,0,0.3);border-radius:10px;padding:14px 16px">
          <div style="font-weight:700;color:var(--orange);margin-bottom:4px">&#x1F33F; ATR Abaixo do Meta da Safra</div>
          <div style="font-size:0.85rem;color:var(--text2)">ATR ponderado acumulado {atr_acum:.2f} kg/t vs meta safra 138.66 kg/t. Gap de {atr_acum-138.66:+.2f} kg/t. Necess&aacute;rio ATR &gt;145 kg/t nos meses Jul-Set para compensar.</div>
        </div>
        <div style="background:rgba(255,23,68,0.08);border:1px solid rgba(255,23,68,0.3);border-radius:10px;padding:14px 16px">
          <div style="font-weight:700;color:var(--red);margin-bottom:4px">&#x1F697; Canaviais 4C+ em Renova&ccedil;&atilde;o Urgente</div>
          <div style="font-size:0.85rem;color:var(--text2)">15.173 ha com TCH m&eacute;dio 64 t/ha vs 99.6 t/ha no 1C. Produtividade 35.7% abaixo do potencial. Impacto direto na moagem e no CCT. Renova&ccedil;&atilde;o acelerada &eacute; a a&ccedil;&atilde;o estrutural mais importante.</div>
        </div>
        <div style="background:rgba(255,109,0,0.08);border:1px solid rgba(255,109,0,0.3);border-radius:10px;padding:14px 16px">
          <div style="font-weight:700;color:var(--orange);margin-bottom:4px">&#x1F4B8; CCT R$50.0/t vs Or&ccedil;ado R$38.3/t</div>
          <div style="font-size:0.85rem;color:var(--text2)">Custo de corte-carregamento-transporte 30.5% acima do or&ccedil;ado (+R$11.7/t). Com o gap de volume, o efeito de dilui&ccedil;&atilde;o dos custos fixos piora o resultado operacional.</div>
        </div>
      </div>
    </div>
  </div>

  <div class="sec-title" style="margin-top:24px">&#x1F4C8; TEND&Ecirc;NCIA FINAL DE SAFRA &mdash; Proje&ccedil;&atilde;o Jul&ndash;Nov/26</div>
  <div class="row2">
    <div class="chart-card">
      <div class="chart-title">Moagem Mensal BPC vs Cen&aacute;rios &mdash; Safra 2026/27</div>
      <canvas id="c_cenarios" height="130"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Acumulado Safra &mdash; BPC vs Trajet&oacute;rias</div>
      <canvas id="c_trajetoria" height="130"></canvas>
    </div>
  </div>

  <div class="method-note" style="margin-top:16px">
    &#x1F9EE; Cen&aacute;rio Pessimista: aproveitamento 60% restante | Base (Reestimativa TCH-BROCA): 82% | Otimista: 95% &bull;
    Receita estimada: etanol R$2.50/l + ATR R$1.03/kg (CONSECANA) + Energia R$250/MWh (UMOE-067: ESTIMATIVA) &bull;
    TAH atual: {tah_calc:.2f} t ATR/ha (TCH {tch_real:.2f} &times; ATR {atr_acum:.2f}/1000)
  </div>
</div>

<script>
function switchTab(n){{
  document.querySelectorAll('.tab').forEach((t,i)=>t.classList.toggle('active',i===n));
  document.querySelectorAll('.content').forEach((c,i)=>c.classList.toggle('active',i===n));
}}
const GREEN='#00C853',GOLD='#FFD600',RED='#FF1744',ORANGE='#FF6D00',BLUE='#42A5F5',PURPLE='#AB47BC';
const BORDER='rgba(255,255,255,0.08)',TEXT='#90A4AE';
Chart.defaults.color=TEXT;
Chart.defaults.borderColor=BORDER;
Chart.defaults.font.family="'Inter',system-ui,sans-serif";

const MESES={meses_json};
const BPC_MOA={bpc_moa_json};
const REAL_MOA={real_moa_json};
const BPC_ATR={bpc_atr_json};
const REAL_ATR={real_atr_json};
const BROCA_FAZ={json.dumps(broca_fazendas)};
const BROCA_IFF={json.dumps(broca_iff)};
const BROCA_HIST_ANOS={json.dumps(broca_hist_anos)};
const BROCA_HIST_IFF={json.dumps(broca_hist_iff)};

function makeGauge(id,val,max,color){{
  const ctx=document.getElementById(id);if(!ctx)return;
  const pct=Math.min(val/max,1);
  new Chart(ctx,{{type:'doughnut',
    data:{{datasets:[{{data:[pct,1-pct],
      backgroundColor:[color,'rgba(255,255,255,0.06)'],
      borderWidth:0,circumference:180,rotation:270}}]}},
    options:{{responsive:true,maintainAspectRatio:true,cutout:'70%',
      plugins:{{legend:{{display:false}},tooltip:{{enabled:false}}}}}}
  }});
}}

window.addEventListener('DOMContentLoaded',function(){{
  makeGauge('gauge_safra',{exec_safra_pct:.4f},100,'{sc_exec}');
  makeGauge('gauge_aprov',{aprov_acum_val:.4f},100,'{sc_aprov}');
  makeGauge('gauge_atr',{atr_acum:.4f},{atr_plan_pond*1.05:.4f},'{sc_atr}');

  new Chart(document.getElementById('c_moa_mensal'),{{type:'bar',
    data:{{labels:MESES,datasets:[
      {{label:'BPC Plano',data:BPC_MOA,backgroundColor:'rgba(33,150,243,0.3)',borderColor:BLUE,borderWidth:2}},
      {{label:'Real',data:REAL_MOA,
        backgroundColor:REAL_MOA.map((v,i)=>v===null?'transparent':v>=BPC_MOA[i]*0.95?'rgba(0,200,83,0.7)':v>=BPC_MOA[i]*0.80?'rgba(255,214,0,0.7)':'rgba(255,23,68,0.7)'),
        borderWidth:0}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{labels:{{color:TEXT}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+(c.raw?.toLocaleString('pt-BR')||'-')+' t'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT,callback:v=>v.toLocaleString('pt-BR')}},grid:{{color:BORDER}}}}}}
    }}
  }});

  new Chart(document.getElementById('c_atr'),{{type:'line',
    data:{{labels:MESES,datasets:[
      {{label:'BPC ATR',data:BPC_ATR,borderColor:BLUE,backgroundColor:'rgba(33,150,243,0.1)',tension:0.4,fill:true}},
      {{label:'Real ATR',data:REAL_ATR,borderColor:GREEN,backgroundColor:'rgba(0,200,83,0.1)',tension:0.4,fill:true,pointRadius:5,pointBackgroundColor:GREEN}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{labels:{{color:TEXT}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+(c.raw?.toFixed(2)||'-')+' kg/t'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT}},grid:{{color:BORDER}},min:100,max:165}}}}
    }}
  }});

  new Chart(document.getElementById('c_paradas'),{{type:'doughnut',
    data:{{labels:['Clima ({par_clima_h:.0f}h)','Industria ({par_ind_h:.0f}h)','Agricola ({par_agr_h:.0f}h)'],
      datasets:[{{data:[{par_clima_h:.1f},{par_ind_h:.1f},{par_agr_h:.1f}],
        backgroundColor:[ORANGE,BLUE,PURPLE],borderWidth:2,borderColor:'#0A1628'}}]}},
    options:{{responsive:true,maintainAspectRatio:true,cutout:'60%',
      plugins:{{legend:{{position:'right',labels:{{color:TEXT,padding:16}}}}}}
    }}
  }});

  new Chart(document.getElementById('c_moa_hora'),{{type:'bar',
    data:{{labels:['Acum. Safra','Jun/26 Real','BPC Jun/26'],
      datasets:[{{label:'t/h',data:[{mh_acum:.2f},{mh_jun:.2f},{mh_bpc:.2f}],
        backgroundColor:[BLUE,GREEN,'rgba(33,150,243,0.4)'],borderWidth:0}}]
    }},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{display:false}}}},
      scales:{{x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT}},grid:{{color:BORDER}},min:450}}}}
    }}
  }});

  new Chart(document.getElementById('c_jun_prog'),{{type:'bar',
    data:{{labels:['Real 1-14/Jun','BPC Proporcional (14d)','BPC Plano Jun Cheio'],
      datasets:[{{data:[{round(moa_jun_real)},{round(moa_jun_prop)},{BPC['moagem'][3]}],
        backgroundColor:[GREEN,'rgba(255,214,0,0.5)','rgba(33,150,243,0.4)'],
        borderColor:[GREEN,GOLD,BLUE],borderWidth:2}}]
    }},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>c.raw.toLocaleString('pt-BR')+' t'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT,callback:v=>v.toLocaleString('pt-BR')}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}}}}
    }}
  }});

  new Chart(document.getElementById('c_waterfall'),{{type:'bar',
    data:{{labels:['Mar/26','Abr/26','Mai/26','Jun/26 (parcial)'],
      datasets:[
        {{label:'BPC Plano',data:[{BPC['moagem'][0]},{BPC['moagem'][1]},{BPC['moagem'][2]},{round(moa_jun_prop)}],
          backgroundColor:'rgba(33,150,243,0.35)',borderColor:BLUE,borderWidth:2}},
        {{label:'Real',data:[{boletim.get('moa_mar',169307)},{boletim.get('moa_abr',258410)},{boletim.get('moa_mai',178701)},{boletim.get('moa_jun',124577)}],
          backgroundColor:[RED,GREEN,RED,GOLD],borderWidth:0}}
      ]}},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{labels:{{color:TEXT}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+c.raw.toLocaleString('pt-BR')+' t'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT,callback:v=>v.toLocaleString('pt-BR')}},grid:{{color:BORDER}}}}}}
    }}
  }});

  new Chart(document.getElementById('c_broca_faz'),{{type:'bar',
    data:{{labels:BROCA_FAZ,datasets:[
      {{label:'IFF Broca %',data:BROCA_IFF,backgroundColor:BROCA_IFF.map(v=>v>1.0?RED:GREEN),borderWidth:0}},
      {{label:'Meta (1.0%)',data:BROCA_IFF.map(()=>1.0),type:'line',borderColor:GOLD,borderDash:[5,5],borderWidth:2,pointRadius:0}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{labels:{{color:TEXT}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+(c.raw?.toFixed(3)||'-')+'%'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT,maxRotation:30}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT,callback:v=>v.toFixed(2)+'%'}},grid:{{color:BORDER}},min:0,max:1.6}}}}
    }}
  }});

  new Chart(document.getElementById('c_broca_hist'),{{type:'bar',
    data:{{labels:BROCA_HIST_ANOS,datasets:[
      {{label:'IFF Broca %',data:BROCA_HIST_IFF,backgroundColor:BROCA_HIST_IFF.map(v=>v>1.0?'rgba(255,23,68,0.7)':'rgba(0,200,83,0.7)'),borderWidth:0}},
      {{label:'Meta (1.0%)',data:BROCA_HIST_ANOS.map(()=>1.0),type:'line',borderColor:GOLD,borderDash:[5,5],borderWidth:2,pointRadius:0}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{labels:{{color:TEXT}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+(c.raw?.toFixed(3)||'-')+'%'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT,callback:v=>v.toFixed(2)+'%'}},grid:{{color:BORDER}},min:0,max:1.5}}}}
    }}
  }});

  // INDUSTRIA charts
  const BPC_EGI={json.dumps(BPC['egi'])};
  const BPC_RTC={json.dumps(BPC['rtc'])};
  const BPC_EH={json.dumps(BPC['etanol_hid'])};
  const BPC_EA={json.dumps(BPC['etanol_ani'])};
  const BPC_ENEX={json.dumps(BPC['energia_exp'])};
  const BPC_VAP={json.dumps([v//1000 for v in BPC['vapor']])};
  const BPC_BIO={json.dumps([v//1000 for v in BPC['biomassa']])};

  new Chart(document.getElementById('c_ind_egi'),{{type:'line',
    data:{{labels:MESES,datasets:[
      {{label:'EGI BPC %',data:BPC_EGI,borderColor:BLUE,backgroundColor:'rgba(33,150,243,0.1)',tension:0.4,fill:true,pointRadius:4}},
      {{label:'RTC BPC %',data:BPC_RTC,borderColor:GREEN,backgroundColor:'rgba(0,200,83,0.05)',tension:0.4,fill:false,borderDash:[5,5],pointRadius:3}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{labels:{{color:TEXT}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+c.raw.toFixed(2)+'%'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT,callback:v=>v.toFixed(1)+'%'}},grid:{{color:BORDER}},min:82,max:96}}}}
    }}
  }});

  new Chart(document.getElementById('c_ind_energia'),{{type:'bar',
    data:{{labels:MESES,datasets:[
      {{label:'Energia Exportada MWh',data:BPC_ENEX,backgroundColor:'rgba(255,214,0,0.6)',borderColor:GOLD,borderWidth:1}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{labels:{{color:TEXT}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+c.raw.toLocaleString('pt-BR')+' MWh'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT,callback:v=>v.toLocaleString('pt-BR')}},grid:{{color:BORDER}}}}}}
    }}
  }});

  new Chart(document.getElementById('c_ind_etanol'),{{type:'bar',
    data:{{labels:MESES,datasets:[
      {{label:'Hidratado (m³)',data:BPC_EH,backgroundColor:'rgba(0,200,83,0.5)',borderColor:GREEN,borderWidth:1}},
      {{label:'Anidro (m³)',data:BPC_EA,backgroundColor:'rgba(33,150,243,0.5)',borderColor:BLUE,borderWidth:1}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{labels:{{color:TEXT}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+c.raw.toLocaleString('pt-BR')+' m³'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT,callback:v=>v.toLocaleString('pt-BR')}},grid:{{color:BORDER}}}},stacked:true}}
    }}
  }});

  new Chart(document.getElementById('c_ind_vapor'),{{type:'bar',
    data:{{labels:MESES,datasets:[
      {{label:'Vapor (kt)',data:BPC_VAP,backgroundColor:'rgba(171,71,188,0.5)',borderColor:PURPLE,borderWidth:1}},
      {{label:'Biomassa (kt)',data:BPC_BIO,backgroundColor:'rgba(255,109,0,0.5)',borderColor:ORANGE,borderWidth:1}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{labels:{{color:TEXT}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+c.raw.toLocaleString('pt-BR')+' kt'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT,callback:v=>v.toLocaleString('pt-BR')}},grid:{{color:BORDER}}}}}}
    }}
  }});

  // TENDENCIAS charts
  const MESES_FULL=['Mar/26','Abr/26','Mai/26','Jun/26','Jul/26','Ago/26','Set/26','Out/26','Nov/26'];
  const BPC_FULL={json.dumps(BPC['moagem'])};
  const REAL_FULL=[169307,258410,178701,{boletim.get('moa_jun',124577)},null,null,null,null,null];
  const PESSIM=[169307,258410,178701,220000,241573,216571,205322,167734,158716];
  const BASE_EST=[169307,258410,178701,242581,330150,295980,280606,229236,216913];
  const OTIMIST=[169307,258410,178701,280000,382491,342903,325093,265578,251297];

  new Chart(document.getElementById('c_cenarios'),{{type:'bar',
    data:{{labels:MESES_FULL,datasets:[
      {{label:'BPC Plano',data:BPC_FULL,backgroundColor:'rgba(33,150,243,0.25)',borderColor:BLUE,borderWidth:2}},
      {{label:'Real/Atual',data:REAL_FULL,backgroundColor:REAL_FULL.map((v,i)=>v===null?'transparent':v>=BPC_FULL[i]*0.95?'rgba(0,200,83,0.8)':'rgba(255,23,68,0.8)'),borderWidth:0}},
      {{label:'Base (Reest.)',data:BASE_EST,type:'line',borderColor:GOLD,borderWidth:2,borderDash:[4,4],pointRadius:3,fill:false}},
      {{label:'Otimista',data:OTIMIST,type:'line',borderColor:GREEN,borderWidth:1,borderDash:[2,4],pointRadius:2,fill:false}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{labels:{{color:TEXT}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+(c.raw?.toLocaleString('pt-BR')||'—')+' t'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT,callback:v=>v.toLocaleString('pt-BR')}},grid:{{color:BORDER}}}}}}
    }}
  }});

  // Cumulative trajectories
  function cumsum(arr){{let s=0;return arr.map(v=>v===null?null:(s+=v,s));}}
  new Chart(document.getElementById('c_trajetoria'),{{type:'line',
    data:{{labels:MESES_FULL,datasets:[
      {{label:'BPC Acumulado',data:cumsum(BPC_FULL),borderColor:BLUE,backgroundColor:'rgba(33,150,243,0.05)',borderWidth:2,tension:0.3,fill:true}},
      {{label:'Real/Atual',data:cumsum(REAL_FULL),borderColor:GREEN,backgroundColor:'rgba(0,200,83,0.1)',borderWidth:3,tension:0.3,pointRadius:5,fill:false}},
      {{label:'Base (Reestimativa)',data:cumsum(BASE_EST),borderColor:GOLD,borderWidth:2,borderDash:[5,5],tension:0.3,pointRadius:3,fill:false}},
      {{label:'Pessimista',data:cumsum(PESSIM),borderColor:RED,borderWidth:1,borderDash:[3,5],tension:0.3,pointRadius:2,fill:false}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:true,
      plugins:{{legend:{{labels:{{color:TEXT}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+(c.raw?.toLocaleString('pt-BR')||'—')+' t acum.'}}}}}},
      scales:{{x:{{ticks:{{color:TEXT}},grid:{{color:BORDER}}}},y:{{ticks:{{color:TEXT,callback:v=>(v/1000).toFixed(0)+'K'}},grid:{{color:BORDER}}}}}}
    }}
  }});
}});
</script>
</body>
</html>"""
    return html


if __name__ == "__main__":
    print("=" * 60)
    print("UMOE OS 8.0 | Painel Moagem | Safra 2026/27")
    print("=" * 60)

    boletim, pdf_path = ler_boletim()
    if pdf_path:
        print(f"[OK] Boletim: {os.path.basename(pdf_path)}")
    else:
        print("[FALLBACK] Using hardcoded boletim data (14/06/2026)")

    agri = ler_tch_broca()
    print(f"[OK] TCH-BROCA: Reestimativa total = {agri['moagem']['total_reest']:,} t")

    ponds = calcular_ponderados(boletim)
    print(f"[OK] ATR ponderado calculado: {ponds['atr_ponderado']:.2f} kg/t")

    html = gerar_html(boletim, agri, datetime.now())

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUT_HTML) / 1024
    print(f"[OK] HTML gerado: {OUT_HTML}")
    print(f"[OK] Tamanho: {size_kb:.1f} KB")
    print("=" * 60)
    print("CONCLUIDO!")
