import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO DE UI/UX PREMIUM
st.set_page_config(
    page_title="Jefferson Wealth Management",
    page_icon="💰",
    layout="wide"
)

# Estilização CSS para cartões e fontes
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    [data-testid="stMetricValue"] { font-size: 28px !important; color: #004b23 !important; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    .css-1r6slb0 { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# 2. BANCO DE DADOS DA CARTEIRA (Edite aqui seus ativos)
meus_investimentos = {
    'Ticker': ['HGLG11', 'KNRI11', 'XPML11', 'BTLG11', 'VISC11', 'MXRF11'],
    'Quantidade': [10, 5, 12, 15, 8, 100],
    'Preco_Medio': [160.50, 155.00, 110.00, 98.00, 115.00, 10.15],
    'Setor': ['Logística', 'Híbrido', 'Shopping', 'Logística', 'Shopping', 'Papel']
}

# 3. MOTOR DE PROCESSAMENTO (Engine)
@st.cache_data(ttl=3600)
def fetch_market_data(df_base):
    results = []
    for _, row in df_base.iterrows():
        ticker_name = f"{row['Ticker']}.SA"
        fii = yf.Ticker(ticker_name)
        hist = fii.history(period="1d")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            divs_annual = fii.dividends.tail(12).sum() if not fii.dividends.empty else 0
            
            # Inteligência Financeira
            invested = row['Quantidade'] * row['Preco_Medio']
            current_val = row['Quantidade'] * current_price
            profit_pct = ((current_val / invested) - 1) * 100
            yoc = (divs_annual / row['Preco_Medio']) * 100
            p_teto = divs_annual / 0.06 # Método Bazin
            
            # Número Mágico (Cotas para 1 nova cota grátis por mês)
            div_mensal_unid = divs_annual / 12
            magic_num = int(current_price // div_mensal_unid) + 1 if div_mensal_unid > 0 else 0

            results.append({
                "Ticker": row['Ticker'],
                "Setor": row['Setor'],
                "Qtd": row['Quantidade'],
                "Cotação": current_price,
                "P. Médio": row['Preco_Medio'],
                "Rentab %": profit_pct,
                "YoC %": yoc,
                "P. Teto": p_teto,
                "Status": "✅ DESCONTO" if current_price < p_teto else "⚠️ CARO",
                "Total Atual": current_val,
                "Nº Mágico": magic_num
            })
    return pd.DataFrame(results)

# --- EXECUÇÃO DOS DADOS ---
df = fetch_market_data(pd.DataFrame(meus_investimentos))

# 4. BARRA LATERAL (Navegação)
with st.sidebar:
    st.title("💼 Menu")
    menu = st.radio("Escolha a Visão:", ["📊 Dashboard Principal", "🔮 Simulador Bola de Neve"])
    st.divider()
    st.write(f"Atualizado em: {datetime.now().strftime('%H:%M - %d/%m')}")

# 5. ABA: DASHBOARD PRINCIPAL
if menu == "📊 Dashboard Principal":
    st.title("Estratégia de Renda Passiva")
    
    # KPIs Superiores
    c1, c2, c3, c4 = st.columns(4)
    patrimonio_total = df['Total Atual'].sum()
    investimento_total = (df['Qtd'] * df['P. Médio']).sum()
    lucro_total = patrimonio_total - investimento_total
    renda_estimada = (df['YoC %']/100 * investimento_total) / 12

    c1.metric("Patrimônio", f"R$ {patrimonio_total:,.2f}")
    c2.metric("Lucro Bruto", f"R$ {lucro_total:,.2f}", f"{(lucro_total/investimento_total)*100:.2f}%")
    c3.metric("Renda Mensal Est.", f"R$ {renda_estimada:,.2f}")
    c4.metric("Ativos", len(df))

    st.markdown("---")

    # Gráficos
    g1, g2 = st.columns([1, 1.5])
    with g1:
        st.subheader("Concentração por Setor")
        fig_pie = px.pie(df, values='Total Atual', names='Setor', hole=0.6, color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig_pie, use_container_width=True)

    with g2:
        st.subheader("Cotação Atual vs Preço Teto")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=df['Ticker'], y=df['Cotação'], name='Atual', marker_color='#2a9d8f'))
        fig_bar.add_trace(go.Bar(x=df['Ticker'], y=df['P. Teto'], name='Teto (Bazin)', marker_color='#e76f51', opacity=0.4))
        fig_bar.update_layout(barmode='overlay', margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tabela Interativa
    st.subheader("Análise Detalhada dos Ativos")
    st.dataframe(
        df.sort_values(by="Rentab %", ascending=False).style.format({
            "Cotação": "R$ {:.2f}", "P. Médio": "R$ {:.2f}", "Rentab %": "{:.2f}%",
            "YoC %": "{:.2f}%", "P. Teto": "R$ {:.2f}", "Total Atual": "R$ {:.2f}"
        }), 
        use_container_width=True
    )

# 6. ABA: SIMULADOR
elif menu == "🔮 Simulador Bola de Neve":
    st.title("Simulador de Independência Financeira")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("### Parâmetros")
        v_inicial = st.number_input("Capital Atual (R$)", value=float(patrimonio_total))
        v_mensal = st.number_input("Aporte Mensal (R$)", value=1000.0)
        v_taxa = st.slider("Dividend Yield Mensal (%)", 0.5, 1.5, 0.8) / 100
        v_anos = st.slider("Horizonte (Anos)", 1, 30, 10)
    
    # Lógica de Juros Compostos
    meses = v_anos * 12
    historico = []
    saldo = v_inicial
    for m in range(1, meses + 1):
        rendimento = saldo * v_taxa
        saldo += rendimento + v_mensal
        historico.append({"Mês": m, "Patrimônio": saldo, "Dividendos": rendimento})
    
    df_sim = pd.DataFrame(historico)
    
    with col2:
        st.write("### Projeção de Crescimento")
        st.success(f"Em {v_anos} anos seu rendimento mensal será de **R$ {saldo * v_taxa:,.2f}**")
        fig_sim = px.area(df_sim, x="Mês", y="Patrimônio", color_discrete_sequence=['#2a9d8f'])
        st.plotly_chart(fig_sim, use_container_width=True)
