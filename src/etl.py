from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")
ENC = "latin1"

COLS_VOTOS = [
    "ANO_ELEICAO", "NR_TURNO", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA",
    "DS_CARGO", "NR_VOTAVEL", "NM_VOTAVEL", "QT_VOTOS",
]
COLS_DETALHE = [
    "ANO_ELEICAO", "NR_TURNO", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA",
    "DS_CARGO", "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES",
    "QT_VOTOS_BRANCOS", "QT_VOTOS_NULOS",
]
NUM_VOTOS = ["ANO_ELEICAO", "NR_TURNO", "CD_MUNICIPIO", "NR_ZONA", "NR_VOTAVEL", "QT_VOTOS"]
NUM_DETALHE = [
    "ANO_ELEICAO", "NR_TURNO", "CD_MUNICIPIO", "NR_ZONA", "QT_APTOS",
    "QT_COMPARECIMENTO", "QT_ABSTENCOES", "QT_VOTOS_BRANCOS", "QT_VOTOS_NULOS",
]


def read_all(pattern, required):
    files = sorted(RAW.glob(pattern))
    if not files:
        raise SystemExit(f"Nenhum arquivo encontrado em {RAW} para: {pattern}")
    frames = []
    for f in files:
        df = pd.read_csv(f, sep=";", encoding=ENC, dtype=str,
                         usecols=lambda c: c in required)
        missing = sorted(set(required) - set(df.columns))
        if missing:
            raise SystemExit(f"{f.name}: colunas ausentes: {missing}")
        print(f"lido: {f.name} ({len(df)} linhas)")
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def prep(df, num_cols):
    df = df[df["DS_CARGO"].str.upper() == "PRESIDENTE"].copy()
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    return df


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    votos = prep(read_all("votacao_secao_*.csv", COLS_VOTOS), NUM_VOTOS)
    chaves = ["ANO_ELEICAO", "NR_TURNO", "CD_MUNICIPIO", "NM_MUNICIPIO",
              "NR_ZONA", "NR_VOTAVEL", "NM_VOTAVEL"]
    votos = votos.groupby(chaves, as_index=False)["QT_VOTOS"].sum()
    votos.to_csv(OUT / "votos.csv", index=False)

    detalhe = prep(read_all("detalhe_votacao_secao_*.csv", COLS_DETALHE), NUM_DETALHE)
    chaves = ["ANO_ELEICAO", "NR_TURNO", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA"]
    soma = ["QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES",
            "QT_VOTOS_BRANCOS", "QT_VOTOS_NULOS"]
    detalhe = detalhe.groupby(chaves, as_index=False)[soma].sum()
    detalhe.to_csv(OUT / "detalhe.csv", index=False)

    print("votos.csv:", votos.shape, "| detalhe.csv:", detalhe.shape)
    print("anos/turnos:", sorted(set(zip(votos.ANO_ELEICAO, votos.NR_TURNO))))


if __name__ == "__main__":
    main()