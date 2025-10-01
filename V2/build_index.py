
# ------------------------------------------------------------------------------

import json, numpy as np, faiss
from sentence_transformers import SentenceTransformer
from parameters import DOCS_FILE, META_FILE, FAISS_INDEX_FILE, EMBEDDING_MODEL, OUTPUT_DIR, VERSION

# Laad documenten
def load_docs(path=DOCS_FILE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def text_for_embedding(doc):
    parts = [
        doc.get("id",""),
        doc.get("title",""),
        doc.get("text",""),
        "\n".join(doc.get("items",[])),
        "\n".join(doc.get("tables",[])),
    ]
    # extra fields for measures
    if doc.get("type") == "measure":
        parts.append("\n".join(doc.get("grondslag", [])))
        parts.append("\n".join(d["id"] + " " + d["title"] for d in doc.get("doelen", [])))
        parts.append("\n".join(s["id"] + " " + s["title"] for s in doc.get("scenarios", [])))
    return "\n".join(p for p in parts if p)

def save_metadata(docs,path = META_FILE):
    meta = [
        {
            "id": d["id"],
            "pgs": d.get("pgs"),
            "type": d.get("type"),
            "title": d.get("title"),
            "source": d.get("source"),    
        }
        for d in docs
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)



if __name__ == "__main__":
    docs = load_docs()
    texts = [text_for_embedding(d) for d in docs]

    model = SentenceTransformer(EMBEDDING_MODEL)
    embs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    dim = embs.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embs)

    faiss.write_index(index, FAISS_INDEX_FILE)
    save_metadata(docs, META_FILE)

    print(f"Indexed {len(docs)} chunks with {EMBEDDING_MODEL} → {FAISS_INDEX_FILE}")
