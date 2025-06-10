# streamlit_app.py (versão aprimorada para uso com Magis e seleção de marketplaces)

# --- IMPORTS E CONFIG ---
import streamlit as st
import pandas as pd
import math
import io
import os

st.set_page_config(layout="wide")
st.title("Calculadora de Preços para Marketplaces")

# --- TABELAS DE FRETE PADRÃO ---
default_tabela_frete_ml = pd.DataFrame([
    {"PesoMaximoG": 300, "CustoFrete": 19.95},
    {"PesoMaximoG": 500, "CustoFrete": 21.45},
    {"PesoMaximoG": 1000, "CustoFrete": 22.45},
    {"PesoMaximoG": 2000, "CustoFrete": 23.45},
    {"PesoMaximoG": 3000, "CustoFrete": 24.95},
    {"PesoMaximoG": 4000, "CustoFrete": 26.95},
    {"PesoMaximoG": 5000, "CustoFrete": 28.45},
])

default_tabela_frete_amazon = pd.DataFrame([
    {"PesoMaximoG": 249, "CustoFrete": 15.94},
    {"PesoMaximoG": 499, "CustoFrete": 16.94},
    {"PesoMaximoG": 999, "CustoFrete": 17.94},
    {"PesoMaximoG": 1990, "CustoFrete": 18.44},
    {"PesoMaximoG": 2990, "CustoFrete": 21.69},
    {"PesoMaximoG": 3990, "CustoFrete": 22.94},
    {"PesoMaximoG": 4990, "CustoFrete": 28.44},
    {"PesoMaximoG": 5990, "CustoFrete": 31.30},
    {"PesoMaximoG": 6990, "CustoFrete": 33.13},
    {"PesoMaximoG": 7990, "CustoFrete": 33.94},
    {"PesoMaximoG": 8990, "CustoFrete": 40.29},
    {"PesoMaximoG": 9990, "CustoFrete": 46.65},
    {"PesoMaximoG": -1, "CustoFrete": 3.50},
])

if "tabela_frete_ml" not in st.session_state:
    st.session_state.tabela_frete_ml = default_tabela_frete_ml.copy()
if "tabela_frete_amazon" not in st.session_state:
    st.session_state.tabela_frete_amazon = default_tabela_frete_amazon.copy()

# --- SIDEBAR ---
st.sidebar.header("Parâmetros Gerais")
margem_desejada = st.sidebar.number_input("Margem de Lucro Desejada (%)", min_value=0.0, value=30.0, step=1.0)
custo_embalagem = st.sidebar.number_input("Custo da Embalagem (R$)", min_value=0.0, value=0.0, step=0.10)
imposto_perc = st.sidebar.number_input("Alíquota de Imposto (%)", min_value=0.0, max_value=99.0, value=7.0, step=0.5)

st.sidebar.header("Selecionar Marketplaces")
usar_shopee = st.sidebar.checkbox("Shopee", value=True)
usar_shein = st.sidebar.checkbox("Shein", value=True)
usar_ml = st.sidebar.checkbox("Mercado Livre", value=True)
usar_amazon = st.sidebar.checkbox("Amazon", value=True)

st.sidebar.header("Comissões dos Marketplaces (%)")
comissoes_input = {}
if usar_shopee:
    comissoes_input["Shopee"] = st.sidebar.number_input("Shopee", min_value=0.0, max_value=100.0, value=20.0)
if usar_shein:
    comissoes_input["Shein"] = st.sidebar.number_input("Shein", min_value=0.0, max_value=100.0, value=16.0)
if usar_ml:
    comissoes_input["Mercado Livre"] = st.sidebar.number_input("Mercado Livre", min_value=0.0, max_value=100.0, value=17.0)
if usar_amazon:
    comissoes_input["Amazon"] = st.sidebar.number_input("Amazon", min_value=0.0, max_value=100.0, value=15.0)

# --- FRETE CONFIG (mantido) ---
st.sidebar.header("Configuração de Frete")
with st.sidebar.expander("Mercado Livre"):
    edited_ml_df = st.data_editor(st.session_state.tabela_frete_ml, num_rows="dynamic")
    if edited_ml_df is not None and not edited_ml_df.isnull().values.any():
        st.session_state.tabela_frete_ml = edited_ml_df.copy()

with st.sidebar.expander("Amazon"):
    edited_amazon_df = st.data_editor(st.session_state.tabela_frete_amazon, num_rows="dynamic")
    if edited_amazon_df is not None and not edited_amazon_df.isnull().values.any():
        st.session_state.tabela_frete_amazon = edited_amazon_df.copy()

# --- COLUNAS PADRÃO ---
st.sidebar.header("Colunas da Planilha")
coluna_custo = st.sidebar.text_input("Nome da Coluna de Custo", value="Custo Produto (N)")
coluna_peso = st.sidebar.text_input("Nome da Coluna de Peso (g)", value="Peso (kg) (N)")
coluna_preco_saida = "Preço Anúncio (S)"

# --- UPLOAD DE PLANILHA ---
st.header("1. Carregar Planilha")
uploaded_file = st.file_uploader("Escolha um arquivo Excel (.xls, .xlsx) ou CSV (.csv)", type=["xls", "xlsx", "csv"])
df_original = None
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".xlsx"):
            df_original = pd.read_excel(uploaded_file, engine="openpyxl")
        elif uploaded_file.name.endswith(".xls"):
            import xlrd
            df_original = pd.read_excel(uploaded_file, engine="xlrd")
        elif uploaded_file.name.endswith(".csv"):
            df_original = pd.read_csv(uploaded_file, sep=None, engine="python")
        st.success("Arquivo carregado com sucesso!")
        st.dataframe(df_original.head())
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")

# --- CÁLCULO E RESULTADO ---
from calculadora_modulo import calcular_preco_venda  # seu módulo de cálculo externo

st.header("2. Calcular Preços")
if df_original is not None and comissoes_input:
    if st.button("Calcular Preços de Venda"):
        df_resultado = df_original.copy()
        for idx, row in df_resultado.iterrows():
            custo = row.get(coluna_custo, 0)
            peso = row.get(coluna_peso, 0)
            resultados = calcular_preco_venda(
                custo_produto=custo,
                custo_embalagem=custo_embalagem,
                margem_desejada_perc=margem_desejada,
                imposto_perc=imposto_perc,
                peso_g=peso,
                comissoes_perc=comissoes_input,
                tabela_frete_ml_df=st.session_state.tabela_frete_ml,
                tabela_frete_amazon_df=st.session_state.tabela_frete_amazon
            )
            # Escreve resultado no campo de preço final (primeiro marketplace selecionado)
            for marketplace, dados in resultados.items():
                if "preco_venda" in dados:
                    df_resultado.at[idx, coluna_preco_saida] = dados["preco_venda"]
                    break  # só escreve uma vez
        st.header("3. Resultado")
        st.dataframe(df_resultado)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_resultado.to_excel(writer, index=False)
        st.download_button(
            label="Download Resultado (.xlsx)",
            data=output.getvalue(),
            file_name="resultado_magis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Por favor, carregue uma planilha e selecione pelo menos um marketplace.")
