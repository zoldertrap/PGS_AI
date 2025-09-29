# ------------------------------------------------------------------------------
# app.py
#
# Doel:
#   Streamlit-app die Retrieval-Augmented Generation (RAG) gebruikt
#   voor het beantwoorden van vragen over PGS-15.
#
# Wat het doet:
#   - Laadt documenten en FAISS-index (met lokale embeddings)
#   - Embed de vraag van de gebruiker lokaal met SentenceTransformer
#   - Zoekt de meest relevante stukken tekst
#   - Bouwt een prompt met context en stuurt die naar GPT (OpenAI API)
#   - Toont gevonden context en het antwoord in de UI
#
# Belangrijk:
#   - Embeddings draaien lokaal (CPU, gratis)
#   - Antwoord komt van OpenAI GPT (gpt-4o-mini)
#   - Sidebar bevat instellingen voor promptstijl en creativiteit
# ------------------------------------------------------------------------------



import os, json, numpy as np, faiss, streamlit as st
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
from parameters import (
    DOCS_FILE, META_FILE, FAISS_INDEX_FILE, EMBEDDING_MODEL,
    MAX_SECTION_CHARS, PROMPT_PRESETS, DEFAULT_SYSTEM_PROMPT,
    OPENAI_MODEL, DEFAULT_TEMPERATURE
)

# --- OpenAI client ---
load_dotenv()
client = OpenAI()

# --- Data en index laden ---
@st.cache_resource
def load_all():
    with open(DOCS_FILE, encoding="utf-8") as f:
        docs = json.load(f)
    index = faiss.read_index(FAISS_INDEX_FILE)
    with open(META_FILE, encoding="utf-8") as f:
        meta = json.load(f)
    id_to_doc = {d["id"]: d for d in docs}
    return docs, index, meta["ids"], id_to_doc

# --- Lokaal embedding model ---
@st.cache_resource
def load_local_model():
    return SentenceTransformer(EMBEDDING_MODEL)

def embed_local(model, text):
    return np.array([model.encode(text, normalize_embeddings=True)], dtype="float32")

# --- Prompt helpers ---
def safe_text(t):
    if not t:
        return ""
    return t[:MAX_SECTION_CHARS] + ("..." if len(t) > MAX_SECTION_CHARS else "")

def make_prompt(query, retrieved):
    ctx = []
    for r in retrieved:
        ctx.append(f"### {r['title']}\nBron: {r['source']}\n\n{safe_text(r['text'])}")
        if r.get("items"):
            ctx.append("• " + "\n• ".join(r["items"][:10]))
        if r.get("flat_table_text"):
            ctx.append("\nTabeluittreksel:\n" + safe_text(r["flat_table_text"]))
    context = "\n\n---\n\n".join(ctx)
    return (
        "Je bent een behulpzame assistent en expert in PGS en ADR.\n"
        "Beantwoord uitsluitend op basis van de context. "
        "Als het antwoord niet in de context staat, zeg dat je het niet zeker weet.\n\n"
        f"VRAAG: {query}\n\n"
        f"CONTEXT:\n{context}"
    )

def answer_with_context(query, retrieved, system_prompt, temperature=DEFAULT_TEMPERATURE):
    prompt = make_prompt(query, retrieved)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )
    return resp.choices[0].message.content

# --- Streamlit UI ---
st.set_page_config(page_title="PGS Q&A", layout="wide")
st.title("PGS 15 en 40 Q&A (RAG demo met lokale embeddings)")

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

docs, index, ids, id_to_doc = load_all()
local_model = load_local_model()

q = st.text_input("Stel je vraag (bijv. 'klant heeft een brandkast. Aan welke eisen moet hij voldoen?')")
k = st.slider("Aantal context-chunks", 1, 20, 4)

if st.button("Zoeken") or q:
    if q:
        q_emb = embed_local(local_model, q)
        D, I = index.search(q_emb, k)
        hits = [id_to_doc[ids[idx]] for idx in I[0] if idx >= 0]
        ans = answer_with_context(q, hits, system_prompt, temperature)
        st.subheader("Antwoord")
        st.markdown(ans)
        with st.expander("Context (gevonden stukken)"):
            for h in hits:
                st.markdown(f"**{h['title']}**  \n_{h['source']}_")
                st.write(safe_text(h["text"]))
                if h.get("items"):
                    st.write("• " + "\n• ".join(h["items"][:10]))
                st.markdown("---")

       
        
