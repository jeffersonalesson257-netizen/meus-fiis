import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(page_title="Jefferson FII Intelligence Pro", layout="wide")

# --- 1. BANCO DE DADOS DA CARTEIRA ---
# Mantenha seus ativos atualizados aqui
meus_investimentos = {
    'Ticker': ['HGLG11', 'KNRI11', 'XPML11', 'BTLG11', 'VISC11', 'MXRF11'],
    'Quantidade': [10, 5, 12, 15, 8, 100],
    'Preco_Medio': [160.50, 155.00, 110.00, 98.00, 115.00, 10.15],
    'Setor': ['Logística', 'Híbrido', 'Shopping', 'Logística', 'Shopping', 'Papel']
}

# --- 2. FUNÇÕES DE INTELIGÊNCIA ---
@st.cache_data(ttl=3600)
def buscar_dados_mercado(df_base):
    dados = []
    for _, row in df_base.iterrows():
        ticker_sa = f"{row['Ticker']}.SA"
        fii = yf.Ticker(ticker_sa)
        
        # Preço e Dividendos
        hist = fii.history(period="1d")
        if not hist.empty:
            preco_atual = hist['Close'].iloc[-1]
            divs = fii.dividends.tail(12).sum() if not fii.dividends.empty else 0
            
            # Cálculos Financeiros
            valor_investido = row['Quantidade'] * row['Preco_Medio']
            valor_atual = row['Quantidade'] * preco_atual
            lucro = valor_atual - valor_investido
            yoc = (divs / row['Preco_Medio']) * 100 # Yield on Cost
            dy_atual = (divs / preco_atual) * 100   # Yield Atual
            
            # Preço Teto Bazin (6%)
            preco_teto = divs / 0.06
            status = "🔥 BARATO" if preco_atual < preco_teto else "⚠️ CARO"

            dados.append({
                "Ticker": row['Ticker'],
                "Setor": row['Setor'],
                "Qtd": row['Quantidade'],
                "Cotação": preco_atual,
                "P. Médio": row['Preco_Medio'],
                "Resultado %": (lucro / valor_investido) * 100,
                "YoC %": yoc,
                "DY Atual %": dy_atual,
                "P. Teto (6%)": preco_teto,
                "Status": status,
                "Patrimônio": valor_atual,
                "Div_Anual_Estimado": divs * row['Quantidade']
            })
    return pd.DataFrame(dados)

# --- 3. INTERFACE PRINCIPAL ---
st.title("🏙️ Jefferson FII Intelligence Pro")
st.markdown("---")

# Menu Lateral (Tabs)
aba_selecionada = st.sidebar.radio("Navegação", ["Minha Carteira", "Simulador Bola de Neve", "Sobre os Ativos"])

df_carteira_raw = pd.DataFrame(meus_investimentos)
df_final = buscar_dados_mercado(df_carteira_raw)

if aba_selecionada == "Minha Carteira":
    # Métricas de Resumo
    t1, t2, t3 = st.columns(3)
    total_patrimonio = df_final['Patrimônio'].sum()
    renda_mensal = df_final['Div_Anual_Estimado'].sum() / 12
    
    t1.metric("Patrimônio Total", f"R$ {total_patrimonio:,.2f}")
    t2.metric("Renda Mensal Est.", f"R$ {renda_mensal:,.2f}")
    t3.metric("Yield Médio da Carteira", f"{(renda_mensal*12/total_patrimonio)*100:.2f}%")

    st.divider()

    # Gráficos
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Diversificação por Setor")
        fig_setor = px.pie(df_final, values='Patrimônio', names='Setor', hole=0.5)
        st.plotly_chart(fig_setor, use_container_width=True)
    
    with col_g2:
        st.subheader("🎯 Preço Atual vs Preço Teto")
        fig_teto = go.Figure(data=[
            go.Bar(name='Cotação Atual', x=df_final['Ticker'], y=df_final['Cotação'], marker_color='#1f77b4'),
            go.Bar(name='Preço Teto', x=df_final['Ticker'], y=df_final['P. Teto (6%)'], marker_color='#2ca02c')
        ])
        st.plotly_chart(fig_teto, use_container_width=True)

    # Tabela Detalhada
    st.subheader("📋 Detalhamento Estratégico")
    st.dataframe(df_final.style.format({
        "Cotação": "R$ {:.2f}", "P. Médio": "R$ {:.2f}", "Resultado %": "{:.2f}%",
        "YoC %": "{:.2f}%", "DY Atual %": "{:.2f}%", "P. Teto (6%)": "R$ {:.2f}", "Patrimônio": "R$ {:.2f}"
    }), use_container_width=True)

elif aba_selecionada == "Simulador Bola de Neve":
    st.subheader("🔮 Simulador de Reinvestimento (Bola de Neve)")
    
    c1, c2, c3 = st.columns(3)
    aporte_ini = c1.number_input("Início (R$)", value=float(total_patrimonio))
    aporte_mes = c2.number_input("Aporte Mensal (R$)", value=1000.0)
    taxa_mes = c3.slider("DY Mensal Esperado (%)", 0.5, 1.5, 0.8) / 100
    anos = st.slider("Tempo (Anos)", 1, 30, 10)

    # Lógica da Simulação
    dados_sim = []
    saldo = aporte_ini
    for mes in range(1, (anos * 12) + 1):
        dividendos = saldo * taxa_mes
        saldo += dividendos + aporte_mes
        dados_sim.append({"Mês": mes, "Patrimônio": saldo, "Renda": dividendos})
    
    df_sim = pd.DataFrame(dados_sim)
    
    st.success(f"Em {anos} anos, sua renda mensal será de **R$ {saldo * taxa_mes:,.2f}**")
    st.line_chart(df_sim.set_index('Mês')['Patrimônio'])

elif aba_selecionada == "Sobre os Ativos":
    st.subheader("📚 Por que esses FIIs?")
    st.write("""
    - **Logística (HGLG11, BTLG11):** Foco em renda resiliente e contratos atípicos.
    - **Shopping (XPML11, VISC11):** Proteção contra inflação e ganho de capital.
    - **Papel (MXRF11):** Dividendos altos no curto/médio prazo.
    """)
