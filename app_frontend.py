import streamlit as st
import pymongo
import requests
from visualizzatore_grafici import (
    genera_heatmap_performance, genera_bar_prodotti,
    genera_linee_comparative, genera_waterfall_patrimonio, genera_sankey_flussi,
    genera_andamento_guadagni, genera_semaforo_adeguatezza, genera_accettazioni_per_scenario,
    genera_trend_compliance, genera_interesse_composto
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
    
if 'grafico_educativo' not in st.session_state:
    st.session_state['grafico_educativo'] = None

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
                
    st.write("---")
    st.markdown("### 📚 Per il Cliente")
    
    grafico_educativo = st.selectbox(
        "Seleziona grafico da mostrare:",
        options=[
            "-- Seleziona --",
            "Interesse Composto",
        ],
        key="grafico_educativo_sel"
    )
    
    if grafico_educativo != "-- Seleziona --":
        st.session_state['grafico_educativo'] = grafico_educativo
    else:
        st.session_state['grafico_educativo'] = None

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
                        st.plotly_chart(fig, width="stretch", key=f"chart_{codice_grafico}_{i}")
                        if didascalia:
                            didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")

                elif codice_grafico == "BAR_PRODOTTI":
                    fig = genera_bar_prodotti(metrics)
                    if fig:
                        st.plotly_chart(fig, width="stretch", key=f"chart_{codice_grafico}_{i}")
                        if didascalia:
                            didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")

                elif codice_grafico == "LINEE_COMPARATIVE":
                    fig = genera_linee_comparative(metrics)
                    if fig:
                        st.plotly_chart(fig, width="stretch", key=f"chart_{codice_grafico}_{i}")
                        if didascalia:
                            didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")

                elif codice_grafico == "WATERFALL_PATRIMONIO":
                    fig = genera_waterfall_patrimonio(metrics)
                    if fig:
                        st.plotly_chart(fig, width="stretch", key=f"chart_{codice_grafico}_{i}")
                        if didascalia:
                            didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")

                elif codice_grafico == "SANKEY_FLUSSI":
                    fig = genera_sankey_flussi(metrics)
                    if fig:
                        st.plotly_chart(fig, width="stretch", key=f"chart_{codice_grafico}_{i}")
                        if didascalia:
                            didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")

                elif codice_grafico == "AREA_GUADAGNI":
                    fig = genera_andamento_guadagni(metrics)
                    if fig:
                        st.plotly_chart(fig, width="stretch", key=f"chart_{codice_grafico}_{i}")
                        if didascalia:
                            didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi IA:**\n\n{didascalia_pulita}")
                            
                elif codice_grafico == "SEMAFORO_ADEGUATEZZA":
                    fig= genera_semaforo_adeguatezza(scenario.get('summary', {}))
                    if fig:
                        st.plotly_chart(fig, width='stretch', key=f"chart_{codice_grafico}_{i}")
                        if didascalia:
                            didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")
                            
                elif codice_grafico == "ACCETTAZIONI_SCENARI":
                    tutti_docs = list(collection.find({}, {
                        'scenario_id': 1,
                        'summary.overall_acceptance_rate': 1,
                        'summary.overall_mismatch_rate': 1,
                        'summary.total_decisions': 1
                    }))
                    dati_scenari = [{
                        'scenario_id': d['scenario_id'],
                        'overall_acceptance_rate': d['summary']['overall_acceptance_rate'],
                        'overall_mismatch_rate': d['summary']['overall_mismatch_rate'],
                        'total_decisions': d['summary']['total_decisions']
                    } for d in tutti_docs]
                    dati_scenari.sort(key=lambda x: x['scenario_id'])
                    fig= genera_accettazioni_per_scenario(dati_scenari)
                    if fig:
                        st.plotly_chart(fig, width='stretch', key=f"chart_{codice_grafico}_{i}")
                        if didascalia:
                            didascalia_pulita =  didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")
                
                elif codice_grafico == "TREND_COMPLIANCE":
                    rounds_correnti = st.session_state["scenario"].get('rounds', [])
                    scenario_id_corrente = st.session_state["scenario"].get('scenario_id', '')
                    fig = genera_trend_compliance(rounds_correnti, scenario_id_corrente)
                    if fig:
                        st.plotly_chart(fig, width='stretch', key=f"chart_{codice_grafico}_{i}")
                        if didascalia:
                            didascalia_pulita = didascalia.replace("\\n", "\n").replace("\n", "\n\n")
                            st.info(f"💡 **Analisi:** \n\n{didascalia_pulita}")
                                          
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
    st.write(scenario.get("rounds", [])[0])

    # --- KPI ROW ---
    try:
        summary = scenario.get("summary", {})
        overall_compliance = summary.get("overall_compliance_rate", 0)
        overall_acceptance = summary.get("overall_acceptance_rate", 0)
        overall_mismatch = summary.get("overall_mismatch_rate", 0)
        total_decisions = summary.get("total_decisions", 0)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Compliance Direttiva", f"{overall_compliance * 100:.1f}%")
        with col2:
            st.metric("Acceptance Rate", f"{overall_acceptance * 100:.1f}%")
        with col3:
            st.metric("Mismatch Rate", f"{overall_mismatch * 100:.1f}%")
        with col4:
            st.metric("Decisioni Totali", int(total_decisions))
    except Exception as e:
        st.warning(f"Dati KPI non disponibili: {e}")

    # --- SEZIONE 1: Prima dell'appuntamento ---
    try:
        st.markdown("### 🎯 Prima dell'appuntamento")

        col1, col2, col3 = st.columns([1, 1, 1])

        # Column 1: Compliance per promotore (ultimo round)
        with col1:
            st.markdown("#### Compliance per promotore (ultimo round)")
            rounds = scenario.get("rounds", [])
            if rounds:
                last_round = rounds[-1]
                compliance_per_promotore = last_round.get("compliance_per_promotore", {})
                if compliance_per_promotore:
                    for promotore_id, compliance_value in compliance_per_promotore.items():
                        st.metric(f"Promotore {promotore_id}", f"{compliance_value * 100:.1f}%")
                else:
                    st.info("Nessun dato di compliance per promotore")
            else:
                st.info("Nessun round disponibile")

        # Column 2: Prodotto dominante per round
        with col2:
            st.markdown("#### Prodotto dominante per round")
            rounds = scenario.get("rounds", [])
            if rounds:
                df_prodotti = []
                for round_data in rounds:
                    df_prodotti.append({
                        "Round": round_data.get("round", "N/A"),
                        "Prodotto": round_data.get("prodotto_dominante", "N/A")
                    })
                if df_prodotti:
                    import pandas as pd
                    df = pd.DataFrame(df_prodotti)
                    st.dataframe(df, width='stretch', hide_index=True)
                else:
                    st.info("Nessun dato disponibile")
            else:
                st.info("Nessun round disponibile")

        # Column 3: Clienti a rischio
        with col3:
            st.markdown("#### Clienti a rischio")
            rounds = scenario.get("rounds", [])
            if rounds:
                import pandas as pd
                # Collect all decisions from all rounds grouped by cluster
                cluster_data = {}
                for round_data in rounds:
                    decisions = round_data.get("decisions", [])
                    for decision in decisions:
                        cluster = decision.get("cluster", "Unknown")
                        profilo = decision.get("profilo_rischio_prevalente", "N/A")
                        adeguatezza = decision.get("adeguatezza_score", 0)
                        accettato = decision.get("accettato", False)

                        if cluster not in cluster_data:
                            cluster_data[cluster] = {
                                "profilo": profilo,
                                "adeguatezza_scores": [],
                                "accettati": []
                            }
                        cluster_data[cluster]["adeguatezza_scores"].append(adeguatezza)
                        cluster_data[cluster]["accettati"].append(1 if accettato else 0)

                # Calculate metrics per cluster
                df_rischio = []
                for cluster, data in cluster_data.items():
                    mean_adeguatezza = sum(data["adeguatezza_scores"]) / len(data["adeguatezza_scores"]) if data["adeguatezza_scores"] else 0
                    accettato_pct = (sum(data["accettati"]) / len(data["accettati"]) * 100) if data["accettati"] else 0
                    df_rischio.append({
                        "Cluster": cluster,
                        "Profilo": data["profilo"],
                        "Adeguatezza Media": f"{mean_adeguatezza * 100:.0f}%",
                        "Accettato %": f"{accettato_pct:.1f}%"
                    })

                # Sort by adeguatezza and take top 5 at risk (lowest scores)
                df_rischio.sort(key=lambda x: float(x["Adeguatezza Media"].replace("%", "")))
                df_rischio = df_rischio[:5]

                if df_rischio:
                    df = pd.DataFrame(df_rischio)
                    st.dataframe(df, width='stretch', hide_index=True)
                else:
                    st.info("Nessun dato disponibile")
            else:
                st.info("Nessun round disponibile")
    except Exception as e:
        st.warning(f"Dati non disponibili: {e}")
        
    st.markdown("---")
    try:
        fig = genera_semaforo_adeguatezza(scenario.get('summary', {}))
        if fig:
            st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.warning(f"Semaforo non disponibile: {e}")

    # --- SEZIONE 2: Cosa funziona con chi ---
    try:
        st.markdown("### 📊 Cosa funziona con chi")

        matrice = scenario.get("summary", {}).get("matrice_strategica", [])
        if matrice:
            import pandas as pd
            df_matrice = pd.DataFrame(matrice)

            # Rename columns to match the requested format
            if "profilo" in df_matrice.columns:
                df_matrice = df_matrice.rename(columns={
                    "profilo": "Profilo",
                    "prodotto": "Prodotto",
                    "num_decisioni": "N. Decisioni",
                    "adeguatezza_media": "Adeguatezza Media",
                    "acceptance_rate": "Acceptance Rate"
                })

            # Sort by Adeguatezza Media descending
            if "Adeguatezza Media" in df_matrice.columns:
                df_matrice = df_matrice.sort_values("Adeguatezza Media", ascending=False)

            # Apply color styling
            def color_adeguatezza(val):
                try:
                    numeric_val = float(val) if isinstance(val, str) else val
                    if numeric_val >= 0.8:
                        return "background-color: green; color: white"
                    elif numeric_val < 0.5:
                        return "background-color: red; color: white"
                    else:
                        return ""
                except:
                    return ""

            # Format columns: percentages (0 decimals) and integers
            format_dict = {}
            if "Adeguatezza Media" in df_matrice.columns:
                format_dict["Adeguatezza Media"] = "{:.0%}"
            if "Acceptance Rate" in df_matrice.columns:
                format_dict["Acceptance Rate"] = "{:.0%}"
            if "N. Decisioni" in df_matrice.columns:
                format_dict["N. Decisioni"] = "{:.0f}"

            styled_df = df_matrice.style \
                .format(format_dict) \
                .map(color_adeguatezza, subset=["Adeguatezza Media"])
            st.dataframe(styled_df, width='stretch', hide_index=True)
        else:
            st.info("Nessun dato disponibile")
    except Exception as e:
        st.warning(f"Dati non disponibili: {e}")

    # --- SEZIONE 3: Analisi scenari ---
    st.markdown("---")
    st.markdown("### 📈 Analisi scenari")

    try:
        col_sx, col_dx = st.columns([1, 1])

        with col_sx:
            tutti_docs = list(collection.find({}, {
                'scenario_id': 1,
                'summary.overall_acceptance_rate': 1,
                'summary.overall_mismatch_rate': 1,
                'summary.total_decisions': 1
            }))
            dati_scenari = [{
                'scenario_id': d['scenario_id'],
                'overall_acceptance_rate': d['summary']['overall_acceptance_rate'],
                'overall_mismatch_rate': d['summary']['overall_mismatch_rate'],
                'total_decisions': d['summary']['total_decisions']
            } for d in tutti_docs]
            dati_scenari.sort(key=lambda x: x['scenario_id'])
            fig = genera_accettazioni_per_scenario(dati_scenari)
            if fig:
                st.plotly_chart(fig, width='stretch')

        with col_dx:
            rounds_correnti = scenario.get('rounds', [])
            fig = genera_trend_compliance(
                rounds_correnti,
                scenario.get('scenario_id', '')
            )
            if fig:
                st.plotly_chart(fig, width='stretch')

    except Exception as e:
        st.warning(f"Dati analisi scenari non disponibili: {e}")

    # --- SEPARATOR ---
    st.markdown("---")
    
    # --- SEZIONE EDUCATIVA ---
    if st.session_state.get('grafico_educativo'):
        st.markdown("### 📚 Strumenti per il cliente")
        if st.session_state['grafico_educativo'] == "Interesse Composto":
            fig_edu = genera_interesse_composto()
            if fig_edu:
                st.plotly_chart(fig_edu, width='stretch')
        st.markdown("---")

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