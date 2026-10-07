"""Turn the episode script into out/voice.mp3 with free edge-tts voices.

Usage: python scripts/make_voice.py queue/2026-10-08.json
Env: VOICE (default en-GB-SoniaNeural), RATE_FIRST (default -15%), RATE_SECOND (default -30%).
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, load_episode, parse_script, run  # noqa: E402

VOICE = os.environ.get("VOICE", "en-GB-SoniaNeural")
RATE_FIRST = os.environ.get("RATE_FIRST", "-15%")
RATE_SECOND = os.environ.get("RATE_SECOND", "-30%")


async def speak(text, rate, path, tries=4):
    import edge_tts
    last = None
    for _ in range(tries):
        try:
            await edge_tts.Communicate(text, VOICE, rate=rate).save(str(path))
            if Path(path).exists() and Path(path).stat().st_size > 500:
                return
        except Exception as e:  # dropped connection, NoAudioReceived
            last = e
        await asyncio.sleep(2)
    raise RuntimeError(f"voice failed for {text[:60]!r}: {last}")


def silence(seconds, path):
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
         "-t", str(seconds), "-c:a", "libmp3lame", "-b:a", "96k", str(path)])


async def main(ep_path):
    ep = load_episode(ep_path)
    work = OUT / "voice_parts"
    work.mkdir(parents=True, exist_ok=True)
    parts, n = [], 0
    for kind, value, second in parse_script(ep["script"]):
        n += 1
        f = work / f"{n:04d}.mp3"
        if kind == "say":
            await speak(value, RATE_SECOND if second else RATE_FIRST, f)
        else:
            silence(value, f)
        parts.append(f)
        # a short breath after each spoken paragraph
        if kind == "say":
            n += 1
            g = work / f"{n:04d}.mp3"
            silence(1.2 if second else 0.8, g)
            parts.append(g)
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", str(OUT / "voice.mp3")])
    print(f"voice.mp3 from {len(parts)} parts")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
