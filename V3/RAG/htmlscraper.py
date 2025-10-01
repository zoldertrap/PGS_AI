import re
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
from RAG.encoding import fix_json_encoding


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def parse_block(section, base_url: str, pgs_label: str):
    """Parse een sectie (maatregel, doel, scenario of gewone sectie)."""
    label_span = section.select_one("span.label")
    label = clean(label_span.get_text()) if label_span else None

    title_span = section.find("span", class_="title")
    title = clean(title_span.get_text()) if title_span else "Ongetitelde sectie"

    details = section.find("div", class_="details")
    text = clean(details.get_text(" ", strip=True)) if details else clean(section.get_text(" ", strip=True))

    items = [
        clean(li.get_text(" ", strip=True))
        for li in (details.find_all("li") if details else section.find_all("li"))
    ]

    grondslag = [clean(span.get_text(" ", strip=True)) for span in section.select("div.bases span.content")]

    doelen = []
    for a in section.select("section.goals a"):
        doelen.append({
            "id": clean(a.find("span", class_="label").get_text()),
            "title": clean(a.find("span", class_="title").get_text())
        })

    scenarios = []
    for a in section.select("section.scenarios a"):
        scenarios.append({
            "id": clean(a.find("span", class_="label").get_text()),
            "title": clean(a.find("span", class_="title").get_text())
        })

    # --- Verbeterde tabel-parsing (met headers + caption + links) ---
    tables = []
    table_texts = []  # extra voor indexing in "text"
    for table in section.find_all("table"):
        rows = []

        # Neem caption mee (als die er is)
        caption = table.find("caption")
        if caption:
            cap_text = clean(caption.get_text(" ", strip=True))
            if cap_text:
                table_texts.append(f"Caption: {cap_text}")

        headers = [clean(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        for tr in table.find_all("tr"):
            cells = []
            row_text_parts = []
            for j, td in enumerate(tr.find_all("td")):
                link = td.find("a", href=True)
                if link:
                    txt = clean(link.get_text(" ", strip=True))
                    url = link["href"]
                    cells.append({"text": txt, "url": url})
                    col_name = headers[j] if j < len(headers) and headers[j] else f"kolom{j+1}"
                    row_text_parts.append(f"{col_name}: {txt} ({url})")
                else:
                    txt = clean(td.get_text(" ", strip=True))
                    cells.append({"text": txt, "url": None})
                    col_name = headers[j] if j < len(headers) and headers[j] else f"kolom{j+1}"
                    row_text_parts.append(f"{col_name}: {txt}")
            if cells:
                rows.append(cells)
                if row_text_parts:
                    table_texts.append("; ".join(row_text_parts))
        if rows:
            tables.append(rows)

    # Tabellen ook toevoegen aan text zodat ze worden geïndexeerd
    if table_texts:
        text += "\n\nTabellen:\n" + "\n".join(table_texts)

    node_type = "section"
    if label:
        if label.upper().startswith("M"):
            node_type = "measure"
        elif label.upper().startswith("D"):
            node_type = "goal"
        elif label.upper().startswith("S"):
            node_type = "scenario"
    elif title and re.match(r"^M\d+", title.strip(), re.I):
        label = title.split()[0]
        node_type = "measure"

    return {
        "id": f"{pgs_label}-{node_type}-{label or section.get('id') or title[:30]}",
        "type": node_type,
        "pgs": pgs_label,
        "title": title,
        "text": text,        # <-- nu bevat ook titels + tabellen (incl. caption)
        "items": items,
        "grondslag": grondslag,
        "doelen": doelen,
        "scenarios": scenarios,
        "tables": tables,    # <-- structured tables blijven behouden
        "source": base_url,
    }



def parse_html_file(html_path: str, source_url: str, pgs_label: str):
    """Parse een opgeslagen HTML-bestand in gestructureerde docs met encoding-detectie."""
    docs = []
    with open(html_path, "rb") as f:   # lees als bytes
        raw = f.read()

    converted = UnicodeDammit(raw)     # detect & fix encoding
    soup = BeautifulSoup(converted.unicode_markup, "lxml")

    for sec in soup.find_all("section"):
        parsed = parse_block(sec, source_url, pgs_label)
        if parsed:
            docs.append(parsed)

    return fix_json_encoding(docs)
