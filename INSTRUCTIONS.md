# Fernwick Nights: channel instructions

The one page to read first. It says what the channel is, what Khalid has decided, and where every rule lives.
Claude reads this before every daily story. When Khalid gives new direction, add it here (with the date) and in the detailed file it belongs to.

## 1. The channel
- **Name:** Fernwick Nights (handle @fernwicknights). The repo keeps its old name, `lamplit-hour`.
- **What it is:** original, calm bedtime stories for grown-ups, set in Fernwick, an invented quiet seaside town. One new video a day, 15 to 20 minutes, then quiet ambience.
- **Look and sound:** one dark, warm picture of the place with one flickering light, the fern-and-lantern logo stamped on frame, thumbnail and Short; a free edge-tts voice; rain, wind, ocean, harbor or stove ambience.
- **Goal:** daily uploads at $0 cost, fully automated, growing toward monetization.

## 2. Hard rules (never break these)
1. **No organized religion.** No prayer, worship, clergy, places of worship, scripture, saints, religious holidays or symbols. Mythology and folklore told as stories are fine.
2. **Never write the word "bible".** The world reference is the **Fernwick Guide** (`world/guide.md`).
3. **Nothing frightening.** No villains, danger, injury, illness, death, arguments, deadlines, loud or sudden events.
4. **Everything original and copyright-safe.** No existing characters, books, films, songs, brands or real people. World tales only from public-domain or oral tradition, retold in our own words.
5. **Uploads go up private.** Khalid listens and publishes in YouTube Studio himself.

## 3. What makes a good Fernwick story
Khalid's notes (2026-10-08): a pleasant mood with nothing behind it is not enough.
- **Hook first.** Right after the intro, a small gentle question or mystery that makes a stranger want to keep listening (who leaves mittens on the ferry wheel every autumn?). Never open with the date or the weather. Answer it by the middle.
- **Context up front.** Who the character is, where we are, the season, and why tonight's small task matters to someone.
- **Real substance.** A little backstory (how this came to be, who it is for, how the teller knows). For world-tradition stories, a few accurate sentences about the craft, custom or tale and where it comes from.
- **Rich, exact description.** Every scene has a sound, a smell or taste, a texture, a temperature and precise sights. "Six cups: blue, white, white, green, white, and one with a chipped gold rim", not "some cups".
- **A wise teller.** Each night someone different (lighthouse keeper, old ferryman, grandmother by the stove, clockmender) tells the story to "you", with a few asides of their own.
- **Energy only goes down.** Sentences get shorter and softer; more pauses in the last third; the character settles to sleep.
- **Plain, human words.** No AI-sounding phrases (tapestry, nestled, embrace, a sense of...).

## 4. Shape of every episode
1. Intro: "Welcome to Fernwick Nights." + tonight's title and teller + one "get comfortable" line.
2. Hook (100 to 150 words), then context (100 to 150 words), then backstory woven in.
3. The story, 16 to 22 short paragraphs, 4 to 6 named chapters.
4. A shorter, slower second telling ("Once More, Slowly").
5. Outro from the teller, ending exactly "Good night." Then ambience plays alone.
Total about 1,750 to 2,150 words. The full spec, JSON fields and voice list are in `prompts/daily-story.md`.

## 5. Variety rules
- Read `world/story_log.csv` (last 14 rows) and recent `published/` files before choosing.
- No repeated teller within 7 days, no repeated region within 7 days, no same series twice in a row.
- Place + character combination not used in the last 14 days. No repeated premise, opening image or ending image.
- Lean on lesser-known stories, crafts and customs from around the world; Myths Retold Slowly about once a week.
- Use the real season of the day. Oct 17 to 31: about every other story may be cozy-spooky (friendly, harmless, all explained).
- Long tales become parts on consecutive days, each part ending calm, never a cliffhanger.

## 6. The daily routine
1. Around noon Eastern, Claude picks and writes the day's story as `queue/YYYY-MM-DD.json`.
2. `python scripts/qc.py` must pass (hook, length, sensory detail, banned and religion words, repetition).
3. Claude adds new places and details to the Fernwick Guide and commits to `main`.
4. GitHub Actions builds the voice, video, thumbnail and Short, uploads to YouTube as **private**, and logs it.
5. Khalid listens to the first minutes in YouTube Studio and sets it public or scheduled.
Build files are deleted after 1 to 2 days.

## 7. Where things live
| What | Where |
| --- | --- |
| This page | `INSTRUCTIONS.md` |
| Full daily writing spec | `prompts/daily-story.md` |
| Fernwick Guide (places, cast, tellers, seasons, series) | `world/guide.md` |
| Story log | `world/story_log.csv` |
| Quality checks | `scripts/qc.py` |
| Build and upload | `.github/workflows/build-episode.yml` |
| Logo and banner | `assets/brand/` |

## 8. Decision log
- 2026-10-07: Channel named Fernwick Nights. World Fernwick and the Fernwick Guide approved. Free voice. 15 to 20 minute videos. Pipeline in GitHub Actions. Daily story, Claude chooses. No organized religion; mythology allowed. Never say "bible". Cozy-spooky season Oct 17 to 31. Long stories split into parts.
- 2026-10-08: Every story needs a hook, context and rich description. A different wise teller each night, speaking to the listener. Concrete, exact sensory detail in every scene.
