# Medidas DAX — BI_AGR_01_CST (17)

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