import pymongo
import requests

# 1. Configurazione (RICORDATI DI METTERE LA TUA PASSWORD)
MONGO_URI = "mongodb://elisa:deepleey@10.12.7.53:27017/"
API_URL = "http://10.12.7.53:8000/api/advisor/chat"

print("🔄 Connessione a MongoDB in corso...")
client = pymongo.MongoClient(MONGO_URI)

# 🟢 CAMBIATO QUI: puntiamo al database reale!
db = client["finsim_analytics"] 
collection = db["simulation_history"]

print(f"🔎 Cerco l'ultimissimo scenario nella collezione '{collection.name}'...")
ultimo_scenario = collection.find_one({}, sort=[("_id", pymongo.DESCENDING)])

if not ultimo_scenario:
    print(f"❌ La collezione '{collection.name}' sembra vuota o inesistente.")
    print(f"📁 Le collezioni reali presenti in 'finsim_analytics' sono: {db.list_collection_names()}")
    exit()
else:
    print("\n✅ Trovato un documento!")
    print(f"👉 Scenario ID: {ultimo_scenario.get('scenario_id', 'Nessun ID trovato')}")
    
    # Identifichiamo la chiave delle metriche
    if "business_metrics" in ultimo_scenario:
        print("📊 Chiave trovata: 'business_metrics'")
        metrics_vere = ultimo_scenario["business_metrics"]
    elif "metrics" in ultimo_scenario:
        print("📊 Chiave trovata: 'metrics'")
        metrics_vere = ultimo_scenario["metrics"]
    else:
        print(f"\n❌ Non trovo le metriche. Chiavi disponibili: {list(ultimo_scenario.keys())}")
        exit()

    # 3. Chiamata API all'IA
    domanda = "Guardando i dati reali, qual è stata la mossa vincente per i clienti con patrimonio alto?"
    payload = {"metrics_data": metrics_vere, "user_message": domanda}
    
    print(f"\n🤖 Invio la domanda all'API...")
    try:
        risposta = requests.post(API_URL, json=payload, timeout=130)
        risposta.raise_for_status()
        dati_ai = risposta.json()
        
        print("\n" + "="*50)
        print("🎯 RISPOSTA DELL'IA:")
        print(f"👉 SUGGERIMENTO: {dati_ai.get('suggerimento_breve')}")
        print(f"📝 DETTAGLIO: {dati_ai.get('dettaglio_risposta')}")
        print(f"📊 GRAFICI SUGGERITI: {dati_ai.get('grafici_consigliati')}")
        print("="*50 + "\n")
    except Exception as e:
        print(f"❌ Errore durante la chiamata API: {e}")