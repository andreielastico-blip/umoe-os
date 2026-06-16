# -*- coding: utf-8 -*-
"""
Clima Engine UMOE OS 8.0
Le sempre o arquivo de precipitacao mais atualizado e integra na SSoT.
Fonte: C:\01 - UMOE\03 - Financeiro\Planilhas\1 - Indice Pluviometrico UMOE.xlsx
"""

import json
import os
import re
import subprocess
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).resolve().parents[2]
SSOT_PATH    = ROOT / "UMOE-OS-8.0" / "99-SSoT" / "SSoT-UMOE-2026.md"
JSON_OUT     = ROOT / "UMOE-OS-8.0" / "99-SSoT" / "umoe-clima-snapshot.json"
LOG_PATH     = ROOT / "logs" / "clima.log"

XLSX_CHUVA   = Path(r"C:\01 - UMOE\03 - Financeiro\Planilhas\1 - Indice Pluviometrico UMOE.xlsx")

# Ordem canonica dos meses em portugues
ORDEM_MESES = ["Janeiro","Fevereiro","Marco","Abril","Maio","Junho",
               "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

MES_NORM = {
    "Marco": "Marco", "Março": "Marco",
    "Janeiro": "Janeiro", "Fevereiro": "Fevereiro",
    "Abril": "Abril", "Maio": "Maio", "Junho": "Junho",
    "Julho": "Julho", "Agosto": "Agosto", "Setembro": "Setembro",
    "Outubro": "Outubro", "Novembro": "Novembro", "Dezembro": "Dezembro",
}

# Safra comeca em marco
MESES_SAFRA = ["Marco","Abril","Maio","Junho","Julho","Agosto",
               "Setembro","Outubro","Novembro"]

# Threshold de alerta (mm/mes) — acima = risco operacional alto
THRESHOLD_CRITICO  = 200
THRESHOLD_ATENCAO  = 100

# Impacto financeiro por mm excedente (referencia: SSoT 2026 = R$35,91M / ~850mm acima threshold safra)
IMPACTO_MM_M = 0.042   # R$ M por mm acima do threshold no mes

# ── Logging ────────────────────────────────────────────────────────────────
LOG_PATH.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CLIMA] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ── Leitura do Excel (sempre a versao mais atualizada) ────────────────────

def ler_precipitacao() -> pd.DataFrame:
    if not XLSX_CHUVA.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {XLSX_CHUVA}")

    mod = datetime.fromtimestamp(XLSX_CHUVA.stat().st_mtime)
    log.info(f"Lendo: {XLSX_CHUVA.name} | Modificado: {mod.strftime('%d/%m/%Y %H:%M')}")

    xl  = pd.ExcelFile(str(XLSX_CHUVA))
    df  = pd.read_excel(xl, sheet_name="HISTORICO", header=None)

    dados = df.iloc[2:, [0, 1, 3, 4, 5, 6]].copy()
    dados.columns = ["ANO2", "DATA", "MM", "MES_RAW", "ANO", "DEC"]
    dados = dados.dropna(subset=["ANO"])
    dados["ANO"] = dados["ANO"].astype(int)
    dados["MM"]  = pd.to_numeric(dados["MM"], errors="coerce").fillna(0)
    dados["MES"] = dados["MES_RAW"].map(MES_NORM).fillna(dados["MES_RAW"].astype(str))

    log.info(f"Registros carregados: {len(dados):,} | Anos: {dados['ANO'].min()}-{dados['ANO'].max()}")
    return dados


# ── Calculos ───────────────────────────────────────────────────────────────

def calcular(dados: pd.DataFrame) -> dict:
    ano_atual = datetime.now().year

    # Total anual por ano
    anual = dados.groupby("ANO")["MM"].sum().to_dict()

    # Mensal por ano (apenas anos recentes relevantes)
    mensal_pivot = (
        dados.groupby(["ANO", "MES"])["MM"]
        .sum()
        .unstack(fill_value=0)
        .astype(float)
    )

    # Media historica por mes (sum anual antes de tirar media — evita media de leituras diarias)
    media_hist = (
        dados.groupby(["ANO", "MES"])["MM"]
        .sum()
        .groupby("MES")
        .mean()
        .to_dict()
    )

    # 2026 mensal
    dados_2026 = dados[dados["ANO"] == ano_atual]
    mensal_2026 = dados_2026.groupby("MES")["MM"].sum().to_dict()
    # Normaliza nomes
    mensal_2026 = {MES_NORM.get(k, k): v for k, v in mensal_2026.items()}

    # Decadas 2026
    dec_2026 = (
        dados_2026.groupby(["MES", "DEC"])["MM"]
        .sum()
        .reset_index()
    )

    # Comparativo 2024 e 2025
    mensal_2024 = {MES_NORM.get(k, k): v for k, v in
                   dados[dados["ANO"] == ano_atual - 2].groupby("MES")["MM"].sum().to_dict().items()}
    mensal_2025 = {MES_NORM.get(k, k): v for k, v in
                   dados[dados["ANO"] == ano_atual - 1].groupby("MES")["MM"].sum().to_dict().items()}

    # Alertas safra 2026
    alertas = []
    total_safra_2026 = 0
    impacto_estimado_M = 0.0
    for mes in MESES_SAFRA:
        mm = mensal_2026.get(mes, 0)
        if mm == 0:
            continue
        total_safra_2026 += mm
        hist = media_hist.get(mes, 0)
        var_pct = ((mm / hist) - 1) * 100 if hist > 0 else 0
        if mm >= THRESHOLD_CRITICO:
            status = "CRITICO"
            excedente = mm - THRESHOLD_CRITICO
            impacto_estimado_M += excedente * IMPACTO_MM_M
            alertas.append({
                "mes": mes, "mm": mm, "media_hist": round(hist, 1),
                "var_vs_hist_pct": round(var_pct, 1), "status": status,
                "excedente_mm": round(excedente, 1),
                "impacto_estimado_M": round(excedente * IMPACTO_MM_M, 2),
            })
        elif mm >= THRESHOLD_ATENCAO:
            status = "ATENCAO"
            alertas.append({
                "mes": mes, "mm": mm, "media_hist": round(hist, 1),
                "var_vs_hist_pct": round(var_pct, 1), "status": status,
            })

    # Meses restantes da safra (sem leitura ainda = projecao media hist)
    meses_sem_dados = [m for m in MESES_SAFRA if m not in mensal_2026 or mensal_2026[m] == 0]
    projecao_restante_mm = sum(media_hist.get(m, 0) for m in meses_sem_dados)

    return {
        "timestamp": datetime.now().isoformat(),
        "safra": "2026/27",
        "arquivo_fonte": str(XLSX_CHUVA),
        "arquivo_modificado": datetime.fromtimestamp(XLSX_CHUVA.stat().st_mtime).isoformat(),
        "historico_anual_mm": {str(k): round(v, 1) for k, v in sorted(anual.items())},
        "media_historica_mm": {k: round(v, 1) for k, v in media_hist.items()},
        "precipitacao_2024_mm": {k: round(v, 1) for k, v in mensal_2024.items()},
        "precipitacao_2025_mm": {k: round(v, 1) for k, v in mensal_2025.items()},
        "precipitacao_2026_mm": {k: round(v, 1) for k, v in mensal_2026.items()},
        "total_anual_2026_acum_mm": round(sum(mensal_2026.values()), 1),
        "safra_2026": {
            "total_safra_acum_mm": round(total_safra_2026, 1),
            "meses_com_dados": sorted(mensal_2026.keys()),
            "meses_sem_dados": meses_sem_dados,
            "projecao_restante_mm_media_hist": round(projecao_restante_mm, 1),
            "projecao_safra_completa_mm": round(total_safra_2026 + projecao_restante_mm, 1),
            "alertas": alertas,
            "impacto_estimado_total_M": round(impacto_estimado_M, 2),
            "nota_impacto": (
                "Estimativa: R$ {:.3f}M/mm acima de {}mm/mes. "
                "Base: desvio SSoT 2026 (R$35,91M / 850mm excedente). "
                "Validar com Controladoria."
            ).format(IMPACTO_MM_M, THRESHOLD_CRITICO),
        },
        "parametros": {
            "threshold_critico_mm": THRESHOLD_CRITICO,
            "threshold_atencao_mm": THRESHOLD_ATENCAO,
            "impacto_R_M_por_mm": IMPACTO_MM_M,
        },
    }


# ── Atualizar SSoT ─────────────────────────────────────────────────────────

BLOCO_CLIMA_HEADER = "## CLIMA ENGINE — PRECIPITACAO REAL 2026"

def atualizar_ssot(ssot_texto: str, resultado: dict) -> str:
    ts       = resultado["timestamp"][:16].replace("T", " ")
    mod      = resultado["arquivo_modificado"][:16].replace("T", " ")
    s26      = resultado["safra_2026"]
    mm26     = resultado["precipitacao_2026_mm"]
    mm25     = resultado["precipitacao_2025_mm"]
    mm24     = resultado["precipitacao_2024_mm"]
    med      = resultado["media_historica_mm"]
    alertas  = s26["alertas"]
    anual    = resultado["historico_anual_mm"]

    # Tabela mensal
    linhas_tabela = []
    for mes in ORDEM_MESES:
        v26 = mm26.get(mes, "-")
        v25 = mm25.get(mes, "-")
        v24 = mm24.get(mes, "-")
        vh  = round(med.get(mes, 0), 0) if med.get(mes) else "-"
        safra_flag = " (*)" if mes in MESES_SAFRA else ""
        alerta_flag = ""
        for a in alertas:
            if a["mes"] == mes:
                alerta_flag = " [CRITICO]" if a["status"] == "CRITICO" else " [ATENCAO]"
        v26_str = f"{v26:.0f}{alerta_flag}" if isinstance(v26, (int, float)) else str(v26)
        v25_str = f"{v25:.0f}" if isinstance(v25, (int, float)) else str(v25)
        v24_str = f"{v24:.0f}" if isinstance(v24, (int, float)) else str(v24)
        vh_str  = f"{vh:.0f}"  if isinstance(vh,  (int, float)) else str(vh)
        linhas_tabela.append(
            f"| {mes}{safra_flag} | {v26_str} | {v25_str} | {v24_str} | {vh_str} |"
        )

    tabela = "\n".join(linhas_tabela)

    # Historico anual resumido
    hist_linhas = " | ".join([f"{a}: {v:.0f}mm" for a, v in sorted(anual.items())])

    # Alertas
    if alertas:
        alert_txt = "\n".join([
            f"> **{a['mes']}**: {a['mm']:.0f}mm ({a['var_vs_hist_pct']:+.0f}% vs hist. {a['media_hist']:.0f}mm) — {a['status']}"
            + (f" | Impacto est. R$ {a['impacto_estimado_M']:.2f}M" if "impacto_estimado_M" in a else "")
            for a in alertas
        ])
    else:
        alert_txt = "> Nenhum mes com precipitacao critica na safra 2026."

    bloco = f"""
---

{BLOCO_CLIMA_HEADER}
### Fonte: 1 - Indice Pluviometrico UMOE.xlsx | Atualizado: {mod} | Engine: {ts}
### (*) = mes de safra ativa | CRITICO > {THRESHOLD_CRITICO}mm | ATENCAO > {THRESHOLD_ATENCAO}mm

| Mes | 2026 (mm) | 2025 (mm) | 2024 (mm) | Media Hist. |
|-----|-----------|-----------|-----------|-------------|
{tabela}
| **TOTAL** | **{s26['total_safra_acum_mm']:.0f}** | -- | -- | -- |

### Alertas Safra 2026
{alert_txt}

### Impacto Financeiro Estimado (chuva)
- Total acumulado safra 2026: **{s26['total_safra_acum_mm']:.0f}mm** ({', '.join(s26['meses_com_dados'])})
- Impacto estimado acumulado: **R$ {s26['impacto_estimado_total_M']:.2f} M**
- Meses restantes sem dados: {', '.join(s26['meses_sem_dados']) if s26['meses_sem_dados'] else 'nenhum'}
- Projecao safra completa (media hist.): {s26['projecao_safra_completa_mm']:.0f}mm

### Historico Anual (mm)
{hist_linhas}

"""

    padrao = re.compile(
        r'\n---\n\n' + re.escape(BLOCO_CLIMA_HEADER) + r'.*?(?=\n---\n|\Z)',
        re.DOTALL
    )
    ssot_texto = padrao.sub("", ssot_texto)
    return ssot_texto.rstrip() + "\n" + bloco


# ── Git ────────────────────────────────────────────────────────────────────

def git_commit_push(mensagem: str):
    try:
        os.chdir(ROOT)
        subprocess.run(["git", "add",
                        str(SSOT_PATH.relative_to(ROOT)),
                        str(JSON_OUT.relative_to(ROOT)),
                        "CLAUDE.md"], check=True)
        subprocess.run(["git", "commit", "-m", mensagem], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        log.info("Git: commit e push realizados com sucesso.")
    except subprocess.CalledProcessError as e:
        log.error(f"Git falhou: {e}")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("CLIMA ENGINE UMOE OS 8.0 — INICIANDO")
    log.info("=" * 60)

    # 1. Ler Excel (sempre o mais atualizado)
    dados = ler_precipitacao()

    # 2. Calcular
    resultado = calcular(dados)

    # 3. Salvar JSON
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    log.info(f"JSON salvo: {JSON_OUT}")

    # 4. Atualizar SSoT
    ssot_texto = SSOT_PATH.read_text(encoding="utf-8")
    ssot_atualizado = atualizar_ssot(ssot_texto, resultado)
    SSOT_PATH.write_text(ssot_atualizado, encoding="utf-8")
    log.info(f"SSoT atualizada: {SSOT_PATH}")

    # 5. Resumo no console
    s26     = resultado["safra_2026"]
    mm26    = resultado["precipitacao_2026_mm"]
    alertas = s26["alertas"]

    print("\n" + "=" * 60)
    print("  CLIMA ENGINE - PRECIPITACAO 2026")
    print("=" * 60)
    print(f"  Fonte: {Path(resultado['arquivo_fonte']).name}")
    print(f"  Modificado: {resultado['arquivo_modificado'][:16]}")
    print("-" * 60)
    print(f"  {'Mes':<12} {'2026':>8} {'2025':>8} {'Media':>8}  Status")
    print("-" * 60)
    med = resultado["media_historica_mm"]
    mm25 = resultado["precipitacao_2025_mm"]
    for mes in ORDEM_MESES:
        v26 = mm26.get(mes)
        if v26 is None:
            continue
        v25 = mm25.get(mes, 0)
        vh  = med.get(mes, 0)
        flag = ""
        for a in alertas:
            if a["mes"] == mes:
                flag = f"  << {a['status']}"
        print(f"  {mes:<12} {v26:>7.0f}  {v25:>7.0f}  {vh:>7.0f}{flag}")
    print("-" * 60)
    print(f"  Total safra acum.: {s26['total_safra_acum_mm']:.0f}mm")
    print(f"  Impacto estimado:  R$ {s26['impacto_estimado_total_M']:.2f} M")
    if alertas:
        print(f"  Alertas CRITICO:   {sum(1 for a in alertas if a['status']=='CRITICO')} mes(es)")
    print("=" * 60)

    # 6. Git
    ts_commit = datetime.now().strftime("%Y%m%d-%H%M")
    n_criticos = sum(1 for a in alertas if a["status"] == "CRITICO")
    git_commit_push(
        f"Clima Engine {ts_commit} | Maio 2026: {mm26.get('Maio',0):.0f}mm | "
        f"{n_criticos} mes(es) CRITICO | Impacto R${s26['impacto_estimado_total_M']:.1f}M"
    )

    log.info("CLIMA ENGINE — CONCLUIDO")


if __name__ == "__main__":
    main()
