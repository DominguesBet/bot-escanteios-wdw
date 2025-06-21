import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import requests
from scipy.stats import poisson

st.title("🏟️ Bot de Escanteios – Windrawwin")

st.markdown("""
Cole abaixo o link da página de escanteios no Windrawwin para importar os dados do campeonato automaticamente.
""")

def extrair_windrawwin(link):
    try:
        resp = requests.get(link)
        soup = BeautifulSoup(resp.text, "lxml")
        tabela = soup.find("table", attrs={"id": "table-corners-league"}) or soup.find("table")
        df = pd.read_html(str(tabela))[0]
        df.columns = df.columns.str.strip().str.lower()
        cols = [c for c in df.columns if "avg corner" in c or "corner" in c]
        if not cols:
            st.error("Não identifiquei colunas de escanteios no site.")
            return None
        df = df[["team"] + cols]
        df.rename(columns={"team":"time"}, inplace=True)
        df["time"] = df["time"].str.strip()
        return df
    except Exception as e:
        st.error(f"Falha ao extrair dados: {e}")
        return None

link = st.text_input("🔗 Cole o link do campeonato no Windrawwin:")

if link:
    with st.spinner("Importando dados..."):
        df = extrair_windrawwin(link)

    if df is not None:
        st.subheader("🧾 Dados do Campeonato")
        st.dataframe(df, use_container_width=True)
        times = df["time"].tolist()
        a, b = st.columns(2)
        with a:
            time_casa = st.selectbox("🏠 Time da Casa", times)
        with b:
            time_fora = st.selectbox("🚩 Time Visitante", times)

        if time_casa and time_fora:
            casa = df[df["time"]==time_casa].iloc[0,1:].astype(float).mean()
            fora = df[df["time"]==time_fora].iloc[0,1:].astype(float).mean()
            total = casa + fora
            st.metric("📊 Média de Escanteios Esperados", f"{total:.2f}")

            probs = {i: poisson.pmf(i, total)*100 for i in range(0,16)}
            dfp = pd.DataFrame.from_dict(probs, orient='index', columns=["% probabilidade"])
            dfp.index.name = "Escanteios"
            st.bar_chart(dfp)
            st.dataframe(dfp)

            p95 = sum(poisson.pmf(i, total) for i in range(10,16))*100
            st.success(f"🎯 Chance de MAIS de 9 escanteios: {p95:.2f}%")
