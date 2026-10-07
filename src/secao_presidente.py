import zipfile

import pandas as pd

Z = "data/raw/votacao_secao_2026_BR.zip"
COLS = ["NR_TURNO", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO",
        "DS_CARGO", "NR_VOTAVEL", "NM_VOTAVEL", "QT_VOTOS", "NR_LOCAL_VOTACAO"]

mun = pd.read_csv("data/processed/municipios_se.csv", dtype=str)
codigos = set(mun.cd_tse.astype(int))

z = zipfile.ZipFile(Z)
nome = [i for i in z.namelist() if i.lower().endswith(".csv")][0]
print("arquivo:", nome)

partes = []
with z.open(nome) as f:
    for ch in pd.read_csv(f, sep=";", encoding="latin1", dtype=str,
                          usecols=COLS, chunksize=500000):
        ch["CD_MUNICIPIO"] = pd.to_numeric(ch.CD_MUNICIPIO, errors="coerce")
        sel = ch[(ch.DS_CARGO.str.upper() == "PRESIDENTE")
                 & (ch.NR_TURNO == "1")
                 & ch.CD_MUNICIPIO.isin(codigos)]
        partes.append(sel)

df = pd.concat(partes, ignore_index=True)
for c in ["CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "NR_VOTAVEL", "QT_VOTOS"]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
df.to_csv("data/processed/secao_presidente_2026_SE.csv", index=False, encoding="utf-8")

total = int(df.QT_VOTOS.sum())
lula = int(df[df.NR_VOTAVEL == 13].QT_VOTOS.sum())
print("linhas:", len(df), "| seções:", df.groupby(["CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]).ngroups)
print("comparecimento (todos os votos):", total, "(esperado 1439082)")
print("Lula:", lula, "(esperado 856019)")