import re, json, requests
from bs4 import BeautifulSoup
from parameters import BASE_URL

def clean(s):
    """Helper: verwijdert dubbele spaties en trims tekst"""
    return re.sub(r"\s+", " ", s or "").strip()

def parse_block(section):
    """
    Parse een sectie, maatregel, doel of scenario.
    Herkent type op basis van ID-label (Mxx, Dxx, Sxx) of valt terug naar 'section'.
    """
    label_span = section.find("span", class_="label")
    label = clean(label_span.get_text()) if label_span else None

    title_span = section.find("span", class_="title")
    title = clean(title_span.get_text()) if title_span else ""

    details = section.find("div", class_="details")
    text = clean(details.get_text(" ", strip=True)) if details else clean(section.get_text(" ", strip=True))

    items = []
    if details:
        items = [clean(li.get_text(" ", strip=True)) for li in details.find_all("li")]
    else:
        items = [clean(li.get_text(" ", strip=True)) for li in section.find_all("li")]

    # Grondslag
    grondslag = [clean(span.get_text(" ", strip=True)) for span in section.select("div.bases span.content")]

    # Gerelateerde doelen
    doelen = []
    for a in section.select("section.goals a"):
        doelen.append({
            "id": clean(a.find("span", class_="label").get_text()),
            "title": clean(a.find("span", class_="title").get_text())
        })

    # Gerelateerde scenario’s
    scenarios = []
    for a in section.select("section.scenarios a"):
        scenarios.append({
            "id": clean(a.find("span", class_="label").get_text()),
            "title": clean(a.find("span", class_="title").get_text())
        })

    # Tabellen
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

    # Type bepalen
    if label:
        if label.startswith("M"):
            node_type = "measure"
        elif label.startswith("D"):
            node_type = "goal"
        elif label.startswith("S"):
            node_type = "scenario"
        else:
            node_type = "section"
    else:
        node_type = "section"

    return {
        "id": label or (section.get("id") or title),
        "type": node_type,
        "title": title,
        "text": text,
        "items": items,
        "grondslag": grondslag,
        "doelen": doelen,
        "scenarios": scenarios,
        "tables": tables,
        "source": BASE_URL,
    }

if __name__ == "__main__":
    resp = requests.get(BASE_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    docs = []
    for sec in soup.find_all("section"):
        parsed = parse_block(sec)
        if parsed:
            docs.append(parsed)

    with open("docs.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(docs)} documenten opgeslagen (maatregelen + doelen + scenario’s + secties)")
