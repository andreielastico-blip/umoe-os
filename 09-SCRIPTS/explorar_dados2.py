import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# Ler ATR-Imp completo
f1 = r"C:\01 - UMOE\09 - IA\umoe-os-8\Plano Diretor\Apresentações UMOE\ATR-TCH-TAH\Historico ATR-Imp. Vegetal e Mineral Safra 2011 a 2025.xlsx"
df = pd.read_excel(f1, sheet_name=0, header=None)
print("=== ATR/IMP COMPLETO ===")
print(df.to_string())

# Ler BD SAFRAS do KPIs
f2 = r"C:\01 - UMOE\03 - Financeiro\Planilhas\Historico Kpis e Indicadores Agrícolas - Real e Projeções - UMOE.xlsx"
xl2 = pd.ExcelFile(f2)
print("\n=== BD SAFRAS (primeiras 10 linhas x 15 cols) ===")
df2 = pd.read_excel(xl2, sheet_name="BD SAFRAS", header=None, nrows=10)
print(df2.iloc[:, :15].to_string())

# Ler aba 2026 do Historico Diario (colunas)
f3 = r"C:\01 - UMOE\03 - Financeiro\Planilhas\Histórico Diário Safras.xlsx"
xl3 = pd.ExcelFile(f3)
df3 = pd.read_excel(xl3, sheet_name="2026", header=None, nrows=3)
print("\n=== HISTORICO DIARIO 2026 (cabecalho) ===")
print(df3.to_string())
print(f"Total colunas: {df3.shape[1]}")
