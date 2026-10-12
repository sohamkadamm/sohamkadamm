
import json
import os
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import requests

USERNAME = "sohamkadamm"
GRAPHQL_URL = "https://api.github.com/graphql"

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "data" / "contributions.json"

LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def graphql_request(token, query, variables):
    response = requests.post(
        GRAPHQL_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "query": query,
            "variables": variables,
        },
        timeout=30,
    )

    response.raise_for_status()
    result = response.json()

    if result.get("errors"):
        raise RuntimeError(
            f"GitHub GraphQL error: {result['errors']}"
        )

    return result["data"]


def fetch_contributions():
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is missing. "
            "Run this script through GitHub Actions "
            "or set the environment variable locally."
        )

    print(f"Fetching contribution history for {USERNAME}...")

    # Fetch the years supported by GitHub's contribution API.
    years_query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionYears
        }
      }
    }
    """

    result = graphql_request(
        token,
        years_query,
        {"login": USERNAME},
    )

    user = result.get("user")

    if not user:
        raise RuntimeError(
            f"GitHub user not found: {USERNAME}"
        )

    years = sorted(
        set(
            user["contributionsCollection"]["contributionYears"]
        )
    )

    if not years:
        raise RuntimeError(
            "GitHub returned no contribution years."
        )

    print(
        f"Checking contribution history from "
        f"{years[0]} to {years[-1]}..."
    )

    calendar_query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                contributionLevel
              }
            }
          }
        }
      }
    }
    """

    today = datetime.now(timezone.utc).date()
    cutoff = today - timedelta(days=370)

    all_time_total = 0
    recent_days = {}

    for year in years:
        start = datetime.combine(
            date(year, 1, 1),
            time.min,
            tzinfo=timezone.utc,
        )

        if year == today.year:
            end = datetime.now(timezone.utc)
        else:
            end = datetime.combine(
                date(year, 12, 31),
                time.max,
                tzinfo=timezone.utc,
            )

        result = graphql_request(
            token,
            calendar_query,
            {
                "login": USERNAME,
                "from": start.isoformat(),
                "to": end.isoformat(),
            },
        )

        user_data = result.get("user")

        if not user_data:
            raise RuntimeError(
                f"Could not retrieve contribution data for {year}."
            )

        calendar = user_data["contributionsCollection"][
            "contributionCalendar"
        ]

        yearly_total = calendar["totalContributions"]
        all_time_total += yearly_total

        print(f"{year}: {yearly_total} contributions")

        for week in calendar["weeks"]:
            for day_data in week["contributionDays"]:
                day_date = date.fromisoformat(
                    day_data["date"]
                )

                if cutoff <= day_date <= today:
                    recent_days[day_data["date"]] = {
                        "date": day_data["date"],
                        "level": LEVELS[
                            day_data["contributionLevel"]
                        ],
                        "count": day_data["contributionCount"],
                    }

    days = sorted(
        recent_days.values(),
        key=lambda item: item["date"],
    )

    if not days:
        raise RuntimeError(
            "GitHub returned no recent calendar days."
        )

    data = {
        "username": USERNAME,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_contributions_all_time": all_time_total,
        "contribution_years": years,
        "heatmap_period": "Last 371 days",
        "days": days,
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    print(f"All-time contributions: {all_time_total}")
    print(f"Recent calendar days: {len(days)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    fetch_contributions()
