from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Permrette al frontend Vue di leggere i dati da Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint a cui Vue chiederà i dati
@app.get("/api/dati-banca")
def get_dati_banca():
    # poi metteremo logica visualizzatore_grafici.py per lettura DB. Per ora mandiamo gli stessi dati che abbiamo in Vue??????
    return{
        "prodotti": [
            {"name": "Fondo Monetario Euro", "cluster": "Conservativi (Lvl 1)", "volume": "5.2", "adequacy": 95, "status": "green"},
            {"name": "BTP 5Y - Nuova Emissione", "cluster": "Conservativi (Lvl 1-2)", "volume": "8.4", "adequacy": 88, "status": "green"},
            {"name": "ETF Azionario Globale", "cluster": "Dinamici (Lvl 4-5)", "volume": "3.1", "adequacy": 62, "status": "amber"}
        ]
    }
