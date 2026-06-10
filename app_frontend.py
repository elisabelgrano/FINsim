import streamlit as st
import pymongo
import requests
from visualizzatore_grafici import (
    genera_heatmap_performance, genera_bar_prodotti,
    genera_linee_comparative, genera_waterfall_patrimonio, genera_sankey_flussi, genera_andamento_guadagni
)

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

# 1. Barra laterale per la selezione dello scenario
st.sidebar.header("📁 Dati di Simulazione")

# Recuperiamo gli ultimi 15 documenti salvati su MongoDB
ultimi_documenti = list(collection.find({}, {"scenario_id": 1}).sort([("_id", pymongo.DESCENDING)]).limit(15))

if ultimi_documenti:
    # Creiamo le opzioni per il menu a tendina associando il nome all'ID univoco
    opzioni = {f"Scenario: {doc.get('scenario_id', 'Sconosciuto')} (ID: {str(doc['_id'])[-4:]})": doc['_id'] for doc in ultimi_documenti}
    
    scelta = st.sidebar.selectbox("Seleziona quale scenario analizzare:", list(opzioni.keys()))
    
    if st.sidebar.button("🔄 Carica Scenario Selezionato"):
        # Recupera il documento completo dal database usando l'ID
        doc_id = opzioni[scelta]
        scenario_selezionato = collection.find_one({"_id": doc_id})
        
        st.session_state["scenario"] = scenario_selezionato
        st.sidebar.success(f"{scelta.split(' (')[0]} caricato con successo!")
else:
    st.sidebar.warning("Nessun dato trovato nel Database.")
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
                    
                    for i, grafico_obj in enumerate(grafici_richiesti):
                        # estraiamo codice e didascalia in modo sicuro
                        if isinstance(grafico_obj, dict):
                            codice_grafico = grafico_obj.get("codice")
                            didascalia = grafico_obj.get("didascalia", "")
                        else:
                            codice_grafico = str(grafico_obj)
                            didascalia = ""
                            
                        with cols_grafici[i]:
                            if codice_grafico == "HEATMAP_PERFORMANCE":
                                fig = genera_heatmap_performance(metrics)
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                    if didascalia:
                                        didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                                        st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")
                                    
                            elif codice_grafico == "BAR_PRODOTTI":
                                fig = genera_bar_prodotti(metrics)
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                    if didascalia: 
                                        didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                                        st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")
                                
                            elif codice_grafico == "LINEE_COMPARATIVE":
                                fig = genera_linee_comparative(metrics)
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                    if didascalia: 
                                        didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                                        st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")

                            elif codice_grafico == "WATERFALL_PATRIMONIO":
                                fig = genera_waterfall_patrimonio(metrics)
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                    if didascalia:
                                        didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                                        st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")

                            elif codice_grafico == "SANKEY_FLUSSI":
                                fig = genera_sankey_flussi(metrics)
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                    if didascalia: 
                                        didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                                        st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")
                                        
                            elif codice_grafico == "AREA_GUADAGNI":
                                fig = genera_andamento_guadagni(metrics)
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                    if didascalia:
                                        didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                                        st.info(f"💡 **Analisi IA:**\n\n{didascalia_pulita}")
                                        
                    
    
                    st.write("---")
                    st.markdown("### 📝 Valuta l'analisi di Gemma")
                    st.markdown("Sei soddisfatto della risposta e dei grafici proposti?")
                    
                    # 1. Creiamo il sistema di voto (da 1 a 5)
                    voto = st.radio(
                        "Seleziona il tuo livello di soddisfazione:", 
                        options=[1, 2, 3, 4, 5], 
                        format_func=lambda x: "⭐" * x, 
                        horizontal=True,
                        index=4
                    )
                    
                    # 2. Pulsante di invio feedback
                    if st.button("Invia Valutazione", type="primary"):
                        
                        # SOGLIA: Se il voto è 3 o meno, forziamo il ricalcolo
                        if voto <= 3:
                            st.warning("⚠️ Valutazione insufficiente rilevata. Rielaborazione forzata in corso...")
                            
                            # Recuperiamo la domanda originale (assicurati di avere la variabile a disposizione qui)
                            # e aggiungiamo un "prompt iniettato" per forzare l'IA a cambiare risposta e grafici
                            domanda_potenziata = (
                                f"{domanda_utente}\n\n"
                                "CRITICAL SYSTEM NOTE: The user was NOT satisfied with your previous answer. "
                                "You must completely change your analysis, be much more specific, detailed, "
                                "and select DIFFERENT charts to explain the situation better."
                            )
                            
                            with st.spinner("Gemma sta analizzando i dati con maggiore profondità..."):
                                # SOSTITUISCI 'chiama_backend_advisor' con il nome reale della tua funzione API
                                # che usi all'inizio per inviare la domanda a FastAPI
                                nuova_risposta = chiama_backend_advisor(domanda_potenziata) 
                                
                                # Aggiorniamo il session_state con la nuova risposta in modo che Streamlit la stampi
                                st.session_state['risposta_advisor'] = nuova_risposta 
                                
                                # Ricarichiamo l'interfaccia per mostrare i nuovi risultati
                                st.rerun()
                                
                        else:
                            # Se il voto è 4 o 5, ringraziamo e chiudiamo
                            st.success("🎉 Grazie per il feedback! Sono felice che l'analisi sia stata di alto livello.")
                            st.balloons()

            except Exception as e:
                st.error(f"Errore durante la comunicazione con il backend: {e}")
else:
    st.warning("👈 Clicca sul pulsante nella barra laterale per caricare i dati reali da MongoDB.")