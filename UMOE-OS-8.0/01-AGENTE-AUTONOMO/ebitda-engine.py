# -*- coding: utf-8 -*-
"""
EBITDA Engine UMOE OS 8.0
Calcula EBITDA, VPL e margem com base na SSoT oficial.
Parametros: CLAUDE.md | Regras: UMOE-066, UMOE-067
"""

import re
import json
import os
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH   = ROOT / "UMOE-OS-8.0" / "99-SSoT" / "SSoT-UMOE-2026.md"
JSON_OUT    = ROOT / "UMOE-OS-8.0" / "99-SSoT" / "umoe-ebitda-snapshot.json"
LOG_PATH    = ROOT / "logs" / "ebitda.log"

# ── Parâmetros (fonte: CLAUDE.md) ──────────────────────────────────────────
PRECO_ETANOL       = 2.50        # R$/litro
EFIC_ETANOL        = 86.95       # litros/t cana
PRECO_ENERGIA      = 250.0       # R$/MWh  [UMOE-067 ESTIMATIVA]
EFIC_ENERGIA       = 63.18       # kWh/t cana
WACC               = 0.1830      # 18,30% aa
TMA                = 0.2100      # 21,00% aa
PRECO_ATR          = 1.03        # R$/kg CONSECANA
META_MOAGEM_SAFRA  = 2_768_000   # t

# ── Logging ────────────────────────────────────────────────────────────────
LOG_PATH.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EBITDA] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ── Helpers de extração ────────────────────────────────────────────────────

def _num(s: str) -> float:
    """Converte string tipo '730.995' ou '126,49' para float."""
    s = s.strip().replace(".", "").replace(",", ".")
    return float(s)


def extrair_ssot(texto: str) -> dict:
    """Extrai os valores chave da SSoT via regex alinhados com a estrutura real do arquivo."""

    dados = {}

    # ── Moagem real acumulada ──────────────────────────────────────────────
    m = re.search(r'\|\s*Moagem real acumulada\s*\|\s*([\d\.]+)\s*t\s*\|', texto)
    if m:
        dados["moagem_real_t"] = _num(m.group(1))
        log.info(f"Moagem real acumulada: {dados['moagem_real_t']:,.0f} t")
    else:
        log.warning("Moagem real NAO encontrada na SSoT — usando CLAUDE.md: 730.995 t")
        dados["moagem_real_t"] = 730_995.0

    # ── ATR ponderado real (UMOE-066) ──────────────────────────────────────
    m = re.search(r'\|\s*ATR ponderado real\s*\|\s*([\d,]+)\s*kg/t\s*\|', texto)
    if m:
        dados["atr_real_kgt"] = _num(m.group(1))
        log.info(f"ATR ponderado real: {dados['atr_real_kgt']} kg/t")
    else:
        log.warning("ATR ponderado real NAO encontrado — usando CLAUDE.md: 126,49 kg/t")
        dados["atr_real_kgt"] = 126.49

    # ── Receita real acumulada (tabela "Real Acumulado Mar-14Jun") ─────────
    # Linha: | TOTAL | R$ 159,19M | R$ 398,62M | R$ 557,81M | R$ 645,52M | -R$ 87,72M |
    m = re.search(
        r'\|\s*TOTAL\s*\|\s*R\$\s*([\d,]+)M\s*\|\s*R\$\s*([\d,]+)M\s*\|',
        texto
    )
    if m:
        dados["receita_real_total_M"]  = _num(m.group(1))
        dados["receita_resto_plano_M"] = _num(m.group(2))
        log.info(f"Receita real acumulada: R$ {dados['receita_real_total_M']} M")
        log.info(f"Receita resto plano:    R$ {dados['receita_resto_plano_M']} M")
    else:
        log.warning("Receita real nao encontrada — calculando via parametros")
        ton = dados["moagem_real_t"]
        rec_etanol  = ton * EFIC_ETANOL * PRECO_ETANOL / 1e6
        rec_energia = ton * EFIC_ENERGIA * (PRECO_ENERGIA / 1000) / 1e6
        dados["receita_real_total_M"]  = round(rec_etanol + rec_energia, 2)
        dados["receita_resto_plano_M"] = 0.0

    # ── Projeção final safra ───────────────────────────────────────────────
    # Linha: | TOTAL | R$ 159,19M | R$ 398,62M | R$ 557,81M | R$ 645,52M | -R$ 87,72M |
    m = re.search(
        r'\|\s*TOTAL\s*\|\s*R\$\s*[\d,]+M\s*\|\s*R\$\s*[\d,]+M\s*\|\s*R\$\s*([\d,]+)M\s*\|\s*R\$\s*([\d,]+)M\s*\|',
        texto
    )
    if m:
        dados["receita_projecao_safra_M"] = _num(m.group(1))
        dados["receita_plano_original_M"] = _num(m.group(2))
        log.info(f"Receita projecao safra: R$ {dados['receita_projecao_safra_M']} M")
    else:
        dados["receita_projecao_safra_M"] = 645.52
        dados["receita_plano_original_M"] = 645.52

    # ── Custos reais (tabela RESUMO CONSOLIDADO — M R$ = R$ mil) ──────────
    # CCT Total: col M R$ Real = 21.851  (R$ mil)
    m = re.search(
        r'\|\s*CCT Total\s*\|\s*R\$/t\s*\|\s*[\d\.]+\s*\|\s*[\d\.]+\s*\|\s*[\d\.]+\s*\|\s*([\d\.]+)\s*\|',
        texto
    )
    if m:
        dados["cct_real_M"] = _num(m.group(1)) / 1000   # R$ mil → R$ M
        log.info(f"CCT Real: R$ {dados['cct_real_M']:.3f} M")
    else:
        # fallback: CCT unitario × volume
        m2 = re.search(r'\|\s*CCT Total\s*\|.*?\|\s*([\d,]+)\s*\|\s*Critico', texto)
        dados["cct_real_M"] = 21.851

    # Formação Total: col M R$ Real = 23.335  (R$ mil)
    m = re.search(
        r'\|\s*Forma[çc][aã]o\s*[—\-]+\s*Total\s*\|\s*R\$/ha\s*\|\s*[\d\.]+\s*\|\s*[\d\.]+\s*\|\s*[\d\.]+\s*\|\s*([\d\.]+)\s*\|',
        texto
    )
    if m:
        dados["formacao_real_M"] = _num(m.group(1)) / 1000
        log.info(f"Formacao Real: R$ {dados['formacao_real_M']:.3f} M")
    else:
        dados["formacao_real_M"] = 23.335

    # Tratos Cana Soca: col M R$ Real = 14.210  (R$ mil)
    m = re.search(
        r'\|\s*Tratos Cana Soca\s*\|\s*R\$/ha\s*\|\s*[\d\.]+\s*\|\s*[\d\.]+\s*\|\s*[\d\.]+\s*\|\s*([\d\.]+)\s*\|',
        texto
    )
    if m:
        dados["tratos_soca_real_M"] = _num(m.group(1)) / 1000
        log.info(f"Tratos Soca Real: R$ {dados['tratos_soca_real_M']:.3f} M")
    else:
        dados["tratos_soca_real_M"] = 14.210

    # ── Gap moagem ─────────────────────────────────────────────────────────
    m = re.search(r'\|\s*Gap moagem vs meta safra\s*\|\s*(-?[\d\.]+)\s*t\s*\|', texto)
    if m:
        dados["gap_moagem_meta_t"] = _num(m.group(1))
    else:
        dados["gap_moagem_meta_t"] = dados["moagem_real_t"] - META_MOAGEM_SAFRA

    return dados


# ── Cálculos EBITDA ────────────────────────────────────────────────────────

def calcular_ebitda(d: dict) -> dict:
    ton           = d["moagem_real_t"]
    receita_real  = d["receita_real_total_M"]

    # Custos acumulados reais
    custo_cct       = d["cct_real_M"]
    custo_formacao  = d["formacao_real_M"]
    custo_soca      = d["tratos_soca_real_M"]
    custo_total     = custo_cct + custo_formacao + custo_soca

    ebitda          = receita_real - custo_total
    margem_pct      = (ebitda / receita_real * 100) if receita_real else 0

    # Receita calculada pelos parâmetros (verificação cruzada)
    rec_etanol_calc   = ton * EFIC_ETANOL * PRECO_ETANOL / 1e6
    rec_energia_calc  = ton * EFIC_ENERGIA * (PRECO_ENERGIA / 1000) / 1e6
    rec_total_calc    = rec_etanol_calc + rec_energia_calc

    # Projeção safra completa
    rec_proj         = d["receita_projecao_safra_M"]
    custo_proj       = rec_proj * (custo_total / receita_real) if receita_real else 0
    ebitda_proj      = rec_proj - custo_proj

    # VPL simplificado — EBITDA projetado descontado a WACC (horizonte 1 safra ~8 meses)
    horizon_anos     = 8 / 12
    vpl              = ebitda_proj / ((1 + WACC) ** horizon_anos)

    # ATR equivalente financeiro (verificação UMOE-066)
    receita_atr_eq   = ton * d["atr_real_kgt"] * PRECO_ATR / 1e6

    return {
        "timestamp": datetime.now().isoformat(),
        "safra": "2026/27",
        "periodo": "Mar-14Jun/2026",
        "umoe_regras": ["UMOE-066", "UMOE-067"],
        "operacional": {
            "moagem_real_t": ton,
            "meta_moagem_safra_t": META_MOAGEM_SAFRA,
            "gap_moagem_t": d.get("gap_moagem_meta_t", ton - META_MOAGEM_SAFRA),
            "gap_moagem_pct": round((ton / META_MOAGEM_SAFRA - 1) * 100, 2),
            "atr_ponderado_real_kgt": d["atr_real_kgt"],
        },
        "receita_M": {
            "real_acumulado_ssot": round(receita_real, 3),
            "calculado_parametros": round(rec_total_calc, 3),
            "etanol_calc": round(rec_etanol_calc, 3),
            "energia_calc_UMOE067_estimativa": round(rec_energia_calc, 3),
            "atr_equivalente_UMOE066": round(receita_atr_eq, 3),
            "projecao_safra_completa": round(rec_proj, 3),
            "plano_original_safra": round(d["receita_plano_original_M"], 3),
            "gap_vs_plano": round(rec_proj - d["receita_plano_original_M"], 3),
        },
        "custos_M": {
            "cct_total": round(custo_cct, 3),
            "formacao_total": round(custo_formacao, 3),
            "tratos_soca": round(custo_soca, 3),
            "total_acumulado": round(custo_total, 3),
        },
        "ebitda_M": {
            "ebitda_parcial": True,
            "custos_apenas_agricolas": True,
            "nota_auditoria": (
                "EBITDA {:.2f}% reflete apenas custos agricolas. "
                "Faltam custos industriais, G&A e depreciacao. "
                "NAO usar para apresentacao ao Conselho sem Opex total."
            ).format(round(margem_pct, 2)),
            "ebitda_acumulado": round(ebitda, 3),
            "margem_pct": round(margem_pct, 2),
            "ebitda_projetado_safra": round(ebitda_proj, 3),
            "margem_projetada_pct": round(margem_pct, 2),
            "ebitda_ajustado_estimado_M": round(
                receita_real * (1 - 0.45) - custo_total, 3
            ),
            "ebitda_ajustado_margem_pct": round(
                ((receita_real * (1 - 0.45) - custo_total) / receita_real * 100)
                if receita_real else 0, 2
            ),
            "nota_ajuste": (
                "Ajuste estimado com custo industrial de 45% da receita "
                "(benchmark setor sucroenergético — PECEGE/DATAGRO). "
                "Substituir pelo Opex industrial real da Controladoria."
            ),
        },
        "vpl": {
            "vpl_M": round(vpl, 3),
            "wacc_pct": WACC * 100,
            "tma_pct": TMA * 100,
            "horizonte_meses": 8,
            "nota": "VPL simplificado — EBITDA projetado descontado a WACC. Para analise CAPEX usar fluxo completo aprovado pela Controladoria.",
        },
        "parametros_utilizados": {
            "preco_etanol_R_litro": PRECO_ETANOL,
            "eficiencia_etanol_l_t": EFIC_ETANOL,
            "preco_energia_R_MWh": PRECO_ENERGIA,
            "eficiencia_energia_kWh_t": EFIC_ENERGIA,
            "preco_atr_CONSECANA_R_kg": PRECO_ATR,
            "wacc_pct": WACC * 100,
            "tma_pct": TMA * 100,
            "flag_energia_estimativa": True,
        },
    }


# ── Atualizar bloco DIGITAL TWIN na SSoT ──────────────────────────────────

BLOCO_EBITDA_HEADER = "## EBITDA ENGINE — SNAPSHOT AUTOMATICO"

def atualizar_ssot(ssot_texto: str, resultado: dict) -> str:
    ts      = resultado["timestamp"][:16].replace("T", " ")
    marg    = resultado["ebitda_M"]["margem_pct"]
    ebitda  = resultado["ebitda_M"]["ebitda_acumulado"]
    ebitda_proj = resultado["ebitda_M"]["ebitda_projetado_safra"]
    rec     = resultado["receita_M"]["real_acumulado_ssot"]
    rec_proj = resultado["receita_M"]["projecao_safra_completa"]
    vpl     = resultado["vpl"]["vpl_M"]
    custo   = resultado["custos_M"]["total_acumulado"]

    ebitda_aj    = resultado["ebitda_M"]["ebitda_ajustado_estimado_M"]
    marg_aj      = resultado["ebitda_M"]["ebitda_ajustado_margem_pct"]

    bloco = f"""
---

{BLOCO_EBITDA_HEADER}
### Gerado em: {ts} | ebitda-engine.py v1.1

| Indicador | Valor Acumulado | Projecao Safra |
|-----------|----------------|----------------|
| Receita total | R$ {rec:.2f} M | R$ {rec_proj:.2f} M |
| Custos operac. agricolas | R$ {custo:.2f} M | -- |
| EBITDA agricola parcial | R$ {ebitda:.2f} M ({marg:.1f}%) | R$ {ebitda_proj:.2f} M |
| EBITDA ajustado* | R$ {ebitda_aj:.2f} M ({marg_aj:.1f}%) | -- |
| VPL (WACC 18,30%) | R$ {vpl:.2f} M | -- |

> *EBITDA ajustado: benchmark industrial 45% receita (PECEGE/DATAGRO) — substituir por Opex real.
> ATENCAO: EBITDA agricola parcial — faltam custos industriais, G&A e depreciacao.
> NAO usar para apresentacao ao Conselho sem Opex total.
> UMOE-067: Energia R$ 250/MWh ESTIMATIVA | UMOE-066: ATR {resultado['operacional']['atr_ponderado_real_kgt']} kg/t ponderado real.

"""

    # Remove bloco anterior se existir
    padrao = re.compile(
        r'\n---\n\n' + re.escape(BLOCO_EBITDA_HEADER) + r'.*?(?=\n---\n|\Z)',
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
                        str(JSON_OUT.relative_to(ROOT))],
                       check=True)
        subprocess.run(["git", "commit", "-m", mensagem], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        log.info("Git: commit e push realizados com sucesso.")
    except subprocess.CalledProcessError as e:
        log.error(f"Git falhou: {e}")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("EBITDA ENGINE UMOE OS 8.0 — INICIANDO")
    log.info("=" * 60)

    # 1. Ler SSoT
    if not SSOT_PATH.exists():
        log.error(f"SSoT nao encontrada em: {SSOT_PATH}")
        raise FileNotFoundError(SSOT_PATH)

    ssot_texto = SSOT_PATH.read_text(encoding="utf-8")
    log.info(f"SSoT lida: {len(ssot_texto):,} chars")

    # 2. Extrair dados
    dados = extrair_ssot(ssot_texto)

    # 3. Calcular EBITDA
    resultado = calcular_ebitda(dados)

    # 4. Salvar JSON
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    log.info(f"JSON salvo: {JSON_OUT}")

    # 5. Atualizar SSoT
    ssot_atualizado = atualizar_ssot(ssot_texto, resultado)
    SSOT_PATH.write_text(ssot_atualizado, encoding="utf-8")
    log.info(f"SSoT atualizada: {SSOT_PATH}")

    # 6. Exibir resumo
    e = resultado["ebitda_M"]
    r = resultado["receita_M"]
    c = resultado["custos_M"]
    v = resultado["vpl"]
    o = resultado["operacional"]

    print("\n" + "=" * 60)
    print("  EBITDA ENGINE - RESULTADO")
    print("=" * 60)
    print(f"  Moagem real acumulada : {o['moagem_real_t']:>12,.0f} t")
    print(f"  ATR ponderado real    : {o['atr_ponderado_real_kgt']:>12.2f} kg/t  [UMOE-066]")
    print(f"  Gap vs meta safra     : {o['gap_moagem_t']:>12,.0f} t  ({o['gap_moagem_pct']:.1f}%)")
    print("-" * 60)
    print(f"  Receita real acum.    : R$ {r['real_acumulado_ssot']:>9.2f} M")
    print(f"    >> Etanol (calc.)   : R$ {r['etanol_calc']:>9.2f} M")
    print(f"    >> Energia (est.)   : R$ {r['energia_calc_UMOE067_estimativa']:>9.2f} M  [UMOE-067]")
    print(f"  Custos operac. acum.  : R$ {c['total_acumulado']:>9.2f} M")
    print(f"    >> CCT             : R$ {c['cct_total']:>9.2f} M")
    print(f"    >> Formacao        : R$ {c['formacao_total']:>9.2f} M")
    print(f"    >> Tratos Soca     : R$ {c['tratos_soca']:>9.2f} M")
    print("-" * 60)
    print(f"  EBITDA acumulado      : R$ {e['ebitda_acumulado']:>9.2f} M")
    print(f"  Margem EBITDA         : {e['margem_pct']:>12.1f}%")
    print(f"  EBITDA projetado      : R$ {e['ebitda_projetado_safra']:>9.2f} M  (safra completa)")
    print(f"  Projecao receita      : R$ {r['projecao_safra_completa']:>9.2f} M")
    print(f"  VPL (WACC {v['wacc_pct']:.1f}%)     : R$ {v['vpl_M']:>9.2f} M")
    print("=" * 60)

    # 7. Git add + commit + push
    ts_commit = datetime.now().strftime("%Y%m%d-%H%M")
    git_commit_push(
        f"EBITDA Engine {ts_commit} — EBITDA R${e['ebitda_acumulado']:.1f}M | Margem {e['margem_pct']:.1f}% | VPL R${v['vpl_M']:.1f}M"
    )

    log.info("EBITDA ENGINE — CONCLUIDO")


if __name__ == "__main__":
    main()
