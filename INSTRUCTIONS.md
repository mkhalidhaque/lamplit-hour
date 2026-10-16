# Fernwick Nights: channel instructions

The one page to read first. It says what the channel is, what Khalid has decided, and where every rule lives.
Claude reads this before every daily story. When Khalid gives new direction, add it here (with the date) and in the detailed file it belongs to.

## 1. The channel
- **Name:** Fernwick Nights (handle @fernwicknights). The repo keeps its old name, `lamplit-hour`.
- **What it is (from 2026-10-15):** Greek myths retold slowly and calmly as bedtime stories for grown-ups, a different figure each night, chosen from the ones most people have not met yet (Clytie, Hypnos, the Hesperides, Philoctetes...). One new video a day, 15 to 20 minutes, then quiet ambience. The earlier Fernwick-town tales (Oct 7 to 14) stay up but are no longer made.
- **Look and sound:** one dark, warm painted scene from the myth with one flickering light, the fern-and-lantern logo stamped on frame, thumbnail and Short; a free edge-tts voice; rain, wind, ocean, harbor or stove ambience.
- **Goal:** daily uploads at $0 cost, fully automated, growing toward monetization.

## 2. Hard rules (never break these)
1. **No organized religion.** No prayer, worship, clergy, places of worship, scripture, saints, religious holidays or symbols. Greek myths are told as old stories, never as worship or belief: no temples, altars, sacrifices, priests or rituals.
2. **Never write the word "bible".** Older world notes are in the **Fernwick Guide** (`world/guide.md`).
3. **Nothing frightening.** Myths have events (a loss, a jealous god, a long wait); tell them softly, briefly and at a distance, never graphic, no battles, no jump or loud moments, and always end calm. Skip myths built on assault, abduction or cruelty.
4. **Copyright-safe.** Retell from the ancient public-domain sources (Hesiod, Homer, Ovid, Apollodorus, Hyginus...) in our own words; never follow a modern translation or retelling. Tellers are invented, never real people.
5. **Uploads go up private.** Khalid listens and publishes in YouTube Studio himself.

## 3. What makes a good story
Khalid's notes (2026-10-08, 2026-10-15): a pleasant mood with nothing behind it is not enough; the figure must be interesting.
- **A fresh figure.** Not the household names (Zeus, Athena, Heracles, Odysseus, Medusa...); they may appear on the side. Never the same figure twice (`world/greek_figures.csv`).
- **Hook first.** Right after the intro, the striking question or fact about tonight's figure (why does a flower follow the sun all day?). Never open with the date or the weather. Answer it by the middle.
- **Context up front.** Who the figure is, their family and home, where in the Greek world, and how they touch a myth the listener already knows.
- **Real substance.** What the ancient writers say, how versions differ, what survives today (a star, a flower, a word). Accurate.
- **Rich, exact description.** Every scene has a sound, a smell or taste, a texture, a temperature and precise sights. "Three apples, gold as late sun, one with a leaf still on its stem", not "some apples".
- **A wise teller.** Each night someone different (an old shepherd, a net-mender on a harbor wall, a beekeeper on a mountain of thyme) tells the myth to "you", with a few asides of their own.
- **Energy only goes down.** Sentences get shorter and softer; more pauses in the last third; the character settles to sleep.
- **Keep them listening (Khalid, 2026-10-16).** The hook opens a question the listener wants answered; a gentle mystery runs through the story; each chapter adds a small reveal or surprise; the answer lands as a satisfying payoff before the last third, then everything winds down.
- **Never say "lesser known"** (or lesser-known, little-known, obscure) anywhere: script, titles, description, tags, series, docs. qc.py blocks it.
- **Plain, human words.** No AI-sounding phrases (tapestry, nestled, embrace, a sense of...).

## 4. Shape of every episode
1. Intro: "Welcome to Fernwick Nights." + tonight's title, that it is a story from the Greek myths (worded freshly each night), the teller + one "get comfortable" line.
2. Hook (100 to 150 words), then context (100 to 150 words), then backstory woven in.
3. The story, 16 to 22 short paragraphs, 4 to 6 named chapters.
4. A shorter, slower second telling ("Once More, Slowly").
5. Outro from the teller, ending exactly "Good night." Then ambience plays alone.
Total about 1,750 to 2,150 words. The full spec, JSON fields and voice list are in `prompts/daily-story.md`.

## 5. Variety rules
- Read `world/story_log.csv` (last 14 rows) and recent `published/` files before choosing.
- Never repeat a figure (`world/greek_figures.csv`, checked by qc.py). No repeated teller within 7 days (checked).
- Vary the kind of figure (nymph, mortal, Titan, minor god, constellation, wind, river) and the part of the Greek world; ideas in `world/myth_ideas.md`.
- Titles name the figure and use a search phrase (Greek Mythology Sleep Story, Greek Myths for Sleep...).
- Oct 17 to 31: about every other story may lean toward night and shadow (Nyx, Hypnos, Lethe), told gently.
- Long myths become parts on consecutive days, each part ending calm, never a cliffhanger.

## 6. The daily routine
1. Around noon Eastern, Claude picks and writes the day's story as `queue/YYYY-MM-DD.json`.
2. `python scripts/qc.py` must pass (hook, length, sensory detail, banned and religion words, repetition).
3. Claude adds the figure to `world/greek_figures.csv` and commits to `main`.
4. GitHub Actions builds the voice, video, thumbnail and Short, uploads to YouTube as **private**, and logs it.
5. Khalid listens to the first minutes in YouTube Studio and sets it public or scheduled.
Build files are deleted after 1 to 2 days.

## 7. Where things live
| What | Where |
| --- | --- |
| This page | `INSTRUCTIONS.md` |
| Full daily writing spec | `prompts/daily-story.md` |
| Figures already used | `world/greek_figures.csv` |
| Ideas for figures | `world/myth_ideas.md` |
| Fernwick Guide (the retired Fernwick-town tales) | `world/guide.md` |
| Story log | `world/story_log.csv` |
| Quality checks | `scripts/qc.py` |
| Build and upload | `.github/workflows/build-episode.yml` |
| Logo and banner | `assets/brand/` |

## 8. Decision log
- 2026-10-07: Channel named Fernwick Nights. World Fernwick and the Fernwick Guide approved. Free voice. 15 to 20 minute videos. Pipeline in GitHub Actions. Daily story, Claude chooses. No organized religion; mythology allowed. Never say "bible". Cozy-spooky season Oct 17 to 31. Long stories split into parts.
- 2026-10-08: Every story needs a hook, context and rich description. A different wise teller each night, speaking to the listener. Concrete, exact sensory detail in every scene.
- 2026-10-15: Pivot to Greek mythology (Khalid: the Fernwick tales got no traction). Every story from 2026-10-15 is one Greek figure most listeners have not met, interesting, with a strong hook, told calmly for sleep by a different wise teller. Same channel, name, logo, intro and outro. Fernwick-town tales retired. Myth told as story, never worship. Never repeat a figure.
- 2026-10-16: Never say "lesser known" (Khalid). Stories must hook listeners and keep them: an open question in the hook, a gentle mystery through the middle, a reveal in each chapter and a satisfying payoff before the calm wind-down. Series renamed "Greek Myths for Sleep".
