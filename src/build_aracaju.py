import unicodedata
from pathlib import Path

import pandas as pd

from src.indicators import build

OUT = Path("data/processed/aracaju")
OUT.mkdir(parents=True, exist_ok=True)
ARACAJU = 31054
CHAVE = ["CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]


def sem_acento(s):
    if pd.isna(s):
        return "SEM BAIRRO"
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.upper().strip()


res = pd.read_csv("data/processed/secao_presidente_2026_SE.csv")
sec = pd.read_csv("data/processed/secoes_se.csv").rename(
    columns={"QT_ELEITOR_SECAO": "aptos"})
sec["CD_MUNICIPIO"] = sec.CD_MUNICIPIO.astype(int)

comp = res.groupby(CHAVE).QT_VOTOS.sum().rename("comparecimento")
bra = res[res.NR_VOTAVEL == 95].groupby(CHAVE).QT_VOTOS.sum().rename("brancos")
nul = res[res.NR_VOTAVEL == 96].groupby(CHAVE).QT_VOTOS.sum().rename("nulos")
tot = pd.concat([comp, bra, nul], axis=1).reset_index()

base = sec.merge(tot, on=CHAVE, how="left")
sem_res = base[base.comparecimento.isna()]
print("seções sem resultado:", len(sem_res),
      "| eleitores nelas:", int(sem_res.aptos.sum()),
      "| só em Aracaju:", int((sem_res.CD_MUNICIPIO == ARACAJU).sum()))
print(sem_res.groupby("NM_MUNICIPIO").size().sort_values(ascending=False).head(5))

base = base[base.comparecimento.notna()].copy()
for c in ["comparecimento", "brancos", "nulos"]:
    base[c] = base[c].fillna(0).astype(int)
print("seções com mais votos que eleitores:", int((base.comparecimento > base.aptos).sum()))
base["abstencoes"] = (base.aptos - base.comparecimento).clip(lower=0)

ara = base[base.CD_MUNICIPIO == ARACAJU].copy()
ara["bairro"] = ara.NM_BAIRRO.map(sem_acento)
ara["escola"] = (ara.NM_LOCAL_VOTACAO + " - " + ara.bairro
                 + " (zona " + ara.NR_ZONA.astype(str) + ")")


def unidades(df_sec, col):
    ids = {n: i + 1 for i, n in enumerate(sorted(df_sec[col].unique()))}
    df_sec = df_sec.assign(uid=df_sec[col].map(ids))
    v = (res.merge(df_sec[CHAVE + ["uid", col]], on=CHAVE)
         .groupby(["uid", col, "NR_VOTAVEL", "NM_VOTAVEL"], as_index=False)
         .QT_VOTOS.sum()
         .rename(columns={col: "NM_MUNICIPIO", "uid": "CD_MUNICIPIO"}))
    v["ANO_ELEICAO"], v["NR_TURNO"], v["NR_ZONA"] = 2026, 1, 0
    d = (df_sec.groupby(["uid", col], as_index=False)
         .agg(QT_APTOS=("aptos", "sum"),
              QT_COMPARECIMENTO=("comparecimento", "sum"),
              QT_ABSTENCOES=("abstencoes", "sum"),