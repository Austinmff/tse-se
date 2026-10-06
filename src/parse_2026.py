import json
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
MUN_DIR = RAW / "2026" / "mun"
OUT = Path("data/processed")

mun = pd.read_csv(OUT / "municipios_se.csv", dtype=str)
nomes = dict(zip(mun.cd_tse, mun.municipio))

with open(RAW / "se_ab_2026.json", encoding="utf-8") as f:
    ab = json.load(f)
totais = {a["cdabr"]: a["e"] for a in ab["abr"] if a["tpabr"] == "mun"}


def candidatos(doc):
    for ag in doc["carg"][0]["agr"]:
        for par in ag["par"]:
            yield from par["cand"]


votos_rows, detalhe_rows, faltando = [], [], []

for cd, nome in nomes.items():
    arq = MUN_DIR / f"{cd}.json"
    if not arq.exists() or cd not in totais:
        faltando.append(cd)
        continue

    with open(arq, encoding="utf-8") as f:
        doc = json.load(f)
    e = totais[cd]
    base = {"ANO_ELEICAO": 2026, "NR_TURNO": 1,
            "CD_MUNICIPIO": int(cd), "NM_MUNICIPIO": nome, "NR_ZONA": 0}

    soma = 0
    for c in candidatos(doc):
        v = int(c["vap"])
        soma += v
        votos_rows.append({**base, "NR_VOTAVEL": int(c["n"]),
                           "NM_VOTAVEL": c["nm"], "QT_VOTOS": v})

    comp = int(e["c"])
    brancos = int(doc.get("v", {}).get("vb", 0))
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

print("municípios processados:", len(detalhe), "| faltando:", faltando)
print("comparecimento:", detalhe.QT_COMPARECIMENTO.sum(), "(esperado 1439082)")
print("abstenções:", detalhe.QT_ABSTENCOES.sum(), "(esperado 301053)")
lula = votos[votos.NR_VOTAVEL == 13].QT_VOTOS.sum()
print("Lula:", lula, "(esperado 856019)")