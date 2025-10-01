import json, faiss, os
import streamlit as st
from parameters import DOCS_FILE, META_FILE, FAISS_INDEX_FILE, OUTPUT_DIR
from rank_bm25 import BM25Okapi

@st.cache_resource
def load_all():
    with open(DOCS_FILE, encoding="utf-8") as f:
        docs = json.load(f)
    index = faiss.read_index(FAISS_INDEX_FILE)
    with open(META_FILE, encoding="utf-8") as f:
        meta = json.load(f)

    id_to_doc = {d["id"]: d for d in docs}
    ids = [m["id"] for m in meta]   # ✅ instead of meta["ids"]

    return docs, index, ids, id_to_doc




def load_bm25_index():
    bm25_file = os.path.join(OUTPUT_DIR, "bm25.json")
    with open(bm25_file, encoding="utf-8") as f:
        bm25_meta = json.load(f)

    tokenized_corpus = bm25_meta["tokenized_corpus"]
    ids = bm25_meta["ids"]

    bm25 = BM25Okapi(tokenized_corpus)
    return bm25, ids