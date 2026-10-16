"""Bold 1280x720 thumbnail: the story's picture, brighter on the right, and big curiosity words on the left.

Layout: a small gold label with the figure's name (thumbnail_label, else myth_figure), then thumbnail_text
(2 to 4 words, the curiosity hook, e.g. "She Stopped the Sea") as large as fits, cream with a thick dark
outline so it reads on a phone. The left side is shaded so the words always stand out. Output: out/thumb.jpg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, load_episode, stamp_brand, story_image  # noqa: E402

BOLD = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
LABEL = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
CREAM, GOLD, INK = (255, 244, 222), (247, 190, 92), (12, 8, 4)
TEXT_W = 700  # the words stay in the left ~55% of the picture


def font(paths, size):
    from PIL import ImageFont
    for f in paths:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def wrap(d, words, f, width):
    lines, cur = [], []
    for w in words:
        if cur and d.textlength(" ".join(cur + [w]), font=f) > width:
            lines.append(" ".join(cur))
            cur = []
        cur.append(w)
    return lines + [" ".join(cur)] if cur else lines


def fit(d, text, width, max_lines=3):
    """The biggest font size (150 down to 70) at which text wraps into max_lines lines within width."""
    words = text.split()
    for size in range(150, 68, -6):
        f = font(BOLD, size)
        lines = wrap(d, words, f, width)
        if len(lines) <= max_lines and all(d.textlength(ln, font=f) <= width for ln in lines):
            return f, size, lines
    f = font(BOLD, 70)
    return f, 70, wrap(d, words, f, width)


def main(ep_path):
    import numpy as np
    from PIL import Image, ImageDraw, ImageEnhance
    ep = load_episode(ep_path)
    img = story_image(ep)
    w, h = img.size
    tw, th = (w, int(w * 9 / 16)) if w / h < 16 / 9 else (int(h * 16 / 9), h)
    img = img.crop(((w - tw) // 2, (h - th) // 2, (w - tw) // 2 + tw, (h - th) // 2 + th)).resize((1280, 720))
    # brighter and punchier than the video frame, so it stands out among other thumbnails
    img = ImageEnhance.Contrast(ImageEnhance.Brightness(img).enhance(0.95)).enhance(1.18)
    img = ImageEnhance.Color(img).enhance(1.2)
    # shade the left side (where the words go), fading out toward the right
    x = np.linspace(0, 1, 1280)[None, :, None]
    shade = np.clip(1 - x / 0.62, 0, 1) ** 1.4 * 0.72
    arr = np.asarray(img).astype("float32") * (1 - shade)
    img = Image.fromarray(arr.clip(0, 255).astype("uint8"))
    d = ImageDraw.Draw(img)

    text = (ep.get("thumbnail_text") or ep["story_title"]).strip()
    f, size, lines = fit(d, text, TEXT_W)
    label = (ep.get("thumbnail_label") or ep.get("myth_figure") or "").strip().upper()
    if label.lower() in text.lower():
        label = ""  # the words already name the figure
    lf = font(LABEL, 40)
    line_h = int(size * 1.08)
    block = len(lines) * line_h + (70 if label else 0)
    y = max(40, (720 - block) // 2 - 10)
    if label:
        d.text((64, y), label, font=lf, fill=GOLD, stroke_width=4, stroke_fill=INK)
        lw = d.textlength(label, font=lf)
        d.rectangle([64, y + 52, 64 + min(lw, 260), y + 57], fill=GOLD)
        y += 70
    for ln in lines:
        d.text((60, y), ln, font=f, fill=CREAM, stroke_width=max(6, size // 16), stroke_fill=INK)
        y += line_h
    img = stamp_brand(img, 120, 36, name_px=36)
    OUT.mkdir(exist_ok=True)
    img.save(OUT / "thumb.jpg", quality=90)
    print(f"thumb.jpg written ({len(lines)} lines at {size}px)")


if __name__ == "__main__":
    main(sys.argv[1])
