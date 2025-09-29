# ------------------------------------------------------------------------------
# parameters.py
#
# Centrale plek voor instellingen en parameters die in meerdere scripts
# (scraper, index, app) gebruikt worden.
# ------------------------------------------------------------------------------

# --- Scraper instellingen ---
BASE_URLS = [
        "https://publicatiereeksgevaarlijkestoffen.nl/publicaties/online/pgs-15/2023/0-1-november-2023",
        "https://publicatiereeksgevaarlijkestoffen.nl/publicaties/online/pgs-40/2025/0-1-juni-2025"
]

# --- Index / Embedding instellingen ---

# Kies hier het embedding model door een nummer te selecteren
# (Alle modellen komen uit sentence-transformers)
#
# 1. all-MiniLM-L6-v2
#    - Zeer snel, lichtgewicht, CPU-vriendelijk
#    - 384 dimensies
#
# 2. all-MiniLM-L12-v2
#    - Iets nauwkeuriger, trager
#    - 384 dimensies
#
# 3. multi-qa-MiniLM-L6-cos-v1
#    - Speciaal getraind voor vraag-antwoord retrieval
#    - Goede balans snelheid/kwaliteit
#
# 4. all-mpnet-base-v2
#    - Hogere kwaliteit, 768 dimensies
#    - Trager, vooral geschikt met GPU
#
# 5. multi-qa-mpnet-base-dot-v1
#    - Sterk in retrieval taken
#    - 768 dimensies
#
# 6. distiluse-base-multilingual-cased-v2
#    - Ondersteunt meerdere talen (ook Nederlands)
#    - 512 dimensies
#
# 7. paraphrase-multilingual-mpnet-base-v2
#    - Hoge kwaliteit, multilingual
#    - Zwaarder, GPU aanbevolen
#
# 8. sentence-t5-base
#    - Goede accuraatheid, maar trager
#    - 768 dimensies
#
# 9. sentence-t5-large
#    - Zeer hoge accuraatheid
#    - Groot en traag zonder GPU

EMBEDDING_MODELS = {
    1: "all-MiniLM-L6-v2",
    2: "all-MiniLM-L12-v2",
    3: "multi-qa-MiniLM-L6-cos-v1",
    4: "all-mpnet-base-v2",
    5: "multi-qa-mpnet-base-dot-v1",
    6: "distiluse-base-multilingual-cased-v2",
    7: "paraphrase-multilingual-mpnet-base-v2",
    8: "sentence-t5-base",
    9: "sentence-t5-large",
}

# Selecteer hier het nummer van het gewenste model
EMBEDDING_MODEL_ID = 6  # <- verander dit naar 2, 3, etc. voor andere modellen
EMBEDDING_MODEL = EMBEDDING_MODELS[EMBEDDING_MODEL_ID]

FAISS_INDEX_FILE = "pgs15.index"
DOCS_FILE = "docs.json"
META_FILE = "meta.json"


# --- Prompt instellingen ---
MAX_SECTION_CHARS = 4000   # maximale lengte van contextfragmenten
DEFAULT_SYSTEM_PROMPT = (
    "Je bent een behulpzame assistent en expert in PGS en ADR.\n"
    "Beantwoord uitsluitend op basis van de context. "
    "Als het antwoord niet in de context staat, zeg dat je het niet zeker weet.\n\n"
    "Geef compacte, feitelijke antwoorden met bronvermelding (sectietitel)."
)

PROMPT_PRESETS = {
    "Default": DEFAULT_SYSTEM_PROMPT,
    "Strikt juridisch": "Gebruik uitsluitend de context. Antwoord feitelijk en letterlijk waar mogelijk, zonder interpretatie. Vermeld altijd het paragraaf- of sectienummer uit de bron. Indien het antwoord niet in de context staat, geef aan: 'Niet in de beschikbare context gevonden.'",
    "Praktische samenvatting": "Vat de relevante verplichtingen of maatregelen kort samen in eenvoudige taal. Focus op wat iemand in de praktijk moet doen. Vermijd juridisch jargon, tenzij strikt noodzakelijk. Vermeld aan het einde de sectietitel als bron.",
    "Checklist": "Zet het antwoord om in een korte checklist van stappen of voorwaarden. Gebruik bullet points. Vermeld steeds welke sectie of tabel de bron is.",
    "Vergelijking": "Indien de context meerdere opties of categorieën bevat, geef een vergelijking in tabelvorm of overzicht met verschillen. Sluit af met de originele sectietitel als bron.",
    "Voor beginners": "Leg het antwoord uit alsof de lezer geen ervaring heeft met ADR/PGS. Gebruik eenvoudige bewoordingen en korte zinnen. Vermijd afkortingen of leg ze kort uit. Vermeld wel de sectietitel als bron.",
    "Managementsamenvatting": "Geef een ultrakorte samenvatting (max 3 zinnen) van de belangrijkste verplichting of maatregel. Noem altijd de sectietitel als bron."
}

# --- OpenAI instellingen ---
OPENAI_MODEL = "gpt-4o-mini"   # kan aangepast worden naar zwaarder model
DEFAULT_TEMPERATURE = 0.2
