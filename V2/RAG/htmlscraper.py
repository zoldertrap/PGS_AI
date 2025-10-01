import re
from bs4 import BeautifulSoup
from RAG.encoding import fix_json_encoding


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def parse_block(section, base_url: str, pgs_label: str):
    """Parse een sectie (maatregel, doel, scenario of gewone sectie)."""
    label_span = section.select_one("span.label")
    label = clean(label_span.get_text()) if label_span else None

    title_span = section.find("span", class_="title")
    title = clean(title_span.get_text()) if title_span else ""

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

    tables = []
    for table in section.find_all("table"):
        headers = [clean(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        for tr in table.find_all("tr"):
            cells = [clean(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
            if not cells:
                continue
            if headers and len(cells) == len(headers):
                row_text = "; ".join(f"{h}: {c}" for h, c in zip(headers, cells))
            else:
                row_text = "; ".join(cells)
            tables.append(row_text)

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
        "text": text,
        "items": items,
        "grondslag": grondslag,
        "doelen": doelen,
        "scenarios": scenarios,
        "tables": tables,
        "source": base_url,
    }


def parse_html_file(html_path: str, source_url: str, pgs_label: str):
    """Parse een opgeslagen HTML-bestand in gestructureerde docs."""
    docs = []
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    for sec in soup.find_all("section"):
        parsed = parse_block(sec, source_url, pgs_label)
        if parsed:
            docs.append(parsed)

    return fix_json_encoding(docs)
