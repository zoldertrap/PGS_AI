import re
import pdfplumber
from RAG.encoding import fix_json_encoding

# Regex patronen
HEADING_RE = re.compile(r'^(?P<num>\d+(?:\.\d+)+)\s+(?P<title>.+)$', re.M)
TRAIL_PAGE_RE = re.compile(r'\s+\d{1,3}$', re.M)


def clean(s: str) -> str:
    return re.sub(r'\s+', ' ', s or '').strip()


def strip_trailing_page_number(title: str) -> str:
    """Verwijder paginanummers aan het einde van een titel (TOC cleaning)."""
    return TRAIL_PAGE_RE.sub('', title)


def extract_sections_from_fulltext(full_text: str, pgs_label: str, source_url: str):
    """Extracteer secties/maatregelen uit de volledige PDF-tekst."""
    docs = []
    matches = list(HEADING_RE.finditer(full_text))

    for i, m in enumerate(matches):
        num = m.group('num')
        raw_title = m.group('title')
        title = strip_trailing_page_number(raw_title)

        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(full_text)
        body = clean(full_text[start:end])

        # Skip inhoudsopgave-regels
        if TRAIL_PAGE_RE.search(raw_title) and len(body) < 100:
            continue

        node_type = 'measure' if re.search(r'\bmaatregel', title, re.I) else 'section'

        docs.append({
            "id": f"{pgs_label}-{'M' if node_type == 'measure' else 'S'}-{num}",
            "type": node_type,
            "pgs": pgs_label,
            "title": f"{num} {title}",
            "text": body,
            "items": [],
            "grondslag": [],
            "doelen": [],
            "scenarios": [],
            "tables": [],
            "source": source_url,
        })

    return fix_json_encoding(docs)


def scrape_pdf(pdf_path: str, source_url: str, pgs_label: str, keep_pages: bool = True):
    """Scrape een PDF in secties (en optioneel page-docs als fallback)."""
    # Volledige tekst ophalen
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages_text.append(page.extract_text() or '')
    full_text = '\n'.join(pages_text)

    # Secties extraheren
    section_docs = extract_sections_from_fulltext(full_text, pgs_label, source_url)

    if not keep_pages:
        return section_docs

    # Optioneel: page-docs
    page_docs = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            t = (page.extract_text() or '').strip()
            page_docs.append({
                "id": f"{pgs_label}-page-{i}",
                "type": "page",
                "pgs": pgs_label,
                "title": f"Page {i}",
                "text": t,
                "items": [],
                "grondslag": [],
                "doelen": [],
                "scenarios": [],
                "tables": [],
                "source": source_url,
            })

    return fix_json_encoding(section_docs + page_docs)
