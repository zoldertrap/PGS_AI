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
    docs = []

    with pdfplumber.open(pdf_path) as pdf:
        # Full text voor heading-detectie
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        # Secties extraheren
        section_docs = extract_sections_from_fulltext(full_text, pgs_label, source_url)
        docs.extend(section_docs)

        if keep_pages:
            for i, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text() or "").strip()

                # --- Extra: tabellen parsen ---
                tables = []
                for tbl in page.extract_tables() or []:
                    row_texts = []
                    for row in tbl:
                        if row:
                            row_texts.append("; ".join(cell or "" for cell in row))
                    if row_texts:
                        tables.append(row_texts)

                # Zet tabellen ook in text zodat ze indexeerbaar zijn
                table_texts = ["; ".join(r) for r in tables]
                if table_texts:
                    text += "\n\n" + "\n".join(table_texts)

                docs.append({
                    "id": f"{pgs_label}-page-{i}",
                    "type": "page",
                    "pgs": pgs_label,
                    "title": f"Page {i}",
                    "text": text,
                    "items": [],
                    "grondslag": [],
                    "doelen": [],
                    "scenarios": [],
                    "tables": tables,
                    "source": source_url,
                })

    return fix_json_encoding(docs)

