# UMOE OS 8.0 - Roteiro de Atualizacao Periodica V2
# Plano Diretor Agricola | Safra 2026/27
# Versao: 2.0 | 14/06/2026 | Com CHI Engine + Solinftec integrado

## ROTEIRO DIARIO - Todo dia util
Horario 06h00 | VOCE | Exportar CSV Solinftec > Solinftec\SOLINFTEC_[AAAAMMDD].csv
Horario 08h30 | AUTOMATICO | CHI Engine processa CSV > gera PDF + JSON
Horario 07h30 | COWORK | Monitor KPIs + boletim matinal
A cada 2h    | TASK | Sync GitHub automatico

Passos diarios (10 minutos):
1. CRITICO - Exportar CSV Solinftec do dia anterior - salvar em Solinftec\
2. IMPORTANTE - Verificar PDF CHI do dia anterior em Relatorios\
3. AUTOMATICO - CHI Engine gera umoe-chi-snapshot.json + UMOE_CHI_[DATA].pdf
4. AUTOMATICO - Cowork gera boletim KPIs em logs\monitor_diario.log
5. VERIFICAR - logs\chi.log ultima linha - CHI controlavel vermelho? Acionar frente
6. VERIFICAR - UMOE-INBOX\A-CLASSIFICAR\ - arquivos para classificar manualmente
Comando Cowork: /status

## ROTEIRO SEMANAL - Toda segunda-feira (30-40 minutos)
1. CRITICO - Conferir CHI da semana em logs\chi.log
2. CRITICO - Atualizar SSoT moagem: 99-SSoT\SSoT-UMOE-2026.md bloco REAL SAFRA 2026
3. CRITICO - Atualizar SSoT ATR ponderado UMOE-066
4. IMPORTANTE - Atualizar SSoT impurezas IM e IV
5. AUTOMATICO - Cowork gera Relatorios\UMOE_Relatorio_Semanal_[DATA].md
6. AUTOMATICO - Sync GitHub em logs\sync.log
7. MANUAL - Revisar relatorio e enviar a diretoria
8. ROTINA - Verificar skill c1-operacional.md - desatualizado?
Comando Cowork: Gere relatorio executivo semanal UMOE OS 8.0 com moagem vs meta,
ATR ponderado UMOE-066, CHI da semana, top 3 causas controlaveis e acoes prioritarias.

## ROTEIRO MENSAL - Dias 1 a 10 de cada mes (2-3 horas)
RECEBER E ORGANIZAR (dias 1-5):
1. CRITICO - PDF custos operacionais > UMOE-INBOX\ > Cowork move para Custos\
2. CRITICO - Relatorio CCT > UMOE-INBOX\ > Cowork move para CCT\
3. CRITICO - Fechamento qualidade > UMOE-INBOX\ > Cowork move para Fechamentos\
4. CRITICO - CSVs Solinftec do mes > Solinftec\ > CHI Engine processa automatico
5. IMPORTANTE - Nota fiscal energia > UMOE-INBOX\ > manual atualizar UMOE-067

ATUALIZAR SSoT (dias 5-8):
6. CRITICO - Bloco REAL SAFRA 2026: moagem real, dias efetivos, gap vs plano
7. CRITICO - Bloco QUALIDADE: ATR ponderado UMOE-066, IM, IV do mes
8. CRITICO - Bloco CUSTOS OPERACIONAIS: waterfall por centro de custo
9. CRITICO - Bloco DIGITAL TWIN: receita real acumulada + projecao revisada
10. CRITICO - Bloco DIAGNOSTICO: CHI acumulado do mes por causa-raiz
11. CRITICO - Bloco EBITDA: estimado com Opex real do mes

ATUALIZAR SKILLS (dias 8-10):
12. SKILL.md - parametros se mudaram
13. c1-operacional.md - DM real, eficiencia, moagem, CHI do mes
14. c2-manutencao.md - MTBF/MTTR, principais falhas do mes
15. c3-financeiro.md - preco ATR CONSECANA, parametros financeiros

ATUALIZAR COWORK (dia 10):
16. Revisar semaforos de KPIs se metas mudaram
17. Verificar logs\organizacao.log + logs\fechamentos.log
18. Confirmar CHI Engine: logs\chi.log - ultima entrada de hoje?

Push mensal:
cd C:\Users\andrei.elastico\umoe-os
git add .
git commit -m "SSoT - fechamento [MES]/[ANO] | CHI + custos + moagem atualizados"
git push origin main

Comando Cowork mensal:
Execute checklist mensal UMOE OS 8.0:
1. Liste arquivos novos em Custos\, CCT\ e Fechamentos\
2. Mostre CHI acumulado do mes por causa-raiz (logs\chi.log)
3. Calcule gap de moagem acumulado vs plano
4. Calcule EBITDA com receita real e Opex disponivel
5. Mostre top 3 desvios criticos com semaforo

## ROTEIRO TRIMESTRAL - Jan/Abr/Jul/Out dia 15 (1 dia completo)
BLOCO 1 - CHI Engine e telemetria (1 hora):
1. CRITICO - Revisar CHI_POR_COLHEDORA em chi-engine.py linha 32
2. CRITICO - Consolidar CHI do trimestre em logs\chi.log
3. CRITICO - Gravar analise CHI trimestral na SSoT
4. IMPORTANTE - Revisar SOLINFTEC_SCHEMA.md - colunas mudaram?

BLOCO 2 - Base granular e fitotecnica (3 horas):
5. CRITICO - Atualizar Base_UMOE.xlsx em Base-Agricola\
6. CRITICO - Reprocessar 12 visoes V1-V12 com Claude + Base_UMOE.xlsx
7. CRITICO - Gravar visoes V1-V12 atualizadas na SSoT
8. IMPORTANTE - Revisar ranking variedades por TAH atualizado

BLOCO 3 - Digital Twin (1 hora):
9. CRITICO - Revisar projecao final safra com dados reais do trimestre
10. CRITICO - Revisar WACC, TMA, preco etanol, energia UMOE-067
11. IMPORTANTE - Recalcular cenarios pessimista/base/otimista

BLOCO 4 - Skills (1 hora):
12. SKILL.md - benchmarks, metas, parametros gerais
13. c0-ceo.md - contexto estrategico da safra
14. c1-operacional.md - KPIs reais do trimestre + CHI
15. c2-manutencao.md - DM real, MTBF/MTTR, causas CHI
16. c3-financeiro.md - CONSECANA, precos, parametros economicos
17. c4-governanca.md - estrutura organizacional, responsaveis
18. c5-ia.md - automacoes ativas, CHI Engine, Solinftec

BLOCO 5 - Cowork (30 minutos):
19. Atualizar semaforos KPIs com base no trimestre
20. Testar CHI Engine: python chi-engine.py
21. Testar 5 automacoes: /status no Cowork
22. Verificar Task Scheduler: Get-ScheduledTaskInfo -TaskName UMOE-OS-Sync

## ROTEIRO SEMESTRAL - Janeiro e Julho semana 1 (5 dias)
DIA 1 manha - SSoT estrutural:
1. Ler SSoT completa - identificar dados desatualizados
2. Unificar blocos duplicados
3. Atualizar ativo biologico - nova estimativa TCH por faixa de corte
4. Atualizar historico safras - adicionar ao historico de 16 safras
5. Revisar regras UMOE-061, 066, 067

DIA 1 tarde - CHI Engine:
6. CRITICO - Atualizar CHI_POR_COLHEDORA chi-engine.py linha 32
7. CRITICO - Atualizar CHI_FROTA_COMPLETA chi-engine.py linha 33
8. CRITICO - Revisar CAUSAS_CONTROLAVEIS chi-engine.py linha 40
9. CRITICO - Atualizar SEM_VERDE e SEM_AMARELO chi-engine.py linhas 43-44
10. IMPORTANTE - Atualizar SOLINFTEC_SCHEMA.md colunas/causas novas

DIA 2 - Plano da safra:
11. Revisar meta de moagem - ajustar se necessario
12. Revisar estrutura de frentes - colhedoras, TT, responsaveis
13. Revisar plano de variedades por ambiente/fazenda
14. Revisar plano renovacao 4C+ - ha renovados vs pendentes

DIA 3 - Skills profunda:
15. SKILL.md - revisao completa com aprendizados do semestre
16. Todas as references\ - atualizar com dados reais
17. Benchmarks PECEGE/DATAGRO/CTC - atualizar se publicados

DIA 4 - Sistema de automacao:
18. sync-umoe.ps1 - testar e corrigir
19. umoe-rotina-diaria.ps1 - revisar e atualizar
20. umoe-email-diario.ps1 - revisar destinatarios
21. Task Scheduler - verificar todas as tasks
22. chi-engine.py - python chi-engine.py com CSV real
23. Cowork - revisao completa das 5 automacoes e semaforos

DIA 5 - Diretoria:
24. Relatorio semestral PPTX com balanco completo
25. EBITDA, VPL e TIR com dados reais
26. CHI semestral: top causas + R$ recuperavel
27. Documentar licoes aprendidas na SSoT

## ROTEIRO ANUAL

NOVEMBRO - Encerramento de safra (2 semanas):
Semana 1:
1. Fechamento final da safra em Fechamentos\
2. Consolidar CHI anual em logs\chi.log
3. Atualizar historico 16 safras na SSoT
4. Atualizar Base_UMOE.xlsx em Base-Agricola\
5. Reprocessar V1-V12 com dados completos da safra
6. Calcular EBITDA final real: receita real - Opex real
7. Ranking final de variedades por TAH
8. Atualizar plano renovacao 4C+: ha renovados vs pendentes
Semana 2:
9. Relatorio anual PPTX para Conselho
10. Analise CHI anual: top 5 causas + R$ total perdido
11. Top 10 licoes aprendidas na SSoT
12. Arquivar safra: criar Arquivo\Safra-2026\ e mover arquivos

FEVEREIRO - Abertura nova safra (1 semana):
1. CRITICO - Criar SSoT-UMOE-2027.md em 99-SSoT\
2. CRITICO - Carregar plano de moagem mes a mes
3. CRITICO - Atualizar metas: moagem, ATR, TCH, EBITDA
4. CRITICO - Atualizar ativo biologico
5. CRITICO - Revisar estrutura de frentes
6. CRITICO - Recalibrar CHI Engine: novo CHI_POR_COLHEDORA
7. CRITICO - Atualizar todas as Skills para safra 27/28
8. CRITICO - Recalibrar Digital Twin: novos precos etanol/energia/ATR
9. CRITICO - Atualizar Cowork: novas metas nos semaforos
10. IMPORTANTE - Plano variedades 2027 por ambiente/fazenda
11. IMPORTANTE - Plano renovacao 4C+ para entressafra

## RESUMO EXECUTIVO

| Cadencia    | Pastas principais                    | Skills   | CHI Engine        | Tempo     |
|-------------|--------------------------------------|----------|-------------------|-----------|
| Diario      | Solinftec\                           | Nao      | Automatico        | 10 min    |
| Semanal     | 99-SSoT\ + Relatorios\               | c1       | Automatico        | 40 min    |
| Mensal      | Custos\ + CCT\ + Fechamentos\ + SSoT | c1 + c3  | Consolidar        | 2-3h      |
| Trimestral  | Base-Agricola\ + 99-SSoT\ + logs\    | Todas    | Revisar params    | 1 dia     |
| Semestral   | SSoT completa + 01-AGENTE-AUTONOMO\  | Todas    | Atualizar CHI     | 5 dias    |
| Anual       | Tudo + nova SSoT                     | Todas    | Recalibrar frota  | 3 semanas |

## ONDE CADA ARQUIVO ENTRA

CSV Solinftec diario       > Solinftec\SOLINFTEC_[AAAAMMDD].csv > CHI Engine automatico
PDF custo operacional      > UMOE-INBOX\ > Cowork move para Custos\
XLSX/CSV CCT               > UMOE-INBOX\ > Cowork move para CCT\
PDF fechamento mensal      > UMOE-INBOX\ > Cowork move para Fechamentos\
Base_UMOE.xlsx atualizado  > Base-Agricola\ diretamente > manual reprocessar V1-V12
Contrato energia UMOE-067  > 99-SSoT\ > manual atualizar Digital Twin
Preco ATR CONSECANA        > skills\references\c3-financeiro.md > manual
Relatorio PECEGE/DATAGRO   > skills\references\ > manual atualizar benchmarks
Plano moagem nova safra    > 99-SSoT\ > manual criar nova SSoT

## PARAMETROS CHI ENGINE - QUANDO ATUALIZAR

CHI_POR_COLHEDORA R$/h    | chi-engine.py linha 32  | Semestral ou se custo/hora mudar
CHI_FROTA_COMPLETA R$/h   | chi-engine.py linha 33  | Semestral ou se numero colhedoras mudar
CHI_CAMINHAO_PATIO fator  | chi-engine.py linha 34  | Anual
SEM_VERDE R$/dia          | chi-engine.py linha 43  | Anual
SEM_AMARELO R$/dia        | chi-engine.py linha 44  | Anual
CAUSAS_CONTROLAVEIS set   | chi-engine.py linha 40  | Trimestral ou nova causa identificada
Schema Solinftec          | SOLINFTEC_SCHEMA.md     | Se Solinftec mudar formato de export

---
UMOE OS 8.0 | Versao Definitiva V2 com CHI Engine | 14/06/2026
GitHub: andreielastico-blip/umoe-os
