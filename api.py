from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pymongo import MongoClient
from collections import defaultdict
import json
import requests
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from datetime import datetime
from io import BytesIO
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import tempfile
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

app = FastAPI(
    title="FINsim Unified API",
    description="Unified API serving dashboard data and Virtual Advisor LLM",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# CONNESSIONE A MONGODB
# =====================================================================
client = MongoClient("mongodb://elisa:deepleey@10.12.7.53:27017/")
db = client["finsim_analytics"]
collection = db["simulation_history"]

# =====================================================================
# MAPPATURA SCENARI: Frontend UI → Database Code
# =====================================================================
# FINSIM-MOD: Traduce i nomi degli scenari inviati dal frontend ai codici del database
MAPPA_SCENARI = {
    "Base": "S0",
    "Espansione": "S1",
    "Rialzo tassi": "S2",
    "Stress": "S3",
    "Recessione": "S4"
}

def get_scenario_code(scenario_ui: str) -> str:
    """
    Converte il nome dello scenario dal frontend al codice database.
    Esempio: "Base" → "S0_200", "Espansione" → "S1_200"
    """
    codice_base = MAPPA_SCENARI.get(scenario_ui, scenario_ui)
    if codice_base.startswith("S") and any(codice_base.endswith(s) for s in ["_200", "_fix8", "_fix9"]):
        return codice_base
    return f"{codice_base}_200"

# =====================================================================
# PYDANTIC MODELS FOR ADVISOR
# =====================================================================

class AdvisorRequest(BaseModel):
    """Request body for advisor endpoint"""
    metrics_data: Dict[str, Any] = Field(
        ...,
        description="Dictionary of calculated metrics from database"
    )
    user_message: Optional[str] = Field(
        default="",
        description="Promoter's question or empty for initial tactical summary"
    )


class GraficoConsigliato(BaseModel):
    codice: str = Field(..., description="Chart code from allowed list")
    didascalia: str = Field(..., description="Explanatory comment to display under the chart")


class AdvisorResponse(BaseModel):
    """Structured response from advisor"""
    suggerimento_breve: str = Field(...)
    dettaglio_risposta: str = Field(...)
    grafici_consigliati: List[GraficoConsigliato] = Field(default_factory=list)


# =====================================================================
# ADVISOR SYSTEM PROMPT
# =====================================================================

ADVISOR_SYSTEM_PROMPT = """Sei un consulente finanziario senior che supporta i promotori bancari italiani.
Il tuo ruolo è analizzare i dati della simulazione e fornire raccomandazioni strategiche chiare e operative.
Parla sempre in italiano formale da consulenza finanziaria, come farebbe un direttore commerciale di banca.

## REGOLE DI LINGUAGGIO — OBBLIGATORIE
Non usare MAI questi termini tecnici o abbreviazioni:
- "MiFID", "CONSOB" → scrivi "normativa di adeguatezza" o "requisiti normativi"
- "S0", "S1", "S2", "S3", "S4" → scrivi "Scenario Base", "Scenario Espansione", "Scenario Rialzo Tassi", "Scenario Stress", "Scenario Recessione"
- "ADAPT" → scrivi "Consulenza Adattiva"
- "FISSO" → scrivi "Strategia Standard"
- "alert", "churn" → scrivi "segnalazione di anomalia" o "abbandono della clientela"
- "KPI" → scrivi "indicatore di performance"
- "AUM" → scrivi "patrimonio gestito"
- "cluster" → scrivi "segmento di clientela" o "gruppo di clienti"
- "benchmark" → scrivi "strategia di riferimento"
- "compliance" → scrivi "conformità normativa"
- "ROI" → scrivi "rendimento sull'investimento"
- "dataset", "array", "endpoint", "algoritmo", "LLM", "AI", "machine learning" → non usare mai
- "Asse X", "Asse Y" → non usare mai per grafici che non hanno assi cartesiani

Esempi di riformulazione corretta:
- SBAGLIATO: "1237 alert MiFID" → CORRETTO: "1.237 segnalazioni di non conformità normativa"
- SBAGLIATO: "churn risk elevato" → CORRETTO: "elevato rischio di abbandono della clientela"
- SBAGLIATO: "scenario S0" → CORRETTO: "Scenario Base"
- SBAGLIATO: "cluster ad alto rischio" → CORRETTO: "segmento di clientela con elevata propensione al rischio"
- SBAGLIATO: "AUM iniziale" → CORRETTO: "patrimonio gestito iniziale"

## FRAMEWORK DI ANALISI
1. Valuta lo stato attuale: trend delle metriche, gap di performance, posizionamento di mercato
2. Identifica i rischi: concentrazioni, segmenti sottoperformanti, anomalie
3. Raccomanda azioni: istruzioni tattiche specifiche e operative
4. Suggerisci visualizzazioni: scegli i grafici più adatti dall'elenco consentito

## REGOLE DI RISPOSTA
- Suggerimento breve: 1-2 frasi massimo, diretto e operativo
- Dettaglio risposta: 2-3 paragrafi di ragionamento approfondito, senza descrivere grafici
- Grafici consigliati: scegli SOLO da questi codici: HEATMAP_PERFORMANCE, BAR_PRODOTTI, LINEE_COMPARATIVE, WATERFALL_PATRIMONIO, SANKEY_FLUSSI, AREA_GUADAGNI, SEMAFORO_ADEGUATEZZA, ACCETTAZIONI_SCENARI, TREND_COMPLIANCE

## REGOLA CRITICA — SEPARAZIONE DEI CONTENUTI
- Nel campo 'dettaglio_risposta': scrivi SOLO analisi strategica, MAI descrizioni di grafici
- Nel campo 'grafici_consigliati': inserisci i grafici con la loro 'didascalia' analitica
- Se menzioni un grafico nella strategia, DEVI aggiungerlo a 'grafici_consigliati'

## ISTRUZIONI PER LE DIDASCALIE
Ogni didascalia deve essere analitica e specifica, strutturata in 3 parti:
1. COME LEGGERLO: spiega i componenti visivi usando linguaggio accessibile
2. ESEMPIO CONCRETO: evidenzia un dato specifico visibile nel grafico
3. COLLEGAMENTO STRATEGICO: collega il grafico alla raccomandazione operativa

Dizionario terminologia per le didascalie:
- HEATMAP_PERFORMANCE: usa "asse orizzontale (patrimonio del cliente)" e "asse verticale (profilo di rischio)". La scala cromatica indica il differenziale percentuale di conversione tra 
le due strategie: il colore verde indica che la Consulenza Adattiva converte meglio in quel segmento di clientela, il colore rosso indica che la Strategia Standard è più efficace.
I valori numerici mostrano il differenziale percentuale. NON dire che i colori rappresentano i due promotori separatamente.
- BAR_PRODOTTI: usa "asse orizzontale (categorie di prodotto)" e "asse verticale (livello di soddisfazione)".
- LINEE_COMPARATIVE: usa "asse orizzontale (sequenza delle 200 proposte)" e "asse verticale (raccolta cumulata in euro)".
- WATERFALL_PATRIMONIO: NON usare asse X/Y. Usa "mattoncini di variazione" e "fattori di composizione". Spiega il percorso dal patrimonio iniziale a quello finale.
- SANKEY_FLUSSI: NON usare asse X/Y. Usa "nodi di partenza (segmenti di rischio)", "nodi di arrivo (stato finale)" e "flussi colorati (volume di migrazione clienti)".
- AREA_GUADAGNI: usa "asse orizzontale (sequenza temporale delle proposte)" e "asse verticale (ricavi generati in euro)".
- SEMAFORO_ADEGUATEZZA: usa "barre orizzontali per categoria di prodotto" e "colore semaforo (verde=adeguato, arancio=margine, rosso=inadeguato)".
- TREND_COMPLIANCE: usa "asse orizzontale (sequenza delle proposte)" e "asse verticale (percentuale di conformità normativa)".
- ACCETTAZIONI_SCENARI: usa "barre raggruppate per strategia" e "altezza della barra (numero di proposte accettate)".

## SELEZIONE AUTONOMA DEI GRAFICI
Scegli i grafici in base alla domanda dell'utente:
1. Domande su patrimonio, raccolta finale → WATERFALL_PATRIMONIO
2. Domande su abbandoni, perdita clienti → SANKEY_FLUSSI
3. Domande su evoluzione nel tempo → LINEE_COMPARATIVE
4. Domande su performance per segmento → HEATMAP_PERFORMANCE
5. Domande su soddisfazione prodotti → BAR_PRODOTTI
6. Domande su ricavi, commissioni → AREA_GUADAGNI
7. Domande su adeguatezza, prodotti sbagliati → SEMAFORO_ADEGUATEZZA
8. Domande su confronto scenari → ACCETTAZIONI_SCENARI
9. Domande su conformità nel tempo → TREND_COMPLIANCE

Non ripetere gli stessi grafici ogni volta. Adatta la selezione alla domanda specifica.

## FORMATO RISPOSTA — OBBLIGATORIO
Rispondi SOLO con un oggetto JSON valido con questa struttura:
{
  "suggerimento_breve": "Raccomandazione operativa in 1-2 frasi.",
  "dettaglio_risposta": "Analisi approfondita in 2-3 paragrafi. Nessuna descrizione di grafici qui.",
  "grafici_consigliati": [
    {
      "codice": "CODICE_GRAFICO",
      "didascalia": "1. Come leggerlo... 2. Esempio concreto... 3. Collegamento strategico..."
    }
  ]
}
"""

# =====================================================================
# OLLAMA INTEGRATION FOR ADVISOR
# =====================================================================

class OllamaAdvisor:
    """Handles communication with Ollama for advisory generation"""

    OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
    OLLAMA_TIMEOUT = 120  # seconds
    MODEL_NAME = "qwen2.5:3b"

    @staticmethod
    def _format_metrics_context(metrics_data: Dict[str, Any]) -> str:
        """Format metrics data into a readable context string"""
        context_lines = ["## Metrics Analysis Context:"]

        for key, value in metrics_data.items():
            if isinstance(value, (dict, list)):
                context_lines.append(f"- {key}: {json.dumps(value, ensure_ascii=False)[:200]}...")
            else:
                context_lines.append(f"- {key}: {value}")

        return "\n".join(context_lines)

    @staticmethod
    def _validate_response_json(response_text: str) -> Dict[str, Any]:
        """
        Extract, clean, and validate JSON response from Ollama.
        Guarantees that required fields are always present with correct types to prevent Pydantic ValidationErrors.
        """
        # 0. Rimuovi blocchi markdown che incapsulano il JSON (```json ... ```)
        response_text = response_text.replace("```json", "").replace("```", "").strip()

        # 1. Pulizia: estraiamo solo quello che risiede tra le parentesi graffe più esterne
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx + 1]
        else:
            json_str = response_text

        # 2. Tentativo di decodifica JSON
        try:
            parsed_json = json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "suggerimento_breve": "Analisi strategica completata.",
                "dettaglio_risposta": response_text,
                "grafici_consigliati": []
            }

        if not isinstance(parsed_json, dict):
            parsed_json = {}

        # 3. Messa in sicurezza e casting dei tipi per prevenire crash Pydantic
        if "suggerimento_breve" not in parsed_json or not isinstance(parsed_json["suggerimento_breve"], str):
            val = parsed_json.get("suggerimento_breve", "Consulenza strategica elaborata con successo.")
            parsed_json["suggerimento_breve"] = json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else str(val)

        if "dettaglio_risposta" not in parsed_json or not isinstance(parsed_json["dettaglio_risposta"], str):
            val = parsed_json.get("dettaglio_risposta", "Dettagli disponibili nell'analisi del modello.")
            parsed_json["dettaglio_risposta"] = json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else str(val)

        if "grafici_consigliati" not in parsed_json or not isinstance(parsed_json["grafici_consigliati"], list):
            parsed_json["grafici_consigliati"] = []
        else:
            grafici_puliti = []
            for g in parsed_json["grafici_consigliati"]:
                if isinstance(g, dict) and "codice" in g:
                    grafici_puliti.append({
                        "codice": str(g["codice"]),
                        "didascalia": str(g.get("didascalia", "Nessun commento fornito dall'IA."))
                    })
                elif isinstance(g, str):
                    grafici_puliti.append({"codice": g, "didascalia": "Analisi visiva generata."})
            parsed_json["grafici_consigliati"] = grafici_puliti

        return parsed_json

    @classmethod
    def generate_advice(
        cls,
        metrics_data: Dict[str, Any],
        user_message: Optional[str] = None
    ) -> AdvisorResponse:
        """
        Generate tactical advice using Ollama with structured JSON output.
        """
        metrics_context = cls._format_metrics_context(metrics_data)

        if user_message and user_message.strip():
            user_prompt = f"""Analyze these metrics and answer the promoter's question:

{metrics_context}

Promoter's Question: {user_message}

Provide your response as a JSON object."""
        else:
            user_prompt = f"""Generate an initial tactical summary for this round based on metrics:

{metrics_context}

Provide your response as a JSON object with tactical guidance and recommended charts."""

        payload = {
            "model": cls.MODEL_NAME,
            "prompt": user_prompt,
            "system": ADVISOR_SYSTEM_PROMPT,
            "stream": False,
            "format": "json"
        }

        try:
            response = requests.post(
                cls.OLLAMA_GENERATE_URL,
                json=payload,
                timeout=cls.OLLAMA_TIMEOUT
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="LLM request timed out")
        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="LLM service unavailable")
        except requests.exceptions.RequestException:
            raise HTTPException(status_code=500, detail="LLM request failed")

        response_data = response.json()
        response_text = response_data.get("response", "").strip()

        if not response_text:
            raise HTTPException(status_code=500, detail="Empty response from LLM")

        # Validazione e normalizzazione del dizionario
        parsed_json = cls._validate_response_json(response_text)

        # Creazione sicura dell'oggetto Pydantic
        try:
            return AdvisorResponse(**parsed_json)
        except Exception:
            return AdvisorResponse(
                suggerimento_breve="Analisi elaborata.",
                dettaglio_risposta=parsed_json.get("dettaglio_risposta", response_text),
                grafici_consigliati=[]
            )


# =====================================================================
# API ENDPOINTS
# =====================================================================

@app.get("/api/dati-banca")
def get_dati_banca(scenario_id: str = "S0"):
    """
    Endpoint che legge l'ultimo round da MongoDB, aggrega i dati dei prodotti
    e calcola i volumi, cluster e adeguatezza reale.
    """
    # Mappa scenario_id dal frontend (Base, Espansione, etc.) al database (S0_200, S1_200, etc.)
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})

    if not doc or "rounds" not in doc or len(doc["rounds"]) == 0:
        return {"prodotti": []}

    # prendiamo l'ultimo round eseguito
    ultimo_round = sorted(doc["rounds"], key=lambda x: x.get('round', 0))[-1]

    prodotti_aggregati = defaultdict(lambda: {
        'adeguatezza_totale': 0.0,
        'decisioni': 0,
        'accettate': 0,
        'cluster': 'N/A',
        'volume': 0.0
    })

    TICKET_MEDIO_MLN = 0.1

    for promo in ultimo_round.get("promoters_data", []):
        for strat in promo.get("strategies", []):

            # normalizz. nome prodotto per l'interfaccia
            prod = strat.get("prodotto_suggerito", "Altro").replace('_', ' ')
            n_clienti = strat.get("clients_in_cluster", 0)
            adeguatezza_score = strat.get("adeguatezza_score", 0.5)
            ha_accettato = strat.get("accettato", False)

            # aggreghiamo dati per prodotto
            prodotti_aggregati[prod]['adeguatezza_totale'] += adeguatezza_score * 1
            prodotti_aggregati[prod]['decisioni'] += 1
            if ha_accettato:
                prodotti_aggregati[prod]['accettate'] += 1
                prodotti_aggregati[prod]['volume'] += n_clienti * TICKET_MEDIO_MLN

            # assegniamo nome cluster (default se non presente)
            if prodotti_aggregati[prod]['cluster'] == 'N/A':
                prodotti_aggregati[prod]['cluster'] = strat.get("cluster_name", "Cluster Generico")

    # risposta per il frontend Vue
    risposta_api = []
    for prod, vals in prodotti_aggregati.items():
        if vals['decisioni'] > 0:
            adeguaatezza_media = vals['adeguatezza_totale'] / vals['decisioni']

            if adeguaatezza_media >= 0.8:
                status = 'green'
            elif adeguaatezza_media >= 0.5:
                status = 'amber'
            else:
                status = 'red'

            risposta_api.append({
                'name': prod,
                'cluster': vals['cluster'],
                'volume': round(vals['volume'], 1),
                'adequacy': round(adeguaatezza_media * 100),
                'status': status
            })

    risposta_api.sort(key=lambda x:x['adequacy'], reverse=True)

    return {"prodotti": risposta_api}
# =====================================================================
# ENDPOINT: TREND BANCA CON DATI VERI DA MONGODB
# =====================================================================
@app.get("/api/trend-banca")
def get_trend_banca(scenario_id: str = "S0"):
    """
    Legge i round da MongoDB e calcola la raccolta netta cumulata
    (Vero vs Falso su 'accettato' moltiplicato per i clienti).
    """
    # Mappa scenario_id al documento corretto da 200 round
    if not scenario_id.endswith("_200"):
        db_scenario_id = f"{scenario_id}_200"
    else:
        db_scenario_id = scenario_id

    # 1. Cerchiamo il documento della simulazione desiderata
    doc = collection.find_one({"scenario_id": db_scenario_id})
    
    # Dati di fallback se il DB è vuoto o lo scenario non esiste
    if not doc or "rounds" not in doc:
        return {
            "labels": [f"R{i}" for i in range(1, 201)],
            "adattivo": [0]*200,
            "fisso": [0]*200
        }

    storico_ia = []
    storico_fisso = []
    rounds_labels = []
    
    # Ipotesi: ogni cliente investe 100.000€ (0.1 Milioni) se accetta la proposta
    TICKET_MEDIO_MLN = 0.1 

    # Variabili per la somma cumulativa nel tempo
    raccolta_cumulata_ia = 0.0
    raccolta_cumulata_fisso = 0.0

    # 2. Iteriamo sui round estratti da Mongo
    for r in doc["rounds"]:
        round_num = r.get("round", 0)
        rounds_labels.append(f"R{round_num}")
        
        raccolta_round_ia = 0.0
        raccolta_round_fisso = 0.0
        
        # 3. Analizziamo le decisioni dei promotori in questo round
        for promo in r.get("promoters_data", []):
            pid = promo.get("promotore_id", "")
            
            for strat in promo.get("strategies", []):
                # Se il cliente ha accettato, calcoliamo il volume
                if strat.get("accettato") == True:
                    clienti_convertiti = strat.get("clients_in_cluster", 0)
                    volume_generato = clienti_convertiti * TICKET_MEDIO_MLN
                    
                    if "ADAPT" in pid:
                        raccolta_round_ia += volume_generato
                    elif "FISSO" in pid:
                        raccolta_round_fisso += volume_generato
                        
        # 4. Aggiungiamo la raccolta del round al totale storico
        raccolta_cumulata_ia += raccolta_round_ia
        raccolta_cumulata_fisso += raccolta_round_fisso
        
        # Salviamo i dati formattati per il grafico (arrotondati a 2 decimali)
        storico_ia.append(round(raccolta_cumulata_ia, 2))
        storico_fisso.append(round(raccolta_cumulata_fisso, 2))
        
    return {
        "labels": rounds_labels,
        "adattivo": storico_ia,
        "fisso": storico_fisso
    }
    
@app.get("/api/dati-promotore")
def get_dati_promotore(scenario_id: str = "S0"):
    """
    Dati per il Promotore: Strategia LLM, approccio, revenue, tag di contesto,
    spaccato delle conversioni per profilo di rischio, product breakdown,
    alerts (churn e mifid), e next best actions.
    """
    # Mappa scenario_id dal frontend (Base, Espansione, etc.) al database (S0_200, S1_200, etc.)
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})
    if not doc or "rounds" not in doc or len(doc["rounds"]) == 0:
        return {
            "status": "no_data",
            "adapt": {"strategia_consigliata": "", "approccio_comunicativo": "", "commissioni_cumulate": 0, "tasso_conversione_pct": 0, "fiducia_media": 0, "proposte_totali": 0, "tags": []},
            "fisso": {"commissioni_cumulate": 0, "tasso_conversione_pct": 0, "fiducia_media": 0, "proposte_totali": 0},
            "risk_profile_breakdown": [],
            "product_breakdown": [],
            "alerts": {"churn_risk_count": 0, "mifid_alerts_count": 0},
            "next_best_actions": []
        }

    rounds = sorted(doc["rounds"], key=lambda x: x.get('round', 0))
    ultimo_round = rounds[-1]

    # --- FEATURE 3: ESTRAZIONE DATI ULTIMO ROUND + GENERAZIONE TAG DI CONTESTO ---
    strat_consigliata = "Nessuna strategia registrata."
    approccio = "Nessun approccio registrato."
    ultimo_prodotto = "N/A"
    ultimo_profilo = "N/A"

    for promo in ultimo_round.get("promoters_data", []):
        if "ADAPT" in promo.get("promotore_id", ""):
            strats = promo.get("strategies", [])
            if strats:
                strat_consigliata = strats[0].get("llm_strategy", "")
                approccio = strats[0].get("approccio_comunicativo", "")
                ultimo_prodotto = strats[0].get("prodotto_suggerito", "Altro").replace('_', ' ')
                ultimo_profilo = strats[0].get("profilo_rischio_prevalente", "Balanced")

    # Creazione automatica dei Tag di contesto basati sulle risposte dell'LLM
    tags = [f"🎯 Target: {ultimo_profilo}", f"📦 Prodotto: {ultimo_prodotto}"]
    if "stabile" in strat_consigliata.lower() or "mitigare" in strat_consigliata.lower() or "ansietà" in strat_consigliata.lower():
        tags.append("⚠️ Sentiment: Ansioso")
        tags.append("💧 Focus: Liquidità/Protezione")
    else:
        tags.append("🚀 Sentiment: Ottimista")
        tags.append("📈 Focus: Performance")

    # --- FEATURE 1: CALCOLO CUMULATO + SPACCATO PER PROFILO DI RISCHIO ---
    # Struttura temporanea: { "Balanced": {"adapt_acc": 0, "adapt_tot": 0, "fisso_acc": 0, "fisso_tot": 0} }
    breakdown_dict = defaultdict(lambda: {"adapt_acc": 0, "adapt_tot": 0, "fisso_acc": 0, "fisso_tot": 0})

    # Product breakdown: { "Bond Corporate": {"adapt_acc": 0, "adapt_tot": 0, "fisso_acc": 0, "fisso_tot": 0} }
    product_dict = defaultdict(lambda: {"adapt_acc": 0, "adapt_tot": 0, "fisso_acc": 0, "fisso_tot": 0})

    adapt_comm, adapt_tot, adapt_acc, adapt_fid_sum = 0, 0, 0, 0
    fisso_comm, fisso_tot, fisso_acc, fisso_fid_sum = 0, 0, 0, 0

    churn_risk_count = 0
    mifid_alerts_count = 0

    TICKET_MEDIO = 100000
    COMMISSIONE = 0.01

    for r in rounds:
        for promo in r.get("promoters_data", []):
            pid = promo.get("promotore_id", "")
            is_adapt = "ADAPT" in pid
            is_fisso = "FISSO" in pid

            for s in promo.get("strategies", []):
                prof = s.get("profilo_rischio_prevalente", "N/A")
                if prof == "N/A": continue

                acc = s.get("accettato", False)
                clients = s.get("clients_in_cluster", 0)
                fid_post = s.get("fiducia_media_post", 0)
                adeguatezza = s.get("adeguatezza_score", 0)
                prodotto = s.get("prodotto_suggerito", "Altro").replace('_', ' ')
                delta_fid = s.get("delta_fiducia_medio", 0)

                if is_adapt:
                    adapt_tot += 1
                    adapt_fid_sum += fid_post
                    breakdown_dict[prof]["adapt_tot"] += 1
                    product_dict[prodotto]["adapt_tot"] += 1

                    if acc:
                        adapt_acc += 1
                        adapt_comm += (clients * TICKET_MEDIO) * COMMISSIONE
                        breakdown_dict[prof]["adapt_acc"] += 1
                        product_dict[prodotto]["adapt_acc"] += 1

                    # Alert churn: fiducia < 0.45 (45%) o delta < -0.10
                    if fid_post < 0.45 or delta_fid < -0.10:
                        churn_risk_count += 1

                    # Alert mifid: adeguatezza < 0.40
                    if adeguatezza < 0.40:
                        mifid_alerts_count += 1

                elif is_fisso:
                    fisso_tot += 1
                    fisso_fid_sum += fid_post
                    breakdown_dict[prof]["fisso_tot"] += 1
                    product_dict[prodotto]["fisso_tot"] += 1

                    if acc:
                        fisso_acc += 1
                        fisso_comm += (clients * TICKET_MEDIO) * COMMISSIONE
                        breakdown_dict[prof]["fisso_acc"] += 1
                        product_dict[prodotto]["fisso_acc"] += 1

                    # Alert churn: fiducia < 0.45 o delta < -0.10
                    if fid_post < 0.45 or delta_fid < -0.10:
                        churn_risk_count += 1

                    # Alert mifid: adeguatezza < 0.40
                    if adeguatezza < 0.40:
                        mifid_alerts_count += 1

    # Formattiamo lo spaccato per renderlo digeribile dalla tabella Vue
    risk_profile_breakdown = []
    for prof, vals in breakdown_dict.items():
        risk_profile_breakdown.append({
            "profilo": prof,
            "adapt_pct": round((vals["adapt_acc"] / vals["adapt_tot"] * 100)) if vals["adapt_tot"] > 0 else 0,
            "fisso_pct": round((vals["fisso_acc"] / vals["fisso_tot"] * 100)) if vals["fisso_tot"] > 0 else 0
        })

    # Product breakdown
    product_breakdown = []
    for prod, vals in product_dict.items():
        product_breakdown.append({
            "prodotto": prod,
            "adapt_pct": round((vals["adapt_acc"] / vals["adapt_tot"] * 100)) if vals["adapt_tot"] > 0 else 0,
            "fisso_pct": round((vals["fisso_acc"] / vals["fisso_tot"] * 100)) if vals["fisso_tot"] > 0 else 0
        })

    # Next best actions condizionali
    next_best_actions = []
    adapt_fiducia_media = round((adapt_fid_sum / adapt_tot * 100)) if adapt_tot > 0 else 0

    if adapt_fiducia_media < 50:
        next_best_actions.append("⚠️ Fiducia media critica: rallentare vendite e recuperare relazione cliente")
    if mifid_alerts_count > 0:
        next_best_actions.append(f"🚨 Allerta Conformità Normativa: {mifid_alerts_count} anomalie di adeguatezza riscontrate")
    if churn_risk_count > 5:
        next_best_actions.append("📉 Rischio Abbandono Critico: rivedere strategia comunicativa")
    if adapt_acc > fisso_acc:
        next_best_actions.append("✅ Consulenza IA Dinamica outperforma Strategia Standard: mantenere approccio attuale")
    else:
        next_best_actions.append("⚙️ Strategia Standard competitive: aumentare personalizzazione")

    if not next_best_actions:
        next_best_actions.append("✓ Situazione stabile, proseguire con strategia corrente")

    return {
        "status": "ok",
        "adapt": {
            "strategia_consigliata": strat_consigliata,
            "approccio_comunicativo": approccio,
            "commissioni_cumulate": round(adapt_comm),
            "tasso_conversione_pct": round((adapt_acc / adapt_tot * 100) if adapt_tot > 0 else 0),
            "fiducia_media": adapt_fiducia_media,
            "proposte_totali": adapt_tot,
            "tags": tags
        },
        "fisso": {
            "commissioni_cumulate": round(fisso_comm),
            "tasso_conversione_pct": round((fisso_acc / fisso_tot * 100) if fisso_tot > 0 else 0),
            "fiducia_media": round((fisso_fid_sum / fisso_tot * 100) if fisso_tot > 0 else 0),
            "proposte_totali": fisso_tot
        },
        "risk_profile_breakdown": risk_profile_breakdown,
        "product_breakdown": product_breakdown,
        "alerts": {
            "churn_risk_count": churn_risk_count,
            "mifid_alerts_count": mifid_alerts_count
        },
        "next_best_actions": next_best_actions
    }

@app.get("/api/dati-promotore-grafici")
def get_dati_promotore_grafici(scenario_id: str = "S0"):
    """
    Dati per i grafici della vista Promotore:
    - Compliance/Adeguatezza media per round (ADAPT vs FISSO)
    - Proposte Accettate per round (stacked bar)
    """
    # Mappa scenario_id dal frontend (Base, Espansione, etc.) al database (S0_200, S1_200, etc.)
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})

    if not doc or "rounds" not in doc or len(doc["rounds"]) == 0:
        return {
            "labels": [f"R{i}" for i in range(1, 201)],
            "compliance_adapt": [0] * 200,
            "compliance_fisso": [0] * 200,
            "accettate_adapt": [0] * 200,
            "accettate_fisso": [0] * 200
        }

    compliance_adapt = []
    compliance_fisso = []
    accettate_adapt = []
    accettate_fisso = []
    labels = []

    for r in sorted(doc.get("rounds", []), key=lambda x: x.get('round', 0)):
        round_num = r.get("round", 0)
        labels.append(f"R{round_num}")

        # Metriche per questo round
        adapt_adeguatezza_cumulata = 0
        adapt_conteggio = 0
        adapt_accettate = 0

        fisso_adeguatezza_cumulata = 0
        fisso_conteggio = 0
        fisso_accettate = 0

        for promo in r.get("promoters_data", []):
            promotore_id = promo.get("promotore_id", "")
            strategies = promo.get("strategies", [])

            for strat in strategies:
                adeguatezza = strat.get("adeguatezza_score", 0)
                ha_accettato = strat.get("accettato", False)

                if "ADAPT" in promotore_id:
                    adapt_adeguatezza_cumulata += adeguatezza
                    adapt_conteggio += 1
                    if ha_accettato:
                        adapt_accettate += 1

                elif "FISSO" in promotore_id:
                    fisso_adeguatezza_cumulata += adeguatezza
                    fisso_conteggio += 1
                    if ha_accettato:
                        fisso_accettate += 1

        # Media di adeguatezza per il round
        adapt_compliance = (adapt_adeguatezza_cumulata / adapt_conteggio * 100) if adapt_conteggio > 0 else 0
        fisso_compliance = (fisso_adeguatezza_cumulata / fisso_conteggio * 100) if fisso_conteggio > 0 else 0

        compliance_adapt.append(round(adapt_compliance, 1))
        compliance_fisso.append(round(fisso_compliance, 1))
        accettate_adapt.append(adapt_accettate)
        accettate_fisso.append(fisso_accettate)

    return {
        "labels": labels,
        "compliance_adapt": compliance_adapt,
        "compliance_fisso": compliance_fisso,
        "accettate_adapt": accettate_adapt,
        "accettate_fisso": accettate_fisso
    }

@app.get("/api/dati-cliente")
def get_dati_cliente(scenario_id: str = "S0"):
    """
    Dati per il Cliente: Trasparenza, Fiducia e Discostamento (Adeguatezza).
    """
    # Mappa scenario_id dal frontend (Base, Espansione, etc.) al database (S0_200, S1_200, etc.)
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})
    if not doc or "rounds" not in doc or len(doc["rounds"]) == 0:
        return {"fiducia_media": 0, "scostamento_profilo": 0}

    ultimo_round = sorted(doc["rounds"], key=lambda x: x.get('round', 0))[-1]
    
    fiducia_tot = 0
    adeguatezza_tot = 0
    conteggio = 0

    # Calcoliamo le medie di come i clienti si sentono trattati
    for promo in ultimo_round.get("promoters_data", []):
        for strat in promo.get("strategies", []):
            fiducia_tot += strat.get("fiducia_media_post", 0)
            # L'adeguatezza_score (0.0 - 1.0) indica quanto il prodotto rispetta il profilo
            adeguatezza_tot += strat.get("adeguatezza_score", 0)
            conteggio += 1

    if conteggio > 0:
        fiducia_media = fiducia_tot / conteggio
        adeguatezza_media = adeguatezza_tot / conteggio
        
        # Se l'adeguatezza è 0.8, c'è un discostamento del 20% da quello che il cliente voleva
        scostamento = (1.0 - adeguatezza_media) * 100 
    else:
        fiducia_media, scostamento = 0, 0

    return {
        "fiducia_attuale": round(fiducia_media * 100),       # Es. 74%
        "scostamento_profilo": round(scostamento),           # Es. 20%
        "trasparenza_status": "green" if scostamento <= 25 else "red"
    }


# =====================================================================
# ADVISOR LLM ENDPOINT
# =====================================================================

@app.post(
    "/api/advisor/chat",
    response_model=AdvisorResponse,
    summary="Get tactical advice from Virtual Advisor",
    tags=["advisor"]
)
async def chat_with_advisor(request: AdvisorRequest) -> AdvisorResponse:
    """Generate tactical advice based on financial metrics."""
    response = OllamaAdvisor.generate_advice(
        metrics_data=request.metrics_data,
        user_message=request.user_message
    )
    return response

def _genera_immagini_grafici(metrics: Dict[str, Any], scenario_id: str) -> Dict[str, str]:
    """
    Genera immagini PNG dei grafici principali per inclusione in PDF/PPTX.
    Legge i dati reali da MongoDB per scenario.
    """
    from visualizzatore_grafici import (
        genera_heatmap_performance,
        genera_waterfall_patrimonio,
        genera_linee_comparative,
        genera_andamento_guadagni
    )
    import tempfile

    immagini = {}

    # Arricchisci metrics con dati reali da MongoDB
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})

    if doc and "rounds" in doc:
        TICKET_MEDIO_MLN = 0.1
        TICKET_MEDIO = 100000
        COMMISSIONE = 0.01

        storico_ia, storico_fisso = [], []
        guadagni_ia, guadagni_fisso = [], []
        raccolta_cumulata_ia, raccolta_cumulata_fisso = 0.0, 0.0

        for r in sorted(doc["rounds"], key=lambda x: x.get("round", 0)):
            raccolta_round_ia, raccolta_round_fisso = 0.0, 0.0
            guadagni_round_ia, guadagni_round_fisso = 0.0, 0.0

            for promo in r.get("promoters_data", []):
                pid = promo.get("promotore_id", "")
                for s in promo.get("strategies", []):
                    if s.get("accettato"):
                        clienti = s.get("clients_in_cluster", 0)
                        if "ADAPT" in pid:
                            raccolta_round_ia += clienti * TICKET_MEDIO_MLN
                            guadagni_round_ia += clienti * TICKET_MEDIO * COMMISSIONE
                        elif "FISSO" in pid:
                            raccolta_round_fisso += clienti * TICKET_MEDIO_MLN
                            guadagni_round_fisso += clienti * TICKET_MEDIO * COMMISSIONE

            raccolta_cumulata_ia += raccolta_round_ia
            raccolta_cumulata_fisso += raccolta_round_fisso
            storico_ia.append(round(raccolta_cumulata_ia, 2))
            storico_fisso.append(round(raccolta_cumulata_fisso, 2))
            guadagni_ia.append(guadagni_round_ia)
            guadagni_fisso.append(guadagni_round_fisso)

        metrics["storico_raccolta_adattivo"] = storico_ia
        metrics["storico_raccolta_fisso"] = storico_fisso
        metrics["guadagni_adapt_per_round"] = guadagni_ia
        metrics["guadagni_fisso_per_round"] = guadagni_fisso

    try:
        fig = genera_heatmap_performance(metrics)
        path = tempfile.mktemp(suffix="_heatmap.png")
        fig.write_image(path, width=800, height=500)
        immagini["heatmap"] = path
    except Exception as e:
        print(f"[IMG] Errore heatmap: {e}")

    try:
        fig = genera_waterfall_patrimonio(metrics)
        path = tempfile.mktemp(suffix="_waterfall.png")
        fig.write_image(path, width=800, height=500)
        immagini["waterfall"] = path
    except Exception as e:
        print(f"[IMG] Errore waterfall: {e}")

    try:
        fig = genera_linee_comparative(metrics)
        path = tempfile.mktemp(suffix="_linee.png")
        fig.write_image(path, width=800, height=400)
        immagini["linee"] = path
    except Exception as e:
        print(f"[IMG] Errore linee: {e}")

    try:
        fig = genera_andamento_guadagni(metrics)
        path = tempfile.mktemp(suffix="_guadagni.png")
        fig.write_image(path, width=800, height=400)
        immagini["guadagni"] = path
    except Exception as e:
        print(f"[IMG] Errore guadagni: {e}")

    return immagini

def _generate_executive_analysis(metrics: Dict[str, Any]) -> str:
    """Genera un'analisi esecutiva completa tramite LLM per report e presentazioni."""
    # Estrai metriche con valori di fallback
    comm_adapt = float(metrics.get('commissioni_cumulate_adapt') or 0)
    comm_fisso = float(metrics.get('commissioni_cumulate_fisso') or 0)
    conv_adapt = float(metrics.get('tasso_conversione_adapt_pct') or 0)
    conv_fisso = float(metrics.get('tasso_conversione_fisso_pct') or 0)
    fid_adapt = float(metrics.get('fiducia_media_adapt') or 0)
    fid_fisso = float(metrics.get('fiducia_media_fisso') or 0)
    prop_adapt = int(metrics.get('proposte_totali_adapt') or 0)
    prop_fisso = int(metrics.get('proposte_totali_fisso') or 0)
    churn = int(metrics.get('churn_risk_count') or 0)
    mifid = int(metrics.get('mifid_alerts_count') or 0)

    prompt = f"""Sei un esperto analista finanziario. Genera un'analisi esecutiva DETTAGLIATA di 500-600 parole per un comitato di direzione basandoti su questi dati reali di 200 round di simulazione:

SCENARIO: {metrics.get('scenario_corrente', 'N/A')}

KPI PRINCIPALI (aggregati su 200 round):
- Commissioni Cumulate ADAPT (IA): € {comm_adapt:,.0f}
- Commissioni Cumulate FISSO (Benchmark): € {comm_fisso:,.0f}
- Differenziale: € {comm_adapt - comm_fisso:,.0f} ({((comm_adapt - comm_fisso) / (comm_fisso or 1) * 100):.1f}%)

- Tasso Conversione ADAPT: {conv_adapt:.1f}%
- Tasso Conversione FISSO: {conv_fisso:.1f}%
- Delta: {conv_adapt - conv_fisso:.1f} punti percentuali

- Fiducia Media ADAPT: {fid_adapt:.1f}%
- Fiducia Media FISSO: {fid_fisso:.1f}%

- Proposte Totali ADAPT: {prop_adapt}
- Proposte Totali FISSO: {prop_fisso}

METRICHE DI RISCHIO:
- Clienti a Rischio Churn: {churn}
- Alert MIFID/CONSOB: {mifid}

REQUISITI:
1. Apri con un executive summary di 2-3 frasi sullo scenario
2. Analizza le performance relative tra ADAPT e FISSO
3. Interpreta i fattori macroeconomici impliciti
4. Commenta il livello di rischio e conformità
5. Suggerisci 3-4 implicazioni strategiche
6. Concludi con raccomandazioni per il board

Rispondi ESCLUSIVAMENTE in italiano, formato testo puro, senza markdown, senza bullet points."""

    try:
        payload = {
            "model": OllamaAdvisor.MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(
            OllamaAdvisor.OLLAMA_GENERATE_URL,
            json=payload,
            timeout=120
        )
        if response.ok:
            data = response.json()
            analysis = data.get("response", "").strip()
            return analysis[:2000] if analysis else "Analisi non disponibile"
    except Exception as e:
        print(f"[ANALYSIS] Errore nella generazione dell'analisi LLM: {str(e)}")
    return "Analisi non disponibile"


def _map_scenario_code_to_name(scenario_code: str) -> str:
    """Mappa codice scenario a nome completo per presentazioni."""
    scenario_map = {
        "S0": "Scenario Base",
        "S1": "Scenario Espansione",
        "S2": "Scenario Rialzo Tassi",
        "S3": "Scenario Stress",
        "S4": "Scenario Recessione"
    }
    return scenario_map.get(scenario_code, scenario_code)

def _generate_views_summary(metrics: Dict[str, Any], scenario_id: str) -> Dict[str, str]:
    """Genera un riepilogo sintetico delle tre viste operative principali."""
    comm_adapt = float(metrics.get('commissioni_cumulate_adapt') or 0)
    comm_fisso = float(metrics.get('commissioni_cumulate_fisso') or 0)
    conv_adapt = float(metrics.get('tasso_conversione_adapt_pct') or 0)
    conv_fisso = float(metrics.get('tasso_conversione_fisso_pct') or 0)
    fid_adapt = float(metrics.get('fiducia_media_adapt') or 0)
    fid_fisso = float(metrics.get('fiducia_media_fisso') or 0)

    riepilogo_banca = f"La raccolta netta complessiva ha generato € {comm_adapt + comm_fisso:,.0f} di commissioni nel periodo analizzato. La Consulenza Adattiva ha contribuito per € {comm_adapt:,.0f}, superando la Strategia Standard di € {comm_adapt - comm_fisso:,.0f}."

    riepilogo_promotore = f"Il tasso di accettazione delle proposte è del {conv_adapt:.1f}% per la Consulenza Adattiva contro il {conv_fisso:.1f}% della Strategia Standard, con un differenziale di {conv_adapt - conv_fisso:.1f} punti percentuali a favore dell'approccio personalizzato."

    sentiment_cliente = "una maggiore soddisfazione percepita" if fid_adapt > fid_fisso else "un'area di attenzione"
    riepilogo_cliente = f"Il livello di fiducia media dei clienti gestiti con la Consulenza Adattiva è del {fid_adapt:.1f}%, rispetto al {fid_fisso:.1f}% della Strategia Standard. Questo indica {sentiment_cliente} nei segmenti seguiti dall'approccio personalizzato."

    return {
        "banca": riepilogo_banca,
        "promotore": riepilogo_promotore,
        "cliente": riepilogo_cliente
    }

@app.post("/api/advisor/export-pptx", tags=["advisor"])
async def export_advisor_pptx(request: AdvisorRequest) -> FileResponse:
    """Generate PowerPoint presentation with 7 slides (compact structure)."""
    metrics = request.metrics_data or {}
    user_message = request.user_message or "Analisi Automatica"

    # Estrai metriche principali
    comm_adapt = float(metrics.get('commissioni_cumulate_adapt') or 0)
    comm_fisso = float(metrics.get('commissioni_cumulate_fisso') or 0)
    conv_adapt = float(metrics.get('tasso_conversione_adapt_pct') or 0)
    conv_fisso = float(metrics.get('tasso_conversione_fisso_pct') or 0)
    fid_adapt = float(metrics.get('fiducia_media_adapt') or 0)
    fid_fisso = float(metrics.get('fiducia_media_fisso') or 0)
    prop_adapt = int(metrics.get('proposte_totali_adapt') or 0)
    prop_fisso = int(metrics.get('proposte_totali_fisso') or 0)
    churn_count = metrics.get('churn_risk_count', 0) or 0
    mifid_count = metrics.get('mifid_alerts_count', 0) or 0

    # Genera analisi esecutiva tramite LLM
    llm_analysis = _generate_executive_analysis(metrics)

    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Colori tema Dark Luxury
    COLOR_ADAPT = RGBColor(31, 164, 99)    # Verde per Consulenza Adattiva
    COLOR_FISSO = RGBColor(46, 111, 214)   # Blu per Strategia Standard
    COLOR_NAVY = RGBColor(11, 17, 24)      # Sfondo
    COLOR_BLUE = RGBColor(52, 152, 219)    # Azzurro per titoli
    COLOR_TEXT = RGBColor(226, 232, 240)   # Testo principale
    COLOR_DARK_BG = RGBColor(241, 245, 250) # Sfondo tabelle

    # Mappa scenario a nome completo
    scenario_code = metrics.get('scenario_corrente', 'S0')
    scenario_name = _map_scenario_code_to_name(scenario_code)

    def add_title_slide():
        """Slide 1: Titolo con nome scenario completo"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = COLOR_NAVY

        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(9), Inches(1.5))
        title_frame = title_box.text_frame
        title_frame.text = "FINsim Financial Analysis"
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(54)
        title_para.font.bold = True
        title_para.font.color.rgb = COLOR_BLUE
        title_para.alignment = PP_ALIGN.CENTER

        subtitle_box = slide.shapes.add_textbox(Inches(0.5), Inches(4.2), Inches(9), Inches(1))
        subtitle_frame = subtitle_box.text_frame
        subtitle_frame.text = f"{scenario_name} | {datetime.now().strftime('%d/%m/%Y')}"
        subtitle_para = subtitle_frame.paragraphs[0]
        subtitle_para.font.size = Pt(20)
        subtitle_para.font.color.rgb = COLOR_TEXT
        subtitle_para.alignment = PP_ALIGN.CENTER

    def add_kpi_and_table_slide():
        """Slide 2: KPI (sinistra) + Tabella (destra) affiancati"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = COLOR_NAVY

        # Titolo
        title_box = slide.shapes.add_textbox(Inches(0.3), Inches(0.2), Inches(9.4), Inches(0.5))
        title_frame = title_box.text_frame
        title_frame.text = "KPI Principali"
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(28)
        title_para.font.bold = True
        title_para.font.color.rgb = COLOR_BLUE

        # Sinistra: 3 box KPI compatti
        kpi_data = [
            ("💰 Commissioni", f"€ {comm_adapt - comm_fisso:,.0f}"),
            ("🎯 Conversione", f"{conv_adapt - conv_fisso:.1f}%"),
            ("💭 Fiducia", f"{fid_adapt - fid_fisso:.1f}%")
        ]

        box_height = 1.4
        box_y = 0.9
        for idx, (label, value) in enumerate(kpi_data):
            y_pos = box_y + idx * (box_height + 0.2)
            box = slide.shapes.add_shape(1, Inches(0.3), Inches(y_pos), Inches(4.8), Inches(box_height))
            box.fill.solid()
            box.fill.fore_color.rgb = COLOR_ADAPT
            box.line.color.rgb = COLOR_BLUE
            box.line.width = Pt(2)

            txt = box.text_frame
            txt.word_wrap = True
            txt.clear()
            p1 = txt.paragraphs[0]
            p1.text = label
            p1.font.size = Pt(12)
            p1.font.bold = True
            p1.font.color.rgb = RGBColor(255, 255, 255)

            txt.add_paragraph()
            p2 = txt.paragraphs[1]
            p2.text = value
            p2.font.size = Pt(16)
            p2.font.bold = True
            p2.font.color.rgb = COLOR_BLUE

        # Destra: Tabella KPI
        rows, cols = 5, 4
        left = Inches(5.3)
        top = Inches(0.85)
        width = Inches(4.4)
        height = Inches(5.5)

        table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
        table = table_shape.table

        headers = ["Metrica", "Consult. Adattiva", "Strat. Standard", "Delta"]
        data = [
            ["Commissioni (€)", f"{comm_adapt:,.0f}", f"{comm_fisso:,.0f}", f"{comm_adapt - comm_fisso:,.0f}"],
            ["Conversione (%)", f"{conv_adapt:.1f}%", f"{conv_fisso:.1f}%", f"{conv_adapt - conv_fisso:.1f}%"],
            ["Fiducia Media (%)", f"{fid_adapt:.1f}%", f"{fid_fisso:.1f}%", f"{fid_adapt - fid_fisso:.1f}%"],
            ["Proposte", f"{prop_adapt}", f"{prop_fisso}", f"{prop_adapt - prop_fisso}"],
        ]

        # Header con colore verde (Consulenza Adattiva)
        for col_idx, header_text in enumerate(headers):
            cell = table.cell(0, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_ADAPT
            tf = cell.text_frame
            tf.text = header_text
            tf.paragraphs[0].font.bold = True
            tf.paragraphs[0].font.size = Pt(9)
            tf.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)

        # Dati con testo nero su sfondo chiaro
        for row_idx, row_data in enumerate(data, 1):
            for col_idx, cell_text in enumerate(row_data):
                cell = table.cell(row_idx, col_idx)
                cell.fill.solid()
                cell.fill.fore_color.rgb = COLOR_DARK_BG
                tf = cell.text_frame
                tf.text = cell_text
                tf.paragraphs[0].font.size = Pt(9)
                tf.paragraphs[0].font.color.rgb = RGBColor(0, 0, 0)  # Nero per leggibilità
                if col_idx == 0:
                    tf.paragraphs[0].font.bold = True

    def add_executive_analysis_slide():
        """Slide 3: Analisi Esecutiva sintetica (max 400 caratteri)"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = COLOR_NAVY

        title_box = slide.shapes.add_textbox(Inches(0.3), Inches(0.2), Inches(9.4), Inches(0.5))
        title_frame = title_box.text_frame
        title_frame.text = "Analisi Esecutiva"
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(28)
        title_para.font.bold = True
        title_para.font.color.rgb = COLOR_BLUE

        # Testo LLM puro, limitato a 400 caratteri
        analysis_text = llm_analysis[:400].strip()
        if len(llm_analysis) > 400:
            analysis_text += "…"

        content_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.9), Inches(9), Inches(6.2))
        tf = content_box.text_frame
        tf.word_wrap = True
        tf.text = analysis_text
        tf.paragraphs[0].font.size = Pt(13)
        tf.paragraphs[0].font.color.rgb = COLOR_TEXT
        tf.paragraphs[0].line_spacing = 1.4

    def add_views_summary_slide():
        """Slide aggiuntiva: Riepilogo delle tre viste operative"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = COLOR_NAVY

        title_box = slide.shapes.add_textbox(Inches(0.3), Inches(0.2), Inches(9.4), Inches(0.5))
        title_frame = title_box.text_frame
        title_frame.text = "Riepilogo Viste Operative"
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(28)
        title_para.font.bold = True
        title_para.font.color.rgb = COLOR_BLUE

        scenario_code = metrics.get('scenario_corrente', 'S0')
        views_summary = _generate_views_summary(metrics, scenario_code)

        sezioni = [
            ("🏦 Vista Banca", views_summary["banca"]),
            ("👤 Vista Promotore", views_summary["promotore"]),
            ("🤝 Vista Cliente", views_summary["cliente"])
        ]

        y_pos = 0.9
        for titolo_sezione, testo_sezione in sezioni:
            box = slide.shapes.add_shape(1, Inches(0.4), Inches(y_pos), Inches(9.2), Inches(1.7))
            box.fill.solid()
            box.fill.fore_color.rgb = RGBColor(20, 30, 42)
            box.line.color.rgb = COLOR_BLUE
            box.line.width = Pt(1)

            tf = box.text_frame
            tf.word_wrap = True
            tf.clear()
            p1 = tf.paragraphs[0]
            p1.text = titolo_sezione
            p1.font.size = Pt(14)
            p1.font.bold = True
            p1.font.color.rgb = COLOR_ADAPT

            tf.add_paragraph()
            p2 = tf.paragraphs[1]
            p2.text = testo_sezione
            p2.font.size = Pt(11)
            p2.font.color.rgb = COLOR_TEXT
            p2.line_spacing = 1.2

            y_pos += 1.9

    def add_chart_with_text_slide(title: str, img_path: str, testo: str, color_title=None):
        """Slide con immagine a sinistra e testo didascalia a destra"""
        if color_title is None:
            color_title = COLOR_BLUE
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = COLOR_NAVY

        # Titolo
        title_box = slide.shapes.add_textbox(Inches(0.3), Inches(0.2), Inches(9.4), Inches(0.5))
        tf = title_box.text_frame
        tf.text = title
        tf.paragraphs[0].font.size = Pt(22)
        tf.paragraphs[0].font.bold = True
        tf.paragraphs[0].font.color.rgb = color_title

        # Immagine a sinistra
        slide.shapes.add_picture(img_path, Inches(0.3), Inches(0.8), Inches(5.2), Inches(5.5))

        # Testo a destra
        txt_box = slide.shapes.add_textbox(Inches(5.7), Inches(0.8), Inches(4.0), Inches(5.5))
        tf2 = txt_box.text_frame
        tf2.word_wrap = True
        p = tf2.paragraphs[0]
        p.text = testo[:600] if len(testo) > 600 else testo
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT
        p.line_spacing = 1.2

    def add_conclusions_slide():
        """Slide 7: Conclusioni con terminologia corretta"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = COLOR_NAVY

        title_box = slide.shapes.add_textbox(Inches(0.3), Inches(0.2), Inches(9.4), Inches(0.5))
        title_frame = title_box.text_frame
        title_frame.text = "Conclusioni e Prossimi Passi"
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(28)
        title_para.font.bold = True
        title_para.font.color.rgb = COLOR_BLUE

        content_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.85), Inches(9), Inches(6.4))
        tf = content_box.text_frame
        tf.word_wrap = True

        conclusions = [
            f"✅ Situazione Competitiva:",
            f"  • Consulenza Adattiva mantiene leadership su commissioni e conversione",
            f"  • Engagement cliente: {'Positivo' if fid_adapt > fid_fisso else 'Richiede attenzione'}",
            f"",
            f"📌 Azioni Prioritarie per il Prossimo Round:",
            f"  1. Consolidare il vantaggio della Consulenza Adattiva",
            f"  2. Monitorare {churn_count} clienti a rischio di abbandono clientela",
            f"  3. Scalare la strategia personalizzata nei segmenti ad alta redditività",
            f"",
            f"⚠️ Metriche di Conformità:",
            f"  • Clienti a rischio abbandono: {churn_count}",
            f"  • Alert normativi: {mifid_count}",
        ]

        for idx, line_text in enumerate(conclusions):
            if idx > 0:
                tf.add_paragraph()
            p = tf.paragraphs[idx]
            p.text = line_text
            p.font.size = Pt(11)
            p.font.color.rgb = COLOR_TEXT
            p.space_before = Pt(3)
            p.space_after = Pt(3)
            p.line_spacing = 1.2

    # ============================================================================
    # GENERAZIONE SLIDE
    # ============================================================================
    add_title_slide()
    add_kpi_and_table_slide()
    add_views_summary_slide()
    add_executive_analysis_slide()

    scenario_id = metrics.get('scenario_corrente', 'S0')
    immagini = _genera_immagini_grafici(metrics, scenario_id)

    # Slide 4: Heatmap con testo
    if immagini.get('heatmap'):
        heatmap_text = "Questa mappa mostra la performance relativa della Consulenza Adattiva vs Strategia Standard sui diversi segmenti clienti. Verde indica dominio della Consulenza Adattiva, rosso indica vantaggi della Strategia Standard."
        add_chart_with_text_slide(
            "Mappa di Valore (Patrimonio vs Profilo di Rischio)",
            immagini['heatmap'],
            heatmap_text
        )

    # Slide 5: Waterfall con testo
    if immagini.get('waterfall'):
        waterfall_text = "Analisi della contribuzione al patrimonio gestito: mostra come la raccolta netta, l'effetto mercato e l'abbandono di clientela hanno determinato la variazione patrimoniale finale nel periodo."
        add_chart_with_text_slide(
            "Analisi Contribuzione Patrimonio Gestito",
            immagini['waterfall'],
            waterfall_text
        )

    # Slide 6: Linee Performance con testo
    if immagini.get('linee'):
        linee_text = "Evoluzione della raccolta cumulata nel tempo: la Consulenza Adattiva (linea verde) evidenzia un trend superiore rispetto alla Strategia Standard (linea blu) lungo i 200 round."
        add_chart_with_text_slide(
            "Evoluzione Performance Cumulata",
            immagini['linee'],
            linee_text
        )

    # Slide 7: Conclusioni
    add_conclusions_slide()

    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
        prs.save(tmp.name)
        tmp_path = tmp.name

    return FileResponse(
        path=tmp_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"FINsim_Presentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
    )


@app.post("/api/advisor/export-pdf", tags=["advisor"])
async def export_advisor_pdf(request: AdvisorRequest) -> FileResponse:
    """Generate PDF report with metrics and LLM-generated analysis."""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    metrics = request.metrics_data or {}

    # Estrai metriche con valori di fallback
    comm_adapt = float(metrics.get('commissioni_cumulate_adapt') or 0)
    comm_fisso = float(metrics.get('commissioni_cumulate_fisso') or 0)
    conv_adapt = float(metrics.get('tasso_conversione_adapt_pct') or 0)
    conv_fisso = float(metrics.get('tasso_conversione_fisso_pct') or 0)
    fid_adapt = float(metrics.get('fiducia_media_adapt') or 0)
    fid_fisso = float(metrics.get('fiducia_media_fisso') or 0)
    prop_adapt = int(metrics.get('proposte_totali_adapt') or 0)
    prop_fisso = int(metrics.get('proposte_totali_fisso') or 0)
    churn = int(metrics.get('churn_risk_count') or 0)
    mifid = int(metrics.get('mifid_alerts_count') or 0)

    # Genera analisi esecutiva tramite LLM
    llm_analysis = _generate_executive_analysis(metrics)

    # Crea PDF con ReportLab
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    doc = SimpleDocTemplate(tmp_path, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()

    # Stili personalizzati
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1FA463'),
        spaceAfter=12,
        alignment=1
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1FA463'),
        spaceAfter=8,
        spaceBefore=8
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=4
    )

    # Titolo
    elements.append(Paragraph("FINsim Financial Analysis Report", title_style))
    elements.append(Spacer(1, 0.3*inch))

    # Metadati
    meta_text = f"<b>Scenario:</b> {metrics.get('scenario_corrente', 'N/A')}<br/><b>Date:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/><b>Coverage:</b> 200 historical rounds"
    elements.append(Paragraph(meta_text, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))

    # Analisi Esecutiva
    elements.append(Paragraph("Executive Summary", heading_style))
    elements.append(Paragraph(llm_analysis, normal_style))
    elements.append(Spacer(1, 0.3*inch))

    # Riepilogo Viste Operative
    scenario_code_pdf = metrics.get('scenario_corrente', 'S0')
    views_summary = _generate_views_summary(metrics, scenario_code_pdf)

    elements.append(Paragraph("Riepilogo Viste Operative", heading_style))

    vista_style = ParagraphStyle(
        'VistaStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=8,
        textColor=colors.HexColor('#1FA463')
    )

    elements.append(Paragraph("<b>Vista Banca</b>", vista_style))
    elements.append(Paragraph(views_summary["banca"], normal_style))
    elements.append(Spacer(1, 0.15*inch))

    elements.append(Paragraph("<b>Vista Promotore</b>", vista_style))
    elements.append(Paragraph(views_summary["promotore"], normal_style))
    elements.append(Spacer(1, 0.15*inch))

    elements.append(Paragraph("<b>Vista Cliente</b>", vista_style))
    elements.append(Paragraph(views_summary["cliente"], normal_style))
    elements.append(Spacer(1, 0.3*inch))

    # Tabella KPI
    elements.append(Paragraph("Key Performance Indicators", heading_style))
    kpi_data = [
        ['Metric', 'ADAPT (IA)', 'FISSO (Benchmark)', 'Delta'],
        ['Cumulative Commissions (€)', f'{comm_adapt:,.0f}', f'{comm_fisso:,.0f}', f'{comm_adapt - comm_fisso:,.0f}'],
        ['Conversion Rate (%)', f'{conv_adapt:.1f}%', f'{conv_fisso:.1f}%', f'{conv_adapt - conv_fisso:.1f}%'],
        ['Average Trust (%)', f'{fid_adapt:.1f}%', f'{fid_fisso:.1f}%', f'{fid_adapt - fid_fisso:.1f}%'],
        ['Total Proposals', f'{prop_adapt}', f'{prop_fisso}', f'{prop_adapt - prop_fisso}'],
    ]

    kpi_table = Table(kpi_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1FA463')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 0.3*inch))

    # Risk Metrics
    elements.append(Paragraph("Risk & Compliance Metrics", heading_style))
    risk_text = f"<b>Clients at Churn Risk:</b> {churn}<br/><b>MIFID/CONSOB Alerts:</b> {mifid}<br/><b>Overall Risk Level:</b> {'High' if (churn + mifid) > 10 else 'Medium' if (churn + mifid) > 5 else 'Low'}"
    elements.append(Paragraph(risk_text, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))

# Grafici come immagini PNG con didascalie LLM
    from reportlab.platypus import Image as RLImage
    scenario_id = metrics.get('scenario_corrente', 'S0')
    immagini = _genera_immagini_grafici(metrics, scenario_id)

    grafici_da_includere = [
        ('heatmap', 'Mappa di Valore (Patrimonio vs Rischio)',
         'Analizza questa mappa di valore e spiega in 3 frasi cosa indicano le celle verdi e rosse per la strategia commerciale della banca. Usa linguaggio da consulente finanziario senior.'),
        ('waterfall', 'Analisi Contribuzione Patrimonio Gestito',
         'Analizza questo grafico a cascata del patrimonio gestito e spiega in 3 frasi i fattori principali che hanno determinato la variazione finale. Usa linguaggio da consulente finanziario senior.'),
        ('linee', 'Evoluzione Performance Cumulata',
         'Analizza queste linee di performance cumulata ADAPT vs FISSO e spiega in 3 frasi cosa indica la divergenza tra le due strategie. Usa linguaggio da consulente finanziario senior.'),
        ('guadagni', 'Andamento Ricavi Cumulati',
         'Analizza questo grafico dei ricavi cumulati e spiega in 3 frasi le implicazioni strategiche per il prossimo periodo. Usa linguaggio da consulente finanziario senior.'),
    ]

    for chiave, titolo, prompt_llm in grafici_da_includere:
        if immagini.get(chiave):
            elements.append(PageBreak())
            elements.append(Paragraph(titolo, heading_style))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(RLImage(immagini[chiave], width=6*inch, height=3.5*inch))
            elements.append(Spacer(1, 0.15*inch))
            # Genera didascalia LLM
            try:
                payload_llm = {
                    "model": OllamaAdvisor.MODEL_NAME,
                    "prompt": f"Scenario {scenario_id}. KPI: Commissioni ADAPT €{comm_adapt:,.0f}, FISSO €{comm_fisso:,.0f}. Conversione ADAPT {conv_adapt:.1f}%, FISSO {conv_fisso:.1f}%. {prompt_llm}",
                    "stream": False
                }
                r = requests.post(OllamaAdvisor.OLLAMA_GENERATE_URL, json=payload_llm, timeout=60)
                didascalia = r.json().get("response", "").strip()[:1500] if r.ok else ""
            except Exception:
                didascalia = ""
            if didascalia:
                elements.append(Paragraph(didascalia, normal_style))
            elements.append(Spacer(1, 0.2*inch))
    

    # Build PDF
    doc.build(elements)

    return FileResponse(
        path=tmp_path,
        media_type="application/pdf",
        filename=f"FINsim_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

# =====================================================================
# HEALTH AND DASHBOARD ENDPOINTS
# =====================================================================

@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "FINsim Unified API",
        "llm_model": OllamaAdvisor.MODEL_NAME
    }


@app.get("/api/dashboard/scenari", tags=["dashboard"])
async def get_scenari():
    """Get list of all scenario IDs"""
    docs = list(collection.find({}, {"scenario_id": 1}))
    return {"scenari": [d["scenario_id"] for d in docs if "scenario_id" in d]}


@app.get("/api/dashboard/scenario/{scenario_id}", tags=["dashboard"])
async def get_scenario(scenario_id: str):
    """Get detailed scenario data"""
    # Mappa scenario_id dal frontend (Base, Espansione, etc.) al database (S0_200, S1_200, etc.)
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    doc.pop("_id", None)
    rounds_summary = []
    for r in doc.pop("rounds", []):
        rounds_summary.append({
            "round": r.get("round"),
            "compliance_rate": r.get("compliance_rate"),
            "mismatch_rate": r.get("mismatch_rate"),
            "prodotto_dominante": r.get("prodotto_dominante"),
            "dispersione_prodotti": r.get("dispersione_prodotti"),
            "compliance_per_promotore": r.get("compliance_per_promotore"),
            "decisions_created": r.get("decisions_created"),
            "clients_updated": r.get("clients_updated"),
        })
    doc["rounds_summary"] = rounds_summary
    return doc


@app.get("/api/dashboard/tutti", tags=["dashboard"])
async def get_tutti_scenari():
    """Get summary of all scenarios"""
    docs = list(collection.find({}, {
        "scenario_id": 1,
        "summary": 1,
        "business_metrics": 1,
        "num_rounds": 1,
        "total_decisions": 1,
    }))
    result = {}
    for d in docs:
        d.pop("_id", None)
        sid = d.get("scenario_id")
        if sid:
            result[sid] = d
    return {"scenari": result}

@app.get("/api/charts/waterfall-data")
def get_waterfall_data(scenario_id: str = "S0"):
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})
    if not doc or "rounds" not in doc:
        return {"aum_iniziale": 0, "nuova_raccolta": 0, "effetto_mercato": 0, "churn": 0}

    rounds = sorted(doc["rounds"], key=lambda x: x.get("round", 0))
    TICKET_MEDIO = 100000

    raccolta_totale = 0.0
    churn_totale = 0.0
    clienti_totali = 0
    fiducia_pre_totale = 0.0
    fiducia_post_totale = 0.0
    count_fiducia = 0

    for r in rounds:
        for promo in r.get("promoters_data", []):
            if "ADAPT" not in promo.get("promotore_id", ""):
                continue
            for s in promo.get("strategies", []):
                clienti = s.get("clients_in_cluster", 0)
                clienti_totali += clienti

                if s.get("accettato"):
                    raccolta_totale += clienti * TICKET_MEDIO

                delta = s.get("delta_fiducia_medio", 0)
                fid_pre = s.get("fiducia_media_pre", 0)
                fid_post = s.get("fiducia_media_post", 0)

                if delta < -0.05:
                    churn_totale += clienti * TICKET_MEDIO * abs(delta) * 2

                fiducia_pre_totale += fid_pre * clienti
                fiducia_post_totale += fid_post * clienti
                count_fiducia += clienti

    aum_iniziale = 10000000 # 100 clienti * 100000 ticket medio = patrimonio inziale simulazione
    
    # Effetto mercato: negativo se fiducia cala, positivo se sale
    if count_fiducia > 0:
        delta_fiducia_medio = (fiducia_post_totale - fiducia_pre_totale) / count_fiducia
        effetto_mercato = delta_fiducia_medio * raccolta_totale * 5
    else:
        effetto_mercato = 0

    return {
        "aum_iniziale": round(aum_iniziale),
        "nuova_raccolta": round(raccolta_totale),
        "effetto_mercato": round(effetto_mercato),
        "churn": round(-churn_totale)
    }
    
@app.get("/api/charts/heatmap-data")
def get_heatmap_data(scenario_id: str = "S0"):
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})
    if not doc or "rounds" not in doc:
        return {"matrice": [[0,0,0],[0,0,0],[0,0,0]]}

    profili_rischio = {"Conservative": 0, "Balanced": 1, "Aggressive": 2}
    patrimoni = {"basso": 0, "medio": 1, "alto": 2}

    adapt_acc = [[0,0,0],[0,0,0],[0,0,0]]
    adapt_tot = [[0,0,0],[0,0,0],[0,0,0]]
    fisso_acc = [[0,0,0],[0,0,0],[0,0,0]]
    fisso_tot = [[0,0,0],[0,0,0],[0,0,0]]

    for r in doc["rounds"]:
        for promo in r.get("promoters_data", []):
            pid = promo.get("promotore_id", "")
            for s in promo.get("strategies", []):
                profilo = s.get("profilo_rischio_prevalente", "Balanced")
                coords = s.get("cluster_coords", [1, 1])
                clienti = s.get("clients_in_cluster", 5)

                # Mappa coords a indice patrimonio (0=basso, 1=medio, 2=alto)
                col = min(int(coords[0] / 7 * 3), 2) if coords else 1
                row = profili_rischio.get(profilo, 1)

                if "ADAPT" in pid:
                    adapt_tot[row][col] += 1
                    if s.get("accettato"):
                        adapt_acc[row][col] += 1
                elif "FISSO" in pid:
                    fisso_tot[row][col] += 1
                    if s.get("accettato"):
                        fisso_acc[row][col] += 1

    matrice = []
    for row in range(3):
        riga = []
        for col in range(3):
            ta = adapt_tot[row][col]
            tf = fisso_tot[row][col]
            ra = adapt_acc[row][col] / ta if ta > 0 else 0
            rf = fisso_acc[row][col] / tf if tf > 0 else 0
            riga.append(round((ra - rf) * 100, 2))
        matrice.append(riga)

    return {"matrice": matrice}
# =====================================================================
# PLOTLY CHARTS HELPERS & ENDPOINTS
# =====================================================================

COLORI_DIVERGENTI = ["#e11d48", "#f59e0b", "#059669"]

def applica_stile_premium(fig, titolo: str, dark_mode: bool = True):
    """Applica tema enterprise con supporto Light/Dark Mode"""
    if dark_mode:
        # FINSIM-MOD: Dark Mode per dashboard Vue
        fig.update_layout(
            title={
                'text': f"<b>{titolo}</b>",
                'y': 0.96,
                'x': 0.02,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': dict(size=18, family="Segoe UI, -apple-system, Arial", color="#C7D5E6")
            },
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(30,41,59,0.3)',
            font=dict(family="Segoe UI, -apple-system, Arial", color="#C7D5E6", size=13),
            margin=dict(l=80, r=40, t=70, b=70),
            showlegend=True,
            hovermode='closest'
        )
        fig.update_xaxes(
            title_font=dict(size=14, color="#C7D5E6", weight="bold"),
            tickfont=dict(size=12, color="#C7D5E6"),
            gridcolor="rgba(199, 213, 230, 0.1)",
            zeroline=False
        )
        fig.update_yaxes(
            title_font=dict(size=14, color="#C7D5E6", weight="bold"),
            tickfont=dict(size=12, color="#C7D5E6"),
            gridcolor="rgba(199, 213, 230, 0.1)",
            zeroline=False
        )
        # FINSIM-MOD: Update colorbar per dark mode
        fig.update_coloraxes(
            colorbar=dict(
                tickfont=dict(color="#C7D5E6", size=11),
                title=dict(font=dict(color="#C7D5E6", size=12))
            )
        )
    else:
        # Light Mode originale
        fig.update_layout(
            title={
                'text': f"<b>{titolo}</b>",
                'y': 0.96,
                'x': 0.02,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': dict(size=18, family="Segoe UI, -apple-system, Arial", color="#111827")
            },
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Segoe UI, -apple-system, Arial", color="#374151", size=13),
            margin=dict(l=80, r=40, t=70, b=70),
            showlegend=True
        )
        fig.update_xaxes(
            title_font=dict(size=14, color="#111827", weight="bold"),
            tickfont=dict(size=12, color="#374151")
        )
        fig.update_yaxes(
            title_font=dict(size=14, color="#111827", weight="bold"),
            tickfont=dict(size=12, color="#374151")
        )
    return fig


@app.post("/api/charts/heatmap", tags=["charts"])
async def get_heatmap_performance(request: AdvisorRequest) -> dict:
    """Generate performance heatmap (Patrimonio Gestito vs Profilo Rischio) as Plotly JSON.
    Data-Driven: Calculates from real conversion rate delta if matrice_performance is unavailable."""
    # FINSIM-MOD: Import inline for data-driven heatmap generation
    from visualizzatore_grafici import genera_heatmap_performance

    metrics = request.metrics_data or {}

    # Call the data-driven function from visualizzatore_grafici
    fig = genera_heatmap_performance(metrics)

    # Apply dark mode styling
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.3)',
        font=dict(color='#C7D5E6')
    )
    fig.update_xaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)',
                     title_font=dict(color='#C7D5E6'))
    fig.update_yaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)',
                     title_font=dict(color='#C7D5E6'))

    return {"data": fig.to_json()}


@app.post("/api/charts/waterfall", tags=["charts"])
async def get_waterfall_patrimonio(request: AdvisorRequest) -> dict:
    """Generate waterfall chart for patrimonio composition as Plotly JSON"""
    metrics = request.metrics_data or {}

    aum_iniziale = float(metrics.get("aum_iniziale", 100000000))
    nuova_raccolta = float(metrics.get("nuova_raccolta_netta", 15500000))
    effetto_mercato = float(metrics.get("effetto_mercato", -3200000))
    churn_clienti = float(metrics.get("patrimonio_perso_churn", -5800000))
    aum_finale = aum_iniziale + nuova_raccolta + effetto_mercato + churn_clienti

    fig = go.Figure(go.Waterfall(
        name="Patrimonio Gestito", orientation="v",
        measure=["relative", "relative", "relative", "relative", "total"],
        x=["Patrimonio Iniziale", "Nuova Raccolta", "Effetto Mercato", "Abbandoni", "Patrimonio Finale"],
        textposition="auto",
        text=[f"+{aum_iniziale/1e6:.1f}M", f"{nuova_raccolta/1e6:.1f}M", f"{effetto_mercato/1e6:.1f}M", f"{aum_finale/1e6:.1f}M"],
        y=[aum_iniziale, nuova_raccolta, effetto_mercato, churn_clienti, 0],
        connector={"line": {"color": "rgba(0,0,0,0.1)", "width": 1}},
        decreasing={"marker": {"color": "#e11d48"}},
        increasing={"marker": {"color": "#059669"}},
        totals={"marker": {"color": "#2e6fd6"}}
    ))

    fig.update_layout(
        showlegend=False,
    )

    fig = applica_stile_premium(fig, "Analisi di Contribuzione del Patrimonio Gestito", dark_mode=True)
    fig.update_traces(textfont=dict(color="#ffffff", size=12))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=10, color="#059669", symbol="square"), name='Incremento patrimoniale'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=10, color="#e11d48", symbol="square"), name='Riduzione patrimoniale'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=10, color="#2e6fd6", symbol="square"), name='Patrimonio finale'))
    fig.update_layout(
        showlegend=True,
        margin=dict(l=60, r=60, t=120, b=100),
        legend=dict(orientation='h', yanchor='bottom', y=-0.25, xanchor='center', x=0.5, font=dict(size=11))
    )

    return {"data": fig.to_json()}


@app.post("/api/charts/performance-lines", tags=["charts"])
async def get_linee_comparative(request: AdvisorRequest) -> dict:
    """
    Generate comparative performance lines as Plotly JSON.
    Data-Driven: Reads from MongoDB instead of synthetic data.
    """
    metrics = request.metrics_data or {}
    scenario_id = metrics.get("scenario_corrente", "S0")

    # Leggi dati reali da MongoDB
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})

    storico_ia = []
    storico_fisso = []

    if doc and "rounds" in doc:
        TICKET_MEDIO_MLN = 0.1
        raccolta_cumulata_ia = 0.0
        raccolta_cumulata_fisso = 0.0

        for r in sorted(doc.get("rounds", []), key=lambda x: x.get("round", 0)):
            raccolta_round_ia = 0.0
            raccolta_round_fisso = 0.0

            for promo in r.get("promoters_data", []):
                pid = promo.get("promotore_id", "")

                for strat in promo.get("strategies", []):
                    if strat.get("accettato") == True:
                        clienti_convertiti = strat.get("clients_in_cluster", 0)
                        volume_generato = clienti_convertiti * TICKET_MEDIO_MLN

                        if "ADAPT" in pid:
                            raccolta_round_ia += volume_generato
                        elif "FISSO" in pid:
                            raccolta_round_fisso += volume_generato

            raccolta_cumulata_ia += raccolta_round_ia
            raccolta_cumulata_fisso += raccolta_round_fisso

            storico_ia.append(round(raccolta_cumulata_ia, 2))
            storico_fisso.append(round(raccolta_cumulata_fisso, 2))

    # Fallback: se nessun dato da MongoDB, ritorna zeri (non sintetici)
    if not storico_ia:
        storico_ia = [0] * 200
    if not storico_fisso:
        storico_fisso = [0] * 200

    # Estendi a 200 elementi se necessario
    storico_ia = storico_ia[:200] + [0] * (200 - len(storico_ia))
    storico_fisso = storico_fisso[:200] + [0] * (200 - len(storico_fisso))

    proposte = [f"Prop. {i}" for i in range(1, 201)]

    df_ia = pd.DataFrame({"Proposta": proposte, "Valore": storico_ia, "Strategia": "Consulenza IA Dinamica"})
    df_fisso = pd.DataFrame({"Proposta": proposte, "Valore": storico_fisso, "Strategia": "Strategia Standard"})
    df = pd.concat([df_ia, df_fisso])

    fig = px.line(
        df, x="Proposta", y="Valore", color="Strategia",
        color_discrete_map={"Consulenza IA Dinamica": "#059669", "Strategia Standard": "#e11d48"}
    )

    fig.update_traces(line=dict(width=3))
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text=""
        ),
        xaxis=dict(showticklabels=False)
    )

    fig = applica_stile_premium(fig, "Evoluzione Performance Cumulata", dark_mode=True)

    return {"data": fig.to_json()}


@app.post("/api/charts/sopravvivenza", tags=["charts"])
async def get_curva_sopravvivenza(request: AdvisorRequest) -> dict:
    """Generate Kaplan-Meier Customer Retention Curve as Plotly JSON.
    Data-Driven: Fetches real rounds data from MongoDB if available.
    Forces 200-round scenario resolution."""
    # FINSIM-MOD: Imported from visualizzatore_grafici
    from visualizzatore_grafici import genera_curva_sopravvivenza

    metrics = request.metrics_data or {}
    scenario_id = metrics.get("scenario_corrente", "S0")

    # FINSIM-MOD: Force 200-round scenario resolution by querying scenario_id field
    # Fetch rounds data from MongoDB
    rounds_data = []
    debug_info = {}
    try:
        # Query MongoDB for simulation data (200 rounds)
        # DB stores as "{scenario_id}_200" (e.g., "S0_200" not "S0")
        db_scenario_key = f"{scenario_id}_200"
        debug_info["searching_for"] = db_scenario_key

        # Try direct query first
        sim_doc = collection.find_one({"scenario_id": db_scenario_key})
        debug_info["found_direct"] = sim_doc is not None

        if not sim_doc:
            # Fallback: search by scenario_id alone, get largest num_rounds
            sim_doc = collection.find_one(
                {"scenario_id": {"$regex": f"^{scenario_id}"}},
                sort=[("num_rounds", -1), ("_id", -1)]
            )
            debug_info["found_fallback"] = sim_doc is not None

        if sim_doc and "rounds" in sim_doc:
            rounds_data = sim_doc["rounds"]
            debug_info["rounds_fetched"] = len(rounds_data)
        else:
            debug_info["error"] = f"No rounds found (tried {db_scenario_key})"
    except Exception as e:
        debug_info["exception"] = str(e)

    business_metrics = {
        "aum_iniziale": float(metrics.get("aum_iniziale", 100000000)),
        "patrimonio_perso_churn_adapt": float(metrics.get("patrimonio_perso_churn", 5800000)) * 0.6,
        "patrimonio_perso_churn_fisso": float(metrics.get("patrimonio_perso_churn", 5800000)) * 1.0,
    }

    # Genera la curva usando dati reali o fallback a sintetici
    fig = genera_curva_sopravvivenza(rounds_data, business_metrics)

    # Applica dark mode styling se necessario
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.3)',
        font=dict(color='#C7D5E6')
    )
    fig.update_xaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')
    fig.update_yaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')

    return {"data": fig.to_json()}


@app.post("/api/charts/sankey-flussi", tags=["charts"])
async def get_sankey_flussi(request: AdvisorRequest) -> dict:
    """[DEPRECATED] Generate Sankey flow diagram for client migration as Plotly JSON"""
    label = ["Cluster Basso Rischio", "Cluster Medio Rischio", "Cluster Alto Rischio", "Stabili", "Upgrade Profilo", "ABBANDONI"]
    source = [0, 0, 0, 1, 1, 1, 2, 2, 2]
    target = [3, 4, 5, 3, 4, 5, 3, 4, 5]
    value = [120, 30, 5, 200, 80, 15, 90, 10, 45]
    colori_link = ["rgba(5, 150, 105, 0.2)", "rgba(245, 158, 11, 0.2)", "rgba(225, 29, 72, 0.2)"] * 3

    fig = go.Figure(data=[go.Sankey(
        textfont=dict(size=13, color="#111827"),
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="#111827", width=1),
            label=[f"<b>{l}</b>" for l in label],
            color=["#3b82f6", "#f59e0b", "#ec4899", "#059669", "#10b981", "#e11d48"]
        ),
        link=dict(source=source, target=target, value=value, color=colori_link)
    )])

    fig.update_layout(
        showlegend=False,
    )

    fig = applica_stile_premium(fig, "Mappa di Migrazione dei Clienti e Tasso di Abbandoni", dark_mode=True)

    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)

    return {"data": fig.to_json()}


# =====================================================================
# STANDARDIZED CHART ENDPOINTS (STEP 2: Global Chart Exposure)
# =====================================================================

@app.post("/api/charts/heatmap", tags=["charts"])
async def get_heatmap_performance(request: AdvisorRequest) -> dict:
    """Generate Performance Heatmap (Patrimonio vs Rischio) as Plotly JSON"""
    from visualizzatore_grafici import genera_heatmap_performance

    metrics = request.metrics_data or {}

    fig = genera_heatmap_performance(metrics)

    # Dark mode styling
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.3)',
        font=dict(color='#C7D5E6')
    )
    fig.update_xaxes(tickfont=dict(color='#C7D5E6'))
    fig.update_yaxes(tickfont=dict(color='#C7D5E6'))

    return {"data": fig.to_json()}


@app.post("/api/charts/prodotti", tags=["charts"])
async def get_bar_prodotti(request: AdvisorRequest) -> dict:
    """Generate Product Satisfaction Bar Chart as Plotly JSON"""
    from visualizzatore_grafici import genera_bar_prodotti

    metrics = request.metrics_data or {}
    scenario_id = metrics.get("scenario_corrente", "S0")
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})

    soddisfazione_prodotti = [78, 62, 85, 54, 90]

    if doc and "rounds" in doc:
        from collections import defaultdict
        prodotti_satisfaction = defaultdict(lambda: {"totale": 0.0, "count": 0})

        for r in doc["rounds"]:
            for promo in r.get("promoters_data", []):
                for s in promo.get("strategies", []):
                    prod = s.get("prodotto", "Unknown")
                    soddisfazione = s.get("soddisfazione_cliente", 70)

                    prodotti_satisfaction[prod]["totale"] += soddisfazione
                    prodotti_satisfaction[prod]["count"] += 1

        prodotti_map = {
            "Fondi Azionari": 0,
            "Obbligazioni": 1,
            "ETF Tematici": 2,
            "Polizze": 3,
            "Liquidità": 4
        }

        for prod, idx in prodotti_map.items():
            if prod in prodotti_satisfaction and prodotti_satisfaction[prod]["count"] > 0:
                media = prodotti_satisfaction[prod]["totale"] / prodotti_satisfaction[prod]["count"]
                soddisfazione_prodotti[idx] = round(media, 1)

    business_metrics = {"soddisfazione_prodotti": soddisfazione_prodotti}
    fig = genera_bar_prodotti(business_metrics)

    # Dark mode styling
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.3)',
        font=dict(color='#C7D5E6')
    )
    fig.update_xaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')
    fig.update_yaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')

    return {"data": fig.to_json()}


@app.post("/api/charts/guadagni", tags=["charts"])
async def get_andamento_guadagni(request: AdvisorRequest) -> dict:
    """Generate Revenue Trend Chart (Profits over 200 rounds) as Plotly JSON"""
    from visualizzatore_grafici import genera_andamento_guadagni

    metrics = request.metrics_data or {}

    # Leggi dati reali da MongoDB
    scenario_id = metrics.get("scenario_corrente", "S0")
    if not scenario_id.endswith("_200"):
        db_scenario_id = f"{scenario_id}_200"
    else:
        db_scenario_id = scenario_id

    documento = collection.find_one({"scenario_id": db_scenario_id})

    # Costruisci dati di guadagni per round
    guadagni_adapt_per_round = []
    guadagni_fisso_per_round = []

    TICKET_MEDIO = 100000
    COMMISSIONE = 0.01

    if documento and "rounds" in documento:
        print(f"[DEBUG guadagni] Scenario: {db_scenario_id}, Rounds trovati: {len(documento['rounds'])}")
        if len(documento["rounds"]) > 0:
            print(f"[DEBUG guadagni] Nomi campi primo round: {documento['rounds'][0].keys()}")

        for r in sorted(documento.get("rounds", []), key=lambda x: x.get('round', 0)):
            guadagni_round_adapt = 0.0
            guadagni_round_fisso = 0.0

            for promo in r.get("promoters_data", []):
                pid = promo.get("promotore_id", "")
                for strat in promo.get("strategies", []):
                    if strat.get("accettato") == True:
                        clienti = strat.get("clients_in_cluster", 0)
                        commissione = (clienti * TICKET_MEDIO) * COMMISSIONE

                        if "ADAPT" in pid:
                            guadagni_round_adapt += commissione
                        elif "FISSO" in pid:
                            guadagni_round_fisso += commissione

            guadagni_adapt_per_round.append(guadagni_round_adapt)
            guadagni_fisso_per_round.append(guadagni_round_fisso)

    # Fallback a sintetici se vuoti
    if not guadagni_adapt_per_round:
        guadagni_adapt_per_round = [i**1.15 * 1200 for i in range(1, 201)]
        guadagni_fisso_per_round = [i * 1000 for i in range(1, 201)]

    # Passa i dati corretti alla funzione
    metrics_enriched = metrics.copy()
    metrics_enriched["guadagni_adapt_per_round"] = guadagni_adapt_per_round
    metrics_enriched["guadagni_fisso_per_round"] = guadagni_fisso_per_round

    fig = genera_andamento_guadagni(metrics_enriched)

    # Dark mode styling
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.3)',
        font=dict(color='#C7D5E6')
    )
    fig.update_xaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')
    fig.update_yaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')

    return {"data": fig.to_json()}


@app.post("/api/charts/linee-comparative", tags=["charts"])
async def get_linee_comparative(request: AdvisorRequest) -> dict:
    """Generate Comparative Performance Lines (Collections over 200 rounds) as Plotly JSON"""
    from visualizzatore_grafici import genera_linee_comparative

    metrics = request.metrics_data or {}

    # Leggi dati reali da MongoDB (raccolta cumulata per round)
    scenario_id = metrics.get("scenario_corrente", "S0")
    if not scenario_id.endswith("_200"):
        db_scenario_id = f"{scenario_id}_200"
    else:
        db_scenario_id = scenario_id

    documento = collection.find_one({"scenario_id": db_scenario_id})

    storico_ia = []
    storico_fisso = []

    TICKET_MEDIO_MLN = 0.1

    if documento and "rounds" in documento:
        raccolta_cumulata_ia = 0.0
        raccolta_cumulata_fisso = 0.0

        for r in sorted(documento.get("rounds", []), key=lambda x: x.get('round', 0)):
            raccolta_round_ia = 0.0
            raccolta_round_fisso = 0.0

            for promo in r.get("promoters_data", []):
                pid = promo.get("promotore_id", "")
                for strat in promo.get("strategies", []):
                    if strat.get("accettato") == True:
                        clienti_convertiti = strat.get("clients_in_cluster", 0)
                        volume_generato = clienti_convertiti * TICKET_MEDIO_MLN

                        if "ADAPT" in pid:
                            raccolta_round_ia += volume_generato
                        elif "FISSO" in pid:
                            raccolta_round_fisso += volume_generato

            raccolta_cumulata_ia += raccolta_round_ia
            raccolta_cumulata_fisso += raccolta_round_fisso

            storico_ia.append(round(raccolta_cumulata_ia, 2))
            storico_fisso.append(round(raccolta_cumulata_fisso, 2))

    # Fallback a sintetici se vuoti
    if not storico_ia:
        storico_ia = [i**1.2 * 10000 for i in range(1, 201)]
    if not storico_fisso:
        storico_fisso = [i * 9000 for i in range(1, 201)]

    # Passa i dati corretti alla funzione
    metrics_enriched = metrics.copy()
    metrics_enriched["storico_raccolta_adattivo"] = storico_ia
    metrics_enriched["storico_raccolta_fisso"] = storico_fisso

    fig = genera_linee_comparative(metrics_enriched)

    # Dark mode styling
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.3)',
        font=dict(color='#C7D5E6')
    )
    fig.update_xaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')
    fig.update_yaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')

    return {"data": fig.to_json()}


@app.post("/api/charts/waterfall", tags=["charts"])
async def get_waterfall_patrimonio(request: AdvisorRequest) -> dict:
    """Generate AUM Waterfall Chart as Plotly JSON"""
    from visualizzatore_grafici import genera_waterfall_patrimonio

    metrics = request.metrics_data or {}

    fig = genera_waterfall_patrimonio(metrics)

    # Dark mode styling
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.3)',
        font=dict(color='#C7D5E6')
    )
    fig.update_xaxes(tickfont=dict(color='#C7D5E6'))
    fig.update_yaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')

    return {"data": fig.to_json()}


@app.post("/api/charts/semaforo", tags=["charts"])
async def get_semaforo_adeguatezza(request: AdvisorRequest) -> dict:
    metrics = request.metrics_data or {}
    scenario_id = metrics.get("scenario_corrente", "S0")
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})

    if not doc or "rounds" not in doc:
        return {"data": "{}"}

    from collections import defaultdict
    prodotti = defaultdict(lambda: {"adeguatezza_totale": 0.0, "decisioni": 0, "accettate": 0})

    for r in doc["rounds"]:
        for promo in r.get("promoters_data", []):
            for s in promo.get("strategies", []):
                prod = s.get("prodotto_suggerito", "Altro").replace("_", " ")
                adeq = s.get("adeguatezza_score", 0.5)
                acc = s.get("accettato", False)
                prodotti[prod]["adeguatezza_totale"] += adeq
                prodotti[prod]["decisioni"] += 1
                if acc:
                    prodotti[prod]["accettate"] += 1

    righe = []
    for prod, vals in prodotti.items():
        if vals["decisioni"] > 0:
            adeq_media = vals["adeguatezza_totale"] / vals["decisioni"]
            acceptance = vals["accettate"] / vals["decisioni"]
            righe.append({
                "prodotto": prod,
                "adeguatezza_media": round(adeq_media, 2),
                "acceptance_rate": round(acceptance, 2),
                "num_decisioni": vals["decisioni"]
            })

    if not righe:
        return {"data": "{}"}

    summary_mock = {"matrice_strategica": righe}

    from visualizzatore_grafici import genera_semaforo_adeguatezza
    fig = genera_semaforo_adeguatezza(summary_mock)

    if fig is None:
        return {"data": "{}"}

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.3)',
        font=dict(color='#C7D5E6')
    )
    fig.update_xaxes(tickfont=dict(color='#C7D5E6'))
    fig.update_yaxes(tickfont=dict(color='#C7D5E6'))

    return {"data": fig.to_json()}


@app.post("/api/charts/accettazioni", tags=["charts"])
async def get_accettazioni_per_scenario(request: AdvisorRequest) -> dict:
    """Generate Acceptance Rate Grouped Bar Chart (ADAPT vs FISSO) as Plotly JSON"""
    from visualizzatore_grafici import genera_accettazioni_per_scenario

    metrics = request.metrics_data or {}
    scenario_id = metrics.get("scenario_corrente", "S0")
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})

    adapt_acc, adapt_tot, fisso_acc, fisso_tot = 0, 0, 0, 0

    if doc and "rounds" in doc:
        for r in doc["rounds"]:
            for promo in r.get("promoters_data", []):
                pid = promo.get("promotore_id", "")
                for s in promo.get("strategies", []):
                    if "ADAPT" in pid:
                        adapt_tot += 1
                        if s.get("accettato"): adapt_acc += 1
                    elif "FISSO" in pid:
                        fisso_tot += 1
                        if s.get("accettato"): fisso_acc += 1

    business_metrics = {
        "tasso_conversione_adapt_pct": round(adapt_acc / adapt_tot * 100, 1) if adapt_tot > 0 else 0,
        "tasso_conversione_fisso_pct": round(fisso_acc / fisso_tot * 100, 1) if fisso_tot > 0 else 0,
    }

    fig = genera_accettazioni_per_scenario(business_metrics)

    if fig is None:
        return {"data": "{}"}

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.3)',
        font=dict(color='#C7D5E6')
    )
    fig.update_xaxes(tickfont=dict(color='#C7D5E6'))
    fig.update_yaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')

    return {"data": fig.to_json()}


@app.post("/api/charts/compliance", tags=["charts"])
async def get_trend_compliance(request: AdvisorRequest) -> dict:
    """Generate Compliance Trend Chart (ADAPT vs FISSO over rounds) as Plotly JSON"""
    from visualizzatore_grafici import genera_trend_compliance

    metrics = request.metrics_data or {}
    scenario_id = metrics.get("scenario_corrente", "S0")

    # Fetch rounds data from MongoDB
    rounds_data = []
    try:
        db_scenario_key = f"{scenario_id}_200"
        sim_doc = collection.find_one({"scenario_id": db_scenario_key})

        if not sim_doc:
            sim_doc = collection.find_one(
                {"scenario_id": {"$regex": f"^{scenario_id}"}},
                sort=[("num_rounds", -1), ("_id", -1)]
            )

        if sim_doc and "rounds" in sim_doc:
            rounds_data = sim_doc["rounds"]
    except Exception as e:
        print(f"[Compliance Chart] Error fetching rounds: {e}")

    fig = genera_trend_compliance(rounds_data, scenario_id)

    if fig is None:
        return {"data": "{}"}

    # Dark mode styling
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.3)',
        font=dict(color='#C7D5E6')
    )
    fig.update_xaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')
    fig.update_yaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')

    return {"data": fig.to_json()}


@app.post("/api/charts/interesse-composto", tags=["charts"])
async def get_interesse_composto(request: AdvisorRequest) -> dict:
    """Generate Compound Interest Educational Chart as Plotly JSON"""
    from visualizzatore_grafici import genera_interesse_composto

    fig = genera_interesse_composto()

    # Dark mode styling
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,41,59,0.3)',
        font=dict(color='#C7D5E6')
    )
    fig.update_xaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')
    fig.update_yaxes(tickfont=dict(color='#C7D5E6'), gridcolor='rgba(199, 213, 230, 0.1)')

    return {"data": fig.to_json()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
@app.post("/api/charts/client-sentiment")
async def get_client_sentiment(payload: dict):
    from visualizzatore_grafici import genera_spider_sentiment_cluster
    try:
        metrics = payload.get("metrics_data", payload)
        scenario_ui = metrics.get("scenario_corrente", "S0")

        dizionario_scenari = {
            "Base": "S0", "Espansione": "S1",
            "Rialzo tassi": "S2", "Stress": "S3", "Recessione": "S4"
        }
        scenario_codice = dizionario_scenari.get(scenario_ui, scenario_ui)
        # Se scenario_ui è già un codice (S0, S1...) usalo direttamente
        if scenario_ui.startswith("S") and len(scenario_ui) <= 3:
            scenario_codice = scenario_ui
        db_scenario_id = f"{scenario_codice}_200" if not scenario_codice.endswith("_200") else scenario_codice

        print(f"[Spider] Cercando scenario: {db_scenario_id}")
        documento = collection.find_one({"scenario_id": db_scenario_id})

        if not documento:
            print(f"[Spider] Documento non trovato per {db_scenario_id}")
            fig = go.Figure()
            fig.add_annotation(text=f"Scenario '{db_scenario_id}' non trovato nel DB", x=0.5, y=0.5, showarrow=False, font=dict(color="white", size=12))
            fig.update_layout(paper_bgcolor='rgba(30,41,59,0.5)', plot_bgcolor='rgba(30,41,59,0.5)')
            return Response(content=fig.to_json(), media_type="application/json")

        rounds_data = documento.get("rounds", [])
        business_metrics = documento.get("business_metrics", {})

        business_metrics.update({
            "tasso_conversione_adapt_pct": metrics.get("tasso_conversione_adapt_pct", 46),
            "tasso_conversione_fisso_pct": metrics.get("tasso_conversione_fisso_pct", 92),
            "fiducia_media_adapt_pct": metrics.get("fiducia_media_adapt", 29),
            "fiducia_media_fisso_pct": metrics.get("fiducia_media_fisso", 55),
        })

        print(f"[Spider] business_metrics keys: {list(business_metrics.keys())}")
        print(f"[Spider] fiducia_adapt={business_metrics.get('fiducia_media_adapt_pct')}, conv_adapt={business_metrics.get('tasso_conversione_adapt_pct')}")

        fig = genera_spider_sentiment_cluster(rounds_data, business_metrics)
        return Response(content=fig.to_json(), media_type="application/json")

    except Exception as e:
        print(f"[Spider] Errore: {str(e)}")
        fig = go.Figure()
        fig.add_annotation(text=f"Errore: {str(e)}", x=0.5, y=0.5, showarrow=False, font=dict(color="red", size=11))
        fig.update_layout(paper_bgcolor='rgba(30,41,59,0.5)', plot_bgcolor='rgba(30,41,59,0.5)')
        return Response(content=fig.to_json(), media_type="application/json")
    
@app.get("/api/dati-banca-direttiva")
def get_dati_banca_direttiva(scenario_id: str = "S0"):
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})
    if not doc or "rounds" not in doc:
        return {"direttiva": [], "scostamenti": []}
        
    rounds = sorted(doc["rounds"], key=lambda x: x.get("round", 0))
    
    fisso_totale = defaultdict(int)
    fisso_count = 0
    adapt_totale = defaultdict(int)
    adapt_count = 0
    
    scostamenti_per_round = []
    
    for r in rounds:
        round_fisso = defaultdict(int)
        round_adapt = defaultdict(int)
        round_fisso_count = 0
        round_adapt_count = 0
        
        for promo in r.get("promoters_data", []):
            pid = promo.get("promotore_id", "")
            for s in promo.get("strategies", []):
                prod = s.get("prodotto_suggerito", "Altro")
                if "FISSO" in pid:
                    fisso_totale[prod] += 1
                    fisso_count += 1
                    round_fisso[prod] += 1
                    round_fisso_count += 1
                elif "ADAPT" in pid:
                    adapt_totale[prod] += 1
                    adapt_count += 1
                    round_adapt[prod] + 1
                    round_adapt_count += 1
                    
        if round_fisso_count > 0 and round_adapt_count > 0:
            scostamento_round = 0
            for prod in set(list(round_fisso.keys()) + list(round_adapt.keys())):
                pct_fisso = round_fisso.get(prod, 0) / round_fisso_count
                pct_adapt = round_adapt.get(prod, 0) / round_adapt_count
                scostamento_round += abs(pct_adapt - pct_fisso)
            scostamenti_per_round.append({
                "round": r.get("round"),
                "scostamento": round(scostamento_round * 100, 1)
            })
            
    direttiva = []
    tutti_prodotti = set(list(fisso_totale.keys()) + list(adapt_totale.keys()))
    for prod in tutti_prodotti:
        pct_fisso = round(fisso_totale.get(prod, 0) / fisso_count * 100, 1) if fisso_count > 0 else 0
        pct_adapt = round(adapt_totale.get(prod, 0) / adapt_count * 100, 1) if adapt_count > 0 else 0
        delta =round(pct_adapt - pct_fisso, 1)
        direttiva.append({
            "prodotto": prod.replace("_", " "),
            "pct_fisso": pct_fisso,
            "pct_adapt": pct_adapt,
            "delta": delta
        })
        
    direttiva.sort(key=lambda x: abs(x["delta"]), reverse=True)
    
    return {
        "direttiva": direttiva,
        "scostamenti": scostamenti_per_round
    }
    
@app.get("/api/dati-banca-flusso-clienti")
def get_dati_banca_flusso_clienti(scenario_id: str = "S0"):
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})
    if not doc or "rounds" not in doc:
        return {"attratti": 0, "arrabbiati": 0, "trend": []}

    rounds = sorted(doc["rounds"], key=lambda x: x.get("round", 0))

    attratti_totale = 0
    arrabbiati_totale = 0
    trend = []

    for r in rounds:
        attratti_round = 0
        arrabbiati_round = 0

        for promo in r.get("promoters_data", []):
            for s in promo.get("strategies", []):
                delta = s.get("delta_fiducia_medio", 0)
                clienti = s.get("clients_in_cluster", 0)
                if delta > 0:
                    attratti_round += clienti
                elif delta < -0.05:
                    arrabbiati_round += clienti

        attratti_totale += attratti_round
        arrabbiati_totale += arrabbiati_round
        trend.append({
            "round": r.get("round"),
            "attratti": attratti_round,
            "arrabbiati": arrabbiati_round
        })

    return {
        "attratti": attratti_totale,
        "arrabbiati": arrabbiati_totale,
        "trend": trend
    }
    
@app.get("/api/dati-banca-spider")
def get_dati_banca_spider(scenario_id: str = "S0"):
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})
    if not doc or "rounds" not in doc:
        return {"adapt": [0,0,0,0,0], "target": [100,100,100,100,100]}

    rounds = sorted(doc["rounds"], key=lambda x: x.get("round", 0))

    # Accumulatori
    adapt_adeguatezza, adapt_conversione, adapt_fiducia = [], [], []
    adapt_commissioni = []
    fisso_prodotti = defaultdict(int)
    adapt_prodotti = defaultdict(int)
    fisso_count = adapt_count = 0

    TICKET_MEDIO = 100000
    COMMISSIONE = 0.01

    for r in rounds:
        for promo in r.get("promoters_data", []):
            pid = promo.get("promotore_id", "")
            for s in promo.get("strategies", []):
                adeq = s.get("adeguatezza_score", 0)
                acc = s.get("accettato", False)
                fid = s.get("fiducia_media_post", 0)
                clienti = s.get("clients_in_cluster", 0)
                prod = s.get("prodotto_suggerito", "Altro")

                if "ADAPT" in pid:
                    adapt_adeguatezza.append(adeq)
                    adapt_conversione.append(1 if acc else 0)
                    adapt_fiducia.append(fid)
                    adapt_commissioni.append((clienti * TICKET_MEDIO * COMMISSIONE) if acc else 0)
                    adapt_prodotti[prod] += 1
                    adapt_count += 1
                elif "FISSO" in pid:
                    fisso_prodotti[prod] += 1
                    fisso_count += 1

    # 1. Compliance (adeguatezza media 0-100)
    compliance = round(sum(adapt_adeguatezza) / len(adapt_adeguatezza) * 100, 1) if adapt_adeguatezza else 0

    # 2. Raccolta (tasso conversione 0-100)
    raccolta = round(sum(adapt_conversione) / len(adapt_conversione) * 100, 1) if adapt_conversione else 0

    # 3. Fiducia cliente (media 0-100)
    fiducia = round(sum(adapt_fiducia) / len(adapt_fiducia) * 100, 1) if adapt_fiducia else 0

    # 4. Aderenza direttiva (100 - scostamento medio dalla distribuzione FISSO)
    scostamento = 0
    if fisso_count > 0 and adapt_count > 0:
        tutti = set(list(fisso_prodotti.keys()) + list(adapt_prodotti.keys()))
        for prod in tutti:
            pct_f = fisso_prodotti.get(prod, 0) / fisso_count
            pct_a = adapt_prodotti.get(prod, 0) / adapt_count
            scostamento += abs(pct_a - pct_f)
    aderenza = round(max(0, 100 - scostamento * 100), 1)

    # 5. Redditività (commissioni normalizzate 0-100 rispetto al max teorico)
    comm_totale = sum(adapt_commissioni)
    comm_max_teorico = adapt_count * TICKET_MEDIO * COMMISSIONE if adapt_count > 0 else 1
    redditivita = round(min(100, comm_totale / comm_max_teorico * 100), 1) if comm_max_teorico > 0 else 0

    return {
        "adapt": [compliance, raccolta, fiducia, aderenza, redditivita],
        "target": [90, 80, 75, 70, 85],
        "labels": ["Compliance", "Raccolta", "Fiducia Cliente", "Aderenza Direttiva", "Redditività"]
    }


@app.get("/api/charts/radar-banca-direttiva")
def get_radar_banca_direttiva(scenario_id: str = "S0"):
    """
    Radar Banca: Allocation Target vs Actual Portfolio
    Dimensioni: Bond Corp, Monetario, Azionario, Illiquidi, Gov Bond
    """
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})

    if not doc or "rounds" not in doc:
        return {
            "target": [80, 90, 20, 10, 85],
            "attuale": [0, 0, 0, 0, 0]
        }

    # Mapping prodotto -> allocation weights
    prodotti_map = {
        "Bond_Corporate": {"bond": 80, "monetario": 20, "azionario": 10, "illiquidi": 5, "gov": 70},
        "Monetario": {"bond": 20, "monetario": 90, "azionario": 5, "illiquidi": 0, "gov": 30},
        "Azionario": {"bond": 10, "monetario": 10, "azionario": 80, "illiquidi": 20, "gov": 20},
        "ETF": {"bond": 30, "monetario": 20, "azionario": 60, "illiquidi": 10, "gov": 40},
        "Obbligazionario": {"bond": 70, "monetario": 30, "azionario": 15, "illiquidi": 5, "gov": 80},
    }

    bond_tot = mon_tot = az_tot = ill_tot = gov_tot = count = 0

    # Usa l'ultimo round per il portafoglio attuale (ADAPT only)
    rounds_sorted = sorted(doc.get("rounds", []), key=lambda x: x.get("round", 0))
    if rounds_sorted:
        ultimo_round = rounds_sorted[-1]
        for promo in ultimo_round.get("promoters_data", []):
            if "ADAPT" not in promo.get("promotore_id", ""):
                continue
            for s in promo.get("strategies", []):
                prod = s.get("prodotto_suggerito", "Bond_Corporate")
                pesi = prodotti_map.get(prod, prodotti_map["Bond_Corporate"])
                bond_tot += pesi["bond"]
                mon_tot += pesi["monetario"]
                az_tot += pesi["azionario"]
                ill_tot += pesi["illiquidi"]
                gov_tot += pesi["gov"]
                count += 1

    if count == 0:
        return {
            "target": [80, 90, 20, 10, 85],
            "attuale": [0, 0, 0, 0, 0]
        }

    return {
        "target": [80, 90, 20, 10, 85],
        "attuale": [
            round(bond_tot / count, 1),
            round(mon_tot / count, 1),
            round(az_tot / count, 1),
            round(ill_tot / count, 1),
            round(gov_tot / count, 1)
        ]
    }

# =====================================================================
# FINSIM-MOD: ENDPOINT MANCANTI PER VISTA CLIENTE (Data-Driven)
# =====================================================================

@app.get("/api/charts/fiducia-evolution")
def get_fiducia_evolution(scenario_id: str = "S0"):
    """
    Evoluzione della fiducia cliente medio per round (200 round).
    Distingue ADAPT vs FISSO con trend smoothing.
    """
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})

    if not doc or "rounds" not in doc:
        return {
            "labels": [f"R{i}" for i in range(1, 201)],
            "fiducia_adapt": [50] * 200,
            "fiducia_fisso": [45] * 200
        }

    fiducia_adapt = []
    fiducia_fisso = []
    labels = []

    for r in sorted(doc["rounds"], key=lambda x: x.get('round', 0)):
        round_num = r.get('round', 0)
        labels.append(f"R{round_num}")

        adapt_sum = adapt_count = fisso_sum = fisso_count = 0

        for promo in r.get("promoters_data", []):
            pid = promo.get("promotore_id", "")
            for strat in promo.get("strategies", []):
                fid = strat.get("fiducia_media_post", 0)

                if "ADAPT" in pid:
                    adapt_sum += fid
                    adapt_count += 1
                elif "FISSO" in pid:
                    fisso_sum += fid
                    fisso_count += 1

        fiducia_adapt.append((adapt_sum / adapt_count * 100) if adapt_count > 0 else 0)
        fiducia_fisso.append((fisso_sum / fisso_count * 100) if fisso_count > 0 else 0)

    return {
        "labels": labels,
        "fiducia_adapt": fiducia_adapt,
        "fiducia_fisso": fiducia_fisso
    }


@app.get("/api/charts/profilo-portafoglio")
def get_profilo_portafoglio(scenario_id: str = "S0"):
    """
    Radar: Allineamento Profilo Dichiarato vs Portafoglio Assegnato.
    Dimensioni: Rischio, Orizzonte Temporale, Liquidità, Rendimento Atteso, Conoscenza Finanziaria.
    """
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})

    # Fallback se nessun dato
    if not doc or "rounds" not in doc:
        return {
            "profilo_dichiarato": [35, 60, 70, 45, 50],
            "portafoglio_assegnato": [40, 58, 75, 48, 50],
            "labels": ["Rischio", "Orizzonte", "Liquidità", "Rendimento", "Conoscenza"]
        }

    rounds = sorted(doc["rounds"], key=lambda x: x.get('round', 0))

    # Accumulatori per ogni dimensione
    profilo_risk = profilo_time = profilo_liquidity = profilo_return = profilo_knowledge = 0
    portfolio_risk = portfolio_time = portfolio_liquidity = portfolio_return = portfolio_knowledge = 0
    conteggio = 0

    for r in rounds:
        for promo in r.get("promoters_data", []):
            if "ADAPT" not in promo.get("promotore_id", ""):
                continue
            for strat in promo.get("strategies", []):
                profilo = strat.get("profilo_rischio_prevalente", "Balanced")
                adeq = strat.get("adeguatezza_score", 0.5)

                # Mappa profilo rischio dichiarato
                risk_map = {"Conservative": 20, "Balanced": 50, "Aggressive": 80}
                profilo_risk += risk_map.get(profilo, 50)

                # Portfolio risk (basato su adeguatezza - se bassa, risk diverso)
                portfolio_risk += (adeq * 80)

                # Altre dimensioni (stimate da adeguatezza e fiducia)
                fid = strat.get("fiducia_media_post", 0.5)
                delta = strat.get("delta_fiducia_medio", 0)

                profilo_time += 60  # Time horizon conservativo
                portfolio_time += (fid * 100)  # Allineato a fiducia

                profilo_liquidity += 70  # Liquidità desiderata
                portfolio_liquidity += (80 if adeq > 0.6 else 60)

                profilo_return += 50  # Return expectations
                portfolio_return += (adeq * 100)  # Actual return potential

                profilo_knowledge += 55  # Assumed knowledge
                portfolio_knowledge += (delta * 100 + 50)  # Knowledge reflected in adjustments

                conteggio += 1

    if conteggio == 0:
        return {
            "profilo_dichiarato": [35, 60, 70, 45, 50],
            "portafoglio_assegnato": [40, 58, 75, 48, 50],
            "labels": ["Rischio", "Orizzonte", "Liquidità", "Rendimento", "Conoscenza"]
        }

    profilo = [
        round(profilo_risk / conteggio),
        round(profilo_time / conteggio),
        round(profilo_liquidity / conteggio),
        round(profilo_return / conteggio),
        round(profilo_knowledge / conteggio)
    ]

    portfolio = [
        round(portfolio_risk / conteggio),
        round(portfolio_time / conteggio),
        round(portfolio_liquidity / conteggio),
        round(portfolio_return / conteggio),
        round(portfolio_knowledge / conteggio)
    ]

    # Normalizza a 0-100
    profilo = [max(0, min(100, p)) for p in profilo]
    portfolio = [max(0, min(100, p)) for p in portfolio]

    return {
        "profilo_dichiarato": profilo,
        "portafoglio_assegnato": portfolio,
        "labels": ["Rischio", "Orizzonte", "Liquidità", "Rendimento", "Conoscenza"]
    }


@app.get("/api/charts/risk-propensity-heatmap")
def get_risk_propensity_heatmap(scenario_id: str = "S0"):
    """
    Heatmap Propensione al Rischio per Cluster (Profilo Rischio × Patrimonio).
    Valori: tasso di accettazione di prodotti a rischio per cluster.
    """
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})

    # Fallback
    if not doc or "rounds" not in doc:
        return {
            "matrice": [[88, 82, 75, 70, 65], [91, 85, 79, 73, 68], [78, 72, 66, 58, 48], [62, 54, 44, 32, 22]],
            "profili": ["Alto Rischio", "Medio Rischio", "Basso Rischio", "Conservativo"],
            "patrimoni": ["Basso", "Medio-Basso", "Medio", "Medio-Alto", "Alto"]
        }

    # Clusters: 4 profili di rischio × 5 livelli di patrimonio
    risk_profiles = ["Alto Rischio", "Medio Rischio", "Basso Rischio", "Conservativo"]
    wealth_levels = ["Basso", "Medio-Basso", "Medio", "Medio-Alto", "Alto"]

    risk_to_idx = {
        "Aggressive": 0,
        "Balanced": 1,
        "Conservative": 2,
        "Conservativo": 3
    }

    # Matrice di conteggio per cluster
    cluster_acceptance = [[0]*5 for _ in range(4)]
    cluster_total = [[0]*5 for _ in range(4)]

    rounds = sorted(doc["rounds"], key=lambda x: x.get('round', 0))

    for r in rounds:
        for promo in r.get("promoters_data", []):
            for strat in promo.get("strategies", []):
                risk_profilo = strat.get("profilo_rischio_prevalente", "Balanced")
                coords = strat.get("cluster_coords", [2, 2])
                clienti = strat.get("clients_in_cluster", 1)
                accettato = strat.get("accettato", False)

                # Map risk profile to index (0-3)
                risk_idx = risk_to_idx.get(risk_profilo, 1)

                # Map coordinates to wealth level (0-4, assume 0-10 scale)
                wealth_idx = min(4, int((coords[0] / 10.0) * 5)) if coords else 2

                cluster_total[risk_idx][wealth_idx] += clienti
                if accettato:
                    cluster_acceptance[risk_idx][wealth_idx] += clienti

    # Calcola tasso di accettazione per cluster (0-100%)
    matrice_propensione = []
    for i in range(4):
        riga = []
        for j in range(5):
            if cluster_total[i][j] > 0:
                tasso = int((cluster_acceptance[i][j] / cluster_total[i][j]) * 100)
            else:
                tasso = 50  # Default se nessun dato
            riga.append(max(20, min(100, tasso)))  # Clamp tra 20-100
        matrice_propensione.append(riga)

    return {
        "matrice": matrice_propensione,
        "profili": risk_profiles,
        "patrimoni": wealth_levels
    }


@app.get("/api/cluster-evolution", tags=["dashboard"])
async def get_cluster_evolution(scenario_id: str = "S0", risk_idx: int = 0, wealth_idx: int = 0):
    """
    Extract evolution of a specific cluster across simulation rounds and analyze strategy transitions.
    Shows how the single promoter managing that cluster evolves their approach over time.

    Args:
        scenario_id: Scenario identifier (S0-S4)
        risk_idx: Risk profile index (0-3)
        wealth_idx: Wealth profile index (0-4)

    Returns:
        Dictionary with rounds evolution, cluster label, promoter type, transitions, and LLM analysis
    """
    db_scenario_id = get_scenario_code(scenario_id)
    doc = collection.find_one({"scenario_id": db_scenario_id})
    if not doc or "rounds" not in doc:
        return {"rounds": [], "cluster_label": "", "promotore_tipo": "", "transizioni": [], "analisi_llm": ""}

    rounds = sorted(doc["rounds"], key=lambda x: x.get("round", 0))
    target_coords = [risk_idx, wealth_idx]

    eventi = []
    tipo_promotore_cluster = None

    for r in rounds:
        round_num = r.get("round", 0)
        for promo in r.get("promoters_data", []):
            pid = promo.get("promotore_id", "")
            for s in promo.get("strategies", []):
                if s.get("cluster_coords") == target_coords:
                    tipo = "Consulenza Adattiva" if "ADAPT" in pid else "Strategia Standard"
                    tipo_promotore_cluster = tipo
                    eventi.append({
                        "round": round_num,
                        "tipo_promotore": tipo,
                        "llm_strategy": s.get("llm_strategy", ""),
                        "approccio_comunicativo": s.get("approccio_comunicativo", ""),
                        "prodotto_suggerito": s.get("prodotto_suggerito", "").replace("_", " "),
                        "adeguatezza_score": s.get("adeguatezza_score", 0),
                        "delta_fiducia_medio": s.get("delta_fiducia_medio", 0),
                        "fiducia_media_pre": s.get("fiducia_media_pre", 0),
                        "fiducia_media_post": s.get("fiducia_media_post", 0),
                        "accettato": s.get("accettato", False)
                    })

    if not eventi:
        return {"rounds": [], "cluster_label": "", "promotore_tipo": "", "transizioni": [], "analisi_llm": ""}

    # Classifica TUTTI gli eventi ADAPT in batch per evitare sovraccarico
    eventi_adapt = [e for e in eventi if e["tipo_promotore"] == "Consulenza Adattiva"]

    BATCH_SIZE = 25
    categorie_valide = {"Aggressiva", "Conservativa", "Informativa", "Relazionale"}

    for batch_start in range(0, len(eventi_adapt), BATCH_SIZE):
        batch = eventi_adapt[batch_start:batch_start + BATCH_SIZE]
        if not batch:
            continue

        strategie_testo = "\n".join([
            f"{i+1}. {e['llm_strategy']}"
            for i, e in enumerate(batch)
        ])

        prompt_classificazione = f"""Classifica ciascuna delle seguenti strategie di consulenza finanziaria in UNA di queste 4 categorie: "Aggressiva" (spinge su prodotti a rischio/rendimento alto), "Conservativa" (privilegia sicurezza, liquidità, protezione capitale), "Informativa" (focus su trasparenza, educazione, dati), "Relazionale" (focus su fiducia, rassicurazione, ascolto).

Strategie da classificare (numerate da 1 a {len(batch)}):
{strategie_testo}

Rispondi SOLO con un array JSON di {len(batch)} stringhe, una per ogni strategia numerata in ordine. Esempio per 3 strategie: ["Aggressiva", "Conservativa", "Informativa"]"""

        try:
            payload_llm = {
                "model": OllamaAdvisor.MODEL_NAME,
                "prompt": prompt_classificazione,
                "stream": False,
                "format": "json"
            }
            r = requests.post(OllamaAdvisor.OLLAMA_GENERATE_URL, json=payload_llm, timeout=90)
            if r.ok:
                result = r.json()
                raw_response = json.loads(result.get("response", "[]"))

                if isinstance(raw_response, list):
                    categorie = raw_response
                elif isinstance(raw_response, dict):
                    categorie = None
                    for key, value in raw_response.items():
                        if isinstance(value, list):
                            categorie = value
                            break
                    if categorie is None:
                        valori = list(raw_response.values())
                        if valori and all(isinstance(v, str) for v in valori):
                            categorie = valori
                        else:
                            categorie = []
                else:
                    categorie = []

                for i, cat in enumerate(categorie):
                    if i < len(batch) and isinstance(cat, str) and cat in categorie_valide:
                        batch[i]["categoria_approccio"] = cat
        except Exception as e:
            print(f"[Cluster Evolution] Errore classificazione batch {batch_start}: {e}")

    for e in eventi:
        if "categoria_approccio" not in e:
            e["categoria_approccio"] = "Non classificato"

    # Identifica le transizioni di categoria (dove cambia rispetto al round precedente)
    transizioni = []
    for i in range(1, len(eventi)):
        if eventi[i]["categoria_approccio"] != eventi[i-1]["categoria_approccio"]:
            transizioni.append({
                "round": eventi[i]["round"],
                "da": eventi[i-1]["categoria_approccio"],
                "a": eventi[i]["categoria_approccio"],
                "fiducia_pre_transizione": round(eventi[i-1]["fiducia_media_post"] * 100, 0),
                "adeguatezza_pre_transizione": round(eventi[i-1]["adeguatezza_score"] * 100, 0)
            })

    # Genera analisi LLM del perché cambia la strategia
    analisi_llm = ""
    if transizioni:
        transizioni_testo = "\n".join([
            f"- Al round {t['round']}, la strategia passa da '{t['da']}' a '{t['a']}' (fiducia cliente prima del cambio: {t['fiducia_pre_transizione']:.0f}%, adeguatezza: {t['adeguatezza_pre_transizione']:.0f}%)"
            for t in transizioni[:8]
        ])
        prompt_analisi = f"""Sei un consulente finanziario senior. Analizza questi cambiamenti di stile di approccio di un promotore verso un segmento di clientela nel corso della simulazione:

{transizioni_testo}

Scrivi un'analisi di massimo 4 frasi in italiano professionale che spieghi il pattern osservato: perché il promotore potrebbe aver cambiato approccio in questi momenti, collegando il cambio di strategia ai livelli di fiducia e adeguatezza osservati. Non usare termini tecnici come MiFID, churn, KPI, S0. Scrivi in modo che un direttore commerciale di banca capisca immediatamente."""

        try:
            payload_analisi = {
                "model": OllamaAdvisor.MODEL_NAME,
                "prompt": prompt_analisi,
                "stream": False
            }
            r2 = requests.post(OllamaAdvisor.OLLAMA_GENERATE_URL, json=payload_analisi, timeout=60)
            if r2.ok:
                analisi_llm = r2.json().get("response", "").strip()
        except Exception:
            analisi_llm = "Analisi non disponibile al momento."
    else:
        analisi_llm = "Il promotore ha mantenuto uno stile di approccio costante per tutto il periodo analizzato, senza variazioni significative di strategia."

    profili_rischio = ["Alto Rischio", "Medio Rischio", "Basso Rischio", "Conservativo"]
    profili_patrimonio = ["Basso Patrimonio", "Medio-Basso", "Medio", "Medio-Alto", "Alto Patrimonio"]
    cluster_label = f"{profili_rischio[risk_idx]} · {profili_patrimonio[wealth_idx]}"

    return {
        "rounds": eventi,
        "cluster_label": cluster_label,
        "promotore_tipo": tipo_promotore_cluster,
        "transizioni": transizioni,
        "analisi_llm": analisi_llm
    }