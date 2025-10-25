import requests
from bs4 import BeautifulSoup
import time
import csv
import sys
from datetime import datetime

BASE_SITE = "https://www.transfermarkt.co.uk"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

start_season = 2025
num_seasons_back = 36  # how many seasons to go back

leagues = [
    ("ligue_2", "FR2"),
]

def safe_get(url, retries=10, delay=5, timeout=10):
    """Try GET request with retries and timeout handling."""
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                return r
            else:
                print(f"⚠️ HTTP {r.status_code} on attempt {attempt}/{retries}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request failed ({e}) — attempt {attempt}/{retries}")
        time.sleep(delay)
    print(f"❌ Failed to fetch {url} after {retries} retries.")
    return None


def save_csv(league_name, data):
    output_file = f"{league_name}_{start_season}_cumulative.csv"
    fieldnames = ["player_name", "age", "nationality", "team_name", "start_year", "end_year", "appearances", "league_name"]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data.values())
    print(f"💾 Saved {len(data)} cumulative player-team records to {output_file}")


def scrape_league(league_name, league_code):
    print(f"\n==============================")
    print(f"⚽ Starting scrape for {league_name}")
    print(f"==============================")

    player_team_data = {}

    for season_year in range(start_season, start_season - num_seasons_back, -1):
        print(f"\n🔹 Scraping season {season_year}")
        year_successful = True

        base_url = (
            f"{BASE_SITE}/meisteeinsaetze/gesamteinsaetze/statistik/{season_year}/ajax/yw1/"
            f"saison_id/{season_year}/selectedOptionKey/{league_code}/land_id/0/altersklasse/alle/"
            f"yt0/Show/plus/1/galerie/0/sort/einsaetze.desc"
        )

        page = 1
        stop_scraping = False

        while not stop_scraping:
            url = f"{base_url}?ajax=yw1" if page == 1 else f"{base_url}/page/{page}?ajax=yw1"
            print(f"Requesting {url}")

            r = safe_get(url)
            if not r:
                print(f"❌ Failed to fetch page {page} for {season_year}. Aborting entire program.")
                year_successful = False
                break

            soup = BeautifulSoup(r.text, "lxml")
            rows = soup.find_all("tr", class_=["odd", "even"])
            if not rows:
                print("No rows found — likely last page.")
                break

            for row in rows:
                tds = row.find_all("td")
                if len(tds) <= 11:
                    continue

                name_cell = row.find("td", class_="hauptlink")
                player_name = name_cell.a.text.strip() if name_cell and name_cell.a else None

                age_td = tds[5] if len(tds) > 5 else None
                age = int(age_td.text.strip()) if age_td and age_td.text.strip().isdigit() else None

                flag_img = row.find("img", class_="flaggenrahmen")
                nationality = flag_img["title"].strip() if flag_img and "title" in flag_img.attrs else None

                team_td = tds[7] if len(tds) > 7 else None
                team_name, league_name_cell = None, None
                if team_td:
                    links = team_td.find_all("a", title=True)
                    if len(links) >= 2:
                        team_name = links[1].text.strip()
                    if len(links) >= 3:
                        league_name_cell = links[2].text.strip()

                appearances_text = tds[11].text.strip().replace("-", "0")
                appearances = int(appearances_text) if appearances_text.isdigit() else 0

                if not player_name or not team_name:
                    continue
                if appearances == 0:
                    stop_scraping = True
                    break

                key = (player_name, team_name)
                if key in player_team_data:
                    player_team_data[key]["appearances"] += appearances
                    if season_year < player_team_data[key]["start_year"]:
                        player_team_data[key]["start_year"] = season_year
                else:
                    player_team_data[key] = {
                        "player_name": player_name,
                        "age": age,
                        "nationality": nationality,
                        "team_name": team_name,
                        "league_name": league_name_cell,
                        "start_year": season_year,
                        "end_year": season_year,
                        "appearances": appearances
                    }

            page += 1
            time.sleep(1.5)

        if not year_successful:
            print(f"🛑 Error during {season_year} for {league_name}. Stopping league early.")
            return False  # league failed

        save_csv(league_name, player_team_data)

    print(f"\n✅ Finished scraping {league_name}")
    return True


# Run all leagues sequentially
for name, code in leagues:
    success = scrape_league(name, code)
    if not success:
        print(f"❌ Stopping entire program due to failure in {name}")
        break

    # Optional: short cooldown between leagues
    print(f"⏸️ Cooling down before next league...\n")
    time.sleep(10)

print("\n🌍 All leagues processed.")
