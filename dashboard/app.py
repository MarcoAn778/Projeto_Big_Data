"""Aplicação Streamlit conectada ao PostgreSQL do projeto."""

from datetime import date, datetime
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RAIZ), str(RAIZ / "codigo")]

from caged.validacao import ErroValidacao
from dashboard.consultas import CATALOGO, Filtros, carregar_indicador, consultar
from dashboard.paineis import graficos


PAINEIS = {
    "saldo": ("Saldo mensal", "Admissões menos desligamentos, por sexo e raça/cor em cada competência."),
    "turnover": ("Turnover setorial", "Desligamentos por admissão em cada setor, mês e grupo. A linha de referência é 1,0."),
    "salario": ("Salário de admissão", "Média ponderada dos salários válidos de admissão. O maior valor do recorte é a referência de 100%."),
    "participacao": (
        "Participação",
        "A série de mulheres respeita o filtro de raça/cor. A série de pessoas negras (pretas e pardas) "
        "respeita o filtro de sexo. Cada proporção usa o total de seu fluxo e setor no recorte correspondente.",
    ),
}
TZ = ZoneInfo("America/Bahia")


@st.cache_data(ttl=300, max_entries=1, show_spinner=False)
def catalogo():
    return pd.DataFrame(consultar(CATALOGO))


@st.cache_data(ttl=60, max_entries=64, show_spinner=False)
def resultado(painel, filtros):
    return pd.DataFrame(carregar_indicador(painel, filtros)), datetime.now(TZ)


def opcoes(dados, categoria):
    return dados.loc[dados.filtro == categoria].set_index("codigo").rotulo.to_dict()


def multiselect(rotulo, opcoes, key):
    return tuple(st.multiselect(
        rotulo, list(opcoes), format_func=opcoes.__getitem__, key=key, placeholder="Todas as opções",
    ))


def filtros(dados):
    competencias = [date.fromisoformat(codigo) for codigo in opcoes(dados, "competencias")]
    with st.sidebar:
        st.header("Filtros")
        if len(competencias) == 1:
            inicio = fim = competencias[0]
            st.caption(f"Competência disponível · {inicio:%m/%Y}")
        else:
            inicio, fim = st.select_slider(
                "Competência", options=competencias, value=(competencias[0], competencias[-1]),
                format_func=lambda dia: dia.strftime("%m/%Y"),
            )
        regioes = multiselect("Região", opcoes(dados, "regioes"), "regioes")
        ufs_disponiveis = dados[dados.filtro == "ufs"]
        if regioes:
            ufs_disponiveis = ufs_disponiveis[ufs_disponiveis.regiao_uf.isin(regioes)]
        ufs = multiselect("UF", opcoes(ufs_disponiveis, "ufs"), f"uf_{regioes}")
        setores = multiselect("Setor · seção CNAE", opcoes(dados, "setores"), "setores")
        sexos = multiselect("Sexo", opcoes(dados, "sexos"), "sexos")
        racas = multiselect("Raça/cor", opcoes(dados, "racas"), "racas")
        idades = multiselect("Faixa etária", opcoes(dados, "idades"), "idades")
    return Filtros(inicio, fim, regioes, ufs, setores, sexos, racas, idades)


def mostrar_erro():
    st.error("Não foi possível consultar o banco de dados agora.")
    st.caption("Verifique se o serviço PostgreSQL está ativo e se a conexão desta aplicação está autorizada. Use Atualizar dados para tentar novamente.")


def main():
    st.set_page_config(
        page_title="Emprego formal em movimento",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    load_dotenv(RAIZ / ".env")
    if arquivo_ambiente := os.getenv("CAGED_ENV_FILE"):
        load_dotenv(Path(arquivo_ambiente).expanduser())
    st.markdown(
        '<p style="color:#147568;font-weight:650;letter-spacing:.07em;margin:0">'
        'NOVO CAGED · ODS 5 E 18</p>',
        unsafe_allow_html=True,
    )
    st.title("Emprego formal em movimento")
    st.caption("Admissões, desligamentos e salários no Brasil por sexo e raça/cor.")

    if st.sidebar.button("Atualizar dados", icon=":material/refresh:", width="stretch"):
        catalogo.clear()
        resultado.clear()

    try:
        dados_catalogo = catalogo()
        if dados_catalogo.empty:
            st.info("O banco ainda não tem competências disponíveis para análise.")
            return
        recorte = filtros(dados_catalogo)
        painel = st.radio(
            "Indicador", list(PAINEIS), format_func=lambda nome: PAINEIS[nome][0],
            horizontal=True, label_visibility="collapsed",
        )
        titulo, descricao = PAINEIS[painel]
        st.subheader(titulo)
        st.caption(descricao)
        with st.spinner("Consultando o PostgreSQL…"):
            dados, consultado_em = resultado(painel, recorte)
    except ErroValidacao:
        mostrar_erro()
        return

    if dados.empty:
        st.info("Nenhuma movimentação para os filtros escolhidos.")
        return

    graficos[painel](dados)
    st.caption(
        f"Fonte: Novo CAGED/MTE · arquivos MOV · última consulta para este recorte às "
        f"{consultado_em:%H:%M:%S} (Bahia)."
    )
    with st.expander("Como interpretar os dados"):
        st.markdown(
            "O recorte abrange movimentações do emprego formal. A razão desligamentos/admissões "
            "é uma medida de fluxo, pois os arquivos MOV não trazem estoque de vínculos. "
            "**Não identificado** e **Não informada** são categorias distintas de raça/cor. "
            "A comparação salarial é descritiva e a base agregada carece de controles "
            "por ocupação ou escolaridade."
        )


if __name__ == "__main__":
    main()
