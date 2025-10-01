import json
import pandas as pd
import csv

# === 1. Parameters ===
INPUT_JSON = "V2\PGS_data\docs.json"
OUTPUT_CSV = "maatregelen.csv"
VERSIE_LABEL = "PGS_2025"

# === 2. Inlezen docs.json ===
with open(INPUT_JSON, encoding="utf-8") as f:
    docs = json.load(f)

# === 3. Filter alleen maatregelen ===
maatregelen = [d for d in docs if d.get("type") == "measure"]

# === 4. Omzetten naar eenvoudige records ===
data = []
for m in maatregelen:
    data.append({
        "Maatregelnummer": m.get("id"),
        "Titel": m.get("title"),
        "Tekst": m.get("text"),
        "Items": " | ".join(m.get("items", [])),
        "Grondslag": " | ".join(m.get("grondslag", [])),
        "Doelen": " | ".join(f"{d['id']} {d['title']}" for d in m.get("doelen", [])),
        "Scenarios": " | ".join(f"{s['id']} {s['title']}" for s in m.get("scenarios", [])),
        "Versie": VERSIE_LABEL,
    })

# === 5. Naar CSV exporteren (Excel-vriendelijk) ===
df = pd.DataFrame(data)
df.to_csv(
    OUTPUT_CSV,
    index=False,
    encoding="utf-8-sig",
    sep=";",                     # ✅ Excel expects ; as separator in Dutch locale
    quoting= csv.QUOTE_ALL,       # ✅ Quote all fields to handle special characters safely
)

print(f"✅ Export voltooid: {OUTPUT_CSV} met {len(df)} maatregelen.")