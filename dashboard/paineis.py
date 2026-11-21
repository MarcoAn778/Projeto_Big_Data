"""Gráficos e detalhamento das consultas."""

import pandas as pd
import plotly.express as px
import streamlit as st


CORES = ["#00796B", "#325A93", "#AD501C", "#85528D", "#5B7035", "#9D4659", "#566C7B"]
ROTULOS = {
    "competencia": "Competência", "mes": "Competência", "setor": "Setor",
    "sexo": "Sexo", "raca": "Raça/cor", "grupo": "Grupo", "fluxo": "Fluxo",
    "admissoes": "Admissões", "desligamentos": "Desligamentos", "saldo": "Saldo",
    "salarios_validos": "Salários válidos", "media": "Média (R$)", "razao": "Razão",
    "referencia": "% da maior média", "proporcao": "Participação", "quantidade": "Eventos do grupo",
    "total": "Eventos no denominador", "percentual": "Participação (%)",
}


def rotulos_grupo(dados):
    return dados.sexo + " · " + dados.raca


def mostrar(figura):
    figura.update_layout(
        font=dict(family="Inter, Arial, sans-serif", size=13),
        margin=dict(l=8, r=18, t=14, b=12),
        legend=dict(title_text="", orientation="h", y=-0.23),
        separators=",.",
    )
    st.plotly_chart(figura, width="stretch", config={"displaylogo": False})


def detalhe(dados):
    with st.expander("Ver dados do gráfico"):
        st.dataframe(dados.rename(columns=ROTULOS), hide_index=True, width="stretch")


def saldo(dados):
    dados = dados.assign(mes=pd.to_datetime(dados.competencia).dt.strftime("%m/%Y"),
                         grupo=rotulos_grupo(dados))
    cores = sorted(dados.raca.unique())
    figura = px.line(
        dados, x="mes", y="saldo", color="raca", line_dash="sexo", markers=True,
        color_discrete_map=dict(zip(cores, CORES)),
        labels=ROTULOS, hover_name="grupo",
        hover_data={"admissoes": ":,d", "desligamentos": ":,d"},
    )
    figura.add_hline(y=0, line_color="#8795A6", line_dash="dot")
    mostrar(figura)
    detalhe(dados[["mes", "sexo", "raca", "admissoes", "desligamentos", "saldo"]])


def turnover(dados):
    meses = sorted(dados.competencia.unique(), reverse=True)
    mes = st.selectbox("Competência no gráfico", meses, format_func=lambda dia: dia.strftime("%m/%Y"))
    setores = sorted(dados.loc[dados.competencia == mes, "setor"].unique())
    setor = st.selectbox("Setor no gráfico", setores)
    recorte = dados[(dados.competencia == mes) & (dados.setor == setor)].copy()
    recorte["grupo"] = rotulos_grupo(recorte)
    recorte["razao"] = pd.to_numeric(recorte.razao)
    validos = recorte.dropna(subset=["razao"])
    if validos.empty:
        st.info("A razão fica indefinida para grupos sem admissões.")
    else:
        figura = px.bar(
            validos.sort_values("razao"), x="razao", y="grupo", color="sexo",
            color_discrete_sequence=CORES, labels=ROTULOS,
            hover_data={"admissoes": ":,d", "desligamentos": ":,d"},
            height=max(340, 27 * len(validos) + 105),
        )
        figura.add_vline(x=1, line_color="#8795A6", line_dash="dot")
        figura.update_xaxes(title="Desligamentos por admissão", rangemode="tozero")
        mostrar(figura)
        if len(validos) < len(recorte):
            st.caption("Grupos sem admissões aparecem com razão indefinida na tabela.")
    detalhe(recorte[["setor", "sexo", "raca", "admissoes", "desligamentos", "razao"]])


def salario(dados):
    dados = dados.assign(grupo=rotulos_grupo(dados), media=pd.to_numeric(dados.media),
                         referencia=pd.to_numeric(dados.razao) * 100)
    validos = dados.dropna(subset=["media"])
    if validos.empty:
        st.info("O recorte não tem salários válidos de admissão.")
    else:
        figura = px.bar(
            validos.sort_values("media"), x="media", y="grupo", color="sexo", labels=ROTULOS,
            color_discrete_sequence=CORES,
            hover_data={"referencia": ":.1f", "salarios_validos": ":,d"},
            height=max(340, 27 * len(validos) + 105),
        )
        mostrar(figura)
    detalhe(dados[["sexo", "raca", "salarios_validos", "media", "referencia"]])


def participacao(dados):
    fluxo = st.radio("Fluxo", ("Admissões", "Desligamentos"), horizontal=True)
    recorte = dados.loc[dados.fluxo == fluxo].copy()
    recorte["percentual"] = pd.to_numeric(recorte.proporcao) * 100
    validos = recorte.dropna(subset=["percentual"])
    if validos.empty:
        st.info("O fluxo selecionado tem denominador zero nos setores deste recorte.")
    else:
        figura = px.bar(
            validos.sort_values("setor", ascending=False), x="percentual", y="setor", color="grupo",
            barmode="group", color_discrete_sequence=CORES,
            labels=ROTULOS, hover_data={"quantidade": ":,d", "total": ":,d"},
            height=max(390, 35 * validos.setor.nunique() + 100),
        )
        figura.update_xaxes(range=[0, 100], ticksuffix="%")
        mostrar(figura)
    detalhe(recorte[["setor", "grupo", "fluxo", "quantidade", "total", "percentual"]])


graficos = {"saldo": saldo, "turnover": turnover, "salario": salario, "participacao": participacao}
