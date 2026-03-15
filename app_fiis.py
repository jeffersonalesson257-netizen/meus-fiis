import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Jefferson FII Analytics",
    layout="wide",
    page_icon="📈"
)

st.title("📊 Plataforma Profissional de Análise de FIIs")

# ------------------------------------------------
# LISTA DE FIIs PARA ANALISAR
# ------------------------------------------------

lista_fiis = [
"HGLG11","KNRI11","XPML11","BTLG11","VISC11",
"MXRF11","CPTS11","XPLG11","BRCO11","PVBI11",
"HGRE11","GGRC11","RBRR11","RECR11"
]

# ------------------------------------------------
# BUSCAR DADOS DO MERCADO
# ------------------------------------------------

@st.cache_data(ttl=3600)
def analisar_fiis(lista):

    dados = []

    for fii in lista:

        try:

            ticker = yf.Ticker(f"{fii}.SA")

            hist = ticker.history(period="1d")

            if hist.empty:
                continue

            preco = hist['Close'].iloc[-1]

            dividendos = ticker.dividends.tail(12).sum()

            dy = (dividendos / preco) * 100 if preco > 0 else 0

            preco_teto = dividendos / 0.06 if dividendos > 0 else 0

            desconto = ((preco_teto - preco) / preco_teto) * 100 if preco_teto > 0 else 0

            dados.append({

                "Ticker": fii,
                "Preço": preco,
                "Dividendos_12m": dividendos,
                "DY %": dy,
                "Preço Teto": preco_teto,
                "Desconto %": desconto,
                "Status": "🟢 Oportunidade" if preco < preco_teto else "🔴 Caro"

            })

        except:
            pass

    df = pd.DataFrame(dados)

    df = df.sort_values(by="DY %", ascending=False)

    return df


df_fiis = analisar_fiis(lista_fiis)

# ------------------------------------------------
# MENU
# ------------------------------------------------

menu = st.sidebar.radio(
"Menu",
[
"📊 Scanner de FIIs",
"🏆 Ranking",
"💼 Minha Carteira",
"🔮 Simulador"
]
)

st.sidebar.write(f"Atualizado {datetime.now().strftime('%H:%M')}")

# ------------------------------------------------
# SCANNER
# ------------------------------------------------

if menu == "📊 Scanner de FIIs":

    st.subheader("Scanner de Oportunidades")

    filtro_dy = st.slider("DY mínimo",0.0,15.0,6.0)

    oportunidades = df_fiis[df_fiis["DY %"] > filtro_dy]

    st.dataframe(oportunidades)

    fig = px.scatter(
        oportunidades,
        x="Preço",
        y="DY %",
        color="Status",
        size="Desconto %",
        hover_name="Ticker"
    )

    st.plotly_chart(fig,use_container_width=True)

# ------------------------------------------------
# RANKING
# ------------------------------------------------

elif menu == "🏆 Ranking":

    st.subheader("Top FIIs por Dividend Yield")

    top = df_fiis.sort_values("DY %",ascending=False).head(10)

    st.dataframe(top)

    fig = px.bar(
        top,
        x="Ticker",
        y="DY %",
        color="Status"
    )

    st.plotly_chart(fig,use_container_width=True)

# ------------------------------------------------
# CARTEIRA
# ------------------------------------------------

elif menu == "💼 Minha Carteira":

    st.subheader("Carteira de FIIs")

    carteira = {
    "Ticker":["HGLG11","KNRI11","MXRF11"],
    "Qtd":[10,5,100],
    "PM":[160,155,10]
    }

    df_cart = pd.DataFrame(carteira)

    patrimonio = 0

    for i,row in df_cart.iterrows():

        preco = df_fiis[df_fiis["Ticker"]==row["Ticker"]]["Preço"].values

        if len(preco)>0:

            patrimonio += preco[0]*row["Qtd"]

    st.metric("Patrimônio Atual",f"R$ {patrimonio:,.2f}")

    st.dataframe(df_cart)

# ------------------------------------------------
# SIMULADOR
# ------------------------------------------------

elif menu == "🔮 Simulador":

    st.subheader("Simulador de Independência Financeira")

    capital = st.number_input("Capital Inicial",10000.0)

    aporte = st.number_input("Aporte mensal",1000.0)

    taxa = st.slider("Yield mensal %",0.5,1.5,0.8)/100

    anos = st.slider("Anos",1,30,10)

    meses = anos*12

    saldo = capital

    historico = []

    for m in range(meses):

        renda = saldo*taxa

        saldo += renda + aporte

        historico.append(saldo)

    st.metric("Renda mensal futura",f"R$ {saldo*taxa:,.2f}")

    st.line_chart(historico)
