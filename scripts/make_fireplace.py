"""Draw the fallback picture: a stone fireplace with logs, used when a story's own picture can't be made.

The flames themselves are not drawn here: make_video.py animates them over the logs (FIRE_X, FIRE_Y in common.py).
Run once: python scripts/make_fireplace.py  -> assets/images/fireplace.jpg
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from common import FIRE_X, FIRE_Y  # noqa: E402

W, H = 1920, 1080


def radial(img, cx, cy, r, color, strength):
    mask = Image.radial_gradient("L").resize((2 * r, 2 * r))
    mask = ImageChops.invert(mask).point(lambda v: int(max(0, v - 70) * strength * 255 / 185))
    img.paste(Image.new("RGB", (2 * r, 2 * r), color), (cx - r, cy - r), mask)


def main():
    rnd = random.Random(7)
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):  # dark plaster wall
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(22 + 8 * t), int(18 + 4 * t), int(22 - 6 * t)))
    # stone surround
    sx0, sx1, sy0 = FIRE_X - 520, FIRE_X + 520, 300
    floor = 900
    d.rectangle([sx0, sy0, sx1, floor], fill=(48, 42, 40))
    y = sy0
    while y < floor:
        h = rnd.randint(46, 70)
        x = sx0 + rnd.randint(-30, 0)
        while x < sx1:
            w = rnd.randint(70, 140)
            c = rnd.randint(52, 78)
            x1, y1 = min(x + w, sx1) - 3, min(y + h, floor) - 3
            if x1 > x + 12 and y1 > y + 12:
                d.rounded_rectangle([x + 3, y + 3, x1, y1], radius=8, fill=(c, c - 6, c - 10))
            x += w
        y += h
    # mantel shelf with a few small things on it
    d.rectangle([sx0 - 60, sy0 - 40, sx1 + 60, sy0 + 5], fill=(58, 38, 26))
    d.rectangle([sx0 - 60, sy0 + 5, sx1 + 60, sy0 + 18], fill=(34, 22, 16))
    d.ellipse([sx0 + 80, sy0 - 150, sx0 + 190, sy0 - 40], fill=(40, 30, 22))  # a round clock
    d.ellipse([sx0 + 95, sy0 - 135, sx0 + 175, sy0 - 55], fill=(150, 128, 92))
    d.line([sx0 + 135, sy0 - 95, sx0 + 135, sy0 - 125], fill=(40, 30, 22), width=4)
    d.line([sx0 + 135, sy0 - 95, sx0 + 158, sy0 - 95], fill=(40, 30, 22), width=4)
    d.rectangle([sx1 - 230, sy0 - 120, sx1 - 170, sy0 - 40], fill=(70, 52, 40))  # a jar
    d.rectangle([sx1 - 140, sy0 - 95, sx1 - 90, sy0 - 40], fill=(60, 70, 66))  # a tin
    # firebox opening
    ox0, ox1, oy0 = FIRE_X - 330, FIRE_X + 330, 470
    d.rectangle([ox0, oy0 + 120, ox1, floor], fill=(10, 7, 6))
    d.pieslice([ox0, oy0, ox1, oy0 + 260], 180, 360, fill=(10, 7, 6))
    d.rectangle([ox0, oy0 + 128, ox1, oy0 + 140], fill=(10, 7, 6))
    # hearth floor and rug
    d.rectangle([0, floor, W, H], fill=(26, 18, 14))
    d.rectangle([sx0 - 40, floor, sx1 + 40, floor + 40], fill=(62, 54, 50))
    d.ellipse([FIRE_X - 520, floor + 70, FIRE_X + 520, floor + 260], fill=(70, 30, 26))
    d.ellipse([FIRE_X - 470, floor + 90, FIRE_X + 470, floor + 240], fill=(88, 40, 32))
    # warm light from the fire on everything
    radial(img, FIRE_X, FIRE_Y, 900, (255, 150, 60), 0.55)
    radial(img, FIRE_X, FIRE_Y + 30, 380, (255, 120, 40), 0.7)
    d = ImageDraw.Draw(img)
    # glowing ember bed and logs
    d.ellipse([FIRE_X - 250, FIRE_Y + 40, FIRE_X + 250, FIRE_Y + 110], fill=(190, 70, 20))
    d.ellipse([FIRE_X - 190, FIRE_Y + 55, FIRE_X + 190, FIRE_Y + 95], fill=(255, 150, 50))
    for (x0, y0, x1, y1) in [(-230, 50, 90, 95), (-70, 40, 240, 90), (-150, 15, 160, 60)]:
        d.rounded_rectangle([FIRE_X + x0, FIRE_Y + y0, FIRE_X + x1, FIRE_Y + y1], radius=22, fill=(48, 28, 18))
        d.ellipse([FIRE_X + x1 - 30, FIRE_Y + y0, FIRE_X + x1 + 10, FIRE_Y + y1], fill=(120, 72, 40))
    # andirons
    for x in (FIRE_X - 210, FIRE_X + 210):
        d.rectangle([x - 8, FIRE_Y + 60, x + 8, FIRE_Y + 140], fill=(20, 16, 14))
    img = img.filter(ImageFilter.GaussianBlur(2.0))
    px = ImageDraw.Draw(img)
    for _ in range(9000):  # paper grain
        x, y = rnd.randrange(W), rnd.randrange(H)
        c = img.getpixel((x, y))
        v = rnd.randrange(-12, 12)
        px.point((x, y), fill=tuple(max(0, min(255, k + v)) for k in c))
    img = ImageEnhance.Brightness(img).enhance(0.85)
    out = Path("assets/images/fireplace.jpg")
    img.save(out, quality=88)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
