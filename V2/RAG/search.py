def search_measures(query, local_model, index, ids, id_to_doc, embed_func, pgs_filter=None, k=5, prefetch_k=200):
    """
    Hybrid semantic search with optional metadata filtering.
    Always searches the full FAISS index first, then applies metadata filters.

    Args:
        query (str): user query
        local_model: embedding model
        index: FAISS index
        ids: list of doc ids (same order as FAISS index)
        id_to_doc (dict): mapping id -> doc
        embed_func: function to embed query
        pgs_filter (str): optional filter, e.g. "PGS6"
        k (int): number of results after filtering
        prefetch_k (int): how many results to fetch from FAISS before filtering
    """
    # Embed query
    q_emb = embed_func(local_model, query)

    # Search full FAISS index
    D, I = index.search(q_emb, prefetch_k)
    candidates = [id_to_doc[ids[idx]] for idx in I[0] if idx >= 0]

    # Apply PGS metadata filter
    if pgs_filter:
        norm_filter = pgs_filter.replace(" ", "").upper()
        candidates = [
            d for d in candidates
            if (d.get("pgs") or "").replace(" ", "").upper().startswith(norm_filter)
        ]

    # If too few results remain, expand search window
    if len(candidates) < k and prefetch_k < len(ids):
        return search_measures(
            query, local_model, index, ids, id_to_doc, embed_func,
            pgs_filter, k, prefetch_k=min(len(ids), prefetch_k * 2)
        )

    return candidates[:k]
