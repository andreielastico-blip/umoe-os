# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 | Pipeline Orquestrador Master
Executa na ordem correta e pusha para GitHub automaticamente.

Uso:
  python umoe-pipeline.py             # pipeline completo
  python umoe-pipeline.py --bi-only   # so gera o BI
  python umoe-pipeline.py --push-only # so faz git push
"""
import os, sys, json, subprocess, argparse, logging
from datetime import datetime
from pathlib import Path

ROOT     = Path(__file__).parent.parent.parent
LOG_FILE = ROOT / "logs" / "pipeline.log"
LOG_FILE.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("pipeline")

# ─── ETAPAS ──────────────────────────────────────────────────────────────────
ETAPAS = [
    {
        "nome": "CHI Engine",
        "script": ROOT / "UMOE-OS-8.0/01-AGENTE-AUTONOMO/chi-engine.py",
        "obrigatorio": False,
        "descricao": "Calcula CHI do dia (paradas controlaveis)"
    },
    {
        "nome": "Clima Engine",
        "script": ROOT / "UMOE-OS-8.0/01-AGENTE-AUTONOMO/clima-engine.py",
        "obrigatorio": False,
        "descricao": "Atualiza previsao climatica"
    },
    {
        "nome": "BI Enterprise",
        "script": ROOT / "UMOE-OS-8.0/01-AGENTE-AUTONOMO/umoe-bi-enterprise.py",
        "obrigatorio": True,
        "descricao": "Gera HTML BI completo com todos os dados"
    },
    {
        "nome": "Cockpit Executivo",
        "script": ROOT / "UMOE-OS-8.0/01-AGENTE-AUTONOMO/umoe-cockpit.py",
        "obrigatorio": False,
        "descricao": "Cockpit executivo (moagem/ATR/variedades/chuva/custos) dados reais PBI"
    },
    {
        "nome": "Moagem Panel",
        "script": ROOT / "UMOE-OS-8.0/01-AGENTE-AUTONOMO/moagem-panel-engine.py",
        "obrigatorio": True,
        "descricao": "Gera painel de moagem com BPC e reestimativa"
    },
]

def run_script(script_path, timeout=300):
    """Executa um script Python e retorna (ok, duration_s, output)."""
    t0 = datetime.now()
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace"
        )
        dur = (datetime.now() - t0).total_seconds()
        ok = result.returncode == 0
        out = (result.stdout + result.stderr).strip()[-2000:]
        return ok, dur, out
    except subprocess.TimeoutExpired:
        dur = (datetime.now() - t0).total_seconds()
        return False, dur, f"TIMEOUT apos {timeout}s"
    except Exception as e:
        dur = (datetime.now() - t0).total_seconds()
        return False, dur, str(e)

def git_push():
    """Adiciona todos os artefatos gerados e faz push."""
    try:
        # Arquivos a commitar
        targets = [
            "UMOE-OS-8.0/Relatorios/",
            "docs/",
            "UMOE-OS-8.0/01-AGENTE-AUTONOMO/",
            "config/",
            "logs/",
        ]
        now_str = datetime.now().strftime("%Y%m%d-%H%M")

        subprocess.run(["git", "add"] + targets, cwd=ROOT, check=True, capture_output=True)

        commit_msg = f"Pipeline auto {now_str} - BI atualizado"
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg,
             "--author", "andreielastico-blip <292870464+andreielastico-blip@users.noreply.github.com>"],
            cwd=ROOT, capture_output=True, text=True
        )

        if "nothing to commit" in result.stdout + result.stderr:
            log.info("Git: nada a commitar.")
            return True

        push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
        if push.returncode == 0:
            log.info(f"Git push OK: {commit_msg}")
            return True
        else:
            log.error(f"Git push falhou: {push.stderr}")
            return False
    except Exception as e:
        log.error(f"Git erro: {e}")
        return False

def salvar_status(resultados):
    """Salva status.json para monitoramento externo."""
    status_path = ROOT / "UMOE-OS-8.0/Relatorios/pipeline-status.json"
    status = {
        "ultima_execucao": datetime.now().isoformat(),
        "resultados": resultados,
        "sucesso_total": all(r["ok"] for r in resultados if r.get("obrigatorio"))
    }
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    log.info(f"Status salvo: {status_path}")

def main():
    parser = argparse.ArgumentParser(description="UMOE Pipeline Master")
    parser.add_argument("--bi-only",   action="store_true", help="Apenas gerar BI")
    parser.add_argument("--push-only", action="store_true", help="Apenas git push")
    parser.add_argument("--no-push",   action="store_true", help="Sem push")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info(f"  UMOE OS 8.0 | Pipeline Master | {datetime.now():%d/%m/%Y %H:%M}")
    log.info("=" * 60)

    if args.push_only:
        git_push()
        return

    resultados = []
    etapas = ETAPAS if not args.bi_only else [e for e in ETAPAS if e["obrigatorio"]]

    for etapa in etapas:
        script = etapa["script"]
        if not script.exists():
            log.warning(f"  [{etapa['nome']}] Script nao encontrado: {script}")
            resultados.append({"nome": etapa["nome"], "ok": False, "erro": "nao encontrado", "obrigatorio": etapa["obrigatorio"]})
            continue

        log.info(f"  [{etapa['nome']}] Iniciando: {etapa['descricao']}")
        ok, dur, out = run_script(script)
        status = "OK" if ok else "ERRO"
        log.info(f"  [{etapa['nome']}] {status} em {dur:.1f}s")
        if not ok:
            log.error(f"    Output: {out[-500:]}")

        resultados.append({
            "nome": etapa["nome"],
            "ok": ok,
            "duracao_s": round(dur, 1),
            "obrigatorio": etapa["obrigatorio"]
        })

        if not ok and etapa["obrigatorio"]:
            log.error(f"  Etapa obrigatoria falhou: {etapa['nome']} — abortando pipeline")
            break

    salvar_status(resultados)

    sucesso = all(r["ok"] for r in resultados if r.get("obrigatorio"))
    log.info(f"\n  Pipeline concluido: {'SUCESSO' if sucesso else 'COM ERROS'}")
    for r in resultados:
        icon = "OK" if r["ok"] else "XX"
        log.info(f"    [{icon}] {r['nome']} ({r.get('duracao_s','?')}s)")

    if not args.no_push and sucesso:
        log.info("\n  Fazendo git push...")
        git_push()
    elif not sucesso:
        log.warning("  Push cancelado — pipeline com erros obrigatorios")

    return 0 if sucesso else 1

if __name__ == "__main__":
    sys.exit(main())
