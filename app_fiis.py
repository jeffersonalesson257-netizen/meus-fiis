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

# Estilização CSS para cartões e visual moderno
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    [data-testid="stMetricValue"] { font-size: 28px !important; color: #004b23 !important; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# 2. BANCO DE DADOS DA CARTEIRA
# Altere seus dados aqui conforme necessário
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
            current_price = float(hist['Close'].iloc[-1])
            divs_annual = float(fii.dividends.tail(12).sum()) if not fii.dividends.empty else 0.0
            
            invested = float(row['Quantidade'] * row['Preco_Medio'])
            current_val = float(row['Quantidade'] * current_price)
            profit_pct = ((current_val / invested) - 1) * 100 if invested > 0 else 0
            yoc = (divs_annual / row['Preco_Medio']) * 100 if row['Preco_Medio'] > 0 else 0
            p_teto = divs_annual / 0.06 # Método Bazin
            
            # Número Mágico
            div_mensal_unid = divs_annual / 12
            magic_num = int(current_price // div_mensal_unid) + 1 if div_mensal_unid > 0 else 0

            results.append({
                "Ticker": row['Ticker'],
                "Setor": row['Setor'],
                "Qtd": int(row['Quantidade']),
                "Cotação": current_price,
                "P. Médio": float(row['Preco_Medio']),
                "Rentab %": profit_pct,
                "YoC %": yoc,
                "P. Teto": p_teto,
                "Status": "✅ DESCONTO" if current_price < p_teto else "⚠️ CARO",
                "Total Atual": current_val,
                "Nº Mágico": magic_num,
                "Renda_Anual_Estimada": divs_annual * row['Quantidade']
            })
    return pd.DataFrame(results)

# --- EXECUÇÃO DOS DADOS ---
df = fetch_market_data(pd.DataFrame(meus_investimentos))

# 4. BARRA LATERAL
with st.sidebar:
    st.title("💼 Menu Principal")
    menu = st.radio("Navegação:", ["📊 Dashboard", "🔮 Simulador"])
    st.divider()
    st.write(f"Atualizado: {datetime.now().strftime('%d/%m %H:%M')}")

# 5. ABA: DASHBOARD
if menu == "📊 Dashboard":
    st.title("Estratégia de Renda Passiva")
    
    # Cálculos Seguros (Proteção contra Erros)
    patrimonio_total = float(df['Total Atual'].sum())
    investimento_total = float((df['Qtd'] * df['P. Médio']).sum())
    lucro_total = patrimonio_total - investimento_total
    renda_mensal_est = float(df['Renda_Anual_Estimada'].sum() / 12)

    # Cards de KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Patrimônio", f"R$ {patrimonio_total:,.2f}")
    c2.metric("Lucro Bruto", f"R$ {lucro_total:,.2f}", f"{(lucro_total/investimento_total if investimento_total > 0 else 0)*100:.2f}%")
    c3.metric("Renda Mensal Est.", f"R$ {renda_mensal_est:,.2f}")
    c4.metric("Ativos", len(df))

    st.markdown("---")

    # Gráficos
    g1, g2 = st.columns([1, 1.5])
    with g1:
        st.subheader("Divisão por Setor")
        fig_pie = px.pie(df, values='Total Atual', names='Setor', hole=0.5, color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_pie, use_container_width=True)

    with g2:
        st.subheader("Preço Atual vs Preço Teto")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=df['Ticker'], y=df['Cotação'], name='Atual', marker_color='#2a9d8f'))
        fig_bar.add_trace(go.Bar(x=df['Ticker'], y=df['P. Teto'], name='Teto', marker_color='#e76f51', opacity=0.4))
        fig_bar.update_layout(barmode='overlay', margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tabela Detalhada
    st.subheader("Análise dos Ativos")
    st.dataframe(
        df.drop(columns=['Renda_Anual_Estimada']).style.format({
            "Cotação": "R$ {:.2f}", "P. Médio": "R$ {:.2f}", "Rentab %": "{:.2f}%",
            "YoC %": "{:.2f}%", "P. Teto": "R$ {:.2f}", "Total Atual": "R$ {:.2f}"
        }), 
        use_container_width=True
    )

# 6. ABA: SIMULADOR
elif menu == "🔮 Simulador":
    st.title("Simulador Bola de Neve")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        v_ini = st.number_input("Capital Inicial (R$)", value=float(df['Total Atual'].sum()))
        v_mensal = st.number_input("Aporte Mensal (R$)", value=1000.0)
        v_taxa = st.slider("Yield Mensal (%)", 0.5, 1.5, 0.8) / 100
        v_anos = st.slider("Anos", 1, 30, 10)
    
    meses = v_anos * 12
    historico = []
    saldo = v_ini
    for m in range(1, meses + 1):
        renda = saldo * v_taxa
        saldo += renda + v_mensal
        historico.append({"Mês": m, "Saldo": saldo, "Renda": renda})
    
    with col2:
        st.success(f"Renda Mensal Futura: R$ {saldo * v_taxa:,.2f}")
        st.area_chart(pd.DataFrame(historico).set_index("Mês")["Saldo"])
