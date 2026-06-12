"""
Product normalization for FINsim metrics.

Standardizes raw product names from LLM responses into normalized categories
for consistent business metric calculation.
"""


def normalize_prodotto(raw: str) -> str:
    """
    Normalize raw product name to standardized category.

    Rules (case-insensitive, whitespace-stripped, substring matching):
    - contains "bond" and "corporate"        → "Bond_Corporate"
    - contains "obbligaz" and "corporate"    → "Bond_Corporate"
    - contains "bond" and "sovereign"        → "Bond_Sovereign"
    - contains "sovereign" or "sovran"       → "Bond_Sovereign"
    - contains "governativ"                  → "Bond_Sovereign"
    - contains "titoli di stato"             → "Bond_Sovereign"
    - contains "cash" or "liquide"           → "Cash_Equivalents"
    - contains "mixed" or "mist"             → "Mixed_Funds"
    - contains "multisett"                   → "Mixed_Funds"
    - anything else                          → "Altro"

    Args:
        raw: Raw product name string from LLM response

    Returns:
        Normalized product category string
    """
    if not isinstance(raw, str):
        return "Altro"

    # Normalize input: strip whitespace and convert to lowercase
    normalized = raw.strip().lower()

    if not normalized:
        return "Altro"

    # Bond_Corporate: (bond OR obbligaz OR banca) + corporate
    if ("corporate" in normalized) and \
       any(x in normalized for x in ["bond", "obbligaz", "banca"]):
        return "Bond_Corporate"

    # Bond_Sovereign: sovereign/sovran/governativ/titoli di stato
    if "sovereign" in normalized or "sovran" in normalized or \
       "governativ" in normalized or "titoli di stato" in normalized:
        return "Bond_Sovereign"

    # Bond_Sovereign: bond + sovereign
    if "bond" in normalized and "sovereign" in normalized:
        return "Bond_Sovereign"

    # Cash_Equivalents: cash or liquide
    if "cash" in normalized or "liquide" in normalized:
        return "Cash_Equivalents"

    # Mixed_Funds: mixed/mist/multisett
    if "mixed" in normalized or "mist" in normalized or \
       "multisett" in normalized:
        return "Mixed_Funds"

    # Default fallback
    return "Altro"


if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("Bond Corporate Investment Grade", "Bond_Corporate"),
        ("Banca Corporate Investment Grade", "Bond_Corporate"),
        ("Bond_Corporate", "Bond_Corporate"),
        ("Obbligazioni Corporate - Grado Investment", "Bond_Corporate"),
        ("Obbligazioni corporate investimento grade", "Bond_Corporate"),
        ("Bond_Sovereign", "Bond_Sovereign"),
        ("Obbligazioni governative", "Bond_Sovereign"),
        ("Obbligati sovrano", "Bond_Sovereign"),
        ("Titoli di stato low-risk", "Bond_Sovereign"),
        ("Cash_Equivalents", "Cash_Equivalents"),
        ("Liquide", "Cash_Equivalents"),
        ("Mixed_Funds", "Mixed_Funds"),
        ("Derivati finanziari (es: futures)", "Altro"),
        ("SLD", "Altro"),
    ]

    print("Testing normalize_prodotto():")
    print("-" * 60)
    passed = 0
    failed = 0

    for input_val, expected in test_cases:
        result = normalize_prodotto(input_val)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} normalize_prodotto('{input_val}') → '{result}' (expected: '{expected}')")

    print("-" * 60)
    print(f"Results: {passed} passed, {failed} failed")
