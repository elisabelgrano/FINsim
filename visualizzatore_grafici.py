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
    """Genera il grafico a barre della soddisfazione prodotti"""
    prodotti = ["Fondi Azionari", "Obbligazioni", "ETF Tematici", "Polizze", "Liquidità"]
    soddisfazione = business_metrics.get("soddisfazione_prodotti", [78, 62, 85, 54, 90])
    
    df = pd.DataFrame({"Prodotto": prodotti, "Soddisfazione": soddisfazione})
    
    fig = px.bar(
        df, x="Prodotto", y="Soddisfazione",
        color="Soddisfazione",
        color_continuous_scale=["#e11d48", "#059669"]
    )
    
    fig.update_coloraxes(
        showscale=True,
        colorbar=dict(
            thickness=15,
            title="<b>Soddisfazione</b>",
            tickvals=[0, 50, 100],
            ticktext=["Critica (Rosso)", "Media", "Alta (Verde)"],
            tickfont=dict(size=11, color="#111827")
        ))
    fig.update_xaxes(title_text="<b>Prodotti Finanziari</b>")
    fig.update_yaxes(title_text="<b>Livello di Soddisfazione (%)</b>", range=[0, 100])
    
    return applica_stile_premium(fig, "Soddisfazione Clienti per Tipologia Prodotto")

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
    """Mostra il flusso dinamico dei clienti dai Cluster iniziali allo stato finale o Churn"""
    label = ["Cluster Basso Rischio", "Cluster Medio Rischio", "Cluster Alto Rischio", "Stabili", "Upgrade Profilo", "CHURN (Persi)"]
    source = [0, 0, 0,  1, 1, 1,  2, 2, 2]
    target = [3, 4, 5,  3, 4, 5,  3, 4, 5]
    value  = [120, 30, 5, 200, 80, 15, 90, 10, 45]
    colori_link = ["rgba(5, 150, 105, 0.2)", "rgba(245, 158, 11, 0.2)", "rgba(225, 29, 72, 0.2)"] * 3

    fig = go.Figure(data=[go.Sankey(
        textfont=dict(size=13, color="#111827"), # <-- CORREZIONE: spostato fuori e rinominato in textfont!
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="#111827", width=1),
            label=[f"<b>{l}</b>" for l in label],
            color=["#3b82f6", "#f59e0b", "#ec4899", "#059669", "#10b981", "#e11d48"]
            # <-- rimosso 'font' da qui
        ),
        link=dict(source=source, target=target, value=value, color=colori_link)
    )])
    
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=12, color="#3b82f6", symbol="square"), name='Basso Rischio'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=12, color="#f59e0b", symbol="square"), name='Medio Rischio'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=12, color="#ec4899", symbol="square"), name='Alto Rischio'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=12, color="#e11d48", symbol="square"), name='Persi (CHURN)'))
    
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            title_text=""
        )
    )
    
    fig = applica_stile_premium(fig, "Mappa di Migrazione dei Clienti e Tasso di Churn")
    
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    
    return fig
    
def genera_andamento_guadagni(business_metrics: dict):
    """Mostra l'andamento dei ricavi/commissioni generate nei 20 round"""
    # Dati fittizi di fallback se non trovi subito la metrica
    guadagni_ia = business_metrics.get("storico_guadagni_adattivo", [i**1.15 * 1200 for i in range(1, 21)])
    guadagni_fisso = business_metrics.get("storico_guadagni_fisso", [i * 1000 for i in range(1, 21)])
    rounds = [f"R{i}" for i in range(1, 21)]
    
    fig = go.Figure()
    
    # Area Promotore Fisso (Rosso)
    fig.add_trace(go.Scatter(
        x=rounds, y=guadagni_fisso, mode='lines',
        line=dict(width=3, color="#e11d48"),
        fill='tozeroy', fillcolor="rgba(225, 29, 72, 0.1)",
        name="Fisso (Regole)"
    ))
    
    # Area Promotore Adattivo (Verde)
    fig.add_trace(go.Scatter(
        x=rounds, y=guadagni_ia, mode='lines',
        line=dict(width=3, color="#059669"),
        fill='tozeroy', fillcolor="rgba(5, 150, 105, 0.1)",
        name="Adattivo (IA)"
    ))
    
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text="")
    )
    
    fig.update_xaxes(title_text="<b>Round Temporali</b>", showgrid=False)
    fig.update_yaxes(title_text="<b>Ricavi Generati (€)</b>", showgrid=True, gridcolor="rgba(0,0,0,0.05)")
    
    return applica_stile_premium(fig, "Andamento Ricavi (Adattivo vs Fisso)")
    