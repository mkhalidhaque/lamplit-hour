"""Captions for the episode: out/captions.srt (uploaded to YouTube as a caption track), out/captions.vtt,
and out/captions.ass (burned softly into the video by make_video.py).

make_voice.py calls add_paragraph() for every spoken paragraph with its start and end time in the finished
episode and, when edge-tts sent them, the time of each spoken word. Cues are short (two lines at most) and break
at sentence or clause ends. Without word times, a paragraph's time is shared out by the length of each cue.
"""
import re

MAX_LINE = 42  # characters per caption line
MAX_CUE = 2 * MAX_LINE
MIN_CUE_SECONDS = 1.2
WORD_RE = re.compile(r"[\w'’]+")

# Fernwick Nights look: warm cream serif, soft dark edge, low and centred, clear of the logo in the corner.
ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Fernwick,DejaVu Serif,40,&H30CDE8F4,&H30CDE8F4,&H60000000,&H00000000,0,0,0,0,100,100,0.5,0,1,2.2,0,2,460,460,64,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def split_cues(text):
    """Split a paragraph into caption-sized pieces, preferring sentence ends, then commas, then spaces."""
    sentences = re.split(r"(?<=[.!?…])\s+|(?<=[.!?…][\"”’)])\s+", text.strip())
    pieces = []
    for s in sentences:
        s = s.strip()
        while len(s) > MAX_CUE:
            # aim for even pieces (no short leftover), cutting at a comma near the aim if there is one
            aim = len(s) // -(-len(s) // MAX_CUE)
            cut = max(s.rfind(", ", 0, aim + 12), s.rfind("; ", 0, aim + 12), s.rfind(" - ", 0, aim + 12))
            if cut < aim * 2 // 3:
                cut = s.rfind(" ", 0, aim + 1)
            if cut <= 0:
                cut = MAX_CUE
            pieces.append(s[: cut + 1].strip())
            s = s[cut + 1:].strip()
        if s:
            pieces.append(s)
    # join very short neighbours ("Yes." "She smiled.") so cues are not too quick to read
    out = []
    for p in pieces:
        if out and len(out[-1]) + 1 + len(p) <= MAX_LINE:
            out[-1] = f"{out[-1]} {p}"
        else:
            out.append(p)
    return out


def wrap(text):
    """Two balanced lines when the cue is longer than one line."""
    if len(text) <= MAX_LINE:
        return [text]
    mid = len(text) // 2
    spaces = [i for i, c in enumerate(text) if c == " "]
    cut = min(spaces, key=lambda i: abs(i - mid)) if spaces else mid
    return [text[:cut].strip(), text[cut:].strip()]


class Captions:
    def __init__(self):
        self.cues = []  # (start, end, text)

    def add_paragraph(self, text, start, end, words=None):
        pieces = split_cues(text)
        counts = [len(WORD_RE.findall(p)) for p in pieces]
        starts = None
        if words and sum(counts) == len(words):
            starts, i = [], 0
            for c in counts:
                starts.append(start + words[i][0] if c else None)
                i += c
            if any(s is None for s in starts):
                starts = None
        if starts is None:  # share the paragraph's time out by length
            total = sum(len(p) for p in pieces) or 1
            starts, t = [], start
            for p in pieces:
                starts.append(t)
                t += (end - start) * len(p) / total
        for k, p in enumerate(pieces):
            s = max(starts[k], self.cues[-1][1] if self.cues else 0)
            e = starts[k + 1] if k + 1 < len(pieces) else end
            e = max(e, s + MIN_CUE_SECONDS)
            self.cues.append((s, e, p))

    def write(self, out_dir):
        def srt_time(t):
            ms = int(round(t * 1000))
            return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

        def ass_time(t):
            cs = int(round(t * 100))
            return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"

        srt, vtt, ass = [], ["WEBVTT", ""], [ASS_HEADER]
        for n, (s, e, text) in enumerate(self.cues, 1):
            lines = wrap(text)
            srt += [str(n), f"{srt_time(s)} --> {srt_time(e)}", *lines, ""]
            vtt += [f"{srt_time(s).replace(',', '.')} --> {srt_time(e).replace(',', '.')}", *lines, ""]
            safe = "\\N".join(ln.replace("{", "(").replace("}", ")") for ln in lines)
            ass.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Fernwick,,0,0,0,,{safe}\n")
        (out_dir / "captions.srt").write_text("\n".join(srt), encoding="utf-8")
        (out_dir / "captions.vtt").write_text("\n".join(vtt), encoding="utf-8")
        (out_dir / "captions.ass").write_text("".join(ass), encoding="utf-8")
        return len(self.cues)
