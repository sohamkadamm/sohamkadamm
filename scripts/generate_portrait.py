
from pathlib import Path
from PIL import (
    Image,
    ImageOps,
    ImageEnhance,
    ImageFilter,
)
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
PHOTO = ROOT / "portrait.jpg"
OUTPUT = ROOT / "portrait.svg"

# Blue and cyan terminal theme
BACKGROUND = "#07111F"
CYAN = "#67E8F9"
BLUE = "#38BDF8"
TEXT = "#CDEFFF"

# Smooth brightness progression: shadows to highlights
RAMP = "  ..,:;irsXA253hMHGS#9B&@"

# Higher resolution for eyes, nose, hair, and smile
COLUMNS = 220
FONT_SIZE = 5.5
CHAR_WIDTH = 3.5
LINE_HEIGHT = 6.5

# Crop: left, top, right, bottom as fractions of photo dimensions.
# Focus on the head and shoulders instead of the full torso.
CROP = (0.04, 0.01, 0.96, 0.79)

# Image-detail tuning
CONTRAST = 1.8
SHARPNESS = 1.7
EDGE_BLEND = 0.28
EDGE_BOOST = 0.85
BACKGROUND_BLUE_REDUCTION = 0.40


def load_photo():
    """Load the portrait and crop around the face and shoulders."""

    if not PHOTO.is_file():
        raise FileNotFoundError(
            f"Photo not found: {PHOTO}\n"
            "Place your photo in the repository root as portrait.jpg."
        )

    with Image.open(PHOTO) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")

    width, height = image.size
    left, top, right, bottom = CROP

    image = image.crop((
        round(width * left),
        round(height * top),
        round(width * right),
        round(height * bottom),
    ))

    return image


def reduce_blue_background(image):
    """Reduce blue/purple background intensity while preserving skin detail."""

    pixels = []

    for red, green, blue in image.getdata():
        # Detect strongly blue pixels relative to red and green.
        blue_excess = max(0, blue - red - 15)

        if blue > red * 1.12 and blue > green * 0.95:
            reduction = (
                blue_excess / 255
            ) * BACKGROUND_BLUE_REDUCTION

            factor = max(0.45, 1.0 - reduction)

            red = round(red * factor)
            green = round(green * factor)
            blue = round(blue * factor)

        pixels.append((red, green, blue))

    result = Image.new("RGB", image.size)
    result.putdata(pixels)
    return result


def prepare_images(image):
    """Create a detailed grayscale image and a facial contour map."""

    image = reduce_blue_background(image)

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray, cutoff=0.5)
    gray = ImageEnhance.Contrast(gray).enhance(CONTRAST)
    gray = ImageEnhance.Sharpness(gray).enhance(SHARPNESS)

    # Fine contours capture eyebrows, eyes, nose, lips, and hair.
    softened = gray.filter(ImageFilter.GaussianBlur(radius=0.55))
    edges = softened.filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.autocontrast(edges, cutoff=1)

    return gray, edges


def convert_to_ascii(gray, edges):
    """Blend tonal shading and contours into a high-detail ASCII portrait."""

    rows = max(
        1,
        round(
            COLUMNS
            * gray.height
            / gray.width
            * 0.58
        ),
    )

    size = (COLUMNS, rows)

    # Resize both maps identically to keep the contours aligned.
    gray = gray.resize(size, Image.Resampling.LANCZOS)
    edges = edges.resize(size, Image.Resampling.LANCZOS)

    tones = list(gray.getdata())
    contours = list(edges.getdata())
    lines = []

    ramp_max = len(RAMP) - 1

    for y in range(rows):
        chars = []

        for x in range(COLUMNS):
            pos = y * COLUMNS + x

            tone = tones[pos]
            edge = contours[pos]

            # Preserve the original shading while emphasizing contours.
            value = (
                tone * (1.0 - EDGE_BLEND)
                + max(tone, edge * EDGE_BOOST) * EDGE_BLEND
            )

            value = max(0, min(255, round(value)))

            # Map each pixel's brightness to a character.
            index = round(value * ramp_max / 255)
            index = max(0, min(index, ramp_max))

            chars.append(RAMP[index])

        lines.append("".join(chars))

    return lines, rows


def generate_portrait():
    """Generate the animated terminal-style ASCII portrait."""

    photo = load_photo()
    original_size = photo.size

    gray, edges = prepare_images(photo)
    lines, rows = convert_to_ascii(gray, edges)

    padding = 14
    header_height = 40
    footer_height = 38

    svg_width = round(COLUMNS * CHAR_WIDTH + padding * 2)
    svg_height = round(
        header_height + rows * LINE_HEIGHT + footer_height
    )

    parts = [
        (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{svg_width}" height="{svg_height}" '
            f'viewBox="0 0 {svg_width} {svg_height}">'
        ),
        """
        <style>
          .terminal-text {
            font-family: Consolas, "Courier New", monospace;
            font-weight: 600;
            white-space: pre;
          }

          .line {
            opacity: 0;
            animation: reveal 0.45s ease forwards;
          }

          @keyframes reveal {
            from { opacity: 0; }
            to { opacity: 1; }
          }

          @media (prefers-reduced-motion: reduce) {
            .line {
              opacity: 1;
              animation: none;
            }
          }
        </style>
        """,
        f'<rect width="100%" height="100%" rx="12" fill="{BACKGROUND}"/>',
        '<circle cx="17" cy="17" r="4" fill="#FF5F57"/>',
        '<circle cx="31" cy="17" r="4" fill="#FEBC2E"/>',
        '<circle cx="45" cy="17" r="4" fill="#28C840"/>',
        (
            f'<text x="62" y="21" fill="{TEXT}" '
            'font-family="monospace" font-size="10">'
            'sohamkadamm@github: ~/portrait</text>'
        ),
        (
            f'<line x1="10" y1="31" x2="{svg_width - 10}" y2="31" '
            'stroke="#164E63"/>'
        ),
    ]

    start_y = header_height + 3

    for y, line in enumerate(lines):
        color = CYAN if y % 4 in (1, 2) else BLUE
        delay = y * 0.012

        parts.append(
            f'<text x="{padding}" '
            f'y="{start_y + y * LINE_HEIGHT:.2f}" '
            f'font-size="{FONT_SIZE}" '
            'class="terminal-text line" '
            f'fill="{color}" '
            f'style="animation-delay:{delay:.3f}s">'
            f'{escape(line)}</text>'
        )

    footer_y = round(start_y + rows * LINE_HEIGHT + 18)

    parts.append(
        f'<text x="{padding}" y="{footer_y}" fill="{TEXT}" '
        'font-family="monospace" font-size="10">'
        'LEARN. BUILD. IMPROVE. REPEAT.'
        '</text>'
    )

    parts.append("</svg>")

    OUTPUT.write_text("\n".join(parts), encoding="utf-8")

    print("Detailed ASCII portrait generated successfully!")
    print(f"Source photo: {PHOTO}")
    print(f"Original dimensions: {original_size}")
    print(f"ASCII dimensions: {COLUMNS} x {rows}")
    print(f"SVG dimensions: {svg_width} x {svg_height}")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    generate_portrait()
