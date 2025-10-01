import numpy as np
from sentence_transformers import SentenceTransformer
import streamlit as st
from parameters import EMBEDDING_MODEL

@st.cache_resource
def load_local_model():
    return SentenceTransformer(EMBEDDING_MODEL)

def embed_local(model, text):
    return np.array([model.encode(text, normalize_embeddings=True)], dtype="float32")
