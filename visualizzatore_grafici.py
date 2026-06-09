import plotly.express as px
import pandas as pd

# Palette elegante e morbida per contesti finanziari (Evitiamo l'effetto semaforo acceso)
COLORI_DIVERGENTI = ["#e11d48", "#f59e0b", "#059669"] # Rosso morbido, Ambra, Smeraldo desaturato

def applica_stile_premium(fig, titolo: str):
    """Applica un tema minimalista, pulito e leggibile specifico per il Light Mode"""
    fig.update_layout(
        title={
            'text': f"<b>{titolo}</b>",
            'y': 0.95,
            'x': 0.02,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': dict(size=16, family="Segoe UI, San Francisco, Arial, sans-serif", color="#1f2937") # Grigio scuro visibile!
        },
        paper_bgcolor='rgba(0,0,0,0)',  # Sfondo trasparente per integrarsi con Streamlit
        plot_bgcolor='rgba(0,0,0,0)',   # Area del grafico trasparente
        font=dict(family="Segoe UI, San Francisco, Arial, sans-serif", color="#4b5563"),
        margin=dict(l=50, r=20, t=60, b=50),
        showlegend=False
    )
    return fig


def genera_heatmap_performance(business_metrics: dict):
    """Genera una Heatmap proporzionata, senza etichette duplicate nelle assi"""
    mappa_data = business_metrics.get("stato_finale_mappa_cluster", [])
    
    if not mappa_data:
        mappa_data = [
            {"riga": r, "colonna": c, "vantaggio_netto_ia": (r * c) / 5 - 0.5}
            for r in range(4) for c in range(5)
        ]

    # Sanificazione radicale delle label per evitare "Rischio Lvl Rischio Lvl"
    dati_puliti = []
    for d in mappa_data:
        riga_raw = str(d.get("riga", ""))
        col_raw = str(d.get("colonna", ""))
        
        # Estraiamo solo il numero finale (es. se è "Rischio Lvl 3" o solo "3", prendiamo l'ultimo elemento)
        num_riga = riga_raw.split()[-1] if " " in riga_raw else riga_raw
        num_col = col_raw.split()[-1] if " " in col_raw else col_raw
        
        dati_puliti.append({
            "Rischio": f"Lvl {num_riga}",
            "Patrimonio": f"Lvl {num_col}",
            "Vantaggio IA": d.get("vantaggio_netto_ia", 0)
        })

    df = pd.DataFrame(dati_puliti)
    grid_df = df.pivot(index="Rischio", columns="Patrimonio", values="Vantaggio IA")
    
    # Invertiamo l'asse Y per mostrare il livello 0 in alto in modo naturale
    grid_df = grid_df.iloc[::-1]

    fig = px.imshow(
        grid_df,
        labels=dict(color="Vantaggio"),
        color_continuous_scale=COLORI_DIVERGENTI,
        aspect="auto"
    )
    
    fig.update_traces(xgap=4, ygap=4)
    fig.update_coloraxes(showscale=True, colorbar=dict(thickness=12, title=None))
    fig.update_xaxes(showgrid=False, side="bottom", tickfont=dict(size=11, color="#4b5563"))
    fig.update_yaxes(showgrid=False, tickfont=dict(size=11, color="#4b5563"))
    
    return applica_stile_premium(fig, "Mappa del Vantaggio Strategico (Adattivo vs Fisso)")


def genera_bar_prodotti(business_metrics: dict):
    """Genera un grafico a barre snello, con griglie soft e leggibile"""
    prodotti_data = business_metrics.get("performance_prodotti", business_metrics.get("soddisfazione_prodotti", {}))
    
    if not prodotti_data:
        prodotti_data = {
            "Bond Corporate": 0.550,
            "Fondi Misti": -0.065
        }
        
    df = pd.DataFrame({
        "Prodotto": list(prodotti_data.keys()),
        "Soddisfazione": list(prodotti_data.values())
    }).sort_values(by="Soddisfazione", ascending=False)
    
    fig = px.bar(
        df,
        x="Prodotto",
        y="Soddisfazione",
        color="Soddisfazione",
        color_continuous_scale=COLORI_DIVERGENTI,
        text_auto=".3f"
    )
    
    fig.update_traces(
        marker_line_width=0,
        textposition="outside",
        cliponaxis=False,
        width=0.4 # Rende le barre più snelle ed eleganti, meno cicciotte
    )
    
    # Aggiungiamo linee di griglia leggerissime sullo sfondo per dare profondità
    fig.update_yaxes(
        showgrid=True, 
        gridcolor="rgba(0, 0, 0, 0.05)", 
        zeroline=True, 
        zerolinecolor="rgba(0, 0, 0, 0.2)",
        tickfont=dict(size=11, color="#4b5563")
    )
    fig.update_xaxes(tickfont=dict(size=11, color="#4b5563"), title=None)
    fig.update_coloraxes(showscale=False)
    
    return applica_stile_premium(fig, "Soddisfazione per Tipologia di Prodotto")