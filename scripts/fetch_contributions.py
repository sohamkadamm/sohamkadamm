
import json
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "sohamkadamm"
URL = f"https://github.com/users/{USERNAME}/contributions"

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "data" / "contributions.json"


def fetch_contributions():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html",
    }

    print(f"Fetching contributions for {USERNAME}...")

    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day")

    if not cells:
        cells = soup.select("[data-date][data-level]")

    if not cells:
        raise RuntimeError("No contribution calendar cells found.")

    days = []

    for cell in cells:
        date = cell.get("data-date")
        level = cell.get("data-level")

        if date and level is not None:
            days.append({
                "date": date,
                "level": int(level),
            })

    if not days:
        raise RuntimeError("No valid contribution days found.")

    data = {
        "username": USERNAME,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_days": len(days),
        "days": days,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    print(f"Days retrieved: {len(days)}")
    print("Contribution levels saved successfully.")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    fetch_contributions()
