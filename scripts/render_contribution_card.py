
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "contributions.json"
OUTPUT_FILE = ROOT / "dist" / "contribution-total.svg"

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
total = int(data["total_contributions_all_time"])
updated = escape(data["updated_at"][:10])

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="495" height="150" viewBox="0 0 495 150"
     role="img" aria-labelledby="title desc">
  <title id="title">GitHub All-Time Contributions</title>
  <desc id="desc">Total contributions across available contribution years.</desc>
  <rect width="495" height="150" rx="14"
        fill="#07111F" stroke="#123B5D"/>
  <text x="25" y="35" fill="#CDEFFF"
        font-family="Arial, sans-serif" font-size="15">
    GITHUB CONTRIBUTIONS
  </text>
  <text x="25" y="91" fill="#67E8F9"
        font-family="Arial, sans-serif" font-size="43"
        font-weight="700">{total:,}</text>
  <text x="27" y="119" fill="#7F9DB5"
        font-family="Arial, sans-serif" font-size="12">
    ALL-TIME TOTAL · UPDATED {updated}
  </text>
  <rect x="440" y="25" width="28" height="4" rx="2"
        fill="#38BDF8"/>
</svg>
"""

OUTPUT_FILE.write_text(svg, encoding="utf-8")
print(f"Generated contribution card: {OUTPUT_FILE}")
print(f"All-time contributions: {total:,}")
