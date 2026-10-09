"""Paint this story's own picture from its image_brief: assets/images/stories/<story-title>.jpg.

Uses the free Pollinations image service (no account, no key, $0). The picture is saved in the repo so a rebuild
reuses it and the channel builds up a picture library. If the service is down or slow, the build simply falls
back to the place picture, so a story never fails because of the picture.
Usage: python scripts/make_image.py queue/2026-10-08.json
"""
import io
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import ASSETS, load_episode, slugify  # noqa: E402

STYLE = ("soft gouache painting, storybook illustration, cozy and calm, night, deep navy and dark teal shadows, "
         "one warm amber light source, gentle glow, painterly texture, low light, wide 16:9 scene, "
         "no text, no letters, no logos, no faces, people only small or seen from behind, no religious symbols")


def prompt(ep):
    brief = ep.get("image_brief") or f"{ep.get('place', 'a seaside town')} at night"
    return f"{brief}. {ep.get('season', '')} in a small invented seaside town. {STYLE}"


def main(ep_path):
    from PIL import Image
    ep = load_episode(ep_path)
    out = ASSETS / "images" / "stories" / (slugify(ep.get("story_title", "story")) + ".jpg")
    if out.exists():
        print(f"story picture already exists: {out}")
        return 0
    seed = sum(map(ord, ep.get("story_title", ""))) % 100000
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt(ep))
           + f"?width=1920&height=1080&seed={seed}&nologo=true&model=flux")
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "fernwick-nights-build"})
            data = urllib.request.urlopen(req, timeout=240).read()
            img = Image.open(io.BytesIO(data)).convert("RGB")
            if img.width < 800:
                raise ValueError(f"picture too small: {img.size}")
            out.parent.mkdir(parents=True, exist_ok=True)
            img.resize((1920, 1080)).save(out, quality=84)
            print(f"story picture painted: {out}")
            return 0
        except Exception as e:  # the service is free and sometimes busy
            print(f"picture attempt {attempt + 1} failed: {type(e).__name__}: {e}")
            time.sleep(20)
    print("no story picture; using the place picture instead")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
