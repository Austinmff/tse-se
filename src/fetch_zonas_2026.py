import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

BASE = "https://resultados.tse.jus.br/oficial/ele2026/6257/dados/se"
OUT = Path("data/raw/2026/zona")
OUT.mkdir(parents=True, exist_ok=True)

mun = pd.read_csv("data/processed/municipios_se.csv", dtype=str)
pares = [(r.cd_tse, z) for r in mun.itertuples() for z in r.zonas.split(",")]
if "--test" in sys.argv:
    pares = [("31054", "0002")]
print(len(pares), "arquivos a verificar")

for cd, z in pares:
    dest = OUT / f"{cd}_{z}.jws"
    if dest.exists():
        continue
    url = f"{BASE}/se{cd}-z{z}-c0001-e006257-u.jws"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            dest.write_bytes(r.read())
    except Exception as e:
        print(f"ERRO em {cd} zona {z}: {e}")
        print(f"URL: {url}")
        print("Parando para evitar bloqueio.")
        sys.exit(1)
    print("ok", cd, z)
    time.sleep(0.5)