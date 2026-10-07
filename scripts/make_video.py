"""Picture + episode.mp3 -> out/episode.mp4 (1920x1080).

The picture gets a gently flickering light (candle, lantern, fire or window glow) that is rendered once as a
seamless 12-second loop and then repeated for the whole episode, so the file stays small.

The episode JSON may contain "light": {"type": "candle|lantern|fire|window|lamp", "x": 0.52, "y": 0.60}
(x and y are fractions of the picture). If it is missing, the brightest part of the picture glows.

Usage: python scripts/make_video.py queue/2026-10-08.json
"""
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, branded_frame, duration, load_episode, run  # noqa: E402

W, H, FPS, LOOP_SECONDS = 1920, 1080, 12, 12
FLAMES = {"candle", "lantern", "fire", "stove"}


def find_light(base, ep):
    import numpy as np
    spec = ep.get("light") or {}
    if "x" in spec and "y" in spec:
        return float(spec["x"]) * W, float(spec["y"]) * H, spec.get("type", "window")
    lum = base.mean(axis=2)
    lum[: H // 8] = 0  # ignore the very top edge
    lum[-H // 6:, -700:] = 0  # ignore the logo corner
    cut = np.quantile(lum, 0.985)
    ys, xs = np.nonzero(lum >= cut)
    return float(xs.mean()), float(ys.mean()), spec.get("type", "window")


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
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "30", "-g", str(FPS * 2),
           "-pix_fmt", "yuv420p", str(loop_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(FPS * LOOP_SECONDS):
        t = i / FPS
        f = flicker(t)
        frame = base * (1 + (f - 1) * 1.6 * glow * warm) + glow * warm * (f - 1) * 40
        frame = np.clip(frame, 0, 255).astype("uint8")
        if kind in FLAMES:
            img = draw_flame(frame, lx, ly, kind, t)
        else:
            img = Image.fromarray(frame)
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
