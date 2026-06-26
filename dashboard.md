# 📊 Guida Completa ai Grafici FINsim Dashboard

## Indice
1. [Dashboard del Promotore](#dashboard-del-promotore)
2. [Dashboard della Banca](#dashboard-della-banca)
3. [Dashboard del Cliente](#dashboard-del-cliente)
4. [Grafici Consigliati dal Copilota IA](#grafici-consigliati-dal-copilota-ia)
5. [Legenda Colori e Simbologie](#legenda-colori-e-simbologie)

---

## Dashboard del Promotore

### 🤖 Copilota IA (All Viste)
**Tipo:** Panel interattivo  
**Posizione:** Top della dashboard (grid-column: 12/12)

**Cosa indica:**
- Motore di ricerca intelligente per interrogazioni custom sulla simulazione
- Analizza i 200 round storici e fornisce risposte con grafici consigliati
- Consente di esplorare aspetti specifici della performance sia ADAPT che FISSO

**A cosa serve:**
- Estendere le analisi oltre i grafici di default
- Ottenere approfondimenti personalizzati su metriche specifiche
- Scoprire pattern e anomalie nascoste nei dati

**Come usarlo:**
1. Scrivi una domanda nel campo di input (es: "Analizza il trend della compliance")
2. Premi Enter o clicca su uno dei quick-pill predefiniti
3. Il sistema analizza i dati e restituisce una breve analisi + grafici consigliati
4. Valuta l'utilità della risposta con le stelle (1-5)

**Output:**
- Brief sintetico della risposta
- Dettagli approfonditi
- Fino a 5 grafici consigliati (renderizzati dinamicamente)
- Rating per feedback sul Copilota

---

### 📍 Regime di Mercato (Market Regime Card)
**Tipo:** Status card  
**Posizione:** Top della dashboard (grid-column: 12/12)

**Cosa indica:**
- **LED Status:** Colore pulsante che riflette il regime macroeconomico attuale (Stabile/Espansione/Warning/Critico)
- **Tasso BCE:** Tasso di policy della Banca Centrale Europea (es: 2.0% dopo 8 tagli)
- **Indice Georisk:** Tensione geopolitica su scala 0-100 (es: 78/100 Crisi Hormuz)
- **Market Pulse:** Sentiment e performance mercati (es: "Equity -12%, Spread +80bp")
- **RegWatch Compliance:** Pressione normativa MiFID attuale (Media/Alta/Allerta)

**A cosa serve:**
- Contextualizzare tutte le decisioni della Direttiva Bancaria nel regime macroeconomico corrente
- Capire perché la strategia cambia da round a round
- Anticipare vincoli di compliance che influenzano le proposte

**Come leggerlo:**
- **LED stabile (verde):** Condizioni neutrali, approccio standard possibile
- **LED espansione (azzurro):** Ciclo favorevole, aggressività misurata su equity/credito
- **LED warning (arancio):** Volatilità elevata, ribilanciamento verso short-duration
- **LED critico (rosso):** Shock di mercato, attivazione protocolli protezione capitale

**Tip specifico:**
- Ogni regime include un `promoter_tip` (per vista promotore) che suggerisce l'approccio strategico consigliato

---

### 🧠 Direttiva Strategica LLM (ADAPT-1)
**Tipo:** Highlight panel  
**Posizione:** Riga 1, colonna 1-8

**Cosa indica:**
- Strategia consigliata dal LLM pesante (HEAVY_LLM) per il round corrente
- Tags semantici che categorizzano l'approccio (es: "Risk-On", "Compliance-First", "Momentum-Trading")
- Approccio comunicativo specifico per il contesto macroeconomico
- Scenario attivo evidenziato in tempo reale

**A cosa serve:**
- Comprendere il razionale della strategia adattiva generata dall'IA
- Allineare le azioni del promotore con la direttiva bancaria
- Tracciare l'evoluzione strategica lungo i 20 round

**Come leggerlo:**
1. Leggi i **Tags:** forniscono una categorizzazione veloce della strategia (es: "Conservative", "Growth-Focused")
2. **Strategia Consigliata:** Descrive l'allocazione e il posizionamento nei mercati
3. **Approccio Comunicativo:** Spiega il tone con cui il promotore deve comunicare ai clienti (es: "Enfatizzare la diversificazione per ridurre ansia")

---

### 💰 Commissioni Cumulate (ADAPT)
**Tipo:** KPI card  
**Posizione:** Riga 1, colonna 9-12

**Cosa indica:**
- Somma totale delle commissioni incassate dalla strategia ADAPT su 200 tentativi di proposta
- Calcolate al 1% sulla raccolta media
- Comparabile con FISSO per misurare il vantaggio economico

**A cosa serve:**
- Quantificare il valore generato dall'approccio personalizzato
- Motivare l'adozione della strategia ADAPT vs benchmark fisso
- Tracciare la redditività del promotore

**Come leggerlo:**
- Valore assoluto in €
- Note sulla commissione % e ticket medio
- Se superiore a FISSO, dimostra che la personalizzazione paga

---

### 📋 Next Best Action
**Tipo:** Lista di azioni consigliate  
**Posizione:** Riga 2, colonna 1-6

**Cosa indica:**
- Azioni prioritarie consigliate dal motore IA per il prossimo ciclo di proposte
- Derivate da analisi di churn risk, sentiment clienti, regime di mercato
- Ordinate per importanza strategica

**A cosa serve:**
- Guidare le decisioni tattiche del promotore nel prossimo round
- Prevenire abbandoni anticipando i bisogni
- Sincronizzare l'operatività con la Direttiva Bancaria

**Come leggerlo:**
- Ogni azione è una box con descrizione testuale
- Implementare dall'alto verso il basso per priorità
- Connettere al "Torre di Controllo Allarmi" per identificare i clienti target

---

### 🚨 Torre di Controllo Allarmi Portafoglio
**Tipo:** Alert badges  
**Posizione:** Riga 2, colonna 7-12

**Cosa indica:**
- **Rischio Abbandono:** Numero di clienti con anomalie fiducia/delta significative
- **Allerta Conformità Normativa:** Numero di proposte con scostamenti di adeguatezza MiFID

**A cosa serve:**
- Monitoraggio real-time dei rischi operativi
- Identificazione immediata di clienti a rischio churn
- Compliance monitoring automatizzato

**Come leggerlo:**
- **Triggered (rosso):** Se il conteggio > 0, esiste un rischio attivo che richiede intervento
- **Non triggered (verde):** Portfolio è entro i parametri di rischio
- Cliccare sul badge per visualizzare la lista dei clienti colpiti (quando implementato)

---

### 🔥 Mappa di Valore (Patrimonio Gestito vs Profilo Rischio) — Promotore
**Tipo:** Heatmap Plotly interattiva  
**Posizione:** Riga 2B, colonna 1-6

**Cosa indica:**
- Grid di cluster clienti (es: 4x5 = 20 cluster)
- Colore indica il vantaggio percentuale di ADAPT vs FISSO in quella zona
- Rosso: FISSO domina; Giallo/Arancio: parità o piccoli vantaggi; Verde: ADAPT domina

**A cosa serve:**
- Identificare i segmenti dove l'IA genera più valore
- Indirizzare gli sforzi di consultazione verso cluster ad alto potenziale
- Diagnosticare segmenti dove la strategia standard è ancora competitiva

**Come leggerlo:**
- Passa il mouse su una cella per vedere il valore % esatto
- Verde intenso = area di massimo vantaggio competitivo per ADAPT
- Rosso = area dove il benchmark standard è più efficace (riconsiderare approccio)
- Celle arancio/gialle = zone di transizione dove dipende dal timing/sentiment

---

### 📊 Delta Performance (Vantaggio ADAPT)
**Tipo:** Comparison cards  
**Posizione:** Riga 2C, colonna 7-12

**Cosa indica:**
- **Commissioni (+€):** Differenza assoluta in € tra ADAPT e FISSO
- **% Superiorità:** Incremento percentuale rispetto a FISSO
- **Conversione (+%):** Punto percentuale di vantaggio nel tasso di conversione

**A cosa serve:**
- Quantificare il ROI della strategia adattiva in modo sintetico
- Fornire evidenza numerica del valore aggiunto per stakeholder/clienti
- Tracciare il momentum della strategia

**Come leggerlo:**
- Colore verde (#1FA463) = vantaggio per ADAPT
- Valore assoluto + percentuale forniscono prospettive diverse
- Se delta negativo, la strategia standard sta performando meglio in quel round

---

### 📈 Curva di Sopravvivenza Clienti (Kaplan-Meier)
**Tipo:** Line chart Plotly  
**Posizione:** Riga 3, colonna 1-12

**Cosa indica:**
- Tasso di retention dei clienti nel tempo (200 round)
- Verde: sopravvivenza ADAPT; Rosso: sopravvivenza FISSO
- "Scalini" verticali = momenti di abbandono di clienti

**A cosa serve:**
- Valutare la stabilità e durability della relazione clienti
- Diagnosticare quando e perché i clienti abbandonano
- Comparare la stickiness tra le due strategie

**Come leggerlo:**
- Asse X = round progressivi
- Asse Y = % clienti ancora attivi (0-100%)
- Se ADAPT è sopra FISSO, la strategia personalizzata tiene meglio i clienti
- Scalini ripidi indicano periodi di abbandoni concentrati (possibile shock di mercato o inadeguatezza percepita)

**Interpretazione:**
- Curva piatta = buona retention
- Curva che scende velocemente = alto churn (necessario intervento)

---

### Confronto Performance: Consulenza IA Dinamica vs Strategia Standard
**Tipo:** Metric cards (4 KPI)  
**Posizione:** Riga 4, colonna 1-12

**Cosa indica:**
Comparazione diretta su 4 dimensioni chiave:
- **Tasso Conversione:** % proposte accettate dal cliente
- **Fiducia Media Clienti:** Sentiment medio su scala 0-100%
- **Commissioni Cumulate:** Ricavo totale in €
- **Proposte Totali:** Volume di proposte inviate

**A cosa serve:**
- Dashboard scoreboard per performance summary
- Facilitare la comunicazione di risultati a stakeholder
- Identificare quale dimensione crea il vantaggio

**Come leggerlo:**
- Ogni card mostra ADAPT (verde, sopra) e FISSO (blu, sotto)
- Leggi verticalmente per comparazione immediata
- Valori ADAPT sistematicamente superiori = strategia vincente

---

### 📊 Conversione per Profilo di Rischio
**Tipo:** Data table  
**Posizione:** Riga 4, colonna 1-6

**Cosa indica:**
- Tasso di conversione (%) ADAPT vs FISSO per ogni profilo di rischio cliente
- Profili: Conservative, Moderate, Growth, Aggressive, Speculative (es.)
- Badge "Dominanza" indica quale strategia vince in quel profilo

**A cosa serve:**
- Diagnosticare su quale segmento demografico ADAPT è più efficace
- Identificare profili dove il benchmark è ancora competitivo
- Ottimizzare la targeting per il prossimo round

**Come leggerlo:**
- Colore verde nella colonna ADAPT = valore più alto
- "Dominanza: ADAPT" = strategia personalizzata più efficace per quel profilo
- "Dominanza: FISSO" = necessario rivedere approccio, possibile inadeguatezza di personalizzazione

---

### 📋 Tasso di Accettazione per Prodotto
**Tipo:** Data table  
**Posizione:** Riga 4, colonna 7-12

**Cosa indica:**
- Tasso di accettazione (%) per ogni categoria prodotto (es: Bond Corporate, Azionario, Monetario, etc.)
- ADAPT vs FISSO
- Badge di dominanza

**A cosa serve:**
- Capire quali prodotti "vendono" meglio con quale strategia
- Indirizzare la composizione delle proposte future
- Diagnosticare prodotti sottoperformanti

**Come leggerlo:**
- Se Bond Corporate in ADAPT è al 65% e in FISSO al 50%, l'IA lo propone meglio
- Badge "FISSO" su un prodotto suggerisce che il benchmark standard lo presenta meglio (più standard, meno personalizzazione)
- Cercare pattern: es., ADAPT domina tutti i prodotti vs FISSO domina solo azionario

---

### Adeguatezza Media per Round
**Tipo:** Line chart (Chart.js)  
**Posizione:** Riga 5, colonna 1-6

**Cosa indica:**
- Percentuale media di adeguatezza (0-100%) delle proposte su 200 tentativi
- Linea verde = ADAPT; Linea blu tratteggiata = FISSO
- Adeguatezza = quanto il prodotto proposto rispecchia il profilo di rischio del cliente

**A cosa serve:**
- Monitorare compliance rispetto ai regolamenti MiFID
- Verificare che la personalizzazione non viola i vincoli di adeguatezza
- Tracciare il miglioramento nel matching prodotto-cliente

**Come leggerlo:**
- Asse X = 200 tentativi di proposta
- Asse Y = adeguatezza % (0-100%)
- Se ADAPT > FISSO, la personalizzazione migliora l'allineamento senza violare norme
- Se ADAPT < FISSO, l'IA sta proponendo prodotti non conformi (anomalia, richiedere revisione)
- Trend decrescente = avanzare l'allarme per revisione della Direttiva

**Deduzione pratica:**
- Se rimane sopra 85%, il sistema è in buona salute
- Scendere sotto 70% richiede intervento immediato

---

### Proposte Accettate per Round
**Tipo:** Bar chart (Chart.js)  
**Posizione:** Riga 5, colonna 7-12

**Cosa indica:**
- Numero cumulato di proposte accettate per blocco di tentativi
- 10 blocchi totali (20 proposte per blocco = 200 totali)
- Verde = ADAPT; Blu = FISSO (barre sovrapposte per confronto)

**A cosa serve:**
- Tracciare la volumetria di vendita nel tempo
- Identificare periodi di maggior successo
- Diagnosticare stagionalità o shock di performance

**Come leggerlo:**
- Asse X = blocchi (es: "1-20", "21-40", ..., "181-200")
- Asse Y = numero cumulato proposte accettate
- Barra ADAPT sistematicamente più alta = conversion rate migliore
- Picchi anomali = possibile effetto di scenario macroeconomico favorevole
- Cali nel blocco finale = possibile affaticamento della strategia a lungo termine

---

---

## Dashboard della Banca

### 🤖 Copilota IA
*(Vedere sezione Dashboard del Promotore — è lo stesso componente)*

---

### 📍 Regime di Mercato (Market Regime Card)
*(Vedere sezione Dashboard del Promotore — è lo stesso, con `client_tip` al posto di `promoter_tip`)*

---

### Matrice Vendite e Adeguatezza
**Tipo:** Data table  
**Posizione:** Riga 1, colonna 1-12

**Cosa indica:**
- Aggregazione delle vendite per categoria di prodotto e cluster clienti
- **Prodotto Proposto:** Categoria (es: Bond Corporate, Azionario, etc.)
- **Cluster Clienti:** Segmento demografico/economico
- **Volume (M€):** Somma raccolta in milioni di euro
- **Adeguatezza %:** Percentuale media di conformità MiFID per quel cluster
- **Status:** Colore (verde/ambra/rosso) che riflette il risk compliance

**A cosa serve:**
- Consolidare la view sulle vendite dal livello direttivo
- Monitorare il rischio di non-conformità per segmento
- Identificare cluster a rischio che necessitano di ribilanciamento

**Come leggerlo:**
- Ordina per volume per capire dove è concentrata la raccolta
- Leggi la barra di adeguatezza: se verde (>85%), è ok; se rosso (<70%), esiste rischio normativo
- Cluster con status rosso richiedono intervento sulla Direttiva

---

### Raccolta Netta — Trend
**Tipo:** Line chart (Chart.js)  
**Posizione:** Riga 2, colonna 1-8

**Cosa indica:**
- Andamento della raccolta netta cumulata su 200 tentativi di proposta
- Linea verde = ADAPT; Linea blu = FISSO
- Raccolta netta = nuova raccolta - abbandoni

**A cosa serve:**
- Visualizzare il trend di crescita del patrimonio gestito
- Misurare la divergenza tra le due strategie nel lungo periodo
- Identificare se la strategia adattiva sta generando maggior valore sostenuto

**Come leggerlo:**
- Asse X = 200 tentativi
- Asse Y = raccolta netta cumulata (milioni €)
- Se ADAPT è sopra FISSO, la strategia personalizzata accumula più valore
- Plateau suggerisce necessità di ricalibrazione della Direttiva
- Trend in calo = recessione percepita o loss of trust, richiedere analisi

---

### Target Direttiva vs Attuale
**Tipo:** Radar chart (Chart.js)  
**Posizione:** Riga 2, colonna 9-12

**Cosa indica:**
- 5 dimensioni strategiche (Bond Corporate, Monetario, Azionario, Illiquidi, Gov Bond)
- Linea grigia tratteggiata = Target della Direttiva (allocazione pianificata)
- Linea blu = Portafoglio Effettivo (allocazione realizzata)

**A cosa serve:**
- Verificare l'esecuzione della Direttiva Bancaria
- Identificare sovraeposizioni o sottodimensionamenti
- Diagnosticare gap tra strategia pianificata e realtà operativa

**Come leggerlo:**
- Se il blu è dentro il grigio, l'allocazione è allineata
- Sporgenze blu = sovraesposizione in quella classe di asset (possibile drift da risk)
- Rientranze blu = sottodimensionamento (necessario aumentare proposte in quella categoria)
- Il radar ideale vede il blu tutto dentro il grigio

---

### 📊 Visualizzazioni Avanzate Plotly (Banca)

#### Mappa di Valore (Patrimonio Gestito vs Profilo Rischio)
*(Uguale a quella della Promotore — vedere sezione Dashboard del Promotore)*

---

#### Analisi Contribuzione Patrimonio Gestito
**Tipo:** Waterfall chart Plotly  
**Posizione:** Riga 3, colonna 7-12

**Cosa indica:**
- Scomposizione del patrimonio finale passo per passo:
  1. **AUM Iniziale:** Patrimonio gestito al Round 1
  2. **Nuova Raccolta:** Somma netti aggiunta
  3. **Effetto Mercato:** Gain/Loss da performance di mercato
  4. **Abbandoni Clienti:** Patrimonio perso per churn
  5. **AUM Finale:** Patrimonio gestito al Round 20

**A cosa serve:**
- Capire quali fattori hanno contribuito alla crescita/contrazione
- Diagnosticare se il problema è nel business (raccolta) o nei mercati (drawdown)
- Quantificare l'impatto del churn sulla base patrimoniale

**Come leggerlo:**
- Barre verdi = contributi positivi
- Barre rosse = contributi negativi
- L'altezza della barra indica l'importanza relativa
- Se "Abbandoni Clienti" è rosso scuro e grande, il churn è il principale problem

---

#### Evoluzione Performance Cumulata (200 Tentativi di Proposta)
**Tipo:** Multi-line chart Plotly  
**Posizione:** Riga 4, colonna 1-12

**Cosa indica:**
- Trend di performance cumulata ADAPT vs FISSO su tutti i 200 tentativi
- Ogni punto rappresenta la performance media sull'universo di clienti
- Linea verde = ADAPT; Linea blu = FISSO

**A cosa serve:**
- Visualizzare la traiettoria della strategia nel tempo
- Identificare inflection point dove una strategia comincia a vincere
- Diagnosticare persistenza vs casualità delle performance differenziali

**Come leggerlo:**
- Se ADAPT è sempre sopra FISSO, la personalizzazione vince stabilmente
- Se le linee si incrociano, significa che una strategia era vincente all'inizio ma ha perso momentum
- La divergenza aumentante = effetto composto della personalizzazione (molto positivo)
- Conversione = strategia standard sta recuperando terreno (anomalia)

---

---

## Dashboard del Cliente

### 🤖 Copilota IA
*(Vedere sezione Dashboard del Promotore)*

---

### 📍 Regime di Mercato (Market Regime Card)
*(Vedere sezione Dashboard della Banca — qui include `client_tip` specifico per il cliente)*

**Client Tip Examples:**
- **S0:** "Condizioni di mercato regolari. Il portafoglio segue l'asset allocation strategica programmata."
- **S1:** "Ciclo favorevole ai mercati. Portafoglio allineato a risk-on moderato con diversificazione."
- **S2:** "Fase di aggiustamento dei tassi di interesse. Monitoraggio attivo della componente obbligazionaria."
- **S3:** "Fase di forte instabilità tecnica dei mercati. Si raccomanda stabilità emotiva e focus sul lungo termine."

---

### Heatmap Propensione al Rischio
**Tipo:** Grid di 20 celle colorate  
**Posizione:** Riga 1, colonna 1-12

**Cosa indica:**
- Griglia 4x5 che rappresenta la propensione al rischio percepita del cliente nel tempo (20 round)
- Colore riflette il % di propensione (verde intenso 85%+ = alto; rosso <40% = basso)
- Evoluzione della risk tolerance del cliente lungo la simulazione

**A cosa serve:**
- Monitorare se il profilo di rischio del cliente sta evolvendo
- Identificare cambiamenti di sentiment dovuti a market conditions
- Diagnosticare se la comunicazione è efficace nel mantenere la fiducia

**Come leggerlo:**
- Cella verde intenso = momento di risk-on forte
- Cella gialla/arancio = moderazione del rischio percepito
- Cella rossa = aversion al rischio aumentata (possibile shock di mercato)
- Leggere riga per riga (round per round) per tracciare la traiettoria
- Omogenea verde = cliente stabile e coerente
- Alternanza rossa-verde = cliente volatile, necessita comunicazione più rassicurante

---

### Evoluzione Fiducia
**Tipo:** Area chart (Chart.js)  
**Posizione:** Riga 2, colonna 1-6

**Cosa indica:**
- Fiducia media del cliente su scala 0-100% lungo i 200 tentativi
- Linea viola piena con area sottostante
- Fiducia = quanto il cliente si fida della Direttiva e del Promotore

**A cosa serve:**
- Tracciare la qualità della relazione nel tempo
- Identificare momenti critici dove la fiducia crolla
- Diagnosticare se la comunicazione sta funzionando

**Come leggerlo:**
- Asse X = 200 tentativi di proposta
- Asse Y = fiducia % (0-100%)
- Trend crescente = comunicazione efficace e soddisfazione aumentante
- Cali improvvisi = perdita di confidenza da:
  - Inadeguatezza percepita nel portafoglio
  - Shock di mercato non comunicato bene
  - Proposta difformi dal profilo del cliente
- Trend decrescente costante = segnale di disallineamento cronico

**Deduzione pratica:**
- Se rimane sopra 75%, relazione è salda
- Se scende sotto 50%, rischio concreto di abbandono

---

### Allineamento Profilo vs Portafoglio
**Tipo:** Radar chart (Chart.js)  
**Posizione:** Riga 2, colonna 7-12

**Cosa indica:**
- 5 dimensioni di preferenza cliente (Rischio, Orizzonte Temporale, Liquidità, Rendimento Atteso, Conoscenza Finanziaria)
- Linea blu = profilo dichiarato del cliente (da assessment iniziale)
- Linea verde = adattamento dinamico percepito nel portafoglio

**A cosa serve:**
- Verificare che il portafoglio rispecchi il profilo del cliente
- Identificare aree di disallineamento che potrebbero causare insoddisfazione
- Diagnosticare dove la comunicazione ha fallito

**Come leggerlo:**
- Se le aree coincidono = client è perfettamente soddisfatto
- Se il blu è dentro il verde = il portafoglio è più conservativo del profilo (possibile underperformance percepita)
- Se il verde sporge = il portafoglio è più rischioso del profilo (rischio compliance, insoddisfazione)
- Discrepanze su "Rendimento" = aspettative non gestite correttamente
- Discrepanze su "Rischio" = maggiore urgenza di intervento (compliance risk)

---

---

## Grafici Consigliati dal Copilota IA

Il Copilota IA può consigliare grafici aggiuntivi oltre a quelli di default nella dashboard. Sono renderizzati dinamicamente con Plotly e includono:

### 1. **TREND_COMPLIANCE** — Trend di Conformità Normativa (MiFID)
**Cosa mostra:**
- Evoluzione della percentuale media di conformità lungo i round
- Linea verde = ADAPT; Linea blu = FISSO

**Quando chiedere:**
- "Analizza il trend della compliance"
- "Quanto è conforme la nostra strategia rispetto alla normativa?"

**Come leggerlo:**
- Se ADAPT rimane sopra FISSO, l'IA mantiene conformità superiore
- Se scende sotto 85%, elevare alert di compliance

---

### 2. **SEMAFORO_ADEGUATEZZA** — Stato Adeguatezza Proposte (Semaforo)
**Cosa mostra:**
- Distribuzione delle proposte in tre stati: Verde (Adeguato ≥85%), Giallo (Margine 70-85%), Rosso (Non Adeguato <70%)
- Per entrambe le strategie

**Quando chiedere:**
- "Mostrami il semaforo di adeguatezza"
- "Quante proposte sono a rischio compliance?"

**Come leggerlo:**
- Predominanza di verde = situazione salda
- Presence di rosso = intervention richiesto

---

### 3. **SANKEY_FLUSSI** — Analisi di Sopravvivenza Clienti (Kaplan-Meier)
**Cosa mostra:**
- Identificazione di quando e perché i clienti abbandonano
- Flussi diretti da "Attivo" a "Abbandonato" nel tempo

**Quando chiedere:**
- "Analizza il churn dei clienti"
- "Quando abbandoniamo la maggior parte dei clienti?"

**Come leggerlo:**
- Larghezze dei flussi indicano il volume relativo di abbandoni
- Colore verde vs rosso differenzia ADAPT vs FISSO

---

### 4. **HEATMAP_PERFORMANCE** — Mappa del Vantaggio Strategico
**Cosa mostra:**
- Grid di cluster con colore proporzionale al vantaggio ADAPT vs FISSO
- Stesso della heatmap nella dashboard, ma isolata

**Quando chiedere:**
- "Dove vinciamo più facilmente?"
- "Quale segmento preferisce l'IA?"

**Come leggerlo:**
- Cercare aree completamente verdi (opportunità di focalizzazione)
- Evitare aree completamente rosse (benchmark è superiore)

---

### 5. **ANDAMENTO_GUADAGNI** — Evoluzione Ricavi Cumulati
**Cosa mostra:**
- Line chart dei ricavi cumulati (commissioni o raccolta) nel tempo

**Quando chiedere:**
- "Come evolvono i ricavi?"
- "Stiamo crescendo o decrescendo?"

**Come leggerlo:**
- Pendenza positiva = crescita sana
- Plateau = stagnazione (necessario intervento strategico)

---

### 6. **BAR_PRODOTTI** — Soddisfazione per Tipologia Prodotto
**Cosa mostra:**
- Bar chart che confronta l'acceptance rate di ADAPT vs FISSO per ogni categoria di prodotto

**Quando chiedere:**
- "Come performa il Bond Corporate vs Azionario?"
- "Quale prodotto piace ai clienti?"

**Come leggerlo:**
- Barre ADAPT sistematicamente più alte = personalizzazione efficace
- Prodotti con barre uguali = personalizzazione non aggiunge valore

---

### 7. **INTERESSE_COMPOSTO** — Proiezione Interesse Composto
**Cosa mostra:**
- Crescita del patrimonio gestito al costo della fattoria (con effetto composto)
- Proiezione della raccolta nel lungo periodo

**Quando chiedere:**
- "Qual è la proiezione della raccolta?"
- "A che velocità stiamo crescendo?"

**Come leggerlo:**
- Curva esponenziale verde (ADAPT) indica compounding accelerante
- Se ADAPT supera FISSO, l'effetto composto della personalizzazione è significativo

---

### 8. **ACCETTAZIONI_SCENARI** — Proposte Accettate vs Rifiutate
**Cosa mostra:**
- Stacked bar chart o pie chart che mostra la ratio di accettazione

**Quando chiedere:**
- "Qual è il tasso di accettazione?"
- "Quante proposte rifiuta il cliente?"

**Come leggerlo:**
- % di verde (accettate) vs rosso (rifiutate)
- Percentuale di accettazione ADAPT > FISSO = strategia migliore

---

### 9. **LINEE_COMPARATIVE** — Trend Raccolta nei 200 Round
**Cosa mostra:**
- Multi-line chart che confronta ADAPT vs FISSO sulla raccolta

**Quando chiedere:**
- "Confronta le due strategie sulla raccolta"
- "Chi raccoglie di più nel tempo?"

**Come leggerlo:**
- Stessa interpretazione di "Raccolta Netta — Trend" della dashboard Banca

---

### 10. **WATERFALL_PATRIMONIO** — Scomposizione AUM (Variazioni)
**Cosa mostra:**
- Waterfall che scompone il patrimonio finale nei fattori contributivi
- Uguale a quello della dashboard Banca

**Quando chiedere:**
- "Come è composto il patrimonio finale?"
- "Quali fattori hanno influenzato la crescita?"

**Come leggerlo:**
- Stessa interpretazione di "Analisi Contribuzione Patrimonio Gestito" della dashboard Banca

---

### 11. **AREA_GUADAGNI** — Andamento Ricavi nei 200 Round
**Cosa mostra:**
- Area chart che mostra l'evoluzione dei ricavi cumulati

**Quando chiedere:**
- "Mostrami i ricavi nel tempo con visualizzazione area"
- "Come crescono le commissioni?"

**Come leggerlo:**
- Area verde sotto la linea = ricavi ADAPT cumulati
- Se la curva accelera, significa che gli ultimi round sono stati più redditizi

---

---

## Legenda Colori e Simbologie

### Colori Strategia
- **Verde (#1FA463):** ADAPT (Strategia Adattiva con IA)
- **Blu (#2E6FD6):** FISSO (Benchmark Standard)

### Colori Compliance & Adeguatezza
- **Verde (#1E9E63):** Adeguato (85%+) / Conforme
- **Giallo (#E0922F):** Margine (70-85%) / Attenzione
- **Arancio (#D9703A):** Borderline (55-70%) / Avviso
- **Rosso (#D64242):** Non Adeguato (<70%) / Non Conforme

### Colori Regime di Mercato (LED Status)
- **Verde (#16A34A):** Stabilità - Mercati neutral, volatilità bassa
- **Azzurro (#0891B2):** Espansione - Ciclo favorevole, tones positivi
- **Arancio (#D97706):** Warning - Volatilità elevata, monitoring richiesto
- **Rosso (#DC2626):** Critico - Shock di mercato, protezione capitale prioritaria

### Simbologie Comuni
- **LED Pulsante 🔴:** Regime di mercato attivo
- **Badge con ✓:** Valore conforme / soddisfacente
- **Badge con ⚠️:** Valore a rischio / richiede attenzione
- **Barra Verticale Grigia nei Grafici:** Target o benchmark (linea tratteggiata)
- **Scalini (Kaplan-Meier):** Momenti di abbandono clienti

---

## Come Navigare tra le Viste

### Sidebar Sinistro
- **VISTA OPERATIVA:** Bottoni per passare tra le tre dashboard (Banca, Promotore, Cliente)
- **SCENARIO ATTIVO:** Seleziona lo scenario macroeconomico (S0-S4)
- **CRONOLOGIA CONVERSAZIONI:** Storico delle domande poste al Copilota IA

### Topbar Destro
- **Esporta PDF:** Genera report completo con analisi LLM
- **Genera PPTX:** Crea presentazione con grafici e findings
- **Guida & Legenda:** Apre questo modal di aiuto

---

## Tips Finali

1. **Inizia con la Banca:** Per una visione consolidata delle performance e risk
2. **Poi il Promotore:** Per capire le azioni tattiche e segmenti ad alto valore
3. **Infine il Cliente:** Per diagnosticare le relazioni individuali
4. **Usa il Copilota:** Quando i grafici di default non rispondono alla tua domanda specifica
5. **Correla i Grafici:** Usa le metriche di una vista per investigare in un'altra (es., high churn in Banca → verifica fiducia in Cliente)

---

