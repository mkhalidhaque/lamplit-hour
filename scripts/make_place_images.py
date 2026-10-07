"""Draw simple, dark, warm illustrations for each place in Fernwick into assets/images/.

Run on any computer: python scripts/make_place_images.py   (needs: pip install pillow)
Files are named after the place so the build picks the right one (Marrow & Crumb -> marrow-crumb.jpg).
Replace any of them with your own art using the same file name.
"""
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

W, H = 1920, 1080
OUT = Path("assets/images")
AMBER = (255, 176, 84)


def sky(top, bottom):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def glow(img, cx, cy, r, color=AMBER, strength=0.9):
    mask = Image.radial_gradient("L").resize((2 * r, 2 * r))
    mask = ImageChops.invert(mask).point(lambda v: int(max(0, v - 76) * strength * 255 / 179))  # fades to 0 before the square's edge
    layer = Image.new("RGB", (2 * r, 2 * r), color)
    img.paste(layer, (cx - r, cy - r), mask)


def finish(img, name, seed):
    rnd = random.Random(seed)
    img = img.filter(ImageFilter.GaussianBlur(2.2))
    px = ImageDraw.Draw(img)
    for _ in range(9000):  # fine grain, like paper
        x, y = rnd.randrange(W), rnd.randrange(H)
        v = rnd.randrange(-14, 14)
        c = img.getpixel((x, y))
        px.point((x, y), fill=tuple(max(0, min(255, k + v)) for k in c))
    img = ImageEnhance.Brightness(img).enhance(0.62)  # keep it low-light for sleep
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / f"{name}.jpg", quality=86)


def window_scene(name, seed, wall=(14, 20, 30), frame=(26, 22, 20), rain=True):
    img = sky(wall, (8, 12, 20))
    glow(img, 960, 470, 900, strength=0.45)
    d = ImageDraw.Draw(img)
    d.rectangle([420, 120, 1500, 800], fill=frame)
    d.rectangle([450, 150, 1470, 770], fill=(236, 160, 78))
    glow(img, 960, 460, 520, color=(255, 214, 140), strength=0.8)
    d = ImageDraw.Draw(img)
    for x in (960,):
        d.rectangle([x - 8, 150, x + 8, 770], fill=frame)
    d.rectangle([450, 452, 1470, 468], fill=frame)
    d.polygon([(600, 770), (780, 600), (900, 770)], fill=(120, 70, 36))      # bowl and loaf shapes
    d.ellipse([1040, 640, 1240, 780], fill=(110, 64, 34))
    d.rectangle([0, 800, W, H], fill=(10, 14, 22))
    rnd = random.Random(seed)
    if rain:
        for _ in range(260):
            x, y = rnd.randrange(450, 1470), rnd.randrange(150, 760)
            d.line([(x, y), (x + 2, y + rnd.randrange(30, 90))], fill=(255, 224, 170), width=2)
    for i in range(12):  # wet cobbles reflecting light
        y = 830 + i * 20
        d.line([(700 + i * 8, y), (1220 - i * 8, y)], fill=(90, 56, 34), width=3)
    finish(img, name, seed)


def lighthouse(name, seed):
    img = sky((10, 16, 30), (22, 40, 52))
    glow(img, 1250, 330, 520, strength=0.6)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 760, W, H], fill=(10, 22, 32))
    d.polygon([(1150, 760), (1190, 330), (1310, 330), (1350, 760)], fill=(40, 46, 56))
    d.rectangle([1170, 270, 1330, 330], fill=(255, 205, 120))
    d.polygon([(1150, 270), (1250, 190), (1350, 270)], fill=(24, 28, 36))
    d.polygon([(0, 800), (700, 760), (1500, 770), (W, 800), (W, H), (0, H)], fill=(8, 14, 20))
    for i in range(10):
        d.line([(300 + i * 90, 850 + i * 14), (400 + i * 90, 850 + i * 14)], fill=(70, 100, 110), width=3)
    finish(img, name, seed)


def lane(name, seed):
    img = sky((12, 16, 28), (10, 14, 22))
    d = ImageDraw.Draw(img)
    for i in range(7):
        x = 160 + i * 250
        h = 380 + (i % 3) * 70
        d.rectangle([x, 760 - h, x + 210, 760], fill=(22, 24, 32))
        d.rectangle([x + 40, 760 - h + 90, x + 110, 760 - h + 190], fill=(240, 160, 80))
        glow(img, x + 75, 760 - h + 140, 130, strength=0.7)
        d = ImageDraw.Draw(img)
    d.rectangle([0, 760, W, H], fill=(10, 14, 22))
    for i in range(14):
        d.line([(200 + i * 100, 800 + i * 12), (260 + i * 100, 800 + i * 12)], fill=(90, 56, 34), width=3)
    finish(img, name, seed)


def halt(name, seed):
    img = sky((8, 14, 26), (18, 28, 40))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 780, W, H], fill=(14, 16, 22))
    for x in (500, 960, 1420):
        d.line([(x, 780), (x, 440)], fill=(30, 30, 36), width=8)
        glow(img, x, 440, 220, strength=0.75)
        d = ImageDraw.Draw(img)
    d.line([(0, 930), (W, 930)], fill=(60, 66, 76), width=6)
    d.line([(0, 990), (W, 990)], fill=(60, 66, 76), width=6)
    d.rectangle([700, 560, 1220, 780], fill=(24, 22, 24))
    d.rectangle([760, 610, 840, 700], fill=(240, 160, 80))
    finish(img, name, seed)


def ferry(name, seed):
    img = sky((10, 16, 30), (22, 40, 52))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 700, W, H], fill=(10, 22, 34))
    d.polygon([(640, 700), (1280, 700), (1200, 780), (720, 780)], fill=(26, 26, 32))
    d.rectangle([800, 620, 1100, 700], fill=(34, 34, 40))
    for x in (840, 920, 1000):
        d.ellipse([x, 640, x + 44, 684], fill=(240, 164, 80))
        glow(img, x + 22, 662, 90, strength=0.7)
        d = ImageDraw.Draw(img)
    for i in range(12):
        d.line([(500 + i * 40, 810 + i * 14), (640 + i * 40, 810 + i * 14)], fill=(70, 100, 110), width=3)
    finish(img, name, seed)


def woods(name, seed):
    img = sky((8, 14, 26), (18, 30, 36))
    glow(img, 1500, 260, 380, color=(255, 230, 170), strength=0.35)
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for layer, col in ((0, (18, 30, 34)), (1, (10, 20, 24)), (2, (6, 12, 16))):
        for i in range(14):
            x = rnd.randrange(-50, W + 50)
            h = rnd.randrange(380, 700) + layer * 60
            base = 820 + layer * 40
            d.polygon([(x - 90, base), (x, base - h), (x + 90, base)], fill=col)
    d.rectangle([0, 960, W, H], fill=(6, 10, 14))
    glow(img, 520, 880, 200, strength=0.55)
    finish(img, name, seed)


def marsh(name, seed):
    img = sky((10, 16, 30), (24, 40, 48))
    glow(img, 1400, 300, 460, color=(255, 230, 170), strength=0.4)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 700, W, H], fill=(12, 26, 34))
    rnd = random.Random(seed)
    for _ in range(160):
        x = rnd.randrange(W)
        h = rnd.randrange(160, 420)
        d.line([(x, 760), (x + rnd.randrange(-30, 30), 760 - h)], fill=(20, 30, 28), width=4)
    d.rectangle([0, 740, W, 770], fill=(40, 34, 26))
    for i in range(10):
        d.line([(1100 + i * 20, 800 + i * 18), (1300 - i * 6, 800 + i * 18)], fill=(120, 110, 90), width=3)
    finish(img, name, seed)


def pond(name, seed):
    img = sky((10, 16, 30), (20, 34, 44))
    glow(img, 600, 360, 420, color=(255, 230, 170), strength=0.35)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 700, W, H], fill=(10, 24, 32))
    d.rectangle([1100, 420, 1500, 700], fill=(22, 24, 30))
    d.polygon([(1060, 420), (1300, 300), (1540, 420)], fill=(16, 18, 24))
    d.rectangle([1240, 520, 1320, 610], fill=(240, 160, 80))
    glow(img, 1280, 565, 120, strength=0.7)
    d = ImageDraw.Draw(img)
    d.rectangle([1280, 760, 1320, 900], fill=(40, 44, 52))
    for i in range(8):
        d.line([(300 + i * 60, 790 + i * 20), (700 + i * 40, 790 + i * 20)], fill=(70, 100, 110), width=3)
    finish(img, name, seed)


def main():
    window_scene("marrow-crumb", 1)
    window_scene("pennywhistle-books", 2, wall=(12, 18, 28), frame=(30, 24, 18))
    window_scene("the-green-kettle", 3, wall=(16, 18, 26), frame=(28, 22, 22), rain=False)
    lighthouse("the-salt-lamp", 4)
    lane("harbor-lane", 5)
    halt("fernwick-halt", 6)
    ferry("the-wren-island-ferry", 7)
    woods("larkspur-woods", 8)
    marsh("the-salt-marsh-path", 9)
    pond("old-mill-pond", 10)
    print("wrote", len(list(OUT.glob("*.jpg"))), "images to", OUT)


if __name__ == "__main__":
    main()
