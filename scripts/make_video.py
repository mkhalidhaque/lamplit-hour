"""Picture + episode.mp3 -> out/episode.mp4 (1920x1080).

The picture gets a gently flickering light (candle, lantern, fire or window glow) plus slow looping motion
(embers, smoke, rain, snow, dust motes, a slow push in; see motion.py). It is rendered once as a seamless
12-second loop and then repeated for the whole episode, so the file stays small and the render quick.

The episode JSON may contain "light": {"type": "candle|lantern|fire|window|lamp", "x": 0.52, "y": 0.60}
(x and y are fractions of the picture). If it is missing, the brightest part of the picture glows.

Usage: python scripts/make_video.py queue/2026-10-08.json
"""
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, branded_frame, duration, load_episode, map_point, run, story_picture, using_fireplace, FIRE_X, FIRE_Y  # noqa: E402
from motion import Motion  # noqa: E402

W, H, FPS, LOOP_SECONDS = 1920, 1080, 15, 12
FLAMES = {"candle", "lantern", "fire", "stove"}


def find_light(base, ep):
    import numpy as np
    spec = ep.get("light") or {}
    if using_fireplace(ep):
        return float(FIRE_X), float(FIRE_Y), "hearth"
    if "x" in spec and "y" in spec and not story_picture(ep):
        x, y = map_point(ep, float(spec["x"]) * W, float(spec["y"]) * H, W, H)
        return x, y, spec.get("type", "window")
    lum = base.mean(axis=2)
    lum[: H // 8] = 0  # ignore the very top edge
    lum[-H // 6:, -700:] = 0  # ignore the logo corner
    # the brightest patch (not scattered bright pixels): average 40x40 blocks, take the brightest block
    b = 40
    blocks = lum[: H // b * b, : W // b * b].reshape(H // b, b, W // b, b).mean(axis=(1, 3))
    by, bx = np.unravel_index(np.argmax(blocks), blocks.shape)
    return float(bx * b + b / 2), float(by * b + b / 2), spec.get("type", "window")


def flicker(t):
    """Seamless over LOOP_SECONDS: whole numbers of cycles. Returns about 0.85 to 1.15."""
    p = 2 * math.pi * t / LOOP_SECONDS
    return 1 + 0.07 * math.sin(3 * p) + 0.045 * math.sin(7 * p + 1.0) + 0.03 * math.sin(13 * p + 2.0)


def draw_flame(frame, cx, cy, kind, t):
    from PIL import Image, ImageDraw, ImageFilter
    p = 2 * math.pi * t / LOOP_SECONDS
    f = flicker(t)
    sway = 5 * math.sin(5 * p) + 3 * math.sin(11 * p + 1)
    h = (78 if kind in {"fire", "stove"} else 58) * (0.9 + 1.2 * (f - 1))
    w = h * 0.36
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    top = (cx + sway, cy - h)
    d.ellipse([cx - w, cy - w * 1.6, cx + w, cy + w * 0.9], fill=(255, 160, 50, 235))
    d.polygon([(cx - w * 0.9, cy - w * 0.5), top, (cx + w * 0.9, cy - w * 0.5)], fill=(255, 160, 50, 235))
    iw = w * 0.55
    d.ellipse([cx - iw, cy - iw * 1.5, cx + iw, cy + iw * 0.7], fill=(255, 238, 180, 255))
    d.polygon([(cx - iw * 0.8, cy - iw * 0.6), (cx + sway * 0.6, cy - h * 0.62), (cx + iw * 0.8, cy - iw * 0.6)],
              fill=(255, 238, 180, 255))
    d.line([cx, cy + w * 0.8, cx, cy + w * 1.6], fill=(40, 28, 20, 255), width=3)
    layer = layer.filter(ImageFilter.GaussianBlur(3.0))
    out = Image.fromarray(frame)
    out.paste(layer, (0, 0), layer)
    return out


def draw_hearth(frame, cx, cy, t):
    """A log fire: overlapping flame tongues of different heights, each swaying in its own seamless rhythm."""
    from PIL import Image, ImageDraw, ImageFilter
    p = 2 * math.pi * t / LOOP_SECONDS
    bw, bh = 640, 520  # work in a box around the logs only (fast)
    ox, oy = int(cx - bw / 2), int(cy + 60 - bh)
    layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    tongues = [(-170, 150, 3, 0.0), (-110, 230, 5, 1.1), (-50, 290, 4, 2.3), (10, 320, 3, 0.7), (70, 270, 6, 1.9),
               (130, 210, 4, 2.9), (185, 140, 5, 0.4), (-20, 200, 7, 3.3), (100, 170, 8, 4.1)]
    base_y = bh - 40
    for colors, scale in (((255, 110, 30, 200), 1.0), ((255, 175, 60, 220), 0.72), ((255, 235, 170, 235), 0.42)):
        for dx, h, cyc, ph in tongues:
            hh = h * scale * (0.82 + 0.18 * math.sin(cyc * p + ph) + 0.06 * math.sin(2 * cyc * p + ph * 2))
            w = (38 + h / 9) * scale
            sway = 14 * math.sin(cyc * p * 0.5 + ph) if cyc % 2 == 0 else 14 * math.sin((cyc + 1) * p * 0.5 + ph)
            x = bw / 2 + dx * (0.9 if scale < 1 else 1)
            d.polygon([(x - w, base_y), (x - w * 0.6, base_y - hh * 0.45), (x + sway, base_y - hh),
                       (x + w * 0.6, base_y - hh * 0.45), (x + w, base_y)], fill=colors)
            d.ellipse([x - w, base_y - w * 0.8, x + w, base_y + w * 0.4], fill=colors)
    layer = layer.filter(ImageFilter.GaussianBlur(9))
    out = Image.fromarray(frame)
    out.paste(layer, (ox, oy), layer)
    return out


def render_loop(ep, loop_path):
    import numpy as np
    from PIL import Image
    base_img = Image.open(branded_frame(ep)).convert("RGB").resize((W, H))
    base = np.asarray(base_img).astype("float32")
    lx, ly, kind = find_light(base, ep)
    yy, xx = np.mgrid[0:H, 0:W]
    dist2 = (xx - lx) ** 2 + (yy - ly) ** 2
    glow = np.exp(-dist2 / (2 * 330.0 ** 2))[..., None].astype("float32")
    warm = np.array([1.0, 0.82, 0.55], dtype="float32")
    motion = Motion(ep, kind, lx, ly, W, H, LOOP_SECONDS)
    print("motion:", ", ".join(motion.effects) or "light only")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "30", "-g", str(FPS * 2),
           "-pix_fmt", "yuv420p", str(loop_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(FPS * LOOP_SECONDS):
        t = i / FPS
        f = flicker(t)
        frame = base * (1 + (f - 1) * 1.6 * glow * warm) + glow * warm * (f - 1) * 40
        frame = np.clip(frame, 0, 255).astype("uint8")
        if kind == "hearth":
            img = draw_hearth(frame, lx, ly, t)
        elif kind in FLAMES and not story_picture(ep):  # painted story pictures already show their flame
            img = draw_flame(frame, lx, ly, kind, t)
        else:
            img = Image.fromarray(frame)
        img = motion.zoom(motion.overlay(img, t), t)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg loop render failed")
    return kind, lx, ly


def main(ep_path):
    ep = load_episode(ep_path)
    OUT.mkdir(exist_ok=True)
    loop = OUT / "loop.mp4"
    kind, lx, ly = render_loop(ep, loop)
    length = duration(OUT / "episode.mp3")
    run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(loop), "-i", str(OUT / "episode.mp3"),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-t", f"{length:.2f}",
         "-movflags", "+faststart", str(OUT / "episode.mp4")])
    print(f"episode.mp4 with flickering {kind} light at ({lx:.0f},{ly:.0f})")


if __name__ == "__main__":
    main(sys.argv[1])
