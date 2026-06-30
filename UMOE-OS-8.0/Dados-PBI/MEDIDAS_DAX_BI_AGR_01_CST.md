# DAX (negocio) — BI_AGR_01_CST
Medidas: 17 | Colunas calculadas: 28 | Tabelas calculadas: 1 | Negocio: 46 | Auto date tables omitidas: 259


## MEDIDAS (17)

### FUNC_99_BI.Z_FUNC_BI_SALDO
```dax

SUM([QTDE_ORC]) - SUM([QTDE_REAL])
```
### FUNC_99_BI.Z_FUNC_BI_SALDO_ID
```dax

IF((
    ROUND(CALCULATE(SUM(FUNC_99_BI[QTDE_ORC]),
                    ALLSELECTED(FUNC_99_BI[NOME])
                    ),1)
    -
    ROUND(CALCULATE(SUM(FUNC_99_BI[QTDE_REAL]),
                    ALLSELECTED(FUNC_99_BI[NOME])
                    ),1)
    )<0,1,2)
```
### CST.Z_CST_QTPRD_ORC
```dax

VAR PRD_PROC = SUM([QT_ORC_PRD_C])
VAR PRD_OPER = SUM([QT_ORC_PRD_OP_C])
VAR PRD_REC = SUM([QT_ORC])
VAR PRD_tCANA = CALCULATE(SUM(CST[QT_ORC_PRD_C]),
                                CST[PROCESSO]="5000-Colheita")
RETURN
    SWITCH(
        TRUE(),
        ISINSCOPE(CST[RECURSO]),PRD_REC,
        ISINSCOPE(CST[ATIVIDADE]),PRD_OPER,
        ISINSCOPE(CST[PROCESSO]),PRD_PROC,
        PRD_tCANA
        )
```
### CST.Z_ZZ_ISINSCOPE
```dax

SWITCH(
    TRUE(),
    ISINSCOPE(CST[RECURSO]),3,
    ISINSCOPE(CST[ATIVIDADE]),2,
    ISINSCOPE(CST[PROCESSO]),1
    
    )
```
### CST.Z_CST_QTPRD_REAL
```dax

VAR PRD_PROC = SUM([QT_REAL_PRD_C])
VAR PRD_OPER = SUM([QT_REAL_PRD_OP_C])
VAR PRD_REC = SUM([QT_REAL])
VAR PRD_tCANA = CALCULATE(SUM(CST[QT_REAL_PRD_C]),
                                CST[PROCESSO]="5000-Colheita")
RETURN
    SWITCH(
        TRUE(),
        ISINSCOPE(CST[RECURSO]),PRD_REC,
        ISINSCOPE(CST[ATIVIDADE]),PRD_OPER,
        ISINSCOPE(CST[PROCESSO]),PRD_PROC,
        PRD_tCANA
        )
```
### CST.Z_CST_UNIT_ORC
```dax

DIVIDE(SUM(CST[VL_ORC]),[Z_CST_QTPRD_ORC])
```
### CST.Z_CST_UNIT_REAL
```dax

DIVIDE(SUM(CST[VL_REAL]),[Z_CST_QTPRD_REAL])
```
### CST.Z_CST_VARPRECO
```dax

DIVIDE(SUM([VAR_PRECO]),[Z_CST_QTPRD_REAL])
```
### CST.Z_CST_VARUNIT
```dax

[Z_CST_UNIT_REAL]-[Z_CST_UNIT_ORC]
```
### CST.Z_CST_VARESTRUTURA
```dax

VAR CST_ORC = CALCULATE(SUM(CST[VL_ORC]),
                                CST[CD_GRCOMPO] = "01-Estrutura"||
                                CST[CD_GRCOMPO] = "01-M.Obra"||
                                CST[CD_GRCOMPO] = "07-Combustível")

VAR CST_REAL = CALCULATE(SUM(CST[VL_REAL]),
                                CST[CD_GRCOMPO] = "01-Estrutura"||
                                CST[CD_GRCOMPO] = "01-M.Obra"||
                                CST[CD_GRCOMPO] = "07-Combustível")

VAR CST_VarCOMB = CALCULATE(SUM(CST[VAR_PRECO]),
                                CST[CD_GRCOMPO] = "07-Combustível")

RETURN
IF(ISBLANK([Z_CST_QTPRD_ORC]),BLANK(),
                ((CST_REAL-CST_VarCOMB)/[Z_CST_QTPRD_REAL])-(CST_ORC/[Z_CST_QTPRD_ORC])
)
```
### CST.Z_CST_VARTERCEIRO
```dax

VAR CST_ORC = CALCULATE(SUM(CST[VL_ORC]),
                                CST[CD_GRCOMPO] = "03-Terceiros")

VAR CST_REAL = CALCULATE(SUM(CST[VL_REAL]),
                                CST[CD_GRCOMPO] = "03-Terceiros")

RETURN
IF(ISBLANK([Z_CST_QTPRD_ORC]),BLANK(),
                (CST_REAL/[Z_CST_QTPRD_REAL])-(CST_ORC/[Z_CST_QTPRD_ORC])
)
```
### CST.Z_CST_VARINSUMO
```dax

VAR CST_ORC = CALCULATE(SUM(CST[VL_ORC]),
                            CST[CD_GRCOMPO] = "04-Insumos")

VAR CST_REAL = CALCULATE(SUM(CST[VL_REAL]),
                            CST[CD_GRCOMPO] = "04-Insumos")

VAR CST_VarINS = CALCULATE(SUM(CST[VAR_PRECO]),
                                CST[CD_GRCOMPO] = "04-Insumos")

RETURN
IF(ISBLANK([Z_CST_QTPRD_ORC]),BLANK(),
                ((CST_REAL-CST_VarINS)/[Z_CST_QTPRD_REAL])-(CST_ORC/[Z_CST_QTPRD_ORC])
)
```
### CST.Z_CST_UNITREC_ORC
```dax


IF(OR(SUM([QT_ORC])=0,ISBLANK(SUM([QT_ORC]))),
        AVERAGE(CST[INSUMO_PRECO_ORC]),
        DIVIDE(SUM([VL_ORC]),[Z_CST_QTRECURSO_ORC])
)
```
### CST.Z_CST_UNITREC_REAL
```dax

DIVIDE(SUM([VL_REAL]),[Z_CST_QTRECURSO_REAL])
```
### CST.Z_CST_QTRECURSO_ORC
```dax

VAR QTRECURSO = SUM(CST[QT_ORC])
VAR QT_TCANA = CALCULATE(SUM([QT_ORC_PRD_C]),
                        FILTER(ALL(CST),CST[PROCESSO]="5000-Colheita"),
                        FILTER(ALL(CST),CST[DT_REFER] >= MIN(CST[DT_REFER])),
                        FILTER(ALL(CST),CST[DT_REFER] <= MAX(CST[DT_REFER]))
                        )
RETURN
SWITCH(
    TRUE(),
    ISINSCOPE(CST[RECURSO]),QTRECURSO,
    QT_TCANA
    )
```
### CST.Z_TESTE
```dax

MIN(CST[DT_REFER])
```
### CST.Z_CST_QTRECURSO_REAL
```dax

VAR QTRECURSO = SUM(CST[QT_REAL])
VAR QT_TCANA = CALCULATE(SUM([QT_REAL_PRD_C]),
                        FILTER(ALL(CST),CST[PROCESSO]="5000-Colheita"),
                        FILTER(ALL(CST),CST[DT_REFER] >= MIN(CST[DT_REFER])),
                        FILTER(ALL(CST),CST[DT_REFER] <= MAX(CST[DT_REFER]))
                        )
RETURN
SWITCH(
    TRUE(),
    ISINSCOPE(CST[RECURSO]),QTRECURSO,
    QT_TCANA
    )
```

## COLUNAS CALCULADAS (28)

### FUNC_90_REAL.QT_AFAST
```dax

CONTAINS(FUNC_10_AFAST,FUNC_AFAST[CDN_FUNCIONARIO],[CDN_FUNCIONARIO],FUNC_AFAST[DT],[DT])
```
### FUNC_90_REAL.QT_FUNC
```dax

IF(AND(ISBLANK([FUNC_FUNC.DAT_DESLIGTO_FUNC])=FALSE(),[FUNC_FUNC.DAT_DESLIGTO_FUNC]<[DT]),0,
IF(OR([QT_AFAST]=TRUE(),[FUNC_FUNC.DAT_ADMIS_FUNC]>[DT]),0,
    1/DAY(EOMONTH([DT],0))
))
```
### FUNC_99_BI.QT_AFAST
```dax

VAR CHV = [CHAVE]
RETURN
IF(ISBLANK([DT])=FALSE(),BLANK(),
    ROUND(
        CALCULATE(SUM(FUNC_10_FUNC[DIAS_AFAST]),
                    FILTER(FUNC_10_FUNC, FUNC_10_FUNC[CHAVE] = CHV)
                    )
        / DAY([MESFIM])
    ,2)
)
```
### FUNC_99_BI.QTDE_REAL
```dax

IF(ISBLANK([DT]) = FALSE(), BLANK(),
IF(AND(EOMONTH([DAT_ADMIS_FUNC],0) = [MESFIM], EOMONTH([DAT_DESLIGTO_FUNC],0) = [MESFIM]),
    ROUND( ([DAT_DESLIGTO_FUNC] - [DAT_ADMIS_FUNC] +1) / DAY([MESFIM]), 2),
IF([DAT_ADMIS_FUNC] >= [MESINI], ROUND( (DAY([MESFIM]) - DAY([DAT_ADMIS_FUNC]) +1) / DAY([MESFIM]), 2),
IF([DAT_DESLIGTO_FUNC] <= [MESFIM], ROUND( DAY([DAT_DESLIGTO_FUNC])/DAY([MESFIM]), 2),
1
))))
- IF([QT_AFAST]>1,1,[QT_AFAST])
```
### FUNC_99_BI.CENTRO_CUSTO
```dax

IF(AND(ISBLANK([CCUSTO])=TRUE(),FUNC_99_BI[FUNC_10_CCUSTO.COD_RH_CCUSTO]>0),FUNC_99_BI[FUNC_10_CCUSTO.COD_RH_CCUSTO],[CCUSTO])
```
### FUNC_99_BI.DESC_CUSTO
```dax

IF(ISBLANK([CCUSTO])=TRUE(),[FUNC_10_CCUSTO.DESC_CCUSTO],[DES_TIT_CTBL])
```
### FUNC_99_BI.CARGO
```dax

IF(AND(ISBLANK([DES_CARGO])=TRUE(),ISBLANK([FUNC_10_CARGO.DES_CARGO])=FALSE()),[FUNC_10_CARGO.DES_CARGO],[DES_CARGO])
```
### FUNC_99_BI.SETOR
```dax

LOOKUPVALUE(FUNC_10_RESP[DESC_PROC],FUNC_10_RESP[CCUSTO],[CENTRO_CUSTO])
```
### FUNC_99_BI.FIMMES
```dax

if(ISBLANK([DT]),[MESFIM],EOMONTH([DT],0))
```
### FUNC_99_BI.NOME
```dax

IF(ISBLANK([DT]),
    [NOM_PESSOA_FISIC] & " - " & FORMAT([CDN_FUNCIONARIO],"4000000"),
    "0000 - ORÇADO"
)
```
### FUNC_99_BI.STATUS
```dax

IF(ISBLANK([CCUSTO])=TRUE(),
    IF(AND([DAT_DESLIGTO_FUNC]<DATE(9999,12,31),[FIMMES]>=EOMONTH([DAT_DESLIGTO_FUNC],0)),"3-Inativo",
    IF([QT_AFAST]>=1,"2-Afastado","1-Ativo"))
,"1-Ativo")
```
### CST.PROCESSO
```dax

IF(OR([CD_CCUSTO]=3501100,[CD_CCUSTO]=3501200),"1000-Preparo",
IF(OR([CD_CCUSTO]=3501300,[CD_CCUSTO]=3501400),"2000-Plantio",
IF([CD_CCUSTO]=3501500,"3000-Tratos Planta",
IF([CD_CCUSTO]=3501600,"4000-Tratos Soca",
IF([CD_CCUSTO]=3502300,"5000-Colheita",
IF([CD_CCUSTO]=3999999,"9999-Entressafra",BLANK()
))))))
```
### CST.ATIVIDADE
```dax

[CD_GRUPO] & " - " & [DE_GRUPO]
```
### CST.RECURSO
```dax

IF(ISBLANK([CD_COMPO]),BLANK(),
                        IF(LEFT([CD_GRCOMPO],2)="03","02-TERC",
                        IF(LEFT([CD_GRCOMPO],2)="04","03-INSU","01-PROP")) & " - " &
                        FORMAT([CD_COMPO],"0000000") & " - " & [DE_COMPO])
```
### CST.RANK
```dax

VALUE(LEFT([PROCESSO],4)) &" "& FORMAT(YEAR([DT_REFER]),"00") & FORMAT(MONTH([DT_REFER]),"00") &" "& [CD_GRUPO] &" "& 
FORMAT(
RANK(DENSE,,ORDERBY([PROCESSO],ASC,[CD_CCUSTO],ASC,[ATIVIDADE],ASC,[DT_REFER],ASC,[CD_GRCOMPO],ASC,[CD_OPERACAO],ASC),,
    PARTITIONBY([PROCESSO],[ATIVIDADE],[DT_REFER]))
,"0000")
```
### CST.QT_ORC_PRD_C
```dax

VAR CST_PROC = [PROCESSO]
VAR CST_ATV = [ATIVIDADE]
VAR CST_DT = [DT_REFER]
RETURN
IF(AND(VALUE(RIGHT([RANK],4))=1,[FG_PRD_PROC]="S"),
                        CALCULATE(SUM([QT_ORC_PRD]),
                                    FILTER(ALL(CST),CST[PROCESSO]=CST_PROC),
                                    FILTER(ALL(CST),CST[ATIVIDADE]=CST_ATV),
                                    FILTER(ALL(CST),CST[DT_REFER]=CST_DT),
                                    FILTER(ALL(CST),CST[FG_PRD_PROC]="S"),
                                    FILTER(ALL(CST),CST[CD_GRCOMPO]="00-Produção")
                                ),
IF(AND(VALUE(RIGHT([RANK],4))=1,[CD_CCUSTO]=3999999),
                        CALCULATE(SUM([QT_ORC_PRD]),
                                    FILTER(ALL(CST),CST[PROCESSO]="5000-Colheita"),
                                    FILTER(ALL(CST),CST[DT_REFER]=CST_DT),
                                    FILTER(ALL(CST),CST[FG_PRD_PROC]="S"),
                                    FILTER(ALL(CST),CST[CD_GRCOMPO]="00-Produção")
                                ),
BLANK()
))
```
### CST.QT_REAL_PRD_C
```dax

VAR CST_PROC = [PROCESSO]
VAR CST_ATV = [ATIVIDADE]
VAR CST_DT = [DT_REFER]
RETURN
IF(AND(VALUE(RIGHT([RANK],4))=1,[FG_PRD_PROC]="S"),
                        CALCULATE(SUM([QT_REAL_PRD]),
                                    FILTER(ALL(CST),CST[PROCESSO]=CST_PROC),
                                    FILTER(ALL(CST),CST[ATIVIDADE]=CST_ATV),
                                    FILTER(ALL(CST),CST[DT_REFER]=CST_DT),
                                    FILTER(ALL(CST),CST[FG_PRD_PROC]="S"),
                                    FILTER(ALL(CST),CST[CD_GRCOMPO]="00-Produção")
                            ),
 IF(AND(VALUE(RIGHT([RANK],4))=1,[CD_CCUSTO]=3999999),
                        CALCULATE(SUM([QT_REAL_PRD]),
                                    FILTER(ALL(CST),CST[PROCESSO]="5000-Colheita"),
                                    FILTER(ALL(CST),CST[DT_REFER]=CST_DT),
                                    FILTER(ALL(CST),CST[FG_PRD_PROC]="S"),
                                    FILTER(ALL(CST),CST[CD_GRCOMPO]="00-Produção")
                                ),
BLANK()
))
```
### CST.QT_ORC_PRD_OP_C
```dax

VAR CST_PROC = [PROCESSO]
VAR CST_ATV = [ATIVIDADE]
VAR CST_DT = [DT_REFER]
RETURN
IF(AND([CD_GRCOMPO]="00-Produção",AND(VALUE(RIGHT([RANK],4))=1,[FG_PRD_OPER]="S")),
                        CALCULATE(SUM([QT_ORC_PRD]),
                                    FILTER(ALL(CST),CST[PROCESSO]=CST_PROC),
                                    FILTER(ALL(CST),CST[ATIVIDADE]=CST_ATV),
                                    FILTER(ALL(CST),CST[DT_REFER]=CST_DT),
                                    FILTER(ALL(CST),CST[FG_PRD_OPER]="S"),
                                    FILTER(ALL(CST),CST[CD_GRCOMPO]="00-Produção")
                                ),
IF(AND([CD_GRCOMPO]="00-Produção",AND(VALUE(RIGHT([RANK],4))=1,[CD_CCUSTO]=3999999)),
                        CALCULATE(SUM([QT_ORC_PRD]),
                                    FILTER(ALL(CST),CST[PROCESSO]="5000-Colheita"),
                                    FILTER(ALL(CST),CST[DT_REFER]=CST_DT),
                                    FILTER(ALL(CST),CST[FG_PRD_PROC]="S"),
                                    FILTER(ALL(CST),CST[CD_GRCOMPO]="00-Produção")
                                ),
IF(AND([CD_GRCOMPO]="00-Produção",AND(VALUE(RIGHT([RANK],4))=1,ISBLANK([OP_PRD])=FALSE())),
                        CALCULATE(SUM([QT_ORC_PRD]),
                                    FILTER(ALL(CST),CST[PROCESSO]=CST_PROC),
                                    FILTER(ALL(CST),CST[DT_REFER]=CST_DT),
                                    FILTER(ALL(CST),CST[FG_PRD_PROC]="S"),
                                    FILTER(ALL(CST),CST[CD_GRCOMPO]="00-Produção")
                                ),
BLANK()
)))
```
### CST.QT_REAL_PRD_OP_C
```dax

VAR CST_PROC = [PROCESSO]
VAR CST_ATV = [ATIVIDADE]
VAR CST_DT = [DT_REFER]
RETURN
IF(AND([CD_GRCOMPO]="00-Produção",AND(VALUE(RIGHT([RANK],4))=1,[FG_PRD_OPER]="S")),
                        CALCULATE(SUM([QT_REAL_PRD]),
                                    FILTER(ALL(CST),CST[PROCESSO]=CST_PROC),
                                    FILTER(ALL(CST),CST[ATIVIDADE]=CST_ATV),
                                    FILTER(ALL(CST),CST[DT_REFER]=CST_DT),
                                    FILTER(ALL(CST),CST[FG_PRD_OPER]="S"),
                                    FILTER(ALL(CST),CST[CD_GRCOMPO]="00-Produção")
                                ),
IF(AND([CD_GRCOMPO]="00-Produção",AND(VALUE(RIGHT([RANK],4))=1,[CD_CCUSTO]=3999999)),
                        CALCULATE(SUM([QT_REAL_PRD]),
                                    FILTER(ALL(CST),CST[PROCESSO]="5000-Colheita"),
                                    FILTER(ALL(CST),CST[DT_REFER]=CST_DT),
                                    FILTER(ALL(CST),CST[FG_PRD_PROC]="S"),
                                    FILTER(ALL(CST),CST[CD_GRCOMPO]="00-Produção")
                                ),
IF(AND([CD_GRCOMPO]="00-Produção",AND(VALUE(RIGHT([RANK],4))=1,ISBLANK([OP_PRD])=FALSE())),
                        CALCULATE(SUM([QT_REAL_PRD]),
                                    FILTER(ALL(CST),CST[PROCESSO]=CST_PROC),
                                    FILTER(ALL(CST),CST[DT_REFER]=CST_DT),
                                    FILTER(ALL(CST),CST[FG_PRD_PROC]="S"),
                                    FILTER(ALL(CST),CST[CD_GRCOMPO]="00-Produção")
                                ),
BLANK()
)))
```
### CST.INSUMO_PRECO_ORC
```dax

VAR GRCOM = [CD_GRCOMPO]
VAR COMPO = [CD_COMPO]
VAR DATAZ = [DT_REFER]
RETURN
IF([CD_GRCOMPO]="04-Insumos",
    IF([QT_ORC]>0,[VL_ORC]/[QT_ORC],
                    IFERROR(LOOKUPVALUE(CST_COMPVAL[VL_COMPO],CST_COMPVAL[CD_COMPO],[CD_COMPO]),0)
        ),
IF([CD_GRCOMPO]="07-Combustível",
    IF(CST[QT_REAL]>0,
        DIVIDE(
            CALCULATE(SUM([VL_ORC]),
                        FILTER(CST,[CD_GRCOMPO]=GRCOM),
                        FILTER(CST,[CD_COMPO]=COMPO)/*,
                        FILTER(CST,[DT_REFER]=DATAZ)*/
                    ),
            CALCULATE(SUM([QT_ORC]),
                        FILTER(CST,[CD_GRCOMPO]=GRCOM),
                        FILTER(CST,[CD_COMPO]=COMPO)/*,
                        FILTER(CST,[DT_REFER]=DATAZ)*/
                    )
                ),
        BLANK()
        )
    ,
    BLANK()
))
```
### CST.INSUMO_PRECO_REAL
```dax


IF(OR([CD_GRCOMPO]="04-Insumos",[CD_GRCOMPO]="07-Combustível"),
    IF([QT_REAL]>0,[VL_REAL]/[QT_REAL],0),
    BLANK()
)
```
### CST.VAR_PRECO_UNIT
```dax

IF([INSUMO_PRECO_REAL]>0,[INSUMO_PRECO_REAL]-[INSUMO_PRECO_ORC],
        BLANK()
)
```
### CST.VAR_PRECO
```dax


IF(OR([CD_GRCOMPO]="04-Insumos",[CD_GRCOMPO]="07-Combustível"),
    IF([INSUMO_PRECO_REAL]>0,[VAR_PRECO_UNIT]*[QT_REAL],
        BLANK()
))
```
### FUNC_10_AFAST.DIAS_AFAST
```dax

VAR CHV = [CHAVE]
RETURN
IF(AND([DAT_INIC_SIT_AFAST]>=[MESINI],[DAT_TERM_SIT_AFAST]<=[MESFIM]),[DAT_TERM_SIT_AFAST]-[DAT_INIC_SIT_AFAST]+1,
IF(AND([DAT_INIC_SIT_AFAST]<=[MESINI],[DAT_TERM_SIT_AFAST]>=[MESFIM]),DAY([MESFIM]),
IF(AND([DAT_TERM_SIT_AFAST]<=[MESINI],EOMONTH([DAT_TERM_SIT_AFAST],0)=[MESFIM]),DAY([DAT_TERM_SIT_AFAST]),
IF(EOMONTH([DAT_INIC_SIT_AFAST],0)=[MESFIM],[MESFIM]-[DAT_INIC_SIT_AFAST]+1,
IF(EOMONTH([DAT_TERM_SIT_AFAST],0)=[MESFIM],DAY([DAT_TERM_SIT_AFAST]),
0
)))))
///CALCULATE(COUNT([CHAVE]),FILTER(FUNC_10_AFAST, FUNC_10_AFAST[CHAVE] = CHV)))
```
### FUNC_10_FUNC.DIAS_AFAST
```dax

VAR CHV = [CHAVE]
RETURN
CALCULATE(SUM(FUNC_10_AFAST[DIAS_AFAST]),
            FILTER(FUNC_10_AFAST, FUNC_10_AFAST[CHAVE] = CHV)
)
```
### FUNC_99_BI.FLT
```dax

IF(AND(ISBLANK([DT])=FALSE(),[QTDE_ORC]>0),"S",
IF(AND(ISBLANK([DT])=TRUE(),([QT_AFAST]+[QTDE_REAL])>0),"S","N"))
```
### FUNC_10_CARGO.QT_FUNC
```dax

VAR DT = [MESINI]
VAR FUNC = [CDN_FUNCIONARIO]
RETURN
CALCULATE(COUNT(FUNC_10_CARGO[CDN_FUNCIONARIO]),
            FILTER(FUNC_10_CARGO,FUNC_10_CARGO[CDN_FUNCIONARIO] = FUNC),
            FILTER(FUNC_10_CARGO,FUNC_10_CARGO[MESINI] = DT)
)
```
### FUNC_99_BI.QT_F
```dax

VAR DT = [FIMMES]
VAR FU = [CDN_FUNCIONARIO]
RETURN
CALCULATE(COUNTA(FUNC_99_BI[CDN_FUNCIONARIO]),
            FILTER(FUNC_99_BI,FUNC_99_BI[CDN_FUNCIONARIO] = FU),
            FILTER(FUNC_99_BI,FUNC_99_BI[FIMMES] = DT)
)
```

## TABELAS CALCULADAS (1)

### FUNC_BI_REAL.FUNC_BI_REAL
```dax

SUMMARIZECOLUMNS(
    FUNC_99_BI[CENTRO_CUSTO],
    FUNC_99_BI[DESC_CUSTO],
    FUNC_99_BI[CARGO],
    FUNC_99_BI[SETOR], 
    FUNC_99_BI[FIMMES],
    FUNC_99_BI[STATUS],
    "QT_REAL",      SUM(FUNC_99_BI[QTDE_REAL])
)
```