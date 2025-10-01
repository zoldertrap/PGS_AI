
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from parameters import PROMPT_PRESETS, DEFAULT_TEMPERATURE
from RAG.data import load_all
from RAG.search import search_measures
from RAG.prompts import answer_with_context, safe_text
from RAG.utils import detect_pgs_from_query
from RAG.embedding import load_local_model, embed_local

st.set_page_config(page_title="PGS Q&A", layout="wide")
st.title("PGS Q&A (RAG demo met lokale embeddings)")

st.sidebar.header("🔧 Prompt instellingen")
chosen_preset = st.sidebar.selectbox("Kies promptstijl", list(PROMPT_PRESETS.keys()))
preset_prompt = PROMPT_PRESETS[chosen_preset]
custom_prompt = st.sidebar.text_area("Of voer je eigen system prompt in:", value="", height=200, placeholder="Laat leeg om de preset te gebruiken...")
system_prompt = custom_prompt.strip() or preset_prompt
temperature = st.sidebar.slider("Creativiteit (temperature)", 0.0, 1.0, DEFAULT_TEMPERATURE)

docs, index, ids, id_to_doc = load_all()
local_model = load_local_model()

q = st.text_input("Stel je vraag (bijv. 'Geef me de maatregelen die bij PGS10 horen')")
k = st.slider("Aantal context-chunks", 1, 199, 100)

if st.button("Zoeken") or q:
    if q:
        detected_pgs = detect_pgs_from_query(q)
        st.sidebar.write(f"🔎 Gedetecteerde PGS: {detected_pgs or 'geen'}")

        hits = search_measures(q, local_model, index, ids, id_to_doc, embed_local, pgs_filter=detected_pgs, k=k)

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
