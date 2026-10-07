import zipfile

import pandas as pd

Z = "data/raw/eleitorado_local_votacao_ATUAL.zip"
N = "eleitorado_local_votacao_ATUAL.csv"
COLS = [
    "SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO",
    "NR_SECAO_PRINCIPAL", "DS_TIPO_SECAO_AGREGADA", "NR_LOCAL_VOTACAO",
    "NM_LOCAL_VOTACAO", "DS_ENDERECO", "NM_BAIRRO", "NR_LATITUDE",
    "NR_LONGITUDE", "QT_ELEITOR_SECAO",
]

partes = []
with zipfile.ZipFile(Z).open(N) as f:
    for ch in pd.read_csv(f, sep=";", encoding="latin1", dtype=str,
                          usecols=COLS, chunksize=300000):
        partes.append(ch[ch.SG_UF == "SE"])
df = pd.concat(partes, ignore_index=True)

for c in ["NR_LATITUDE", "NR_LONGITUDE"]:
    df[c] = pd.to_numeric(df[c].str.replace(",", "."), errors="coerce")
df["QT_ELEITOR_SECAO"] = pd.to_numeric(df.QT_ELEITOR_SECAO, errors="coerce").fillna(0).astype(int)
df.loc[df.NM_BAIRRO.isin(["#NULO", ""]), "NM_BAIRRO"] = pd.NA

df.to_csv("data/processed/secoes_se.csv", index=False, encoding="utf-8")

print("seções em SE:", len(df), "| eleitores:", df.QT_ELEITOR_SECAO.sum(), "(oficial: 1740135)")
a = df[df.NM_MUNICIPIO == "ARACAJU"]
print("ARACAJU: seções", len(a),
      "| locais", a.groupby(["NR_ZONA", "NR_LOCAL_VOTACAO"]).ngroups,
      "| bairros", a.NM_BAIRRO.nunique(),
      "| seções sem bairro", int(a.NM_BAIRRO.isna().sum()))
print(a.groupby("NM_BAIRRO").QT_ELEITOR_SECAO.sum().sort_values(ascending=False).head(10))
print(df.DS_TIPO_SECAO_AGREGADA.value_counts(dropna=False).head())