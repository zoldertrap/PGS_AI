import re, json, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://publicatiereeksgevaarlijkestoffen.nl/publicaties/"

# ---- Helpers ----
def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def parse_measure(section, source, pgs_id):
    measure_id = section.find("span", class_="label")
    measure_num = clean(measure_id.get_text()) if measure_id else None

    title_span = section.find("span", class_="title")
    title = clean(title_span.get_text()) if title_span else ""

    details = section.find("div", class_="details")
    text = clean(details.get_text(" ", strip=True)) if details else ""
    items = [clean(li.get_text(" ", strip=True)) for li in details.find_all("li")] if details else []

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

    return {
        "id": measure_num,
        "type": "measure",
        "pgs": pgs_id,
        "title": title,
        "text": text,
        "items": items,
        "grondslag": grondslag,
        "doelen": doelen,
        "scenarios": scenarios,
        "source": source,
    }

def parse_section(section, source, pgs_id):
    heading = section.find(["h1","h2","h3","h4","h5","h6"])
    if not heading:
        return None

    section_id = section.get("id") or clean(heading.get_text())
    title = clean(heading.get_text(" ", strip=True))

    text = clean(section.get_text(" ", strip=True))
    items = [clean(li.get_text(" ", strip=True)) for li in section.find_all("li")]

    tables = []
    for table in section.find_all("table"):
        headers = [clean(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        for ri, tr in enumerate(table.find_all("tr")):
            cells = [clean(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
            if not cells:
                continue
            if headers and len(cells) == len(headers):
                row_text = "; ".join(f"{h}: {c}" for h, c in zip(headers, cells))
            else:
                row_text = "; ".join(cells)
            tables.append(row_text)

    return {
        "id": section_id,
        "type": "section",
        "pgs": pgs_id,
        "title": title,
        "text": text,
        "items": items,
        "tables": tables,
        "source": source,
    }

# ---- Main ----
if __name__ == "__main__":
    # alle PGS links definieren (of ophalen via scraping)
    PGS_LINKS = [
        "/publicaties/pgs1/","/publicaties/pgs2/","/publicaties/pgs3/",
        "/publicaties/pgs4/","/publicaties/pgs5/","/publicaties/pgs6/",
        "/publicaties/pgs7/","/publicaties/pgs8/","/publicaties/pgs9/",
        "/publicaties/pgs10/","/publicaties/pgs11/","/publicaties/pgs12/",
        "/publicaties/pgs13/","/publicaties/pgs14/","/publicaties/pgs15/",
        "/publicaties/pgs16/","/publicaties/pgs17/","/publicaties/pgs18/",
        "/publicaties/pgs19/","/publicaties/pgs20/","/publicaties/pgs21/",
        "/publicaties/pgs22/","/publicaties/pgs23/","/publicaties/pgs24/",
        "/publicaties/pgs25/","/publicaties/pgs26/","/publicaties/pgs27/",
        "/publicaties/pgs28/","/publicaties/pgs29/","/publicaties/pgs30/",
        "/publicaties/pgs31/","/publicaties/pgs32/","/publicaties/pgs33-1/",
        "/publicaties/pgs33-2/","/publicaties/pgs34/","/publicaties/pgs35/",
        "/publicaties/pgs36/","/publicaties/pgs37-1/","/publicaties/pgs37-2/",
        "/publicaties/pgs38/","/publicaties/pgs39/","/publicaties/pgs40/",
    ]

    docs = []

    for rel_url in PGS_LINKS:
        url = urljoin(BASE, rel_url)
        pgs_id = rel_url.strip("/").upper()   # bv "PGS15" of "PGS33-1"

        print(f"🔎 Bezig met {pgs_id} ({url})...")
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"⚠️  Fout bij {url}: {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        for sec in soup.find_all("section"):
            if "measure" in sec.get("class", []):
                docs.append(parse_measure(sec, url, pgs_id))
            else:
                parsed = parse_section(sec, url, pgs_id)
                if parsed:
                    docs.append(parsed)

    with open("all_pgs_docs.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(docs)} items opgeslagen uit {len(PGS_LINKS)} PGS-publicaties")
