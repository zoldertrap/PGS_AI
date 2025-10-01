import json, faiss
import streamlit as st
from parameters import DOCS_FILE, META_FILE, FAISS_INDEX_FILE

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
