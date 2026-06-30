# DAX (negocio) — BI_AGR_01_CTRL
Medidas: 1 | Colunas calculadas: 29 | Tabelas calculadas: 5 | Negocio: 35 | Auto date tables omitidas: 126


## MEDIDAS (1)

### CTRL_ESTOQ_SALDO.Z_CTRL_ESTOQ_SALDO_QTSALDO
```dax

ROUND(CALCULATE(SUM(CTRL_ESTOQ_SALDO[QT_ESTOQUE]),
            ALLEXCEPT(CTRL_ESTOQ_SALDO,CTRL_ESTOQ_SALDO[CD_INSUMO])
        ),2)
- ROUND(SUM(CTRL_ESTOQ_SALDO[QT_RESERVA]),2)
```

## COLUNAS CALCULADAS (29)

### USER_EMAIL.EMAIL_LIDER
```dax

IF(LEFT([DE_FUNC],SEARCH(" ",[DE_FUNC],1)-1)="WAGNER","wanderlei.souza@umoe.com.br; " &
                                                      "wanderson.santos@umoe.com.br; " &
                                                      "ronaldo.delgado@umoe.com.br",
    BLANK()
)
```
### CTRL_ORDEMCORTE.FAZENDA
```dax
[CD_UPNIVEL1] & " - " &
SUBSTITUTE(
    SUBSTITUTE(
        SUBSTITUTE(
            SUBSTITUTE([DE_UPNIVEL1],"Fazenda","Faz."),
                "Estância","Est."),
            "Nossa Senhora", "N.S."),
        "Sítio","Sít.")
```
### FUNC_DIV.DIV
```dax

IF(OR([TURNO]="DIV",[TURNO]="NI"),BLANK(),
IF(OR([TURNO]<>[TURNO_FUNC],[CD_LOC_ESCALA]<>[CD_LOC_RH]),1,BLANK()
))
```
### FUNC_DIV.TP_DIV
```dax

IF([DIV]=BLANK(),BLANK(),
IF(AND([TURNO]<>[TURNO_FUNC],[CD_LOC_ESCALA]<>[CD_LOC_RH]),"1 - Turno e Local de Pagamento",
IF([TURNO]<>[TURNO_FUNC],"2 - Turno","3 - Local de Pagamento <> Frente"
)))
```
### FUNC_DIV.LIDER_APTO
```dax

IF([DE_LIDER]=BLANK(),[RESP_APTO] & " - " & [DE_RESP_APTO], [LIDER] & " - " & [DE_LIDER])
```
### ORDEM_SERVICO_DOSE.QTDE_DOSE
```dax

ROUND(DIVIDE([QTDE_PRODUTO],[QTDE_AREA]),3)
```
### ORDEM_SERVICO_DOSE.CHECK_DOSE
```dax

IF(OR([QTDE_DOSE]<[DOSE_MIN],[QTDE_DOSE]>[DOSE_MAX]),"Verificar Item",BLANK())
```
### ORDEM_SERVICO_DOSE.QTDE_CHECK
```dax

IF([CHECK_DOSE]=BLANK(),BLANK(),1)
```
### ORDEM_SERVICO_DOSE.CHECK_OS
```dax

VAR N_OS = [NO_OS]
RETURN
IF(CALCULATE(SUM([QTDE_CHECK]),FILTER(ORDEM_SERVICO_DOSE,[NO_OS]=N_OS)) = 0, BLANK(), "Verificar O.S.")
```
### CST_ORCAMENTO.PRD_YTD_R
```dax

VAR PRC = [PROCESSO]
VAR GRP = [CD_GRUPO]

RETURN

CALCULATE(SUM(CST_OS[QT_AREA]),
    CST_OS[PROCESSO] = PRC,
    CST_OS[CD_GRUPO] = GRP)
+
CALCULATE(SUM(CST_REALIZADO[PRD_YTD_R]),
    CST_REALIZADO[PROCESSO] = PRC,
    CST_REALIZADO[CD_GRUPO] = GRP)
```
### CST_ORCAMENTO.VLR_YTD_R
```dax

VAR PRC = [PROCESSO]
VAR GRP = [CD_GRUPO]

RETURN

CALCULATE(SUM(CST_OS[VL_OS]),
    CST_OS[PROCESSO] = PRC,
    CST_OS[CD_GRUPO] = GRP)
+
CALCULATE(SUM(CST_REALIZADO[VLR_YTD_R]),
    CST_REALIZADO[PROCESSO] = PRC,
    CST_REALIZADO[CD_GRUPO] = GRP)
```
### CST_ORCAMENTO.REGRA
```dax

IF(OR([VLR_YTD_R]>[VLR_TT],[VLR_YTD_R]>[VLR_YTD]),1,
IF(OR([PRD_YTD_R]>[PRD_TT],[PRD_YTD_R]>[PRD_YTD]),1,0))
```
### CST_ORCAMENTO.UNIT_YTD
```dax

ROUND(IFERROR([VLR_YTD]/[PRD_YTD],0),2)
```
### CST_ORCAMENTO.UNIT_TT
```dax

ROUND(IFERROR([VLR_TT]/[PRD_TT],0),2)
```
### CST_ORCAMENTO.UNIT_REAL
```dax

ROUND(IFERROR([VLR_YTD_R]/[PRD_YTD_R],0),2)
```
### CST_OS.PRD_TT
```dax

IF(ISBLANK(
            LOOKUPVALUE(CST_ORCAMENTO[PRD_TT],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO])
            ), 0, 
            ROUND(
            LOOKUPVALUE(CST_ORCAMENTO[PRD_TT],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO]),2)
)
```
### CST_OS.PRD_YTD
```dax

IF(ISBLANK(
            LOOKUPVALUE(CST_ORCAMENTO[PRD_YTD],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO])
            ), 0,
            ROUND(
            LOOKUPVALUE(CST_ORCAMENTO[PRD_YTD],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO]),2)
)
```
### CST_OS.PRD_REAL
```dax

IF(ISBLANK(
            LOOKUPVALUE(CST_ORCAMENTO[PRD_YTD_R],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO])
            ), 0, 
            ROUND(
            LOOKUPVALUE(CST_ORCAMENTO[PRD_YTD_R],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO]),2)
)
```
### CST_OS.VLR_TT
```dax

IF(ISBLANK(
            LOOKUPVALUE(CST_ORCAMENTO[VLR_TT],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO])
            ), 0,
            ROUND(
            LOOKUPVALUE(CST_ORCAMENTO[VLR_TT],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO]),2)
)
```
### CST_OS.VLR_YTD
```dax

IF(ISBLANK(
            LOOKUPVALUE(CST_ORCAMENTO[VLR_YTD],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO])
            ), 0,
            ROUND(
            LOOKUPVALUE(CST_ORCAMENTO[VLR_YTD],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO]),2)
)
```
### CST_OS.VLR_REAL
```dax

IF(ISBLANK(
            LOOKUPVALUE(CST_ORCAMENTO[VLR_YTD_R],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO])
            ), 0,
            ROUND(
            LOOKUPVALUE(CST_ORCAMENTO[VLR_YTD_R],
                        CST_ORCAMENTO[PROCESSO],[PROCESSO],
                        CST_ORCAMENTO[CD_GRUPO],[CD_GRUPO]),2)
)
```
### CST_OS.UNIT_TT
```dax

ROUND(IFERROR([VLR_TT]/[PRD_TT],0),2)
```
### CST_OS.UNIT_YTD
```dax

ROUND(IFERROR([VLR_YTD]/[PRD_YTD],0),2)
```
### CST_OS.UNIT_REAL
```dax

ROUND(IFERROR([VLR_REAL]/[PRD_REAL],0),2)
```
### CST_OS.ALERTA
```dax

IF([VLR_REAL]>[VLR_TT],"Gasto real maior que Gasto orçado total",
IF([CST_UNIT]>[UNIT_TT],"Custo unitário da OS maior que Custo unitário Total orçado",
IF([PRD_REAL]>[PRD_TT],"Produção realizada maior do que Produção Total orçada",
BLANK()
)))
```
### CST_OS.EMAIL_COORD
```dax

IF([CD_FUNC] = 4014697,
    LOOKUPVALUE(USER_EMAIL[DE_EMAIL],
                USER_EMAIL[CD_USUARIO], 4015770),
IF(AND([CD_COORD]=4011426,and([CD_OPERACAO]>=2900,[CD_OPERACAO]<=2999)),
    LOOKUPVALUE(USER_EMAIL[DE_EMAIL],
            USER_EMAIL[CD_USUARIO], [CD_COORD]) &"; "&
    LOOKUPVALUE(USER_EMAIL[DE_EMAIL],
            USER_EMAIL[CD_USUARIO], 4013214) &"; claudinei.archangelo@umoe.com.br"
    ,
    LOOKUPVALUE(USER_EMAIL[DE_EMAIL],
                USER_EMAIL[CD_USUARIO], [CD_COORD])
))
```
### CST_OS.EMAIL_GERENCIA
```dax

/*IF(OR([CD_COORD] = 4008577, OR([CD_COORD] = 4015770, [CD_COORD] = 4010530)), "andrei.elastico@umoe.com.br; cristiano.silva@umoe.com.br",
IF(OR([CD_COORD] = 4011426, [CD_COORD] = 4011723), "andrei.elastico@umoe.com.br; wagner.rodrigues@umoe.com.br",
"andrei.elastico@umoe.com.br"
))*/

//IF(OR([CD_FUNC] = 4014697, OR([CD_COORD] = 4008577, OR([CD_COORD] = 4015770, [CD_COORD] = 4010530))), "cristiano.silva@umoe.com.br",
//IF(OR([CD_COORD] = 4011426, [CD_COORD] = 4011723), "wagner.rodrigues@umoe.com.br",
//"andrei.elastico@umoe.com.br"
"wagner.rodrigues@umoe.com.br"
//)
```
### CST_OS.COORD
```dax

IF([CD_FUNC] = 4014697,"DIEGO",
IF(AND([CD_COORD]=4011426,and([CD_OPERACAO]>=2900,[CD_OPERACAO]<=2999)),
    LEFT(
        LOOKUPVALUE(USER_EMAIL[DE_FUNC],
                USER_EMAIL[CD_USUARIO], 4013214),
        SEARCH(" ",LOOKUPVALUE(USER_EMAIL[DE_FUNC],USER_EMAIL[CD_USUARIO], 4013214),1,1000)
        )
    ,
    LEFT([DE_COORD],SEARCH(" ",[DE_COORD],1,1000))
))
```
### CST_OS.FILT_DTHR
```dax

IF(AND(ISBLANK([ALERTA])=FALSE,
    [DT_ALTERA] >= [DTHR]
        ),"S","N")
```

## TABELAS CALCULADAS (5)

### CTRL_ORDEMCORTE_EMAIL.CTRL_ORDEMCORTE_EMAIL
```dax

SELECTCOLUMNS(/*FILTER(MNF_OM,MNF_OM[STATUS_OS] = "ABERTA"),*/
                CTRL_ORDEMCORTE,
                "FAZENDA",          CTRL_ORDEMCORTE[FAZENDA],
                "TALHAO",           CTRL_ORDEMCORTE[CD_UPNIVEL3],
                "VARIEDADE",        CTRL_ORDEMCORTE[DE_VARIED],
                "PERIODO_CTT",      CTRL_ORDEMCORTE[MES_INI] & " - " & CTRL_ORDEMCORTE[MES_FIM],
                "ORDEM",            CTRL_ORDEMCORTE[NO_QUEIMA],
                "FRENTE",           CTRL_ORDEMCORTE[CD_FREN_TRAN],
                "DT_CTT",           FORMAT(CTRL_ORDEMCORTE[DT_QUEIMA],"DD/MM/YYYY"),
                "PROD_EST",         CTRL_ORDEMCORTE[QT_ESTIM],
                "AREA",             CTRL_ORDEMCORTE[QT_AREA],
                "INSUMO",           CTRL_ORDEMCORTE[DE_INSUMO],
                "DT_APLIC",         FORMAT(CTRL_ORDEMCORTE[DT_APLIC],"DD/MM/YYYY"),
                "DT_MIN",           FORMAT(CTRL_ORDEMCORTE[DT_MIN_MATUR],"DD/MM/YYYY"),
                "DT_MAX",           FORMAT(CTRL_ORDEMCORTE[DT_MAX_MATUR],"DD/MM/YYYY"),
                "DT_PRE",           FORMAT(CTRL_ORDEMCORTE[DT_PRE],"DD/MM/YYYY"),
                "ATR_PRE",          FORMAT(CTRL_ORDEMCORTE[ATR_PRE],"0,0.00"),
                "TIPO_CANA",        CTRL_ORDEMCORTE[TIPO_CANA],
                "MOTIVO",           CTRL_ORDEMCORTE[MOTIVO]
)
```
### CTRL_PESAGEM_EQ_DIVERG_EMAIL.CTRL_PESAGEM_EQ_DIVERG_EMAIL
```dax

SELECTCOLUMNS(FILTER(CTRL_PESAGEM_EQ_DIVERG,CTRL_PESAGEM_EQ_DIVERG[DT_MOVIMENTO] >= DATE(2024,6,1)),
                /*MNF_OM,*/
                "ULT_ATUALIZACAO",  FORMAT(CTRL_PESAGEM_EQ_DIVERG[ULT_ATUALIZACAO],"DD/MM/YYYY HH:MM"),
                "CD_UNID_IND",      CTRL_PESAGEM_EQ_DIVERG[CD_UNID_IND],
                "HR_ENTRADA",       FORMAT(CTRL_PESAGEM_EQ_DIVERG[HR_ENTRADA],"DD/MM/YYYY HH:MM"),
                "DT_MOVIMENTO",     FORMAT(CTRL_PESAGEM_EQ_DIVERG[DT_MOVIMENTO],"DD/MM/YYYY"),
                "FAZENDA",          CTRL_PESAGEM_EQ_DIVERG[CD_UPNIVEL1],
                "TALHAO",           CTRL_PESAGEM_EQ_DIVERG[CD_UPNIVEL3],
                "TIPO_PROPR",       CTRL_PESAGEM_EQ_DIVERG[CD_TP_PROPR],
                "CD_FREN_TRAN",     CTRL_PESAGEM_EQ_DIVERG[CD_FREN_TRAN],
                "DE_FREN_TRAN",     CTRL_PESAGEM_EQ_DIVERG[DE_FREN_TRAN],
                "CD_TP_RECURSO",    CTRL_PESAGEM_EQ_DIVERG[CD_TP_RECURSO],
                "CD_TRANP",         CTRL_PESAGEM_EQ_DIVERG[CD_TRANSP],
                "DE_TRANP",         CTRL_PESAGEM_EQ_DIVERG[DE_TRANSP],
                "CD_EQUIPTO",       CTRL_PESAGEM_EQ_DIVERG[CD_EQUIPTO],
                "FG_TP_EQUIP",      CTRL_PESAGEM_EQ_DIVERG[FG_TP_EQUIP],
                "NO_LIBERACAO",     CTRL_PESAGEM_EQ_DIVERG[NO_LIBERACAO],
                "ORDEM_CORTE",      CTRL_PESAGEM_EQ_DIVERG[ORDEM_CORTE],
                "EQUIPTO",          CTRL_PESAGEM_EQ_DIVERG[EQUIPTO],
                "TON",              CTRL_PESAGEM_EQ_DIVERG[TON],
                "OCORRENCIA",       CTRL_PESAGEM_EQ_DIVERG[OCORRENCIA]
)
```
### FUNC_DIV_EMAIL.FUNC_DIV_EMAIL
```dax

SELECTCOLUMNS(FILTER(FUNC_DIV,FUNC_DIV[DIV] = 1),
                "GESTOR",           FUNC_DIV[DE_COORDENADOR] & " - " & FUNC_DIV[COORDENADOR],
                "SETOR",            FUNC_DIV[SETOR],
                "FRENTE",           FUNC_DIV[FRENTE],
                "TURNO",            FUNC_DIV[TURNO],
                "LIDER",            FUNC_DIV[LIDER_APTO],
                "TURNO_FUNC",       FUNC_DIV[TURNO_FUNC],
                "FUNCIONARIO",      FUNC_DIV[DE_FUNC] & " - " & FUNC_DIV[FUNC],
                "CCUSTO",           FUNC_DIV[CD_CCUSTO] & " - " & FUNC_DIV[DE_CCUSTO],
                "LP_FRENTE",        FUNC_DIV[CD_LOC_ESCALA] & " - " & FUNC_DIV[DE_LOC_ESCALA],
                "LP_FUNC",          FUNC_DIV[CD_LOC_RH] & " - " & FUNC_DIV[DE_LOC_RH],
                "TIPO_DIV",         FUNC_DIV[TP_DIV]
)
```
### ORDEM_SERVICO_DOSE_EMAIL.ORDEM_SERVICO_DOSE_EMAIL
```dax

SELECTCOLUMNS(FILTER(ORDEM_SERVICO_DOSE,[CHECK_OS]="Verificar O.S."),
    "FAZENDA",              ORDEM_SERVICO_DOSE[FAZENDA],
    "ORDEM_SERVICO",        ORDEM_SERVICO_DOSE[NO_OS],
    "TALHOES",              ORDEM_SERVICO_DOSE[TALHOES],
    "CCUSTO",               ORDEM_SERVICO_DOSE[CCUSTO],
    "OPERACAO",             ORDEM_SERVICO_DOSE[OPERACAO],
    "RECURSO",              ORDEM_SERVICO_DOSE[RECURSO],
    "QTDE_RECURSO",         ORDEM_SERVICO_DOSE[QTDE_PRODUTO],
    "QTDE_AREA",            ORDEM_SERVICO_DOSE[QTDE_AREA],
    "DOSE_ORDEM_SERV",      ORDEM_SERVICO_DOSE[QTDE_DOSE],
    "DOSE_MIN",             ORDEM_SERVICO_DOSE[DOSE_MIN],
    "DOSE_MAX",             ORDEM_SERVICO_DOSE[DOSE_MAX],
    "CHECK",                ORDEM_SERVICO_DOSE[CHECK_DOSE]
)
```
### Z_DTHR.Z_DTHR
```dax
Row("DTHR", UTCNOW() - (3/24))
```