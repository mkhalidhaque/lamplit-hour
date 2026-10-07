"""Shared helpers for The Dreaming Storyteller pipeline."""
import json
import re
import subprocess
from pathlib import Path

OUT = Path("out")
ASSETS = Path("assets")
PAUSE_SECONDS = {"[pause]": 2.0, "[long pause]": 4.0}
SECOND_MARKER = "[[SECOND]]"


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
    """Return a list of (kind, value) items: ('say', text, second?) or ('pause', seconds).

    Text before the [[SECOND]] marker is the first telling, text after it the slower second telling.
    """
    items, second = [], False
    for block in re.split(r"(\[\[SECOND\]\]|\[long pause\]|\[pause\])", script):
        b = block.strip()
        if not b:
            continue
        if b == SECOND_MARKER:
            second = True
        elif b in PAUSE_SECONDS:
            items.append(("pause", PAUSE_SECONDS[b], second))
        else:
            for para in re.split(r"\n\s*\n", b):
                para = " ".join(para.split())
                if para:
                    items.append(("say", para, second))
    return items


def plain_text(script):
    return re.sub(r"\[\[SECOND\]\]|\[long pause\]|\[pause\]", " ", script)


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
