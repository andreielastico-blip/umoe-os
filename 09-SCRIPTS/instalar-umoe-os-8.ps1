# ============================================================
# UMOE OS 8.0 — INSTALADOR AUTOMÁTICO
# Copia toda a estrutura para o repositório GitHub
# Execute como Administrador
# ============================================================

$REPO = "C:\Users\andrei.elastico\umoe-os"
$OS8  = "$REPO\UMOE-OS-8.0"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  UMOE OS 8.0 — INSTALANDO..." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

# Cria estrutura de pastas
$pastas = @(
    "00-NUCLEO",
    "01-AGENTE-AUTONOMO",
    "02-DIGITAL-TWIN-FINANCEIRO",
    "03-MEMORIA-CORPORATIVA",
    "04-CICLO-REUNIOES",
    "05-MATURITY-INDEX",
    "06-COPILOTOS",
    "07-EBITDA-LEAKAGE",
    "08-DATA-QUALITY",
    "09-SENSOR-HEALTH",
    "10-DECISION-INTELLIGENCE",
    "99-SSoT"
)

foreach ($pasta in $pastas) {
    $caminho = "$OS8\$pasta"
    New-Item -ItemType Directory -Path $caminho -Force | Out-Null
    New-Item -ItemType File -Path "$caminho\.gitkeep" -Force | Out-Null
}

Write-Host "  Estrutura de pastas criada" -ForegroundColor Cyan

# Cria arquivo de versão
$versao = @"
# UMOE OS 8.0 — Autonomous Enterprise Layer
Versão: 8.0.0
Data de instalação: $(Get-Date -Format "dd/MM/yyyy HH:mm")
Repositório: andreielastico-blip/umoe-os
Instalado por: Andrei Elastico

## Módulos ativos
- NÓ 01: Agente Autônomo de Safra
- NÓ 02: Digital Twin Financeiro Vivo
- NÓ 03: Memória Corporativa Ativa
- NÓ 04: Ciclo de Reuniões Automatizado
- NÓ 05: UMOE Operational Maturity Index
- NÓ 06: Copilotos Executivos V2
- NÓ 07: EBITDA Leakage Engine V2
- NÓ 08: Data Quality Gate
- NÓ 09: Sensor Health Validator
- NÓ 10: Decision Intelligence Engine
- NÓ 99: Single Source of Truth

## Status de automações
- Sync GitHub: a cada 2h (UMOE-OS-Sync)
- Rotina diária: 12h00 (UMOE-OS-Rotina-Diaria)
- E-mail diário: 12h00 (UMOE-OS-Email-Diario)
"@

$versao | Out-File -FilePath "$OS8\VERSION.md" -Encoding UTF8

# Cria SSoT template
$ssot = @"
# SINGLE SOURCE OF TRUTH — UMOE OS 8.0
## Parâmetros Oficiais da Safra 2026
## CONFIDENCIAL — USO INTERNO

---

## METAS OFICIAIS

| KPI | Meta | Unidade | Fonte |
|-----|------|---------|-------|
| Moagem total | 3.000.000 | toneladas | Plano aprovado |
| TCH médio | [preencher] | t/ha | Planejamento agrícola |
| ATR médio | [preencher] | kg/t | Curva de maturação |
| DM frota | 90 | % | Meta conselho |
| Eficiência op. | 60 | % | Meta operacional |
| DMT | [preencher] | km | Planejamento logístico |

---

## PARÂMETROS FINANCEIROS

| Parâmetro | Valor | Vigência |
|-----------|-------|----------|
| Preço ATR | R$ [preencher]/kg | [data] |
| WACC UMOE | [preencher]% | [data] |
| TMA referência | [preencher]% | [data] |
| Câmbio USD/BRL | R$ [preencher] | atualizar diariamente |

---

## ESTRUTURA DE FRENTES

| Frente | Tipo | Colhedoras | Transbordos | Responsável |
|--------|------|-----------|------------|-------------|
| Frente 01 | Própria | [N] | [N] | [nome] |
| Frente 02 | Própria | [N] | [N] | [nome] |
| Frente 03 | Própria | [N] | [N] | [nome] |
| Frente 04 | Própria | [N] | [N] | [nome] |
| Frente 10 | Fornecedor | [N] | [N] | [nome] |
| Frente 27 | Fornecedor | [N] | [N] | [nome] |

---

## CONTATOS ESTRATÉGICOS

| Nome | Cargo | Área | Nível de Alerta |
|------|-------|------|-----------------|
| Andrei Elastico | Diretor | Agrícola | Todos os níveis |
| Wagner Magalhães | Gerente | Operações | Nível 2+ |
| [Outros contatos] | | | |

---

## GLOSSÁRIO OFICIAL DE KPIs

| KPI | Fórmula | Unidade | Meta |
|-----|---------|---------|------|
| TCH | Toneladas colhidas / Hectares | t/ha | [meta] |
| ATR | Pol corrigida + AR × fator | kg/t | [meta] |
| TAH | TCH × ATR / 1000 | t ATR/ha | [meta] |
| DM% | Horas disponíveis / Horas calendário | % | 90% |
| EF% | Horas produtivas / Horas disponíveis | % | 60% |
| MTBF | Horas entre falhas | horas | [meta] |
| MTTR | Horas para reparar | horas | [meta] |
| DMT | Distância média de transporte | km | [meta] |

---

Última atualização: $(Get-Date -Format "dd/MM/yyyy HH:mm")
Responsável pela SSoT: Andrei Elastico
"@

$ssot | Out-File -FilePath "$OS8\99-SSoT\SSoT-UMOE-2026.md" -Encoding UTF8

# Commit e push
Set-Location $REPO
git add . 2>&1 | Out-Null
git commit -m "instala UMOE OS 8.0 — Autonomous Enterprise Layer" 2>&1 | Out-Null
git push origin main 2>&1 | Out-Null

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  UMOE OS 8.0 INSTALADO COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Localização: $OS8" -ForegroundColor Cyan
Write-Host "  GitHub: andreielastico-blip/umoe-os/UMOE-OS-8.0/" -ForegroundColor Cyan
Write-Host "  Próximo passo: preencher SSoT com dados oficiais" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "  1. Preencher $OS8\99-SSoT\SSoT-UMOE-2026.md" -ForegroundColor White
Write-Host "     com as metas e parâmetros oficiais da safra" -ForegroundColor White
Write-Host ""
Write-Host "  2. Copiar os arquivos .md dos módulos" -ForegroundColor White
Write-Host "     para as pastas correspondentes" -ForegroundColor White
Write-Host ""
Write-Host "  3. Executar /cockpit no Claude com os dados reais" -ForegroundColor White
Write-Host "     para ativar o Digital Twin Financeiro" -ForegroundColor White
Write-Host ""
