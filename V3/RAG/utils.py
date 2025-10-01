import re

def detect_pgs_from_query(query: str):
    match = re.search(r"\bPGS\s*-?\s*0*(\d+)\b", query, re.I)
    if match:
        return f"PGS{int(match.group(1))}"
    return None
