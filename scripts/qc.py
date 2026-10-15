"""Automatic quality checks for a queued episode. Exit code 1 = fail (blocks the build).

Usage: python scripts/qc.py queue/2026-10-08.json
Checks: length, pause markers, banned AI-sounding phrases, alarm words, religion words,
the spoken intro (title, teller), chapters, teller/listener/voice fields,
an opening hook and grounding context, enough sensory description,
similarity to earlier episodes, and (since 2026-10-15, lesser-known Greek myths) the myth figure:
named in every title, sources given, and never used before (world/greek_figures.csv).
"""
import csv
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import CHAPTER_RE, SECOND_MARKER, VOICES, load_episode, plain_text  # noqa: E402

WORDS_MIN, WORDS_MAX = 1650, 2200  # ~15-20 min at ~110 words a minute, plus ambience tail
BANNED = ["tapestry", "symphony", "embrace", "testament", "nestled", "whisper of", "a sense of",
          "as if the world itself", "little did", "in the heart of", "bustling", "delve", "journey of", "magical"]
ALARM = ["scream", "blood", "crash", "gun", "monster", "died", "dead", "suddenly", "shadowy figure", "explod",
         "thunderclap", "terrified", "panic", "knife", "danger", "attack", "storm raged"]
RELIGION = ["prayer", "pray", "church", "chapel", "cathedral", "mosque", "synagogue", "scripture", "bible",
            "quran", "saint", "priest", "vicar", "worship", "sermon", "blessing", "christmas", "easter", "eid",
            "diwali", "ramadan", "hanukkah", "angel", "holy", "temple", "altar", "sacrific"]
# Sensory words, grouped by sense, used to make sure the story is described and not just summarized
SENSES = {
    "sound": ["cicada", "bell", "click", "tick", "creak", "hum", "mutter", "rustl", "hiss", "lap", "patter", "drip", "murmur",
              "sound", "quiet", "soft", "rattl", "chime", "knock", "whistl", "crackl", "sigh"],
    "touch": ["warm", "cool", "cold", "soft", "rough", "smooth", "heavy", "damp", "wet", "dry", "snug", "heat",
              "wool", "worn", "stiff", "silk", "prickl", "tender", "stone", "sand", "linen", "bronze"],
    "smell": ["smell", "scent", "smok", "toast", "tea", "pine", "salt", "bread", "peel", "coffee", "spice",
              "cinnamon", "resin", "earth", "lavender", "honey", "thyme", "olive", "figs", "myrtle", "laurel", "wine"],
    "sight": ["glow", "light", "shin", "amber", "gold", "gray", "cream", "blue", "green", "orange", "shadow",
              "pale", "flicker", "color", "lamp", "dark", "silver", "plum", "stars", "white", "purple"],
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
    paras = [p for p in re.split(r"\n\s*\n", plain_text(script)) if words(p)]
    pauses = len(re.findall(r"\[(?:long )?pause\]", script))
    if pauses < max(1, len(paras) // 2 - 1):
        problems.append(f"only {pauses} pause markers for {len(paras)} paragraphs")
    for label, terms in (("banned phrases", BANNED), ("alarm words", ALARM)):
        h = hits(text, terms)
        if h:
            problems.append(f"{label}: {', '.join(h)}")
    # Greek myth is told as story, not worship: "angel", "holy" and "saint" never fit, temples and altars are blocked
    h = hits(text + " " + ep.get("story_title", "") + " " + " ".join(ep.get("tags", [])), RELIGION)
    if h:
        problems.append(f"religion words: {', '.join(h)}")
    # spoken intro: "Welcome to Fernwick Nights.", tonight's title and who is telling it
    paras_plain = [" ".join(words(p)) for p in re.split(r"\n\s*\n", plain_text(script)) if words(p)]
    intro = paras_plain[0] if paras_plain else ""
    if not intro.startswith("welcome to fernwick nights"):
        problems.append('first paragraph must start "Welcome to Fernwick Nights."')
    title_core = " ".join(words(re.sub(r"\(part.*?\)", "", ep.get("story_title", ""), flags=re.I)))
    if title_core and title_core not in intro:
        problems.append("intro must say tonight's story title")
    teller = ep.get("teller") or {}
    if not (isinstance(teller, dict) and teller.get("name") and teller.get("who")):
        problems.append('missing field: teller {"name": ..., "who": ...} (the wise storyteller for tonight)')
    elif " ".join(words(teller["name"])) not in intro:
        problems.append("intro must name the teller")
    if not ep.get("listener"):
        problems.append("missing field: listener (who the teller is telling the story to)")
    from make_bed import LAYERS
    bad = [x for x in ep.get("soundscape", []) if x not in LAYERS]
    if not ep.get("soundscape") or bad:
        problems.append("soundscape must be a list of 2 to 4 of: " + ", ".join(LAYERS))
    if ep.get("voice") not in VOICES:
        problems.append("voice must be one of: " + ", ".join(VOICES))
    chapters = re.findall(CHAPTER_RE, script.split(SECOND_MARKER)[0])
    if not script.lstrip().startswith("[[CHAPTER"):
        problems.append("script must start with a [[CHAPTER Welcome]] line")
    if len(chapters) < 4:
        problems.append(f"{len(chapters)} chapters in the first telling, expected at least 4")
    # no relaxation instructions in the story itself (the intro may say "get comfortable")
    cues = re.findall(r"\b(?:breathe|breath|inhale|exhale|sleep well|relax your|close your eyes)\b",
                      " ".join(paras_plain[1:]))
    if cues:
        problems.append("relaxation cues in the story: " + ", ".join(sorted(set(cues))))
    if not " ".join(paras_plain).endswith("good night"):
        problems.append('does not end with "Good night."')
    for t in ep.get("title_options", []):
        if len(t) > 100:
            problems.append(f"title over 100 characters: {t}")

    # hook and grounding context: the first 150 words after the intro must carry the hook
    first = script.split(SECOND_MARKER)[0]
    after_intro = re.split(r"\n\s*\n", plain_text(first).strip(), maxsplit=1)
    opening = " ".join(words(after_intro[-1])[:150])
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

    # the myth figure (Khalid, 2026-10-15): searchable titles, real sources, never the same figure twice
    figure = (ep.get("myth_figure") or "").strip()
    if not figure:
        problems.append("missing field: myth_figure (tonight's lesser-known Greek figure)")
    else:
        fig = " ".join(words(figure))
        for t in ep.get("title_options", []):
            if fig not in " ".join(words(t)):
                problems.append(f"title must name {figure}: {t}")
        if fig not in " ".join(paras_plain[:4]):
            problems.append(f"name {figure} in the opening (intro, hook or context)")
        used = Path("world/greek_figures.csv")
        if used.exists():
            core = lambda t: " ".join(words(re.sub(r"\(part.*?\)", "", t or "", flags=re.I)))
            for row in csv.DictReader(used.open(encoding="utf-8")):
                if " ".join(words(row.get("myth_figure", ""))) == fig and core(row.get("story_title")) != core(ep.get("story_title")):
                    problems.append(f"{figure} was already used on {row.get('date')} ({row.get('story_title')})")
            if not any(" ".join(words(r.get("myth_figure", ""))) == fig for r in csv.DictReader(used.open(encoding="utf-8"))):
                problems.append(f"add {figure} to world/greek_figures.csv")
    if not ep.get("myth_sources"):
        problems.append("missing field: myth_sources (the ancient sources followed)")

    # teller not repeated within 7 days
    log = Path("world/story_log.csv")
    name = (ep.get("teller") or {}).get("name", "") if isinstance(ep.get("teller"), dict) else ""
    if log.exists() and name:
        cutoff = date.today() - timedelta(days=7)
        for row in csv.DictReader(log.open(encoding="utf-8")):
            try:
                d = date.fromisoformat(row["date"])
            except Exception:
                continue
            if row.get("story_title") == ep.get("story_title"):
                continue  # this same story, being rebuilt
            if d >= cutoff and row.get("teller") == name:
                problems.append(f"teller {name} already told a story on {row['date']}")

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
