import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

BASE = "https://resultados.tse.jus.br/oficial/ele2026/6257/dados/se"
OUT = Path("data/raw/2026/mun")
OUT.mkdir(parents=True, exist_ok=True)

mun = pd.read_csv("data/processed/municipios_se.csv", dtype=str)
codigos = list(mun.cd_tse)
if "--test" in sys.argv:
    codigos = ["31054"]

for cd in codigos:
    dest = OUT / f"{cd}.json"
    if dest.exists():
        continue
    url = f"{BASE}/se{cd}-c0001-e006257-u.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            dest.write_bytes(r.read())
    except Exception as e:
        print(f"ERRO em {cd}: {e}")
        print(f"URL: {url}")
        print("Parando para evitar bloqueio.")
        sys.exit(1)
    print("ok", cd)
    time.sleep(0.5)