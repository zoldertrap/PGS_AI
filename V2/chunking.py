# chunking.py
import re

def chunk_text(text: str, max_tokens: int = 500):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current, length = [], [], 0
    for s in sentences:
        length += len(s.split())
        if length > max_tokens:
            chunks.append(" ".join(current))
            current, length = [], 0
        current.append(s)
    if current:
        chunks.append(" ".join(current))
    return chunks
