import zipfile

import pandas as pd

Z = "data/raw/votacao_secao_2026_SE.zip"
z = zipfile.ZipFile(Z)
print(z.namelist())
n = [i for i in z.namelist() if i.lower().endswith(".csv")][0]

with z.open(n) as f:
    head = pd.read_csv(f, sep=";", encoding="latin1", nrows=3, dtype=str)
print(list(head.columns))
print(head.to_string())

cargos, turnos = set(), set()
with z.open(n) as f:
    for ch in pd.read_csv(f, sep=";", encoding="latin1", dtype=str,
                          usecols=["DS_CARGO", "NR_TURNO"], chunksize=500000):
        cargos |= set(ch.DS_CARGO.unique())
        turnos |= set(ch.NR_TURNO.unique())
print("cargos:", cargos)
print("turnos:", turnos)