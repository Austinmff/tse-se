import pandas as pd

ARQ = "data/raw/perfil_eleitor_secao_2026_SE.csv"

df = pd.read_csv(
    ARQ, sep=";", encoding="latin1", dtype=str,
    usecols=["CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "NR_LOCAL_VOTACAO",
             "NM_LOCAL_VOTACAO", "QT_ELEITORES"],
)
df["CD_MUNICIPIO"] = df.CD_MUNICIPIO.astype(int)
df["NR_ZONA"] = df.NR_ZONA.astype(int)
df["QT_ELEITORES"] = pd.to_numeric(df.QT_ELEITORES, errors="coerce").fillna(0).astype(int)

locais = (
    df.groupby(["CD_MUNICIPIO", "NR_ZONA", "NR_LOCAL_VOTACAO", "NM_LOCAL_VOTACAO"],
               as_index=False)
    .agg(eleitores=("QT_ELEITORES", "sum"), secoes=("NR_SECAO", "nunique"))
    .sort_values(["CD_MUNICIPIO", "NR_ZONA", "eleitores"], ascending=[True, True, False])
)
locais.to_csv("data/processed/locais_votacao.csv", index=False, encoding="utf-8")

zl = (
    locais.groupby(["CD_MUNICIPIO", "NR_ZONA"])
    .agg(
        n_locais=("NM_LOCAL_VOTACAO", "size"),
        n_secoes=("secoes", "sum"),
        principais_locais=("NM_LOCAL_VOTACAO", lambda s: "; ".join(s.head(3))),
    )
    .reset_index()
)
zl.to_csv("data/processed/zonas_locais.csv", index=False, encoding="utf-8")

print("zonas:", len(zl), "| locais:", len(locais))
print(zl[zl.CD_MUNICIPIO == 31054].to_string())