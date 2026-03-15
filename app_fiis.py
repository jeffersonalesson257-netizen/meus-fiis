import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO GOOGLE SHEETS ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# No Streamlit Cloud, você usará st.secrets para segurança, 
# mas para rodar localmente use o arquivo json:
def buscar_dados_sheets():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        client = gspread.authorize(creds)
        sh = client.open("Carteira_FII").worksheet("Dados")
        return pd.DataFrame(sh.get_all_records())
    except Exception as e:
        st.error(f"Erro ao conectar no Google Sheets: {e}")
        return pd.DataFrame()

# --- CÓDIGO DO DASHBOARD ---
st.title("📊 Minha Carteira Automática (Via Google Sheets)")

df_carteira = buscar_dados_sheets()

if not df_carteira.empty:
    # ... aqui continua a lógica de cálculo que criamos antes ...
    st.success("Dados carregados com sucesso da nuvem!")
    st.dataframe(df_carteira)
else:
    st.warning("Aguardando conexão com a planilha...")
