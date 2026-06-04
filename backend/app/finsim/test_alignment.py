"""
Test di allineamento tra populate_finsim.py e search_finsim.py.
Verifica che le proprietà generate da populate siano compatibili con le query di search.
"""

import json
from pathlib import Path
from backend.app.finsim.ontology.populate_finsim import (
    generate_scenario_macro,
    generate_promotori,
    generate_clienti,
)


def test_scenario_properties():
    """Verifica che ScenarioMacro abbia scenario_id come proprietà."""
    scenario = generate_scenario_macro()
    assert 'properties' in scenario, "ScenarioMacro deve avere 'properties'"
    assert 'scenario_id' in scenario['properties'], "properties deve contenere 'scenario_id'"
    assert scenario['properties']['scenario_id'] == 'S0', "scenario_id deve essere 'S0'"
    print("✓ ScenarioMacro ha scenario_id corretto")


def test_promotore_properties():
    """Verifica che Promotore abbia promotore_id come proprietà."""
    promotori = generate_promotori()
    for p in promotori:
        assert 'properties' in p, "Promotore deve avere 'properties'"
        assert 'promotore_id' in p['properties'], "properties deve contenere 'promotore_id'"
    print(f"✓ {len(promotori)} Promotori hanno promotore_id corretto")


def test_cliente_grid_properties():
    """Verifica che Cliente abbia cluster_riga e cluster_col come proprietà."""
    clienti = generate_clienti(num_clienti=10)
    for c in clienti:
        assert 'properties' in c, "Cliente deve avere 'properties'"
        assert 'cluster_riga' in c['properties'], "properties deve contenere 'cluster_riga'"
        assert 'cluster_col' in c['properties'], "properties deve contenere 'cluster_col'"
        assert 'cliente_id' in c['properties'], "properties deve contenere 'cliente_id'"
    print(f"✓ {len(clienti)} Clienti hanno cluster_riga/col e cliente_id corretti")


def test_schema_file_exists():
    """Verifica che finsim_schema.json esista."""
    schema_path = Path(__file__).parent / 'ontology' / 'finsim_schema.json'
    assert schema_path.exists(), f"Schema file non trovato: {schema_path}"

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    assert 'allowed_labels' in schema, "Schema deve contenere 'allowed_labels'"
    assert 'allowed_relationships' in schema, "Schema deve contenere 'allowed_relationships'"
    assert 'ScenarioMacro' in schema['allowed_labels'], "ScenarioMacro non in allowed_labels"
    assert 'Promotore' in schema['allowed_labels'], "Promotore non in allowed_labels"
    assert 'Cliente' in schema['allowed_labels'], "Cliente non in allowed_labels"
    print(f"✓ Schema file valido con {len(schema['allowed_labels'])} label allowed")


if __name__ == '__main__':
    test_scenario_properties()
    test_promotore_properties()
    test_cliente_grid_properties()
    test_schema_file_exists()
    print("\n✅ Tutti i test di allineamento sono passati!")
