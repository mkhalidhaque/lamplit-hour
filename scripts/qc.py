"""Automatic quality checks for a queued episode. Exit code 1 = fail (blocks the build).

Usage: python scripts/qc.py queue/2026-10-08.json
Checks: length, pause markers, banned AI-sounding phrases, alarm words, religion words,
an opening hook and grounding context, enough sensory description,
similarity to earlier episodes, and series/place repeats in the last 14 days.
"""
import csv
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import SECOND_MARKER, load_episode, plain_text  # noqa: E402

WORDS_MIN, WORDS_MAX = 1600, 2300  # ~15-20 min of narration plus ambience tail
BANNED = ["tapestry", "symphony", "embrace", "testament", "nestled", "whisper of", "a sense of",
          "as if the world itself", "little did", "in the heart of", "bustling", "delve", "journey of", "magical"]
ALARM = ["scream", "blood", "crash", "gun", "monster", "died", "dead", "suddenly", "shadowy figure", "explod",
         "thunderclap", "terrified", "panic", "knife", "danger", "attack", "storm raged"]
RELIGION = ["prayer", "pray", "church", "chapel", "cathedral", "mosque", "synagogue", "scripture", "bible",
            "quran", "saint", "priest", "vicar", "worship", "sermon", "blessing", "christmas", "easter", "eid",
            "diwali", "ramadan", "hanukkah", "angel", "holy"]
# Sensory words, grouped by sense, used to make sure the story is described and not just summarized
SENSES = {
    "sound": ["click", "tick", "creak", "hum", "mutter", "rustl", "hiss", "lap", "patter", "drip", "murmur",
              "sound", "quiet", "soft", "rattl", "chime", "knock", "whistl", "crackl", "sigh"],
    "touch": ["warm", "cool", "cold", "soft", "rough", "smooth", "heavy", "damp", "wet", "dry", "snug", "heat",
              "wool", "worn", "stiff", "silk", "prickl", "tender"],
    "smell": ["smell", "scent", "smok", "toast", "tea", "pine", "salt", "bread", "peel", "coffee", "spice",
              "cinnamon", "resin", "earth", "lavender", "honey"],
    "sight": ["glow", "light", "shin", "amber", "gold", "gray", "cream", "blue", "green", "orange", "shadow",
              "pale", "flicker", "color", "lamp", "dark", "silver", "plum"],
}
MIN_SENSE_HITS = 60       # in the first telling
MIN_FIRST_PARAGRAPHS = 16  # first telling must be a real story, not a sketch
NGRAM = 8
MAX_SHARED_NGRAMS = 3


def words(text):
    return re.findall(r"[a-z']+", text.lower())


def ngrams(ws, n=NGRAM):
    return {" ".join(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def hits(text, terms):
    t = " " + " ".join(words(text)) + " "
    return sorted({w for w in terms if re.search(r"\b" + re.escape(w), t)})


def main(path):
    ep = load_episode(path)
    script = ep["script"]
    text = plain_text(script)
    ws = words(text)
    problems, notes = [], []

    n = len(ws)
    if not WORDS_MIN <= n <= WORDS_MAX:
        problems.append(f"length {n} words, expected {WORDS_MIN}-{WORDS_MAX}")
    if SECOND_MARKER not in script:
        problems.append("missing [[SECOND]] marker for the slower second telling")
    paras = [p for p in re.split(r"\n\s*\n", script) if p.strip()]
    pauses = len(re.findall(r"\[(?:long )?pause\]", script))
    if pauses < max(1, len(paras) // 2 - 1):
        problems.append(f"only {pauses} pause markers for {len(paras)} paragraphs")
    for label, terms in (("banned phrases", BANNED), ("alarm words", ALARM)):
        h = hits(text, terms)
        if h:
            problems.append(f"{label}: {', '.join(h)}")
    myth = ep.get("series", "").lower().startswith("myths")
    h = hits(text + " " + ep.get("story_title", "") + " " + " ".join(ep.get("tags", [])),
             [w for w in RELIGION if not (myth and w in {"angel", "holy", "saint"})])
    if h:
        problems.append(f"religion words: {', '.join(h)}")
    narration = re.sub(r"[\"\u201c][^\"\u201d]*[\"\u201d]", " ", text)
    narration = re.sub(r"^\s*welcome back to fernwick\.", " ", narration.strip(), flags=re.I)
    narration = re.sub(r"good night\.\s*$", " ", narration.strip(), flags=re.I)
    addr = re.findall(r"\b(?:you|your|yours|yourself|sleep well|goodnight|breathe|breath)\b", narration.lower())
    if addr:
        problems.append("speaks to the listener (or relaxation cues) outside dialogue: " + ", ".join(sorted(set(addr))))
    flat = " ".join(text.lower().split())
    if not flat.startswith("welcome back to fernwick."):
        problems.append('does not open with "Welcome back to Fernwick."')
    if not flat.rstrip().endswith("good night."):
        problems.append('does not end with "Good night."')

    # hook and grounding context: the first 150 words after the welcome must carry the hook
    first = script.split(SECOND_MARKER)[0]
    opening = " ".join(words(plain_text(first))[4:154])
    hook = ep.get("hook", "")
    if not hook:
        problems.append("missing field: hook (the one-sentence question or small mystery that opens the story)")
    else:
        key = {w for w in words(hook) if len(w) > 3}
        found = {w for w in key if w in opening.split()}
        if len(found) < 0.6 * len(key):
            problems.append("hook: the story must open with the hook (most of its words belong in the first 150 words)")
    if not ep.get("context"):
        problems.append("missing field: context (who, where and why it matters, set up in the first two paragraphs)")
    if re.match(r"(it is|it was) (the )?(a |an )?\w*\s?(evening|night|morning|middle of|early|late)", opening):
        problems.append("opening starts with the date or weather; open with the hook instead")

    # description: enough paragraphs and sensory detail in the first telling
    fparas = [p for p in re.split(r"\n\s*\n", plain_text(first)) if words(p)]
    if len(fparas) < MIN_FIRST_PARAGRAPHS:
        problems.append(f"first telling has {len(fparas)} paragraphs, expected at least {MIN_FIRST_PARAGRAPHS}")
    fwords = " " + " ".join(words(plain_text(first))) + " "
    sense_hits = {k: len(re.findall(r"\b(?:" + "|".join(map(re.escape, v)) + r")", fwords)) for k, v in SENSES.items()}
    notes.append("sensory words: " + ", ".join(f"{k} {v}" for k, v in sense_hits.items()))
    if sum(sense_hits.values()) < MIN_SENSE_HITS:
        problems.append(f"only {sum(sense_hits.values())} sensory words in the first telling, expected {MIN_SENSE_HITS}+")
    thin = [k for k, v in sense_hits.items() if v < 6]
    if thin:
        problems.append("too little description for: " + ", ".join(thin))

    # sentence length should fall: first third vs last third of the first telling
    sents = [len(words(s)) for s in re.split(r"[.!?]+", plain_text(first)) if words(s)]
    if len(sents) > 12:
        a = sum(sents[: len(sents) // 3]) / (len(sents) // 3)
        b = sum(sents[-(len(sents) // 3):]) / (len(sents) // 3)
        notes.append(f"avg sentence length start {a:.1f} -> end {b:.1f}")
        if b > a:
            notes.append("warning: sentences do not get shorter toward the end")

    # similarity to earlier episodes
    here = ngrams(ws)
    this = Path(path).resolve()
    for p in sorted(list(Path("queue").glob("*.json")) + list(Path("published").glob("*.json"))):
        if p.resolve() == this:
            continue
        try:
            other = ngrams(words(plain_text(json.loads(p.read_text(encoding="utf-8"))["script"])))
        except Exception:
            continue
        shared = len(here & other)
        if shared > MAX_SHARED_NGRAMS:
            problems.append(f"{shared} shared {NGRAM}-word phrases with {p.name}")

    # series/place combination used in the last 14 days
    log = Path("world/story_log.csv")
    if log.exists():
        cutoff = date.today() - timedelta(days=14)
        for row in csv.DictReader(log.open(encoding="utf-8")):
            try:
                d = date.fromisoformat(row["date"])
            except Exception:
                continue
            if row.get("story_title") == ep.get("story_title"):
                continue  # this same story, being rebuilt
            if d >= cutoff and row.get("place") == ep.get("place") and row.get("series") == ep.get("series"):
                problems.append(f"same series+place already used on {row['date']}")

    for f in ("story_title", "series", "place", "ambience", "title_options", "thumbnail_text",
              "description_summary", "description_setting", "tags", "short_excerpt",
              "source_tradition", "source_note"):
        if not ep.get(f):
            problems.append(f"missing field: {f}")

    print(f"QC for {path}: {n} words")
    for line in notes:
        print("  note:", line)
    if problems:
        print("FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print("PASSED automatic checks (human review still required)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
