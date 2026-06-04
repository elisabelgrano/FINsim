# FINsim — Istruzioni per Claude Code

## Progetto
Fork di MiroFish-Offline per simulazione di promozione finanziaria con swarm intelligence. 
FINsim è un simulatore finanziario progettato per valutare per 20 round consecutivi l'efficacia di una strategia commerciale "Adattiva" (AI-driven) rispetto a una strategia "Fissa" (Benchmark broadcast) interagendo con 100 clienti sintetici.

## Architettura Agenti FINsim (4 Livelli)
- **Livello 1 - ScenarioMacro:** 1 nodo, comportamento deterministico e configurazione statica lungo i 20 round.
- **Livello 2 - DirettivaBancaria:** 1 agente adattivo, elaborato tramite HEAVY_LLM (qwen2.5:32b).
- **Livello 3 - Promotori:** N agenti in parallelo (A/B testing tra strategia Adattiva e benchmark Fisso), generati tramite mix di HEAVY_LLM e LIGHT_LLM.
- **Livello 4 - Clienti:** 100 agenti sintetici disposti in griglia, elaborati in modalità batch tramite LIGHT_LLM (qwen2.5:3b).

## Scenari Simulazione (S0 - S4)
La simulazione si sviluppa su 5 scenari macroeconomici distinti (20 round ciascuno):
- **S0 (Baseline Neutro / Reale):** Tassi 2.0%, tensione geopolitica attiva, sentiment ansioso.
- **S1 (Shock Tassi / Rialzo):** Rialzo tassi improvviso (2.5%), crollo dell'equity, spread in allargamento.
- **S2 (Crisi Acuta / Liquidità):** Blocco geopolitico totale, "flight to quality" massivo, PIL negativo.
- **S3 (Opportunità / Pressione Normativa):** Distensione geopolitica, rimbalzo azionario, ma con forte pressione compliance.
- **S4 (Biforcazione Dinamica):** Inizia identico a S0, ma al Round 10 scatta un cambio drastico e obbligatorio della DirettivaBancaria.

## Regole di Codice Tassative
- **Ambiente:** Python 3.11 - 3.12 (vincolo camel-oasis, non aggiornare le dipendenze).
- **Modifiche:** Non alterare i file originali di MiroFish-Offline senza aggiungere il commento `# FINSIM-MOD`.
- **Directory:** Tutti i nuovi moduli backend FINsim vanno in `backend/app/finsim/`.
- **Standard:** Ogni nuova funzione richiede type hints completi e docstring.
- **Query Neo4j:** MAI label dinamiche non validate, usare allowlist

## Regole Neo4j (Sicurezza Critica)
- **Zero Concatenazioni:** È assolutamente vietato usare f-strings o concatenazioni per inserire parametri nelle query Cypher. Usa sempre la parametrizzazione nativa del driver.
- **Allowlist Label:** Non usare MAI label dinamiche non validate. Verifica ogni label contro la lista `allowed_labels` presente nel file `finsim_schema.json` prima di ogni esecuzione.

## File Intoccabili
- `backend/app/config.py`: configurazione centrale
- `backend/app/storage/neo4j_storage.py`: interfaccia Neo4j 
- `docker-compose.yml`: orchestratore container

## Sicurezza (da fixare in Fase 7)
CVE-2026-7059: path traversal in simulation.py (param Platform non
sanitizzato)CVE-2026-7058: command injection in services/send_command