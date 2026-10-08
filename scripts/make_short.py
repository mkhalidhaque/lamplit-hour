"""Make a ~35-45 s vertical Short from the episode's short_excerpt. Output: out/short.mp4"""
import asyncio
import os
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, duration, load_episode, run, stamp_brand, story_image  # noqa: E402
from make_voice import pick_voice, speak  # noqa: E402


def card(ep, text):
    from PIL import Image, ImageDraw, ImageEnhance, ImageFont
    img = story_image(ep)
    w, h = img.size
    tw = int(h * 9 / 16)
    left = max(0, (w - tw) // 2)
    img = img.crop((left, 0, left + min(tw, w), h)).resize((1080, 1920))
    img = ImageEnhance.Brightness(img).enhance(0.45)
    d = ImageDraw.Draw(img)
    fp = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    font = ImageFont.truetype(fp, 52) if Path(fp).exists() else ImageFont.load_default()
    lines = textwrap.wrap(text, 30)[:14]
    y = 1920 // 2 - len(lines) * 36
    for ln in lines:
        d.text((90, y), ln, font=font, fill=(244, 232, 205))
        y += 72
    img = stamp_brand(img, 150, 60)
    p = OUT / "short.png"
    img.save(p)
    return p


async def main(ep_path):
    ep = load_episode(ep_path)
    text = ep["short_excerpt"].strip()
    await speak(text, "-18%", OUT / "short_voice.mp3", voice=pick_voice(ep))
    png = card(ep, text)
    secs = duration(OUT / "short_voice.mp3") + 3
    bed = f"anoisesrc=color=pink:amplitude=0.5,highpass=f=400,lowpass=f=5000,volume=-24dB"
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", "2", "-i", str(png), "-i", str(OUT / "short_voice.mp3"),
         "-f", "lavfi", "-i", bed,
         "-filter_complex", "[1:a]adelay=1000:all=1,apad[v];[v][2:a]amix=inputs=2:duration=first:normalize=0,afade=t=out:st="
         f"{secs - 2:.1f}:d=2[a]",
         "-map", "0:v", "-map", "[a]", "-t", f"{secs:.1f}", "-c:v", "libx264", "-tune", "stillimage",
         "-pix_fmt", "yuv420p", "-r", "2", "-c:a", "aac", "-b:a", "128k", str(OUT / "short.mp4")])
    print(f"short.mp4 {secs:.0f}s")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
