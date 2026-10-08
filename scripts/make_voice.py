"""Turn the episode script into out/voice.mp3 with free edge-tts voices.

Usage: python scripts/make_voice.py queue/2026-10-08.json
The voice is the episode's "voice" field (one of common.VOICES, chosen to fit the teller); env VOICE overrides it.
Pacing aims at about 110 words a minute overall: a slowed voice plus a rest after every paragraph.
Env: RATE_FIRST (default -22%), RATE_SECOND (default -32%).
Also writes out/chapters.json: the start time of each [[CHAPTER Name]] in the finished episode.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import DEFAULT_VOICE, LEAD, OUT, VOICES, duration, load_episode, parse_script, run  # noqa: E402

RATE_FIRST = os.environ.get("RATE_FIRST", "-22%")
RATE_SECOND = os.environ.get("RATE_SECOND", "-32%")
GAP_FIRST, GAP_SECOND = 1.4, 2.0  # rest after each spoken paragraph


def pick_voice(ep):
    v = os.environ.get("VOICE") or ep.get("voice") or DEFAULT_VOICE
    return v if v in VOICES or os.environ.get("VOICE") else DEFAULT_VOICE


async def speak(text, rate, path, tries=4, voice=None):
    import edge_tts
    last = None
    for i in range(tries):
        v = voice or os.environ.get("VOICE") or DEFAULT_VOICE
        if i == tries - 1 and v != DEFAULT_VOICE:
            v = DEFAULT_VOICE  # last try: the voice that has always worked
        try:
            await edge_tts.Communicate(text, v, rate=rate).save(str(path))
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
    voice = pick_voice(ep)
    print(f"voice: {voice}")
    parts, n, t, chapters, spoken = [], 0, 0.0, [], 0
    for kind, value, second in parse_script(ep["script"]):
        if kind == "chapter":
            chapters.append({"title": value, "start": round(LEAD + t, 1)})
            continue
        n += 1
        f = work / f"{n:04d}.mp3"
        if kind == "say":
            await speak(value, RATE_SECOND if second else RATE_FIRST, f, voice=voice)
            spoken += len(value.split())
        else:
            silence(value, f)
        parts.append(f)
        t += duration(f)
        # a short rest after each spoken paragraph
        if kind == "say":
            n += 1
            g = work / f"{n:04d}.mp3"
            silence(GAP_SECOND if second else GAP_FIRST, g)
            parts.append(g)
            t += duration(g)
    if chapters:
        chapters[0]["start"] = 0.0  # YouTube needs the first chapter at 0:00
        chapters.append({"title": "Quiet ambience to stay asleep", "start": round(LEAD + t + 3, 1)})
    (OUT / "chapters.json").write_text(json.dumps(chapters, indent=1))
    print(f"pace: {spoken} words in {t / 60:.1f} min = {spoken / (t / 60):.0f} words a minute (aim ~110)")
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", str(OUT / "voice.mp3")])
    print(f"voice.mp3 from {len(parts)} parts")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
