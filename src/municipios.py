import json
from pathlib import Path

import pandas as pd

with open("data/raw/mun_config_2026.json", encoding="utf-8") as f:
    cfg = json.load(f)

se = next(a for a in cfg["abr"] if a["cd"] == "se")
rows = [
    {
        "cd_tse": m["cd"],
        "cd_ibge": m["cdi"],
        "municipio": m["nm"],
        "capital": m["c"],
        "zonas": ",".join(m["z"]),
    }
    for m in se["mu"]
]

df = pd.DataFrame(rows)
Path("data/processed").mkdir(parents=True, exist_ok=True)
df.to_csv("data/processed/municipios_se.csv", index=False, encoding="utf-8")
print(len(df), "municípios")
print(df.head(5).to_string())