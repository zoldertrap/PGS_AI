import json
with open("docs.json", encoding="utf-8") as f:
    docs = json.load(f)

print("Aantal docs:", len(docs))
print("Measures:", sum(1 for d in docs if d["type"] == "measure"))
print("Sections:", sum(1 for d in docs if d["type"] == "section"))
