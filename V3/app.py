from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from parameters import PROMPT_PRESETS, DEFAULT_TEMPERATURE
from RAG.data import load_all
from RAG.data import load_bm25_index
from RAG.search import search_measures  # dit moet FAISS/BM25/Hybrid ondersteunen
from RAG.prompts import answer_with_context, safe_text
from RAG.utils import detect_pgs_from_query
from RAG.embedding import load_local_model, embed_local

# -------------------------------
# UI instellingen
# -------------------------------
st.set_page_config(page_title="PGS Q&A", layout="wide")
st.title("PGS Q&A (RAG demo met lokale embeddings)")

# Prompt instellingen
st.sidebar.header("🔧 Prompt instellingen")
chosen_preset = st.sidebar.selectbox("Kies promptstijl", list(PROMPT_PRESETS.keys()))
preset_prompt = PROMPT_PRESETS[chosen_preset]
custom_prompt = st.sidebar.text_area(
    "Of voer je eigen system prompt in:",
    value="",
    height=200,
    placeholder="Laat leeg om de preset te gebruiken..."
)
system_prompt = custom_prompt.strip() or preset_prompt
temperature = st.sidebar.slider("Creativiteit (temperature)", 0.0, 1.0, DEFAULT_TEMPERATURE)

# Zoekopties
st.sidebar.header("🔎 Zoekopties")
search_mode = st.sidebar.selectbox(
    "Kies zoekmethode",
    ["FAISS", "BM25", "Hybrid (BM25 → FAISS rerank)"]
)

pgs_filter_mode = st.sidebar.radio(
    "PGS filter:",
    ["Automatisch detecteren", "Geen filter (alle PGS)", "Handmatig kiezen"]
)

# -------------------------------
# Data & modellen laden
# -------------------------------
docs, index, ids, id_to_doc = load_all()
bm25, bm25_ids = load_bm25_index()              # BM25
local_model = load_local_model()

# -------------------------------
# Query invoer
# -------------------------------
q = st.text_input("Stel je vraag (bijv. 'Geef me de maatregelen die bij PGS10 horen')")
k = st.slider("Aantal context-chunks", 1, 199, 20)

# -------------------------------
# Zoekactie
# -------------------------------
if st.button("Zoeken") or q:
    if q:
        # PGS-filter bepalen
        if pgs_filter_mode == "Automatisch detecteren":
            pgs_filter = detect_pgs_from_query(q)
        elif pgs_filter_mode == "Geen filter (alle PGS)":
            pgs_filter = None
        else:  # Handmatig kiezen
            all_pgs = sorted({d.get("pgs") for d in docs if d.get("pgs")})
            pgs_filter = st.sidebar.selectbox("Kies PGS document:", all_pgs)

        st.sidebar.write(f"🔎 PGS filter: {pgs_filter or 'geen'}")

        # Zoekfunctie uitvoeren
        hits = search_measures(
            q,
            local_model,
            index,
            ids,
            id_to_doc,
            embed_local,
            pgs_filter=pgs_filter,
            k=k,
            mode=search_mode
        )

        # Antwoord genereren
        ans = answer_with_context(q, hits, system_prompt, temperature)
        st.subheader("Antwoord")
        st.markdown(ans)

        # Context tonen
        with st.expander("Context (gevonden stukken)"):
            for h in hits:
                st.markdown(f"**{h['title']}**  \n_{h['source']}_")
                st.write(safe_text(h["text"]))
                if h.get("items"):
                    st.write("• " + "\n• ".join(h["items"][:10]))
                st.markdown("---")
