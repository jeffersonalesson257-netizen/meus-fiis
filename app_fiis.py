import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Gestor de FIIs Pro", layout="wide")

# --- FUNÇÃO DE SCRAPING (Melhoria de Dados) ---
def buscar_indicadores(ticker):
    # Exemplo simplificado de extração de indicadores fundamentais
    url = f"https://www.fundamentus.com.br/detalhes.php?papel={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Aqui você capturaria as tags específicas de P/VP e Dividend Yield
        # Para este exemplo, manteremos valores simulados que seriam extraídos
        return {"P/VP": 0.95, "DY_12M": "10.5%"} 
    except:
        return {"P/VP": "N/A", "DY_12M": "N/A"}

# --- BANCO DE DADOS DA CARTEIRA ---
# Na prática, isso poderia vir de um Excel ou SQL
minha_carteira = {
    "HGLG11": {"quantidade": 10, "preco_medio": 160.00},
    "KNRI11": {"quantidade": 15, "preco_medio": 155.00},
    "BTLG11": {"quantidade": 20, "preco_medio": 98.50}
}

st.title("🚀 Dashboard Inteligente de FIIs")

# --- CÁLCULOS E EXIBIÇÃO ---
dados_finais = []

for ticker_bruto, info_pessoal in minha_carteira.items():
    ticker = f"{ticker_bruto}.SA"
    fii = yf.Ticker(ticker)
    preco_atual = fii.history(period="1d")['Close'].iloc[-1]
    
    # Cálculos de Performance
    valor_investido = info_pessoal['quantidade'] * info_pessoal['preco_medio']
    valor_atual = info_pessoal['quantidade'] * preco_atual
    lucro_prejuizo = valor_atual - valor_investido
    porcentagem = (lucro_prejuizo / valor_investido) * 100
    
    # Indicadores Extra (Scraping)
    extra = buscar_indicadores(ticker_bruto)
    
    dados_finais.append({
        "Fundo": ticker_bruto,
        "Qtd": info_pessoal['quantidade'],
        "Preço Médio": f"R$ {info_pessoal['preco_medio']:.2f}",
        "Cotação Atual": f"R$ {preco_atual:.2f}",
        "P/VP": extra['P/VP'],
        "Resultado (R$)": f"R$ {lucro_prejuizo:.2f}",
        "Resultado (%)": f"{porcentagem:.2f}%"
    })

# --- INTERFACE ---
df = pd.DataFrame(dados_finais)

# Filtro de Alerta: FIIs com P/VP abaixo de 1.0 (Baratos)
st.subheader("⚠️ Oportunidades (P/VP < 1.0)")
oportunidades = df[df['P/VP'].astype(float) < 1.0]
st.dataframe(oportunidades, use_container_width=True)

st.divider()

st.subheader("📊 Minha Performance")
st.table(df)

# Gráfico de Composição da Carteira
st.write("### Divisão do Patrimônio")
st.bar_chart(df.set_index('Fundo')['Resultado (%)'])