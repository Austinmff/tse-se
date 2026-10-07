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
sec = pd.read_csv("data/processed/secoes_se.csv")
sec = sec.rename(columns={"QT_ELEITOR_SECAO": "aptos"})
sec["CD_MUNICIPIO"] = sec.CD_MUNICIPIO.astype(int)

comp = res.groupby(CHAVE).QT_VOTOS.sum().rename("comparecimento")
bra = res[res.NR_VOTAVEL == 95].groupby(CHAVE).QT_VOTOS.sum().rename("brancos")
nul = res[res.NR_VOTAVEL == 96].groupby(CHAVE).QT_VOTOS.sum().rename("nulos")
tot = pd.concat([comp, bra, nul], axis=1).reset_index()

base = sec.merge(tot, on=CHAVE, how="left")
sem_res = base[base.comparecimento.isna()]
print("seções sem resultado:", len(sem_res))
print("eleitores nelas:", int(sem_res.aptos.sum()))
print("só em Aracaju:", int((sem_res.CD_MUNICIPIO == ARACAJU).sum()))
print(sem_res.groupby("NM_MUNICIPIO").size().sort_values(ascending=False).head(5))

base = base[base.comparecimento.notna()].copy()
for c in ["comparecimento", "brancos", "nulos"]:
    base[c] = base[c].fillna(0).astype(int)
print("seções com mais votos que eleitores:", int((base.comparecimento > base.aptos).sum()))
base["abstencoes"] = (base.aptos - base.comparecimento).clip(lower=0)

ara = base[base.CD_MUNICIPIO == ARACAJU].copy()
ara["bairro"] = ara.NM_BAIRRO.map(sem_acento)
ara["escola"] = (
    ara.NM_LOCAL_VOTACAO + " - " + ara.bairro + " (zona " + ara.NR_ZONA.astype(str) + ")"
)


def unidades(df_sec, col):
    nomes = sorted(df_sec[col].unique())
    ids = {n: i + 1 for i, n in enumerate(nomes)}
    df_sec = df_sec.assign(uid=df_sec[col].map(ids))

    juntos = res.merge(df_sec[CHAVE + ["uid", col]], on=CHAVE)
    chaves_v = ["uid", col, "NR_VOTAVEL", "NM_VOTAVEL"]
    v = juntos.groupby(chaves_v, as_index=False).QT_VOTOS.sum()
    v = v.rename(columns={col: "NM_MUNICIPIO", "uid": "CD_MUNICIPIO"})
    v["ANO_ELEICAO"] = 2026
    v["NR_TURNO"] = 1
    v["NR_ZONA"] = 0

    g = df_sec.groupby(["uid", col], as_index=False)
    d = g.agg(
        QT_APTOS=("aptos", "sum"),
        QT_COMPARECIMENTO=("comparecimento", "sum"),
        QT_ABSTENCOES=("abstencoes", "sum"),
        QT_VOTOS_BRANCOS=("brancos", "sum"),
        QT_VOTOS_NULOS=("nulos", "sum"),
    )
    d = d.rename(columns={col: "NM_MUNICIPIO", "uid": "CD_MUNICIPIO"})
    d["ANO_ELEICAO"] = 2026
    d["NR_TURNO"] = 1
    d["NR_ZONA"] = 0
    return v, d


for nome, col in [("bairros", "bairro"), ("escolas", "escola")]:
    v, d = unidades(ara, col)
    v.to_csv(OUT / f"{nome}_votos.csv", index=False)
    d.to_csv(OUT / f"{nome}_detalhe.csv", index=False)
    lula = v[v.NR_VOTAVEL == 13].NM_VOTAVEL.iloc[0]
    df = build(v, d, 2026, 1, lula)
    print(f"\n{nome.upper()}: {len(df)} unidades")
    cols = ["NM_MUNICIPIO", "QT_APTOS", "taxa_abst", "pct_cand", "votos_potenciais", "categoria"]
    print(df.head(8)[cols].to_string())

det = pd.read_csv("data/processed/detalhe_2026.csv")
a = det[det.CD_MUNICIPIO == ARACAJU]
print("\nAracaju, comparecimento: por seção", int(ara.comparecimento.sum()),
      "| oficial", int(a.QT_COMPARECIMENTO.sum()))
print("Aracaju, eleitores: por seção", int(ara.aptos.sum()),
      "| oficial", int(a.QT_APTOS.sum()))