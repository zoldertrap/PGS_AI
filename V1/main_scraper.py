import re
import json
import os
import time
import requests
from bs4 import BeautifulSoup
from scraper import parse_html_file, scrape_pdf
from chunking import chunk_text
from parameters import BASE, PGS_LINKS


OUTPUT_DIR = "PGS"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_full_urls():
    return [BASE.rstrip("/") + link for link in PGS_LINKS]


if __name__ == "__main__":
    all_docs = []

    for url in get_full_urls():
        match = re.search(r"(pgs[\d\-]+)", url)
        pgs_label = match.group(1).upper() if match else "UNKNOWN"

        print(f"🔎 Visiting {pgs_label} ({url}) ...")
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Failed to fetch landing page {url}: {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        # --- Step 1: detect 'Meest actuele versie' link ---
        pub_url = None
        for tag in soup.find_all(True):
            if "meest actuele versie" in tag.get_text(strip=True).lower():
                a = tag.find_parent("a", href=True)
                if a:
                    href = a["href"]
                    if not href.startswith("http"):
                        href = BASE.rstrip("/") + href
                    pub_url = href
                    break

        if not pub_url:
            print(f"⚠️ No 'Meest actuele versie' found for {pgs_label}")
            continue

        # --- Step 2: PDF or HTML ---
        if pub_url.lower().endswith(".pdf"):
            print(f"  ➜ Scraping PDF {pub_url}")
            try:
                resp = requests.get(pub_url, timeout=20)
                resp.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Failed to download PDF {pub_url}: {e}")
                continue

            pdf_path = os.path.join(OUTPUT_DIR, f"{pgs_label}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(resp.content)

            pdf_docs = scrape_pdf(pdf_path, pub_url, pgs_label)
            all_docs.extend(pdf_docs)

        else:
            print(f"  ➜ Scraping HTML {pub_url}")
            try:
                resp = requests.get(pub_url, timeout=20)
                resp.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Failed to fetch HTML {pub_url}: {e}")
                continue

            html_path = os.path.join(OUTPUT_DIR, f"{pgs_label}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(resp.text)

            html_docs = parse_html_file(html_path, pub_url, pgs_label)
            all_docs.extend(html_docs)

        time.sleep(0.5)

    print(f"📄 {len(all_docs)} raw docs scraped from {len(PGS_LINKS)} PGS pages")

    # --- Step 3: Chunking ---
    chunked_docs = []
    for doc in all_docs:
        if not doc.get("text"):
            continue
        for i, chunk in enumerate(chunk_text(doc["text"], 400)):
            chunked_docs.append({
                **doc,
                "id": f"{doc['id']}-c{i+1}",
                "text": chunk
            })

    print(f"✂️  {len(chunked_docs)} chunks created")

    docs_file = os.path.join(OUTPUT_DIR, "docs.json")
    with open(docs_file, "w", encoding="utf-8") as f:
        json.dump(chunked_docs, f, ensure_ascii=False, indent=2)

    print(f"✅ {docs_file} saved with {len(chunked_docs)} chunks")
