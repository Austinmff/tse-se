import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.indicators import BRANCO_NULO, build  # noqa: E402

st.set_page_config(page_title="Mobilização SE", layout="wide")

GRUPOS = {
    "Prioridade alta": "Prioridade alta",
    "Mobilizar": "Chamar para votar",
    "Persuadir": "Conversar e convencer",
    "Manter": "Manter o apoio",
    "Baixa prioridade": "Menos urgente",
}
ORDEM_OPCOES = {
    "votos_potenciais": "Votos que dá para buscar",
    "abst_excedente": "Gente que faltou além do normal",
}


@st.cache_data
def load():
    pasta = Path("data/processed")
    v = sorted(pasta.glob("votos*.csv"))
    d = sorted(pasta.glob("detalhe*.csv"))
    if not v or not d:
        return None, None
    votos = pd.concat([pd.read_csv(f) for f in v], ignore_index=True)
    detalhe = pd.concat([pd.read_csv(f) for f in d], ignore_index=True)
    return votos, detalhe

@st.cache_data
def load_locais():
    arq = Path("data/processed/zonas_locais.csv")
    return pd.read_csv(arq) if arq.exists() else None


votos, detalhe = load()
if votos is None:
    st.error("Os dados ainda não foram preparados. Rode o ETL primeiro.")
    st.stop()

st.title("Onde chamar o povo para votar: Sergipe")
st.write(
    "Este painel mostra em quais lugares vale mais a pena concentrar o trabalho "
    "de conversar com as pessoas e chamá-las para votar no segundo turno. "
    "Ele ajuda a decidir onde agir. Ele não prevê quem vai ganhar."
)
st.caption("Fonte: TSE, resultados oficiais do 1º turno de 2026.")

ano = st.sidebar.selectbox("Ano da eleição", sorted(votos.ANO_ELEICAO.unique(), reverse=True))
turnos = sorted(votos[votos.ANO_ELEICAO == ano].NR_TURNO.unique())
turno = st.sidebar.selectbox("Turno", turnos)
sel = votos[(votos.ANO_ELEICAO == ano) & (votos.NR_TURNO == turno)
            & ~votos.NR_VOTAVEL.isin(BRANCO_NULO)]
nomes = sorted(sel.NM_VOTAVEL.unique())
idx_padrao = next((i for i, n in enumerate(nomes) if "LULA" in n), 0)
candidato = st.sidebar.selectbox("Candidato", nomes, index=idx_padrao)
detalhe_nivel = st.sidebar.radio("Nível de detalhe", ["Cidade", "Zona eleitoral"])
nivel = "municipio" if detalhe_nivel == "Cidade" else "zona"

df = build(votos, detalhe, ano, turno, candidato, nivel)
df["grupo"] = df.categoria.map(GRUPOS)
df["locais"] = ""
if nivel == "zona":
    zl = load_locais()
    if zl is not None:
        df = df.merge(zl, on=["CD_MUNICIPIO", "NR_ZONA"], how="left")
        df["locais"] = df["principais_locais"].fillna("")
    df["local"] = df.NM_MUNICIPIO + " (zona " + df.NR_ZONA.astype(int).astype(str) + ")"
else:
    df["local"] = df.NM_MUNICIPIO

c1, c2, c3, c4 = st.columns(4)
c1.metric("Lugares", len(df))
c2.metric("Prioridade alta", int((df.categoria == "Prioridade alta").sum()))
c3.metric("Chamar para votar", int((df.categoria == "Mobilizar").sum()))
c4.metric("Votos que dá para buscar (máximo)", int(df.votos_potenciais.sum()))

presentes = [g for g in GRUPOS.values() if g in df.grupo.unique()]
padrao = [g for g in ["Prioridade alta", "Chamar para votar"] if g in presentes] or presentes
filtro = st.multiselect("Mostrar os grupos", presentes, default=padrao)
ordem = st.selectbox("Ordenar por", list(ORDEM_OPCOES), format_func=ORDEM_OPCOES.get)

vis = df[df.grupo.isin(filtro)].sort_values(ordem, ascending=False)

tabela = vis[["local", "grupo", "pct_cand", "taxa_abst",
              "votos_potenciais", "abst_excedente", "margem", "locais"]].copy()
tabela["pct_cand"] = (tabela.pct_cand * 100).round(1)
tabela["taxa_abst"] = (tabela.taxa_abst * 100).round(1)
tabela["margem"] = (tabela.margem * 100).round(1)
tabela = tabela.rename(columns={
    "locais": "Maiores locais de votação da zona (só para orientar)",
    "local": "Local",
    "grupo": "Grupo",
    "pct_cand": "% dos votos válidos",
    "taxa_abst": "% que faltou",
    "votos_potenciais": "Votos que dá para buscar",
    "abst_excedente": "Gente que faltou além do normal",
    "margem": "Vantagem sobre o 2º (pontos)",
})
st.dataframe(tabela, use_container_width=True, hide_index=True)
if nivel == "municipio":
    tabela = tabela.drop(columns=["Maiores locais de votação da zona (só para orientar)"])

top = vis.head(15)
fig = px.bar(
    top, x=ordem, y="local", color="grupo", orientation="h",
    title="Os 15 primeiros lugares",
    labels={ordem: ORDEM_OPCOES[ordem], "local": "Local", "grupo": "Grupo"},
)
fig.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig, use_container_width=True)

st.info(
    "Como ler: 'Votos que dá para buscar' é uma conta simples. Pegamos quem faltou "
    "na votação e aplicamos a porcentagem que o candidato teve no lugar. "
    "É um teto, não uma promessa: nem todo mundo que faltou vai votar. "
    "'Gente que faltou além do normal' é quem faltou acima da média do estado; "
    "zero quer dizer que o lugar faltou menos que a média."
)