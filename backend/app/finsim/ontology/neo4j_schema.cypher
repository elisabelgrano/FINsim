// FINsim Neo4j Schema - Constraints and Indexes
// Version: 2.0
// Purpose: Define unique constraints on primary keys and B-Tree indexes on frequently queried properties
// Neo4j Version: 5.18+
// FINSIM-MOD: Complete Cypher schema initialization script

// ============================================================================
// SECTION 1: UNIQUE CONSTRAINTS ON PRIMARY KEYS
// ============================================================================

// ScenarioMacro: scenario_id is the primary key
CREATE CONSTRAINT sc_scenario_id_unique IF NOT EXISTS
FOR (n:ScenarioMacro) REQUIRE n.scenario_id IS UNIQUE;

// DirettivaBancaria: direttiva_id is the primary key
CREATE CONSTRAINT db_direttiva_id_unique IF NOT EXISTS
FOR (n:DirettivaBancaria) REQUIRE n.direttiva_id IS UNIQUE;

// Promotore: promotore_id is the primary key
CREATE CONSTRAINT pr_promotore_id_unique IF NOT EXISTS
FOR (n:Promotore) REQUIRE n.promotore_id IS UNIQUE;

// Cliente: cliente_id is the primary key
CREATE CONSTRAINT cl_cliente_id_unique IF NOT EXISTS
FOR (n:Cliente) REQUIRE n.cliente_id IS UNIQUE;

// ProdottoFinanziario: prodotto_id is the primary key
CREATE CONSTRAINT pf_prodotto_id_unique IF NOT EXISTS
FOR (n:ProdottoFinanziario) REQUIRE n.prodotto_id IS UNIQUE;

// ClusterProfilo: cluster_id is the primary key
CREATE CONSTRAINT cp_cluster_id_unique IF NOT EXISTS
FOR (n:ClusterProfilo) REQUIRE n.cluster_id IS UNIQUE;

// RagionamentoCluster: composite key (round, scenario_id, cluster_id)
CREATE CONSTRAINT rc_composite_key_unique IF NOT EXISTS
FOR (n:RagionamentoCluster) REQUIRE (n.round, n.scenario_id, n.cluster_id) IS UNIQUE;

// PropostaIndividuale: composite key (round, prodotto_id)
CREATE CONSTRAINT pi_composite_key_unique IF NOT EXISTS
FOR (n:PropostaIndividuale) REQUIRE (n.round, n.prodotto_id) IS UNIQUE;

// RispostaCliente: composite key (round, scenario_id, cliente_id)
CREATE CONSTRAINT rc_cliente_composite_unique IF NOT EXISTS
FOR (n:RispostaCliente) REQUIRE (n.round, n.scenario_id, n.cliente_id) IS UNIQUE;

// KPIRun: composite key (round, scenario_id)
CREATE CONSTRAINT kpi_composite_key_unique IF NOT EXISTS
FOR (n:KPIRun) REQUIRE (n.round, n.scenario_id) IS UNIQUE;

// Interazione: id_interazione is the primary key
CREATE CONSTRAINT int_id_interazione_unique IF NOT EXISTS
FOR (n:Interazione) REQUIRE n.id_interazione IS UNIQUE;

// Round: id_round is the primary key
CREATE CONSTRAINT rnd_id_round_unique IF NOT EXISTS
FOR (n:Round) REQUIRE n.id_round IS UNIQUE;

// ============================================================================
// SECTION 2: B-TREE INDEXES ON FREQUENTLY QUERIED PROPERTIES
// ============================================================================

// --- Cliente Indexes ---
// Grid-based clustering queries: frequently filtered by cluster position
CREATE INDEX cliente_cluster_riga_idx IF NOT EXISTS
FOR (n:Cliente) ON (n.cluster_riga);

CREATE INDEX cliente_cluster_col_idx IF NOT EXISTS
FOR (n:Cliente) ON (n.cluster_col);

// --- Round Indexes ---
// Round-based queries across all temporal nodes
CREATE INDEX ragionamento_round_idx IF NOT EXISTS
FOR (n:RagionamentoCluster) ON (n.round);

CREATE INDEX proposta_round_idx IF NOT EXISTS
FOR (n:PropostaIndividuale) ON (n.round);

CREATE INDEX risposta_round_idx IF NOT EXISTS
FOR (n:RispostaCliente) ON (n.round);

CREATE INDEX kpi_round_idx IF NOT EXISTS
FOR (n:KPIRun) ON (n.round);

// --- Scenario Indexes ---
// Scenario-based filtering across simulation entities
CREATE INDEX ragionamento_scenario_idx IF NOT EXISTS
FOR (n:RagionamentoCluster) ON (n.scenario_id);

CREATE INDEX risposta_scenario_idx IF NOT EXISTS
FOR (n:RispostaCliente) ON (n.scenario_id);

CREATE INDEX kpi_scenario_idx IF NOT EXISTS
FOR (n:KPIRun) ON (n.scenario_id);

CREATE INDEX direttiva_scenario_idx IF NOT EXISTS
FOR (n:DirettivaBancaria) ON (n.scenario_rif);

// --- DirettivaBancaria Indexes ---
// Status and type-based queries
CREATE INDEX direttiva_attiva_idx IF NOT EXISTS
FOR (n:DirettivaBancaria) ON (n.attiva);

CREATE INDEX direttiva_tipo_idx IF NOT EXISTS
FOR (n:DirettivaBancaria) ON (n.tipo);

// --- Promotore Indexes ---
// Strategy type queries (adaptive vs benchmark)
CREATE INDEX promotore_adattativo_idx IF NOT EXISTS
FOR (n:Promotore) ON (n.adattativo);

CREATE INDEX promotore_tipo_idx IF NOT EXISTS
FOR (n:Promotore) ON (n.tipo);

// --- ScenarioMacro Indexes ---
// Round tracking in scenario context
CREATE INDEX scenario_round_corrente_idx IF NOT EXISTS
FOR (n:ScenarioMacro) ON (n.round_corrente);

// ============================================================================
// NOTES FOR FUTURE PHASES
// ============================================================================
// Phase 3+ may add Vector Indexes on:
//   - RagionamentoCluster.embedding (strategy reasoning embeddings)
//   - PropostaIndividuale.embedding (proposal communication embeddings)
//   - Cliente.embedding (client profile semantic embeddings)
//
// These will be added after integrating embedding model with EMBEDDING_MODEL config
// (default: nomic-embed-text from config.py)
