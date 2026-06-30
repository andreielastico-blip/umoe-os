# DAX (negocio) — MANUT_umoe_dataset
Medidas: 157 | Colunas calculadas: 79 | Tabelas calculadas: 6 | Negocio: 242 | Auto date tables omitidas: 0


## MEDIDAS (157)

### medidas.Disponibilidade (%)
```dax
VAR HORAS_DISPONIVEIS =
    SUMX(
        ADDCOLUMNS(
            d_data_hora,
            "HORAS_DISP",
            CALCULATE(DISTINCTCOUNT(d_equipamentos[CD_EQUIPTO]))
        ),
        [HORAS_DISP]
    )
VAR HORAS =
    SUMX(
        ADDCOLUMNS(
            d_data_hora,
            "HORASP",
            CALCULATE(
                DISTINCTCOUNT(f_manfro[CD_EQUIPTO]),
                FILTER(f_manfro,
                    [HORA_INICIAL]<[DATA_HORA] && [HORA_INICIAL]>0 && [HORA_FINAL]>[DATA_HORA] && NOT [ORIGEM_OS] IN {"E"} && [STATUS] IN {"Andamento","Encerrada"}
                ),
                FILTER(d_criterio_disponibilidade, [Considerar]="S")
            )
        ),
        [HORASP]
    )
VAR HORAS_INICIAL =
    SUMX(
        ADDCOLUMNS(
            d_data_hora,
            "HORASP",
            CALCULATE(
                DISTINCTCOUNT(f_manfro[CD_EQUIPTO]) - SUM(f_manfro[DESCONTO_INICIAL]),
                FILTER(f_manfro,
                    [HORA_INICIAL]=[DATA_HORA] && [HORA_INICIAL]>0 && [HORA_FINAL]>[DATA_HORA] && NOT [ORIGEM_OS] IN {"E"} && [STATUS] IN {"Andamento","Encerrada"}
                ),
                FILTER(d_criterio_disponibilidade, [Considerar]="S")
            )
        ),
        [HORASP]
    )
VAR HORAS_FINAL =
    SUMX(
        ADDCOLUMNS(
            d_data_hora,
            "HORASP",
            CALCULATE(
                SUM(f_manfro[ACRESCIMO_FINAL]),
                FILTER(f_manfro,
                    [HORA_INICIAL]<[DATA_HORA] && [HORA_INICIAL]>0 && [HORA_FINAL]=[DATA_HORA] && NOT [ORIGEM_OS] IN {"E"} && [STATUS] IN {"Andamento","Encerrada"}
                ),
                FILTER(d_criterio_disponibilidade, [Considerar]="S")
            )
        ),
        [HORASP]
    )
VAR HORAS_ENTRE =
    SUMX(
        ADDCOLUMNS(
            d_data_hora,
            "HORASP",
            CALCULATE(
                SUMX(f_manfro, [ACRESCIMO_FINAL]-[DESCONTO_INICIAL]),
                FILTER(f_manfro,
                    [HORA_INICIAL]=[DATA_HORA] && [HORA_FINAL]=[DATA_HORA] && NOT [ORIGEM_OS] IN {"E"} && [STATUS] IN {"Andamento","Encerrada"}
                ),
                FILTER(d_criterio_disponibilidade, [Considerar]="S")
            )
        ),
        [HORASP]
    )
RETURN
AVERAGEX(
    d_data_hora,
    1-
    DIVIDE(
        HORAS+HORAS_INICIAL+HORAS_FINAL+HORAS_ENTRE,
        HORAS_DISPONIVEIS
    )
)
```
### medidas.Disponibilidade Média (%)
```dax

// VAR vMedia =
// CALCULATE(
//     AVERAGEX(
//         ADDCOLUMNS(d_data_hora
//             ,"DISPONIBILIDADE"
//             ,[Disponibilidade (%)]
//         )
//         ,[DISPONIBILIDADE]
//     )
//     ,USERELATIONSHIP(d_data_hora[FECHAMENTO],d_calendar[DATA])
//     ,FILTER(d_data_hora
//         ,[FILTRO_ANTES_AGORA]=1
//     )
// )
// RETURN
// COALESCE(
//     [Disponibilidade Semana Ajuste]
//     ,IF(vMedia>=0,vMedia)
// )
CALCULATE(
    IF(
        --HASONEFILTER(d_data_hora[HORA]) || HASONEFILTER(d_data_hora[HORA_FECHA]) || HASONEFILTER(d_calendar[FILTRO_TEXTO]) || 
        SELECTEDVALUE(d_calendar[DATA]) < CALCULATE(MAX(d_calendar[DATA]),ALLSELECTED(d_calendar))-1 && (HASONEFILTER(d_data_hora[HORA]) || HASONEFILTER(d_data_hora[HORA_FECHA])) = FALSE()
        ,CALCULATE(
            AVERAGEX(d_disponibilidade_eqp_data, MAX([DISP],0))
            ,FILTER(d_calendar
                ,[DATA]<=TODAY()
            )
        )
        ,[Disponibilidade Hora (%)]
    )
)
```
### medidas.Disponibilidade Média Conjunto (%)
```dax

CALCULATE(
    MINX(
        ADDCOLUMNS(d_equipamentos
            ,"DISPONIBILIDADES"
            ,[Disponibilidade (%)]
        )
        ,[DISPONIBILIDADES]
    )
    ,USERELATIONSHIP(d_data_hora[FECHAMENTO],d_calendar[DATA])
    ,FILTER(d_data_hora
        ,[FILTRO_ANTES_AGORA]=1
    )
)
```
### medidas.Disponibilidade Meta (%)
```dax

COALESCE(
    AVERAGEX(
        ADDCOLUMNS(d_equipamentos
            ,"META"
            ,AVERAGE(d_meta_equipamentos[META DISP])
        )
        ,IF([CATEGORIA_M]="VEÍCULOS LEVES",.9,[META])
    )
    ,0.85
)
```
### medidas.Disponível Agora
```dax

DISTINCTCOUNT(d_equipamentos[CD_EQUIPTO]) -
CALCULATE(
    DISTINCTCOUNT(f_manfro[CD_EQUIPTO])
    ,FILTER(f_manfro
        ,[STATUS]="Andamento"
    )
    ,FILTER(d_criterio_disponibilidade
        ,[Considerar]="S"
    )
)
```
### medidas.Parados
```dax

CALCULATE(
    DISTINCTCOUNT(f_manfro[CD_EQUIPTO])
    ,FILTER(f_manfro
        ,[STATUS]="Andamento"
    )
    ,FILTER(d_criterio_disponibilidade
        ,[Considerar]="S" || [COD_CLASS] in {3}
    )
)
```
### medidas.Total Equipamentos
```dax
DISTINCTCOUNT(d_equipamentos[CD_EQUIPTO])
```
### medidas.Delta Equipamentos
```dax

[Total Equipamentos]-[Disponível Agora]
```
### medidas.Disponibilidade Média Att (%)
```dax

DIVIDE(
    [Disponibilidade Média (%)]
    ,[Disponibilidade Meta (%)]
)
```
### medidas.Disponível Agora (%)
```dax

DIVIDE(
    [Disponível Agora]
    ,[Total Equipamentos]
)
```
### medidas.Disponibilidade Gráfico
```dax

VAR vDia = SELECTEDVALUE(d_data_hora[Date])
RETURN
AVERAGEX(
    ADDCOLUMNS(
        d_data_hora
        ,"DISP"
        ,IF([DATE]=vDia,[Disponibilidade Média (%)])
    )
    ,[DISP]
)
```
### medidas.Cor
```dax
IF(medidas[Disponibilidade Média (%)] >= medidas[Disponibilidade Meta (%)], "#187518", "#870000")
```
### medidas.Requisições de Compra
```dax

DISTINCTCOUNT(f_ordem_compra[NUM_DOCERP])
```
### medidas.Leadtime de Aprovação RC
```dax

CALCULATE(
    AVERAGEX(f_pend_aprov,MAX(([DT_APROVA]+[HORA_APROVACAO])-([DT_GERACAO]+[HORA_GERACAO]),0))*1
    ,FILTER(f_pend_aprov
        ,[SEQ_APROV] = 1
    )
    ,USERELATIONSHIP(f_ordem_compra[CHAVE_DOC_APROV],f_pend_aprov[CHAVE_DOC])
)
```
### medidas.Leadtime de Criação do Pedido
```dax

AVERAGEX(
    f_ordem_compra
    ,IF([PEDIDO] <> "0" && [PEDIDO] <> BLANK()
        ,COALESCE([DT_GERACAO_PEDIDO_1],TODAY())
        -COALESCE([DT_APROVA_REQUISIÇÃO],[DT_GERACAO_PEDIDO_1],TODAY())
    )
)
```
### medidas.Leadtime 1ª Aprovação do Pedido
```dax

CALCULATE(
    AVERAGEX(f_pend_aprov,MAX(([DT_APROVA]+[HORA_APROVACAO])-([DT_GERACAO]+[HORA_GERACAO]),0))*1
    ,FILTER(f_pend_aprov
        ,[SEQ_APROV] = 1
    )
    ,USERELATIONSHIP(f_ordem_compra[PEDIDO],f_pend_aprov[CHAVE_DOC])
)
```
### medidas.Leadtime 2ª Aprovação do Pedido
```dax

CALCULATE(
    AVERAGEX(f_pend_aprov,MAX(([DT_APROVA]+[HORA_APROVACAO])-([DT_GERACAO]+[HORA_GERACAO]),0))*1
    ,FILTER(f_pend_aprov
        ,[SEQ_APROV] = 2
    )
    ,USERELATIONSHIP(f_ordem_compra[PEDIDO],f_pend_aprov[CHAVE_DOC])
)
```
### medidas.Leadtime de Atendimento Pedido
```dax
AVERAGEX(f_ordem_compra, 
    IF(f_ordem_compra[DATA_RECEBIMENTO] <> BLANK() && f_ordem_compra[PEDIDO] <> "0", f_ordem_compra[DATA_RECEBIMENTO] - f_ordem_compra[DT_GERACAO_PEDIDO_1]))
```
### medidas.Leadtime Total
```dax

AVERAGEX(f_ordem_compra, 
    IF(f_ordem_compra[DATA_RECEBIMENTO] <> BLANK() && f_ordem_compra[PEDIDO] <> "0"
        , f_ordem_compra[DATA_RECEBIMENTO] - f_ordem_compra[HR_ENTRADA]
    )
)
```
### medidas.Valor Total
```dax
SUMX(f_ordem_compra, [QT_MATERIAL] * [PRECO_UN])
```
### medidas.RC Valor Total
```dax
SUMX(f_ordem_compra, f_ordem_compra[QT_MATERIAL] * f_ordem_compra[PRECO_UN])
```
### medidas.Pedidos Valor Total
```dax

CALCULATE(
    SUMX(f_ordem_compra
    ,f_ordem_compra[QT_MATERIAL] * f_ordem_compra[PRECO_UN])
    ,filter(f_ordem_compra,[DT_GERACAO_PEDIDO_1]>0)
)
```
### medidas.Delta Valor RC
```dax
[RC Valor Total] - [Pedidos Valor Total]
```
### medidas.Delta Prazo Faturamento
```dax

AVERAGEX(f_ordem_compra, 
    COALESCE(f_ordem_compra[DATA_FATURAMENTO],TODAY()) - [DATA_FAT_PROMETIDA_AJUSTE]
)
```
### medidas.Quantidade Itens
```dax
SUM(f_ordem_compra[QT_MATERIAL])
```
### medidas.Leadtime de Transporte
```dax
AVERAGEX(f_ordem_compra, 
    IF(f_ordem_compra[DATA_RECEBIMENTO] <> BLANK() && f_ordem_compra[PEDIDO] <> "0", f_ordem_compra[DATA_RECEBIMENTO] - f_ordem_compra[DATA_FATURAMENTO]))
```
### medidas.Leadtime de Geração RC
```dax

AVERAGEX(f_ordem_compra,IF([DT_ENVIO]>0,MAX([DT_ENVIO]-[HR_ENTRADA],0)))*1
```
### medidas.Lubrificante Volume (l)
```dax

CALCULATE(
    SUM(f_lubrificante[QT_LUBRIF])
    ,FILTER(
        f_lubrificante
        ,[CD_MATERIAL] = 14320
        && [FG_REM_TROCA] = "R"
    )
)
```
### medidas.Consumo Diesel Meta (l/h)
```dax

VAR EQP =
SELECTEDVALUE(d_equipamentos[CATEGORIA],"Colhedora")
RETURN
SWITCH(TRUE()
    ,EQP="Colhedora",35.95
    ,9
)
```
### medidas.Consumo Diesel Meta (l/t)
```dax

VAR COLHEDORAS =
COALESCE(
    CALCULATE(
        MAX(d_meta_unidade[DIESEL_COLHEDORA])
        ,FILTER(d_meta_unidade
            ,MONTH([MES])=MONTH(SELECTEDVALUE(d_calendar[DATA]))
        )
    )
    ,DIVIDE(
        SUMX(
            d_meta_unidade
            ,[DIESEL_COLHEDORA]*[TC]
        )
        ,SUM(d_meta_unidade[TC])
    )
)
VAR TRATORES =
COALESCE(
    CALCULATE(
        MAX(d_meta_unidade[DIESEL_TRATOR])
        ,FILTER(d_meta_unidade
            ,MONTH([MES])=MONTH(SELECTEDVALUE(d_calendar[DATA]))
        )
    )
    ,DIVIDE(
        SUMX(
            d_meta_unidade
            ,[DIESEL_TRATOR]*[TC]
        )
        ,SUM(d_meta_unidade[TC])
    )
)
VAR EQP =
SELECTEDVALUE(d_equipamentos[CATEGORIA],"Colhedora")
RETURN
SWITCH(TRUE()
    ,EQP="Colhedora",COLHEDORAS
    ,TRATORES
)
```
### medidas.Diesel Hora Eixo Y Mês
```dax

VAR vTabela = ALLSELECTED(d_calendar[MES])
VAR vMaiorValor = MAXX(vTabela,[Consumo Diesel (l/h)])
VAR vTabela2 = ALLSELECTED(d_equipamentos[FRENTE])
VAR vMaiorValor2 = MAXX(vTabela2,[Consumo Diesel (l/h)])
RETURN
IF(
    SELECTEDVALUE(d_calendar[DATA],0)=0
    ,MAX(vMaiorValor,vMaiorValor2)*1.2
    ,50
)
```
### medidas.Diesel Hora Eixo Y Semana
```dax

VAR vTabela = ALLSELECTED(d_calendar[SEMANA_ANO])
VAR vMaiorValor = MAXX(vTabela,[Consumo Diesel (l/h)])
RETURN
// IF(
//     SELECTEDVALUE(d_calendar[DATA],0)=0
//     ,vMaiorValor*1.2
//     ,50
// )
[Diesel Hora Eixo Y Mês]
```
### medidas.Diesel Tonelada Eixo Y Mês
```dax

VAR vTabela = ALLSELECTED(d_calendar[MES])
VAR vMaiorValor = MAXX(vTabela,[Consumo Diesel (l/t)])
VAR vTabela2 = ALLSELECTED(d_equipamentos[FRENTE])
VAR vMaiorValor2 = MAXX(vTabela2,[Consumo Diesel (l/t)])
RETURN
IF(
    SELECTEDVALUE(d_calendar[DATA],0)=0
    ,MAX(vMaiorValor,vMaiorValor2)*1.2
    ,50
)
```
### medidas.Diesel Tonelada Eixo Y Semana
```dax

VAR vTabela = ALLSELECTED(d_calendar[SEMANA_ANO])
VAR vMaiorValor = MAXX(vTabela,[Consumo Diesel (l/t)])
RETURN
// IF(
//     SELECTEDVALUE(d_calendar[DATA],0)=0
//     ,vMaiorValor*1.2
//     ,2
// )
[Diesel Tonelada Eixo Y Mês]
```
### medidas.Diesel Volume (l)
```dax

VAR __dieselEQP =
CALCULATE(
    CALCULATE(
        SUM(f_abastecimento[LITROS])
        ,FILTER(f_abastecimento
            ,[CD_MATERIAL] IN {89500,89838,104542}
        )
        ,USERELATIONSHIP(d_meta_frente[FRENTE],d_equipamentos[FRENTE])
    )
    ,FILTER(
        ADDCOLUMNS(
            ADDCOLUMNS(f_abastecimento
                ,"EQPS"
                ,VAR vEqp = f_abastecimento[CD_EQUIPTO]
                RETURN
                CALCULATE(
                    COUNTROWS(d_equipamentos)
                    ,FILTER(d_equipamentos
                        ,[CD_EQUIPTO]=vEqp
                        &&[DATA.1]>0
                    )
                )
            )
            ,"IGNORAR"
            ,IF([DT_OPERACAO]>=MIN(d_equipamentos[DATA.1])&&[DT_OPERACAO]<=MAX(d_equipamentos[DATA.2])&&[EQPS]>0,1,0)
        )
        ,[IGNORAR]=0
    )
)
VAR __dieselCC =
CALCULATE(
    __dieselEQP
    ,CROSSFILTER(d_equipamentos[CD_CCUSTO],d_orcamento_diesel[C Custo],None)
)
RETURN
IF(
    SELECTEDVALUE(d_base_calc[Cod],1)=2
    ,__dieselCC
    ,__dieselEQP
)
```
### medidas.Perda Hidráulico (l/t)
```dax
VAR VolumeLubrificanteValido =
    CALCULATE(
        SUM(f_lubrificante[QT_LUBRIF]),
        FILTER(
            f_lubrificante,
            f_lubrificante[CD_MATERIAL] = 14320
                && f_lubrificante[FG_REM_TROCA] = "R"
                && CALCULATE(
                    COUNTROWS(d_datas_ignorar),
                    FILTER(
                        ALL(d_datas_ignorar),
                        d_datas_ignorar[CD_EQUIPTO] = f_lubrificante[CD_EQUIPTO]
                            && f_lubrificante[DT_OPERACAO] >= d_datas_ignorar[DATA.1]
                            && f_lubrificante[DT_OPERACAO] <= d_datas_ignorar[DATA.2]
                    )
                ) = 0
        )
    )
VAR ProducaoValida =
    CALCULATE(
        SUM(f_produtividade[QT_CANA_ENT]),
        USERELATIONSHIP(d_meta_frente[CD_FREN_TRAN], d_equipamentos[CD_FREN_TRAN]),
        FILTER(
            f_produtividade,
            CALCULATE(
                COUNTROWS(d_datas_ignorar),
                FILTER(
                    ALL(d_datas_ignorar),
                    d_datas_ignorar[CD_EQUIPTO] = f_produtividade[CD_EQUIPTO]
                        && f_produtividade[DT_HISTORICO] >= d_datas_ignorar[DATA.1]
                        && f_produtividade[DT_HISTORICO] <= d_datas_ignorar[DATA.2]
                )
            ) = 0
        )
    )
RETURN
    ROUND(
        DIVIDE(VolumeLubrificanteValido, ProducaoValida),
        3
    )
```
### medidas.Perda Hidráulico Att (%)
```dax

DIVIDE(
    [Perda Hidráulico Meta (l/t)]
    ,[Perda Hidráulico (l/t)]
)
```
### medidas.Perda Hidráulico Meta (l/t)
```dax

VAR COLHEDORAS =
COALESCE(
    CALCULATE(
        MAX(d_meta_unidade[HIDRAULICO_COLHEDORA])
        ,FILTER(d_meta_unidade
            ,MONTH([MES])=MONTH(SELECTEDVALUE(d_calendar[DATA]))
        )
    )
    ,DIVIDE(
        SUMX(
            d_meta_unidade
            ,[HIDRAULICO_COLHEDORA]*[TC]
        )
        ,SUM(d_meta_unidade[TC])
    )
)
VAR TRATORES =
COALESCE(
    CALCULATE(
        MAX(d_meta_unidade[HIDRAULICO_TRATOR])
        ,FILTER(d_meta_unidade
            ,MONTH([MES])=MONTH(SELECTEDVALUE(d_calendar[DATA]))
        )
    )
    ,DIVIDE(
        SUMX(
            d_meta_unidade
            ,[HIDRAULICO_TRATOR]*[TC]
        )
        ,SUM(d_meta_unidade[TC])
    )
)
VAR EQP =
SELECTEDVALUE(d_equipamentos[CATEGORIA],"Colhedora")
RETURN
SWITCH(TRUE()
    ,EQP="Colhedora",COLHEDORAS
    ,TRATORES
)
```
### medidas.Tempo Distancia (h/km)
```dax

CALCULATE(
    CALCULATE(
        SUM(f_abastecimento[HORA_KM])
        ,FILTER(
            ADDCOLUMNS(
                f_abastecimento
                ,"maxAbastecimento"
                ,CALCULATE(
                    MAX(f_abastecimento[DT_OPERACAO])
                    ,FILTER(
                        f_abastecimento
                        ,f_abastecimento[LITROS]>0
                    )
                )
            )
            ,[CD_MATERIAL] IN {89500,89838,104542} && [DT_OPERACAO]<=[maxAbastecimento]
        )
        ,USERELATIONSHIP(d_meta_frente[CD_FREN_TRAN],d_equipamentos[CD_FREN_TRAN])
    )
    ,FILTER(
        ADDCOLUMNS(
            ADDCOLUMNS(f_abastecimento
                ,"EQPS"
                ,VAR vEqp = f_abastecimento[CD_EQUIPTO]
                RETURN
                CALCULATE(
                    COUNTROWS(d_equipamentos)
                    ,FILTER(d_equipamentos
                        ,[CD_EQUIPTO]=vEqp
                        &&[DATA.1]>0
                    )
                )
            )
            ,"IGNORAR"
            ,IF([DT_OPERACAO]>=MIN(d_equipamentos[DATA.1])&&[DT_OPERACAO]<=MAX(d_equipamentos[DATA.2])&&[EQPS]>0,1,0)
        )
        ,[IGNORAR]=0
    )
)
```
### medidas.Texto Meta Diesel
```dax

"Meta Consumo: ≤"&FORMAT([Consumo Diesel Meta (l/t)],"0.00")&" (l/t)"
```
### medidas.Texto Meta Diesel Hora
```dax

"Meta Consumo: ≤"&FORMAT([Consumo Diesel Meta (l/h)],"0.00")&" (l/h)"
```
### medidas.Texto Meta Hidráulico
```dax

"Meta Consumo: ≤"&FORMAT([Perda Hidráulico Meta (l/t)],"0.000")&" (l/t)"
```
### medidas.Consumo Diesel Att Hora (%)
```dax

MIN(
    DIVIDE(
        [Consumo Diesel Meta (l/h)]
        ,[Consumo Diesel (l/h)]
    )
    ,1
)
```
### medidas.Consumo Diesel Att (%)
```dax

MIN(
    DIVIDE(
        [Consumo Diesel Meta (l/t)]
        ,[Consumo Diesel (l/t)]
    )
    ,1
)
```
### medidas.Consumo Diesel (l/t)
```dax

VAR vFrente = SELECTEDVALUE(d_equipamentos[FRENTE],BLANK())
VAR vMedida =
CALCULATE(
    ROUND(
        DIVIDE(
            [Diesel Volume (l)]
            ,[Produção Equipamentos Volume (t)]
        )
        ,3
    )
    ,FILTER(d_calendar
        ,[DATA]<=MAX(d_calendar[DATA])
    )
)
RETURN
COALESCE(
    [Diesel Tonelada Semana Ajuste]
    ,IF(vFrente <> BLANK()
        ,
        COALESCE(
            vMedida
            ,0
        )
        ,vMedida
    )
)
```
### medidas.Consumo Diesel (l/h)
```dax

VAR vFrente = SELECTEDVALUE(d_equipamentos[FRENTE],BLANK())
VAR vLitrosHora =
CALCULATE(
    ROUND(
        DIVIDE(
            [Diesel Volume (l)]
            ,[Tempo Distancia (h/km)]
        )
        ,3
    )
    ,FILTER(d_calendar
        ,d_calendar[DATA] <= MAX(d_calendar[DATA])
    )
)
VAR vKMLitros =
CALCULATE(
    ROUND(
        DIVIDE(
            [Tempo Distancia (h/km)]
            ,[Diesel Volume (l)]
        )
        ,3
    )
    ,FILTER(d_calendar
        ,d_calendar[DATA] <= MAX(d_calendar[DATA])
    )
)
VAR vMedida =
IF(
    [Unidade Medida]="(l/h)"
    ,vLitrosHora
    ,vKMLitros
)
RETURN
COALESCE(
    [Diesel Hora Semana Ajuste]
    ,IF(vFrente <> BLANK()
        ,
        COALESCE(
            vMedida
            ,0
        )
        ,vMedida
    )
)
```
### medidas.Produção Equipamentos Volume (t)
```dax

CALCULATE(
    SUM(f_produtividade[QT_CANA_ENT])
    ,USERELATIONSHIP(d_meta_frente[CD_FREN_TRAN],d_equipamentos[CD_FREN_TRAN])
)
```
### medidas.Quantidade Cana (t)
```dax
SUM(f_produtividade[QT_CANA_ENT])
```
### medidas.Valor (R$/h)
```dax

CALCULATE(
    DIVIDE([Valor Total Aplicado],[Tempo Distancia (h/km)])
    ,FILTER(d_criterio_disponibilidade,[COD_CLASS] <> 7) --removendo a entressafra
)
```
### medidas.Valor (R$/t)
```dax

CALCULATE(
    DIVIDE([Valor Total Aplicado],[Quantidade Cana (t)])
    ,FILTER(d_criterio_disponibilidade,[COD_CLASS] <> 7) --removendo a entressafra
)
```
### medidas.TON/FACA
```dax

DIVIDE(
    [Produção Equipamentos Volume (t)]
    ,CALCULATE(
        [Quantidade Itens Aplicados]
        ,FILTER(d_item
            ,[IT_CODIGO] = "11269"
        )
    )
)
```
### medidas.TON/FACAO
```dax

DIVIDE(
    [Produção Equipamentos Volume (t)]
    ,CALCULATE(
        [Quantidade Itens Aplicados]
        ,FILTER(d_item
            ,[IT_CODIGO] IN {"12858","71049","20183"}
        )
    )
)
```
### medidas.TON/H
```dax

CALCULATE(
    DIVIDE([Quantidade Cana (t)],[Tempo Distancia (h/km)])
    ,FILTER(
        ADDCOLUMNS(
            ADDCOLUMNS(f_abastecimento
                ,"EQPS"
                ,VAR vEqp = f_abastecimento[CD_EQUIPTO]
                RETURN
                CALCULATE(
                    COUNTROWS(d_equipamentos)
                    ,FILTER(d_equipamentos
                        ,[CD_EQUIPTO]=vEqp
                        &&[DATA.1]>0
                    )
                )
            )
            ,"IGNORAR"
            ,IF([DT_OPERACAO]>=MIN(d_equipamentos[DATA.1])&&[DT_OPERACAO]<=MAX(d_equipamentos[DATA.2])&&[EQPS]>0,1,0)
        )
        ,[IGNORAR]=0
    )
)
```
### medidas.TCH
```dax

CALCULATE(
    DIVIDE(
        SUM(f_tch[TON_ENTREGUE])
        ,SUM(f_tch[AREA_COLHIDA])
    )
    ,USERELATIONSHIP(d_calendar[DATA],f_tch[DT_FECHEMENTO])
    ,USERELATIONSHIP(d_equipamentos[FRENTE],d_meta_frente[FRENTE])
)
```
### medidas.Leadtime de Emissão da Nota
```dax

AVERAGEX(f_ordem_compra, 
    IF(f_ordem_compra[DATA_FATURAMENTO] <> BLANK() && f_ordem_compra[PEDIDO] <> "0" && [DATA_FATURAMENTO] > COALESCE([DT_APROVA_PEDIDO_2],[DT_APROVA_PEDIDO_1],[DT_GERACAO_PEDIDO_1])
        , f_ordem_compra[DATA_FATURAMENTO] - COALESCE(f_ordem_compra[DT_APROVA_PEDIDO_2],[DT_APROVA_PEDIDO_1],[DT_GERACAO_PEDIDO_1])
    )
)
```
### medidas.Leadtime Total 2
```dax

[Leadtime de Geração RC]+[Leadtime de Aprovação RC]+[Leadtime de Criação do Pedido]+[Leadtime 1ª Aprovação do Pedido]+[Leadtime 2ª Aprovação do Pedido]+[Leadtime de Emissão da Nota]+[Leadtime de Transporte]
```
### medidas.Hidraulico Tonelada Eixo Y Mês
```dax

VAR vTabela = ALLSELECTED(d_calendar[DATA])
VAR vMaiorValor = MAXX(vTabela,[Perda Hidráulico (l/t)])
VAR vTabela2 = ALLSELECTED(d_equipamentos[FRENTE])
VAR vMaiorValor2 = MAXX(vTabela2,[Perda Hidráulico (l/t)])
RETURN
IF(
    SELECTEDVALUE(d_calendar[DATA],0)=0
    ,MAX(vMaiorValor,vMaiorValor2)*1.2
    ,50
)
```
### medidas.Hidraulico Tonelada Eixo Y Semana
```dax

VAR vTabela = ALLSELECTED(d_calendar[SEMANA_ANO])
VAR vMaiorValor = MAXX(vTabela,[Perda Hidráulico (l/t)])
RETURN
// IF(
//     SELECTEDVALUE(d_calendar[DATA],0)=0
//     ,vMaiorValor*1.2
//     ,2
// )
[Hidraulico Tonelada Eixo Y Mês]
```
### medidas.Valor Total Aplicado
```dax

CALCULATE(
    SUMX(f_ordem_compra,IF([VALOR_APLICADO]=0,[VALOR_APLICADO_AJUSTADO],[VALOR_APLICADO]))
    ,CROSSFILTER(d_calendar[DATA],f_ordem_compra[DATA_ENVIO_AJUSTE],None)
    ,USERELATIONSHIP(d_calendar[DATA],f_ordem_compra[DT_ATEND])
)
```
### medidas.Quantidade Itens Aplicados
```dax

CALCULATE(
    SUM(f_ordem_compra[QTD_MAT_APLICADO])
    ,CROSSFILTER(d_calendar[DATA],f_ordem_compra[DATA_ENVIO_AJUSTE],None)
    ,USERELATIONSHIP(d_calendar[DATA],f_ordem_compra[DT_ATEND])
)
```
### medidas.Consumo Diesel Meta (l/h) MAX
```dax
MAX([Consumo Diesel Meta (l/h)],[Consumo Diesel (l/h)])*1.1
```
### medidas.Consumo Diesel Meta (l/t) MAX
```dax
MAX([Consumo Diesel Meta (l/T)],[Consumo Diesel (l/t)])*1.1
```
### medidas.Perda Hidráulico (l/t) MAX
```dax

MAX([Perda Hidráulico (l/t)],[Perda Hidráulico Meta (l/t)])*1.20
```
### medidas.Disponibilidade Semana Ajuste
```dax

IF(SELECTEDVALUE(d_calendar[SEMANA_PIMS],"") IN {"S-01","S-02"}
    ,CALCULATE(
        MAX(ajustes_consumos[Valor])
        ,FILTER(ajustes_consumos
            ,[Indicador]="disp"
        )
    )
)
```
### medidas.Diesel Hora Semana Ajuste
```dax

IF(SELECTEDVALUE(d_calendar[SEMANA_PIMS],"") IN {"S-01","S-02"}
    ,CALCULATE(
        MAX(ajustes_consumos[Valor])
        ,FILTER(ajustes_consumos
            ,[Indicador]="dh"
        )
    )
)
```
### medidas.Diesel Tonelada Semana Ajuste
```dax

IF(SELECTEDVALUE(d_calendar[SEMANA_PIMS],"") IN {"S-01","S-02"}
    ,CALCULATE(
        MAX(ajustes_consumos[Valor])
        ,FILTER(ajustes_consumos
            ,[Indicador]="dt"
        )
    )
)
```
### medidas.Hidráulico Semana Ajuste
```dax

IF(SELECTEDVALUE(d_calendar[SEMANA_PIMS],"") IN {"S-01","S-02"}
    ,CALCULATE(
        MAX(ajustes_consumos[Valor])
        ,FILTER(ajustes_consumos
            ,[Indicador]="h"
        )
    )
)
```
### medidas.Disponibilidade Gráfico Mês
```dax

VAR vMes = SELECTEDVALUE(d_meses[FIM_MES_ANO],0)
RETURN
CALCULATE(
    SUMX(
        ADDCOLUMNS(d_meses,"DISP",[Disponibilidade Média (%)])
        ,IF([DISP]>0,[DISP])
    )
    ,FILTER(
        d_calendar
        ,[FIM_MES_ANO]=vMes
    )
)
```
### medidas.Lubrificante Volume Semana (l)
```dax

VAR vPeriodo = MAX(d_calendar[ANO_SEMANA])
VAR vMaxData = MAX(d_calendar[DATA])
RETURN
CALCULATE(
    [Lubrificante Volume (l)]
    ,FILTER(
        d_calendar
        ,[ANO_SEMANA] = vPeriodo
        &&[DATA] <= vMaxData
    )
)
```
### medidas.Lubrificante Volume Mês (l)
```dax

VAR vPeriodo = MAX(d_calendar[FIM_MES_ANO])
VAR vMaxData = MAX(d_calendar[DATA])
RETURN
CALCULATE(
    [Lubrificante Volume (l)]
    ,FILTER(
        d_calendar
        ,[FIM_MES_ANO] = vPeriodo
        &&[DATA] <= vMaxData
    )
)
```
### medidas.Lubrificante Volume (tambor)
```dax
DIVIDE([Lubrificante Volume (l)], 200)
```
### medidas.Consumo Diesel (l/h) Gráfico Mês
```dax

VAR vMes = SELECTEDVALUE(d_meses[FIM_MES_ANO],0)
RETURN
CALCULATE(
    SUMX(
        ADDCOLUMNS(d_meses,"MEDIDA",[Consumo Diesel (l/h)])
        ,IF([MEDIDA]>0,[MEDIDA])
    )
    ,FILTER(
        d_calendar
        ,[FIM_MES_ANO]=vMes
    )
)
```
### medidas.Consumo Diesel (l/t) Gráfico Mês
```dax

VAR vMes = SELECTEDVALUE(d_meses[FIM_MES_ANO],0)
RETURN
CALCULATE(
    SUMX(
        ADDCOLUMNS(d_meses,"MEDIDA",[Consumo Diesel (l/t)])
        ,IF([MEDIDA]>0,[MEDIDA])
    )
    ,FILTER(
        d_calendar
        ,[FIM_MES_ANO]=vMes
    )
)
```
### medidas.Perda Hidráulico (l/t) Gráfico Mês
```dax

VAR vMes = SELECTEDVALUE(d_meses[FIM_MES_ANO],0)
RETURN
CALCULATE(
    SUMX(
        ADDCOLUMNS(d_meses,"MEDIDA",[Perda Hidráulico (l/t)])
        ,IF([MEDIDA]>0,[MEDIDA])
    )
    ,FILTER(
        d_calendar
        ,[FIM_MES_ANO]=vMes
    )
)
```
### medidas.Orçamento KM Veículos
```dax

SUM(d_orcamento_equipamentos[Valor])
```
### medidas.Realizado KM Veículos
```dax

CALCULATE(
    SUMX(
        ADDCOLUMNS(
            f_abastecimento
            ,"EQP"
            ,CALCULATE(
                COUNT(d_orcamento_equipamentos[FROTA])
                ,USERELATIONSHIP(d_orcamento_equipamentos[FROTA],f_abastecimento[CD_EQUIPTO])
            )
        )
        ,IF([EQP]>0,[HORA_KM])
    )
)
// CALCULATE(
//     SUM(f_abastecimento[HORA_KM])
//     ,FILTER(ADDCOLUMNS(f_abastecimento,"maxAbastecimento",CALCULATE(MAX(f_abastecimento[DT_OPERACAO]),FILTER(f_abastecimento,f_abastecimento[LITROS]>0)))
//         ,[DT_OPERACAO]<=[maxAbastecimento]
//     )
//     ,USERELATIONSHIP(d_orcamento_equipamentos[FROTA],f_abastecimento[CD_EQUIPTO])
// )
```
### medidas.Orçamento KM Veículos Att
```dax

DIVIDE([Realizado KM Veículos],[Orçamento KM Veículos])
```
### medidas.Orcamento KM Veículos Max
```dax
[Orçamento KM Veículos]*1.2
```
### medidas.Destaque Frota Cor
```dax
IF (
    CONTAINS(
        d_datas_ignorar,
        d_datas_ignorar[CD_EQUIPTO],
        SELECTEDVALUE('d_equipamentos'[CD_EQUIPTO])
    ),
    "#808080",
    IF (
        SELECTEDVALUE('d_equipamentos'[FRENTE]) = "Frente 4" || SELECTEDVALUE('d_equipamentos'[FRENTE]) = "Frente 2",
        "#e6e6e6",
        ""
    )
)
```
### medidas.Quantidade Realizado Veículos
```dax

CALCULATE(
    SUMX(
        ADDCOLUMNS(
            f_ordem_compra
            ,"EQP"
            ,CALCULATE(
                COUNT(d_orcamento_equipamentos[FROTA])
                ,USERELATIONSHIP(d_equipamentos[CD_EQUIPTO],d_orcamento_equipamentos[FROTA])
            )
        )
        ,IF([EQP]>0,[QTD_MAT_APLICADO])
    )
    ,CROSSFILTER(d_calendar[DATA],f_ordem_compra[DATA_ENVIO_AJUSTE],None)
    ,USERELATIONSHIP(d_calendar[DATA],f_ordem_compra[DT_ATEND])
)
```
### medidas.Cor Orçamento KM
```dax

IF(
    [Orçamento KM Veículos Att] < 1,
    "#187518", --verde
    "#870000"  --vermelho
)
```
### medidas.Orçado KM Veículos Delta
```dax
MAX([Orçamento KM Veículos]-[Realizado KM Veículos],0)
```
### medidas.Orçamento KM Veículos Label
```dax

[Orçamento KM Veículos]
```
### medidas.Valor Realizado Veículos
```dax

CALCULATE(
    SUMX(
        ADDCOLUMNS(
            f_ordem_compra
            ,"EQP"
            ,CALCULATE(
                COUNT(d_orcamento_equipamentos[FROTA])
                ,USERELATIONSHIP(d_equipamentos[CD_EQUIPTO],d_orcamento_equipamentos[FROTA])
            )
        )
        ,IF([EQP]>0,[VALOR_APLICADO])
    )
    ,CROSSFILTER(d_calendar[DATA],f_ordem_compra[DATA_ENVIO_AJUSTE],None)
    ,USERELATIONSHIP(d_calendar[DATA],f_ordem_compra[DT_ATEND])
)
```
### medidas.Realizado KM Veículos Acum em DATA
```dax

IF(
    MAX(d_calendar[DATA])<=CALCULATE(MAX(f_abastecimento[DT_OPERACAO]),ALL(d_calendar))
    ,CALCULATE(
        [Realizado KM Veículos],
        FILTER(
            ALLSELECTED('d_calendar'[DATA]),
            ISONORAFTER('d_calendar'[DATA], MAX('d_calendar'[DATA]), DESC)
        )
    )
)
```
### medidas.Orçamento KM Dia
```dax

SUMX(
    ADDCOLUMNS(d_calendar
        ,"BGT"
        ,[Orçamento KM Veículos]
    )
    ,DIVIDE([BGT],DAY([FIM_MES_ANO]))
)
```
### medidas.Orçamento KM Dia Acum em DATA
```dax

CALCULATE(
	[Orçamento KM Dia],
	FILTER(
		ALLSELECTED('d_calendar'[DATA]),
		ISONORAFTER('d_calendar'[DATA], MAX('d_calendar'[DATA]), DESC)
	)
)
```
### medidas.Realizado KM Veículos Hoje Verde
```dax

IF(MAX(d_calendar[DATA])=CALCULATE(MAX(f_abastecimento[DT_OPERACAO]),ALL(d_calendar))
    ,[Realizado KM Veículos Acum em DATA]
)
```
### medidas.Orçamento KM Acum Veículos Att
```dax

DIVIDE([Realizado KM Veículos Acum em DATA],[Orçamento KM Dia Acum em DATA])
```
### medidas.Cor Orçamento Acum KM
```dax

IF(
    [Orçamento KM Acum Veículos Att] < 1,
    "#187518", --verde
    "#870000"  --vermelho
)
```
### medidas.Disponibilidade Gráfico Mês Att
```dax
DIVIDE([Disponibilidade Gráfico Mês],[Disponibilidade Meta (%)])
```
### medidas.Consumo Diesel (l/h) Gráfico Mês Att
```dax
DIVIDE([Consumo Diesel Meta (l/h)],[Consumo Diesel (l/h) Gráfico Mês])
```
### medidas.Consumo Diesel (l/t) Gráfico Mês Att
```dax
DIVIDE([Consumo Diesel Meta (l/t)],[Consumo Diesel (l/t) Gráfico Mês])
```
### medidas.Perda Hidráulico (l/t) Gráfico Mês Att
```dax
DIVIDE([Perda Hidráulico Meta (l/t)],[Perda Hidráulico (l/t) Gráfico Mês])
```
### medidas.Óleo Motor Volume (l)
```dax

CALCULATE(
    SUM(f_lubrificante[QT_LUBRIF])
    ,FILTER(
        f_lubrificante
        ,[CD_MATERIAL] = 81025
        && [FG_REM_TROCA] = "R"
    )
)
```
### medidas.Óleo Motor / Diesel
```dax

VAR vFrente = SELECTEDVALUE(d_equipamentos[FRENTE],BLANK())
VAR vMedida =
ROUND(
    DIVIDE(
        [Óleo Motor Volume (l)]
        ,[Diesel Volume (l)]/100
    )
    ,4
)
RETURN
IF(vFrente <> BLANK()
    ,COALESCE(
        vMedida
        ,0
    )
    ,vMedida
)
```
### medidas.Óleo Motor / Diesel Meta
```dax
0.04
```
### medidas.Óleo Motor / Diesel Cor
```dax

IF([Óleo Motor / Diesel]>[Óleo Motor / Diesel Meta],"#870000","#187518")
```
### medidas.Óleo Motor / Diesel Eixo Y Mês
```dax

VAR vTabela = ALLSELECTED(d_calendar[DATA])
VAR vMaiorValor = MAXX(vTabela,[Óleo Motor / Diesel])
VAR vTabela2 = ALLSELECTED(d_equipamentos[FRENTE])
VAR vMaiorValor2 = MAXX(vTabela2,[Óleo Motor / Diesel])
RETURN
IF(
    SELECTEDVALUE(d_calendar[DATA],0)=0
    ,MAX(vMaiorValor,vMaiorValor2)*1.2
    ,50
)
```
### medidas.TON/FACA Meta
```dax
155
```
### medidas.R$/H Meta
```dax
134.84
```
### medidas.R$/TON Meta
```dax
3.31
```
### medidas.TON/H Meta
```dax
41
```
### medidas.TON/FACAO Meta
```dax
550
```
### medidas.Óleo Motor / Diesel Gráfico Mês
```dax

VAR vMes = SELECTEDVALUE(d_meses[FIM_MES_ANO],0)
RETURN
CALCULATE(
    SUMX(
        ADDCOLUMNS(d_meses,"MEDIDA",[Óleo Motor / Diesel])
        ,IF([MEDIDA]>0,[MEDIDA])
    )
    ,FILTER(
        d_calendar
        ,[FIM_MES_ANO]=vMes
    )
)
```
### medidas.Óleo Motor / Diesel Gráfico Mês Cor
```dax

IF([Óleo Motor / Diesel Gráfico Mês]>[Óleo Motor / Diesel Meta],"#870000","#187518")
```
### medidas.TON/FACA Cor
```dax

IF([TON/FACA]>[TON/FACA Meta],"#870000","#187518")
```
### medidas.TON/FACAO Cor
```dax

IF([TON/FACAO]>[TON/FACAO Meta],"#870000","#187518")
```
### medidas.Texto Meta Óleo Mineral
```dax

"Meta Consumo: ≤"&FORMAT([Óleo Motor / Diesel Meta],"0.0000")&" (l/l. diesel)"
```
### medidas.Texto Meta t/faca
```dax

"Meta Consumo: ≤"&FORMAT([TON/FACA Meta],"0.0000")&" (t/un.)"
```
### medidas.Texto Meta t/facao
```dax

"Meta Consumo: ≤"&FORMAT([TON/FACAO Meta],"0.0000")&" (t/un.)"
```
### medidas.Horas
```dax

CALCULATE(
    [Tempo Distancia (h/km)]
    ,FILTER(f_abastecimento
        ,[LITROS]>0
        --&&[CD_UNIMED]="H"
    )
)
```
### medidas.Diesel Volume Semana (l)
```dax
// VAR vPeriodo = MAX(d_calendar[ANO_SEMANA])
// VAR vMaxData = MAX(d_calendar[DATA])
// RETURN
// CALCULATE(
//     [Diesel Volume (l)]
//     ,FILTER(
//         d_calendar
//         ,[ANO_SEMANA] = vPeriodo
//         &&[DATA] <= vMaxData
//     )
// )
VAR vMaxAbast = CALCULATE(MAX(f_abastecimento[DT_OPERACAO]))
VAR vMaxFiltro = CALCULATE(MAX(d_calendar[DATA]), ALLSELECTED(d_calendar))
VAR vMaxData = MIN(vMaxAbast, vMaxFiltro)
VAR vPeriodo = CALCULATE(SELECTEDVALUE(d_calendar[ANO_SEMANA]), FILTER(ALL(d_calendar), d_calendar[DATA] = vMaxData))
RETURN
CALCULATE(
    [Diesel Volume (l)],
    FILTER(ALLSELECTED(d_calendar), d_calendar[ANO_SEMANA] = vPeriodo && d_calendar[DATA] <= vMaxData)
)
```
### medidas.Diesel Volume Mês (l)
```dax
// VAR vPeriodo = MAX(d_calendar[FIM_MES_ANO])
// VAR vMaxData = MAX(d_calendar[DATA])
// RETURN
// CALCULATE(
//     [Diesel Volume (l)]
//     ,FILTER(
//         d_calendar
//         ,[FIM_MES_ANO] = vPeriodo
//         &&[DATA] <= vMaxData
//     )
// )
VAR vMaxAbast = CALCULATE(MAX(f_abastecimento[DT_OPERACAO]))
VAR vMaxFiltro = CALCULATE(MAX(d_calendar[DATA]), ALLSELECTED(d_calendar))
VAR vMaxData = MIN(vMaxAbast, vMaxFiltro)
VAR vPeriodo = CALCULATE(SELECTEDVALUE(d_calendar[FIM_MES_ANO]), FILTER(ALL(d_calendar), d_calendar[DATA] = vMaxData))
RETURN
CALCULATE(
    [Diesel Volume (l)],
    FILTER(ALLSELECTED(d_calendar), d_calendar[FIM_MES_ANO] = vPeriodo && d_calendar[DATA] <= vMaxData)
)
```
### medidas.Horas Mês
```dax
// VAR vPeriodo = MAX(d_calendar[FIM_MES_ANO])
// VAR vMaxData = MAX(d_calendar[DATA])
// RETURN
// CALCULATE(
//     [Horas]
//     ,FILTER(
//         d_calendar
//         ,[FIM_MES_ANO] = vPeriodo
//         &&[DATA] <= vMaxData
//     )
// )
VAR vMaxAbast = CALCULATE(MAX(f_abastecimento[DT_OPERACAO]))
VAR vMaxFiltro = CALCULATE(MAX(d_calendar[DATA]), ALLSELECTED(d_calendar))
VAR vMaxData = MIN(vMaxAbast, vMaxFiltro)
VAR vPeriodo = CALCULATE(SELECTEDVALUE(d_calendar[FIM_MES_ANO]), FILTER(ALL(d_calendar), d_calendar[DATA] = vMaxData))
RETURN
CALCULATE(
    [Horas],
    FILTER(ALLSELECTED(d_calendar), d_calendar[FIM_MES_ANO] = vPeriodo && d_calendar[DATA] <= vMaxData)
)
```
### medidas.Horas Semana
```dax
// VAR vPeriodo = MAX(d_calendar[ANO_SEMANA])
// VAR vMaxData = MAX(d_calendar[DATA])
// RETURN
// CALCULATE(
//     [Horas]
//     ,FILTER(
//         d_calendar
//         ,[ANO_SEMANA] = vPeriodo
//         &&[DATA] <= vMaxData
//     )
// )
VAR vMaxAbast = CALCULATE(MAX(f_abastecimento[DT_OPERACAO]))
VAR vMaxFiltro = CALCULATE(MAX(d_calendar[DATA]), ALLSELECTED(d_calendar))
VAR vMaxData = MIN(vMaxAbast, vMaxFiltro)
VAR vPeriodo = CALCULATE(SELECTEDVALUE(d_calendar[ANO_SEMANA]), FILTER(ALL(d_calendar), d_calendar[DATA] = vMaxData))
RETURN
CALCULATE(
    [Horas],
    FILTER(ALLSELECTED(d_calendar), d_calendar[ANO_SEMANA] = vPeriodo && d_calendar[DATA] <= vMaxData)
)
```
### medidas.Consumo Diesel Semana (l/h)
```dax
// DIVIDE(
//     [Diesel Volume Semana (l)]
//     ,[Horas Semana]
// )
// CALCULATE([Consumo Diesel (l/h)], ALLEXCEPT(d_calendar, d_calendar[ANO_SEMANA]))
// VAR vMaxData = CALCULATE(MAX(f_abastecimento[DT_OPERACAO]))
// VAR vSemana = CALCULATE(SELECTEDVALUE(d_calendar[ANO_SEMANA]), FILTER(d_calendar, d_calendar[DATA] = vMaxData))
// RETURN CALCULATE([Consumo Diesel (l/h)], FILTER(ALL(d_calendar), d_calendar[ANO_SEMANA] = vSemana))
// VAR vMaxData = MAX(d_calendar[DATA])
// VAR vSemana = CALCULATE(SELECTEDVALUE(d_calendar[ANO_SEMANA]), FILTER(ALL(d_calendar), d_calendar[DATA] = vMaxData))
// RETURN CALCULATE([Consumo Diesel (l/h)], FILTER(ALLSELECTED(d_calendar), d_calendar[ANO_SEMANA] = vSemana))
VAR vMaxAbast = CALCULATE(MAX(f_abastecimento[DT_OPERACAO]))
VAR vMaxFiltro = CALCULATE(MAX(d_calendar[DATA]), ALLSELECTED(d_calendar))
VAR vMaxData = MIN(vMaxAbast, vMaxFiltro)
VAR vSemana = CALCULATE(SELECTEDVALUE(d_calendar[ANO_SEMANA]), FILTER(ALL(d_calendar), d_calendar[DATA] = vMaxData))
RETURN
CALCULATE(
    [Consumo Diesel (l/h)],
    FILTER(ALLSELECTED(d_calendar), d_calendar[ANO_SEMANA] = vSemana)
)
```
### medidas.Consumo Diesel Mês (l/h)
```dax

VAR vMaxAbast = CALCULATE(MAX(f_abastecimento[DT_OPERACAO]))
VAR vMaxFiltro = CALCULATE(MAX(d_calendar[DATA]), ALLSELECTED(d_calendar))
VAR vMaxData = MIN(vMaxAbast, vMaxFiltro)
VAR vMes = CALCULATE(SELECTEDVALUE(d_calendar[FIM_MES_ANO]), FILTER(ALL(d_calendar), d_calendar[DATA] = vMaxData))
RETURN
CALCULATE(
    [Consumo Diesel (l/h)],
    FILTER(ALLSELECTED(d_calendar), d_calendar[FIM_MES_ANO] = vMes)
)
```
### medidas.Padrão Orçado (l/h_km/l)
```dax

CALCULATE(
    AVERAGE(d_equipamentos[MD_CONSUMO])
)
```
### medidas.Consumo Diesel Att. (L/H)
```dax

VAR vPeriodo = SELECTEDVALUE(d_periodo[Período],"SAFRA")
RETURN
DIVIDE(
    SWITCH(TRUE()
        ,vPeriodo = "SEMANA", [Consumo Diesel Semana (l/h)]
        ,vPeriodo = "MÊS", [Consumo Diesel Mês (l/h)]
        ,vPeriodo = "SAFRA", [Consumo Diesel (l/h)]
    )
    ,[Padrão Orçado (l/h_km/l)]
)
```
### medidas.Consumo MAX Gráfico (l/h)
```dax
MAX([Consumo Diesel (l/h)],[Padrão Orçado (l/h_km/l)])*1.2
```
### medidas.Consumos Diesel Cor
```dax

IF([Unidade Medida Upper]="(km/l)"
    ,IF([Consumo Diesel Att. (L/H)]>1,"#187518","#870000")
    ,IF([Consumo Diesel Att. (L/H)]>1,"#870000","#187518")
)
```
### medidas.Unidade Medida
```dax

VAR vUnidade =
FIRSTNONBLANK(f_abastecimento[CD_UNIMED],"h")
RETURN
LOWER(
    IF(
        vUnidade="h"
        ,"(l/"&vUnidade&")"
        ,"("&vUnidade&"/l)"
    )
)
```
### medidas.Unidade Medida Upper
```dax

UPPER([Unidade Medida])
```
### medidas.Diesel Volume Meta (l)
```dax

VAR __baseeqp =
SUMX(
    ADDCOLUMNS(
        ADDCOLUMNS(
            d_calendar_metas
            ,"META_MES"
            ,CALCULATE(
                SUM(d_orcamento_diesel[Valor])
                ,USERELATIONSHIP(d_equipamentos[CD_CCUSTO],d_orcamento_diesel[C Custo])
            )
        )
        ,"META_DIA"
        ,DIVIDE(
            [META_MES]
            ,DAY([FIM_MES_ANO])
        )
    )
    ,[META_DIA]
)
VAR __basecc =
SUMX(
    ADDCOLUMNS(
        ADDCOLUMNS(
            d_calendar_metas
            ,"META_MES"
            ,CALCULATE(
                SUM(d_orcamento_diesel[Valor])
            )
        )
        ,"META_DIA"
        ,DIVIDE(
            [META_MES]
            ,DAY([FIM_MES_ANO])
        )
    )
    ,[META_DIA]
)
RETURN
IF(
    SELECTEDVALUE(d_base_calc[Cod],1)=2
    ,__basecc
    ,__baseeqp
)
```
### medidas.Diesel MAX Gráfico (l)
```dax
MAX([Diesel Volume (l)],[Diesel Volume Meta (l)])*1.2
```
### medidas.Diesel Volume Cor
```dax

IF([Diesel Volume (l)]>[Diesel Volume Meta (l)],"#870000","#187518")
```
### medidas.Diesel Volume ST
```dax

VAR vReal = COALESCE([Diesel Volume (l)],0)
VAR vMeta = COALESCE([Diesel Volume Meta (l)],0)
VAR vPerc =
DIVIDE(
    vReal
    ,vMeta
    ,1
)
VAR vVariacao = vReal-vMeta
VAR vIcon = IF(vVariacao<=0,"✅","⛔")
RETURN
"PERÍODO: "&FORMAT(vReal,"#,##0")&" de "&FORMAT(vMeta,"#,##0")&" | "&FORMAT(vPerc,"0.0%")&" | Var. "&FORMAT(vVariacao,"#,##0")&" "&vIcon
```
### medidas.Tempo Distancia Meta (h/km)
```dax

VAR __basecc = 
SUMX(
    ADDCOLUMNS(
        ADDCOLUMNS(
            d_calendar_metas
            ,"META_MES"
            ,CALCULATE(
                SUM(d_orcamento_km_h[Valor])
            )
        )
        ,"META_DIA"
        ,DIVIDE(
            [META_MES]
            ,DAY([FIM_MES_ANO])
        )
    )
    ,[META_DIA]
)
VAR __baseeqp = 
SUMX(
    ADDCOLUMNS(
        ADDCOLUMNS(
            d_calendar_metas
            ,"META_MES"
            ,CALCULATE(
                SUM(d_orcamento_km_h[Valor])
                ,USERELATIONSHIP(d_equipamentos_sistema[CD_CCUSTO],d_orcamento_km_h[C Custo])
            )
        )
        ,"META_DIA"
        ,DIVIDE(
            [META_MES]
            ,DAY([FIM_MES_ANO])
        )
    )
    ,[META_DIA]
)
RETURN
IF(
    SELECTEDVALUE(d_base_calc[Cod],1)=2
    ,__basecc
    ,__baseeqp
)
```
### medidas.Tempo Distancia ST
```dax

VAR vReal = COALESCE([Tempo Distancia 2 (h/km)],0)
VAR vMeta = COALESCE([Tempo Distancia Meta (h/km)],0)
VAR vPerc =
DIVIDE(
    vReal
    ,vMeta
    ,1
)
VAR vVariacao = vReal-vMeta
VAR vIcon = IF(vVariacao<=0,"✅","⛔")
RETURN
"PERÍODO: "&FORMAT(vReal,"#,##0")&" de "&FORMAT(vMeta,"#,##0")&" | "&FORMAT(vPerc,"0.0%")&" | Var. "&FORMAT(vVariacao,"#,##0")&" "&vIcon
```
### medidas.Tempo Distancia Cor
```dax

IF([Tempo Distancia 2 (h/km)]>[Tempo Distancia Meta (h/km)],"#870000","#187518")
```
### medidas.Tempo Distancia MAX
```dax

MAX([Tempo Distancia 2 (h/km)],[Tempo Distancia Meta (h/km)])*1.2
```
### medidas.Tempo Distancia 2 (h/km)
```dax

CALCULATE(
    CALCULATE(
        SUM(f_abastecimento[HORA_KM])
        ,FILTER(ADDCOLUMNS(f_abastecimento,"maxAbastecimento",CALCULATE(MAX(f_abastecimento[DT_OPERACAO]),FILTER(f_abastecimento,f_abastecimento[LITROS]>0)))
            ,[DT_OPERACAO]<=[maxAbastecimento]
        )
        ,USERELATIONSHIP(d_meta_frente[CD_FREN_TRAN],d_equipamentos[CD_FREN_TRAN])
    )
    ,FILTER(
        ADDCOLUMNS(
            ADDCOLUMNS(f_abastecimento
                ,"EQPS"
                ,VAR vEqp = f_abastecimento[CD_EQUIPTO]
                RETURN
                CALCULATE(
                    COUNTROWS(d_equipamentos)
                    ,FILTER(d_equipamentos
                        ,[CD_EQUIPTO]=vEqp
                        &&[DATA.1]>0
                    )
                )
            )
            ,"IGNORAR"
            ,IF([DT_OPERACAO]>=MIN(d_equipamentos[DATA.1])&&[DT_OPERACAO]<=MAX(d_equipamentos[DATA.2])&&[EQPS]>0,1,0)
        )
        ,[IGNORAR]=0
    )
)
```
### medidas.Disponibilidade Média (%) Dia
```dax

CALCULATE(
    [Disponibilidade Média (%)]
    ,CROSSFILTER(d_data_hora[FECHAMENTO],d_calendar[DATA],None)
    ,USERELATIONSHIP(d_data_hora[Date],d_calendar[DATA]))
```
### medidas.Equipamentos Falharam
```dax

CALCULATE(
    DISTINCTCOUNT(f_manfro[CD_EQUIPTO]),
    FILTER(
        f_manfro,
        f_manfro[HORA_INICIAL] > 0
    ),
    FILTER(
        d_criterio_disponibilidade,
        d_criterio_disponibilidade[COD_CLASS]=1
    )
    ,USERELATIONSHIP(f_manfro[HORA_INICIAL],d_data_hora[DATA_HORA])
)
```
### medidas.Reparos Emergenciais
```dax

CALCULATE(
    COUNT(f_manfro[CD_EQUIPTO]),
    FILTER(
        f_manfro,
        f_manfro[HORA_INICIAL] > 0
    ),
    FILTER(
        d_criterio_disponibilidade,
        d_criterio_disponibilidade[COD_CLASS] in {1,5,6}
    )
    ,USERELATIONSHIP(f_manfro[DATA_OS],d_calendar[DATA])
)
```
### medidas.Downtime (%)
```dax
1-[Disponibilidade Média (%)]
```
### medidas.Ocorrências
```dax

CALCULATE(
    COUNT(f_manfro[CD_EQUIPTO]),
    FILTER(
        f_manfro,
        f_manfro[HORA_INICIAL] > 0
    )
    ,USERELATIONSHIP(f_manfro[HORA_INICIAL],d_data_hora[DATA_HORA])
)
```
### medidas.Tempo Calendário (h)
```dax

DISTINCTCOUNT(d_calendar[DATA]) * 24
*DISTINCTCOUNT(d_equipamentos[CD_EQUIPTO])
```
### medidas.Tempo Manutenção (h)
```dax

CALCULATE(
    SUMX(
        ADDCOLUMNS(
            f_manfro
            ,"TEMPO"
            ,DATEDIFF(f_manfro[INICIAL],f_manfro[FINAL],SECOND)
        )
        ,[TEMPO]/(60*60)
    )
    ,USERELATIONSHIP(d_calendar[DATA],f_manfro[DATA_OS])
)
```
### medidas.Tempo Manutenção Não Planejado (h)
```dax

CALCULATE(
    SUMX(
        ADDCOLUMNS(
            f_manfro
            ,"TEMPO"
            ,DATEDIFF(f_manfro[INICIAL],f_manfro[FINAL],HOUR)
        )
        ,[TEMPO]
    )
    ,FILTER(
        d_criterio_disponibilidade
        ,[COD_CLASS]=1
    )
    ,USERELATIONSHIP(d_calendar[DATA],f_manfro[DATA_OS])
)
```
### medidas.Tempo Manutenção Planejado (h)
```dax

CALCULATE(
    SUMX(
        ADDCOLUMNS(
            f_manfro
            ,"TEMPO"
            ,DATEDIFF(f_manfro[INICIAL],f_manfro[FINAL],HOUR)
        )
        ,[TEMPO]
    )
    ,FILTER(
        d_criterio_disponibilidade
        ,[COD_CLASS]<>1
    )
    ,USERELATIONSHIP(d_calendar[DATA],f_manfro[DATA_OS])
)
```
### medidas.MTBF
```dax

CALCULATE(
    DIVIDE(
        [Tempo Calendário (h)]-[Tempo Manutenção (h)]
        ,[Reparos Emergenciais]
    )
    ,FILTER(
        d_criterio_disponibilidade
        ,[COD_CLASS] in {1,5,6}
    )
)
```
### medidas.MTTR
```dax

CALCULATE(
    AVERAGEX(
        ADDCOLUMNS(
            f_manfro
            ,"TEMPO"
            ,DATEDIFF(f_manfro[INICIAL],f_manfro[FINAL],SECOND)
        )
        ,[TEMPO]/(60*60)
    )
    ,FILTER(
        d_criterio_disponibilidade
        ,[COD_CLASS] in {1,5,6}
    )
    ,USERELATIONSHIP(d_calendar[DATA],f_manfro[DATA_OS])
)
```
### medidas.Ordens Em Aberto
```dax

CALCULATE(
    COUNT(f_manfro[CD_EQUIPTO]),
    FILTER(
        f_manfro,
        f_manfro[HORA_INICIAL] > 0
        &&[STATUS]="Andamento"
        &&[COD_CLASS] in {1,5,6}
    )
)
```
### medidas.Aproveitamento Mecânico Dia (%)
```dax

VAR DIAS_DISPONIVEIS = 
    CALCULATE(
        DISTINCTCOUNT(d_equipamentos[CD_EQUIPTO]),
        ALLSELECTED(d_calendar)
    )

VAR DIAS = 
    CALCULATE(
        DISTINCTCOUNT(f_manfro[CD_EQUIPTO]),
        FILTER(
            f_manfro,
            f_manfro[DATA_INICIAL] < MAX(d_calendar[DATA]) &&
            f_manfro[DATA_INICIAL] > 0 &&
            f_manfro[DATA_FINAL] > MAX(d_calendar[DATA])
        ),
        FILTER(
            d_criterio_disponibilidade,
            d_criterio_disponibilidade[Considerar] = "S"
        )
    )

VAR DIAS_INICIAL = 
    CALCULATE(
        DISTINCTCOUNT(f_manfro[CD_EQUIPTO]) - SUM(f_manfro[DESCONTO_DIA]),
        FILTER(
            f_manfro,
            f_manfro[DATA_INICIAL] = MAX(d_calendar[DATA]) &&
            f_manfro[DATA_INICIAL] > 0 &&
            f_manfro[DATA_FINAL] > MAX(d_calendar[DATA])
        ),
        FILTER(
            d_criterio_disponibilidade,
            d_criterio_disponibilidade[Considerar] = "S"
        )
    )

VAR DIAS_FINAL = 
    CALCULATE(
        SUM(f_manfro[ACRESCIMO_DIA]),
        FILTER(
            f_manfro,
            f_manfro[DATA_INICIAL] < MAX(d_calendar[DATA]) &&
            f_manfro[DATA_INICIAL] > 0 &&
            f_manfro[DATA_FINAL] = MAX(d_calendar[DATA])
        ),
        FILTER(
            d_criterio_disponibilidade,
            d_criterio_disponibilidade[Considerar] = "S"
        )
    )

VAR DIAS_ENTRE = 
    CALCULATE(
        SUMX(f_manfro, f_manfro[ACRESCIMO_DIA] - f_manfro[DESCONTO_DIA]),
        FILTER(
            f_manfro,
            f_manfro[DATA_INICIAL] = MAX(d_calendar[DATA]) &&
            f_manfro[DATA_FINAL] = MAX(d_calendar[DATA])
        ),
        FILTER(
            d_criterio_disponibilidade,
            d_criterio_disponibilidade[Considerar] = "S"
        )
    )

VAR TOTAL_DIAS = DIAS + DIAS_INICIAL + DIAS_FINAL + DIAS_ENTRE

RETURN
    AVERAGEX(
        d_calendar,
        1 - DIVIDE(TOTAL_DIAS, DIAS_DISPONIVEIS)
    )

```
### medidas.Disponibilidade Hora (%)
```dax

CALCULATE(
        AVERAGEX(
            ADDCOLUMNS(d_data_hora
                ,"DISPONIBILIDADE"
                ,[Disponibilidade (%)]
            )
            ,MAX([DISPONIBILIDADE],0)
        )
        ,USERELATIONSHIP(d_data_hora[FECHAMENTO],d_calendar[DATA])
        ,FILTER(d_data_hora
            ,[FILTRO_ANTES_AGORA]=1
        )
    )
```
### medidas.Orçamento R$
```dax

SUM(d_orcamento_reais[Valor])
```
### medidas.Saldo R$
```dax

[Orçamento R$ EQP]-[Valor Total Aplicado]
```
### medidas.MaxOrçado
```dax
MAX([Orçamento R$],[Valor Total Aplicado])*1.1
```
### medidas.CRM
```dax

DIVIDE(
    [Valor Total Aplicado]
    ,[Tempo Distancia (h/km)]
)
```
### medidas.CRM Orçado
```dax

DIVIDE(
    [Orçamento R$ EQP]
    ,[Orçamento KM EQP]
    ,0
)
```
### medidas.CRM Delta
```dax

[CRM Orçado]-[CRM]
```
### medidas.Orçamento R$ EQP
```dax

SUMX(
    ADDCOLUMNS(
        d_equipamentos_sistema
        ,"VALOR"
        ,VAR __ccusto = TRIM([CD_CCUSTO])
        RETURN
        CALCULATE(
            SUM(d_orcamento_reais[Valor])
            ,FILTER(
                d_orcamento_reais
                ,TRIM([Cód.])=__ccusto
            )
        )
    )
    ,DIVIDE([VALOR],[QTD_EQP])
)
```
### medidas.Orçamento KM EQP
```dax

SUMX(
    ADDCOLUMNS(
        d_equipamentos
        ,"VALOR"
        ,VAR __ccusto = TRIM([CCUSTO_SIS])
        RETURN
        CALCULATE(
            SUM(d_orcamento_km_h[Valor])
            ,FILTER(
                d_orcamento_km_h
                ,TRIM(d_orcamento_km_h[C Custo])=__ccusto
            )
        )
    )
    ,DIVIDE([VALOR],[QTD_EQP])
)
```
### d_equipamentos.Equipamentos Ativos
```dax
VAR Equip = SELECTEDVALUE(d_equipamentos[CD_EQUIPTO])
VAR DiasSelecionados = VALUES(d_calendar[DATA])
VAR DiasAtivos =
    SUMX(
        DiasSelecionados,
        VAR Dia = d_calendar[DATA]
        VAR DiaIgnorado =
            CALCULATE(
                COUNTROWS(d_datas_ignorar),
                FILTER(
                    ALL(d_datas_ignorar),
                    d_datas_ignorar[CD_EQUIPTO] = Equip
                        && Dia >= d_datas_ignorar[DATA.1]
                        && Dia <= d_datas_ignorar[DATA.2]
                )
            )
        RETURN IF(DiaIgnorado > 0, 0, 1)
    )
RETURN
IF(
    ISBLANK(Equip),
    1,
    IF(DiasAtivos > 0, 1, 0)
)
```
### medidas.Destaque Letra Frota Cor
```dax
IF (
    CONTAINS(
        d_datas_ignorar,
        d_datas_ignorar[CD_EQUIPTO],
        SELECTEDVALUE('d_equipamentos'[CD_EQUIPTO])
    ),
    "#FFFFFF",
    "#252423"
)
```

## COLUNAS CALCULADAS (79)

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
### d_criterio_disponibilidade.Gera Indisponibilidade
```dax

IF([Considerar]="N","Não Gera Indisponibilidade","Gera Indisponibilidade")
```
### f_manfro.TEMPO_TOTAL_PARADO
```dax

VAR AGORA =
MAX(f_atualizado[AGORA5])
RETURN
COALESCE([SAIDA],AGORA)-COALESCE([INICIO_ANDAMENTO],[ENTRADA])
```
### f_manfro.TEXTO
```dax

VAR FRT = 
RELATED(d_equipamentos[FRENTE])
VAR DIAS =
ROUNDDOWN([TEMPO_TOTAL_PARADO],0)
VAR HORAS =
ROUNDDOWN(([TEMPO_TOTAL_PARADO]-DIAS)*24,0)
VAR MINUTOS =
ROUNDDOWN((([TEMPO_TOTAL_PARADO]-DIAS)*24-HORAS)*60,0)
VAR TEMPO =
IF(DIAS>0,DIAS&"d ")
&HORAS&"h"&MINUTOS&"m"
VAR TEXTO_QRM =
TRIM(LEFT([SERVICO],23))
VAR QRM_MOTIVO =
UPPER(IF(TEXTO_QRM="",[DE_MOTENTR],TEXTO_QRM))
RETURN
IF([STATUS]="Andamento",
    FRT&" | "&[CD_EQUIPTO]&" | "&QRM_MOTIVO&" | "&TEMPO
)
```
### f_manfro.INICIAL
```dax

VAR CALCULO =
RELATED(d_criterio_disponibilidade[Cálculo])
RETURN
IF(CALCULO=1,[ENTRADA],[INICIO_ANDAMENTO])
```
### f_manfro.FINAL
```dax

VAR AGORA = 
MAX(f_atualizado[AGORA5])
RETURN
COALESCE(
    [SAIDA]
    ,AGORA
)
```
### f_manfro.DESCONTO_INICIAL
```dax

DIVIDE(
    MINUTE([INICIAL])
    ,60
)
+DIVIDE(
    SECOND([INICIAL])
    ,60*60
)
```
### f_manfro.ACRESCIMO_FINAL
```dax

DIVIDE(
    MINUTE([FINAL])
    ,60
)
+
DIVIDE(
    SECOND([FINAL])
    ,60*60
)
```
### f_manfro.HORA_INICIAL
```dax
[INICIAL]-[DESCONTO_INICIAL]/24
```
### f_manfro.HORA_FINAL
```dax
[FINAL]-[ACRESCIMO_FINAL]/24
```
### f_manfro.TEXTO_2
```dax

VAR FRT = 
RELATED(d_equipamentos[FRENTE])
VAR DIAS =
ROUNDDOWN([TEMPO_TOTAL_PARADO],0)
VAR HORAS =
ROUNDDOWN(([TEMPO_TOTAL_PARADO]-DIAS)*24,0)
VAR MINUTOS =
ROUNDDOWN((([TEMPO_TOTAL_PARADO]-DIAS)*24-HORAS)*60,0)
VAR TEMPO =
IF(DIAS>0,DIAS&"d ")
&HORAS&"h"&MINUTOS&"m"
VAR TEXTO_QRM =
TRIM(LEFT([SERVICO],70))
VAR QRM_MOTIVO =
UPPER(IF(TEXTO_QRM="",[DE_MOTENTR],TEXTO_QRM))
RETURN
SUBSTITUTE(
    IF([STATUS]="Andamento",
        [BOLETIM]&" | "&FRT&" | "&[CD_EQUIPTO]&" | "&QRM_MOTIVO&" | "&TEMPO
    )
    ,"
"
    ,""
)
```
### f_manfro.CATEGORIA_2
```dax
COALESCE(
    RELATED(d_equipamentos[CATEGORIA])
    ,"Outros"
    )
```
### d_equipamentos.CATEGORIA_2
```dax
COALESCE(
    [CATEGORIA]
    ,"Outros"
    )
```
### d_equipamentos.GRUPO_2
```dax
COALESCE(
    [GRUPO]
    ,"Outros"
    )
```
### d_equipamentos.FRENTE_UP
```dax

IF(
    UPPER([FRENTE]) = ""
    ,"SEM FRENTE"
    ,UPPER([FRENTE])
)
```
### d_equipamentos.PROCESSO_2
```dax
COALESCE(
    UPPER([PROCESSO])
    ,"OUTRO"
    )
```
### f_ordem_compra.CHAVE_DOC_APROV
```dax
FORMAT([NUM_DOCERP],"00000000")&[SEQUENCIA]&IF(LEN([SEQUENCIA])>2,""," ")&[CD_MATERIAL]
```
### f_ordem_compra.BOLETIM_MANFRO_TEXTO
```dax
UPPER([NO_BOLETIM])
```
### f_ordem_compra.DT_APROVA_PEDIDO_1
```dax

VAR vChave = [CHAVE_DOC_APROV]
VAR vSC = [NUM_DOCERP]
VAR vPC = [PEDIDO]
RETURN
CALCULATE(
    MAXX(f_pend_aprov,[DT_APROVA]+[HORA_APROVACAO])
    ,FILTER(f_pend_aprov
        ,f_pend_aprov[CHAVE_DOC]=vPC
        &&[SEQ_APROV] = 1
    )
)
```
### f_ordem_compra.DT_APROVA_PEDIDO_2
```dax

VAR vChave = [CHAVE_DOC_APROV]
VAR vSC = [NUM_DOCERP]
VAR vPC = [PEDIDO]
RETURN
CALCULATE(
    MAXX(f_pend_aprov,[DT_APROVA]+[HORA_APROVACAO])
    ,FILTER(f_pend_aprov
        ,f_pend_aprov[CHAVE_DOC]=vPC
        &&[SEQ_APROV] = 2
    )
)
```
### f_ordem_compra.DT_APROVA_REQUISIÇÃO
```dax

VAR vChave = [CHAVE_DOC_APROV]
VAR vSC = [NUM_DOCERP]
VAR vPC = [PEDIDO]
RETURN
CALCULATE(
    MAXX(f_pend_aprov,[DT_APROVA]+[HORA_APROVACAO])
    ,FILTER(f_pend_aprov
        ,([CHAVE_DOC]=vChave || [CHAVE_DOC]=vSC)
        &&[SEQ_APROV] = 1
    )
)
```
### f_ordem_compra.DT_GERACAO_PEDIDO_1
```dax

VAR vChave = [CHAVE_DOC_APROV]
VAR vSC = [NUM_DOCERP]
VAR vPC = [PEDIDO]
RETURN
CALCULATE(
    MAXX(f_pend_aprov,[DT_GERACAO]+[HORA_GERACAO])
    ,FILTER(f_pend_aprov
        ,f_pend_aprov[CHAVE_DOC]=vPC
        &&[SEQ_APROV] = 1
    )
)
```
### f_ordem_compra.DT_GERACAO_PEDIDO_2
```dax

VAR vChave = [CHAVE_DOC_APROV]
VAR vSC = [NUM_DOCERP]
VAR vPC = [PEDIDO]
RETURN
CALCULATE(
    MAXX(f_pend_aprov,[DT_GERACAO]+[HORA_GERACAO])
    ,FILTER(f_pend_aprov
        ,f_pend_aprov[CHAVE_DOC]=vPC
        &&[SEQ_APROV] = 2
    )
)
```
### f_ordem_compra.DT_GERACAO_REQUISIÇÃO
```dax

VAR vChave = [CHAVE_DOC_APROV]
VAR vSC = [NUM_DOCERP]
VAR vPC = [PEDIDO]
RETURN
    CALCULATE(
        MAXX(f_pend_aprov,[DT_GERACAO]+[HORA_GERACAO])
        ,FILTER(f_pend_aprov
            ,([CHAVE_DOC]=vChave || [CHAVE_DOC]=vSC)
        )
    )
```
### d_equipamentos.EQUIPAMENTO_TEXTO
```dax
UPPER([CD_EQUIPTO])
```
### f_manfro.BOLETIM_TEXTO
```dax
UPPER([BOLETIM])
```
### f_ordem_compra.DATA_ENVIO_AJUSTE
```dax

DATE(YEAR([DT_ENVIO]),MONTH([DT_ENVIO]),DAY([DT_ENVIO]))
```
### f_ordem_compra.STATUS_REQ_AJUSTE
```dax

SWITCH(TRUE()
    ,[FG_STATUS_ERP]<>BLANK() && [FG_STATUS_ERP]<>"",[FG_STATUS_ERP]
    ,[PEDIDO]<>"","PE"
    ,"SO"
)
```
### f_ordem_compra.DATA_RECEBIMENTO
```dax

VAR vOrdem = [NUMERO_ORDEM]
VAR vItem = [CD_MATERIAL]
RETURN
CALCULATE(
    MAX(f_recebimento[DATA_MOVTO])
    ,FILTER(f_recebimento
        ,[NUMERO_ORDEM]=vOrdem
        &&[IT_CODIGO]=vItem
    )
)
```
### f_ordem_compra.DATA_FATURAMENTO
```dax

VAR vOrdem = [NUMERO_ORDEM]
VAR vItem = [CD_MATERIAL]
RETURN
CALCULATE(
    MAX(f_recebimento[DATA_NOTA])
    ,FILTER(f_recebimento
        ,[NUMERO_ORDEM]=vOrdem
        &&[IT_CODIGO]=vItem
    )
)
```
### f_ordem_compra.STATUS REQUISICAO
```dax

SWITCH(TRUE()
    ,[DATA_RECEBIMENTO]<>BLANK(),"RECEBIDO"
    ,[DT_APROVA_PEDIDO_2]<>BLANK(),"PEDIDO APROVADO"
    ,[DATA_PEDIDO]<>BLANK(),"PEDIDO GERADO"
    ,[EMISSAO_OC]<>BLANK(),"AGUARDANDO PEDIDO"
    ,"AGUARDANDO ORDEM"
)
```
### f_ordem_compra.APROVADOR_RC
```dax

VAR vChave = [CHAVE_DOC_APROV]
VAR vSC = [NUM_DOCERP]
VAR vPC = [PEDIDO]
VAR vAprovador =
COALESCE(
    CALCULATE(
        FIRSTNONBLANK(f_pend_aprov[COD_USUAR],0)
        ,FILTER(f_pend_aprov
            ,([CHAVE_DOC]=vChave || [CHAVE_DOC]=vSC)
            &&[SEQ_APROV] = 1
        )
    )
    ,CALCULATE(
        FIRSTNONBLANK(f_pend_aprov[COD_USUAR_ALTERN],0)
        ,FILTER(f_pend_aprov
            ,([CHAVE_DOC]=vChave || [CHAVE_DOC]=vSC)
            &&[SEQ_APROV] = 1
        )
    )
)
RETURN
COALESCE(
    CALCULATE(
        FIRSTNONBLANK(d_aprovadores[NOME_USUAR],0)
        ,FILTER(d_aprovadores
            ,[COD_USUAR]=vAprovador
        )
    )
    ,"SEM APROVADOR"
)
```
### f_ordem_compra.APROVADOR_PEDIDO_1
```dax

VAR vChave = [CHAVE_DOC_APROV]
VAR vSC = [NUM_DOCERP]
VAR vPC = [PEDIDO]
VAR vAprovador =
COALESCE(
    CALCULATE(
        FIRSTNONBLANK(f_pend_aprov[COD_USUAR],0)
        ,FILTER(f_pend_aprov
            ,f_pend_aprov[CHAVE_DOC]=vPC
            &&[SEQ_APROV] = 1
        )
    )
    ,CALCULATE(
        FIRSTNONBLANK(f_pend_aprov[COD_USUAR_ALTERN],0)
        ,FILTER(f_pend_aprov
            ,f_pend_aprov[CHAVE_DOC]=vPC
            &&[SEQ_APROV] = 1
        )
    )
)
RETURN
COALESCE(
    CALCULATE(
        FIRSTNONBLANK(d_aprovadores[NOME_USUAR],0)
        ,FILTER(d_aprovadores
            ,[COD_USUAR]=vAprovador
        )
    )
    ,"SEM APROVADOR"
)
```
### f_ordem_compra.APROVADOR_PEDIDO_2
```dax

VAR vChave = [CHAVE_DOC_APROV]
VAR vSC = [NUM_DOCERP]
VAR vPC = [PEDIDO]
VAR vAprovador =
COALESCE(
    CALCULATE(
        FIRSTNONBLANK(f_pend_aprov[COD_USUAR],0)
        ,FILTER(f_pend_aprov
            ,f_pend_aprov[CHAVE_DOC]=vPC
            &&[SEQ_APROV] = 2
        )
    )
    ,CALCULATE(
        FIRSTNONBLANK(f_pend_aprov[COD_USUAR_ALTERN],0)
        ,FILTER(f_pend_aprov
            ,f_pend_aprov[CHAVE_DOC]=vPC
            &&[SEQ_APROV] = 2
        )
    )
)
RETURN
COALESCE(
    CALCULATE(
        FIRSTNONBLANK(d_aprovadores[NOME_USUAR],0)
        ,FILTER(d_aprovadores
            ,[COD_USUAR]=vAprovador
        )
    )
    ,"SEM APROVADOR"
)
```
### f_ordem_compra.COMPRADOR
```dax

VAR vCod = RIGHT([COD_COMPRADO],4)
RETURN
CALCULATE(
    FIRSTNONBLANK(d_compradores[NOME],0)
    ,FILTER(d_compradores
        ,RIGHT([COD_COMPRADO],4)=vCod
    )
)
```
### f_ordem_compra.STATUS DE ENTREGA
```dax

SWITCH(TRUE()
    ,[DATA_RECEBIMENTO]<>BLANK() && [DATA_FATURAMENTO]<=[DATA_FAT_PROMETIDA_AJUSTE],"RECEBIDO NO PRAZO"
    ,[DATA_RECEBIMENTO]<>BLANK() && [DATA_FATURAMENTO]>[DATA_FAT_PROMETIDA_AJUSTE],"RECEBIDO FORA DO PRAZO"
    ,[DATA_FAT_PROMETIDA_AJUSTE]=BLANK(),"SEM PRAZO"
    ,[DATA_RECEBIMENTO]=BLANK() && TODAY()<=[DATA_FAT_PROMETIDA_AJUSTE],"AGUARD. NO PRAZO"
    ,[DATA_RECEBIMENTO]=BLANK() && TODAY()>[DATA_FAT_PROMETIDA_AJUSTE],"AGUARD. FORA DO PRAZO"
)
```
### f_ordem_compra.DATA_FAT_PROMETIDA_AJUSTE
```dax

COALESCE([DATA_FATURAMENTO_PROMETIDA],[DATA_PREVISAO_ENTREGA])
```
### f_lubrificante.FIM_MES_ANO
```dax

EOMONTH([DT_OPERACAO],0)
```
### f_ordem_compra.EQUIPAMENTO_TEXTO
```dax
UPPER([CD_EQUIPTO])
```
### f_produtividade.FIM_MES_ANO
```dax

EOMONTH([DT_HISTORICO],0)
```
### f_abastecimento.FIM_MES_ANO
```dax

EOMONTH([DT_OPERACAO],0)
```
### d_equipamentos.CD_FREN_TRAN
```dax

    SWITCH(
        TRUE(),
        d_equipamentos[FRENTE_UP] = "FRENTE 1", "1",
        d_equipamentos[FRENTE_UP] = "FRENTE 2", "2",
        d_equipamentos[FRENTE_UP] = "FRENTE 3", "3",
        d_equipamentos[FRENTE_UP] = "FRENTE 4", "4",
        d_equipamentos[FRENTE_UP] = "FRENTE 5", "5",
        BLANK()
    )

```
### f_abastecimento.CATEGORIA
```dax
RELATED(d_equipamentos[CATEGORIA])
```
### d_equipamentos.CATEGORIA_M
```dax
UPPER(d_equipamentos[CATEGORIA_2])
```
### f_ordem_compra.DATA_CHEGADA_ESPERADA
```dax
RELATED(d_transportadoras[DIAS])+[DATA_FATURAMENTO_PROMETIDA]
```
### d_emitente.LEADTIME_TRANSP_EMITENTE
```dax

ROUNDUP(
    CALCULATE(
        AVERAGEX(
            f_recebimento
            ,MAX([DATA_MOVTO]-[DATA_NOTA],0)
        )
    )
    ,0
)
```
### d_emitente.LEADTIME_CIDADE
```dax

VAR vCidade = [CIDADE]
VAR vQ2 =
CALCULATE(
    PERCENTILE.INC(d_emitente[LEADTIME_TRANSP_EMITENTE],0.1)
    ,FILTER(
        d_emitente
        ,[CIDADE]=vCidade
        &&[LEADTIME_TRANSP_EMITENTE] >0
    )
)
VAR vQ3 =
CALCULATE(
    PERCENTILE.INC(d_emitente[LEADTIME_TRANSP_EMITENTE],0.9)
    ,FILTER(
        d_emitente
        ,[CIDADE]=vCidade
        &&[LEADTIME_TRANSP_EMITENTE] >0
    )
)
RETURN
CALCULATE(
    AVERAGE(d_emitente[LEADTIME_TRANSP_EMITENTE])
    ,FILTER(
        d_emitente
        ,[CIDADE]=vCidade
        &&[LEADTIME_TRANSP_EMITENTE] >= vQ2
        &&[LEADTIME_TRANSP_EMITENTE] <= vQ3
    )
)
```
### f_tch.FIM_MES
```dax
EOMONTH([DT_FECHEMENTO],0)
```
### d_calendar.SEMANA_PIMS
```dax

VAR vData = [DATA]
RETURN
SWITCH(TRUE()
    ,[DATA]>=DATE(2024,12,29),"S-"&FORMAT(WEEKNUM(vData,1),"00")
    ,"S-"&FORMAT(WEEKNUM(vData,1),"00")
)
```
### d_equipamentos.DATA.1
```dax

CALCULATE(
    MIN(d_datas_ignorar[DATA.1])
)
```
### d_equipamentos.DATA.2
```dax

CALCULATE(
    MIN(d_datas_ignorar[DATA.2])
)
```
### d_equipamentos.FRT
```dax
SUBSTITUTE([FRENTE_UP],"FRENTE ","F-")
```
### d_equipamentos.CONSUMO DIESEL
```dax

VAR vEquipto = [CD_EQUIPTO]
RETURN
IF(
    CALCULATE(
        SUM(f_abastecimento[LITROS])
        ,FILTER(f_abastecimento
            ,[CD_MATERIAL] IN {89500,89838,104542}
            &&[CD_EQUIPTO] = vEquipto
        )
    )>0
    ,"SIM"
    ,"NÃO"
)
```
### f_abastecimento.META_CONSUMO
```dax
"META: "&FORMAT([MD_CONSUMO],"0")
```
### d_equipamentos.META_CONSUMO
```dax
"META: "&FORMAT(CALCULATE(MAX(f_abastecimento[MD_CONSUMO])),"0.00")
```
### d_equipamentos.MD_CONSUMO
```dax
CALCULATE(MAX(f_abastecimento[MD_CONSUMO]))
```
### d_equipamentos.GRUPO EQP
```dax

SWITCH(TRUE()
    ,FIND("CM",[CATEGORIA_M],1,0)>0,"CAMINHÕES"
    ,FIND("PRANCHA",[CATEGORIA_M],1,0)>0,"CAMINHÕES"
    ,FIND("TRATOR",[CATEGORIA_M],1,0)>0,"TRATORES"
    ,FIND("UNIPORT",[CATEGORIA_M],1,0)>0,"UNIPORT HERBIC"
    ,FIND("MOTOBOMBA",[CATEGORIA_M],1,0)>0,"MOTOBOMBA"
    ,FIND("LEVES",[CATEGORIA_M],1,0)>0,"VEICULOS LEVES"
    ,FIND("PÁ CARREGADEIRA",[CATEGORIA_M],1,0)>0,"PÁ CARREGADEIRA"
    ,[CATEGORIA_M]
)   
```
### f_manfro.ORIGEM
```dax

SWITCH(
    TRUE()
    ,[ORIGEM_OS]="C","Campo"
    ,[ORIGEM_OS]="I","Interna"
    ,[ORIGEM_OS]="T","Terceiro"
    ,"Outro")
```
### f_manfro.DATA_OS
```dax
DATE(YEAR([ENTRADA]),MONTH([ENTRADA]),DAY([ENTRADA]))
```
### d_criterio_disponibilidade.CLASSE
```dax

SUBSTITUTE([Descrição],"Manutenção ","")
```
### f_manfro.DATA_INICIAL
```dax
ROUNDDOWN([INICIAL]-MAX(d_inicio_turno[HORA_INICIAL])/24,0)
```
### f_manfro.DATA_FINAL
```dax
ROUNDDOWN([FINAL]-MAX(d_inicio_turno[HORA_INICIAL])/24,0)
```
### f_manfro.DESCONTO_DIA
```dax

ROUND(
    DIVIDE(
        HOUR([INICIAL]-MAX(d_inicio_turno[HORA_INICIAL])/24)
        ,24
    )
    +DIVIDE(
        MINUTE([INICIAL])
        ,24*60
    )
    +DIVIDE(
        SECOND([INICIAL])
        ,24*60*60
    )
    ,4
)
```
### f_manfro.ACRESCIMO_DIA
```dax

ROUND(
    DIVIDE(
        HOUR([FINAL]-MAX(d_inicio_turno[HORA_INICIAL])/24)
        ,24
    )
    +
    DIVIDE(
        MINUTE([FINAL])
        ,24*60
    )
    +
    DIVIDE(
        SECOND([FINAL])
        ,24*60*60
    )
    ,4
)
```
### d_funcionario.FUNC
```dax
UPPER([CD_FUNC])&" - "&[NOME_.1]
```
### d_orcamento_reais.INICIO_MES
```dax

VAR __ano = 2025
RETURN
VALUE(1&"/"&[Atributo]&"/"&IF([Atributo] IN {"JAN","FEV","MAR"}, __ano+1,__ano))
```
### d_equipamentos_sistema.CENTRO DE CUSTO
```dax
UPPER([CD_CCUSTO])
```
### d_equipamentos_sistema.QTD_EQP
```dax

VAR __ccusto = [CENTRO DE CUSTO]
RETURN
COUNTROWS(
    FILTER(d_equipamentos_sistema
        ,[CENTRO DE CUSTO]=__ccusto
    )
)
```
### d_equipamentos.CCUSTO_SIS
```dax
RELATED(d_equipamentos_sistema[CENTRO DE CUSTO])
```
### d_equipamentos.QTD_EQP
```dax

VAR __ccusto = [CCUSTO_SIS]
RETURN
COUNTROWS(
    FILTER(d_equipamentos
        ,[CCUSTO_SIS]=__ccusto
    )
)
```
### d_equipamentos.DE_CCUSTO
```dax
RELATED(d_equipamentos_sistema[DE_CCUSTO])
```
### f_ordem_compra.VALOR_APLICADO_AJUSTADO
```dax

[PRECO_UNIT2]*[QTD_MAT_APLICADO]
```
### f_ordem_compra.PRECO_UNIT2
```dax

VAR __ITEM = [CD_MATERIAL]
RETURN
CALCULATE(
    AVERAGE(d_preco_unit[Preço])
    ,FILTER(
        d_preco_unit
        ,[Item]=__ITEM
    )
)
```
### d_equipamentos.Grupo Equip.
```dax

VAR __ccusto = [CD_CCUSTO]
RETURN
CALCULATE(
    FIRSTNONBLANK(d_orcamento_reais[Grupo Equip.],1)
    ,FILTER(d_orcamento_reais
        ,[Cód.]=__ccusto
    )
)
```
### d_equipamentos_sistema.Grupo Equip.
```dax

VAR __ccusto = [CD_CCUSTO]
RETURN
CALCULATE(
    FIRSTNONBLANK(d_orcamento_reais[Grupo Equip.],1)
    ,FILTER(d_orcamento_reais
        ,[Cód.]=__ccusto
    )
)
```
### d_orcamento_reais.Coluna
```dax
[Orçamento R$ EQP]
```
### d_equipamentos_sistema.EQUIPAMENTO
```dax
UPPER(d_equipamentos_sistema[CD_EQUIPTO])
```

## TABELAS CALCULADAS (6)

### d_calendar.d_calendar
```dax

VAR VIRA_DIA =
IF(HOUR(MAX(f_atualizado[AGORA5]))-1<MAX(d_inicio_turno[HORA_INICIAL]),-1,0)
VAR MAXMOV = 
DATE(YEAR(MAX(f_atualizado[AGORA5]))+1,3,31)+VIRA_DIA
VAR MAXMOV2 =
DATE(YEAR(MAX(f_atualizado[AGORA5])),MONTH(MAX(f_atualizado[AGORA5])),DAY(MAX(f_atualizado[AGORA5])))+1+VIRA_DIA
RETURN
VAR DATAMIN = 
CALCULATE(
    MIN(f_manfro[ENTRADA])
    ,FILTER(f_manfro
        ,[ENTRADA]>0
    )
)
RETURN
ADDCOLUMNS (
    CALENDAR(EOMONTH(DATAMIN,-1)-1,EOMONTH(MAXMOV-1,0))
    ,"FILTRO"
    ,SWITCH(
        TRUE()
        ,[DATE]=MAXMOV2-1,1
        ,[DATE]=MAXMOV2-2,2
        ,[DATE]=MAXMOV2-3,3
        ,[DATE]=MAXMOV2-4,4
        ,[DATE]=MAXMOV2-5,5
        ,[DATE]=MAXMOV2-6,6
        ,[DATE]=MAXMOV2-7,7
        ,0
    )
    ,"FILTRO_TEXTO"
    ,SWITCH(
        TRUE()
        ,[DATE]=MAXMOV2-1,"Hoje"
        ,[DATE]=MAXMOV2-2,"D-1"
        ,[DATE]=MAXMOV2-3,FORMAT([DATE],"DD/MM/YYYY")
        ,[DATE]=MAXMOV2-4,FORMAT([DATE],"DD/MM/YYYY")
        ,[DATE]=MAXMOV2-5,FORMAT([DATE],"DD/MM/YYYY")
        ,[DATE]=MAXMOV2-6,FORMAT([DATE],"DD/MM/YYYY")
        ,[DATE]=MAXMOV2-7,FORMAT([DATE],"DD/MM/YYYY")
        ,FORMAT([DATE],"DD/MM/YYYY")
    )
    ,"EVENTOS"
    ,SWITCH(
        TRUE()
        ,[DATE]=DATAMIN,"Início Safra"
        ,""
    )
    ,"TEXTO_DATA"
    ,UPPER(FORMAT([Date],"DDD, DD/MMM"))
    ,"DATA_BRASIL"
    ,UPPER(FORMAT([Date],"DD/MM/YYYY"))
    ,"DATA_BRASIL_RESUMIDA"
    ,UPPER(FORMAT([Date],"DD/MM"))
    ,"ORDENA_DATA_BRASIL_RESUMIDA"
    ,VALUE(FORMAT([Date],"MM")&","&FORMAT([Date],"MM"))
    ,"ANO"
    ,UPPER(FORMAT([Date],"YYYY"))
    ,"MES"
    ,UPPER(FORMAT([Date],"MMM"))
    ,"MES_ANO"
    ,UPPER(FORMAT([Date],"MMM, YYYY"))
    ,"INICIO_MES_ANO"
    ,DATE(YEAR([Date]),MONTH([Date]),DAY(EOMONTH([Date],-1)+1))
    ,"FIM_MES_ANO"
    ,DATE(YEAR([Date]),MONTH([Date]),DAY(EOMONTH([Date],0)))
    ,"MES_NUM"
    ,MONTH([Date])
    ,"DIA_SEMANA"
    ,UPPER(FORMAT([Date],"DDD"))
    ,"DIA_SEMANA_COMPLETO"
    ,UPPER(FORMAT([Date],"DDDD"))
    ,"DIA_SEMANA_NUM"
    ,WEEKDAY([Date],1)
    ,"DIA_SEMANA_NUM_CORINGA"
    ,SWITCH(TRUE()
        ,WEEKDAY([Date],1)=1,"D"
        ,WEEKDAY([Date],1)=2,"S"
        ,WEEKDAY([Date],1)=3,"T"
        ,WEEKDAY([Date],1)=4,"Q"
        ,WEEKDAY([Date],1)=5,"Q "
        ,WEEKDAY([Date],1)=6,"S "
        ,WEEKDAY([Date],1)=7," S "
    )
    ,"DIA_MES"
    ,DAY([Date])
    ,"SEMANA_ANO"
    ,WEEKNUM([Date],1)
    ,"ANO_SEMANA"
    ,VALUE(FORMAT([Date],"YYYY")+(VALUE(WEEKNUM([Date],1))/100))
    ,"FILTRO_MES"
    ,IF(MONTH(MAXMOV-2)=MONTH([Date])
        ,1
        ,0
    )
)
```
### d_data_hora.d_data_hora
```dax

VAR vInicioTurno = MAX(d_inicio_turno[HORA_INICIAL])
VAR MAXMOV = DATE(YEAR(MAX(f_atualizado[AGORA5])),MONTH(MAX(f_atualizado[AGORA5])),DAY(MAX(f_atualizado[AGORA5])))+1
VAR DATAMIN = 
CALCULATE(
    MIN(f_manfro[ENTRADA])
    ,FILTER(f_manfro
        ,[ENTRADA]>0
    )
)
VAR AGORA =
MAX(f_atualizado[AGORA5])
RETURN
ADDCOLUMNS(
    CROSSJOIN(
        CALENDAR(DATAMIN,EOMONTH(MAXMOV,0))
        ,CALCULATETABLE(VALUES(d_hora[HORA]),FILTER(d_hora,[HORA]>=0))
    )
    ,"FECHAMENTO"
    ,IF(
        [HORA]<vInicioTurno
        ,[DATE]-1
        ,[DATE]
    )
    ,"FECHAMENTO_HORA"
    ,IF(
        [HORA]<vInicioTurno
        ,[DATE]-1
        ,[DATE]
    )+TIME([HORA],0,0)
    ,"DATA_HORA"
    ,[DATE]+TIME([HORA],0,0)
    ,"HORA_HORA"
    ,FORMAT(TIME([HORA],0,0),"HH:MM")&"-"&FORMAT(TIME([HORA],59,59),"HH:MM")
    ,"HORA_FECHA"
    ,IF([HORA]+1=24,0,[HORA]+1)
    ,"HR_ORDENADOR"
    ,IF([HORA]<vInicioTurno
        ,[HORA]+(24-vInicioTurno)
        ,[HORA]-vInicioTurno
    )
    ,"DATA_BRASIL"
    ,UPPER(FORMAT([Date],"DD/MM/YYYY"))
    ,"FECHAMENTO_BRASIL"
    ,UPPER(FORMAT(
        IF(
            [HORA]<vInicioTurno
            ,[DATE]-1
            ,[DATE]
        )
        ,"DD/MM/YYYY")
    )
    ,"FILTRO_10HS"
    ,IF(AND([DATE]+TIME([HORA],0,0)<=AGORA,[DATE]+TIME([HORA],0,0)>=AGORA-0.42),1,0)
    ,"FILTRO_ANTES_AGORA"
    ,IF([DATE]+TIME([HORA],0,0)+DIVIDE(1,24)<AGORA,1,0)
    ,"TURNO"
    ,SWITCH(
        TRUE()
        ,[HORA]>=7 && [HORA]<15, "A"
        ,[HORA]>=15 && [HORA]<23, "B"
        ,"C"
    )
)
```
### d_meses.d_meses
```dax
SUMMARIZECOLUMNS(d_calendar[ANO],d_calendar[MES],d_calendar[FIM_MES_ANO])
```
### d_calendar_metas.d_calendar_metas
```dax

VAR ANO_ATUAL = 2026
VAR MAXMOV = 
DATE(ANO_ATUAL+1,3,31)
VAR MAXMOV2 = 
DATE(ANO_ATUAL+1,3,31)
VAR DATAMIN = 
DATE(2024,4,1)
RETURN
ADDCOLUMNS (
    CALENDAR(DATAMIN,MAXMOV)
    ,"FILTRO"
    ,SWITCH(
        TRUE()
        ,[DATE]=MAXMOV-1,1
        ,[DATE]=MAXMOV-2,2
        ,[DATE]=MAXMOV-3,3
        ,[DATE]=MAXMOV-4,4
        ,[DATE]=MAXMOV-5,5
        ,[DATE]=MAXMOV-6,6
        ,[DATE]=MAXMOV-7,7
        ,0
    )
    ,"FILTRO_TEXTO"
    ,SWITCH(
        TRUE()
        ,[DATE]=MAXMOV2-1,"Hoje"
        ,[DATE]=MAXMOV2-2,"D-1"
        ,[DATE]=MAXMOV2-3,FORMAT([DATE],"DD/MM/YYYY")
        ,[DATE]=MAXMOV2-4,FORMAT([DATE],"DD/MM/YYYY")
        ,[DATE]=MAXMOV2-5,FORMAT([DATE],"DD/MM/YYYY")
        ,[DATE]=MAXMOV2-6,FORMAT([DATE],"DD/MM/YYYY")
        ,[DATE]=MAXMOV2-7,FORMAT([DATE],"DD/MM/YYYY")
        ,FORMAT([DATE],"DD/MM/YYYY")
    )
    ,"EVENTOS"
    ,SWITCH(
        TRUE()
        ,[DATE]=DATAMIN,"Início Safra"
        ,""
    )
    ,"TEXTO_DATA"
    ,UPPER(FORMAT([Date],"DDD, DD/MMM"))
    ,"DATA_BRASIL"
    ,UPPER(FORMAT([Date],"DD/MM/YYYY"))
    ,"DATA_BRASIL_RESUMIDA"
    ,UPPER(FORMAT([Date],"DD/MM"))
    ,"ORDENA_DATA_BRASIL_RESUMIDA"
    ,VALUE(FORMAT([Date],"MM")&","&FORMAT([Date],"MM"))
    ,"ANO"
    ,UPPER(FORMAT([Date],"YYYY"))
    ,"MES"
    ,UPPER(FORMAT([Date],"MMM"))
    ,"MES_ANO"
    ,UPPER(FORMAT([Date],"MMM, YYYY"))
    ,"INICIO_MES_ANO"
    ,DATE(YEAR([Date]),MONTH([Date]),DAY(EOMONTH([Date],-1)+1))
    ,"FIM_MES_ANO"
    ,DATE(YEAR([Date]),MONTH([Date]),DAY(EOMONTH([Date],0)))
    ,"MES_NUM"
    ,MONTH([Date])
    ,"DIA_SEMANA"
    ,UPPER(FORMAT([Date],"DDD"))
    ,"DIA_SEMANA_COMPLETO"
    ,UPPER(FORMAT([Date],"DDDD"))
    ,"DIA_SEMANA_NUM"
    ,WEEKDAY([Date],1)
    ,"DIA_SEMANA_NUM_CORINGA"
    ,SWITCH(TRUE()
        ,WEEKDAY([Date],1)=1,"D"
        ,WEEKDAY([Date],1)=2,"S"
        ,WEEKDAY([Date],1)=3,"T"
        ,WEEKDAY([Date],1)=4,"Q"
        ,WEEKDAY([Date],1)=5,"Q "
        ,WEEKDAY([Date],1)=6,"S "
        ,WEEKDAY([Date],1)=7," S "
    )
    ,"DIA_MES"
    ,DAY([Date])
    ,"SEMANA_ANO"
    ,WEEKNUM([Date],1)
    ,"ANO_SEMANA"
    ,VALUE(FORMAT([Date],"YYYY")+(VALUE(WEEKNUM([Date],1))/100))
    ,"FILTRO_MES"
    ,IF(MONTH(MAXMOV-2)=MONTH([Date])
        ,1
        ,0
    )
)
```
### Ano Safra.Ano Safra
```dax
GENERATESERIES(2019, 2026, 1)
```
### d_disponibilidade_eqp_data.d_disponibilidade_eqp_data
```dax
ADDCOLUMNS(
    FILTER(
        CROSSJOIN(
            ALL(d_equipamentos[CD_EQUIPTO]),
            CALCULATETABLE(
                ALL(d_calendar[DATA]),
                d_calendar[DATA] > DATE(2025,1,1),
                d_calendar[DATA] <= TODAY() + 1
            )
        ),
        COUNTROWS(
            FILTER(
                d_datas_ignorar,
                d_datas_ignorar[CD_EQUIPTO] = d_equipamentos[CD_EQUIPTO]
                && d_calendar[DATA] >= d_datas_ignorar[DATA.1]
                && d_calendar[DATA] <= d_datas_ignorar[DATA.2]
            )
        ) = 0
    ),
    "DISP",
    MAX([Aproveitamento Mecânico Dia (%)], 0)
)
```