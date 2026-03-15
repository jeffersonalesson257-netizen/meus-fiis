import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Plataforma FIIs", layout="wide")

# ----------------------------
# Lista de FIIs
# ----------------------------

fiis_lista = [
"HGLG11","KNRI11","XPML11","BTLG11","VISC11","MXRF11",
"CPTS11","XPLG11","BRCO11","PVBI11","HGRE11","GGRC11",
"RBRR11","RECR11","IRDM11","VGIR11","VILG11","RBRP11",
"JSRE11","HSML11","PATL11","ALZR11","LVBI11","XPCI11"
]

# ----------------------------
# Formato R$
# ----------------------------

def brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")

# ----------------------------
# Buscar dados mercado
# ----------------------------

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

            score = (dy*0.6 + (1/preco)*40)

            dados.append({

                "Ticker":fii,
                "Preço":preco,
                "Dividendos":dividendos,
                "DY":dy,
                "Score":score

            })

        except:
            pass

    return pd.DataFrame(dados)

df = buscar_dados()

# ----------------------------
# Menu
# ----------------------------

menu = st.sidebar.selectbox(

"Menu",

[
"Dashboard",
"Heatmap",
"Scanner",
"Ranking",
"Minha Carteira",
"Radar",
"Simulador"
]

)

# ----------------------------
# Dashboard
# ----------------------------

if menu == "Dashboard":

    st.title("📊 Dashboard FIIs")

    col1,col2,col3 = st.columns(3)

    col1.metric("FIIs analisados",len(df))
    col2.metric("DY médio",f"{df['DY'].mean():.2f}%")
    col3.metric("Preço médio",brl(df["Preço"].mean()))

    fig = px.bar(df,x="Ticker",y="DY",color="DY")

    st.plotly_chart(fig,use_container_width=True)

    st.dataframe(df)

# ----------------------------
# Heatmap
# ----------------------------

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

# ----------------------------
# Scanner
# ----------------------------

elif menu == "Scanner":

    st.title("🔎 Scanner de FIIs")

    dy_min = st.slider("DY mínimo",0.0,15.0,7.0)

    preco_max = st.slider("Preço máximo",10.0,200.0,120.0)

    filtro = df[
        (df["DY"]>=dy_min) &
        (df["Preço"]<=preco_max)
    ]

    st.write(f"{len(filtro)} FIIs encontrados")

    st.dataframe(filtro)

    buffer = BytesIO()

    filtro.to_excel(buffer,index=False)

    st.download_button(
        "📥 Exportar Excel",
        buffer.getvalue(),
        "scanner_fiis.xlsx"
    )

# ----------------------------
# Ranking
# ----------------------------

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

# ----------------------------
# Minha Carteira
# ----------------------------

elif menu == "Minha Carteira":

    st.title("💼 Minha Carteira")

    if "carteira" not in st.session_state:
        st.session_state.carteira = []

    col1,col2,col3 = st.columns(3)

    ticker = col1.selectbox("FII",fiis_lista)

    quantidade = col2.number_input("Quantidade",1)

    preco_compra = col3.number_input("Preço de compra",0.0)

    if st.button("Adicionar FII"):

        preco_atual = df[df["Ticker"]==ticker]["Preço"].values[0]

        investido = quantidade*preco_compra

        valor_atual = quantidade*preco_atual

        lucro = valor_atual-investido

        dy = df[df["Ticker"]==ticker]["DY"].values[0]

        dividendo = valor_atual*(dy/100)/12

        st.session_state.carteira.append({

            "Ticker":ticker,
            "Quantidade":quantidade,
            "Preço Compra":preco_compra,
            "Preço Atual":preco_atual,
            "Investido":investido,
            "Valor Atual":valor_atual,
            "Lucro":lucro,
            "Dividendo Mensal":dividendo

        })

    if len(st.session_state.carteira)>0:

        carteira_df = pd.DataFrame(st.session_state.carteira)

        total_investido = carteira_df["Investido"].sum()
        total_atual = carteira_df["Valor Atual"].sum()
        lucro_total = carteira_df["Lucro"].sum()
        renda = carteira_df["Dividendo Mensal"].sum()

        c1,c2,c3,c4 = st.columns(4)

        c1.metric("Total Investido",brl(total_investido))
        c2.metric("Valor Atual",brl(total_atual))
        c3.metric("Lucro / Prejuízo",brl(lucro_total))
        c4.metric("Dividendos Mensais",brl(renda))

        st.dataframe(carteira_df)

        fig = px.pie(
            carteira_df,
            names="Ticker",
            values="Valor Atual",
            title="Alocação da Carteira"
        )

        st.plotly_chart(fig,use_container_width=True)

        buffer = BytesIO()

        carteira_df.to_excel(buffer,index=False)

        st.download_button(
            "📥 Exportar Carteira Excel",
            buffer.getvalue(),
            "minha_carteira_fiis.xlsx"
        )

# ----------------------------
# Radar
# ----------------------------

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

# ----------------------------
# Simulador
# ----------------------------

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
