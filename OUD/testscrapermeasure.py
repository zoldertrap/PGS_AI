import re
import requests
from bs4 import BeautifulSoup

def check_measures(url):
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Kon {url} niet ophalen: {e}")
        return

    soup = BeautifulSoup(resp.text, "lxml")

    # Zoek naar spans met class="label" die beginnen met M
    measures = []
    for span in soup.find_all("span", class_="label"):
        txt = span.get_text(strip=True)
        if re.match(r"^M\d+", txt, re.I):
            measures.append(txt)

    if measures:
        print(f"✅ Gevonden maatregelen op {url}: {measures[:10]}{' ...' if len(measures) > 10 else ''}")
    else:
        print(f"❌ Geen Mxx labels gevonden op {url}")

if __name__ == "__main__":
    url = "https://publicatiereeksgevaarlijkestoffen.nl/publicaties/online/pgs-15/2023/0-1-november-2023"
    check_measures(url)
