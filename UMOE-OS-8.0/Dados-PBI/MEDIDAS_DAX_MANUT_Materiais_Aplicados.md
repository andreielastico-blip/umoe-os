# DAX (negocio) — MANUT_Materiais_Aplicados
Medidas: 0 | Colunas calculadas: 5 | Tabelas calculadas: 0 | Negocio: 5 | Auto date tables omitidas: 70


## COLUNAS CALCULADAS (5)

### Materiais Aplicados.Data Aplicação
```dax
'Materiais Aplicados'[DT_APLICACAO]
```
### Materiais Aplicados.META DIA
```dax
80854
```
### f_atualizado.AGORA 2
```dax

FORMAT(DATE(YEAR([AGORA5]),MONTH([AGORA5]),DAY([AGORA5]))+TIME(HOUR([AGORA5]),0,0),"dd/mm/yy hh:mm")
```
### f_atualizado.AGORA5
```dax

[AGORA]+0.0034722222
```
### f_atualizado.agora0
```dax
DATE(YEAR([AGORA5]),MONTH([AGORA5]),DAY([AGORA5]))+TIME(HOUR([AGORA5]),0,0)
```