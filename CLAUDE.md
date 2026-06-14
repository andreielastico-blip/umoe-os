# CLAUDE.md — UMOE OS 8.0 | Plano Diretor Agrícola
## Contexto do Projeto
Empresa: UMOE Bioenergy | Diretor: Andrei Elastico | Presidente Prudente, SP
Setor: Sucroenergético | Safra ativa: 2026/27 | Meta moagem: 2.768.000 t
GitHub: andreielastico-blip/umoe-os | Último commit: 3dabe8c

## Estrutura de Pastas Principal
- SSoT (fonte única da verdade): UMOE-OS-8.0/99-SSoT/SSoT-UMOE-2026.md
- CHI Engine: UMOE-OS-8.0/01-AGENTE-AUTONOMO/chi-engine.py
- Base agrícola: UMOE-OS-8.0/Base-Agricola/Base_UMOE.xlsx
- Solinftec CSV diário: UMOE-OS-8.0/Solinftec/SOLINFTEC_[AAAAMMDD].csv
- Relatórios: UMOE-OS-8.0/Relatorios/
- Logs: logs/chi.log | logs/sync.log | logs/pipeline.log
- INBOX arquivos: C:\01 - UMOE\09 - IA\UMOE-INBOX\
- Sync script: C:\01 - UMOE\09 - IA\sync-umoe.ps1

## Regras Críticas — NUNCA VIOLAR
- UMOE-066: ATR SEMPRE ponderado pelas toneladas reais de cada período
- UMOE-067: Energia R$250/MWh é ESTIMATIVA — aguarda contrato ACR/spot
- NUNCA deletar arquivos — sempre mover para Arquivo/Safra-[ANO]/
- SEMPRE fazer git add + commit + push após atualizar a SSoT
- Git user: andreielastico-blip | email: 292870464+andreielastico-blip@users.noreply.github.com
- Encoding PowerShell: sem acentos em scripts .ps1

## Parâmetros CHI Engine
- CHI_POR_COLHEDORA: R$ 81,90/h
- CHI_FROTA_COMPLETA: R$ 1.638,00/h (20 colhedoras)
- SEM_VERDE: < R$ 2.000/dia | SEM_AMARELO: R$ 2.000–5.000 | SEM_VERMELHO: > R$ 5.000
- Causas controláveis: Hilo Travamento, T.Carregamento, Manutenção, Combustível, Turno, Pátio/Usina
- Causas NÃO controláveis: Chuva/Clima

## Parâmetros Financeiros
- Preço etanol: R$ 2,50/litro | Eficiência: 86,95 l/t cana
- Energia: R$ 250/MWh (ESTIMATIVA — UMOE-067) | Eficiência: 63,18 kWh/t
- WACC: 18,30% aa | TMA: 21,00% aa | Selic: 14,50% aa
- Preço ATR CONSECANA: R$ 1,03/kg
- Meta ATR safra 26/27: 138,66 kg/t | ATR real acumulado mai/26: 126,49 kg/t

## Indicadores Operacionais Atuais (mai/26)
- Moagem acumulada mar-mai: 606.418 t | Meta proporcional: 822.918 t | Gap: -216.500 t
- Gap receita estimado: -R$ 50,78 M (89% volume | 11% custo)
- CCT real: R$ 50,0/t vs orçado R$ 38,3/t (+R$ 11,7/t)
- CHI dia 13/06: R$ 18.129 total | R$ 7.786 controlável — VERMELHO
- Tratos Soca: único centro de custo abaixo do orçado (-R$ 126/ha)

## Frota e Estrutura de Frentes
- Total colhedoras: 20 | Total TT: 40
- Frentes 01-04: próprias (4 colhedoras + 8 TT cada) | Responsável: Flavio Faveri
- Frente 10: fornecedor | Responsável: Ricardo Lerosa
- Frente 27: fornecedor | Responsável: Fabiano Pontes
- Caminhões: 36 linha + 3 bate-volta | Carretas: 171 | Carga: 67 t/viagem

## Base Granular
- Base_UMOE.xlsx: 23.320 registros | 8 safras (19/20–26/27) | 218 fazendas
- Melhor TAH histórico: 18,45 t ATR/ha — Faz. Santa Helena (7 safras)
- Melhor variedade×ambiente: CTC9006 × Amb.E — TAH 15,43 t ATR/ha
- Pior variedade: CTC15 — TAH nunca passou de 7,6 em nenhuma safra
- Canavial 4C+ (renovação urgente): 15.173 ha | TCH 64 t/ha vs 99,6 t/ha no 1C

## Comandos Rápidos
- Pipeline completo: python UMOE-OS-8.0/01-AGENTE-AUTONOMO/chi-engine.py
- Sync GitHub: powershell "C:\01 - UMOE\09 - IA\sync-umoe.ps1"
- Verificar CHI: Get-Content logs/chi.log -Tail 10
- Validar SSoT: python ssot-validator.py (a criar)
- EBITDA: python ebitda-engine.py (a criar)

## Próximos Desenvolvimentos Prioritários
1. ebitda-engine.py — calcular EBITDA real com Opex acumulado
2. ssot-validator.py — validar integridade da SSoT antes de cada push
3. umoe-pipeline.py — pipeline end-to-end CSV→CHI→SSoT→Push
4. anomalia-detector.py — alertas vs histórico 16 safras
5. dashboard.html — gerado automaticamente da SSoT
