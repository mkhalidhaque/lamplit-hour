"""Build the story's background soundscape as a seamless 2-minute loop: out/bed.wav.

Layers are chosen per story (episode JSON "soundscape": a list) or from the ambience word.
Everything is synthesized with numpy (no downloads, $0): noise is shaped in the frequency domain, which makes
it loop perfectly, and every small event (a crackle, a tick, a wave) wraps around the loop end.
Nothing is loud or sudden: events are soft and the whole bed sits under the voice.

Layers:
  room      low, warm room tone (an indoor hum)
  crackle   a fire or coal stove: soft pops and the occasional settling coal
  clock     a quiet clock ticking once a second
  rain      steady rain
  drips     drops tapping on a window or a gutter
  wind      wind with slow gusts
  ocean     big slow waves breaking far off
  lapping   small harbor waves against stone and hulls
  stream    a brook running over stones
  crickets  far-off crickets on a warm night
  pines     wind moving through pine trees, soft and airy
Usage: python scripts/make_bed.py queue/2026-10-08.json
"""
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, load_episode  # noqa: E402

SR = 44100
SECONDS = 120
N = SR * SECONDS
LAYERS = ["room", "crackle", "clock", "rain", "drips", "wind", "ocean", "lapping", "stream", "crickets", "pines"]
DEFAULTS = {
    "stove": ["room", "crackle"],
    "rain": ["rain", "drips", "room"],
    "wind": ["wind", "room"],
    "ocean": ["ocean"],
    "harbor": ["lapping", "ocean"],
}
# relative loudness of each layer in the mix. Steady layers are scaled by their average level;
# layers made of separate events (pops, ticks, drops, chirps) by their loudest event, kept low so nothing jumps out
GAIN = {"room": 0.35, "rain": 0.8, "wind": 0.7, "ocean": 0.85, "lapping": 0.6, "stream": 0.55, "pines": 0.5,
        "crackle": 1.6, "clock": 0.35, "drips": 0.7, "crickets": 0.3}
EVENTS = {"crackle", "clock", "drips", "crickets"}


def layers_for(ep):
    want = ep.get("soundscape")
    if isinstance(want, list) and want:
        return [x for x in want if x in LAYERS]
    return DEFAULTS.get(str(ep.get("ambience", "rain")).lower().split()[0], DEFAULTS["rain"])


def shaped_noise(rng, lo, hi, slope=0.0):
    """Noise between lo and hi Hz with a 1/f**slope tilt. Periodic over the loop, so it repeats seamlessly."""
    spec = np.fft.rfft(rng.standard_normal(N))
    f = np.fft.rfftfreq(N, 1 / SR)
    gain = np.zeros_like(f)
    band = (f >= lo) & (f <= hi)
    gain[band] = 1 / np.maximum(f[band], 1) ** slope
    # soft edges instead of brick walls
    edge = 0.15
    gain *= np.clip((f - lo * (1 - edge)) / (lo * edge + 1e-9), 0, 1) if lo > 0 else 1
    gain *= np.clip((hi * (1 + edge) - f) / (hi * edge), 0, 1)
    x = np.fft.irfft(spec * gain, N)
    return x / (np.abs(x).max() + 1e-9)


def slow(cycles_list, depth, rng):
    """A slow loudness swell made of sines with whole numbers of cycles per loop (seamless)."""
    t = np.arange(N) / N
    env = np.ones(N)
    for c in cycles_list:
        env += depth / len(cycles_list) * np.sin(2 * np.pi * (c * t + rng.random()))
    return np.clip(env, 0.05, None)


def place(out, event, at):
    """Add an event at sample `at`, wrapping around the loop end."""
    idx = (np.arange(len(event)) + at) % N
    np.add.at(out, idx, event)


def smooth(x, k):
    """Circular moving average (a gentle low-pass)."""
    if k <= 1:
        return x
    xp = np.concatenate([x[-k:], x, x[:k]])
    y = np.convolve(xp, np.ones(k) / k, mode="same")
    return y[k:-k]


def layer(name, rng):
    t = np.arange(N) / SR
    if name == "room":
        return shaped_noise(rng, 30, 260, 1.0)
    if name == "rain":
        return shaped_noise(rng, 400, 9000, 0.5) * slow([2, 5], 0.15, rng)
    if name == "wind":
        return shaped_noise(rng, 60, 900, 1.0) * slow([3, 7, 11], 0.9, rng)
    if name == "pines":
        return shaped_noise(rng, 800, 6000, 0.3) * slow([4, 9], 0.8, rng)
    if name == "stream":
        return shaped_noise(rng, 300, 5000, 0.4) * slow([17, 29, 41], 0.25, rng)
    if name == "ocean":
        base = shaped_noise(rng, 60, 2500, 0.9)
        waves = np.zeros(N)
        n_waves = 12  # one every ~10 s
        for i in range(n_waves):
            at = int((i + rng.uniform(-0.2, 0.2)) * N / n_waves)
            L = int(SR * rng.uniform(6, 9))
            k = np.arange(L) / L
            place(waves, np.sin(np.pi * k) ** 2 * (1 - 0.5 * k), at)
        return base * (0.15 + waves)
    if name == "lapping":
        base = shaped_noise(rng, 200, 4000, 0.6)
        env = np.zeros(N)
        for i in range(int(SECONDS / 2.6)):
            at = int(i * 2.6 * SR + rng.uniform(-0.4, 0.4) * SR)
            L = int(SR * rng.uniform(0.6, 1.2))
            k = np.arange(L) / L
            place(env, rng.uniform(0.4, 1) * np.sin(np.pi * k) ** 3, at)
        return base * (0.1 + env)
    out = np.zeros(N)
    if name == "crackle":
        for _ in range(int(SECONDS * 2.2)):  # soft pops
            L = int(SR * rng.uniform(0.002, 0.012))
            pop = rng.standard_normal(L) * np.exp(-np.arange(L) / (L / 4)) * rng.uniform(0.15, 0.6)
            place(out, smooth(np.pad(pop, 8), rng.choice([1, 2, 3]))[: L + 16], rng.integers(N))
        for _ in range(int(SECONDS / 14)):  # a coal settling: a slower, duller shuffle
            L = int(SR * rng.uniform(0.25, 0.5))
            s = smooth(rng.standard_normal(L), 12) * np.sin(np.pi * np.arange(L) / L) * 0.8
            place(out, s, rng.integers(N))
        out += 0.25 * shaped_noise(rng, 80, 600, 1.0) * slow([5, 13], 0.5, rng)  # the low breathing of the fire
        return out
    if name == "drips":
        for _ in range(int(SECONDS * 1.5)):
            L = int(SR * 0.04)
            k = np.arange(L) / SR
            f = rng.uniform(1800, 3800)
            place(out, np.sin(2 * np.pi * f * k) * np.exp(-k / 0.008) * rng.uniform(0.2, 1), rng.integers(N))
        return out
    if name == "clock":
        L = int(SR * 0.025)
        k = np.arange(L) / SR
        for i in range(SECONDS):
            f = 2400 if i % 2 == 0 else 2000  # tick, tock
            place(out, np.sin(2 * np.pi * f * k) * np.exp(-k / 0.003), i * SR)
        return out
    if name == "crickets":
        # a few crickets, each chirping in its own rhythm: 3 pulses of a 4.5 kHz tone
        for _ in range(4):
            f = rng.uniform(4200, 4900)
            period = rng.uniform(0.7, 1.3)
            gain = rng.uniform(0.3, 1)
            L = int(SR * 0.012)
            k = np.arange(L) / SR
            pulse = np.sin(2 * np.pi * f * k) * np.sin(np.pi * np.arange(L) / L)
            pos = rng.uniform(0, period)
            while pos < SECONDS:
                for j in range(3):
                    place(out, pulse * gain, int((pos + j * 0.025) * SR))
                pos += period * rng.uniform(0.95, 1.05)
        return out * slow([1, 3], 0.5, rng)
    raise ValueError(name)


def normalize(x):
    return x / (np.sqrt(np.mean(x ** 2)) + 1e-9)


def main(ep_path):
    ep = load_episode(ep_path)
    names = layers_for(ep)
    import hashlib
    rng = np.random.default_rng(int(hashlib.sha1(ep.get("story_title", "").encode()).hexdigest()[:8], 16))
    mix = np.zeros(N)
    for name in names:
        x = layer(name, rng)
        x = x / (np.abs(x).max() + 1e-9) if name in EVENTS else normalize(x)
        mix += GAIN[name] * x
    # soft limiter: rounds off any peak so the bed stays even (peaks at most ~16 dB over the average)
    mix = np.tanh(mix * 0.15 / (np.sqrt(np.mean(mix ** 2)) + 1e-9))
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.7  # headroom; make_audio sets the final level
    stereo = np.stack([mix, np.roll(mix, int(SR * 0.013))], axis=1)  # a touch of width
    OUT.mkdir(exist_ok=True)
    with wave.open(str(OUT / "bed.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((stereo * 32767).astype("<i2").tobytes())
    print("bed.wav:", ", ".join(names))


if __name__ == "__main__":
    main(sys.argv[1])
