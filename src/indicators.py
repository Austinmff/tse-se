import numpy as np
import pandas as pd

BRANCO_NULO = {95, 96}
MARGEM_APERTADA = 0.05


def build(votos, detalhe, ano, turno, candidato, nivel="municipio"):
    chaves = ["CD_MUNICIPIO", "NM_MUNICIPIO"]
    if nivel == "zona":
        chaves.append("NR_ZONA")

    v = votos[(votos.ANO_ELEICAO == ano) & (votos.NR_TURNO == turno)]
    d = detalhe[(detalhe.ANO_ELEICAO == ano) & (detalhe.NR_TURNO == turno)]
    nominais = v[~v.NR_VOTAVEL.isin(BRANCO_NULO)]

    cand = (nominais[nominais.NM_VOTAVEL == candidato]
            .groupby(chaves, as_index=False)["QT_VOTOS"].sum()
            .rename(columns={"QT_VOTOS": "votos_cand"}))

    por_cand = nominais.groupby(chaves + ["NM_VOTAVEL"], as_index=False)["QT_VOTOS"].sum()
    rival = (por_cand[por_cand.NM_VOTAVEL != candidato]
             .groupby(chaves, as_index=False)["QT_VOTOS"].max()
             .rename(columns={"QT_VOTOS": "votos_rival"}))

    soma = ["QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES",
            "QT_VOTOS_BRANCOS", "QT_VOTOS_NULOS"]
    det = d.groupby(chaves, as_index=False)[soma].sum()

    df = (det.merge(cand, on=chaves, how="left")
             .merge(rival, on=chaves, how="left")
             .fillna({"votos_cand": 0, "votos_rival": 0}))

    df["validos"] = (df.QT_COMPARECIMENTO - df.QT_VOTOS_BRANCOS - df.QT_VOTOS_NULOS).clip(lower=1)
    df["pct_cand"] = df.votos_cand / df.validos
    df["taxa_abst"] = df.QT_ABSTENCOES / df.QT_APTOS.clip(lower=1)
    df["votos_potenciais"] = (df.QT_ABSTENCOES * df.pct_cand).round().astype(int)
    df["margem"] = (df.votos_cand - df.votos_rival) / df.validos

    ref_pct = df.votos_cand.sum() / df.validos.sum()
    ref_abst = df.QT_ABSTENCOES.sum() / df.QT_APTOS.sum()
    base_forte = df.pct_cand >= ref_pct
    abst_alta = df.taxa_abst >= ref_abst
    apertada = df.margem.abs() <= MARGEM_APERTADA

    df["categoria"] = np.select(
        [base_forte & abst_alta, apertada, base_forte],
        ["Mobilizar", "Persuadir", "Manter"],
        default="Baixa prioridade",
    )
    return df.sort_values("votos_potenciais", ascending=False).reset_index(drop=True)