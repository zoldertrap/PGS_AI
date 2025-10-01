
# ------------------------------------------------------------------------------

import os, json, numpy as np, faiss
from sentence_transformers import SentenceTransformer
from parameters import DOCS_FILE, META_FILE, FAISS_INDEX_FILE, EMBEDDING_MODEL, OUTPUT_DIR, VERSION
from rank_bm25 import BM25Okapi


# Laad documenten
def load_docs(path=DOCS_FILE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
    
def normalize_tables(tables):
    """Zet tabellen altijd om naar strings (1 regel per rij)."""
    norm = []
    for row in tables:
        if isinstance(row, str):
            norm.append(row)

        elif isinstance(row, (list, tuple)):
            # bv. ["ADR 2023", "rijksoverheid.nl"]
            parts = []
            for cell in row:
                if isinstance(cell, dict):
                    txt = cell.get("text", "")
                    url = cell.get("url")
                    if url:
                        parts.append(f"{txt} ({url})")
                    else:
                        parts.append(txt)
                else:
                    parts.append(str(cell))
            norm.append("; ".join(parts))

        elif isinstance(row, dict):
            # losse dict als cell
            txt = row.get("text", "")
            url = row.get("url")
            norm.append(f"{txt} ({url})" if url else txt)

        else:
            norm.append(str(row))
    return norm



def text_for_indexing(doc):
    parts = [
        doc.get("id",""),
        doc.get("title",""),
        doc.get("text",""),
        "\n".join(doc.get("items",[])),
        "\n".join(normalize_tables(doc.get("tables",[]))),
    ]
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

# -------------------------------
# FAISS indexing
# -------------------------------
def build_faiss_index(docs,texts):
    
    model = SentenceTransformer(EMBEDDING_MODEL)
    embs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    dim = embs.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embs)

    faiss.write_index(index, FAISS_INDEX_FILE)
    save_metadata(docs, META_FILE)

    print(f"✅ FAISS: Indexed {len(docs)} chunks with {EMBEDDING_MODEL} → {FAISS_INDEX_FILE}")

# -------------------------------
# BM25 indexing
# -------------------------------
def build_bm25_index(docs):
    
    corpus = [d.get("text", "") for d in docs]
    tokenized_corpus = [doc.split() for doc in corpus]

    bm25 = BM25Okapi(tokenized_corpus)

    bm25_meta = {
        "ids": [d["id"] for d in docs],
        "tokenized_corpus": tokenized_corpus,
    }

    bm25_file = os.path.join(OUTPUT_DIR, "bm25.json")
    with open(bm25_file, "w", encoding="utf-8") as f:
        json.dump(bm25_meta, f, ensure_ascii=False, indent=2)

    print(f"✅ BM25: Indexed {len(docs)} docs → {bm25_file}")








#python build_index.py --mode all

# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["faiss", "bm25", "all"], default="all")
    args = parser.parse_args()

    docs = load_docs()
    texts = [text_for_indexing(d) for d in docs]


    if args.mode in ("faiss", "all"):
        build_faiss_index(docs,texts)
    if args.mode in ("bm25", "all"):
        build_bm25_index(docs)