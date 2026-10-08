"""Shared helpers for Fernwick Nights pipeline."""
import json
import re
import subprocess
from pathlib import Path

OUT = Path("out")
ASSETS = Path("assets")
PAUSE_SECONDS = {"[pause]": 2.0, "[long pause]": 4.0}
SECOND_MARKER = "[[SECOND]]"
CHAPTER_RE = r"\[\[CHAPTER [^\]]+\]\]"  # [[CHAPTER Name]] on its own line starts a YouTube chapter
LEAD = 5.0  # seconds of ambience before the voice starts (make_audio.py), also shifts chapter times
DEFAULT_VOICE = "en-GB-SoniaNeural"
# Free edge-tts voices allowed for narrators: pick the one that fits the teller (warmest first).
VOICES = {
    "en-US-AvaNeural": "warm, soft female (US)",
    "en-US-AndrewNeural": "warm, low male (US)",
    "en-GB-SoniaNeural": "calm, dry female (British)",
    "en-GB-RyanNeural": "gentle, steady male (British)",
    "en-US-EmmaNeural": "bright, kind female (US)",
    "en-US-BrianNeural": "relaxed, friendly male (US)",
    "en-IE-EmilyNeural": "soft female (Irish)",
    "en-IE-ConnorNeural": "soft male (Irish)",
}


def load_episode(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run(cmd):
    """Run a command, show the tail of stderr if it fails."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed:\n{r.stderr[-1500:]}")
    return r


def duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)])
    return float(r.stdout.strip())


def parse_script(script):
    """Return a list of (kind, value, second) items: ('say', text), ('pause', seconds) or ('chapter', name).

    Text before the [[SECOND]] marker is the first telling, text after it the slower second telling.
    """
    items, second = [], False
    for block in re.split(r"(\[\[SECOND\]\]|" + CHAPTER_RE + r"|\[long pause\]|\[pause\])", script):
        b = block.strip()
        if not b:
            continue
        if b == SECOND_MARKER:
            second = True
        elif re.fullmatch(CHAPTER_RE, b):
            items.append(("chapter", b[10:-2].strip(), second))
        elif b in PAUSE_SECONDS:
            items.append(("pause", PAUSE_SECONDS[b], second))
        else:
            for para in re.split(r"\n\s*\n", b):
                para = " ".join(para.split())
                if para:
                    items.append(("say", para, second))
    return items


def plain_text(script):
    return re.sub(r"\[\[SECOND\]\]|" + CHAPTER_RE + r"|\[long pause\]|\[pause\]", " ", script)


def pick_image(ep):
    """Use assets/images/<place>.* if present, else any image, else make a dark gradient."""
    from PIL import Image
    exts = (".jpg", ".jpeg", ".png")
    slug = re.sub(r"[^a-z0-9]+", "-", ep.get("place", "").lower()).strip("-")
    cands = [p for p in sorted((ASSETS / "images").glob("*")) if p.suffix.lower() in exts]
    for p in cands:
        if slug and p.stem.lower() == slug:
            return p
    if cands:
        # deterministic pick so reruns match
        return cands[sum(map(ord, ep.get("story_title", ""))) % len(cands)]
    OUT.mkdir(exist_ok=True)
    img = Image.new("RGB", (1920, 1080))
    px = img.load()
    for y in range(1080):
        for x in range(1920):
            d = ((x - 600) ** 2 + (y - 650) ** 2) ** 0.5 / 1400
            k = max(0.0, 1 - d)
            px[x, y] = (int(14 + 70 * k), int(18 + 45 * k), int(30 + 15 * k))
    p = OUT / "fallback.png"
    img.save(p)
    return p


def _seed(ep):
    import hashlib
    return int(hashlib.sha1(ep.get("story_title", "").encode()).hexdigest(), 16)


def story_view(ep, w=1920, h=1080):
    """How this story frames its place picture: mirror, zoom and crop, chosen from the title.

    Returns (flip, zoom, left, top) in a w x h picture. The crop keeps the story's light in view.
    """
    sd = _seed(ep)
    flip = sd % 2 == 1
    zoom = 1.0 + (sd // 2 % 13) / 100  # 1.00 to 1.12
    light = ep.get("light") or {}
    lx = float(light.get("x", 0.5)) * w
    ly = float(light.get("y", 0.5)) * h
    if flip:
        lx = w - lx
    cw, ch = w / zoom, h / zoom
    u, v = 0.35 + (sd // 26 % 31) / 100, 0.4 + (sd // 806 % 21) / 100
    left = min(max(lx - cw * u, 0), w - cw)
    top = min(max(ly - ch * v, 0), h - ch)
    return flip, zoom, left, top


def map_point(ep, x, y, w=1920, h=1080):
    """Where a point of the original place picture lands in this story's framing."""
    flip, zoom, left, top = story_view(ep, w, h)
    if flip:
        x = w - x
    return (x - left) * zoom, (y - top) * zoom


GRADES = {  # (tint color, strength) by season, so each story's picture has its own light
    "autumn": ((120, 70, 25), 0.10), "winter": ((40, 60, 95), 0.12),
    "spring": ((70, 90, 60), 0.08), "summer": ((95, 55, 85), 0.08),
}
SEASON_WORDS = {"autumn": ["autumn", "september", "october", "november", "harvest"],
                "winter": ["winter", "december", "january", "february", "snow", "frost"],
                "spring": ["spring", "march", "april", "may", "blossom"],
                "summer": ["summer", "june", "july", "august", "midsummer"]}


def story_image(ep):
    """The place picture, framed and graded for this story (1920x1080), with rain or mist when the story has it."""
    import random
    from PIL import Image, ImageDraw, ImageFilter
    src = pick_image(ep)
    img = Image.open(src).convert("RGB").resize((1920, 1080))
    if src.stem != "fallback":
        flip, zoom, left, top = story_view(ep)
        if flip:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        img = img.crop((int(left), int(top), int(left + 1920 / zoom), int(top + 1080 / zoom))).resize((1920, 1080))
    text = " ".join(str(ep.get(k, "")) for k in ("season", "image_brief", "ambience")).lower()
    for season, ws in SEASON_WORDS.items():
        if any(w in text for w in ws):
            color, k = GRADES[season]
            img = Image.blend(img, Image.new("RGB", img.size, color), k)
            break
    rnd = random.Random(_seed(ep))
    if "rain" in text:
        layer = Image.new("L", img.size, 0)
        d = ImageDraw.Draw(layer)
        for _ in range(900):
            x, y = rnd.randrange(1920), rnd.randrange(1080)
            d.line([x, y, x - 6, y + 34], fill=rnd.randrange(25, 60), width=1)
        # streaks show mostly over the lit parts (window glass, lamplight), like rain seen against light
        from PIL import ImageChops
        lit = img.convert("L").point(lambda v: min(255, max(0, (v - 40) * 3)))
        layer = ImageChops.multiply(layer.filter(ImageFilter.GaussianBlur(0.8)), lit).point(lambda v: min(255, v * 3))
        img.paste(Image.new("RGB", img.size, (200, 205, 215)), (0, 0), layer)
    if "mist" in text or "fog" in text:
        mist = Image.new("L", img.size, 0)
        d = ImageDraw.Draw(mist)
        for _ in range(14):
            x, y = rnd.randrange(-200, 1920), rnd.randrange(500, 1080)
            d.ellipse([x, y, x + rnd.randrange(400, 900), y + rnd.randrange(80, 200)], fill=rnd.randrange(20, 45))
        img.paste(Image.new("RGB", img.size, (150, 160, 170)), (0, 0), mist.filter(ImageFilter.GaussianBlur(60)))
    return img


def brand_mark(size):
    """The Fernwick Nights logo (assets/brand/logo.png) resized, or None if missing."""
    from PIL import Image
    f = ASSETS / "brand" / "logo.png"
    return Image.open(f).convert("RGB").resize((size, size)) if f.exists() else None


def stamp_brand(img, mark_px, margin, name_px=0):
    """Put a small, dim logo (and optionally the channel name) bottom-right of a PIL image."""
    from PIL import Image, ImageDraw, ImageFont
    m = brand_mark(mark_px)
    if m is None:
        return img
    img = img.copy()
    mask = Image.new("L", (mark_px, mark_px), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, mark_px, mark_px], fill=215)
    x, y = img.width - mark_px - margin, img.height - mark_px - margin
    img.paste(m, (x, y), mask)
    if name_px:
        fp = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
        if Path(fp).exists():
            f = ImageFont.truetype(fp, name_px)
            d = ImageDraw.Draw(img)
            t = "Fernwick Nights"
            w = d.textlength(t, font=f)
            d.text((x - w - margin // 2, y + mark_px // 2 - name_px // 2), t, font=f, fill=(244, 214, 160))
    return img


def branded_frame(ep):
    """Episode picture with the channel logo and name added; saved to out/frame.jpg."""
    img = story_image(ep)
    img = stamp_brand(img, 110, 40, name_px=34)
    OUT.mkdir(exist_ok=True)
    p = OUT / "frame.jpg"
    img.save(p, quality=92)
    return p
