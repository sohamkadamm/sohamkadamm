
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
        "User-Agent": "Mozilla/5.0 (compatible; ContributionHeatmap/1.0)",
        "Accept": "text/html",
    }

    print(f"Fetching contributions for {USERNAME}...")

    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find contribution calendar cells.
    cells = soup.select(
        "td.ContributionCalendar-day, "
        "[data-date][data-level]"
    )

    days_by_date = {}

    for cell in cells:
        date = cell.get("data-date")
        level = cell.get("data-level")

        if not date or level is None:
            continue

        try:
            level = int(level)
        except (TypeError, ValueError):
            continue

        if 0 <= level <= 4:
            days_by_date[date] = {
                "date": date,
                "level": level,
            }

    days = sorted(
        days_by_date.values(),
        key=lambda day: day["date"],
    )

    if not days:
        raise RuntimeError(
            "No contribution days found. "
            "GitHub may have changed its page structure."
        )

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
    print(f"Output saved to: {OUTPUT_FILE}")
    print("Contribution data fetched successfully!")


if __name__ == "__main__":
    fetch_contributions()
