# lamplit-hour

Fernwick Nights: sleep stories set in the invented seaside town of Fernwick.
Approved story JSON in `queue/` -> GitHub Action -> voice, ambience mix, video, thumbnail, Short -> YouTube (private) -> logged in `world/story_log.csv`.

## Daily flow
1. A scheduled Claude task writes `queue/YYYY-MM-DD.json` (see the daily prompt) and opens a pull request.
2. `check-story.yml` runs `scripts/qc.py` on the PR. Read the story; edit lines in your own words.
3. Merge the PR = approval. `build-episode.yml` builds the ~15-20 minute video and uploads it as **private**.
4. Open YouTube Studio, listen to the first minutes, then set it to public or scheduled.

## One-time setup
- Create a **private** repo named `lamplit-hour`, copy these files in.
- Settings > Secrets and variables > Actions: add `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` (same steps as the trader repo; a channel for Fernwick Nights needs its own refresh token).
- Optional repo variable `YT_PRIVACY` = `public` or `unlisted`, only after Google's API audit is approved. Until then YouTube forces private.
- Settings > Actions > General > Workflow permissions: Read and write (the bot commits the log).
- Add 10-30 illustrations to `assets/images/` named after places (e.g. `harbor-lane.jpg`) and, optionally, recorded loops to `assets/ambience/` named `rain`, `wind`, `ocean`, `harbor`, `stove`. Without them the build uses a dark gradient and synthesized noise, so it still works on day one.

## Limits
- Artifacts are kept 2 days (free plan: 500 MB total). Videos are not stored in git.
- Free private-repo minutes: 2,000 a month. Watch the first runs to see how long an episode takes.
- Voice: `edge-tts` (free, unofficial). Change the voice with the `VOICE` environment variable in `build-episode.yml`.

## Story file fields
story_title, series, place, character, season, ambience, summary, hook, context, title_options[3], script (with [pause], [long pause] and a [[SECOND]] marker before the slower second telling), thumbnail_text, description_summary, description_setting, tags[10], short_excerpt, image_brief, new_world_facts.
