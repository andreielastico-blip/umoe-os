# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Inteligencia Cruzada
Cruza TCH/ATR/TAH x Variedade x Ambiente x Idade x Estagio x Frente +
chuva->ATR com defasagem (lag) + projecao de fim de safra calibrada.
Tudo a partir de dados reais (BD SAFRAS 8 safras, CTT_HISTPRD, historico
industrial, pluviometria oficial).

Saida: UMOE-OS-8.0/Relatorios/UMOE_Inteligencia_Cruzada.html (+ docs/)
"""
import json, glob
from pathlib import Path
from datetime import datetime
try:
    import pandas as pd, numpy as np
except ImportError:
    import os; os.system("pip install pandas numpy -q"); import pandas as pd, numpy as np
import warnings; warnings.filterwarnings("ignore")
try: import openpyxl
except ImportError: import os; os.system("pip install openpyxl -q")

ROOT = Path(__file__).parent.parent.parent
PBI  = ROOT / "UMOE-OS-8.0" / "Dados-PBI"
OUT  = ROOT / "UMOE-OS-8.0" / "Relatorios" / "UMOE_Inteligencia_Cruzada.html"
DOCS = ROOT / "docs"
HOJE = datetime.now().strftime("%d/%m/%Y")
PLAN = r"C:\01 - UMOE\03 - Financeiro\Planilhas"

def L(n):
    p = PBI / f"{n}.json"
    if not p.exists(): return pd.DataFrame()
    d = json.load(open(p, encoding="utf-8-sig"))
    df = pd.DataFrame(d); df.columns=[c.split("[")[-1].rstrip("]") for c in df.columns]; return df
def N(s): return pd.to_numeric(s, errors="coerce").fillna(0)
def br(v,d=0):
    try: return f"{float(v):,.{d}f}".replace(",","X").replace(".",",").replace("X",".")
    except: return "-"

charts={}; ins=[]
def add(t,tipo="info"): ins.append({"t":t,"tipo":tipo})

print("[1/4] BD SAFRAS (8 safras)...")
bd_f=glob.glob(PLAN+r"\Historico Kpis*Agr*.xlsx")
bd=pd.DataFrame()
if bd_f:
    wb=pd.ExcelFile(bd_f[0]); sh=next((s for s in wb.sheet_names if "BD" in s.upper() and "SAFRA" in s.upper()), wb.sheet_names[0])
    bd=wb.parse(sh,header=0).rename(columns={"Amb.Prod. ":"AMB","Variedade ":"VAR","Estágio":"EST",
        "Idade":"IDADE","Área Realiz.":"AREA","TCH Realiz.":"TCH","   ATR":"ATR","   TAH":"TAH","N_Corte":"CORTE","Safra":"SAFRA"})
    for c in ["AREA","TCH","ATR","TAH","CORTE"]: bd[c]=N(bd.get(c))
    bd=bd[(bd.AREA>0.5)&(bd.TCH>10)&(bd.TAH>0.5)].copy()
    bd["AMB1"]=bd["AMB"].astype(str).str[:1]

def pond(df,by,val,area="AREA"):
    g=df.groupby(by).apply(lambda x:(x[val]*x[area]).sum()/x[area].sum() if x[area].sum() else 0)
    return g

var_amb=pd.DataFrame(); idade_tah=pd.DataFrame(); est_tah=pd.DataFrame(); var_rank=pd.DataFrame()
if not bd.empty:
    g=bd.groupby(["VAR","AMB1"]).apply(lambda x:pd.Series({
        "TAH":(x.TAH*x.AREA).sum()/x.AREA.sum(),"TCH":(x.TCH*x.AREA).sum()/x.AREA.sum(),
        "ATR":(x.ATR*x.AREA).sum()/x.AREA.sum(),"AREA":x.AREA.sum()})).reset_index()
    var_amb=g[g.AREA>500].sort_values("TAH",ascending=False)
    charts["var_amb_top"]=var_amb.head(12).to_dict("records")
    charts["var_amb_bot"]=var_amb.tail(6).to_dict("records")
    gi=bd[bd.CORTE.between(1,9)].groupby("CORTE").apply(lambda x:pd.Series({
        "TAH":(x.TAH*x.AREA).sum()/x.AREA.sum(),"TCH":(x.TCH*x.AREA).sum()/x.AREA.sum(),"AREA":x.AREA.sum()})).reset_index()
    idade_tah=gi; charts["idade"]=gi.to_dict("records")
    if "EST" in bd.columns:
        ge=bd.groupby(bd["EST"].astype(str)).apply(lambda x:pd.Series({"TAH":(x.TAH*x.AREA).sum()/x.AREA.sum(),"AREA":x.AREA.sum()})).reset_index()
        ge.columns=["EST","TAH","AREA"]; est_tah=ge[ge.AREA>1000].sort_values("EST")
        charts["estagio"]=est_tah.to_dict("records")
    vr=bd.groupby("VAR").apply(lambda x:pd.Series({"TAH":(x.TAH*x.AREA).sum()/x.AREA.sum(),
        "TCH":(x.TCH*x.AREA).sum()/x.AREA.sum(),"ATR":(x.ATR*x.AREA).sum()/x.AREA.sum(),"AREA":x.AREA.sum()})).reset_index()
    var_rank=vr[vr.AREA>vr.AREA.sum()*0.005].sort_values("TAH",ascending=False)
    if not var_amb.empty:
        b=var_amb.iloc[0]; w=var_amb.iloc[-1]
        add(f"Variedade x Ambiente: <b>{b.VAR.strip()} x Amb.{b.AMB1}</b> rende <b>{br(b.TAH,1)} t ATR/ha</b> "
            f"vs apenas {br(w.TAH,1)} do pior ({w.VAR.strip()} x Amb.{w.AMB1}) — diferenca de <b>{br(b.TAH/w.TAH,1)}x</b>. "
            f"Alocar variedade por aptidao de ambiente e a maior alavanca estrutural de ATR/ha.","verde")
    if not idade_tah.empty:
        c1=idade_tah[idade_tah.CORTE==1]["TAH"].sum(); c4=idade_tah[idade_tah.CORTE==4]["TAH"].sum()
        add(f"Idade do canavial: TAH cai de <b>{br(c1,1)}</b> (1o corte) para <b>{br(c4,1)}</b> no 4o corte "
            f"(-{br((1-c4/c1)*100,0) if c1 else 0}%). Renovacao dos talhoes 4C+ recupera produtividade — priorizar os de pior TAH.","amarelo")

print("[2/4] Entrega por frente x variedade (safra atual)...")
his=L("BASE_CTT_HISTPRD"); fre_var=pd.DataFrame()
GRP={1:"Propria",2:"Propria",3:"Propria",4:"Propria",10:"Lerosa",27:"Fabiano"}
if not his.empty:
    his["QT_CANA_ENT"]=N(his.QT_CANA_ENT); his["KG_ACUCAR"]=N(his.KG_ACUCAR)
    his["GRP"]=pd.to_numeric(his.CD_FREN_TRAN,errors="coerce").map(GRP).fillna("Outras")
    g=his.groupby("GRP").apply(lambda x:pd.Series({"CANA":x.QT_CANA_ENT.sum(),
        "ATR":x.KG_ACUCAR.sum()/x.QT_CANA_ENT.sum() if x.QT_CANA_ENT.sum() else 0})).reset_index()
    fre_var=g[g.CANA>0].sort_values("CANA",ascending=False)
    charts["frente"]=fre_var.to_dict("records")

print("[3/4] Chuva -> ATR com defasagem (lag) ...")
lag_res=[]
try:
    # ATR mensal por safra (historico industrial)
    fI=glob.glob(PLAN+r"\Hist*Industri*Safras.xlsx")
    chuva_m={}; atr_m={}
    if fI:
        wbI=openpyxl.load_workbook(fI[0],read_only=True,data_only=True)
        for ano in ["2022","2023","2024","2025","2026"]:
            if ano not in wbI.sheetnames: continue
            for r in wbI[ano].iter_rows(min_row=3,values_only=True):
                dt=r[2] if len(r)>2 else None
                if dt is None or not hasattr(dt,"month"): continue
                mo=float(r[3] or 0) if len(r)>3 and r[3] else 0; at=float(r[4] or 0) if len(r)>4 and r[4] else 0
                if mo>0:
                    key=(dt.year,dt.month); atr_m.setdefault(key,[0,0]); atr_m[key][0]+=mo*at; atr_m[key][1]+=mo
    # chuva mensal (pluviometrico HISTORICO)
    pl=PLAN+r"\1 - Indice Pluviometrico UMOE.xlsx"
    if Path(pl).exists():
        ch=pd.read_excel(pl,sheet_name="HISTORICO"); ch.columns=[str(c).strip().upper() for c in ch.columns]
        qt=next((c for c in ch.columns if "LEITURA" in c),None); dc=next((c for c in ch.columns if c=="DATA"),None)
        if qt and dc:
            ch[qt]=N(ch[qt]); ch["_d"]=pd.to_datetime(ch[dc],errors="coerce")
            ch=ch.dropna(subset=["_d"]);
            gm=ch.groupby([ch._d.dt.year,ch._d.dt.month])[qt].sum()
            for (y,m),v in gm.items(): chuva_m[(y,m)]=float(v)
    # series alinhadas
    atr_series={k:(v[0]/v[1]) for k,v in atr_m.items() if v[1]>0}
    keys=sorted(set(atr_series)&set(chuva_m))
    if len(keys)>=10:
        def shift(k,lag):
            y,m=k; m-=lag
            while m<=0: m+=12; y-=1
            return (y,m)
        for lag in range(0,7):
            pairs=[(chuva_m[shift(k,lag)],atr_series[k]) for k in keys if shift(k,lag) in chuva_m]
            if len(pairs)>=8:
                a=np.array(pairs); c=np.corrcoef(a[:,0],a[:,1])[0,1]
                lag_res.append({"lag":lag,"corr":float(c),"n":len(pairs)})
        if lag_res:
            best=max(lag_res,key=lambda x:abs(x["corr"]))
            charts["lag"]=lag_res
            sinal="negativa" if best["corr"]<0 else "positiva"
            add(f"Chuva -> ATR: correlacao mais forte com defasagem de <b>{best['lag']} meses</b> "
                f"(r={br(best['corr'],2)}, {sinal}; n={best['n']}). "
                f"Chuva concentrada {best['lag']} meses antes {'reduz' if best['corr']<0 else 'eleva'} o ATR — antecipa a janela de maturacao.",
                "info")
except Exception as e: print("  lag:",e)

print("[4/4] Projecao calibrada de fim de safra...")
proj={}
try:
    META=2_768_000
    fI=glob.glob(PLAN+r"\Hist*Industri*Safras.xlsx")
    if fI:
        wbI=openpyxl.load_workbook(fI[0],read_only=True,data_only=True)
        # curva de % acumulado por mes-do-ano para safras completas (2022-2025)
        perfis=[]
        for ano in ["2022","2023","2024","2025"]:
            if ano not in wbI.sheetnames: continue
            mm={}
            for r in wbI[ano].iter_rows(min_row=3,values_only=True):
                dt=r[2] if len(r)>2 else None
                if dt is None or not hasattr(dt,"month"): continue
                mm[dt.month]=mm.get(dt.month,0)+(float(r[3] or 0) if len(r)>3 and r[3] else 0)
            tot=sum(mm.values())
            if tot>500000:
                perfis.append({m:mm.get(m,0)/tot for m in range(1,13)})
        if perfis:
            # perfil mediano de fracao acumulada ate o mes
            cumperf=[]
            for p in perfis:
                acc=0; c={}
                for m in range(1,13): acc+=p.get(m,0); c[m]=acc
                cumperf.append(c)
            # safra atual: realizado ate o ultimo mes
            cur={}
            for r in wbI["2026"].iter_rows(min_row=3,values_only=True):
                dt=r[2] if len(r)>2 else None
                if dt is None or not hasattr(dt,"month"): continue
                cur[dt.month]=cur.get(dt.month,0)+(float(r[3] or 0) if len(r)>3 and r[3] else 0)
            real=sum(cur.values()); ultmes=max(cur) if cur else 6
            frac_med=float(np.median([c[ultmes] for c in cumperf]))
            proj["real"]=real; proj["frac"]=frac_med
            proj["final"]=real/frac_med if frac_med else 0
            proj["meta"]=META; proj["gap"]=proj["final"]-META
            charts["proj"]={"real":real,"final":proj["final"],"meta":META,"ultmes":ultmes,"frac":frac_med*100}
            add(f"Projecao CALIBRADA (curva-S real das ultimas safras, nao linear): no mes {ultmes} a UMOE moeu "
                f"<b>{br(real)} t</b> = {br(frac_med*100,0)}% do que historicamente moe ate aqui. "
                f"Projecao de fim de safra: <b>{br(proj['final'])} t</b> vs meta {br(META)} t = "
                f"{'deficit' if proj['gap']<0 else 'superavit'} de <b>{br(abs(proj['gap']))} t</b>.",
                "vermelho" if proj["gap"]<0 else "verde")
except Exception as e: print("  proj:",e)

# ── HTML ──────────────────────────────────────────────────────────────────────
def rows(df,cols,fmts):
    return "".join("<tr>"+"".join(f"<td>{fmts[i](r[c])}</td>" for i,c in enumerate(cols))+"</tr>" for _,r in df.iterrows())
varamb_rows = rows(var_amb.head(12),["VAR","AMB1","TAH","TCH","ATR","AREA"],[lambda v:str(v).strip(),str,lambda v:br(v,1),lambda v:br(v,0),lambda v:br(v,1),lambda v:br(v,0)]) if not var_amb.empty else "<tr><td colspan=6>-</td></tr>"
ins_html="".join(f'<div class="insight {i["tipo"]}">{i["t"]}</div>' for i in ins) or '<div class="insight info">Sem dados.</div>'

html=f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UMOE | Inteligencia Cruzada</title><script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#0A0F1E;--surf:#111A30;--line:#22325C;--txt:#E8EEFC;--mut:#8FA3C8;--green:#22C55E;--gold:#FACC15;--red:#F43F5E;--blue:#3B82F6;--cyan:#22D3EE}}
*{{margin:0;padding:0;box-sizing:border-box}}body{{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px}}
header{{padding:22px 34px;border-bottom:1px solid var(--line);background:var(--surf)}}
header h1{{font-size:1.25rem;color:#fff}}header .sub{{color:var(--mut);font-size:.8rem;margin-top:3px}}
.wrap{{max-width:1500px;margin:0 auto;padding:24px 34px}}
.card{{background:var(--surf);border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:18px}}
.card h3{{font-size:.85rem;color:var(--gold);text-transform:uppercase;letter-spacing:.8px;margin-bottom:16px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
.chart{{position:relative;height:300px}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}th{{text-align:left;color:var(--mut);font-size:.7rem;text-transform:uppercase;padding:8px 10px;border-bottom:1px solid var(--line)}}
td{{padding:7px 10px;border-bottom:1px solid #16213d}}tr:hover td{{background:#16213d}}
.insight{{background:#16213d;border-left:3px solid var(--blue);border-radius:0 10px 10px 0;padding:13px 16px;margin-bottom:12px;font-size:.92rem;line-height:1.55}}
.insight.verde{{border-left-color:var(--green)}}.insight.amarelo{{border-left-color:var(--gold)}}.insight.vermelho{{border-left-color:var(--red)}}
.foot{{color:var(--mut);font-size:.72rem;padding:18px 34px;border-top:1px solid var(--line);text-align:center}}
</style></head><body>
<header><h1>UMOE BIOENERGY — Inteligencia Cruzada</h1><div class="sub">Cruzamento de TCH/ATR/TAH x Variedade x Ambiente x Idade x Estagio x Frente + Chuva-lag + Projecao | {HOJE}</div></header>
<div class="wrap">
  <div class="card"><h3>Conclusoes cruzadas (calculadas dos dados reais)</h3>{ins_html}</div>
  <div class="grid">
    <div class="card"><h3>Variedade x Ambiente — TAH (t ATR/ha) — top 12</h3><div class="chart"><canvas id="cVA"></canvas></div></div>
    <div class="card"><h3>TAH x Idade do canavial (corte)</h3><div class="chart"><canvas id="cID"></canvas></div></div>
  </div>
  <div class="grid">
    <div class="card"><h3>Entrega de cana por frente + ATR (safra atual)</h3><div class="chart"><canvas id="cFR"></canvas></div></div>
    <div class="card"><h3>Chuva -> ATR: correlacao por defasagem (meses)</h3><div class="chart"><canvas id="cLAG"></canvas></div></div>
  </div>
  <div class="card"><h3>Projecao calibrada de fim de safra (curva-S real)</h3><div class="chart"><canvas id="cPROJ"></canvas></div></div>
  <div class="card"><h3>Matriz Variedade x Ambiente (top 12 por TAH)</h3>
    <table><tr><th>Variedade</th><th>Amb.</th><th>TAH</th><th>TCH</th><th>ATR</th><th>Area (ha)</th></tr>{varamb_rows}</table></div>
</div>
<div class="foot">UMOE OS 8.0 | Inteligencia Cruzada | dados reais: BD SAFRAS (8 safras), CTT_HISTPRD, historico industrial, pluviometria oficial | {HOJE}</div>
<script>
const CT={json.dumps(charts,ensure_ascii=False,default=str)};
const G='#22C55E',O='#FACC15',B='#3B82F6',R='#F43F5E',C='#22D3EE',M='#8FA3C8';
const opt={{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:M,font:{{size:11}}}}}}}},scales:{{x:{{ticks:{{color:M}},grid:{{color:'#1b2848'}}}},y:{{ticks:{{color:M}},grid:{{color:'#1b2848'}}}}}}}};
(()=>{{const d=CT.var_amb_top||[];if(!d.length)return;new Chart(cVA,{{type:'bar',data:{{labels:d.map(x=>x.VAR.trim()+' '+x.AMB1),datasets:[{{label:'TAH',data:d.map(x=>x.TAH),backgroundColor:G+'cc'}}]}},options:{{...opt,indexAxis:'y'}}}});}})();
(()=>{{const d=CT.idade||[];if(!d.length)return;new Chart(cID,{{type:'line',data:{{labels:d.map(x=>x.CORTE+'o'),datasets:[{{label:'TAH',data:d.map(x=>x.TAH),borderColor:O,backgroundColor:O+'22',fill:true,tension:.3}},{{label:'TCH',data:d.map(x=>x.TCH),borderColor:G,backgroundColor:'transparent',tension:.3,yAxisID:'y1'}}]}},options:{{...opt,scales:{{...opt.scales,y1:{{position:'right',ticks:{{color:G}},grid:{{display:false}}}}}}}}}});}})();
(()=>{{const d=CT.frente||[];if(!d.length)return;new Chart(cFR,{{type:'bar',data:{{labels:d.map(x=>x.GRP),datasets:[{{label:'Cana (t)',data:d.map(x=>x.CANA),backgroundColor:B+'cc',yAxisID:'y'}},{{label:'ATR',type:'line',data:d.map(x=>x.ATR),borderColor:O,yAxisID:'y1'}}]}},options:{{...opt,scales:{{x:{{ticks:{{color:M}},grid:{{color:'#1b2848'}}}},y:{{ticks:{{color:M}}}},y1:{{position:'right',ticks:{{color:O}},grid:{{display:false}}}}}}}}}});}})();
(()=>{{const d=CT.lag||[];if(!d.length)return;new Chart(cLAG,{{type:'bar',data:{{labels:d.map(x=>x.lag+'m'),datasets:[{{label:'correlacao r',data:d.map(x=>x.corr),backgroundColor:d.map(x=>Math.abs(x.corr)===Math.max(...d.map(y=>Math.abs(y.corr)))?C:M+'88')}}]}},options:opt}});}})();
(()=>{{const p=CT.proj;if(!p)return;new Chart(cPROJ,{{type:'bar',data:{{labels:['Realizado ate mes '+p.ultmes,'Projecao fim safra','Meta safra'],datasets:[{{label:'Toneladas',data:[p.real,p.final,p.meta],backgroundColor:[G+'cc',O+'cc',R+'88']}}]}},options:opt}});}})();
</script></body></html>"""
OUT.write_text(html,encoding="utf-8"); DOCS.mkdir(exist_ok=True); (DOCS/"UMOE_Inteligencia_Cruzada.html").write_text(html,encoding="utf-8")
print(f"OK -> {OUT} ({len(html)//1024} KB) | insights={len(ins)}")
