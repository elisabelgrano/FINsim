# FINsim Ontology Module

Modulo per caricamento e gestione della topologia FINsim su Neo4j.

## Componenti

### `finsim_scehma.json` (v2.0)
Schema ontologico del progetto FINsim:
- **12 allowed_labels**: ScenarioMacro, DirettivaBancaria, Promotore, Cliente, ProdottoFinanziario, ClusterProfilo, RagionamentoCluster, PropostaIndividuale, RispostaCliente, KPIRun, Interazione, Round
- **16 allowed_relationships**: DEFINISCE, EMETTE, GESTISCE, PROPONE, ACQUISTA, GENERA_STRATEGIA, RICEVE_PROPOSTA, PRODUCE_ESITO, REGISTRA_PERFORMANCE, INFLUENZA, APPARTIENE_A, OPERA_IN, AVVIENE_IN_ROUND, APPLICA_DIRETTIVA, DEFINISCE_CONTESTO, INTERAGISCE_CON
- **Node types**: Con proprietà specifiche per ogni tipo

### `ontology_loader.py`
Classe `OntologyLoader` per caricamento bulk nodi e relazioni su Neo4j.

**Caratteristiche:**
- ✓ Validazione rigorosa: ogni label e relationship verificata contro allowlist
- ✓ Query parametrizzate: ZERO concatenazioni di stringhe per parametri
- ✓ Label dinamiche sicure: validate rigorosamente prima dell'uso
- ✓ Bulk insert con UNWIND: inserimento efficiente in una transazione
- ✓ Retry logic: gestione errori transitori Neo4j
- ✓ Logging dettagliato per debugging

**Utilizzo:**
```python
from ontology_loader import OntologyLoader

loader = OntologyLoader()  # Carica schema, connette a Neo4j

result = loader.load(
    graph_id="my-graph",
    nodes=[
        {
            'uuid': 'node-1',
            'label': 'ScenarioMacro',
            'properties': {'nome': 'S0', 'descrizione': 'Baseline'}
        }
    ],
    relationships=[
        {
            'uuid': 'rel-1',
            'type': 'DEFINISCE',
            'source_uuid': 'node-1',
            'target_uuid': 'node-2',
            'properties': {'fact': 'Define context'}
        }
    ]
)

# result = {
#     'nodes_created': 1,
#     'relationships_created': 1,
#     'errors': [],
#     'success': True
# }

loader.close()
```

**Context manager:**
```python
with OntologyLoader() as loader:
    result = loader.load(graph_id, nodes, relationships)
```

### `populate_finsim.py`
Script per generare e caricare dati S0 (Baseline Neutro) su Neo4j.

**Dati generati:**
- 1 ScenarioMacro (S0 Baseline)
- 1 DirettivaBancaria (strategia Fisso/Broadcast)
- 3 Promotori (2 Fissi + 1 Adattativo AI-driven)
- 20 ClusterProfilo (griglia 4 righe × 5 colonne)
- 100 Clienti (distribuiti uniformemente nei cluster)
- Relazioni iniziali secondo relationship_rules

**Funzioni:**
- `generate_scenario_macro()` → dict ScenarioMacro
- `generate_direttiva_bancaria()` → dict DirettivaBancaria
- `generate_promotori()` → List[dict] 3 promotori
- `generate_cluster_profili()` → List[dict] 20 cluster
- `generate_clienti(num: int)` → List[dict] clienti
- `generate_relationships()` → List[dict] relazioni
- `populate_s0(graph_id: str)` → dict risultato

**Utilizzo:**
```python
from populate_finsim import populate_s0

result = populate_s0(graph_id='finsim-s0-baseline')
print(f"Nodi: {result['nodes_created']}, Relazioni: {result['relationships_created']}")
```

**Via CLI:**
```bash
cd backend/app/finsim/ontology
python populate_finsim.py
```

### `test_populate.py`
Suite di test per verificare struttura dati e validazione schema.

**Test inclusi:**
1. `test_data_generation()` - Verifica generazione nodi
2. `test_schema_validation()` - Verifica validazione label/relationship
3. `test_node_structure()` - Verifica struttura nodi
4. `test_relationship_structure()` - Verifica struttura relazioni

**Esecuzione:**
```bash
python -m unittest discover -s . -p "test_*.py"
# oppure
python test_populate.py
```

## Sicurezza

### Validazione Schema
Tutte le label e relationship sono validate rigosamente contro l'allowlist prima di essere usate:

```python
loader.validate_label('ScenarioMacro')       # True
loader.validate_label('InvalidLabel')        # False

loader.validate_relationship('DEFINISCE')    # True
loader.validate_relationship('INVALID')      # False
```

### Query Parametrizzate
Nessuna concatenazione di stringhe per parametri:

```cypher
# ✓ CORRETTO - parametrizzato
UNWIND $nodes_batch AS node_data
CREATE (n:Entity {
    uuid: node_data.uuid,
    graph_id: $graph_id,
    name: node_data.properties.nome
})

# ✓ SICURO - label validata, poi usata in f-string
WHERE n.uuid IN $uuids
SET n:`${validated_label}`
```

## Integrazione

### Struttura directory
```
backend/app/finsim/
├── __init__.py
├── ontology/
│   ├── __init__.py
│   ├── finsim_scehma.json        # Schema v2.0
│   ├── ontology_loader.py         # OntologyLoader class
│   ├── populate_finsim.py         # Genera S0
│   ├── test_populate.py           # Test suite
│   └── README.md                  # Questo file
├── agents/
├── scenarios/
```

### Import
```python
from backend.app.finsim.ontology import OntologyLoader, populate_s0
```

## Configurazione Neo4j

L'`OntologyLoader` usa configurazione da `backend/app/config.py`:

```python
NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'mirofish'  # da .env
```

Personalizzazione:
```python
loader = OntologyLoader(
    uri='bolt://neo4j-server:7687',
    user='custom_user',
    password='custom_pass'
)
```

## Logging

Configurazione logging:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('finsim.populate')
```

Output: messagi INFO/ERROR per ogni operazione.

## Prossimi Step

✓ Fase 1: Caricamento topologia S0 (COMPLETATO)

□ Fase 2: Integrazione Ollama per DirettivaBancaria (LLMA + reasoning)
□ Fase 3: ThreadPool per Promotori (parallelo A/B testing)
□ Fase 4: Batch processing Clienti (LIGHT_LLM evaluation)
□ Fase 5-7: Simulazione completa 20 round, KPI tracking, etc.

## Riferimenti

- CLAUDE.md — Regole progetto e vincoli di sicurezza
- neo4j_storage.py — Interfaccia Neo4j di base
- config.py — Configurazione centrale
