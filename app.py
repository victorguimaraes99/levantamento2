import streamlit as st
import pandas as pd
import plotly.express as px
import re

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Análise de Periódicos", layout="wide")

# SISTEMA DE SENHA
def check_password():
    def password_entered():
        if st.session_state["password"] == "1234":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>Acesso Restrito</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Digite a senha para visualizar os dados", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", False)

if check_password():

    @st.cache_data
    def carregar_dados():
        # Carregamento da base conforme solicitado
        df = pd.read_excel("spell.xlsx")
        df.columns = [c.strip() for c in df.columns]
        # Métrica de eficiência (Citações por Documento)
        df['CIT_POR_DOC'] = (df['CITAÇÕES'] / df['DOCUMENTOS']).round(2)
        return df

    df = carregar_dados()

    st.title("Produção Científica: Painel de Periódicos")
    st.markdown("---")

    # ==============================
    # FILTROS E BUSCA (ÁREA CENTRAL)
    # ==============================
    
    col_busca, col_select = st.columns([1, 1])
    with col_busca:
        busca = st.text_input("Buscar por Nome ou ISSN", placeholder="Ex: 2177-6083...").lower()
    with col_select:
        lista_periodicos = sorted(df['periodico'].unique())
        selecionados = st.multiselect("Selecionar Periódicos Específicos", options=lista_periodicos)

    st.write("### ⚙️ Refinar por Indicadores")
    
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        h_min, h_max = int(df['ÍNDICE H'].min()), int(df['ÍNDICE H'].max())
        filtro_h = st.slider("Índice H", h_min, h_max, (h_min, h_max))
    with f2:
        cit_min, cit_max = int(df['CITAÇÕES'].min()), int(df['CITAÇÕES'].max())
        filtro_cit = st.slider("Citações", cit_min, cit_max, (cit_min, cit_max))
    with f3:
        ace_min, ace_max = int(df['ACESSOS'].min()), int(df['ACESSOS'].max())
        filtro_ace = st.slider("Acessos", ace_min, ace_max, (ace_min, ace_max))
    with f4:
        doc_min, doc_max = int(df['DOCUMENTOS'].min()), int(df['DOCUMENTOS'].max())
        filtro_doc = st.slider("Documentos", doc_min, doc_max, (doc_min, doc_max))

    # --- LÓGICA DE FILTRAGEM ---
    df_filtrado = df.copy()
    
    if busca:
        df_filtrado = df_filtrado[
            (df_filtrado['periodico'].str.lower().str.contains(busca)) | 
            (df_filtrado['ISSN'].astype(str).str.contains(busca))
        ]
    
    if selecionados:
        df_filtrado = df_filtrado[df_filtrado['periodico'].isin(selecionados)]
        
    df_filtrado = df_filtrado[
        (df_filtrado['ÍNDICE H'] >= filtro_h[0]) & (df_filtrado['ÍNDICE H'] <= filtro_h[1]) &
        (df_filtrado['CITAÇÕES'] >= filtro_cit[0]) & (df_filtrado['CITAÇÕES'] <= filtro_cit[1]) &
        (df_filtrado['ACESSOS'] >= filtro_ace[0]) & (df_filtrado['ACESSOS'] <= filtro_ace[1]) &
        (df_filtrado['DOCUMENTOS'] >= filtro_doc[0]) & (df_filtrado['DOCUMENTOS'] <= filtro_doc[1])
    ]

    st.markdown("---")

    # ==============================
    # EVIDÊNCIA DE TOTAIS (KPIs)
    # ==============================
    if not df_filtrado.empty:
        st.subheader("Totais da Seleção")
        
        # Criando 4 colunas para os totais principais
        t1, t2, t3, t4 = st.columns(4)
        
        # Formatação para milhar com ponto (estilo brasileiro)
        def fmt(valor):
            return f"{int(valor):,}".replace(",", ".")

        t1.metric("Total de CITAÇÕES", fmt(df_filtrado['CITAÇÕES'].sum()))
        t2.metric("Total de ACESSOS", fmt(df_filtrado['ACESSOS'].sum()))
        t3.metric("Total de DOWNLOADS", fmt(df_filtrado['DOWNLOADS'].sum()))
        t4.metric("Total de DOCUMENTOS", fmt(df_filtrado['DOCUMENTOS'].sum()))
        
        st.markdown("---")

        # ==============================
        # GRÁFICOS E TABELA
        # ==============================
        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.subheader("Ranking por Citações")
            fig_bar = px.bar(
                df_filtrado.sort_values("CITAÇÕES", ascending=True),
                x="CITAÇÕES", y="periodico", color="ÍNDICE H",
                orientation='h', template="simple_white",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_graf2:
            st.subheader("Acessos vs Downloads")
            fig_scat = px.scatter(
                df_filtrado, x="ACESSOS", y="DOWNLOADS", size="CITAÇÕES",
                hover_name="periodico", color="ÍNDICE H", template="simple_white"
            )
            st.plotly_chart(fig_scat, use_container_width=True)

        st.subheader("Lista Detalhada")
        st.dataframe(df_filtrado.sort_values("CITAÇÕES", ascending=False), use_container_width=True, hide_index=True)

    else:
        st.warning("Nenhum periódico encontrado para os filtros aplicados.")

    # Botão de Logout
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sair e Bloquear Dados"):
        st.session_state.clear()
        st.rerun()

st.caption("Dashboard de Análise Bibliométrica | Dados Protegidos")
