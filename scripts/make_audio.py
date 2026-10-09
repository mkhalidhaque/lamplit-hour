"""Mix voice over a looped ambience bed, add an ambience-only tail, normalize loudness.

Usage: python scripts/make_audio.py queue/2026-10-08.json
Env: TAIL_SECONDS (default 600), BED_DB (default -22), LOUDNESS (default -30 LUFS)
Bed: the story's own soundscape built by make_bed.py (layers from the "soundscape" field, e.g. stove crackle +
clock + room tone). A recorded assets/ambience/<ambience>.(mp3|wav|ogg|m4a) is used instead only when the story
names no soundscape. After the story the bed rises gently and plays alone for TAIL_SECONDS, then fades.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import ASSETS, LEAD, OUT, duration, load_episode, run  # noqa: E402

TAIL = float(os.environ.get("TAIL_SECONDS", "600"))
BED_DB = os.environ.get("BED_DB", "-22")
LOUD = os.environ.get("LOUDNESS", "-30")  # quieter than the usual -24 so it is gentle in bed

def find_bed(name):
    for ext in (".mp3", ".wav", ".ogg", ".m4a"):
        p = ASSETS / "ambience" / f"{name}{ext}"
        if p.exists():
            return p
    return None


def main(ep_path):
    ep = load_episode(ep_path)
    name = ep.get("ambience", "rain").lower().split()[0]
    voice = OUT / "voice.mp3"
    total = LEAD + duration(voice) + TAIL
    bed = None if ep.get("soundscape") else find_bed(name)
    if not bed:
        import make_bed
        make_bed.main(ep_path)
        bed = OUT / "bed.wav"
    bed_in = ["-stream_loop", "-1", "-i", str(bed)]
    vend = LEAD + duration(voice) + 3
    # after the story the soundscape rises by about 4 dB over 20 s, so it carries the listener on alone
    rise = f"volume='if(gt(t,{vend:.1f}),min(1.6,1+0.6*(t-{vend:.1f})/20),1)':eval=frame,"
    fade_in = "afade=t=in:st=0:d=6"
    fade_out = f"afade=t=out:st={total - 40:.1f}:d=40"
    fc = (
        f"[0:a]adelay={int(LEAD * 1000)}:all=1,apad=whole_dur={total:.1f}[v];"
        f"[1:a]{rise}aresample=44100,volume={BED_DB}dB,{fade_in},{fade_out}[b];"
        f"[v][b]amix=inputs=2:duration=first:normalize=0,"
        f"loudnorm=I={LOUD}:TP=-6:LRA=7,alimiter=limit=0.5[out]"
    )
    cmd = ["ffmpeg", "-y", "-i", str(voice), *bed_in, "-filter_complex", fc,
           "-map", "[out]", "-t", f"{total:.1f}", "-ac", "2", "-ar", "44100",
           "-c:a", "libmp3lame", "-b:a", "128k", str(OUT / "episode.mp3")]
    run(cmd)
    print(f"episode.mp3: {total / 60:.1f} min (voice {duration(voice) / 60:.1f} min)")


if __name__ == "__main__":
    main(sys.argv[1])
