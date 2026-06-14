#!/usr/bin/env python3
"""
UMOE OS 8.0 — Automação 6: CHI Engine (Custo da Hora Inoperante)
Lê CSV Solinftec, calcula CHI por causa-raiz e gera JSON + PDF accountability.

Uso: python chi-engine.py [--csv CAMINHO_CSV] [--data YYYYMMDD]
"""

import csv, json, os, sys, argparse, logging
from datetime import datetime, date
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent  # UMOE-OS-8.0/
SOLINFTEC_DIR = BASE_DIR / "Solinftec"
LOG_DIR = BASE_DIR.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / "chi.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("chi-engine")

# ── PARÂMETROS CHI (SSoT) ────────────────────────────────────────────────────
CHI_POR_COLHEDORA   = 81.90   # R$/h/colhedora
CHI_FROTA_COMPLETA  = 1638.00 # R$/h (20 colhedoras)
CHI_CAMINHAO_PATIO  = 0.15    # fator multiplicador para evento de pátio/usina

SEM_VERDE    = 2_000   # < 2.000 → verde
SEM_AMARELO  = 5_000   # 2.000–5.000 → amarelo; > 5.000 → vermelho

CAUSAS_CONTROLAVEIS = {
    "Hilo Travamento", "T.Carregamento", "Manutenção Corretiva",
    "Manutenção Preventiva", "Combustível / Insumo", "Troca de Turno",
    "Pátio / Usina",
}


def parse_float(v):
    try: return float(str(v).replace(",", ".").strip())
    except: return 0.0


def semaforo(val):
    if val < SEM_VERDE:   return "🟢 VERDE"
    if val < SEM_AMARELO: return "🟡 AMARELO"
    return "🔴 VERMELHO"


def find_csv(data_str: str | None) -> Path | None:
    """Localiza CSV Solinftec para a data. Se data=None, usa o mais recente."""
    if data_str:
        p = SOLINFTEC_DIR / f"SOLINFTEC_{data_str}.csv"
        return p if p.exists() else None
    csvs = sorted(SOLINFTEC_DIR.glob("SOLINFTEC_*.csv"), reverse=True)
    return csvs[0] if csvs else None


def processar_csv(csv_path: Path) -> dict:
    """Lê CSV semicolon e agrega paradas por causa-raiz."""
    causa_horas  = defaultdict(float)
    causa_equip  = defaultdict(set)
    causa_tipo   = defaultdict(set)
    total_eventos = 0

    with open(csv_path, encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            dur  = parse_float(row.get("duracao_h", 0))
            tipo = row.get("tipo_equipamento", "").strip().upper()
            causa= row.get("causa_raiz", "").strip()
            equip= row.get("equipamento", "").strip()
            if dur <= 0 or not causa:
                continue
            # Pátio/Usina aplica fator caminhão
            fator = CHI_CAMINHAO_PATIO if ("CAMINHAO" in tipo and causa == "T.Carregamento") else 1.0
            causa_horas[causa]  += dur * fator
            causa_equip[causa].add(equip)
            causa_tipo[causa].add(tipo)
            total_eventos += 1

    return {
        "causa_horas": dict(causa_horas),
        "causa_equip": {k: list(v) for k, v in causa_equip.items()},
        "total_eventos": total_eventos,
    }


def calcular_chi(causa_horas: dict) -> list:
    """Converte horas paradas em CHI (R$) por causa."""
    resultado = []
    for causa, horas in sorted(causa_horas.items(), key=lambda x: -x[1]):
        chi_val = horas * CHI_POR_COLHEDORA
        controlavel = causa in CAUSAS_CONTROLAVEIS
        resultado.append({
            "causa_raiz": causa,
            "horas_paradas": round(horas, 3),
            "chi_reais": round(chi_val, 2),
            "controlavel": controlavel,
            "semaforo": semaforo(chi_val),
        })
    return resultado


def gerar_json(data_ref: str, csv_path: Path, causas: list, total_eventos: int) -> Path:
    """Salva umoe-chi-snapshot.json na pasta 99-SSoT."""
    total_chi = sum(c["chi_reais"] for c in causas)
    total_ctrl = sum(c["chi_reais"] for c in causas if c["controlavel"])
    snap = {
        "meta": "UMOE OS 8.0 — CHI Snapshot",
        "data_ref": data_ref,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fonte_csv": str(csv_path.name),
        "total_eventos": total_eventos,
        "chi_total_reais": round(total_chi, 2),
        "chi_controlavel_reais": round(total_ctrl, 2),
        "chi_incontrolavel_reais": round(total_chi - total_ctrl, 2),
        "semaforo_geral": semaforo(total_chi),
        "causas": causas,
    }
    out = BASE_DIR / "99-SSoT" / "umoe-chi-snapshot.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=4)
    log.info(f"JSON salvo: {out}")
    return out


def gerar_pdf(data_ref: str, causas: list, snap: dict) -> Path | None:
    """Gera PDF accountability CHI. Requer reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        log.warning("reportlab não instalado — PDF não gerado")
        return None

    out = BASE_DIR.parent / "Plano Diretor Agricola" if (BASE_DIR.parent / "Plano Diretor Agricola").exists() \
          else BASE_DIR / "Relatorios"
    out.mkdir(exist_ok=True)
    pdf_path = out / f"UMOE_CHI_{data_ref}.pdf"

    C_NAVY = colors.HexColor('#1a2744')
    C_TEAL = colors.HexColor('#0f6e6e')
    C_GREEN= colors.HexColor('#27ae60')
    C_YELLOW=colors.HexColor('#f39c12')
    C_RED  = colors.HexColor('#e74c3c')
    C_LGRAY= colors.HexColor('#f7f7f7')
    C_MGRAY= colors.HexColor('#cccccc')

    def PS(nm,sz=8,bold=False,color=colors.black,align=TA_LEFT):
        return ParagraphStyle(nm,fontName='Helvetica-Bold' if bold else 'Helvetica',
                              fontSize=sz,textColor=color,alignment=align,leading=sz+3)

    H1=PS('H1',12,True,C_NAVY,TA_CENTER)
    H2=PS('H2',9,True,C_TEAL)
    SM=PS('SM',7,False,colors.gray,TA_CENTER)
    BD=PS('BD',7.5)

    W=17*cm
    elems=[]

    # Header
    hdr=Table([[Paragraph('UMOE BIOENERGY',PS('',10,True,colors.white)),
                Paragraph(f'CHI — Custo da Hora Inoperante  |  {data_ref}',PS('',8,False,colors.HexColor('#aadddd'),align=TA_CENTER))]],
              colWidths=[7*cm,10*cm])
    hdr.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),C_NAVY),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(0,-1),10),]))
    elems+=[hdr,Spacer(1,6)]
    elems.append(Paragraph('PAINEL DE ACCOUNTABILITY — HORAS INOPERANTES POR CAUSA-RAIZ',H1))
    elems.append(Spacer(1,4))

    # KPIs
    kd=[['CHI Total','CHI Controlável','CHI Incontrolável','Semáforo Geral'],
        [f"R$ {snap['chi_total_reais']:,.2f}",
         f"R$ {snap['chi_controlavel_reais']:,.2f}",
         f"R$ {snap['chi_incontrolavel_reais']:,.2f}",
         snap['semaforo_geral']]]
    kt=Table(kd,colWidths=[4*cm,4*cm,4.5*cm,4.5*cm])
    kt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),C_NAVY),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),8),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('BACKGROUND',(0,1),(-1,1),C_LGRAY),('GRID',(0,0),(-1,-1),0.3,C_MGRAY),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),]))
    elems+=[kt,Spacer(1,8)]

    # Tabela causas
    elems.append(Paragraph('Detalhamento por Causa-Raiz',H2))
    td=[['Causa-Raiz','Horas Paradas','CHI (R$)','Controlável','Semáforo']]
    ex=[]
    for i,c in enumerate(causas,1):
        td.append([c['causa_raiz'],f"{c['horas_paradas']:.2f} h",
                   f"R$ {c['chi_reais']:,.2f}",
                   '✅ Sim' if c['controlavel'] else '❌ Não',
                   c['semaforo']])
        cor=(C_RED if '🔴' in c['semaforo'] else (C_YELLOW if '🟡' in c['semaforo'] else C_GREEN))
        ex+=[ ('BACKGROUND',(4,i),(4,i),cor),('TEXTCOLOR',(4,i),(4,i),colors.white),
              ('FONTNAME',(4,i),(4,i),'Helvetica-Bold')]
    base=[('BACKGROUND',(0,0),(-1,0),C_NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
          ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7.5),
          ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_LGRAY,colors.white]),
          ('GRID',(0,0),(-1,-1),0.3,C_MGRAY),('ALIGN',(1,0),(-1,-1),'CENTER'),
          ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]
    t=Table(td,colWidths=[5*cm,3*cm,3.5*cm,2.8*cm,2.7*cm])
    t.setStyle(TableStyle(base+ex))
    elems+=[t,Spacer(1,8)]

    # Regra CHI
    elems.append(HRFlowable(width=W,thickness=1,color=C_MGRAY))
    elems.append(Spacer(1,4))
    elems.append(Paragraph(
        f'<b>CHI base:</b> R${CHI_POR_COLHEDORA}/h/colhedora  |  '
        f'<b>CHI frota:</b> R${CHI_FROTA_COMPLETA}/h (20 colhedoras)  |  '
        f'<b>Ref. ATR:</b> 138,66 kg/t  |  <b>CONSECANA:</b> R$1,03/kg',SM))
    elems.append(Paragraph(
        f'Semáforo: 🟢 < R$2.000  |  🟡 R$2.000–5.000  |  🔴 > R$5.000  |  UMOE OS 8.0 | {datetime.now().strftime("%d/%m/%Y %H:%M")}',SM))

    doc=SimpleDocTemplate(str(pdf_path),pagesize=A4,
        leftMargin=1.5*cm,rightMargin=1.5*cm,topMargin=1.5*cm,bottomMargin=1.5*cm)
    doc.build(elems)
    log.info(f"PDF salvo: {pdf_path}")
    return pdf_path


def main():
    parser = argparse.ArgumentParser(description="UMOE OS 8.0 — CHI Engine")
    parser.add_argument("--csv",  help="Caminho explícito do CSV Solinftec")
    parser.add_argument("--data", help="Data YYYYMMDD (padrão: mais recente)")
    args = parser.parse_args()

    log.info("=== CHI Engine iniciado ===")

    # 1. Localizar CSV
    if args.csv:
        csv_path = Path(args.csv)
    else:
        data_str = args.data or None
        csv_path = find_csv(data_str)

    if not csv_path or not csv_path.exists():
        msg = f"CSV Solinftec não encontrado em {SOLINFTEC_DIR}. Aguardando exportação."
        log.warning(msg)
        print(f"[CHI] ⚠️  {msg}")
        sys.exit(0)

    data_ref = args.data or csv_path.stem.replace("SOLINFTEC_", "")
    log.info(f"CSV: {csv_path}")

    # 2. Processar
    resultado = processar_csv(csv_path)
    causas = calcular_chi(resultado["causa_horas"])

    total_chi = sum(c["chi_reais"] for c in causas)
    log.info(f"CHI total: R$ {total_chi:,.2f} | Causas: {len(causas)} | Eventos: {resultado['total_eventos']}")

    # 3. JSON
    json_path = gerar_json(data_ref, csv_path, causas, resultado["total_eventos"])
    print(f"[CHI] ✅ JSON: {json_path}")

    # 4. Carregar snapshot para PDF
    with open(json_path, encoding="utf-8") as f:
        snap = json.load(f)

    # 5. PDF
    pdf_path = gerar_pdf(data_ref, causas, snap)
    if pdf_path:
        print(f"[CHI] ✅ PDF: {pdf_path}")

    # 6. Console summary
    print(f"\n{'='*60}")
    print(f"  UMOE OS 8.0 | CHI Engine | Data: {data_ref}")
    print(f"  CHI Total:       R$ {total_chi:,.2f}")
    print(f"  Semáforo geral:  {semaforo(total_chi)}")
    print(f"  Top causa:       {causas[0]['causa_raiz']} (R$ {causas[0]['chi_reais']:,.2f})")
    print(f"{'='*60}")
    log.info("=== CHI Engine encerrado ===")


if __name__ == "__main__":
    main()
