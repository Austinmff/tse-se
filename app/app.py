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
NIVEIS = ["Cidade", "Zona eleitoral", "Bairros de Aracaju", "Escolas de Aracaju"]
ARA = Path("data/processed/aracaju")


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


@st.cache_data
def load_aracaju(nome):
    v = ARA / f"{nome}_votos.csv"
    d = ARA / f"{nome}_detalhe.csv"
    if not v.exists() or not d.exists():
        return None, None, None
    e = ARA / f"{nome}_extra.csv"
    extra = pd.read_csv(e) if e.exists() else None
    return pd.read_csv(v), pd.read_csv(d), extra


@st.cache_data
def load_incertos():
    arq = ARA / "incertos.csv"
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
with st.expander("Como funciona? (leia primeiro)", expanded=True):
    st.markdown(
        """
**O que é isto?**
Um mapa de onde tem mais gente que **deixou de votar** em lugares onde o candidato escolhido
foi bem. A ideia é decidir onde conversar com as pessoas e chamá-las para votar no 2º turno.

**De onde vêm os números?**
Do resultado oficial do TSE, do 1º turno (4 de outubro de 2026). São só totais por cidade, zona,
bairro ou escola. Não há informação sobre nenhuma pessoa.

**Como ler**
- **% que faltou:** de cada 100 eleitores do lugar, quantos não foram votar.
- **Votos que dá para buscar:** quem faltou, multiplicado pela votação do candidato no lugar. É o
  máximo possível, não uma promessa. Nem todo mundo que faltou vai votar agora.
- **Gente que faltou além do normal:** só quem passou da média de faltas do estado.
- **Grupos:** "Prioridade alta" são os lugares que, somados, concentram metade dos votos que dá
  para buscar. "Chamar para votar" são lugares de boa votação e muita falta.

**O que isto NÃO faz**
Não é pesquisa e não prevê quem vai ganhar. Também não diz em quem as pessoas que faltaram votariam.

**Cuidados**
- O bairro mostrado é o da escola onde se vota, que nem sempre é onde a pessoa mora.
- Algumas escolas de Aracaju têm números que não combinam entre as listas oficiais. Elas ficam de
  fora do ranking e aparecem numa caixa à parte.
- Use junto com o que quem conhece o bairro sabe. Quem vive lá corrige o painel melhor que qualquer número.
        """
    )

ano = st.sidebar.selectbox("Ano da eleição", sorted(votos.ANO_ELEICAO.unique(), reverse=True))
turnos = sorted(votos[votos.ANO_ELEICAO == ano].NR_TURNO.unique())
turno = st.sidebar.selectbox("Turno", turnos)
sel = votos[(votos.ANO_ELEICAO == ano) & (votos.NR_TURNO == turno)
            & ~votos.NR_VOTAVEL.isin(BRANCO_NULO)]
nomes = sorted(sel.NM_VOTAVEL.unique())
idx_padrao = next((i for i, n in enumerate(nomes) if "LULA" in n), 0)
candidato = st.sidebar.selectbox("Candidato", nomes, index=idx_padrao)
detalhe_nivel = st.sidebar.radio("Nível de detalhe", NIVEIS)

arac = detalhe_nivel in NIVEIS[2:]
nivel = "zona" if detalhe_nivel == "Zona eleitoral" else "municipio"

if arac:
    if ano != 2026 or turno != 1:
        st.warning("Os dados de Aracaju existem só para o 1º turno de 2026.")
        st.stop()
    nome_arq = "bairros" if detalhe_nivel.startswith("Bairros") else "escolas"
    va, da, extra = load_aracaju(nome_arq)
    if va is None:
        st.warning("Os dados de Aracaju ainda não foram preparados. Rode: python -m src.build_aracaju")
        st.stop()
    num = sel[sel.NM_VOTAVEL == candidato].NR_VOTAVEL.iloc[0]
    cand_ara = va[va.NR_VOTAVEL == num].NM_VOTAVEL.iloc[0]
    df = build(va, da, 2026, 1, cand_ara)
    df["local"] = df.NM_MUNICIPIO
    df["locais"] = ""
    if extra is not None:
        df = df.merge(extra[["NM_MUNICIPIO", "pct_incerto"]], on="NM_MUNICIPIO", how="left")
else:
    df = build(votos, detalhe, ano, turno, candidato, nivel)
    df["locais"] = ""
    if nivel == "zona":
        zl = load_locais()
        if zl is not None:
            df = df.merge(zl, on=["CD_MUNICIPIO", "NR_ZONA"], how="left")
            df["locais"] = df["principais_locais"].fillna("")
        df["local"] = df.NM_MUNICIPIO + " (zona " + df.NR_ZONA.astype(int).astype(str) + ")"
    else:
        df["local"] = df.NM_MUNICIPIO

df["grupo"] = df.categoria.map(GRUPOS)

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

colunas = ["local", "grupo", "pct_cand", "taxa_abst",
           "votos_potenciais", "abst_excedente", "margem"]
if nivel == "zona" and df["locais"].str.len().gt(0).any():
    colunas.append("locais")
if detalhe_nivel == "Bairros de Aracaju" and "pct_incerto" in df.columns:
    colunas.append("pct_incerto")

tabela = vis[colunas].copy()
tabela["pct_cand"] = (tabela.pct_cand * 100).round(1)
tabela["taxa_abst"] = (tabela.taxa_abst * 100).round(1)
tabela["margem"] = (tabela.margem * 100).round(1)
tabela = tabela.rename(columns={
    "local": "Local",
    "grupo": "Grupo",
    "pct_cand": "% dos votos válidos",
    "taxa_abst": "% que faltou",
    "votos_potenciais": "Votos que dá para buscar",
    "abst_excedente": "Gente que faltou além do normal",
    "margem": "Vantagem sobre o 2º (pontos)",
    "locais": "Maiores locais de votação da zona (só para orientar)",
    "pct_incerto": "% dos eleitores do bairro em escolas com dado incerto",
})
st.dataframe(tabela, use_container_width=True, hide_index=True)

top = vis.head(15)
fig = px.bar(
    top, x=ordem, y="local", color="grupo", orientation="h",
    title="Os 15 primeiros lugares",
    labels={ordem: ORDEM_OPCOES[ordem], "local": "Local", "grupo": "Grupo"},
)
fig.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig, use_container_width=True)

if arac:
    inc = load_incertos()
    if inc is not None:
        with st.expander(f"Escolas de Aracaju com dado incerto ({len(inc)}): ficam fora do ranking"):
            st.write(
                "Nestas escolas, o número de eleitores da lista oficial não combina com "
                "os votos apurados (por exemplo, escolas novas ou seções que mudaram de "
                "lugar). Para não passar um número errado, elas não entram na conta."
            )
            st.dataframe(inc.rename(columns={
                "NR_ZONA": "Zona", "NR_LOCAL_VOTACAO": "Nº do local", "nome": "Escola",
                "bairro": "Bairro", "aptos": "Eleitores na lista", "votos": "Votos apurados",
                "motivo": "Por que é incerto",
            }), use_container_width=True, hide_index=True)
    st.info(
        "Em Aracaju, os grupos são comparados com a média da própria cidade. "
        "O bairro mostrado é o da escola onde a pessoa vota, que nem sempre é onde "
        "ela mora. A lista de eleitores é de 01/10/2026."
    )

st.info(
    "Como ler: 'Votos que dá para buscar' é uma conta simples. Pegamos quem faltou "
    "na votação e aplicamos a porcentagem que o candidato teve no lugar. "
    "É um teto, não uma promessa: nem todo mundo que faltou vai votar. "
    "'Gente que faltou além do normal' é quem faltou acima da média; "
    "zero quer dizer que o lugar faltou menos que a média."
)