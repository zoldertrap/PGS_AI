def fix_encoding(s: str) -> str:
    """Fix verkeerde tekens (bv. â → ’) in strings."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
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
