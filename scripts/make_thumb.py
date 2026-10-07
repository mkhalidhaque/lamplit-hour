"""Dark, warm 1280x720 thumbnail with 2-4 words, lower left. Output: out/thumb.jpg"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, load_episode, pick_image  # noqa: E402

FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]


def main(ep_path):
    from PIL import Image, ImageDraw, ImageEnhance, ImageFont
    ep = load_episode(ep_path)
    img = Image.open(pick_image(ep)).convert("RGB")
    w, h = img.size
    tw, th = (w, int(w * 9 / 16)) if w / h < 16 / 9 else (int(h * 16 / 9), h)
    img = img.crop(((w - tw) // 2, (h - th) // 2, (w - tw) // 2 + tw, (h - th) // 2 + th)).resize((1280, 720))
    img = ImageEnhance.Brightness(img).enhance(0.62)
    shade = Image.new("RGB", img.size, (30, 18, 8))
    img = Image.blend(img, shade, 0.12)
    d = ImageDraw.Draw(img)
    font = None
    for f in FONTS:
        if Path(f).exists():
            font = ImageFont.truetype(f, 92)
            break
    font = font or ImageFont.load_default()
    words = ep.get("thumbnail_text", ep["story_title"]).split()
    lines = [" ".join(words[:2]), " ".join(words[2:])] if len(words) > 2 else [" ".join(words)]
    y = 720 - 70 - 110 * len([ln for ln in lines if ln])
    for line in filter(None, lines):
        d.text((62, y + 3), line, font=font, fill=(0, 0, 0))
        d.text((60, y), line, font=font, fill=(244, 232, 205))
        y += 110
    OUT.mkdir(exist_ok=True)
    img.save(OUT / "thumb.jpg", quality=88)
    print("thumb.jpg written")


if __name__ == "__main__":
    main(sys.argv[1])
