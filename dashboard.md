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
**Tipo:** Status card  
**Posizione:** Riga 1, colonna 1-12

*(Uguale a quella della Promotore, ma con `client_tip` al posto di `promoter_tip` per fornire suggerimenti dal punto di vista direttivo bancario)*

**A cosa serve dal lato Banca:**
- Comprendere il contesto macroeconomico in cui operano i promotori
- Informare le decisioni della Direttiva Bancaria su allocazione e compliance
- Anticipare necessità di ricalibrazione strategica in base ai regimi di mercato

**Client Tip Bancario Examples:**
- **S0:** "Condizioni regolari. Mantenere la Direttiva standard con focus su acquisizione clienti e compliance"
- **S1:** "Ciclo espansivo. Aumentare allocazione equity con vigilanza su adeguatezza"
- **S2:** "Stress di mercato. Attivare protocolli di protezione capitale e monitoring di adeguatezza rafforzato"

---

### Matrice Vendite e Adeguatezza
**Tipo:** Data table  
**Posizione:** Riga 2, colonna 1-12

**Cosa indica:**
- Aggregazione consolidata delle vendite per categoria di prodotto e cluster clienti
- **Prodotto Proposto:** Categoria (es: Bond Corporate, Azionario, Monetario, Illiquidi, Gov Bond)
- **Cluster Clienti:** Segmento demografico/economico (es: Small HNI, Imprenditori, Privati Conservative)
- **Volume (M€):** Somma raccolta in milioni di euro per quella combinazione prodotto-cluster
- **Adeguatezza %:** Percentuale media di conformità MiFID per quel cluster (0-100%)
- **Status:** Colore badge (verde/ambra/rosso) che riflette il risk compliance

**A cosa serve:**
- Consolidare la view commerciale-compliance dal livello direttivo
- Monitorare il rischio di non-conformità MiFID per segmento
- Identificare cluster a rischio churn o inadeguatezza che necessitano di ribilanciamento
- Tracciare allocazione effettiva vs target della Direttiva

**Come leggerlo:**
1. **Scorri per Volume:** Identifica dove è concentrata la raccolta (prodotto + cluster dominante)
2. **Valuta Adeguatezza:** 
   - Verde (≥85%): Conformità solida, nessun intervento
   - Giallo (70-85%): Margine, monitorare prossime proposte
   - Rosso (<70%): Rischio normativo, necessario intervento sulla Direttiva
3. **Diagnostica:** Cluster con status rosso richiedono:
   - Revisione delle proposte per quella categoria
   - Possibile change della Direttiva Bancaria per quello specifico segmento
   - Comunicazione aggiuntiva al cliente sul razionale

**Interpretazione Tattica:**
- Se un prodotto è sempre rosso, potrebbe essere inadatto al mercato (considerare ritiro)
- Se solo certi cluster hanno problemi, la soluzione è segmentazione più granulare della Direttiva
- Traccia le righe stesse nel tempo per identificare trend di deterioramento

---

### Raccolta Netta — Trend
**Tipo:** Line chart (Chart.js)  
**Posizione:** Riga 3, colonna 1-8

**Cosa indica:**
- Andamento della raccolta netta cumulata su 200 tentativi di proposta
- **Linea verde** = ADAPT (Consulenza IA Adattiva)
- **Linea blu** = FISSO (Strategia Standard)
- Raccolta netta = nuova raccolta da proposte accettate - patrimonio perso per churn

**A cosa serve:**
- Visualizzare il trend di crescita della base patrimoniale gestita dalla banca
- Misurare la divergenza composta tra le due strategie nel lungo periodo
- Identificare se la Consulenza Adattiva sta generando maggior valore sostenuto
- Diagnosticare periodi di stagnazione o contrazione

**Come leggerlo:**
- **Asse X:** 200 tentativi di proposta (sequenziali su 5 scenari)
- **Asse Y:** Raccolta netta cumulata in milioni di euro
- **Linea ADAPT sistematicamente sopra FISSO:** La personalizzazione accumula valore più velocemente
- **Plateau (curva piatta):** Suggerisce necessità di ricalibrazione della Direttiva (stesso approccio non scalabile)
- **Conversione (ADAPT scende sotto FISSO):** Anomalia — possibile degrado della strategia personalizzata
- **Trend in calo:** Recessione percepita dai clienti o loss of trust, richiedere analisi dell'advisor

**Interpretazione Bancaria:**
- La pendenza della linea ADAPT indica la "velocità di crescita" della strategia
- Una divergenza crescente tra ADAPT e FISSO indica effetto composto della personalizzazione (ottimo)
- Se le due linee convergono, l'IA sta diventando simile al benchmark (perdita di valore aggiunto)

---

### 🎯 Performance Strategica Banca
**Tipo:** Radar chart (Plotly)  
**Posizione:** Riga 3, colonna 9-12

**Cosa indica:**
- Valutazione multi-dimensionale della Consulenza Adattiva rispetto al target bancario
- **5 Dimensioni Misurate:**
  1. **Compliance:** % adeguatezza media proposte (target ≥85%)
  2. **Raccolta:** Tasso conversione proposte (target ≥35%)
  3. **Fiducia Cliente:** Sentiment medio post-proposta (target ≥70%)
  4. **Aderenza Direttiva:** Quanto ADAPT segue la strategia dichiarata (target ≥80%)
  5. **Redditività:** Commissioni generate per cliente (target ≥€1000)
- **Linea verde** = Performance ADAPT effettiva
- **Linea grigia tratteggiata** = Target bancario per quella dimensione

**A cosa serve:**
- Valutare la salute complessiva della Consulenza Adattiva in uno sguardo
- Identificare quale dimensione è collo di bottiglia
- Monitorare se la strategia personalizzata rispetta i vincoli bancari
- Diagnosticare se serve ricalibrazione della Direttiva

**Come leggerlo:**
- **Se la linea verde è dentro il grigio:** Quella dimensione è conforme al target
- **Se la linea verde sporge:** Superperformance in quella area (positivo)
- **Se la linea verde è rientrante (dentro il grigio):** Underperformance, necessario intervento
- **Lettura generale:** Un radar "stellato" (tutto dentro) = salute ottima. Un radar "bucherellato" = aree critiche

**Dimensioni Critiche per Priorità:**
1. **Compliance:** Prima priorità assoluta (implicazioni normative)
2. **Raccolta:** Secondo (sostenibilità economica)
3. **Fiducia:** Terzo (sostenibilità relazionale)
4. **Aderenza & Redditività:** Indicatori di efficienza tattica

---

### 📊 Visualizzazioni Avanzate Plotly (Banca)

#### Mappa di Valore (Patrimonio Gestito vs Profilo Rischio)
**Tipo:** Heatmap Plotly interattiva  
**Posizione:** Riga 4, colonna 1-6

*(Uguale a quella della Promotore)*

**Cosa indica:**
- Grid di cluster clienti (es: 4×5 = 20 cluster)
- Colore indica il vantaggio percentuale di ADAPT vs FISSO in quella zona
- Rosso: FISSO domina; Giallo/Arancio: parità o piccoli vantaggi; Verde: ADAPT domina

**Interpretazione dal Lato Banca:**
- Identifica segmenti di clientela dove l'investimento in Consulenza Adattiva genera massimo ROI
- Aree rosse sono "fortini" del benchmark — valutare se la Direttiva ha limitazioni di segmentazione
- Aree verdi sono opportunità di focalizzazione commerciale

---

#### Analisi Contribuzione Patrimonio Gestito
**Tipo:** Waterfall chart Plotly  
**Posizione:** Riga 4, colonna 7-12

**Cosa indica:**
- Scomposizione del patrimonio gestito finale nei componenti contributivi:
  1. **AUM Iniziale:** Patrimonio al Round 1 (baseline)
  2. **Nuova Raccolta:** Somma dei netti da proposte accettate (positivo)
  3. **Effetto Mercato:** Gain/Loss da performance di mercato sui portafogli (può essere negativo in recessione)
  4. **Abbandoni Clienti:** Patrimonio perso per churn (sempre negativo)
  5. **AUM Finale:** Patrimonio gestito al Round 20 (risultato netto)

**A cosa serve:**
- Diagnosticare quali fattori hanno guidato la crescita o contrazione patrimoniale
- Capire se il problema è nel business (raccolta insufficiente) o nei mercati (drawdown)
- Quantificare l'impatto relativo di ogni fattore sul risultato finale
- Identificare il driver principale di performance: raccolta, mercato, o retention?

**Come leggerlo:**
- **Barre verdi:** Contributi positivi (Raccolta)
- **Barre rosse:** Contributi negativi (Abbandoni, Effetto Mercato)
- **Altezza della barra:** Importanza relativa del fattore (barra più alta = impatto maggiore)
- **Sequenza:** Leggi da sinistra a destra per tracciare il "percorso" verso il risultato finale

**Interpretazione Bancaria:**
- Se "Abbandoni Clienti" è una barra rossa enorme, il churn è il principale limitante
- Se "Effetto Mercato" è fortemente negativo, il mercato ha trascinato giù i portafogli (oltre controllo della banca)
- Se "Nuova Raccolta" è insufficiente, le proposte non stanno convertendo a sufficienza
- Il waterfall di ADAPT vs FISSO mostra quale strategia ha gestito meglio questi fattori

---

#### Evoluzione Performance Cumulata (200 Tentativi di Proposta)
**Tipo:** Multi-line chart Plotly  
**Posizione:** Riga 5, colonna 1-12

**Cosa indica:**
- Trend di performance cumulata ADAPT vs FISSO su tutti i 200 tentativi
- Ogni punto rappresenta il KPI aggregato (es: commissioni, raccolta, fiducia media) al tentativo N
- **Linea verde** = ADAPT
- **Linea blu** = FISSO

**A cosa serve:**
- Visualizzare la traiettoria strategica complessiva della banca
- Identificare "inflection points" dove una strategia inizia a vincere
- Diagnosticare se la performance differenziale è persistente (real) o casuale (noise)
- Misurare il "valore composto" della personalizzazione nel tempo

**Come leggerlo:**
- **Se ADAPT è sempre sopra FISSO:** La Consulenza Adattiva vince stabilmente (scenario ideale)
- **Se le linee si incrociano:** Una strategia era vincente all'inizio ma ha perso momentum (anomalia, richiede diagnosi)
- **Se la divergenza aumenta:** L'effetto composto della personalizzazione si sta amplificando (excellente)
- **Se la divergenza diminuisce:** Le due strategie stanno convergendo (personalizzazione sta perdendo efficacia)
- **Picchi anomali:** Possono indicare shock di mercato (controllare Regime di Mercato nello stesso round)

**Interpretazione Strategica:**
- Una linea ADAPT che "fugge via" dal FISSO suggerisce che la Direttiva personalizzata è molto efficace
- Un "canale" stretto tra ADAPT e FISSO (linee parallele) suggerisce che l'IA non sta aggiungendo valore differenziale
- Incroci multipli suggeriscono volatilità nella strategia — potrebbe essere necessaria maggior stabilità

---

---

## Dashboard del Cliente

### 🤖 Copilota IA
*(Vedere sezione Dashboard del Promotore — è lo stesso componente)*

---

### 📍 Regime di Mercato (Market Regime Card)
**Tipo:** Status card  
**Posizione:** Riga 1, colonna 1-12

*(Uguale a quelle della Banca e Promotore, ma con `client_tip` specifico per il cliente finale)*

**Cosa indica:**
- Il regime macroeconomico attuale in cui il cliente opera
- Contesto per interpretare la performance del suo portafoglio
- Suggerimento personalizzato per il cliente su cosa aspettarsi

**Client Tip Examples (Comunicazione al Cliente):**
- **S0:** "Condizioni di mercato regolari. Il tuo portafoglio segue l'asset allocation strategica programmata. Continua a mantenere una prospettiva a lungo termine."
- **S1:** "Ciclo favorevole ai mercati. Il tuo portafoglio è allineato a un risk-on moderato con diversificazione. Monitoraggio regolare mantiene il controllo."
- **S2:** "Fase di aggiustamento dei tassi di interesse. Abbiamo aumentato il monitoraggio attivo della componente obbligazionaria. Questa è una strategia difensiva consigliata."
- **S3:** "Fase di instabilità tecnica dei mercati. Ti consigliamo di mantenere stabilità emotiva e focus sul lungo termine. Le fluttuazioni sono normali in questo contesto."

**A cosa serve:**
- Rassicurare il cliente sul contesto della sua performance
- Spiegare le decisioni di portafoglio in relazione al regime macroeconomico
- Impostare aspettative realistiche sulla performance

---

### 📊 Intelligence Cliente — KPI Medi & Distribuzione Portafoglio
**Tipo:** 4 KPI cards + Data table  
**Posizione:** Riga 2, colonna 1-12

**Cosa indica (4 KPI):**
1. **Fiducia Media (ADAPT):** Sentiment medio del cliente con Consulenza Adattiva (0-100%)
2. **Fiducia Media (FISSO):** Sentiment medio del cliente con Strategia Standard (0-100%)
3. **Tasso Accettazione (ADAPT):** % proposte accettate dal cliente con Consulenza Adattiva
4. **Tasso Accettazione (FISSO):** % proposte accettate dal cliente con Strategia Standard

**Cosa indica (Tabella):**
- **Profilo di Rischio:** Categoria del cliente (Conservative, Moderate, Growth, Aggressive, etc.)
- **Accettazione ADAPT:** % di proposte accettate quando proposte con Consulenza Adattiva
- **Accettazione FISSO:** % di proposte accettate quando proposte con Strategia Standard
- **Dominanza:** Quale strategia il cliente preferisce (badge verde ADAPT o blu FISSO)

**A cosa serve:**
- Capire immediatamente se il cliente è più felice con la Consulenza Adattiva o con il benchmark
- Identificare quali profili di rischio beneficiano più dalla personalizzazione
- Diagnosticare se la strategia personalizzata sta creando valore per quel segmento di clientela

**Come leggerlo:**
- **KPI Cards:** Se ADAPT Fiducia > FISSO Fiducia, il cliente preferisce l'approccio personalizzato
- **Tabella:** 
  - Colore verde nella colonna ADAPT = strategia personalizzata più efficace per quel profilo
  - "Dominanza: ADAPT" = personalizzazione sta pagando per quel segmento
  - "Dominanza: FISSO" = il benchmark è più efficace (possibile sovra-personalizzazione o inadeguatezza)

**Interpretazione Strategica:**
- Se tutti i profili hanno "Dominanza: ADAPT", la Consulenza Adattiva è vincente su tutta la base
- Se solo certi profili preferiscono ADAPT, la segmentazione della Direttiva è efficace
- Se un profilo "Conservative" preferisce FISSO, potrebbe significare che ADAPT è troppo rischioso per quel segmento

---

### 🧠 Radar Sentiment Clienti
**Tipo:** Radar chart Plotly  
**Posizione:** Riga 3, colonna 1-12

**Cosa indica:**
- Profilo multi-dimensionale del sentiment del cliente medio
- **5 Dimensioni Misurate:**
  1. **Soddisfazione Comunicazione:** Quanto il cliente si sente ascoltato e compreso (0-100%)
  2. **Alignment Aspettative:** Quanto il portafoglio rispecchia le aspettative iniziali (0-100%)
  3. **Fiducia nel Promotore:** Livello di confidenza relazionale (0-100%)
  4. **Percezione Performance:** Come il cliente percepisce la performance del suo portafoglio vs benchmark (0-100%)
  5. **Comfort sulla Compliance:** Quanto il cliente si sente sicuro che il portafoglio sia conforme alle sue esigenze (0-100%)

**A cosa serve:**
- Diagnosticare "quali" aspetti della relazione stanno funzionando e quali no
- Identificare leve di miglioramento della soddisfazione cliente
- Comparare il profilo ADAPT vs FISSO per valutare l'impatto della personalizzazione

**Come leggerlo:**
- **Tutti i raggi verso l'esterno (stella ampia):** Cliente molto soddisfatto su più dimensioni
- **Raggi irregolari (stella storta):** Alcune aree forti, altre critiche
- **Raggi corti e rientranti:** Cliente insoddisfatto su molte dimensioni (allarme churn)
- **ADAPT radar ampio vs FISSO radar stretto:** La personalizzazione sta migliorando il profilo di soddisfazione

**Dimensioni Critiche per Priorità:**
1. **Fiducia nel Promotore:** Se crolla, il cliente abbandona (assoluta priorità)
2. **Alignment Aspettative:** Se non è allineato, il cliente percepisci un scostamento importante
3. **Soddisfazione Comunicazione:** Se bassa, il promotore non sta comunicando efficacemente
4. **Comfort Compliance:** Importante per la retention a lungo termine

---

### 🗺️ Heatmap Propensione al Rischio per Cluster
**Tipo:** Grid di celle colorate (4 righe × 5 colonne)  
**Posizione:** Riga 4, colonna 1-12

**Cosa indica:**
- Griglia che mostra la propensione al rischio media dei clienti in ogni cluster
- **Assi:**
  - **Righe:** Profilo di Rischio (Conservative, Moderate, Growth, Aggressive)
  - **Colonne:** Segmento di Patrimonio (Basso, Medio-Basso, Medio, Medio-Alto, Alto)
- **Colore cella:** Propensione al rischio media (0-100%) — verde chiaro, arancio, rosso scuro
- Ogni cella rappresenta "l'incrocio" tra profilo e patrimonio

**A cosa serve:**
- Monitorare se il profilo di rischio dei clienti sta evolvendo nel tempo
- Identificare cluster dove la propensione al rischio è crollata (possibile stress o shock)
- Diagnosticare se la comunicazione della banca sta mantenendo stabile la risk tolerance
- Identificare cluster "critici" dove il cliente è avverso al rischio ma il portafoglio potrebbe essere troppo aggressivo

**Come leggerlo:**
- **Cella verde intenso (85%+):** Cluster con alta propensione al rischio, opportunità per prodotti equity/growth
- **Cella gialla/arancio (40-85%):** Cluster con rischio moderato, allocazione balanced appropriate
- **Cella rossa (<40%):** Cluster avverso al rischio, prodotti conservativi necessari
- **Pattern di riga:** Leggi per profilo — tutti green = segmento stabile e coerente; alternanza rosso-verde = volatilità
- **Pattern di colonna:** Leggi per patrimonio — high-net-worth dovrebbe avere maggior propensione

**Interpretazione Tattica:**
- Celle rosse indicano cluster dove la proposta standard fallisce → priorità per la Consulenza Adattiva
- Uniformità di colore lungo una riga = coerenza del profilo
- Scatter colors lungo una riga = volatilità o incertezza del cliente su quel profilo
- Comparazione ADAPT vs FISSO: se ADAPT ha meno celle rosse, la personalizzazione sta funzionando

**Deduzione Pratica:**
- Se "Aggressive + Alto Patrimonio" è rosso, i clienti ricchi stanno diventando avversi al rischio (anomalia, possibile shock di mercato)
- Se "Conservative + Basso Patrimonio" è sempre rosso, è una caratteristica naturale di quel segmento
- Se una cella era verde e diventa rossa, è un segnale di deterioramento della fiducia in quel cluster

---

### Evoluzione Fiducia
**Tipo:** Line chart (Chart.js)  
**Posizione:** Riga 5, colonna 1-6

**Cosa indica:**
- Fiducia media del cliente su scala 0-100% lungo i 200 tentativi di proposta
- Curva è una media mobile a 15 periodi per eliminare il rumore giornaliero
- **Linea solida viola** = valore effettivo
- **Area sottostante** = banda di fiducia (per visualizzare il range)

**A cosa serve:**
- Tracciare il "polso" della qualità della relazione cliente nel tempo
- Identificare momenti critici dove la fiducia crolla bruscamente
- Diagnosticare se la comunicazione e le decisioni di portafoglio stanno funzionando
- Anticipare churn analizzando il trend di fiducia

**Come leggerlo:**
- **Asse X:** 200 tentativi di proposta (sequenziali nei 5 scenari)
- **Asse Y:** Fiducia % (0-100%)
- **Trend crescente:** Comunicazione efficace e soddisfazione aumentante (positivo)
- **Trend piatto:** Stabilità nella relazione, mantenimento dello status quo
- **Trend decrescente lento:** Graduale erosione della fiducia (allarme giallo)
- **Calo improvviso (scalino verticale):** Perdita di fiducia acuta da evento specifico

**Cause di Crolli di Fiducia:**
1. **Inadeguatezza percepita:** Cliente riceve una proposta non coerente con il suo profilo
2. **Shock di mercato non comunicato:** Performance negativa che il cliente non si aspettava
3. **Proposta conforme ma non desiderata:** Prodotto adatto ma non gradito (es: troppo conservativo)
4. **Mancanza di comunicazione proattiva:** Promotore non spiega il razionale delle scelte

**Interpretazione per Deduzione:**
- Se rimane sopra 75%, relazione è salda — cliente tollerante
- Se scende sotto 50%, rischio concreto e imminente di abbandono
- Se rimane sotto 60%, cliente è insoddisfatto e probabilmente lascerà entro 1-2 mesi
- Confronta ADAPT vs FISSO: se ADAPT fiducia > FISSO fiducia, la personalizzazione sta guadagnando fiducia

**Azioni Consigliate:**
- Se cala velocemente, contatta cliente proattivamente per capire le ragioni
- Se rimane bassa, valuta ribilanciamento del portafoglio o cambio di promotore
- Se sale velocemente, il promotore ha fatto un buon lavoro di comunicazione/rassicurazione

---

### Allineamento Profilo vs Portafoglio
**Tipo:** Radar chart (Chart.js)  
**Posizione:** Riga 5, colonna 7-12

**Cosa indica:**
- Comparazione tra profilo dichiarato del cliente e portafoglio effettivo ricevuto
- **5 Dimensioni di Preferenza Cliente:**
  1. **Rischio:** Tolleranza al rischio (0-100%)
  2. **Orizzonte Temporale:** Lunghezza dell'investimento (0-100%, dove 100%=lungo termine)
  3. **Liquidità:** Necessità di accesso ai fondi (0-100%, dove 100%=bassa liquidità tollerata)
  4. **Rendimento Atteso:** Aspettative di return (0-100%)
  5. **Conoscenza Finanziaria:** Sofisticazione dell'investitore (0-100%)

- **Linea blu:** Profilo dichiarato del cliente (da assessment iniziale/primo incontro)
- **Linea verde:** Portafoglio effettivo riflesso nei prodotti proposti

**A cosa serve:**
- Verificare che le decisioni di portafoglio rispettino il profilo del cliente (compliance)
- Identificare aree di disallineamento che potrebbero causare insoddisfazione o violazioni normative
- Diagnosticare dove la comunicazione dei prodotti ha fallito
- Comparare ADAPT vs FISSO per valutare quale strategia è più "conforme"

**Come leggerlo:**
- **Se le aree coincidono (blu = verde):** Cliente è perfettamente soddisfatto, portafoglio è allineato
- **Se il blu è DENTRO il verde (verde sporge):** Portafoglio è più aggressivo/rischioso del profilo
  - Possibile violazione MiFID (prodotto non adatto)
  - Cliente potrebbe essere scontento (portafoglio oltre comfort)
  - **Urgenza: ALTA** — necessario intervento per compliance e soddisfazione
- **Se il verde è DENTRO il blu (blu sporge):** Portafoglio è più conservativo del profilo
  - Cliente può percepirsene underserved (aspettative non incontrate)
  - Possibile underperformance percepita (rendimento inferiore alle attese)
  - **Urgenza: Media** — valutare se ribilanciare verso risk-on
- **Discrepanze specifiche:**
  - **Su "Rischio":** Urgenza massima (compliance + soddisfazione)
  - **Su "Rendimento":** Necessità di gestione aspettative (comunicazione della banca)
  - **Su "Liquidità":** Possibile lock-in sui prodotti illiquidi non graditi
  - **Su "Orizzonte Temporale":** Cliente potrebbe ritirare fondi prima della scadenza pianificata

**Interpretazione Radar per Cluster:**
- Un radar "perfetto" è un cerchio regolare (tutte le aree uguali tra blu e verde)
- Un radar "sbilanciato" suggerisce segmentazione incomplete della Direttiva
- Se ADAPT radar è più simmetrico di FISSO radar, la personalizzazione sta migliorando l'allineamento

**Azioni Consigliate:**
- Se il verde sporge molto su "Rischio," contatta cliente per rassicurazione o ribilanciamento
- Se il blu sporge su "Rendimento," comunica più chiaramente le attese di return realistiche
- Se il radar è "storto" asimmetricamente, potrebbe essere necessaria una consulenza finanziaria aggiuntiva al cliente

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

## 🆕 Nuove Funzionalità Implementate

### 📊 Chart Explanation Modal — Spiegazione LLM dei Grafici

**Cosa è:**
- Nuova funzionalità che permette di cliccare su **qualsiasi grafico** nella dashboard per ottenere una spiegazione contestuale generata dall'IA

**Come funziona:**
1. Clicca su un grafico (qualsiasi canvas Chart.js o div Plotly)
2. Si apre un **modal con sfondo scuro** al centro dello schermo
3. Il modal mostra:
   - **Titolo del grafico:** Nome del grafico cliccato
   - **Loading spinner:** Mentre l'IA analizza (2-5 secondi)
   - **Spiegazione completa:**
     - Come si legge il grafico (2-3 frasi)
     - Interpretazione dei dati attuali nello scenario selezionato (3-4 frasi)
     - Raccomandazione strategica concreta (2 frasi)

**Stile:**
- Sfondo: Dark mode (#111A24) con border verde (#1FA463)
- Blur effect sul backdrop
- Facilmente chiudibile con bottone "✕"

**Grafici supportati (13+):**
- Vista Banca: `bRaccolta`, `plotly-heatmap`, `plotly-waterfall`, `plotly-lines`, `plotly-spider-banca`
- Vista Promotore: `pCompliance`, `pAccept`, `plotly-heatmap-promotore`, `plotly-sopravvivenza`
- Vista Cliente: `cFiducia`, `cRadar`, `spider-sentiment-clienti`
- Grafici AI dinamici: `plotly-ai-N` (tutti i grafici consigliati dal Copilota)

**Vantaggi:**
- Riduce la necessità di consultare questa guida durante l'uso
- Spiegazioni personalizzate al scenario corrente
- Feedback immediato sull'interpretazione del grafico

---

### 🔄 Data-Driven Updates — Grafici Statici Convertiti a Data-Driven

**Cosa è cambiato:**
Tutti i grafici della dashboard che precedentemente usavano dati hardcoded, sintetici o Math.random() sono stati convertiti per leggere direttamente da **MongoDB in tempo reale**.

**Grafici Aggiornati:**

#### Vista Cliente
1. **cFiducia (Evoluzione Fiducia)**
   - **Prima:** Math.random() * 40 + 20 (falso)
   - **Dopo:** Legge da `/api/charts/fiducia-evolution` (MongoDB)
   - **Cambio:** Data-driven con fallback a zeri

2. **cRadar (Profilo vs Portafoglio)**
   - **Prima:** Hardcoded [35, 60, 70, 45, 50] e [40, 58, 75, 48, 50]
   - **Dopo:** Legge da `/api/charts/profilo-portafoglio` (MongoDB)
   - **Cambio:** Data-driven con fallback a zeri

3. **Heatmap Propensione Rischio**
   - **Prima:** Hardcoded con matrice statica
   - **Dopo:** Legge da `/api/charts/risk-propensity-heatmap` (MongoDB)
   - **Cambio:** Nuova ref `heatmapReale` con caricamento asincrono

#### Vista Banca
1. **bRadar (Performance Strategica Banca)**
   - **Prima:** Hardcoded [80, 90, 20, 10, 85] e [65, 80, 35, 15, 70]
   - **Dopo:** Legge da `/api/charts/radar-banca-direttiva` (MongoDB)
   - **Cambio:** Data-driven con fallback a zeri

2. **plotly-lines (Evoluzione Performance Cumulata)**
   - **Prima:** Sintetico con formula [i**1.2 * 10000]
   - **Dopo:** Legge da `/api/charts/performance-lines` che estrae dati da MongoDB
   - **Cambio:** Data-driven con fallback a zeri

#### Vista Promotore
1. **pCompliance (Conformità)**
   - **Prima:** Math.random() * 20 + 70 come fallback
   - **Dopo:** Fallback a **zeri** (non sintetici)

2. **pAccept (Proposte Accettate)**
   - **Prima:** Math.random() * 10 + 5 e Math.random() * 5 + 2 come fallback
   - **Dopo:** Fallback a **zeri** (non sintetici)

**Conseguenze:**
- ✅ Tutti i grafici cambiano automaticamente al cambio dello scenario
- ✅ Nessun dato inventato — fallback è "0", non sintetico
- ✅ Accuratezza 100% con i dati reali da MongoDB
- ✅ Performance stabile anche con MongoDB lento

---

### 🆕 Nuovi Endpoint API

#### 1. `/api/charts/fiducia-evolution` (GET)
**Cosa legge:**
- Fiducia media per round dal documento MongoDB
- Distingue ADAPT (dai promotori con "ADAPT" nel nome) vs FISSO (dai promotori con "FISSO")

**Ritorna:**
```json
{
  "labels": ["R1", "R2", ..., "R200"],
  "fiducia_adapt": [45.5, 46.2, ..., 52.1],
  "fiducia_fisso": [42.1, 43.5, ..., 48.9]
}
```

---

#### 2. `/api/charts/profilo-portafoglio` (GET)
**Cosa legge:**
- Profilo dichiarato del cliente vs portafoglio assegnato ADAPT
- 5 dimensioni: Rischio, Orizzonte, Liquidità, Rendimento, Conoscenza

**Ritorna:**
```json
{
  "profilo_dichiarato": [35, 60, 70, 45, 50],
  "portafoglio_assegnato": [40, 58, 75, 48, 50],
  "labels": ["Rischio", "Orizzonte", "Liquidità", "Rendimento", "Conoscenza"]
}
```

---

#### 3. `/api/charts/risk-propensity-heatmap` (GET)
**Cosa legge:**
- Propensione al rischio per cluster (4 profili × 5 livelli patrimonio)
- Accettazione cliente media per combinazione profilo-patrimonio

**Ritorna:**
```json
{
  "matrice": [
    [88, 82, 75, 70, 65],
    [91, 85, 79, 73, 68],
    [78, 72, 66, 58, 48],
    [62, 54, 44, 32, 22]
  ]
}
```

---

#### 4. `/api/charts/radar-banca-direttiva` (GET)
**Cosa legge:**
- Portafoglio target fisso vs allocation attuale ADAPT
- 5 asset class: Bond Corp, Monetario, Azionario, Illiquidi, Gov Bond

**Ritorna:**
```json
{
  "target": [80, 90, 20, 10, 85],
  "attuale": [75.3, 88.2, 22.1, 11.5, 83.7]
}
```

---

#### 5. `/api/charts/performance-lines` (POST) — AGGIORNATO
**Cosa legge (AGGIORNATO):**
- **Prima:** Usava `storico_raccolta_adattivo` dal payload (sintetico)
- **Dopo:** Legge da MongoDB e calcola la raccolta cumulata per ogni round

**Logica:**
1. Estrae scenario_id da metrics
2. Queries MongoDB per il documento della simulazione
3. Itera sui rounds ordinati
4. Per ogni round e promotore, calcola:
   - Raccolta se strategia ADAPT e cliente accetta
   - Raccolta se strategia FISSO e cliente accetta
5. Accumula cumulativamente
6. Fallback: zeri se MongoDB è vuoto

**Ritorna:**
```json
{
  "data": "<Plotly JSON with data: [{x: [...], y: [...], type: 'scatter'}]>"
}
```

---

### 📝 Fallback Strategy

Tutti gli endpoint segue la stessa logica **"Zero Fallback"**:

```
Se MongoDB ha dati → usa quelli
Se MongoDB è vuoto → ritorna array di zeri (non dati sintetici)
```

**Vantaggi:**
- Impossibile "inventare" un trend che non esiste
- Se MongoDB è down, il grafico appare vuoto (non fuorviante)
- Facilita il debugging di problemi di data loading

---

---

## Tips Finali

1. **Inizia con la Banca:** Per una visione consolidata delle performance e risk
2. **Poi il Promotore:** Per capire le azioni tattiche e segmenti ad alto valore
3. **Infine il Cliente:** Per diagnosticare le relazioni individuali
4. **Usa il Copilota:** Quando i grafici di default non rispondono alla tua domanda specifica
5. **Correla i Grafici:** Usa le metriche di una vista per investigare in un'altra (es., high churn in Banca → verifica fiducia in Cliente)

---

