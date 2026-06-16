import pandas as pd
import warnings
warnings.filterwarnings("ignore")

ARQUIVO = r"C:\01 - UMOE\03 - Financeiro\Planilhas\1 - Indice Pluviometrico UMOE.xlsx"

xl = pd.ExcelFile(ARQUIVO)

df = pd.read_excel(xl, sheet_name="HISTORICO", header=None)
dados = df.iloc[2:, [0,1,3,4,5,6]].copy()
dados.columns = ["ANO2","DATA","MM","MES","ANO","DEC"]
dados = dados.dropna(subset=["ANO"])
dados["ANO"] = dados["ANO"].astype(int)
dados["MM"] = pd.to_numeric(dados["MM"], errors="coerce").fillna(0)

print("=== PRECIPITACAO ANUAL TOTAL (mm) ===")
anual = dados.groupby("ANO")["MM"].sum()
print(anual.to_string())

print()
print("=== MES A MES 2024, 2025, 2026 ===")
resumo = dados.groupby(["ANO","MES"])["MM"].sum().reset_index()
for ano in [2024, 2025, 2026]:
    sub = resumo[resumo["ANO"]==ano]
    if not sub.empty:
        print(f"Ano {ano}:")
        for _, r in sub.iterrows():
            print(f"  {r['MES']}: {r['MM']:.1f} mm")

print()
print("=== DECADAS 2026 (DEC 1/2/3 por mes) ===")
dec2026 = dados[dados["ANO"]==2026].groupby(["MES","DEC"])["MM"].sum().reset_index()
print(dec2026.to_string(index=False))

print()
print("=== MEDIA HISTORICA POR MES (todos os anos) ===")
media = dados.groupby("MES")["MM"].mean().reset_index()
media.columns = ["MES","Media_mm"]
print(media.to_string(index=False))
