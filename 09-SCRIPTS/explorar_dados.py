import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# ATR + Impurezas historico
f1 = r"C:\01 - UMOE\09 - IA\umoe-os-8\Plano Diretor\Apresentações UMOE\ATR-TCH-TAH\Historico ATR-Imp. Vegetal e Mineral Safra 2011 a 2025.xlsx"
xl1 = pd.ExcelFile(f1)
print("=== ATR-IMP HISTORICO | Abas:", xl1.sheet_names)
for aba in xl1.sheet_names:
    df = pd.read_excel(xl1, sheet_name=aba, header=None, nrows=6)
    print(f"\n-- {aba} --")
    print(df.to_string())

# KPIs historico
f2 = r"C:\01 - UMOE\03 - Financeiro\Planilhas\Historico Kpis e Indicadores Agrícolas - Real e Projeções - UMOE.xlsx"
xl2 = pd.ExcelFile(f2)
print("\n\n=== KPIs HISTORICO | Abas:", xl2.sheet_names[:10])
for aba in xl2.sheet_names[:3]:
    df = pd.read_excel(xl2, sheet_name=aba, header=None, nrows=5)
    print(f"\n-- {aba} --")
    print(df.iloc[:5, :10].to_string())

# Historico Diario
f3 = r"C:\01 - UMOE\03 - Financeiro\Planilhas\Histórico Diário Safras.xlsx"
xl3 = pd.ExcelFile(f3)
print("\n\n=== HISTORICO DIARIO | Abas:", xl3.sheet_names[:10])
for aba in xl3.sheet_names[:2]:
    df = pd.read_excel(xl3, sheet_name=aba, header=None, nrows=5)
    print(f"\n-- {aba} --")
    print(df.iloc[:5, :10].to_string())
