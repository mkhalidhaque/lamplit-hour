# Daily story task (read fully, then do it)

You write one new sleep story for the YouTube channel The Lamplit Hour and publish it by committing a JSON file. Everything is original; nothing here is religious.

## Steps
1. Read world/guide.md and world/story_log.csv, and look at the last ~14 rows. Also skim the recent files in published/ so you do not repeat a premise, task, opening image or ending image.
2. Choose tonight's story yourself. Khalid's direction (2026-10-07): lean on lesser-known stories from around the world that English-speaking listeners are unlikely to know. Rotate regions (check the source_tradition column of the log and do not repeat a region within 7 days) and keep it copyright-safe (see rule 9). Fernwick stories can borrow a small motif, craft or custom from a tradition; Myths Retold Slowly retells a whole tale. Rotate series (do not use the same series twice in a row; use Myths Retold Slowly about once a week). Pick a place and a recurring character (or none) that were not used in the last 14 days together. Use the real season of the date you are running on, a matching weather and an ambience bed (rain, wind, ocean, harbor or stove).
3. Write the story as described in the rules below.
4. Save it as queue/YYYY-MM-DD.json for the date you are running on (UTC date is fine).
5. Run `python scripts/qc.py queue/YYYY-MM-DD.json`. If it fails, fix the story and run it again until it passes (up to 3 tries; if it still fails, do not commit; stop and explain).
6. Add any new places, people or details you invented to world/guide.md (short bullet under the right heading), and commit everything to the main branch with the message `Story YYYY-MM-DD: <title>`. Pushing the file in queue/ starts the video build and a private YouTube upload automatically. Do not change anything else.

## Rules
1. Entirely original telling. No existing characters, books, films, songs, brands or real people. Invented place names only. Exception: the Myths Retold Slowly series may retell public-domain myths and folklore (Greek, Norse, Celtic, and similar) in an original, quiet way, as stories and never as scripture or living-faith content.
2. Almost nothing happens. One small task or journey, done step by step. No villains, danger, injury, illness, death, arguments, deadlines, loud sounds, sudden events, or anything frightening, even mildly. No organized-religion content (no prayer, worship, clergy, places of worship, scripture, saints, religious holidays or symbols). Festivals stay secular.
3. Energy only goes down. Sentences get a little shorter and softer as the story goes on. The character settles to sleep at the end.
4. Concrete and specific: real textures, small sounds, warm light, plain objects. One vivid detail per paragraph, not five.
5. Write like a human storyteller: plain words, varied sentence openings, occasional gentle humor. Do not use: tapestry, symphony, embrace, testament, nestled, whisper of, a sense of, as if the world itself, little did, in the heart of, bustling, delve, journey of, magical.
6. Mostly third person; at most three short lines of dialogue. Address the listener as "you" only in the opening and settling.
7. Avoid words the checker blocks as alarming or religious even in passing (for example danger, dead*, gun*, attack, panic, scream, blood, crash, monster, knife, died, suddenly, holy, angel, pray*, church, saint, bible).
9. World stories, copyright-safe. Use only public-domain or oral-tradition folklore as inspiration (old tales, proverbs, traditional crafts and customs). Write an original retelling in the Fernwick voice; never follow the plot beats, wording or structure of one specific modern translation, anthology or retelling, since those can be copyrighted. Skip sacred or ceremonial stories of living cultures and anything from religious texts or practices; ordinary folk tales, animal tales and craft or weather lore are fine. Fill source_tradition (people/region) and source_note (one sentence: the tale or motif is traditional/public domain and the telling is original).
8. Mark pauses with [pause] (2 s) and [long pause] (4 s) on their own lines between paragraphs, more toward the end.

## Structure of the script (about 1,350 to 1,600 words in total)
A. Opening (about 90 words): exactly "Hello, and welcome back to Fernwick." then tonight's place, weather and the promise that nothing much will happen.
B. Settling (about 100 words): get comfortable, two slow breaths, "you don't need to stay awake for the ending."
C. The story (about 1,000 words in 14 to 18 short paragraphs).
D. A line `[[SECOND]]` on its own, then the second telling (about 200 to 250 words): the same story retold more simply and slowly, shorter sentences, ending a little earlier.
E. Final line exactly: "The lamps are low in Fernwick. Sleep well."

## JSON file keys (copy queue/2026-10-07.json for the exact shape; it is valid)
story_title, series, place (must match a place in the guide, so the right picture is used), character, season, ambience (one word: rain, wind, ocean, harbor or stove), summary (2 sentences for the log), source_tradition (e.g. "Sami, northern Scandinavia" or "none, original Fernwick"), source_note (one sentence on why it is copyright-safe), title_options (3 titles in the form "[Search phrase]: [Story title] | [Ambience]", each under 100 characters; rotate the search phrases: Cozy Sleep Story for Grown-Ups, Bedtime Story for Adults, Calm Sleep Story, Boring Sleep Story, Story to Fall Asleep To), thumbnail_text (2 to 4 words), description_summary (1 sentence), description_setting (2 to 3 sentences), hashtags (3), tags (10), image_brief (one dark, warm scene, no faces, no religious symbols), short_excerpt (70 to 110 consecutive words copied from the story, the most evocative, no pause markers), new_world_facts (list), script.
