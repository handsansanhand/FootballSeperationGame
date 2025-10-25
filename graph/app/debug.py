import requests
from bs4 import BeautifulSoup
import time

base_url = "https://www.transfermarkt.co.uk/meisteeinsaetze/gesamteinsaetze/statistik/2025/ajax/yw1/saison_id/2025/selectedOptionKey/GB1/land_id/0/altersklasse/alle/yt0/Show/plus/1/galerie/0"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

page = 1

url = f"{base_url}?ajax=yw1"
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

rows = soup.find_all("tr", class_=["odd", "even"])

print(f"Found {len(rows)} player rows on page 1.\n")

for idx, row in enumerate(rows[:5], start=1):  # just show first 5 players for clarity
    cols = [td.text.strip() for td in row.find_all("td")]
    print(f"\n=== Player {idx} ===")
    for i, val in enumerate(cols):
        print(f"[{i}] {val}")