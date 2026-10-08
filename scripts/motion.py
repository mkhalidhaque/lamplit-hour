"""Gentle looping motion layered over the episode picture, so the video feels like a moving painting.

Every effect is a function of t / LOOP_SECONDS with whole numbers of cycles, so the short loop repeats
without a visible seam. Effects (episode JSON "motion": a list; if missing they are picked from the story):
  embers  sparks drifting up from a fire, stove, candle or lantern
  smoke   soft chimney or stove smoke curling upward
  rain    rain streaks running down over the lit parts (window glass, lamplight)
  snow    slow snowflakes drifting down
  dust    motes floating in the warm light
  zoom    a very slow push in and back out
The flickering light itself is always on (make_video.py).
"""
import math
import random

EFFECTS = ["embers", "smoke", "rain", "snow", "dust", "zoom"]
FLAMES = {"candle", "lantern", "fire", "stove"}


def pick(ep, kind):
    """Which effects to use: the episode's own "motion" list, or chosen from the light, ambience and season."""
    if isinstance(ep.get("motion"), list):
        return [m for m in ep["motion"] if m in EFFECTS]
    text = " ".join(str(ep.get(k, "")) for k in ("season", "image_brief", "ambience", "description_setting")).lower()
    out = ["zoom"]
    if kind in FLAMES:
        out += ["embers", "smoke"]
    if "rain" in text:
        out.append("rain")
    elif "snow" in text:
        out.append("snow")
    if not ({"embers", "rain", "snow"} & set(out)):
        out.append("dust")
    return out


class Motion:
    def __init__(self, ep, kind, lx, ly, w, h, loop_seconds):
        self.effects = pick(ep, kind)
        self.lx, self.ly, self.w, self.h, self.T = lx, ly, w, h, loop_seconds
        rnd = random.Random(ep.get("story_title", ""))
        # each particle: (phase, x offset, sway, size, cycles per loop)
        self.embers = [(rnd.random(), rnd.uniform(-40, 40), rnd.uniform(10, 40), rnd.uniform(1.5, 3.5),
                        rnd.choice([2, 3, 4])) for _ in range(28)]
        self.smoke = [(rnd.random(), rnd.uniform(-20, 20), rnd.uniform(30, 70), rnd.uniform(40, 80), 1)
                      for _ in range(9)]
        self.rain = [(rnd.random(), rnd.uniform(0, w), rnd.uniform(18, 34), rnd.choice([3, 4, 5]))
                     for _ in range(420)]
        self.snow = [(rnd.random(), rnd.uniform(0, w), rnd.uniform(20, 60), rnd.uniform(1.5, 4), rnd.choice([1, 2]))
                     for _ in range(220)]
        self.dust = [(rnd.random(), rnd.uniform(-300, 300), rnd.uniform(-220, 220), rnd.uniform(1.8, 3.4))
                     for _ in range(60)]
        self.lit = None

    def zoom(self, img, t):
        """Push in up to 2.5% and back out once per loop."""
        from PIL import Image
        if "zoom" not in self.effects:
            return img
        z = 1 + 0.0125 * (1 - math.cos(2 * math.pi * t / self.T))
        cw, ch = self.w / z, self.h / z
        cx = min(max(self.lx, cw / 2), self.w - cw / 2)
        cy = min(max(self.ly, ch / 2), self.h - ch / 2)
        return img.transform((self.w, self.h), Image.EXTENT, (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2),
                             Image.BILINEAR)

    def overlay(self, img, t):
        from PIL import Image, ImageChops, ImageDraw, ImageFilter
        u = t / self.T
        if self.lit is None and "rain" in self.effects:
            self.lit = img.convert("L").point(lambda v: min(255, max(0, (v - 40) * 3)))
        if "smoke" in self.effects:
            # drawn small and blurred, then scaled up: soft and cheap
            s = 4
            layer = Image.new("L", (self.w // s, self.h // s), 0)
            d = ImageDraw.Draw(layer)
            for ph, dx, sway, r, _ in self.smoke:
                p = (u + ph) % 1
                x = (self.lx + dx + sway * math.sin(2 * math.pi * (p * 1.5 + ph))) / s
                y = (self.ly - 60 - p * 420) / s
                rr = (r * (0.6 + p)) / s
                a = int(60 * math.sin(math.pi * p))
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=a)
            layer = layer.filter(ImageFilter.GaussianBlur(6)).resize((self.w, self.h), Image.BILINEAR)
            img.paste(Image.new("RGB", img.size, (175, 165, 155)), (0, 0), layer)
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(glow)
        if "embers" in self.effects:
            for ph, dx, sway, r, cyc in self.embers:
                p = (u * cyc + ph) % 1
                x = self.lx + dx + sway * math.sin(2 * math.pi * (p * 2 + ph))
                y = self.ly - 10 - p * 260
                a = int(230 * (1 - p) * min(1, p * 6))
                d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 170 + int(60 * (1 - p)), 70, a))
        if "dust" in self.effects:
            for ph, dx, dy, r in self.dust:
                ang = 2 * math.pi * (u + ph)
                x = self.lx + dx + 25 * math.sin(ang)
                y = self.ly + dy - 18 * math.sin(2 * ang + ph)
                a = int(150 + 60 * math.sin(ang * 3))
                d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 230, 190, a))
        if "snow" in self.effects:
            for ph, x0, sway, r, cyc in self.snow:
                p = (u * cyc + ph) % 1
                x = x0 + sway * math.sin(2 * math.pi * (p * 2 + ph))
                y = -10 + p * (self.h + 20)
                d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 240, 250, 150))
        img.paste(glow.filter(ImageFilter.GaussianBlur(1.2)), (0, 0), glow.filter(ImageFilter.GaussianBlur(1.2)))
        if "rain" in self.effects:
            layer = Image.new("L", img.size, 0)
            d = ImageDraw.Draw(layer)
            for ph, x, ln, cyc in self.rain:
                y = ((u * cyc + ph) % 1) * (self.h + 60) - 40
                d.line([x, y, x - 4, y + ln], fill=110, width=1)
            layer = ImageChops.multiply(layer, self.lit).point(lambda v: min(255, v * 2))
            img.paste(Image.new("RGB", img.size, (205, 210, 220)), (0, 0), layer)
        return img
