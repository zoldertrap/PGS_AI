import re, json, requests
from bs4 import BeautifulSoup
from parameters import BASE_URLS  # lijst met urls naar verschillende PGS-publicaties
from pdfminer.high_level import extract_text
import pathlib
from chunking import chunk_text





def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def parse_block(section, base_url, pgs_label):
    """Parse maatregel, doel, scenario of gewone sectie"""
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


def scrape_pdf(pdf_path: str, source_url: str, pgs_label: str):
    """Extracts text from PDF and wraps in the same schema as your HTML scraper"""
    text = extract_text(pdf_path)
    chunks = text.split("\f")  # split on page breaks

    docs = []
    for i, page in enumerate(chunks):
        docs.append({
            "id": f"{pgs_label}-p{i+1}",
            "type": "page",
            "pgs": pgs_label,
            "title": f"Page {i+1}",
            "text": page.strip(),
            "items": [],
            "grondslag": [],
            "doelen": [],
            "scenarios": [],
            "tables": [],
            "source": source_url,
        })
    return docs


if __name__ == "__main__":
    all_docs = []

    for url in BASE_URLS:
        # PGS-label uit URL (bv. "pgs-15")
        match = re.search(r"(pgs-\d+)", url)
        pgs_label = match.group(1).upper() if match else "UNKNOWN"

        print(f"🔎 Scraping {pgs_label} ({url}) ...")

        if url.endswith(".pdf"):
            # PDF download + parse
            resp = requests.get(url)
            resp.raise_for_status()
            pdf_path = f"{pgs_label}.pdf"
            with open(pdf_path, "wb") as f:
                f.write(resp.content)

            pdf_docs = scrape_pdf(pdf_path, url, pgs_label)
            all_docs.extend(pdf_docs)

        else:
            # HTML parse
            resp = requests.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            for sec in soup.find_all("section"):
                parsed = parse_block(sec, url, pgs_label)
                if parsed:
                    all_docs.append(parsed)

    print(f"📄 {len(all_docs)} documenten scraped")

    # 🔹 Step 2: Chunk the docs
    chunked_docs = []
    for doc in all_docs:
        if not doc["text"]:
            continue
        for i, chunk in enumerate(chunk_text(doc["text"], 400)):
            chunked_docs.append({
                **doc,
                "id": f"{doc['id']}-c{i+1}",
                "text": chunk
            })

    print(f"✂️  {len(chunked_docs)} chunks gemaakt uit {len(all_docs)} docs")

    # Alles in één bestand
    with open("docs.json", "w", encoding="utf-8") as f:
        json.dump(chunked_docs, f, ensure_ascii=False, indent=2)

    print(f"✅ docs.json opgeslagen ({len(chunked_docs)} chunks)")
