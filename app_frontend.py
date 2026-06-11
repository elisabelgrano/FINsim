import streamlit as st
import pymongo
import requests
from visualizzatore_grafici import (
    genera_heatmap_performance, genera_bar_prodotti,
    genera_linee_comparative, genera_waterfall_patrimonio, genera_sankey_flussi,
    genera_andamento_guadagni, estrai_playbook_strategico,
    genera_donut_asset_allocation, genera_bubble_clientela, genera_win_rate_prodotti
)

# --- Inizializzazione stato di sessione ---
if 'cronologia_risposte' not in st.session_state:
    st.session_state['cronologia_risposte'] = {}

if 'risposta_advisor' not in st.session_state:
    st.session_state['risposta_advisor'] = None

if 'ricalcolo_in_corso' not in st.session_state:
    st.session_state['ricalcolo_in_corso'] = False

if 'ultima_domanda' not in st.session_state:
    st.session_state['ultima_domanda'] = ""

# --- Configurazione Pagina ---
st.set_page_config(page_title="FINsim v2 - AI Financial Advisor", layout="wide")

# --- Connessioni ---
MONGO_URI = "mongodb://elisa:deepleey@10.12.7.53:27017/"
API_URL = "http://127.0.0.1:8000/api/advisor/chat"

@st.cache_resource
def init_mongo():
    client = pymongo.MongoClient(MONGO_URI)
    return client["finsim_analytics"]["simulation_history"]

collection = init_mongo()

st.title("📊 FINsim v2 — Advisor Strategico con Gemma 4")
st.subheader("Analisi scenari finanziari basata su simulazioni reali")

# --- Barra laterale ---
st.sidebar.header("📁 Dati di Simulazione")

with st.sidebar:
    st.write("---")
    st.markdown("### 📚 Archivio Analisi (On-Demand)")

    cronologia = st.session_state.get('cronologia_risposte', {})

    if not cronologia:
        st.info("Nessuna analisi salvata. Fai una domanda per iniziare!")
    else:
        st.caption("Clicca su una domanda precedente per ricaricare i grafici:")

        for vecchia_domanda, json_salvato in cronologia.items():
            titolo_pulsante = vecchia_domanda[:30] + "..." if len(vecchia_domanda) > 30 else vecchia_domanda
            if st.button(f"🔍 {titolo_pulsante}", key=f"hist_{vecchia_domanda}"):
                st.session_state['risposta_advisor'] = json_salvato
                st.rerun()

# Recuperiamo gli ultimi 15 documenti da MongoDB
ultimi_documenti = list(collection.find({}, {"scenario_id": 1}).sort([("_id", pymongo.DESCENDING)]).limit(15))

if ultimi_documenti:
    opzioni = {f"Scenario: {doc.get('scenario_id', 'Sconosciuto')} (ID: {str(doc['_id'])[-4:]})": doc['_id'] for doc in ultimi_documenti}

    scelta = st.sidebar.selectbox("Seleziona quale scenario analizzare:", list(opzioni.keys()))

    if st.sidebar.button("🔄 Carica Scenario Selezionato"):
        doc_id = opzioni[scelta]
        scenario_selezionato = collection.find_one({"_id": doc_id})
        st.session_state["scenario"] = scenario_selezionato
        st.sidebar.success(f"{scelta.split(' (')[0]} caricato con successo!")
else:
    st.sidebar.warning("Nessun dato trovato nel Database.")


# --- Funzione di rendering grafici e feedback ---
def render_risposta(dati_ai, metrics, domanda_utente):
    st.success("✨ Risposta elaborata!")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.warning(f"**Suggerimento rapido:**\n{dati_ai.get('suggerimento_breve')}")
    with col2:
        st.write(f"**Analisi Dettagliata:**\n{dati_ai.get('dettaglio_risposta')}")

    st.write("---")
    st.markdown("### 🚨 KPI di Portafoglio")
    kpi1, kpi2, kpi3 = st.columns(3)
    pct_churn = metrics.get('pct_clienti_sotto_soglia_fiducia', 0.0)
    mismatch = metrics.get('mismatch_rate', 0.0) * 100
    kpi1.metric("Capitale a Rischio Churn", f"{pct_churn:.1f}%", "- Pericolo Fuga" if pct_churn > 10 else "Sicuro", delta_color="inverse")
    kpi2.metric("Win Rate Globale", f"{100 - mismatch:.1f}%", "Efficacia Commerciale")
    kpi3.metric("Compliance Score", f"{100 - mismatch:.1f}/100", "MIFID OK" if mismatch < 20 else "Rischio Legale", delta_color="inverse")

    grafici_richiesti = dati_ai.get("grafici_consigliati", [])

    if grafici_richiesti:
        st.write("---")
        st.write("### 📊 Dashboard Grafica (On-Demand)")

        cols_grafici = st.columns(len(grafici_richiesti))

        for i, grafico_obj in enumerate(grafici_richiesti):
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

                elif codice_grafico == "DONUT_ASSET":
                    fig = genera_donut_asset_allocation(metrics)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                        if didascalia:
                            didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")

                elif codice_grafico == "BUBBLE_CLIENTI":
                    fig = genera_bubble_clientela(st.session_state['scenario'].get('rounds', []))
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                        if didascalia:
                            didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")

                elif codice_grafico == "BAR_WIN_RATE":
                    fig = genera_win_rate_prodotti(metrics)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                        if didascalia:
                            didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")

            if "scenario" in st.session_state and "rounds" in st.session_state["scenario"]:
                st.write("---")
                st.markdown("### 🎯 Playbook Strategico del Promotore")
                st.caption("Seleziona l'identikit del cliente per estrarre la strategia d'azione ottimale emersa dalla simulazione:")
                
                rounds_data = st.session_state["scenario"]["rounds"]
                playbook = estrai_playbook_strategico(rounds_data)
                
                col_r, col_p = st.columns(2)
                with col_r:
                    rischio_sel = st.selectbox(
                        "Propensiona al Rischio",
                        options=[0, 1, 2, 3],
                        format_func=lambda x: f"Livello {x} (0=Basso, 3=Alto)",
                        key="playbook_rischio_widget"
                    )
                with col_p:
                    patrimonio_sel = st.selectbox(
                        "Fascia Patrimoniale",
                        options=[0, 1, 2, 3, 4],
                        format_func=lambda x: f"Fascia{x}",
                        key="playbook_patrimonio_widget"
                    )
                    
                chiave_ricerca = (rischio_sel, patrimonio_sel)
                
                if chiave_ricerca in playbook:
                    strategia = playbook[chiave_ricerca]
                    st.success(f"🏆 **Prodotto Raccomandato:** {strategia['prodotto_top']}")
                    
                    m1, m2 = st.columns(2)
                    segno = "+" if strategia['crescita_attesa'] > 0 else ""
                    m1.metric("Delta Fiducia Medio Atteso", f"{segno}{strategia['crescita_attesa']:.4f} pts")
                    m2.metric("Affidabilità Statistica", f"Validato su {strategia['casi_studio']} decisioni")
                else:
                    st.info("Nessun dato sufficiente per questa combinazione. L'agente adattivo non ha esplorato questo cluster.")

        st.write("---")
        st.markdown("### 📝 Valuta l'analisi di Gemma")
        st.markdown("Sei soddisfatto della risposta e dei grafici proposti?")

        voto = st.radio(
            "Seleziona il tuo livello di soddisfazione:",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: "⭐" * x,
            horizontal=True,
            index=4
        )

        if st.button("Invia Valutazione", type="primary"):
            if voto <= 3:
                st.session_state['ricalcolo_in_corso'] = True
                st.rerun()
            else:
                st.success("🎉 Grazie per il feedback! Sono felice che l'analisi sia stata di alto livello.")
                st.balloons()


# --- Flusso principale ---
if "scenario" in st.session_state:
    scenario = st.session_state["scenario"]
    metrics = scenario.get("business_metrics", {})

    st.info(f"📂 Stai analizzando lo Scenario ID: **{scenario.get('scenario_id')}**")

    # Ricalcolo automatico se l'utente ha dato una valutazione bassa
    if st.session_state.get('ricalcolo_in_corso') and st.session_state.get('ultima_domanda'):
        st.session_state['ricalcolo_in_corso'] = False  # reset flag subito per evitare loop

        domanda_potenziata = (
            f"{st.session_state['ultima_domanda']}\n\n"
            "CRITICAL SYSTEM NOTE: The user was NOT satisfied with your previous answer. "
            "You must completely change your analysis, be much more specific, detailed, "
            "and select DIFFERENT charts to explain the situation better."
        )

        st.warning("⚠️ Valutazione insufficiente rilevata. Rielaborazione automatica in corso...")

        with st.spinner("Gemma sta analizzando i dati con maggiore profondità..."):
            try:
                payload_ricalcolo = {"metrics_data": metrics, "user_message": domanda_potenziata}
                risposta = requests.post(API_URL, json=payload_ricalcolo, timeout=130)
                risposta.raise_for_status()

                nuovo_json = risposta.json()
                st.session_state['risposta_advisor'] = nuovo_json
                st.session_state['cronologia_risposte'][st.session_state['ultima_domanda']] = nuovo_json

            except Exception as e:
                st.error(f"Errore durante il ricalcolo con il backend: {e}")

    # Box di chat con l'IA
    st.write("### 🤖 Chiedi un'analisi strategica all'Advisor")
    domanda_utente = st.text_input(
        "Inserisci la tua domanda:",
        value="Guardando i dati reali, qual è stata la mossa vincente per i clienti con patrimonio alto?"
    )

    if st.button("🚀 Interroga Advisor"):
        with st.spinner("Gemma 4 sta analizzando i dati e generando i grafici..."):
            try:
                st.session_state['ultima_domanda'] = domanda_utente  # salviamo la domanda

                payload = {"metrics_data": metrics, "user_message": domanda_utente}
                risposta = requests.post(API_URL, json=payload, timeout=130)
                risposta.raise_for_status()
                dati_ai = risposta.json()

                st.session_state['risposta_advisor'] = dati_ai
                st.session_state['cronologia_risposte'][domanda_utente] = dati_ai

            except Exception as e:
                st.error(f"Errore durante la comunicazione con il backend: {e}")

    # Rendering della risposta (sia dopo il pulsante che dopo il ricalcolo automatico)
    if st.session_state.get('risposta_advisor'):
        render_risposta(
            st.session_state['risposta_advisor'],
            metrics,
            st.session_state.get('ultima_domanda', domanda_utente)
        )

else:
    st.warning("👈 Clicca sul pulsante nella barra laterale per caricare i dati reali da MongoDB.")