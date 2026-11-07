import os
import json
import requests
from datetime import datetime, timezone

API_KEY = os.environ["ODDS_API_KEY"]
BASE = "https://api.the-odds-api.com/v4"
SPORTS = ["soccer_italy_serie_a", "soccer_epl", "soccer_spain_la_liga"]
MARKETS = {"h2h": "1X2", "totals": "Over/Under 2.5"}
results = []

for sport in SPORTS:
    for market, label in MARKETS.items():
        try:
            response = requests.get(
                f"{BASE}/sports/{sport}/odds/",
                params={
                    "apiKey": API_KEY,
                    "regions": "eu",
                    "markets": market,
                    "oddsFormat": "decimal"
                },
                timeout=20
            )
            response.raise_for_status()
            matches = response.json()
        except Exception as exc:
            print(f"Errore {sport}/{market}: {exc}")
            continue

        for match in matches:
            best = {}
            for book in match.get("bookmakers", []):
                for group in book.get("markets", []):
                    if group.get("key") != market:
                        continue
                    for outcome in group.get("outcomes", []):
                        if market == "totals":
                            if outcome.get("point") != 2.5:
                                continue
                            key = outcome["name"]
                        else:
                            key = outcome["name"]
                        price = outcome.get("price", 0)
                        if price > best.get(key, {}).get("price", 0):
                            best[key] = {
                                "price": price,
                                "bookmaker": book["title"]
                            }

            expected = 3 if market == "h2h" else 2
            if len(best) != expected:
                continue
            implied = sum(1 / item["price"] for item in best.values())
            if implied <= 1 / 1.01:
                results.append({
                    "match": match["home_team"] + " - " + match["away_team"],
                    "market": label,
                    "implied": round(implied * 100, 3),
                    "profit_percent": round((1 / implied - 1) * 100, 3),
                    "outcomes": best,
                    "commence_time": match.get("commence_time")
                })

with open("surebets.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "surebets": results
    }, f, ensure_ascii=False, indent=2)

print(f"Trovate {len(results)} potenziali surebet")
