# DIAGNOSI — Anomalia PROM-ADAPT-1 (dataset fix8, 200 round)

> **Nota:** questo report sostituisce `diagnosi_anomalia_adapt.md`, che è **obsoleto**.
> Quel report descriveva la versione pre-fix (dataset fix5) in cui:
> - i clienti erano **segregati** (FISSO gestiva righe 0-1, ADAPT righe 2-3);
> - `calcola_reazione_clienti` usava `adeguatezza_score` diretto (senza componente dinamica);
> - `clienti_salvati_dal_churn` era **sempre 0**.
>
> Tutti e tre questi punti **sono già stati modificati nel codice attuale** (vedi §5). La
> diagnosi qui sotto è rifatta da zero sul codice e sui dati di fix8.

---

## 0. Sommario esecutivo

ADAPT continua a perdere contro FISSO in **tutti** gli scenari fix8, e il divario
**peggiora quanto più lo scenario è "difficile"**:

| Scenario | valore_aggiunto_personalizzazione | conv. ADAPT | conv. FISSO | delta_fid ADAPT | delta_fid FISSO |
|----------|-----------------------------------|-------------|-------------|-----------------|-----------------|
| S0_fix8  | **−35.9**  | 96.2% | 96.8% | +0.00263 | +0.00266 |
| S1_fix8  | **−13.2**  | 91.5% | 96.5% | +0.0023  | +0.0027  |
| S2_fix8  | **−158.6** | 82.1% | 93.9% | +0.00134 | +0.00246 |

La causa **non è la qualità dell'LLM**. È strutturale, e si riassume in una frase:

> **La funzione di reward (adeguatezza) non ha alcun asse "scenario". L'adeguatezza
> dipende solo da `(profilo_rischio, prodotto)`. Quindi "adattarsi allo scenario" — l'unica
> cosa che ADAPT fa in più — è letteralmente invisibile al punteggio. Peggio: dato che
> `Bond_Corporate` (il bias fisso di FISSO) è l'UNICO prodotto sicuro per tutti i profili,
> qualunque deviazione di ADAPT può solo pareggiare o perdere, mai vincere in modo affidabile.**

---

## 1. Catena causale: da decisione LLM a numero finale

Ogni trasformazione, con file e riga.

### Step 1 — L'LLM sceglie il prodotto
`promotore_agent.py:138-186` — `genera_strategia_cluster()`
- **Entrambi** i promotori passano dallo stesso path LLM. FISSO **non è hardcoded**:
  è un LLM con `adattativo=False` e `bias_prodotto="Bond_Corporate"` nel system prompt
  (`_build_system_prompt`, riga 213-239). La sua "fissità" è *soft*: nei dati sceglie
  Bond_Corporate nel 92% dei cluster in S0 e nel 77% in S2.
- Output: `prodotto_suggerito` come stringa raw (es. `"Obbligazioni corporate IG"`), più
  `strategia` e `approccio_comunicativo`. Sanitizzazione lista/dict alle righe 171-186;
  fallback `'Altro'` se vuoto.

### Step 2 — Normalizzazione
`normalizzatore.py:9-99` — `normalize_prodotto()`
- Substring matching case-insensitive → una delle 10 categorie canoniche, altrimenti `"Altro"`.
- **Leak strutturale:** ogni frase che i pattern non catturano diventa `"Altro"` →
  adeguatezza 0.0 (vedi Step 3). Nei dati: **3.2%–5.1% di "Altro" per FISSO, 3.8%–4.5% per ADAPT**.

### Step 3 — Adeguatezza (statica → "dinamica")
`simulation_engine.py:343-363`
1. `adeguatezza_base = ADEGUATEZZA_MATRIX[profilo_prevalente][prodotto_norm]` (default 0.0).
   La matrice (righe 25-74) è **lookup puro 4 profili × 10 prodotti**. **Non contiene nessun
   asse scenario** (tassi, liquidità, crisi, direttiva non entrano MAI nel punteggio).
2. `calcola_adeguatezza_dinamica()` (righe 80-122) aggiunge ritocchi minimi:
   `acceptance_boost = 0.01·min(acceptance_count,10)` (max +0.1),
   `recovery_bonus = +0.02` se `fiducia<0.3 AND base≥0.7`,
   `stagnation_malus = −0.02` se `refusal_streak≥3`.
3. `adeguatezza_score` = media per-cliente; `accettato = score ≥ 0.5` (`SOGLIA_ACCETTAZIONE`).

### Step 4 — Reazione clienti (delta fiducia)
`simulation_engine.py:635-660` — `calcola_reazione_clienti()`, funzione a gradini:
| adeguatezza_dinamica | delta_fiducia |
|----------------------|---------------|
| ≥ 0.8 | **+0.05** |
| ≥ 0.5 | **+0.02** |
| ≥ 0.3 | **−0.01** |
| < 0.3 | **−0.04** |

E **in aggiunta**, a livello di cluster (`esegui_round`, righe 383-399): se `accettato==False`
(cioè score cluster < 0.5) viene applicato `MALUS_FIDUCIA_RIFIUTO = −0.15` a **tutti** i
clienti del cluster. Quindi un cluster sotto-soglia paga **due volte**: `−0.04` per-cliente
**+** `−0.15` di malus ≈ **−0.19** in un round.

### Step 5 — Metriche di business
`simulation_engine.py:777-1087` — `_calcola_metriche_business()`
- `valore_aggiunto_personalizzazione` (riga 871) = Σ round `(sodd_adapt − sodd_fisso)`.
- `soddisfazione = delta_fiducia · 0.5` (riga 652): soddisfazione e fiducia sono **collineari**,
  non due segnali indipendenti.
- `fiducia_cumulata`, `tasso_conversione`, `mismatch_rate`, `clienti_salvati_dal_churn` (§3).

---

## 2. Il punto ESATTO di impossibilità strutturale

### Prova A — Bond_Corporate è il prodotto DOMINANTE per costruzione ✅ CONFERMATA
Calcolando il **minimo** dell'adeguatezza di ogni prodotto sui 4 profili
(SOGLIA accettazione = 0.5):

```
Bond_Corporate    min=0.5  (C=0.5, B=0.8, G=1.0, A=0.7)  <-- UNICO sicuro ovunque (>=0.5)
Bond_Sovereign    min=0.3
Real_Estate       min=0.3
Cash_Equivalents  min=0.2
ETF_Tematici      min=0.2
Polizze           min=0.1
Mixed_Funds       min=0.1
Fondi_Azionari    min=0.1
Derivati          min=0.0
```

`Bond_Corporate` è **l'unico prodotto che non scende mai sotto la soglia di accettazione per
nessun profilo**. È esattamente il `bias_prodotto` di FISSO. **FISSO è stato dotato della
strategia dominante del gioco.** Giocando sempre Bond_Corporate, non attiva quasi mai il malus
`−0.15` (solo sul 3-6% di allucinazioni "Altro"). Qualunque cosa faccia ADAPT:
- sui profili dove BC è già in fascia alta (Balanced 0.8, Growth 1.0) → **può solo pareggiare**;
- sui profili dove BC è in fascia media (Conservative 0.5, Aggressive 0.7) → **potrebbe** battere
  BC (es. Bond_Sovereign 0.9 su Conservative), ma solo se sceglie *perfettamente* e *senza mai*
  scendere sotto soglia.

### Prova B — l'adeguatezza NON ha dimensione dinamica di scenario ✅ CONFERMATA
`ADEGUATEZZA_MATRIX` = `f(profilo, prodotto)`. Lo stato macro (S0…S4), la direttiva, il round,
la storia del cliente **non entrano nel punteggio**. Conseguenza: "adattarsi allo scenario" non
produce alcun segnale positivo misurabile. La componente "dinamica"
(`calcola_adeguatezza_dinamica`) **non crea un canale di ricompensa per l'adattamento**: è quasi
inerte (la fiducia parte a 0.5 e sale, quindi `recovery_bonus` scatta di rado) e il
`acceptance_boost` premia **la costanza** — quindi favorisce FISSO, non ADAPT.

### Prova C — perché il divario ESPLODE in crisi (S2) — la prova del meccanismo ✅
Il dato più eloquente di S2_fix8:

| | adeguatezza media | delta_fid medio | cluster negativi |
|---|---|---|---|
| FISSO | 0.828 | **+0.00246** | 6.1% |
| ADAPT | 0.821 | **+0.00134** | **15.7%** |

**Adeguatezza media quasi identica, ma ADAPT ha delta dimezzato e 2.5× cluster negativi.**
Perché? Perché il reward è una **scogliera asimmetrica**: upside max +0.05, downside −0.19 quando
si scende sotto 0.5. In S2 la direttiva spinge "flight to quality" (Cash/Sovereign). ADAPT
obbedisce e, sui profili **Growth/Aggressive**, sceglie prodotti che la matrice punisce:
- `Cash_Equivalents` → Aggressive 0.2 (−0.04 + malus), Growth 0.3 (−0.01 + malus)
- `Bond_Sovereign` → Aggressive 0.3 (−0.01 + malus)

FISSO invece **ignora la direttiva** e resta su Bond_Corporate (0.7-1.0 su Growth/Aggressive) →
resta sicuro ovunque. **ADAPT viene punito per aver fatto la cosa "giusta" rispetto allo scenario,
perché lo scorer non vede lo scenario.** A parità di adeguatezza media, la politica a varianza più
alta perde sistematicamente per via della scogliera.

**Conclusione §2:** non è che ADAPT *non possa mai* battere FISSO in astratto (in S0 una politica
perfetta lo batterebbe di poco su Conservative/Aggressive). È che il design rende il margine
minuscolo e a somma negativa: reward cieco allo scenario + prodotto dominante regalato a FISSO +
penalità asimmetrica che punisce ogni deviazione + leak "Altro". Il risultato atteso è
esattamente quello osservato.

---

## 3. Perché `clienti_salvati_dal_churn` era sempre 0 (e cosa è cambiato)

Codice: `simulation_engine.py:858-861`
```python
if coords in mappa_fisso:
    delta_fid_adapt = strat.get('delta_fiducia_medio', 0.0)
    if mappa_fisso[coords] < 0 and delta_fid_adapt >= 0:
        metrics["clienti_salvati_dal_churn"] += 1
```
Servono **due** condizioni: (1) `coords in mappa_fisso` e (2) `mappa_fisso[coords] < 0`
(FISSO in calo su quel cluster in quel round).

**Nella versione che conosci (fix5) era impossibile per DUE motivi:**
1. **Segregazione:** FISSO e ADAPT gestivano cluster diversi → le `coords` di ADAPT non
   comparivano mai in `mappa_fisso` → condizione (1) sempre falsa.
2. Anche se avessero condiviso i cluster, FISSO giocando Bond_Corporate (≥0.5 ovunque) non
   andava **mai** negativo → condizione (2) sempre falsa.

Verifica dati: `S0_fix5=0, S1_fix5=0, S2_fix5=0`.

**In fix8 non è più 0** (`S0=106, S1=98, S2=157`) perché il fix A/B (§5) ha reso i cluster
condivisi (condizione 1 ora vera) e FISSO ora va occasionalmente negativo (sulle allucinazioni
"Altro" e, in S2, quando talvolta segue la direttiva Cash su profili aggressivi).

**Attenzione però:** la metrica resta **concettualmente illusoria** anche quando è > 0. Nel
modello **non esiste alcun meccanismo di churn/abbandono**: nessun cliente viene mai rimosso o
"perso" per fiducia bassa (unica traccia: `pct_clienti_sotto_soglia_fiducia`). Quindi la metrica
non conta clienti salvati, ma **coppie (cluster, round) in cui FISSO è sceso e ADAPT no**. Il nome
sovrastima ciò che misura.

---

## 4. Report finale

### (a) Causa radice
**Il modello di reward non modella ciò che ADAPT ottimizza.** L'adeguatezza — e quindi ogni
delta di fiducia/soddisfazione — è `f(profilo, prodotto)` e nient'altro. Su questa base:
1. `Bond_Corporate` è l'unico prodotto sicuro (≥ soglia) per tutti i profili, ed è il bias fisso
   di FISSO → **FISSO parte con la strategia dominante**;
2. lo scenario/direttiva/tempo/storia **non entrano nel punteggio** → l'adattamento non ha un
   canale di valore;
3. il reward è una **scogliera asimmetrica** (+0.05 max vs −0.19 sotto soglia) → **ogni varianza
   è punita**, e ADAPT è per natura più variabile;
4. il leak `normalize→"Altro"` (3-6%) inietta rumore negativo che erode il margine sottile.

### (b) Opzioni di intervento

#### OPZIONE 1 — Adeguatezza dipendente dallo scenario (CORREZIONE ONESTA) ⭐⭐⭐⭐⭐
**Cosa:** rendere l'adeguatezza `f(profilo, prodotto, scenario/direttiva)`. Il prodotto "giusto"
deve cambiare col regime macro: in S2 (crisi) Cash/Sovereign devono diventare **premianti** per i
profili difensivi e Bond_Corporate deve **perdere** la sua dominanza universale. Concretamente:
un moltiplicatore/bonus di adeguatezza legato a `focus_prodotto` della direttiva e allo stato di
mercato (es. `liquidita_mercato`, `sentiment`).
**Perché onesta:** allinea la metrica al fenomeno che la simulazione dichiara di studiare
(l'efficacia dell'adattamento allo scenario). Oggi la metrica misura un'altra cosa.
**Cosa misurare dopo:** `valore_aggiunto_personalizzazione` deve diventare ≥ 0 almeno in S1/S2/S3;
il vantaggio di ADAPT deve **crescere** negli scenari a regime spostato (S2, S3) e la
compliance_rate di FISSO deve calare dove la direttiva contraddice il suo bias.

#### OPZIONE 2 — Reward simmetrico + eliminare il prodotto dominante (CORREZIONE ONESTA) ⭐⭐⭐⭐
**Cosa:** (a) rendere la funzione delta continua/simmetrica (upside ≈ downside) o ridurre il malus
`−0.15` così che la varianza non sia strutturalmente punita; (b) ribilanciare `ADEGUATEZZA_MATRIX`
in modo che **nessun** singolo prodotto sia ≥ soglia per tutti i profili (rompere la dominanza di
Bond_Corporate). Da fare **insieme** all'Opzione 1.
**Perché onesta:** un benchmark fisso deve essere battibile da una politica migliore; oggi è quasi
imbattibile per costruzione, non per merito.
**Cosa misurare dopo:** a parità di adeguatezza media tra i due promotori, il delta_fiducia deve
essere ~uguale (oggi in S2 è 0.00134 vs 0.00246 a parità di media 0.82 → è il sintomo della
scogliera); `mismatch_rate` di ADAPT non deve più tradursi in perdita netta sproporzionata.

#### OPZIONE 3 — Chiudere il leak "Altro" + churn reale (IGIENE, non risolutiva) ⭐⭐
**Cosa:** (a) forzare l'output prodotto su un enum chiuso (constrained decoding / validazione con
retry) così che "Altro" ≈ 0; (b) introdurre un vero meccanismo di churn (cliente sotto una soglia
di fiducia per N round → esce dal portafoglio) così che `clienti_salvati_dal_churn` misuri un
evento reale.
**Perché non risolutiva:** toglie rumore e rende oneste le metriche, ma **non** cambia il fatto
che l'adattamento è invisibile al reward. Da fare dopo 1+2.
**Cosa misurare dopo:** % "Altro" → ~0; churn > 0 solo dove la fiducia crolla davvero; le altre
metriche non devono cambiare per il solo effetto della pulizia.

#### ⚠️ SCORCIATOIE da NON confondere con le correzioni (le elenco per trasparenza)
- **Prompt-steering di ADAPT** verso i prodotti che la matrice premia (es. "per Aggressive usa
  Fondi_Azionari"): alza il tasso di conversione di ADAPT senza toccare il design. È **trucco**:
  fa vincere ADAPT insegnandogli a giocare la matrice statica, non ad adattarsi allo scenario.
- **Post-processing dell'output ADAPT** o clamp selettivi del malus solo per ADAPT: falsa i numeri.
- **Azzerare `MALUS` solo per ADAPT** / pesare i cluster a favore di ADAPT: trucca la metrica.
  (Il commit `3acc134 "no post-processing: adapt deve poter sbagliare"` va in questa direzione
  corretta: ADAPT deve poter sbagliare, il fix va fatto nel *modello*, non nascondendo gli errori.)

### (c) Ordine consigliato
1. **Opzione 1** (adeguatezza per-scenario) — è la causa radice.
2. **Opzione 2** (reward simmetrico + rompere la dominanza) — insieme alla 1.
3. Rieseguire S0-S4 a 200 round e validare con le metriche indicate sopra.
4. **Opzione 3** (igiene "Altro" + churn reale) come rifinitura.

### Criterio di validazione globale
Dopo 1+2, su S0-S4 (200 round) ci si aspetta:
`valore_aggiunto_personalizzazione` ≥ 0 e **crescente** con la "difficoltà"/scostamento dello
scenario; `vantaggio_adapt` in `fiducia_cumulata` > 0; convergenza dei tassi di conversione a
parità di adeguatezza media; e — controllo di onestà — se si rimette la segregazione o si toglie
l'asse scenario, il vantaggio di ADAPT deve sparire (prova che il valore viene dal modello, non da
un trucco).
