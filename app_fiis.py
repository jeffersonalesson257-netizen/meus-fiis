import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Plataforma FIIs", layout="wide")

# -------------------------
# Lista grande de FIIs
# -------------------------

fiis_lista = [
"HGLG11","KNRI11","XPML11","BTLG11","VISC11","MXRF11",
"CPTS11","XPLG11","BRCO11","PVBI11","HGRE11","GGRC11",
"RBRR11","RECR11","IRDM11","VGIR11","VILG11","RBRP11",
"JSRE11","HSML11","PATL11","ALZR11","LVBI11","XPCI11"
]

# -------------------------
# Formatação brasileira
# -------------------------

def brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")

# -------------------------
# Buscar dados
# -------------------------

@st.cache_data(ttl=600)
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

            score = (
                dy*0.6 +
                (1/preco)*40
            )

            dados.append({

                "Ticker":fii,
                "Preço":preco,
                "Dividendos":dividendos,
                "DY":dy,
                "Score":score

            })

        except:
            pass

    df = pd.DataFrame(dados)

    return df

df = buscar_dados()

# -------------------------
# Menu
# -------------------------

menu = st.sidebar.selectbox(

"Menu",

[
"Dashboard",
"Heatmap",
"Scanner",
"Ranking",
"Radar",
"Simulador"
]

)

# -------------------------
# Dashboard
# -------------------------

if menu == "Dashboard":

    st.title("📊 Dashboard FIIs")

    col1,col2,col3 = st.columns(3)

    col1.metric("FIIs analisados",len(df))
    col2.metric("DY médio",f"{df['DY'].mean():.2f}%")
    col3.metric("Preço médio",brl(df["Preço"].mean()))

    fig = px.bar(df,x="Ticker",y="DY",color="DY")

    st.plotly_chart(fig,use_container_width=True)

    st.dataframe(df)

# -------------------------
# HEATMAP
# -------------------------

elif menu == "Heatmap":

    st.title("🔥 Mapa de Calor dos FIIs")

    fig = px.density_heatmap(
        df,
        x="Preço",
        y="DY",
        z="Score",
        color_continuous_scale="RdYlGn"
    )

    st.plotly_chart(fig,use_container_width=True)

# -------------------------
# Scanner
# -------------------------

elif menu == "Scanner":

    st.title("🔎 Scanner Profissional")

    dy_min = st.slider("Dividend Yield mínimo",0.0,15.0,7.0)

    preco_max = st.slider("Preço máximo",10.0,200.0,120.0)

    filtro = df[
        (df["DY"] >= dy_min) &
        (df["Preço"] <= preco_max)
    ]

    st.write(f"{len(filtro)} FIIs encontrados")

    st.dataframe(filtro)

    # exportar excel
    buffer = BytesIO()

    filtro.to_excel(buffer,index=False)

    st.download_button(
        "📥 Exportar Excel",
        buffer.getvalue(),
        "scanner_fiis.xlsx"
    )

# -------------------------
# Ranking
# -------------------------

elif menu == "Ranking":

    st.title("🏆 Ranking de FIIs")

    ranking = df.sort_values("Score",ascending=False)

    st.dataframe(ranking)

    fig = px.bar(
        ranking.head(10),
        x="Ticker",
        y="Score",
        color="DY"
    )

    st.plotly_chart(fig,use_container_width=True)

# -------------------------
# Radar
# -------------------------

elif menu == "Radar":

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

# -------------------------
# Simulador
# -------------------------

elif menu == "Simulador":

    st.title("🔮 Simulador de Dividendos")

    capital = st.number_input("Capital inicial",10000)

    aporte = st.number_input("Aporte mensal",1000)

    dy = st.slider("DY anual (%)",5,15,10)

    anos = st.slider("Tempo (anos)",1,30,10)

    meses = anos*12

    taxa = dy/100/12

    saldo = capital

    historico = []

    for i in range(meses):

        renda = saldo*taxa

        saldo += renda + aporte

        historico.append(saldo)

    fig = px.line(y=historico,title="Crescimento do patrimônio")

    st.plotly_chart(fig)

    renda_final = saldo*taxa

    st.metric("Renda mensal estimada",brl(renda_final))
