from pathlib import Path

import pandas as pd

from src.tse_jws import read_jws

RAW = Path("data/raw/2026/zona")
OUT = Path("data/processed")

mun = pd.read_csv(OUT / "municipios_se.csv", dtype=str)


def candidatos(doc):
    for ag in doc["carg"][0]["agr"]:
        for par in ag["par"]:
            yield from par["cand"]


votos_rows, detalhe_rows, faltando = [], [], []

for r in mun.itertuples():
    for z in r.zonas.split(","):
        arq = RAW / f"{r.cd_tse}_{z}.jws"
        if not arq.exists():
            faltando.append((r.cd_tse, z))
            continue

        doc = read_jws(arq)
        e, v = doc["e"], doc["v"]
        base = {"ANO_ELEICAO": 2026, "NR_TURNO": 1,
                "CD_MUNICIPIO": int(r.cd_tse), "NM_MUNICIPIO": r.municipio,
                "NR_ZONA": int(z)}

        soma = 0
        for c in candidatos(doc):
            qt = int(c["vap"])
            soma += qt
            votos_rows.append({**base, "NR_VOTAVEL": int(c["n"]),
                               "NM_VOTAVEL": c["nm"], "QT_VOTOS": qt})

        comp = int(e["c"])
        brancos = int(v["vb"])
        detalhe_rows.append({**base,
                             "QT_APTOS": int(e["te"]),
                             "QT_COMPARECIMENTO": comp,
                             "QT_ABSTENCOES": int(e["a"]),
                             "QT_VOTOS_BRANCOS": brancos,
                             "QT_VOTOS_NULOS": comp - soma - brancos})

votos = pd.DataFrame(votos_rows)
detalhe = pd.DataFrame(detalhe_rows)
votos.to_csv(OUT / "votos_2026.csv", index=False)
detalhe.to_csv(OUT / "detalhe_2026.csv", index=False)

print("zonas processadas:", len(detalhe), "| faltando:", faltando)
print("comparecimento:", detalhe.QT_COMPARECIMENTO.sum(), "(esperado 1439082)")
print("abstenções:", detalhe.QT_ABSTENCOES.sum(), "(esperado 301053)")
print("Lula:", votos[votos.NR_VOTAVEL == 13].QT_VOTOS.sum(), "(esperado 856019)")