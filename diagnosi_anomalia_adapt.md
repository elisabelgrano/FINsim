DIAGNOSI: Anomalia FINsim - PROM-ADAPT-1 Underperformance
Sommario Esecutivo
PROM-ADAPT-1 (promotore adattativo AI-driven) underperforma sistematicamente PROM-FISSO-1 (benchmark) non per insufficienza dell'algoritmo, ma per un difetto strutturale di design del modello di simulazione.

Tre cause radice, ordinate per severità:

Segregazione Cliente-Promotore (CRITICO): FISSO e ADAPT gestiscono cluster completamente diversi, quindi non è A/B test vero
ADEGUATEZZA_MATRIX Statica (SERIO): Matrice di lookup (profilo, prodotto) → score non incentiva personalizzazione nel tempo
clienti_salvati_dal_churn Impossibile per Design (GRAVE): La metrica è strutturalmente impossibile da incrementare
1. TRACCIA CAUSALE: LLM → Metriche Finali
Step 1: Decisione LLM (promotore_agent.genera_strategia_cluster, riga 48)
FISSO: Riceve prompt che gli chiede di scegliere prodotti conservativi
ADAPT: Riceve prompt generico che lo guida su scenario/direttiva/clienti
Output: prodotto_suggerito (stringa raw, es. "Bond Corporate Investment Grade")
# promotore_agent.py, riga 168-186
result['prodotto_suggerito'] = strategy_json.get('prodotto_suggerito', '')
Step 2: Normalizzazione (normalizzatore.normalize_prodotto, riga 9)
Converte raw → categoria standard (Bond_Corporate, Fondi_Azionari, ecc.)
Lookup case-insensitive con substring matching
Se non matcha: ritorna "Altro"
# normalizzatore.py, riga 44-99
if ("corporate" in normalized) and any(x in normalized for x in ["bond", "obbligaz"]):
    return "Bond_Corporate"
# ... altri pattern ...
return "Altro"
Step 3: Calcolo Adeguatezza (simulation_engine.esegui_round, riga 287)
Lookup puro: ADEGUATEZZA_MATRIX[profilo_rischio_prevalente][prodotto_normalized] → score [0.0-1.0]
Matrice è hardcoded e statica (riga 25-74 simulation_engine.py)
Profilo determinato dal Cliente (cluster_riga % 4):
Riga 0: Conservative
Riga 1: Balanced
Riga 2: Growth
Riga 3: Aggressive
# simulation_engine.py, riga 287-292
adeguatezza_score = round(
    ADEGUATEZZA_MATRIX.get(profilo_rischio_prevalente, {})
                       .get(prodotto_normalized, 0.0),
    2
)
accettato = adeguatezza_score >= SOGLIA_ACCETTAZIONE  # 0.5
Step 4: Reazione Clienti (calcola_reazione_clienti, riga 521)
Delta_fiducia è determinato UNICAMENTE da adeguatezza_score
Non dipende da storia, personalizzazione, o qualità della scelta
Valori fissi per fascia di adeguatezza:
adeguatezza_score	delta_fiducia
>= 0.8	+0.05
0.5 - 0.79	+0.02
0.3 - 0.49	-0.01
< 0.3	-0.04
# simulation_engine.py, riga 522-529
if adeguatezza_score >= 0.8:
    delta_fiducia_base = 0.05
elif adeguatezza_score >= 0.5:
    delta_fiducia_base = 0.02
elif adeguatezza_score >= 0.3:
    delta_fiducia_base = -0.01
else:
    delta_fiducia_base = -0.04
Punto critico: Questo delta è applicato a TUTTI i clienti del cluster, indipendentemente dalla loro history o evoluzione.

Step 5: Metriche di Business (_calcola_metriche_business, riga 667)
Aggrega delta_fiducia su tutti round e cluster
Calcola metriche finali per i due promotori
# simulation_engine.py, riga 821-823
metrics["valore_aggiunto_personalizzazione"] = round(
    metrics["valore_aggiunto_personalizzazione"], 4
)
2. Dati Osservati (S0_fix5, 200 round)
Metrica	FISSO	ADAPT	Differenza
Media delta_fiducia/round	+0.0015	+0.0001	-0.0014 (ADAPT peggio)
Media adeguatezza_score	0.7096	0.6807	ADAPT più disperso
Tasso accettazione	95.4%	78.9%	ADAPT ha più rifiuti
Delta fiducia cumulato	+2.9	+0.22	ADAPT 7.6x peggio
clienti_salvati_dal_churn	N/A	0	Sempre zero
Analisi per Cluster
FISSO gestisce: Cluster (0,0)-(1,4) = righe 0-1 = profili Conservative + Balanced
ADAPT gestisce: Cluster (2,0)-(3,4) = righe 2-3 = profili Growth + Aggressive
Non stanno competendo sui medesimi clienti.

3. Ipotesi Verificate
✓ IPOTESI A: ADEGUATEZZA_MATRIX non incentiva personalizzazione
CONFERMATA.

ADEGUATEZZA_MATRIX è una tabella lookup 4×10 (4 profili × 10 prodotti)
Tutti i valori sono hardcoded (riga 25-74 simulation_engine.py)
Per un dato (profilo, prodotto), il score è sempre lo stesso, indipendentemente da:
Quanto bene ADAPT ha imparato nei round precedenti
Quanta fiducia il cliente ha accumulato
Se questo è il 1° o il 200° round
Conseguenza: Non esiste meccanismo di ricompensa per personalizzazione nel tempo.

Se ADAPT sceglie Bond_Corporate per un cliente Growth, ottiene sempre adeguatezza = 1.0 → delta = +0.05. Se FISSO sceglie Bond_Corporate per lo stesso profilo, ottiene sempre adeguatezza = 1.0 → delta = +0.05.

L'unica differenza è la frequenza di scelta del prodotto "giusto".

✓ IPOTESI B: FISSO parte avvantaggiato per costruzione
PARZIALMENTE CONFERMATA.

FISSO sceglie Bond_Corporate in ~80% dei casi (per sua natura "benchmark fissa").

Valutiamo l'adeguatezza per i due profili che FISSO gestisce:

Conservative: Bond_Corporate → adeguatezza = 0.5 (accettabile, delta = +0.02)
Balanced: Bond_Corporate → adeguatezza = 0.8 (buono, delta = +0.05)
Media ponderata: 0.65-0.8 adeguatezza, quasi sempre accettato.

Tuttavia, ADAPT gestisce:

Growth: Bond_Corporate → adeguatezza = 1.0 (perfetto, delta = +0.05)
Aggressive: Bond_Corporate → adeguatezza = 0.7 (buono, delta = +0.05)
Media ponderata: 0.85 adeguatezza, dovrebbe essere migliore di FISSO!

Perché ADAPT underperforma allora? Perché sceglie diversamente rispetto a Bond_Corporate:

Sceglie Fondi_Azionari (30%), Assicurazioni (15%), ecc.
Questi prodotti hanno adeguatezza più bassa per Growth/Aggressive
Tasso di accettazione crolla da 95% (FISSO) a 79% (ADAPT)
Questo è dovuto a qualità dell'LLM, non a vantaggio di design.

✓ IPOTESI C: Non esiste dimensione dinamica di valore per l'adattamento
CONFERMATA.

Delta_fiducia è determinato UNICAMENTE da lookup(profilo, prodotto).

La storia del cliente è irrilevante:

Se un cliente Conservative ha fiducia bassa nel round 50, ADAPT non lo sa
ADAPT sceglie comunque in base al suo prompt generico, non su "questo cliente ha bisogno di recupero"
Se sceglie il prodotto "sbagliato", perde -0.01 di fiducia per quel cliente
Se sceglie quello "giusto", guadagna +0.02
Non c'è feedback: Il cliente non "grida" che ha fiducia bassa e richiede un prodotto speciale.

✓ IPOTESI D: clienti_salvati_dal_churn è sempre zero
CONFERMATA.

Codice (riga 750-751 simulation_engine.py):

if coords in mappa_fisso:
    delta_fid_adapt = strat.get('delta_fiducia_medio', 0.0)
    if mappa_fisso[coords] < 0 and delta_fid_adapt >= 0:
        metrics["clienti_salvati_dal_churn"] += 1
Condizione: mappa_fisso[coords] < 0

Per cui FISSO deve aver generato delta_fiducia_medio < 0 in quel cluster.

Valori minimi di delta_fiducia:

Se adeguatezza < 0.3: delta = -0.04
Se adeguatezza >= 0.3: delta >= -0.01
FISSO sceglie Bond_Corporate:

Per Conservative: adeguatezza = 0.5 → delta = +0.02 (sempre positivo)
Per Balanced: adeguatezza = 0.8 → delta = +0.05 (sempre positivo)
FISSO NEVER ha delta < 0. Quindi la condizione non si verifica mai. Counter rimane a 0.

Questo rende la metrica illusoria: Misura l'assunzione che FISSO "scarsi", ma il design non lo permette.

4. Causa Radice #1: Segregazione Cliente-Promotore (CRITICO)
Codice Incriminato
File: populate_finsim.py, riga 326-331

# GESTISCE: Promotori → Clienti (A/B split: cluster_riga < 2 → Fisso, cluster_riga >= 2 → Adattativo)
for i in range(100):
    cluster_row = (i // 5) % 4
    prom_uuid = 'promotore-fisso-1' if cluster_row < 2 else 'promotore-adattativo-1'
    
    rels.append({
        'uuid': str(uuid.uuid4()),
        'type': 'GESTISCE',
        'source_uuid': prom_uuid,
        'target_uuid': f'cliente-{i:03d}',
        ...
    })
Conseguenza
Promotore	Gestisce	Profili	Patrimonio	Num Clienti
FISSO	Righe 0-1	Conservative, Balanced	Basso-Medio	50
ADAPT	Righe 2-3	Growth, Aggressive	Medio-Alto	50
Problema
Non è A/B testing. È confronto tra due strategie su coorti diverse.

La vera domanda che dovrebbe sottostare è:

"Dato lo stesso cliente, è meglio personalizzare con LLM o usare una strategia fissa?"

Quella che state testando è:

"Promotore fisso è efficace con clienti conservativi? Promotore adattativo è efficace con clienti aggressivi?"

Impossibile separare due effetti:

Qualità della strategia (FISSO vs ADAPT)
Difficoltà della clientela (Conservative è "più facile" che Growth)
5. Causa Radice #2: ADEGUATEZZA_MATRIX Statica (SERIO)
Codice Incriminato
File: simulation_engine.py, riga 25-74

ADEGUATEZZA_MATRIX = {
    "Conservative": {
        "Cash_Equivalents":      1.0,
        "Bond_Sovereign":        0.9,
        "Bond_Corporate":        0.5,
        ...
    },
    "Balanced": { ... },
    ...
}
Problema
La matrice è lookup puro, non modello. Conseguenze:

Non premia l'apprendimento: Se ADAPT imparasse nel round 10 che un cliente ha bisogno di un prodotto diverso, non potrebbe applicarlo diversamente dal round 1.

Delta_fiducia è fisso: Il cliente guadagna sempre +0.02 per un prodotto "accettabile", indipendentemente da quante volte ADAPT l'ha già proposto.

Nessun effetto compounding: La fiducia cresce come n × 0.02, non esponenziale. Un cliente che "scopre" nel round 5 che ADAPT capisce i suoi bisogni non guadagna fiducia più veloce.

Esempio di Design Migliore
# Ipotetico: delta_fiducia varia anche con l'acceptance rate storico
acceptance_rate = count_accepted / count_offered
if acceptance_rate > 0.9:
    delta_fiducia = 0.05 + 0.02 * (acceptance_rate - 0.9)  # Boost
elif acceptance_rate < 0.5:
    delta_fiducia = 0.02 - 0.01 * (0.5 - acceptance_rate)  # Malus
else:
    delta_fiducia = 0.02
Con questo, ADAPT potrebbe costruire fiducia più veloce se imparasse a scegliere bene.

6. Causa Radice #3: clienti_salvati_dal_churn Impossibile per Design (GRAVE)
Codice Incriminato
File: simulation_engine.py, riga 750-751

if mappa_fisso[coords] < 0 and delta_fid_adapt >= 0:
    metrics["clienti_salvati_dal_churn"] += 1
Problema
Nessun cliente potrà mai essere "salvato" dal churn perché:

FISSO ha delta_fiducia sempre >= +0.02 (mai negativo)
La condizione richiede mappa_fisso < 0
Evento impossibile
Questa metrica è illusoria: Misura un risultato che non può accadere.

7. Opzioni di Intervento
OPZIONE 1: Riallocazione Equa dei Clienti (CORREZIONE ONESTA)
Impatto: ⭐⭐⭐⭐⭐ (altissimo)

Sforzo: 🔧 Piccolo (1-2 ore)

Che cosa: Dividere equamente i 100 clienti tra FISSO e ADAPT, ma su cluster diversi:

Ogni cluster (riga, col) viene gestito da ENTRAMBI i promotori
A/B testing vero: stesso cliente, due strategie
Come:

Modificare populate_finsim.py riga 326-331 per assegnare i 100 clienti in modo casuale (non per cluster_riga)
Creare una relazione GESTISCE per ogni (Cliente, Promotore)
~50 clienti per FISSO
~50 clienti per ADAPT
Ma distribuiti uniformemente nei cluster
Alternativa più semplice: Usare hash(cliente_id) % 2 == 0 per determinare il promotore.

Metriche da validare dopo:

✓ valore_aggiunto_personalizzazione: dovrebbe essere > 0 se ADAPT è intelligente
✓ clienti_salvati_dal_churn: dovrebbe crescere se ADAPT recupera clienti in calo
✓ tasso_conversione: dovrebbe essere simile se non ci sono effetti di selezione
OPZIONE 2: Dinamicità della Matrice (CORREZIONE PROFONDA)
Impatto: ⭐⭐⭐⭐ (molto alto, se combinato con OPZIONE 1)

Sforzo: 🔧 Medio (4-6 ore)

Che cosa: Fare in modo che il delta_fiducia dipenda anche da:

Acceptance rate storico del cliente per quel promotore
Fiducia attuale vs fiducia iniziale
Tempo (round) dalla ultima accettazione
Come:

Tracciare per ogni cliente (riga 555 simulation_engine.py):

acceptance_count: quanti round il cliente ha accettato il prodotto
last_acceptance_round: quando è stata l'ultima accettazione
Modificare calcola_reazione_clienti() per aggiungere un acceptance_boost:

acceptance_boost = 0.01 * min(acceptance_count, 10)  # Up to +0.1
delta_fiducia_base += acceptance_boost
Aggiungere un malus per churn risk se fiducia cala:

if fiducia_attuale < 0.3:
    delta_fiducia_base += 0.02  # "Recovery opportunity"
Metriche da validare dopo:

✓ valore_aggiunto_personalizzazione: dovrebbe crescere se ADAPT riconosce e recupera clienti
✓ clienti_salvati_dal_churn: dovrebbe essere > 0 se ADAPT ha malus/recovery
✓ trend_fiducia: dovrebbe mostrare crescita accelerata per ADAPT nel tempo
OPZIONE 3: Prompt Specifico per Growth/Aggressive (SCORCIATOIA)
Impatto: ⭐⭐ (basso, non risolve il problema)

Sforzo: 🔧 Minimo (30 min)

Che cosa: Modificare il prompt dell'LLM per indirizzare meglio le scelte di ADAPT verso clienti Growth/Aggressive

Come:

Aggiungere al user_prompt di PromotoreAgent (riga 255):
Se il cluster è Growth/Aggressive:
    "Per questo profilo, considera Fondi_Azionari e Bond_Corporate come preferiti."
Metriche da validare dopo:

✗ valore_aggiunto_personalizzazione: probabilmente migliorerà leggermente, ma non drasticamente
✗ clienti_salvati_dal_churn: rimane 0 (problema di design non risolto)
✓ tasso_conversione_adapt: dovrebbe migliorare un po'
Avvertenza: Questa è una "scorciatoia" che non affronta il problema di design. È una patch, non una soluzione.

OPZIONE 4: Combinazione (SOLUZIONE COMPLETA)
Impatto: ⭐⭐⭐⭐⭐

Sforzo: 🔧 Medio-Alto (8-10 ore)

Sequenza:

Fase 1: Applicare OPZIONE 1 (riallocazione clienti)
Fase 2: Applicare OPZIONE 2 (dinamicità matrice)
Fase 3: Test su 200 round
Fase 4: Validare metriche
Risultato atteso:

ADAPT dovrebbe avere valore_aggiunto_personalizzazione > 0
clienti_salvati_dal_churn > 0
ADAPT mantiene acceptance rate alto perché capisce i clienti nel tempo
8. Ordine di Priorità
Numero	Opzione	Impatto	Sforzo	Quando Farla
1	OPZIONE 1 (Riallocazione)	⭐⭐⭐⭐⭐	🔧	Immediatamente
2	OPZIONE 2 (Dinamicità)	⭐⭐⭐⭐	🔧	Dopo opzione 1
3	OPZIONE 3 (Prompt)	⭐⭐	🔧	Se opzione 1 non risolve completamente
4	OPZIONE 4 (Completa)	⭐⭐⭐⭐⭐	🔧	Se vuoi massima robustezza
9. Validazione Post-Intervento
Per ogni opzione, dopo l'implementazione:

Rieseguire la simulazione su S0_fix5 (200 round)

Controllare queste metriche:

valore_aggiunto_personalizzazione: Dovrebbe cambiare segno (da negativo a positivo) con OPZIONE 1
clienti_salvati_dal_churn: Dovrebbe essere > 0 con OPZIONE 1+2
tasso_conversione_adapt_pct: Dovrebbe convergere verso tasso_conversione_fisso_pct
fiducia_cumulata.vantaggio_adapt: Dovrebbe crescere positivamente
Verificare i cluster:

Con OPZIONE 1, ogni cluster dovrebbe avere dati sia per FISSO che per ADAPT
Il vantaggio_netto_ia dovrebbe essere positivo per almeno il 50% dei cluster
Analisi di sensibilità:

Eseguire su tutti e 5 gli scenari (S0-S4)
Verificare che il miglioramento di ADAPT sia coerente
Conclusione
ADAPT underperforma non per insufficienza dell'AI, ma perché:

✗ Gestisce clienti completamente diversi da FISSO (non è A/B test)
✗ La matrice di adeguatezza non premia l'apprendimento nel tempo
✗ La metrica "clienti salvati dal churn" è strutturalmente impossibile
Soluzione: Applicare OPZIONE 1 (riallocazione equa) + OPZIONE 2 (dinamicità) per permettere a ADAPT di competere onestamente e di costruire valore nel tempo.
