from openai import OpenAI
from parameters import MAX_SECTION_CHARS, OPENAI_MODEL, DEFAULT_TEMPERATURE

client = OpenAI()

def safe_text(t: str) -> str:
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
