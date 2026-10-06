from pathlib import Path

import pandas as pd

for f in sorted(Path("data/raw").glob("*.csv")):
    df = pd.read_csv(f, sep=";", encoding="latin1", nrows=3, dtype=str)
    print(f.name)
    print(list(df.columns))
    print(df.head(3).to_string())
    print()