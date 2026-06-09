import streamlit as st
import pymongo
import requests
from visualizzatore_grafici import genera_heatmap_performance, genera_bar_prodotti

# Configurazione Pagina
st.set_page_config(page_title="FINsim v2 - AI Financial Advisor", layout="wide")

# Configuro le connessioni
MONGO_URI = "mongodb://elisa:deepleey@10.12.7.53:27017/"
API_URL = "http://127.0.0.1:8000/api/advisor/chat"

@st.cache_resource
def init_mongo():
    client = pymongo.MongoClient(MONGO_URI)
    return client["finsim_analytics"]["simulation_history"]

collection = init_mongo()

st.title("📊 FINsim v2 — Advisor Strategico con Gemma 4")
st.subheader("Analisi scenari finanziari basata su simulazioni reali")

# 1. Barra laterale per recuperare l'ultimo scenario
st.sidebar.header("📁 Dati di Simulazione")
if st.sidebar.button("🔄 Carica Ultimo Scenario da MongoDB"):
    ultimo = collection.find_one({}, sort=[("_id", pymongo.DESCENDING)])
    if ultimo:
        st.session_state["scenario"] = ultimo
        st.sidebar.success(f"Scenario {ultimo.get('scenario_id', 'Sconosciuto')} caricato!")
    else:
        st.sidebar.error("Nessun dato trovato nel Database.")

# Se lo scenario è caricato, procediamo
if "scenario" in st.session_state:
    scenario = st.session_state["scenario"]
    metrics = scenario.get("business_metrics", {})
    
    st.info(f"📂 Stai analizzando lo Scenario ID: **{scenario.get('scenario_id')}**")
    
    # 2. Box di chat con l'IA
    st.write("### 🤖 Chiedi un'analisi strategica a Gemma 4")
    domanda_utente = st.text_input(
        "Inserisci la tua domanda:", 
        value="Guardando i dati reali, qual è stata la mossa vincente per i clienti con patrimonio alto?"
    )
    
    if st.button("🚀 Interroga Advisor"):
        with st.spinner("Gemma 4 sta analizzando i dati e generando i grafici..."):
            try:
                # Prepariamo il payload per FastAPI
                payload = {"metrics_data": metrics, "user_message": domanda_utente}
                risposta = requests.post(API_URL, json=payload, timeout=130)
                risposta.raise_for_status()
                dati_ai = risposta.json()
                
                # Visualizziamo la risposta dell'IA
                st.success("✨ Risposta elaborata!")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.warning(f"**Suggerimento rapido:**\n{dati_ai.get('suggerimento_breve')}")
                with col2:
                    st.write(f"**Analisi Dettagliata:**\n{dati_ai.get('dettaglio_risposta')}")
                
                # 3. Rendering Dinamico dei Grafici Richiesti dall'IA
                grafici_richiesti = dati_ai.get("grafici_consigliati", [])
                
                if grafici_richiesti:
                    st.write("---")
                    st.write("### 📊 Dashboard Grafica (On-Demand)")
                    
                    # Creiamo le colonne a seconda di quanti grafici ha chiesto l'IA
                    cols_grafici = st.columns(len(grafici_richiesti))
                    
                    for i, codice_grafico in enumerate(grafici_richiesti):
                        with cols_grafici[i]:
                            if codice_grafico == "HEATMAP_PERFORMANCE":
                                fig = genera_heatmap_performance(metrics)
                                if fig: st.plotly_chart(fig, use_container_width=True)
                            
                            elif codice_grafico == "BAR_PRODOTTI":
                                fig = genera_bar_prodotti(metrics)
                                if fig: st.plotly_chart(fig, use_container_width=True)
                                
            except Exception as e:
                st.error(f"Errore durante la comunicazione con il backend: {e}")
else:
    st.warning("👈 Clicca sul pulsante nella barra laterale per caricare i dati reali da MongoDB.")