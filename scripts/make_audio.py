"""Mix voice over a looped ambience bed, add an ambience-only tail, set the final loudness.

Usage: python scripts/make_audio.py queue/2026-10-08.json
Env: TAIL_SECONDS (default 600), BED_UNDER_DB (default 14), RAMP_END (default 0.8), LOUDNESS (default -30 LUFS)
Bed: the story's own soundscape built by make_bed.py (layers from the "soundscape" field, e.g. stove crackle +
clock + room tone). A recorded assets/ambience/<ambience>.(mp3|wav|ogg|m4a) is used instead only when the story
names no soundscape.

Mixing rule (Khalid, 2026-10-10): the voice always stays clearly on top.
- The voice is set to LOUDNESS. The bed starts silent and rises slowly on a smooth curve, reaching its peak
  (BED_UNDER_DB below the voice) at RAMP_END of the way through the story.
- While the teller speaks, the bed also dips by a few dB, and comes back up in the pauses.
- After the story the bed rises about 6 dB over 30 s and plays alone for TAIL_SECONDS, then fades out.
Levels are measured and set by fixed gains (no automatic loudness leveling), so quiet parts stay quiet.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import ASSETS, LEAD, OUT, duration, load_episode, run  # noqa: E402

TAIL = float(os.environ.get("TAIL_SECONDS", "600"))
BED_UNDER = float(os.environ.get("BED_UNDER_DB", "14"))  # how far the bed sits under the voice at its peak
RAMP_END = float(os.environ.get("RAMP_END", "0.8"))  # share of the story by which the bed reaches its peak
LOUD = float(os.environ.get("LOUDNESS", "-30"))  # quieter than the usual -24 so it is gentle in bed
TAIL_RISE = 2.0  # x2 amplitude (~6 dB) when the story ends: the bed carries the listener on alone


def find_bed(name):
    for ext in (".mp3", ".wav", ".ogg", ".m4a"):
        p = ASSETS / "ambience" / f"{name}{ext}"
        if p.exists():
            return p
    return None


def lufs(path, af=None):
    """Integrated loudness of a file (EBU R128), in LUFS."""
    chain = f"{af}," if af else ""
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", f"{chain}ebur128", "-f", "null", "-"])
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])


def bed_curve(start, story, vend, total):
    """ffmpeg volume expression: silent before the voice, then a slow ease-in rise to 1 at RAMP_END of the
    story (smoothstep squared, so the first minutes stay very quiet), then the tail rise, then the fade out."""
    p = f"clip((t-{start:.1f})/{story * RAMP_END:.1f},0,1)"
    ramp = f"pow({p}*{p}*(3-2*{p}),2)"
    rise = f"(1+{TAIL_RISE - 1}*clip((t-{vend:.1f})/30,0,1))"
    fade = f"clip(({total:.1f}-t)/40,0,1)"
    return f"{ramp}*{rise}*{fade}"


def main(ep_path):
    ep = load_episode(ep_path)
    name = ep.get("ambience", "rain").lower().split()[0]
    voice = OUT / "voice.mp3"
    story = duration(voice)
    total = LEAD + story + TAIL
    bed = None if ep.get("soundscape") else find_bed(name)
    if not bed:
        import make_bed
        make_bed.main(ep_path)
        bed = OUT / "bed.wav"
    vgain = LOUD - lufs(voice)
    bgain = LOUD - BED_UNDER - lufs(bed)
    vend = LEAD + story + 3
    st = "aformat=sample_rates=44100:channel_layouts=stereo"
    fc = (
        f"[0:a]{st},volume={vgain:.2f}dB,adelay={int(LEAD * 1000)}:all=1,apad=whole_dur={total:.1f},"
        f"asplit=2[v][key];"
        f"[1:a]{st},volume={bgain:.2f}dB,volume='{bed_curve(LEAD, story, vend, total)}':eval=frame[b0];"
        # gentle ducking: about 3 dB less bed while the voice speaks, released slowly in the pauses
        f"[b0][key]sidechaincompress=threshold=0.015:ratio=2:attack=150:release=1200:knee=6[b];"
        f"[v][b]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.5:level=0[out]"
    )
    cmd = ["ffmpeg", "-y", "-i", str(voice), "-stream_loop", "-1", "-i", str(bed), "-filter_complex", fc,
           "-map", "[out]", "-t", f"{total:.1f}", "-ac", "2", "-ar", "44100",
           "-c:a", "libmp3lame", "-b:a", "128k", str(OUT / "episode.mp3")]
    run(cmd)
    print(f"episode.mp3: {total / 60:.1f} min (voice {story / 60:.1f} min at {LOUD:.0f} LUFS, "
          f"bed rises from silence to {BED_UNDER:.0f} dB under the voice)")


if __name__ == "__main__":
    main(sys.argv[1])
