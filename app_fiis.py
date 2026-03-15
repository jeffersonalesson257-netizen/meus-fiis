import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

st.set_page_config(layout="wide")

# -----------------------------
# Lista de FIIs
# -----------------------------

fiis_lista = [
"HGLG11","KNRI11","XPML11","BTLG11","VISC11",
"MXRF11","CPTS11","XPLG11","BRCO11","PVBI11",
"HGRE11","GGRC11","RBRR11","RECR11","IRDM11",
"VGIR11","VILG11","RBRP11","JSRE11","HSML11"
]

# -----------------------------
# Função preço BR
# -----------------------------

def brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")

# -----------------------------
# Buscar dados
# -----------------------------

@st.cache_data(ttl=300)
def buscar_dados():

    dados = []

    for fii in fiis_lista:

        try:

            ticker = yf.Ticker(f"{fii}.SA")

            hist = ticker.history(period="1d")

            if hist.empty:
                continue

            preco = hist["Close"].iloc[-1]

            dividendos = ticker.dividends.tail(12).sum()

            dy = (dividendos/preco)*100 if preco>0 else 0

            dados.append({
                "Ticker":fii,
                "Preço":preco,
                "Dividendos":dividendos,
                "DY":dy
            })

        except:
            pass

    df = pd.DataFrame(dados)

    return df

df = buscar_dados()

# -----------------------------
# Menu lateral
# -----------------------------

menu = st.sidebar.selectbox(

"Menu",

[
"Dashboard",
"Scanner",
"Ranking",
"Minha Carteira",
"Radar de Risco",
"Simulador"
]

)

# -----------------------------
# Dashboard
# -----------------------------

if menu == "Dashboard":

    st.title("📊 Dashboard de FIIs")

    col1,col2,col3 = st.columns(3)

    col1.metric("FIIs analisados",len(df))
    col2.metric("Dividend Yield médio",f"{df['DY'].mean():.2f}%")
    col3.metric("Preço médio",brl(df["Preço"].mean()))

    fig = px.bar(
        df,
        x="Ticker",
        y="DY",
        title="Dividend Yield dos FIIs"
    )

    st.plotly_chart(fig,use_container_width=True)

    st.dataframe(df)

# -----------------------------
# Scanner
# -----------------------------

elif menu == "Scanner":

    st.title("🔎 Scanner de FIIs")

    dy_min = st.slider("DY mínimo",0.0,15.0,6.0)

    df_filtrado = df[df["DY"]>=dy_min]

    st.write(f"{len(df_filtrado)} FIIs encontrados")

    st.dataframe(df_filtrado)

    # exportar excel
    buffer = BytesIO()
    df_filtrado.to_excel(buffer,index=False)

    st.download_button(
        "📥 Exportar Excel",
        data=buffer.getvalue(),
        file_name="scanner_fiis.xlsx"
    )

# -----------------------------
# Ranking
# -----------------------------

elif menu == "Ranking":

    st.title("🏆 Ranking de FIIs")

    df["Score"] = (
        df["DY"]*0.7 +
        (1/df["Preço"])*30
    )

    ranking = df.sort_values("Score",ascending=False)

    st.dataframe(ranking)

    fig = px.bar(
        ranking.head(10),
        x="Ticker",
        y="Score",
        title="Top 10 FIIs"
    )

    st.plotly_chart(fig,use_container_width=True)

# -----------------------------
# Carteira
# -----------------------------

elif menu == "Minha Carteira":

    st.title("💼 Minha Carteira")

    ticker = st.selectbox("FII",fiis_lista)

    quantidade = st.number_input("Quantidade",1)

    preco_compra = st.number_input("Preço compra",0.0)

    if st.button("Adicionar"):

        valor = quantidade * preco_compra

        st.success(f"Investimento total: {brl(valor)}")

# -----------------------------
# Radar de risco
# -----------------------------

elif menu == "Radar de Risco":

    st.title("📡 Radar de Risco")

    categorias = [
    "Liquidez",
    "Vacância",
    "Gestão",
    "Diversificação",
    "Dividendos",
    "Risco"
    ]

    valores = np.random.randint(4,10,6)

    categorias.append(categorias[0])
    valores = np.append(valores,valores[0])

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill='toself'
    ))

    st.plotly_chart(fig)

# -----------------------------
# Simulador
# -----------------------------

elif menu == "Simulador":

    st.title("🔮 Simulador de Dividendos")

    capital = st.number_input("Capital inicial",10000)

    aporte = st.number_input("Aporte mensal",1000)

    dy = st.slider("Dividend Yield anual",5,15,10)

    anos = st.slider("Anos",1,30,10)

    meses = anos*12

    saldo = capital

    historico = []

    taxa = dy/100/12

    for i in range(meses):

        renda = saldo*taxa

        saldo += renda + aporte

        historico.append(saldo)

    fig = px.line(
        y=historico,
        title="Crescimento do patrimônio"
    )

    st.plotly_chart(fig)

    renda_final = saldo*taxa

    st.metric(
        "Renda mensal estimada",
        brl(renda_final)
    )
