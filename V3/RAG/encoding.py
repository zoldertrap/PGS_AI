def fix_encoding(s: str) -> str:
    """Fix encoding-issues (bv. â → ’) en vervang rare symbolen."""
    if not isinstance(s, str):
        return s
    try:
        s = s.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass  # gewoon doorgaan als dit niet lukt

    # Extra replacements voor rare tekens
    replacements = {
        "": "-",   # rare bullet uit PDF
        "•": "-",   # gewone bullet
        "–": "-",   # en-dash → normaal streepje
        "—": "-",   # em-dash → normaal streepje
        "“": "\"",
        "”": "\"",
        "’": "'",
        "´": "'",
        "•": "-",
        "·": "-",   # soms puntjes in tabellen
    }
    for bad, good in replacements.items():
        s = s.replace(bad, good)

    return s

def fix_json_encoding(obj):
    """Pas encoding-fix toe op dicts, lists en strings (recursief)."""
    if isinstance(obj, dict):
        return {k: fix_json_encoding(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fix_json_encoding(x) for x in obj]
    elif isinstance(obj, str):
        return fix_encoding(obj)
    else:
        return obj
