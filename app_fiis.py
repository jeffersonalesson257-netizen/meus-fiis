import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# -----------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------

st.set_page_config(
    page_title="Jefferson Wealth Management",
    page_icon="📈",
    layout="wide"
)

# -----------------------------
# ESTILO VISUAL
# -----------------------------

st.markdown("""
<style>

.main {
background-color:#f4f7f6;
}

div[data-testid="stMetric"]{
background-color:white;
padding:15px;
border-radius:12px;
box-shadow:0px 3px 6px rgba(0,0,0,0.08);
}

[data-testid="stMetricValue"]{
font-size:28px;
color:#004b23;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# CARTEIRA
# -----------------------------

meus_investimentos = {
'Ticker':['HGLG11','KNRI11','XPML11','BTLG11','VISC11','MXRF11'],
'Quantidade':[10,5,12,15,8,100],
'Preco_Medio':[160.50,155.00,110.00,98.00,115.00,10.15],
'Setor':['Logística','Híbrido','Shopping','Logística','Shopping','Papel']
}

base_df = pd.DataFrame(meus_investimentos)

# -----------------------------
# FUNÇÃO DE BUSCA DE DADOS
# -----------------------------

@st.cache_data(ttl=3600)
def buscar_dados(df):

    resultados = []

    for _, row in df.iterrows():

        ticker = row['Ticker'] + ".SA"

        try:

            fii = yf.Ticker(ticker)

            hist = fii.history(period="1d")

            if hist.empty:
                continue

            preco = float(hist['Close'].iloc[-1])

            dividendos = fii.dividends.tail(12).sum()

            qtd = row['Quantidade']
            pm = row['Preco_Medio']

            investido = qtd * pm
            valor_atual = qtd * preco

            lucro = valor_atual - investido
            rentabilidade = (lucro / investido) * 100

            dy = (dividendos / preco) * 100 if preco > 0 else 0
            yoc = (dividendos / pm) * 100 if pm > 0 else 0

            preco_teto = dividendos / 0.06 if dividendos > 0 else 0

            renda_anual = dividendos * qtd

            resultados.append({

                "Ticker":row['Ticker'],
                "Setor":row['Setor'],
                "Qtd":qtd,
                "Cotação":preco,
                "P.Médio":pm,
                "DY %":dy,
                "YoC %":yoc,
                "Rentab %":rentabilidade,
                "P.Teto":preco_teto,
                "Status":"🟢 Barato" if preco < preco_teto else "🔴 Caro",
                "Total Atual":valor_atual,
                "Renda Anual":renda_anual

            })

        except Exception as e:
            print(e)

    return pd.DataFrame(resultados)

df = buscar_dados(base_df)

# -----------------------------
# SIDEBAR
# -----------------------------

with st.sidebar:

    st.title("💼 Jefferson WM")

    menu = st.radio(
    "Menu",
    ["📊 Dashboard","🔮 Simulador"]
    )

    st.divider()

    st.caption(f"Atualizado: {datetime.now().strftime('%d/%m %H:%M')}")

# -----------------------------
# DASHBOARD
# -----------------------------

if menu == "📊 Dashboard":

    st.title("📊 Dashboard de FIIs")

    patrimonio = df['Total Atual'].sum()
    investido = (df['Qtd'] * df['P.Médio']).sum()
    lucro = patrimonio - investido
    renda_mensal = df['Renda Anual'].sum() / 12

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Patrimônio",f"R$ {patrimonio:,.2f}")
    c2.metric("Lucro",f"R$ {lucro:,.2f}",f"{(lucro/investido)*100:.2f}%")
    c3.metric("Renda Mensal",f"R$ {renda_mensal:,.2f}")
    c4.metric("FIIs",len(df))

    st.divider()

    col1,col2 = st.columns(2)

    with col1:

        st.subheader("Alocação por Setor")

        fig = px.pie(
        df,
        values="Total Atual",
        names="Setor",
        hole=0.5
        )

        st.plotly_chart(fig,use_container_width=True)

    with col2:

        st.subheader("Preço vs Preço Teto")

        fig = go.Figure()

        fig.add_trace(go.Bar(
        x=df['Ticker'],
        y=df['Cotação'],
        name="Preço Atual"
        ))

        fig.add_trace(go.Bar(
        x=df['Ticker'],
        y=df['P.Teto'],
        name="Preço Teto",
        opacity=0.4
        ))

        fig.update_layout(barmode="overlay")

        st.plotly_chart(fig,use_container_width=True)

    st.subheader("Tabela de Análise")

    st.dataframe(
    df.style.format({
    "Cotação":"R$ {:.2f}",
    "P.Médio":"R$ {:.2f}",
    "DY %":"{:.2f}%",
    "YoC %":"{:.2f}%",
    "Rentab %":"{:.2f}%",
    "P.Teto":"R$ {:.2f}",
    "Total Atual":"R$ {:.2f}",
    "Renda Anual":"R$ {:.2f}"
    }),
    use_container_width=True
    )

# -----------------------------
# SIMULADOR
# -----------------------------

elif menu == "🔮 Simulador":

    st.title("Simulador de Renda Passiva")

    col1,col2 = st.columns([1,2])

    with col1:

        capital = st.number_input(
        "Capital Inicial",
        value=float(df['Total Atual'].sum())
        )

        aporte = st.number_input(
        "Aporte Mensal",
        value=1000.0
        )

        taxa = st.slider(
        "Yield Mensal %",
        0.5,
        1.5,
        0.8
        ) / 100

        anos = st.slider(
        "Anos",
        1,
        30,
        10
        )

    meses = anos * 12

    saldo = capital

    historico = []

    for mes in range(1,meses+1):

        renda = saldo * taxa
        saldo += renda + aporte

        historico.append({
        "Mes":mes,
        "Saldo":saldo
        })

    with col2:

        renda_futura = saldo * taxa

        st.success(
        f"Renda mensal futura: R$ {renda_futura:,.2f}"
        )

        graf = pd.DataFrame(historico)

        st.area_chart(
        graf.set_index("Mes")["Saldo"]
        )
