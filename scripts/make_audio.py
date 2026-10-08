"""Mix voice over a looped ambience bed, add an ambience-only tail, normalize loudness.

Usage: python scripts/make_audio.py queue/2026-10-08.json
Env: TAIL_SECONDS (default 150), BED_DB (default -22), LOUDNESS (default -30 LUFS)
Bed: assets/ambience/<ambience>.(mp3|wav|ogg|m4a) if it exists, else synthesized steady noise.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import ASSETS, LEAD, OUT, duration, load_episode, run  # noqa: E402

TAIL = float(os.environ.get("TAIL_SECONDS", "150"))
BED_DB = os.environ.get("BED_DB", "-22")
LOUD = os.environ.get("LOUDNESS", "-30")  # quieter than the usual -24 so it is gentle in bed

# filters that turn white noise into steady, peak-free beds (used when no recorded bed exists)
SYNTH = {
    "rain": "anoisesrc=color=pink:amplitude=0.6,highpass=f=400,lowpass=f=6000",
    "wind": "anoisesrc=color=brown:amplitude=0.8,lowpass=f=500,tremolo=f=0.07:d=0.35",
    "ocean": "anoisesrc=color=brown:amplitude=0.9,lowpass=f=700,tremolo=f=0.11:d=0.5",
    "harbor": "anoisesrc=color=brown:amplitude=0.9,lowpass=f=700,tremolo=f=0.11:d=0.5",
    "stove": "anoisesrc=color=brown:amplitude=0.6,lowpass=f=300",
}


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
    bed = find_bed(name)
    if bed:
        bed_in = ["-stream_loop", "-1", "-i", str(bed)]
        bed_filter = ""
    else:
        syn = SYNTH.get(name, SYNTH["rain"])
        bed_in = ["-f", "lavfi", "-i", syn]
        bed_filter = ""
    fade_in = "afade=t=in:st=0:d=6"
    fade_out = f"afade=t=out:st={total - 25:.1f}:d=25"
    fc = (
        f"[0:a]adelay={int(LEAD * 1000)}:all=1,apad=whole_dur={total:.1f}[v];"
        f"[1:a]{bed_filter}aresample=44100,volume={BED_DB}dB,{fade_in},{fade_out}[b];"
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
