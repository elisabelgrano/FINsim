import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Palette elegante e morbida (Light Mode Premium)
COLORI_DIVERGENTI = ["#e11d48", "#f59e0b", "#059669"]

def applica_stile_premium(fig, titolo: str):
    """Applica un tema Light Mode enterprise ad alto contrasto e nitidezza"""
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
        margin=dict(l=60, r=30, t=70, b=60),
        showlegend=True
    )
    
    # Forziamo la nitidezza su tutti gli assi cartesiani presenti nel grafico
    fig.update_xaxes(
        title_font=dict(size=14, color="#111827", weight="bold"),
        tickfont=dict(size=12, color="#374151")
    )
    fig.update_yaxes(
        title_font=dict(size=14, color="#111827", weight="bold"),
        tickfont=dict(size=12, color="#374151")
    )
    
    return fig

def genera_heatmap_performance(business_metrics: dict):
    """Genera la heatmap di performance incrociata Rischio vs Patrimonio"""
    rischi = ["Rischio Basso", "Rischio Medio", "Rischio Alto"]
    patrimoni = ["Patrimonio Basso", "Patrimonio Medio", "Patrimonio Alto"]
    
    # Recupera i dati reali o usa un fallback se la simulazione non ha estratto la matrice
    dati_matrice = business_metrics.get("matrice_performance", [
        [1.5, -0.4, 2.1],
        [-0.8, 0.0, 1.2],
        [0.5, -1.1, -0.2]
    ])
    
    grid_df = pd.DataFrame(dati_matrice, index=rischi, columns=patrimoni)
    
    fig = px.imshow(
        grid_df,
        labels=dict(color="Vantaggio Netto"),
        color_continuous_scale=COLORI_DIVERGENTI,
        aspect="auto"
    )
    
    fig.update_traces(xgap=4, ygap=4)
    
    val_min = grid_df.values.min() if not grid_df.isna().all().all() else -1
    val_max = grid_df.values.max() if not grid_df.isna().all().all() else 1
    
    fig.update_coloraxes(
        showscale=True, 
        colorbar=dict(
            thickness=15, 
            title="<b>Performance</b>",
            tickvals=[val_min, 0, val_max],
            ticktext=["Vince Fisso (Rosso)", "Pareggio", "Vince Adattivo (Verde)"],
            tickfont=dict(size=11, color="#111827")
        )
    )
    
    # Creiamo la matrice di testi personalizzati per il pop-up del mouse
    testo_hover = []
    for riga in grid_df.values:
        valori_riga = []
        for val in riga:
            if pd.isna(val):
                valori_riga.append("Dati non disponibili")
            elif val > 0:
                valori_riga.append(f"🟢 Vince ADATTIVO (+{val:.2f} pts)")
            elif val < 0:
                valori_riga.append(f"🔴 Vince FISSO ({val:.2f} pts)")
            else:
                valori_riga.append("🟡 Pareggio perfetto")
        testo_hover.append(valori_riga)

    fig.update_traces(
        customdata=testo_hover,
        hovertemplate="<b>Livello Rischio (Y):</b> %{y}<br>" +
                      "<b>Patrimonio (X):</b> %{x}<br>" +
                      "<b>Verdetto:</b> %{customdata}<extra></extra>"
    )
    
    fig.update_xaxes(title_text="<b>Patrimonio del Cliente</b>", side="bottom")
    fig.update_yaxes(title_text="<b>Livello di Rischio</b>")
    
    return applica_stile_premium(fig, "Mappa del Vantaggio Strategico (Adattivo vs Fisso)")

def genera_bar_prodotti(business_metrics: dict):
    """Legge l'efficacia prodotti direttamente dai dati puliti di MongoDB"""
    prodotti_puliti = business_metrics.get("efficacia_strategica_prodotti", {})
    
    if not prodotti_puliti:
        return go.Figure()
    
    # Estraiamo direttamente i dati perché le chiavi sono normalizzate
    nomi_finali = list(prodotti_puliti.keys())
    valori_soddisfazione = [prodotti_puliti[k].get("soddisfazione_generata", 0.0) for k in nomi_finali]
    testi_utilizzi = [f"Utilizzato {prodotti_puliti[k].get('utilizzi',0)} volte" for k in nomi_finali]
    
    df = pd.DataFrame({
        "Asset Class": [n.replace("_", " ") for n in nomi_finali],
        "Soddisfazione": valori_soddisfazione,
        "Info": testi_utilizzi
    })
    
    fig = px.bar(
        df, x="Asset Class", y="Soddisfazione",
        color="Soddisfazione", text="Info",
        color_continuous_scale=["#e11d48", "#059669"]
    )
    fig.update_traces(textposition="outside")
    
    if valori_soddisfazione:
        fig.update_coloraxes(
            showscale=True,
            colorbar=dict(
                thickness=15, title="<b>Soddisfazione</b>",
                tickvals=[min(valori_soddisfazione), 0, max(valori_soddisfazione)],
                ticktext=["Bassa", "Media", "Alta"], tickfont=dict(size=11, color="#111827")
            )
        )
    
    fig.update_xaxes(title_text="<b>Asset Class (Normalizzate)</b>")
    fig.update_yaxes(title_text="<b>Impatto Soddisfazione Totale</b>")
    
    return applica_stile_premium(fig, "Efficacia Strategica dei Prodotti sui Clienti")

def genera_linee_comparative(business_metrics: dict):
    """Mostra l'andamento temporale del vantaggio cumulato nei 20 round"""
    storico_ia = business_metrics.get("storico_raccolta_adattivo", [i**1.2 * 10000 for i in range(1, 21)])
    storico_fisso = business_metrics.get("storico_raccolta_fisso", [i * 9000 for i in range(1, 21)])
    rounds = [f"R{i}" for i in range(1, 21)]
    
    df_ia = pd.DataFrame({"Round": rounds, "Valore": storico_ia, "Modello": "Adattivo (IA)"})
    df_fisso = pd.DataFrame({"Round": rounds, "Valore": storico_fisso, "Modello": "Fisso (Regole)"})
    df = pd.concat([df_ia, df_fisso])
    
    fig = px.line(
        df, x="Round", y="Valore", color="Modello",
        color_discrete_map={"Adattivo (IA)": "#059669", "Fisso (Regole)": "#e11d48"}
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
        )
    )
    
    return applica_stile_premium(fig, "Evoluzione Performance Cumulata nei 20 Round")

def genera_waterfall_patrimonio(business_metrics: dict):
    """Mostra la scomposizione dei fattori che hanno determinato il patrimonio finale"""
    aum_iniziale = business_metrics.get("aum_iniziale", 100_000_000)
    nuova_raccolta = business_metrics.get("nuova_raccolta_netta", 15_500_000)
    effetto_mercato = business_metrics.get("effetto_mercato", -3_200_000)
    churn_clienti = business_metrics.get("patrimonio_perso_churn", -5_800_000)
    aum_finale = aum_iniziale + nuova_raccolta + effetto_mercato + churn_clienti

    fig = go.Figure(go.Waterfall(
        name="AUM", orientation="v",
        measure=["relative", "relative", "relative", "relative", "total"],
        x=["AUM Iniziale", "Nuova Raccolta", "Effetto Mercato", "Churn", "AUM Finale"],
        textposition="outside",
        text=[f"+{nuova_raccolta/1e6:.1f}M", f"{effetto_mercato/1e6:.1f}M", f"{churn_clienti/1e6:.1f}M", f"{aum_finale/1e6:.1f}M"],
        y=[aum_iniziale, nuova_raccolta, effetto_mercato, churn_clienti, 0],
        connector={"line": {"color": "rgba(0,0,0,0.1)", "width": 1}},
        decreasing={"marker": {"color": "#e11d48"}},
        increasing={"marker": {"color": "#059669"}},
        totals={"marker": {"color": "#1f2937"}}
    ))
    
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=12, color="#059669", symbol="square"), name='Nuova Raccolta (Positivo)'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=12, color="#e11d48", symbol="square"), name='Uscite / Churn (Negativo)'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=12, color="#1f2937", symbol="square"), name='Totale Patrimonio'))
    
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            title_text=""
        )
    )
    
    return applica_stile_premium(fig, "Analisi di Contribuzione del Patrimonio (AUM)")

def genera_sankey_flussi(business_metrics: dict):
    """Sankey dinamico basato sui clienti reali salvati o persi"""
    # Usiamo i dati reali dal backend (con fallback di sicurezza)
    clienti_salvati = business_metrics.get("clienti_salvati_dal_churn", 0)
    
    # Stimiamo il volume totale sui round per dare proporzione al flusso
    variazioni = business_metrics.get("velocita_variazione_soddisfazione", [])
    round_totali = len(variazioni) if variazioni else 20
    clienti_stimati_inizio = 100 * round_totali # (es. 100 clienti per round)
    
    # Calcoliamo i flussi
    gestiti_fisso = int(clienti_stimati_inizio / 2)
    gestiti_adattivo = int(clienti_stimati_inizio / 2)
    
    # Assumiamo un churn base del 10% per il Fisso, mentre l'Adattivo ne salva una parte
    churn_fisso = int(gestiti_fisso * 0.10)
    churn_adattivo = int(gestiti_adattivo * 0.10) - clienti_salvati
    if churn_adattivo < 0: churn_adattivo = 0
    
    successo_fisso = gestiti_fisso - churn_fisso
    successo_adattivo = gestiti_adattivo - churn_adattivo

    label = ["Clienti Iniziali", "Modello Fisso", "Modello Adattivo (IA)", "Fidelizzati (Successo)", "Persi (Churn)"]
    source = [0, 0, 1, 1, 2, 2]
    target = [1, 2, 3, 4, 3, 4]
    value  = [gestiti_fisso, gestiti_adattivo, successo_fisso, churn_fisso, successo_adattivo, churn_adattivo]
    
    colori_link = [
        "rgba(245, 158, 11, 0.3)", # Da Inizio a Fisso
        "rgba(5, 150, 105, 0.3)",  # Da Inizio ad Adattivo
        "rgba(59, 130, 246, 0.4)", # Da Fisso a Successo
        "rgba(225, 29, 72, 0.4)",  # Da Fisso a Churn
        "rgba(59, 130, 246, 0.4)", # Da Adattivo a Successo
        "rgba(225, 29, 72, 0.4)"   # Da Adattivo a Churn
    ]

    fig = go.Figure(data=[go.Sankey(
        textfont=dict(size=13, color="#111827"),
        node=dict(
            pad=20, thickness=25, line=dict(color="#111827", width=1),
            label=[f"<b>{l}</b>" for l in label],
            color=["#3b82f6", "#f59e0b", "#10b981", "#3b82f6", "#e11d48"]
        ),
        link=dict(source=source, target=target, value=value, color=colori_link)
    )])
    
    fig = applica_stile_premium(fig, "Flusso di Fidelizzazione e Churn")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig
    
def genera_andamento_guadagni(business_metrics: dict):
    """Grafico ad area che mappa il delta di fiducia cumulativo"""
    variazioni = business_metrics.get("velocita_variazione_soddisfazione", [])
    
    if not variazioni:
        return go.Figure()

    rounds = [f"R{item.get('round')}" for item in variazioni]
    # Creiamo un dato cumulativo (somma progressiva) per mostrare l'area di crescita
    valori_netti = [item.get("variazione_netta", 0.0) for item in variazioni]
    valori_cumulativi = []
    somma_corrente = 0
    for v in valori_netti:
        somma_corrente += v
        valori_cumulativi.append(somma_corrente)
        
    df = pd.DataFrame({"Round": rounds, "Valore Cumulativo (AUM Proxy)": valori_cumulativi})
    
    fig = px.area(
        df, x="Round", y="Valore Cumulativo (AUM Proxy)", 
        color_discrete_sequence=["#059669"]
    )
    
    # Gradiente sotto l'area per renderlo "premium"
    fig.update_traces(fillcolor='rgba(5, 150, 105, 0.2)', line=dict(width=3))
    
    fig.update_xaxes(title_text="<b>Progressione Temporale</b>")
    fig.update_yaxes(title_text="<b>Crescita Cumulativa Netta</b>")
    
    return applica_stile_premium(fig, "Impatto Cumulativo Generato dall'IA")

def estrai_playbook_strategico(rounds_data):
    """
    Analizza i round dell'agente Adattivo per scoprire le 'Best Practice' per ogni tipologia di cliente basandosi sui nuovi snapshot di fiducia.
    """
    storico_cluster = {}
    
    # Raccolta delta di fiducia per prodotto e per cluster
    for r in rounds_data:
        for dec in r.get("decisions", []):
            # analizziamo solo le scelte dell'adattivo
            if dec.get("promotore_id") != "PROM-ADAPT-1":
                continue
            
            riga = dec.get("cluster_riga")
            col = dec.get("cluster_col")
            prodotto = dec.get("prodotto_suggerito", "Altro")
            delta = dec.get("delta_fiducia_medio_snapshot", 0.0)
            
            chiave_cluster = (riga, col)
            
            if chiave_cluster not in storico_cluster:
                storico_cluster[chiave_cluster] = {}
            if prodotto not in storico_cluster[chiave_cluster]:
                storico_cluster[chiave_cluster][prodotto] = []
                
            storico_cluster[chiave_cluster][prodotto].append(delta)
            
    # troviamo il prodotto vincitore per ogni cluster
    best_practices = {}
    for cluster, prodotti, in storico_cluster.items():
        miglior_prodotto = "Nessuno"
        miglior_media = -999.0
        compioni = 0
        
        for prod, deltas in prodotti.items():
            if not deltas: continue
            media = sum(deltas) / len(deltas)
            if media > miglior_media:
                miglior_media = miglior_media
                miglior_prodotto = prod
                campioni = len(deltas)
                
        best_practices[cluster] = {
            "prodotto_top": miglior_prodotto.replace("_", " "),
            "crescita_attesa": miglior_media,
            "casi_studio": campioni
        }
        
    return best_practices    