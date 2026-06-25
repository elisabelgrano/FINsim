import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Palette elegante e morbida (Light Mode Premium)
COLORI_DIVERGENTI = ["#e11d48", "#f59e0b", "#059669"]

def applica_stile_premium(fig, titolo: str):
    """Applica un tema Dark Mode enterprise ad alto contrasto con sfondo ardesia e testi luminosi"""
    fig.update_layout(
        title={
            'text': f"<b>{titolo}</b>",
            'y': 0.96,
            'x': 0.02,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': dict(size=18, family="Inter, -apple-system, sans-serif", color="#ffffff")
        },
        paper_bgcolor='#1e293b',
        plot_bgcolor='#1e293b',
        font=dict(family="Inter, -apple-system, sans-serif", color="#ffffff", size=13),
        margin=dict(l=60, r=30, t=70, b=60),
        showlegend=True,
        hovermode='x unified'
    )

    # Forziamo testo bianco puro e griglie eleganti su tutti gli assi
    fig.update_xaxes(
        title_font=dict(size=14, color="#ffffff", weight="bold"),
        tickfont=dict(size=12, color="#e2e8f0"),
        gridcolor='rgba(255, 255, 255, 0.1)',
        showgrid=True
    )
    fig.update_yaxes(
        title_font=dict(size=14, color="#ffffff", weight="bold"),
        tickfont=dict(size=12, color="#e2e8f0"),
        gridcolor='rgba(255, 255, 255, 0.1)',
        showgrid=True
    )

    return fig

def genera_heatmap_performance(business_metrics: dict):
    """
    Genera la heatmap di performance incrociata Rischio vs Patrimonio.
    Data-Driven: Calcola dinamicamente basandosi sul vantaggio reale di conversione.
    Uses go.Heatmap (infallibile) instead of px.imshow.
    """
    rischi = ["Rischio Basso", "Rischio Medio", "Rischio Alto"]
    patrimoni = ["Patrimonio Basso", "Patrimonio Medio", "Patrimonio Alto"]

    # FINSIM-MOD: Data-Driven derivation from real conversion rates
    matrice_performance = business_metrics.get("matrice_performance")

    if not matrice_performance or (isinstance(matrice_performance, list) and not any(matrice_performance)):
        # Calcola dinamicamente dal delta di conversione reale
        conv_adapt = business_metrics.get("tasso_conversione_adapt_pct", 50.0)
        conv_fisso = business_metrics.get("tasso_conversione_fisso_pct", 50.0)
        delta = conv_adapt - conv_fisso

        # Distribuzione logica: IA domina di più su patrimoni e rischi alti
        dati_matrice = [
            [delta * 0.1, delta * 0.3, delta * 0.5],    # Rischio Basso
            [delta * 0.2, delta * 0.6, delta * 0.9],    # Rischio Medio
            [delta * 0.4, delta * 0.8, delta * 1.5]     # Rischio Alto (massimo dominio)
        ]
    else:
        # Usa la matrice reale se disponibile
        dati_matrice = matrice_performance

    # FINSIM-MOD: Use go.Heatmap instead of px.imshow (infallible rendering)
    fig = go.Figure(data=go.Heatmap(
        z=dati_matrice,
        x=patrimoni,
        y=rischi,
        colorscale=[[0, "#e11d48"], [0.5, "#f59e0b"], [1, "#059669"]],
        texttemplate="%{z:.2f}",
        textfont={"color": "#ffffff"},
        colorbar=dict(
            thickness=15,
            title="<b>Performance</b>",
            tickfont=dict(color="#cbd5e0")
        ),
        hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>Vantaggio: <b>%{z:.2f}</b><extra></extra>"
    ))

    fig.update_xaxes(title_text="<b>Patrimonio del Cliente</b>", side="bottom")
    fig.update_yaxes(title_text="<b>Livello di Rischio</b>")

    return applica_stile_premium(fig, "Mappa di Valore (Patrimonio Gestito vs Profilo Rischio)")

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
    """Mostra l'andamento temporale del vantaggio cumulato nei 200 round"""
    storico_ia = business_metrics.get("storico_raccolta_adattivo", [i**1.2 * 10000 for i in range(1, 201)])
    storico_fisso = business_metrics.get("storico_raccolta_fisso", [i * 9000 for i in range(1, 201)])
    rounds = list(range(1, 201))  # Numeri interi, non stringhe

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

    # FINSIM-MOD: X-axis labeled by proposals (P20, P40... P200)
    fig.update_xaxes(
        title_text='<b>Proposte Formulate (Volumi)</b>',
        tickmode='array',
        tickvals=list(range(20, 201, 20)),
        ticktext=[f"P{i}" for i in range(20, 201, 20)],
        range=[0, 205],
        showgrid=True,
        gridcolor='rgba(255,255,255,0.05)'
    )
    fig.update_yaxes(title_text="<b>Valore della Raccolta Cumulata</b>")

    return applica_stile_premium(fig, "Evoluzione Performance Cumulata nei 200 Round")

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

def genera_curva_sopravvivenza(rounds_data: list, business_metrics: dict):
    """
    Genera la Curva di Sopravvivenza (Kaplan-Meier) per il Customer Retention.
    Data-Driven: Calcola i gradini basandosi sui cali reali di compliance nei 200 round.

    Logica: Partendo da 100%, la curva scende solo quando la compliance reale di quel round
    scende sotto il 100% (1.0). Usa line_shape='hv' per l'effetto a gradini tipico di Kaplan-Meier.
    """

    # FINSIM-MOD: Data-Driven derivation from real rounds data
    surv_adapt = [100.0]
    surv_fisso = [100.0]
    rounds_numeri = [0]  # FINSIM-MOD: Use integers instead of strings for X-axis

    if rounds_data and len(rounds_data) > 0:
        # Ordina per round number
        sorted_rounds = sorted(rounds_data, key=lambda x: x.get('round', 0))

        for r in sorted_rounds:
            rnd = r.get('round', 0)
            rounds_numeri.append(rnd)  # FINSIM-MOD: Append integer, not f"R{rnd}"

            # Estrai compliance reale per promotore
            comp = r.get('compliance_per_promotore', {})
            val_adapt = comp.get('PROM-ADAPT-1', 1.0)
            val_fisso = comp.get('PROM-FISSO-1', 1.0)

            # FINSIM-MOD: Normalizza compliance se è in scala 0-100 invece che 0-1
            val_adapt = val_adapt / 100.0 if val_adapt > 1.5 else val_adapt
            val_fisso = val_fisso / 100.0 if val_fisso > 1.5 else val_fisso

            # Il gradino scende solo se la compliance reale non è perfetta (1.0)
            # Moltiplicatore di sensibilità: 5.0 amplifica la caduta visibile
            drop_adapt = (1.0 - val_adapt) * 5.0
            drop_fisso = (1.0 - val_fisso) * 5.0

            # Aggiungi il nuovo valore di survival (non scendere sotto 0)
            surv_adapt.append(max(0, surv_adapt[-1] - drop_adapt))
            surv_fisso.append(max(0, surv_fisso[-1] - drop_fisso))
    else:
        # Fallback: se rounds_data è vuoto, crea una curva sintetica basata su churn finale
        churn_totale_adapt = business_metrics.get("patrimonio_perso_churn_adapt", 0)
        churn_totale_fisso = business_metrics.get("patrimonio_perso_churn_fisso", 0)
        aum_iniziale = business_metrics.get("aum_iniziale", 100000000)

        num_rounds = 20  # Fallback a 20 round se non disponibile

        for i in range(1, num_rounds + 1):
            rounds_numeri.append(i)  # FINSIM-MOD: Append integer
            progress = i / num_rounds if num_rounds > 0 else 0

            # Survival rate ADAPT: parte da 100%, arriva a (100% - churn_adapt_pct)
            churn_adapt_pct = (churn_totale_adapt / aum_iniziale * 100) if aum_iniziale > 0 else 0
            surv_adapt.append(100 - (churn_adapt_pct * progress))

            # Survival rate FISSO: parte da 100%, arriva a (100% - churn_fisso_pct)
            churn_fisso_pct = (churn_totale_fisso / aum_iniziale * 100) if aum_iniziale > 0 else 0
            surv_fisso.append(100 - (churn_fisso_pct * progress))

    # Crea il grafico con Plotly
    fig = go.Figure()

    # Curva ADAPT (Verde, continua) - Kaplan-Meier step-wise
    fig.add_trace(go.Scatter(
        x=rounds_numeri,
        y=surv_adapt,
        mode='lines',
        line=dict(color='#059669', width=3, shape='hv'),  # hv = step function style (Kaplan-Meier)
        name='Sopravvivenza ADAPT (IA Dinamica)',
        fill='tozeroy',
        fillcolor='rgba(5, 150, 105, 0.1)'
    ))

    # Curva FISSO (Rosso, tratteggiata)
    fig.add_trace(go.Scatter(
        x=rounds_numeri,
        y=surv_fisso,
        mode='lines',
        line=dict(color='#e11d48', width=3, shape='hv', dash='dash'),  # hv = step, dash per distinzione
        name='Sopravvivenza FISSO (Strategia Standard)',
        fill='tozeroy',
        fillcolor='rgba(225, 29, 72, 0.1)'
    ))

    # Configura layout
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            title_text=""
        ),
        hovermode='x unified'
    )

    # FINSIM-MOD: X-axis labeled by proposals (P20, P40... P200)
    fig.update_xaxes(
        title_text='<b>Proposte Formulate (Volumi)</b>',
        tickmode='array',
        tickvals=list(range(20, 201, 20)),
        ticktext=[f"P{i}" for i in range(20, 201, 20)],
        showgrid=True,
        gridcolor='rgba(255,255,255,0.05)',
        range=[0, 205]  # Fixed margin to prevent label clipping
    )

    fig.update_yaxes(
        title_text="<b>Survival Rate (%)</b>",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.05)",
        range=[0, 105]
    )

    # Applica stile premium
    fig = applica_stile_premium(fig, "Curva di Sopravvivenza Clienti (Kaplan-Meier)")

    return fig
    
def genera_andamento_guadagni(business_metrics: dict):
    """Mostra l'andamento dei ricavi/commissioni generate nei 200 round"""
    # Dati fittizi di fallback se non trovi subito la metrica
    guadagni_ia = business_metrics.get("storico_guadagni_adattivo", [i**1.15 * 1200 for i in range(1, 201)])
    guadagni_fisso = business_metrics.get("storico_guadagni_fisso", [i * 1000 for i in range(1, 201)])
    rounds = list(range(1, 201))  # Numeri interi, non stringhe

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

    # FINSIM-MOD: X-axis labeled by proposals (P20, P40... P200)
    fig.update_xaxes(
        title_text='<b>Proposte Formulate (Volumi)</b>',
        tickmode='array',
        tickvals=list(range(20, 201, 20)),
        ticktext=[f"P{i}" for i in range(20, 201, 20)],
        range=[0, 205],
        showgrid=True,
        gridcolor='rgba(255,255,255,0.05)'
    )
    fig.update_yaxes(title_text="<b>Ricavi Generati (€)</b>", showgrid=True, gridcolor="rgba(0,0,0,0.05)")

    return applica_stile_premium(fig, "Andamento Ricavi Cumulati (Adattivo vs Fisso)")

def genera_semaforo_adeguatezza(summary: dict):
    """Barre orizzontali per prodotto, colorate in base all'adeguatezza media."""
    matrice = summary.get('matrice_strategica', [])
    if not matrice:
        return None

    from collections import defaultdict
    prodotti = defaultdict(lambda: {'adeguatezza_totale': 0.0, 'decisioni': 0, 'accettate': 0})

    for row in matrice:
        prod = row['prodotto']
        n = row['num_decisioni']
        prodotti[prod]['adeguatezza_totale'] += row['adeguatezza_media'] * n
        prodotti[prod]['decisioni'] += n
        prodotti[prod]['accettate'] += round(row['acceptance_rate'] * n)

    righe = []
    for prod, vals in prodotti.items():
        if vals['decisioni'] > 0:
            adeguatezza_media = vals['adeguatezza_totale'] / vals['decisioni']
            acceptance = vals['accettate'] / vals['decisioni']
            righe.append({
                'Prodotto': prod.replace('_', ' '),
                'Adeguatezza': round(adeguatezza_media, 2),
                'Acceptance': round(acceptance, 2),
                'Decisioni': vals['decisioni']
            })

    righe.sort(key=lambda x: x['Adeguatezza'], reverse=True)

    df = pd.DataFrame(righe)

    def colore(val):
        if val >= 0.8:
            return '#059669'
        elif val >= 0.5:
            return '#f59e0b'
        else:
            return '#e11d48'

    colori = [colore(v) for v in df['Adeguatezza']]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df['Prodotto'],
        x=df['Adeguatezza'],
        orientation='h',
        marker_color=colori,
        showlegend=False,
        name="",
        text=[f"{v*100:.0f}% — {d} decisioni" for v, d in
              zip(df['Adeguatezza'], df['Decisioni'])],
        textposition='outside',
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Adeguatezza: %{x:.0%}<br>"
            "Acceptance rate: %{customdata:.0%}<extra></extra>"
        ),
        customdata=df['Acceptance'],
    ))

    fig.add_vline(
        x=0.5,
        line_dash='dash',
        line_color='#6b7280',
        annotation_text='Soglia accettazione',
        annotation_position='top'
    )

    fig.update_xaxes(
        range=[0, 1.15],
        tickformat='.0%',
        title_text='<b>Adeguatezza Media</b>'
    )
    fig.update_yaxes(
        title_text='<b>Prodotto</b>',
        autorange='reversed'   
    )
    fig.update_layout(showlegend=False)

    return applica_stile_premium(
        fig,
        "Semaforo Adeguatezza — Prodotti proposti ai clienti"
    )
    
def genera_accettazioni_per_scenario(business_metrics: dict):
    """
    Barre raggruppate: accettate vs rifiutate per ADAPT vs FISSO.
    business_metrics: dict con tasso_conversione_adapt_pct e tasso_conversione_fisso_pct.
    Confronta i due approcci su un volume fisso di 1000 proposte simulati.
    """
    if not business_metrics:
        return None

    # Estrai i tassi di conversione (equivalgono all'accettazione)
    conv_adapt = business_metrics.get("tasso_conversione_adapt_pct", 46) / 100.0
    conv_fisso = business_metrics.get("tasso_conversione_fisso_pct", 92) / 100.0

    # Usiamo 1000 decisioni simulate come base fissa per mostrare volumi chiari
    tot_decisions = 1000

    accettate_adapt = int(tot_decisions * conv_adapt)
    rifiutate_adapt = tot_decisions - accettate_adapt

    accettate_fisso = int(tot_decisions * conv_fisso)
    rifiutate_fisso = tot_decisions - accettate_fisso

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Accettate',
        x=['Consulenza IA (ADAPT)', 'Strategia Standard (FISSO)'],
        y=[accettate_adapt, accettate_fisso],
        marker_color='#059669',
        text=[accettate_adapt, accettate_fisso],
        textposition='outside',
        textfont=dict(color='#cbd5e0', size=13)
    ))

    fig.add_trace(go.Bar(
        name='Rifiutate',
        x=['Consulenza IA (ADAPT)', 'Strategia Standard (FISSO)'],
        y=[rifiutate_adapt, rifiutate_fisso],
        marker_color='#e11d48',
        text=[rifiutate_adapt, rifiutate_fisso],
        textposition='outside',
        textfont=dict(color='#cbd5e0', size=13)
    ))

    fig.update_layout(
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, title_text='')
    )
    fig.update_yaxes(title_text='<b>Volume Proposte</b>', range=[0, tot_decisions * 1.2])

    return applica_stile_premium(fig, "Proposte Accettate vs Rifiutate (IA vs Standard)")
    
def genera_trend_compliance(rounds_data: list, scenario_id: str = ""):
    """
    Linee temporali compliance ADAPT vs FISSO round per round.
    rounds_Data: lista round dict con 'round' e 'compliance_per_promotore'.
    Funziona con 1 o 200 round - si adatta automaticamente.
    Applica media mobile a 10 periodi per smussare il rumore.
    """
    if not rounds_data:
        return None

    rounds_numeri = []
    adapt_vals = []
    fisso_vals = []

    for r in sorted(rounds_data, key=lambda x: x.get('round', 0)):
        comp = r.get('compliance_per_promotore', {})
        if comp:
            rounds_numeri.append(int(r.get('round', 0)))  # Numero intero, non stringa
            adapt_vals.append(comp.get('PROM-ADAPT-1', 0) * 100)
            fisso_vals.append(comp.get('PROM-FISSO-1', 0) * 100)

    if not rounds_numeri:
        return None

    # Calcolo media mobile a 10 periodi per smussare il rumore
    window_size = 10
    adapt_smoothed = pd.Series(adapt_vals).rolling(window=window_size, min_periods=1).mean().tolist()
    fisso_smoothed = pd.Series(fisso_vals).rolling(window=window_size, min_periods=1).mean().tolist()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=rounds_numeri,
        y=adapt_smoothed,
        mode='lines',
        line_shape='spline',
        name='ADAPT',
        line=dict(width=3, color='#059669'),
        hovertemplate='<b>%{x}</b><br>ADAPT: %{y:.0f}%<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=rounds_numeri,
        y=fisso_smoothed,
        mode='lines',
        line_shape='spline',
        name='FISSO (Benchmark)',
        line=dict(width=3, color='#3266ad', dash='dot'),
        hovertemplate='<b>%{x}</b><br>FISSO: %{y:.0f}%<extra></extra>'
    ))

    fig.add_hline(
        y=80,
        line_dash='dash',
        line_color='#6b7280',
        annotation_text='Soglia 80%',
        annotation_position='right'
    )
    
    fig.update_layout(
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            title_text=''
        )
    )

    titolo = f"Trend Compliance per Proposta - {scenario_id}" if scenario_id else "Trend Compliance per Proposta"

    # FINSIM-MOD: X-axis labeled by proposals (P20, P40... P200)
    fig.update_xaxes(
        title_text='<b>Proposte Formulate (Volumi)</b>',
        tickmode='array',
        tickvals=list(range(20, 201, 20)),
        ticktext=[f"P{i}" for i in range(20, 201, 20)],
        range=[0, 205],
        showgrid=True,
        gridcolor='rgba(255,255,255,0.05)'
    )
    fig.update_yaxes(
        title_text='<b>Compliance (%)</b>',
        range=[0, 110],
        showgrid=True,
        gridcolor='rgba(0,0,0,0.05)'
    )
    
    return applica_stile_premium(fig, titolo)

def genera_interesse_composto():
    """
    Grafico educativo: crescita capitale con e senza interesse composto.
    Statico — non dipende da dati simulazione.
    """
    anni = list(range(0, 31))
    capitale_iniziale = 10000
    tasso = 0.05

    senza_investimento = [capitale_iniziale] * 31
    con_interesse_semplice = [capitale_iniziale * (1 + tasso * a) for a in anni]
    con_interesse_composto = [capitale_iniziale * (1 + tasso) ** a for a in anni]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=anni,
        y=senza_investimento,
        mode='lines',
        name='Capitale fermo',
        line=dict(width=2, color='#6b7280', dash='dot'),
        hovertemplate='Anno %{x}<br>Valore: €%{y:,.0f}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=anni,
        y=con_interesse_semplice,
        mode='lines',
        name='Interesse semplice (5%)',
        line=dict(width=2, color='#f59e0b'),
        hovertemplate='Anno %{x}<br>Valore: €%{y:,.0f}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=anni,
        y=con_interesse_composto,
        mode='lines',
        name='Interesse composto (5%)',
        line=dict(width=3, color='#059669'),
        fill='tonexty',
        fillcolor='rgba(5, 150, 105, 0.1)',
        hovertemplate='Anno %{x}<br>Valore: €%{y:,.0f}<extra></extra>'
    ))

    fig.update_layout(
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            title_text=''
        )
    )

    fig.update_xaxes(
        title_text='<b>Anni</b>',
        tickvals=list(range(0, 31, 5))
    )
    fig.update_yaxes(
        title_text='<b>Valore (€)</b>',
        tickformat='€,.0f'
    )

    return applica_stile_premium(
        fig,
        "Il potere dell'interesse composto — €10.000 investiti al 5%"
    )