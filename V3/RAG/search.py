import numpy as np
from rank_bm25 import BM25Okapi
import json, os
from parameters import OUTPUT_DIR

# Helper: laad BM25 index
def load_bm25():
    bm25_file = os.path.join(OUTPUT_DIR, "bm25.json")
    with open(bm25_file, encoding="utf-8") as f:
        data = json.load(f)
    bm25 = BM25Okapi(data["tokenized_corpus"])
    return bm25, data["ids"]

def search_measures(query, local_model, index, ids, id_to_doc, embed_func,
                    pgs_filter=None, k=5, prefetch_k=200, mode="FAISS"):
    """
    Flexible search: FAISS, BM25, or Hybrid (BM25 → FAISS rerank).
    """

    # -----------------------
    # FAISS only
    # -----------------------
    if mode.upper() == "FAISS":
        q_emb = embed_func(local_model, query)
        D, I = index.search(q_emb, prefetch_k)
        candidates = [id_to_doc[ids[idx]] for idx in I[0] if idx >= 0]

    # -----------------------
    # BM25 only
    # -----------------------
    elif mode.upper() == "BM25":
        bm25, bm25_ids = load_bm25()
        tokenized_q = query.split()
        scores = bm25.get_scores(tokenized_q)
        top = np.argsort(scores)[::-1][:k]
        candidates = [id_to_doc[bm25_ids[i]] for i in top]

    # -----------------------
    # Hybrid: BM25 preselect → rerank with FAISS
    # -----------------------
    elif mode.upper().startswith("HYBRID"):
        bm25, bm25_ids = load_bm25()
        tokenized_q = query.split()
        scores = bm25.get_scores(tokenized_q)
        top = np.argsort(scores)[::-1][:prefetch_k]   # breed zoeken
        pre_candidates = [id_to_doc[bm25_ids[i]] for i in top]

        # FAISS rerank
        q_emb = embed_func(local_model, query)
        cand_embs = [embed_func(local_model, d["text"]) for d in pre_candidates]
        sims = np.dot(cand_embs, q_emb.T).flatten()
        best = np.argsort(sims)[::-1][:k]
        candidates = [pre_candidates[i] for i in best]

    else:
        raise ValueError(f"Unknown search mode: {mode}")

    # -----------------------
    # Apply PGS filter
    # -----------------------
    if pgs_filter:
        norm_filter = pgs_filter.replace(" ", "").upper()
        candidates = [
            d for d in candidates
            if (d.get("pgs") or "").replace(" ", "").upper().startswith(norm_filter)
        ]

    return candidates[:k]
