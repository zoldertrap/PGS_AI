import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://publicatiereeksgevaarlijkestoffen.nl"

url = f"{BASE_URL}/publicaties/"
response = requests.get(url)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Alle links ophalen
links = [a["href"] for a in soup.find_all("a", href=True)]

# Filter: alleen PGS-links
pgs_links = [urljoin(BASE_URL, link) for link in links if "pgs" in link.lower()]

# Duplicaten verwijderen en sorteren
pgs_links = sorted(set(pgs_links))

# Printen
for link in pgs_links:
    print(link)
    
with open("pgs_links.txt", "w") as f:
    for link in pgs_links:
        f.write(link + "\n")
