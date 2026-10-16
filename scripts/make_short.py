"""Make a 30-second vertical teaser Short from tonight's cold open (the hook). Output: out/short.mp4

The Short speaks the episode's cold_open (the first paragraph of the script; older episodes fall back to
short_excerpt), then one line sending people to the full story. The card shows the bold thumbnail words at
the top and the spoken words below. It is kept under MAX_SECONDS (sped up a little if it runs long).
"""
import asyncio
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, duration, load_episode, plain_text, run, stamp_brand, story_image  # noqa: E402
from make_voice import pick_voice, speak  # noqa: E402

MAX_SECONDS = 30.0
CTA = "The whole story is on Fernwick Nights tonight."
RATE = "-12%"  # brisker than the episode: a Short has to catch people scrolling
FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
BODY = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"


def teaser_text(ep):
    """The cold open: the cold_open field, else the script's first paragraph if it is not the welcome."""
    if ep.get("cold_open"):
        return " ".join(ep["cold_open"].split())
    paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", plain_text(ep.get("script", ""))) if p.strip()]
    if paras and not paras[0].lower().startswith("welcome to fernwick nights"):
        return paras[0]
    return " ".join(ep["short_excerpt"].split())


def font(paths, size):
    from PIL import ImageFont
    for f in paths:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def card(ep, text):
    from PIL import ImageDraw, ImageEnhance
    img = story_image(ep)
    w, h = img.size
    tw = int(h * 9 / 16)
    left = max(0, (w - tw) // 2)
    img = img.crop((left, 0, left + min(tw, w), h)).resize((1080, 1920))
    img = ImageEnhance.Brightness(img).enhance(0.5)
    d = ImageDraw.Draw(img)
    # bold hook words at the top, like the thumbnail
    head = (ep.get("thumbnail_text") or ep.get("story_title", "")).strip()
    hf = font(FONTS, 104)
    y = 230
    for ln in textwrap.wrap(head, 16)[:3]:
        x = (1080 - d.textlength(ln, font=hf)) / 2
        d.text((x, y), ln, font=hf, fill=(255, 244, 222), stroke_width=7, stroke_fill=(12, 8, 4))
        y += 118
    figure = (ep.get("myth_figure") or "").upper()
    if figure and figure.lower() not in head.lower():
        lf = font(FONTS, 44)
        d.text(((1080 - d.textlength(figure, font=lf)) / 2, y + 10), figure, font=lf, fill=(247, 190, 92),
               stroke_width=4, stroke_fill=(12, 8, 4))
        y += 70
    bf = font([BODY], 50)
    lines = textwrap.wrap(text, 32)[:12]
    y = max(y + 90, 1920 // 2 - len(lines) * 35)
    for ln in lines:
        d.text((90, y), ln, font=bf, fill=(244, 232, 205), stroke_width=2, stroke_fill=(12, 8, 4))
        y += 70
    cf = font(FONTS, 46)
    c = "Full story: Fernwick Nights"
    d.text(((1080 - d.textlength(c, font=cf)) / 2, 1600), c, font=cf, fill=(247, 190, 92), stroke_width=3,
           stroke_fill=(12, 8, 4))
    img = stamp_brand(img, 150, 60)
    p = OUT / "short.png"
    img.save(p)
    return p


async def main(ep_path):
    ep = load_episode(ep_path)
    OUT.mkdir(exist_ok=True)
    text = teaser_text(ep)
    await speak(f"{text} {CTA}", RATE, OUT / "short_voice.mp3", voice=pick_voice(ep))
    png = card(ep, text)
    spoken = duration(OUT / "short_voice.mp3")
    tempo = min(1.25, max(1.0, spoken / (MAX_SECONDS - 2.5)))  # 1 s lead in + 1.5 s fade out
    secs = min(MAX_SECONDS, spoken / tempo + 2.5)
    bed = "anoisesrc=color=pink:amplitude=0.5,highpass=f=400,lowpass=f=5000,volume=-24dB"
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", "2", "-i", str(png), "-i", str(OUT / "short_voice.mp3"),
         "-f", "lavfi", "-i", bed,
         "-filter_complex", f"[1:a]atempo={tempo:.3f},adelay=1000:all=1,apad[v];"
         f"[v][2:a]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={secs - 1.5:.1f}:d=1.5[a]",
         "-map", "0:v", "-map", "[a]", "-t", f"{secs:.1f}", "-c:v", "libx264", "-tune", "stillimage",
         "-pix_fmt", "yuv420p", "-r", "2", "-c:a", "aac", "-b:a", "128k", str(OUT / "short.mp4")])
    print(f"short.mp4 {secs:.0f}s (tempo x{tempo:.2f})")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
