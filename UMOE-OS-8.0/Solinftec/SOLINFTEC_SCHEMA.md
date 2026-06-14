# SOLINFTEC — Schema de Exportação Esperado pelo CHI Engine
## UMOE OS 8.0 | Automação 6

O arquivo CSV exportado do Solinftec deve seguir este formato para ser processado pelo `chi-engine.py`.

## Colunas Obrigatórias

| Coluna | Tipo | Exemplo | Descrição |
|--------|------|---------|-----------|
| `data` | date | 2026-06-14 | Data do evento |
| `equipamento` | string | COLH-01 | ID ou nome do equipamento |
| `tipo_equipamento` | string | COLHEDORA | COLHEDORA / TRANSBORDO / CAMINHAO |
| `frente` | string | F01 | Código da frente (F01–F27) |
| `evento` | string | Hilo Travamento | Descrição textual do evento/parada |
| `categoria` | string | OPERACIONAL | OPERACIONAL / MANUTENCAO / CHUVA / INSUMO |
| `inicio` | datetime | 2026-06-14 06:15:00 | Início da parada |
| `fim` | datetime | 2026-06-14 06:43:00 | Fim da parada |
| `duracao_h` | float | 0.47 | Duração em horas decimais |
| `talhao` | string | FAZ-CONCORDIA-T14 | Talhão onde ocorreu (opcional) |

## Mapeamento de Causas-Raiz (chi-engine.py)

O engine classifica o campo `evento` nas seguintes causas-raiz:

| Causa-Raiz CHI | Palavras-chave no campo `evento` | Controlável |
|----------------|----------------------------------|-------------|
| Hilo Travamento | hilo, travamento, espera transbordo | ✅ Sim |
| T.Carregamento | carregamento, carga, fila pátio, pesagem | ✅ Sim |
| Pátio / Usina | patio, usina, fila balança, descarga | ✅ Sim |
| Manutenção Corretiva | corretiva, quebra, falha, pane, vazamento | ✅ Sim |
| Manutenção Preventiva | preventiva, lubrificação, troca filtro | ✅ Sim |
| Combustível / Insumo | combustivel, abastecimento, agua, sem insumo | ✅ Sim |
| Troca de Turno | turno, refeição, troca operador | ✅ Sim |
| Chuva / Clima | chuva, umidade, barro, solo molhado | ❌ Não |
| Outros Operacionais | demais eventos não classificados acima | ⚠️ Revisar |

## Como Exportar do Solinftec

1. Acesse o módulo **Relatórios → Paradas e Disponibilidade**
2. Filtre por: Data, Todas as Frentes, Tipo: Colhedoras + Transbordos
3. Exporte como `.csv` (separador ponto e vírgula, encoding UTF-8)
4. Salve em: `C:\Users\andrei.elastico\umoe-os\UMOE-OS-8.0\Solinftec\`
5. O agente detecta automaticamente e processa na Automação 6

## Frequência Recomendada

- Exportação diária às **08h30** (dados do dia anterior fechados)
- O boletim matinal das **09h00** incorpora o CHI do dia anterior automaticamente
