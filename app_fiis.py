import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# -----------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------

st.set_page_config(
    page_title="Jefferson Wealth Management",
    layout="wide",
    page_icon="📊"
)

# -----------------------------------
# ESTILO VISUAL PROFISSIONAL
# -----------------------------------

st.markdown("""
<style>

.stApp {
background: linear-gradient(135deg,#0f172a,#1e293b);
color:white;
}

div[data-testid="stMetric"]{
background:linear-gradient(145deg,#1e293b,#0f172a);
border-radius:15px;
padding:20px;
box-shadow:0 10px 25px rgba(0,0,0,0.4);
border:1px solid #334155;
}

[data-testid="stMetricValue"]{
font-size:30px;
font-weight:700;
color:#22c55e;
}

h1,h2,h3{
color:#f1f5f9;
}

</style>
""", unsafe_allow_html=True)

st.title("📊 Jefferson Wealth Management")

# -----------------------------------
# FORMATAR MOEDA BR
# -----------------------------------

def brl(valor):

    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")

# -----------------------------------
# LISTA DE FIIs
# -----------------------------------

lista_fiis = [
"HGLG11","KNRI11","XPML11","BTLG11","VISC11",
"MXRF11","CPTS11","XPLG11","BRCO11","PVBI11",
"HGRE11","GGRC11","RBRR11","RECR11"
]

# -----------------------------------
# BUSCAR DADOS
# -----------------------------------

@st.cache_data(ttl=300)

def buscar_dados(lista):

    dados=[]

    for fii in lista:

        try:

            ticker=yf.Ticker(f"{fii}.SA")

            hist=ticker.history(period="1d")

            if hist.empty:
                continue

            preco=hist["Close"].iloc[-1]

            dividendos=ticker.dividends.tail(12).sum()

            dy=(dividendos/preco)*100 if preco>0 else 0

            preco_teto=dividendos/0.06 if dividendos>0 else 0

            desconto=((preco_teto-preco)/preco_teto)*100 if preco_teto>0 else 0

            dados.append({

                "Ticker":fii,
                "Preço":preco,
                "Dividendos":dividendos,
                "DY":dy,
                "Preço Teto":preco_teto,
                "Desconto":desconto

            })

        except:

            pass

    return pd.DataFrame(dados)

df_fiis=buscar_dados(lista_fiis)

# -----------------------------------
# MENU LATERAL
# -----------------------------------

menu = st.sidebar.selectbox(

"Menu",

[
"Dashboard",
"Scanner de FIIs",
"Minha Carteira",
"Radar FII",
"Simulador"
]

)

st.sidebar.caption(f"Atualizado {datetime.now().strftime('%H:%M:%S')}")

# -----------------------------------
# DASHBOARD
# -----------------------------------

if menu=="Dashboard":

    st.subheader("Visão geral do mercado")

    fig = px.scatter(
        df_fiis,
        x="Preço",
        y="DY",
        size="Desconto",
        hover_name="Ticker",
        color="DY"
    )

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig,use_container_width=True)

# -----------------------------------
# SCANNER
# -----------------------------------

if menu=="Scanner de FIIs":

    st.subheader("Scanner de oportunidades")

    col1,col2,col3=st.columns(3)

    with col1:
        filtro_dy=st.slider("Dividend Yield mínimo",0.0,15.0,6.0)

    with col2:
        filtro_desc=st.slider("Desconto mínimo",-20.0,50.0,0.0)

    with col3:
        preco_max=st.number_input("Preço máximo",0.0,500.0,200.0)

    df_filtrado=df_fiis[
        (df_fiis["DY"]>=filtro_dy) &
        (df_fiis["Desconto"]>=filtro_desc) &
        (df_fiis["Preço"]<=preco_max)
    ]

    df_exibir=df_filtrado.copy()

    df_exibir["Preço"]=df_exibir["Preço"].apply(brl)

    df_exibir["Preço Teto"]=df_exibir["Preço Teto"].apply(brl)

    st.dataframe(df_exibir)

    # EXPORTAR EXCEL

    excel=df_filtrado.to_excel("scanner_fiis.xlsx",index=False)

    st.download_button(

        "📥 Exportar Excel",

        data=open("scanner_fiis.xlsx","rb"),

        file_name="scanner_fiis.xlsx"

    )

# -----------------------------------
# MINHA CARTEIRA
# -----------------------------------

if menu=="Minha Carteira":

    st.subheader("Gestão da carteira")

    if "carteira" not in st.session_state:

        st.session_state.carteira=pd.DataFrame({

            "Ticker":["HGLG11","MXRF11"],
            "Qtd":[10,100],
            "PM":[160,10]

        })

    carteira_edit=st.data_editor(

        st.session_state.carteira,

        num_rows="dynamic"

    )

    st.session_state.carteira=carteira_edit

    patrimonio=0

    renda_anual=0

    dados=[]

    for _,row in carteira_edit.iterrows():

        ticker=row["Ticker"]

        qtd=row["Qtd"]

        pm=row["PM"]

        if ticker in df_fiis["Ticker"].values:

            preco=df_fiis[df_fiis["Ticker"]==ticker]["Preço"].values[0]

            dy=df_fiis[df_fiis["Ticker"]==ticker]["DY"].values[0]

            valor=qtd*preco

            patrimonio+=valor

            renda=qtd*(dy/100)*preco

            renda_anual+=renda

            dados.append({

                "Ticker":ticker,
                "Qtd":qtd,
                "PM":pm,
                "Preço":preco,
                "Valor":valor,
                "DY":dy

            })

    df_cart=pd.DataFrame(dados)

    col1,col2,col3=st.columns(3)

    col1.metric("Patrimônio",brl(patrimonio))

    col2.metric("Renda anual",brl(renda_anual))

    col3.metric("Renda mensal",brl(renda_anual/12))

    df_exibir=df_cart.copy()

    df_exibir["Preço"]=df_exibir["Preço"].apply(brl)

    df_exibir["Valor"]=df_exibir["Valor"].apply(brl)

    st.dataframe(df_exibir)

    # EXPORTAR CARTEIRA

    df_cart.to_excel("minha_carteira.xlsx",index=False)

    st.download_button(

        "📥 Exportar carteira",

        data=open("minha_carteira.xlsx","rb"),

        file_name="minha_carteira.xlsx"

    )

    fig=px.pie(df_cart,names="Ticker",values="Valor")

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig,use_container_width=True)

# -----------------------------------
# RADAR FII
# -----------------------------------

if menu=="Radar FII":

    st.subheader("Análise de risco do FII")

    fii=st.selectbox("Escolher FII",df_fiis["Ticker"])

    dy=st.slider("Dividend Yield",0,10,7)

    pvp=st.slider("P/VP",0,10,6)

    liquidez=st.slider("Liquidez",0,10,8)

    estabilidade=st.slider("Estabilidade Dividendos",0,10,7)

    vacancia=st.slider("Vacância",0,10,6)

    diversificacao=st.slider("Diversificação",0,10,7)

    categorias=["DY","PVP","Liquidez","Estabilidade","Vacância","Diversificação"]

    valores=[dy,pvp,liquidez,estabilidade,vacancia,diversificacao]

    valores.append(valores[0])

    categorias.append(categorias[0])

    fig=go.Figure()

    fig.add_trace(go.Scatterpolar(

        r=valores,

        theta=categorias,

        fill='toself'

    ))

    fig.update_layout(

        template="plotly_dark",

        polar=dict(

            radialaxis=dict(

                visible=True,

                range=[0,10]

            )

        )

    )

    st.plotly_chart(fig)

# -----------------------------------
# SIMULADOR
# -----------------------------------

if menu=="Simulador":

    st.subheader("Simulador de renda passiva")

    capital=st.number_input("Capital inicial",10000.0)

    aporte=st.number_input("Aporte mensal",1000.0)

    taxa=st.slider("Yield mensal %",0.5,1.5,0.8)/100

    anos=st.slider("Anos",1,30,10)

    meses=anos*12

    saldo=capital

    historico=[]

    for i in range(meses):

        renda=saldo*taxa

        saldo+=renda+aporte

        historico.append(saldo)

    st.metric(

        "Renda mensal futura",

        brl(saldo*taxa)

    )

    st.line_chart(historico)
