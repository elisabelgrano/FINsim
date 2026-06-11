"""
Product normalizer for FINsim — standardizes inconsistent LLM-generated product names.

Handles variations in product naming across LLM runs by applying substring-based
normalization rules, allowing future LLM variants to be handled without code changes.
"""


def normalize_prodotto(raw: str) -> str:
    """
    Normalize raw product string to canonical form.

    Rules (applied in order, case-insensitive):
    - (bond|obbligazi) + corporate → "Bond_Corporate"
    - (bond|obbligazi) + sovereign → "Bond_Sovereign"
    - sovereign or sovran or stato  → "Bond_Sovereign"
    - governativ                    → "Bond_Sovereign"
    - cash or liquide               → "Cash_Equivalents"
    - mixed or mist                 → "Mixed_Funds"
    - multisett                     → "Mixed_Funds"
    - unrecognized                  → "Altro"

    Args:
        raw: Raw product name from LLM output

    Returns:
        Normalized product name as str
    """
    if not raw:
        return "Altro"

    # Strip whitespace and lowercase for matching
    normalized = raw.strip().lower()

    # Bond rules (order matters: corporate before sovereign)
    bond_keywords = ["bond", "obbligazi"]
    has_bond = any(kw in normalized for kw in bond_keywords)

    if has_bond and "corporate" in normalized:
        return "Bond_Corporate"
    if has_bond and "sovereign" in normalized:
        return "Bond_Sovereign"

    # Sovereign/government bonds
    if any(kw in normalized for kw in ["sovereign", "sovran", "stato"]):
        return "Bond_Sovereign"

    # Government bonds
    if "governativ" in normalized:
        return "Bond_Sovereign"

    # Cash equivalents
    if "cash" in normalized or "liquide" in normalized:
        return "Cash_Equivalents"

    # Mixed/diversified funds
    if "mixed" in normalized or "mist" in normalized:
        return "Mixed_Funds"
    if "multisett" in normalized:
        return "Mixed_Funds"

    # Unrecognized products
    return "Altro"


if __name__ == "__main__":
    # Test with 10 real examples from risultati JSON files
    test_cases = [
        ("Bond Corporate Investment Grade", "Bond_Corporate"),
        ("Bond Corporate", "Bond_Corporate"),
        ("Bond_Corporate", "Bond_Corporate"),
        ("Obbligazioni Corporate - Grado Investment Grade", "Bond_Corporate"),
        ("Obbligazioni corporate investimento grade", "Bond_Corporate"),
        ("Obbligazioni Sovrane Europee", "Bond_Sovereign"),
        ("Titoli di stato low-risk", "Bond_Sovereign"),
        ("Cash_Equivalents", "Cash_Equivalents"),
        ("Liquide", "Cash_Equivalents"),
        ("Derivati finanziari (es: futures, opzioni)", "Altro"),
    ]

    print("Testing normalize_prodotto():")
    print("-" * 70)
    all_pass = True
    for raw, expected in test_cases:
        result = normalize_prodotto(raw)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_pass = False
        print(f"{status} {raw:50} → {result:20} (expected: {expected})")

    print("-" * 70)
    if all_pass:
        print("All tests passed!")
    else:
        print("Some tests failed!")
