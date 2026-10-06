import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.indicators import BRANCO_NULO, build  # noqa: E402

st.set_page_config(page_title="Mobilização SE", layout="wide")


@st.cache_data
def load():
    pasta = Path("data/processed")
    v = sorted(pasta.glob("votos*.csv"))
    d = sorted(pasta.glob("detalhe*.csv"))
    if not v or not d:
        st.error("Nenhum arquivo processado em data/processed. Rode o ETL primeiro.")
        st.stop()
    votos = pd.concat([pd.read_csv(f) for f in v], ignore_index=True)
    detalhe = pd.concat([pd.read_csv(f) for f in d], ignore_index=True)
    return votos, detalhe


votos, detalhe = load()

st.title("Prioridades territoriais: Sergipe")
st.caption("Fonte: TSE, resultados oficiais do 1º turno de 2026. Dados agregados por município.")

ano = st.sidebar.selectbox("Ano", sorted(votos.ANO_ELEICAO.unique(), reverse=True))
turnos = sorted(votos[votos.ANO_ELEICAO == ano].NR_TURNO.unique())
turno = st.sidebar.selectbox("Turno", turnos)
sel = votos[(votos.ANO_ELEICAO == ano) & (votos.NR_TURNO == turno)
            & ~votos.NR_VOTAVEL.isin(BRANCO_NULO)]
candidato = st.sidebar.selectbox("Candidato", sorted(sel.NM_VOTAVEL.unique()))
nivel = "municipio"

df = build(votos, detalhe, ano, turno, candidato, nivel)
rotulo = ["NM_MUNICIPIO"] + (["NR_ZONA"] if nivel == "zona" else [])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Territórios", len(df))
c2.metric("Mobilizar", int((df.categoria == "Mobilizar").sum()))
c3.metric("Persuadir", int((df.categoria == "Persuadir").sum()))
c4.metric("Votos potenciais (total)", int(df.votos_potenciais.sum()))

CATEGORIAS = ["Mobilizar", "Persuadir", "Manter", "Baixa prioridade"]
presentes = [c for c in CATEGORIAS if c in df.categoria.unique()]
padrao = [c for c in ["Mobilizar", "Persuadir"] if c in presentes] or presentes
filtro = st.multiselect("Categorias", presentes, default=padrao)
ordem = st.selectbox(
    "Ordenar por", ["votos_potenciais", "abst_excedente"],
    format_func=lambda c: {"votos_potenciais": "votos potenciais",
                           "abst_excedente": "abstenção acima da média"}[c],
)
vis = df[df.categoria.isin(filtro)].sort_values(ordem, ascending=False)

tabela = vis[rotulo + ["categoria", "pct_cand", "taxa_abst",
                       "votos_potenciais", "margem"]].copy()
tabela["pct_cand"] = (tabela.pct_cand * 100).round(1)
tabela["taxa_abst"] = (tabela.taxa_abst * 100).round(1)
tabela["margem"] = (tabela.margem * 100).round(1)
tabela = tabela.rename(columns={
    "pct_cand": "% votos válidos", "taxa_abst": "% abstenção",
    "votos_potenciais": "votos potenciais", "margem": "margem (p.p.)",
})
st.dataframe(tabela, use_container_width=True, hide_index=True)

top = vis.head(15).copy()
top["territorio"] = top[rotulo].astype(str).agg(" / ".join, axis=1)
fig = px.bar(top, x="votos_potenciais", y="territorio", color="categoria",
             orientation="h", title="Top 15 por votos potenciais")
fig.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig, use_container_width=True)

st.info(
    "Votos potenciais = abstenções × % de votos válidos do candidato no território. "
    "É uma estimativa para priorizar esforço, não uma previsão de resultado. "
    "Abstenção não equivale a apoio."
)