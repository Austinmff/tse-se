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
    votos = pd.read_csv("data/processed/votos.csv")
    detalhe = pd.read_csv("data/processed/detalhe.csv")
    return votos, detalhe


votos, detalhe = load()

st.title("Prioridades territoriais: Sergipe")
st.caption("Fonte: TSE, dados abertos. Dados agregados por município e zona eleitoral.")

ano = st.sidebar.selectbox("Ano", sorted(votos.ANO_ELEICAO.unique(), reverse=True))
turnos = sorted(votos[votos.ANO_ELEICAO == ano].NR_TURNO.unique())
turno = st.sidebar.selectbox("Turno", turnos)
sel = votos[(votos.ANO_ELEICAO == ano) & (votos.NR_TURNO == turno)
            & ~votos.NR_VOTAVEL.isin(BRANCO_NULO)]
candidato = st.sidebar.selectbox("Candidato", sorted(sel.NM_VOTAVEL.unique()))
nivel = st.sidebar.radio("Nível", ["municipio", "zona"])

df = build(votos, detalhe, ano, turno, candidato, nivel)
rotulo = ["NM_MUNICIPIO"] + (["NR_ZONA"] if nivel == "zona" else [])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Territórios", len(df))
c2.metric("Mobilizar", int((df.categoria == "Mobilizar").sum()))
c3.metric("Persuadir", int((df.categoria == "Persuadir").sum()))
c4.metric("Votos potenciais (total)", int(df.votos_potenciais.sum()))

filtro = st.multiselect("Categorias", list(df.categoria.unique()),
                        default=["Mobilizar", "Persuadir"])
vis = df[df.categoria.isin(filtro)]

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