
import json
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "data" / "contributions.json"
OUTPUT_FILE = ROOT / "contrib-heatmap.svg"

# GitHub-inspired contribution colors, from least to most active.
COLORS = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
]

CELL_SIZE = 11
GAP = 4
STEP = CELL_SIZE + GAP
LEFT = 48
TOP = 42


def render_heatmap():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "Contribution data not found. Run fetch_contributions.py first."
        )

    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    days = data["days"]

    if not days:
        raise ValueError("The contribution data contains no days.")

    # Build a date-to-level lookup.
    levels = {}

    for item in days:
        try:
            parsed_date = date.fromisoformat(item["date"])
            level = int(item["level"])
        except (ValueError, KeyError, TypeError):
            continue

        if 0 <= level <= 4:
            levels[parsed_date] = level

    if not levels:
        raise ValueError("No valid contribution levels were found.")

    first_date = min(levels)
    last_date = max(levels)

    # Align the grid to Sunday, like GitHub's contribution calendar.
    start_date = date.fromordinal(
        first_date.toordinal() - (first_date.weekday() + 1) % 7
    )
    end_date = date.fromordinal(
        last_date.toordinal() + (6 - (last_date.weekday() + 1) % 7)
    )

    weeks = ((end_date - start_date).days + 1) // 7
    width = max(860, LEFT + weeks * STEP + 20)
    height = TOP + 7 * STEP + 32

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        """
        <style>
          .day {
            opacity: 0;
            animation: reveal 0.22s ease-out forwards;
          }
          @keyframes reveal {
            from { opacity: 0; }
            to { opacity: 1; }
          }
          .label {
            fill: #8b949e;
            font: 10px sans-serif;
          }
          @media (prefers-reduced-motion: reduce) {
            .day { animation: none; opacity: 1; }
          }
        </style>
        """,
        '<rect width="100%" height="100%" fill="#0d1117" rx="8"/>',
        '<text x="12" y="20" fill="#c9d1d9" '
        'font-family="monospace" font-size="12">'
        'sohamkadamm@github:~$ contributions</text>',
    ]

    # Weekday labels.
    for label, row in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
        y = TOP + row * STEP + CELL_SIZE - 2
        parts.append(
            f'<text x="7" y="{y}" class="label">{label}</text>'
        )

    current = start_date

    while current <= end_date:
        days_since_start = (current - start_date).days
        week = days_since_start // 7
        row = (current.weekday() + 1) % 7

        level = levels.get(current, 0)
        x = LEFT + week * STEP
        y = TOP + row * STEP

        parts.append(
            f'<rect class="day" x="{x}" y="{y}" '
            f'width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2" '
            f'fill="{COLORS[level]}" '
            f'style="animation-delay:{days_since_start * 0.002:.3f}s">'
            f'<title>{escape(current.isoformat())}: '
            f'activity level {level}</title></rect>'
        )

        current = date.fromordinal(current.toordinal() + 1)

    # Legend.
    legend_y = height - 17
    parts.append(
        f'<text x="{LEFT}" y="{legend_y}" class="label">Less</text>'
    )

    legend_x = LEFT + 32

    for level, color in enumerate(COLORS):
        x = legend_x + level * STEP
        parts.append(
            f'<rect x="{x}" y="{legend_y - 10}" '
            f'width="{CELL_SIZE}" height="{CELL_SIZE}" '
            f'rx="2" fill="{color}"/>'
        )

    parts.append(
        f'<text x="{legend_x + 5 * STEP}" y="{legend_y}" '
        f'class="label">More</text>'
    )

    parts.append("</svg>")

    OUTPUT_FILE.write_text("\n".join(parts), encoding="utf-8")

    print("Heatmap SVG generated successfully!")
    print(f"Date range: {first_date} to {last_date}")
    print(f"Weeks displayed: {weeks}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    render_heatmap()
