# DAX (negocio) — MANUT_OS_Transporte
Medidas: 0 | Colunas calculadas: 7 | Tabelas calculadas: 0 | Negocio: 7 | Auto date tables omitidas: 49


## COLUNAS CALCULADAS (7)

### Base O.S.Status Previsao
```dax
IF(ISBLANK('Base O.S'[Previsao de Saida]),"Aguardando Previsão",IF(('Base O.S'[Previsao de Saida]- NOW() ) < 0,"Atrasado","Dentro da Previsão"))
```
### Base O.S.Tempo Permanencia
```dax
DATEDIFF([HR_ENTRADA],NOW(),DAY)
```
### Base O.S.Indice
```dax
IF(AND([Tempo Permanencia] >= 0,'BASE O.S'[Tempo Permanencia] <= 1),"0-1 Dias",IF(AND('BASE O.S'[Tempo Permanencia]>1,'BASE O.S'[Tempo Permanencia] <=5 ),"2-5 Dias",IF(AND('BASE O.S'[Tempo Permanencia] >5,'BASE O.S'[Tempo Permanencia] <=10),"6-10 Dias",IF(AND('BASE O.S'[Tempo Permanencia] > 10,'BASE O.S'[Tempo Permanencia] <= 15),"11-15 Dias",IF(AND('BASE O.S'[Tempo Permanencia] > 15,'BASE O.S'[Tempo Permanencia] <= 20),"16-20 Dias",IF(AND('BASE O.S'[Tempo Permanencia] >15,'BASE O.S'[Tempo Permanencia] <= 25),"21-25 Dias",IF(AND('BASE O.S'[Tempo Permanencia] >25,'BASE O.S'[Tempo Permanencia] <=35),"26-35 Dias",IF(AND('BASE O.S'[Tempo Permanencia] >36,'BASE O.S'[Tempo Permanencia] <=60),"36-60 Dias","+61 Dias"))))))))
```
### Base O.S.Coluna
```dax
NOW() - 'Base O.S'[DT_ENTRADA]
```
### Base O.S.Tempo Horas
```dax
'Base O.S'[Coluna] * 24
```
### Base O.S.Posicao
```dax
IF(AND([Tempo Permanencia] >= 0,'BASE O.S'[Tempo Permanencia] <= 1),"1",IF(AND('BASE O.S'[Tempo Permanencia]>1,'BASE O.S'[Tempo Permanencia] <=5 ),"2",IF(AND('BASE O.S'[Tempo Permanencia] >5,'BASE O.S'[Tempo Permanencia] <=10),"3",IF(AND('BASE O.S'[Tempo Permanencia] > 10,'BASE O.S'[Tempo Permanencia] <= 15),"4",IF(AND('BASE O.S'[Tempo Permanencia] > 15,'BASE O.S'[Tempo Permanencia] <= 20),"5",IF(AND('BASE O.S'[Tempo Permanencia] >15,'BASE O.S'[Tempo Permanencia] <= 25),"6",IF(AND('BASE O.S'[Tempo Permanencia] >25,'BASE O.S'[Tempo Permanencia] <=35),"7",IF(AND('BASE O.S'[Tempo Permanencia] >36,'BASE O.S'[Tempo Permanencia] <=60),"8","9"))))))))
```
### Base O.S.Localização
```dax
RELATED('Tabela Fornecedores'[Município])&";"&RELATED('Tabela Fornecedores'[UF])
```