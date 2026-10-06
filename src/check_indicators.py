import pandas as pd

from src.indicators import build

votos = pd.read_csv("data/processed/votos_2026.csv")
detalhe = pd.read_csv("data/processed/detalhe_2026.csv")

candidato = votos[votos.NR_VOTAVEL == 13].NM_VOTAVEL.iloc[0]
df = build(votos, detalhe, 2026, 1, candidato)

cols = ["NM_MUNICIPIO", "pct_cand", "taxa_abst", "votos_potenciais", "categoria"]
print(df.head(10)[cols].to_string())
print()
print(df.categoria.value_counts())
print("votos potenciais (total):", df.votos_potenciais.sum())