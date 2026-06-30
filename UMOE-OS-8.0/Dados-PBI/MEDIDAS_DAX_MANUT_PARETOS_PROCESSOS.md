# DAX (negocio) — MANUT_PARETOS_PROCESSOS
Medidas: 4 | Colunas calculadas: 0 | Tabelas calculadas: 0 | Negocio: 4 | Auto date tables omitidas: 28


## MEDIDAS (4)

### Paretos.Lista de SISTEMA valores
```dax

VAR __DISTINCT_VALUES_COUNT = DISTINCTCOUNT('Paretos'[SISTEMA])
VAR __MAX_VALUES_TO_SHOW = 3
RETURN
	IF(
		__DISTINCT_VALUES_COUNT > __MAX_VALUES_TO_SHOW,
		CONCATENATE(
			CONCATENATEX(
				TOPN(
					__MAX_VALUES_TO_SHOW,
					VALUES('Paretos'[SISTEMA]),
					'Paretos'[SISTEMA],
					ASC
				),
				'Paretos'[SISTEMA],
				", ",
				'Paretos'[SISTEMA],
				ASC
			),
			",  etc."
		),
		CONCATENATEX(
			VALUES('Paretos'[SISTEMA]),
			'Paretos'[SISTEMA],
			", ",
			'Paretos'[SISTEMA],
			ASC
		)
	)
```
### Paretos.MTTR
```dax

DIVIDE(
	SUM('Paretos'[Tempo dePermanência(h)]),
	COUNTA('Paretos'[SISTEMA])
)
```
### Paretos.limite mttr
```dax

DIVIDE(
	SUM('Paretos'[Tempo dePermanência(h)]),
	COUNTA('Paretos'[Boletim])
)
```
### Paretos.limite N
```dax

DIVIDE(COUNTA('Paretos'[Boletim]), DISTINCTCOUNT('Paretos'[SISTEMA]))
```