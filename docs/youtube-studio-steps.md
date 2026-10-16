# YouTube Studio steps for Khalid

The pipeline does everything it can through the YouTube API. These are the few things only you can do, in the
order that helps most. Written 2026-10-16 with the growth changes (curiosity titles, bold thumbnails, cold open,
30-second Shorts, series playlists, "tomorrow" teasers, pinned comments, warmer voice).

## 1. Once: give the pipeline a little more permission (5 minutes)

Today the upload key can only upload videos. With one more permission ("youtube.force-ssl") the build can also
add each video to its playlists, post the comment for you to pin, add captions and set the thumbnail.

1. On your computer, in the repo folder: `python -m pip install google-auth-oauthlib`, then
   `python scripts/get_refresh_token.py`.
2. A browser opens. Pick the **Fernwick Nights** channel and allow both permissions.
3. Copy the token it prints into GitHub: repo **Settings > Secrets and variables > Actions >
   YT_REFRESH_TOKEN > Update**.
4. In Google Cloud Console, **APIs & Services > OAuth consent screen**: if "Publishing status" says
   **Testing**, click **Publish app**. In Testing mode Google expires the token every 7 days and uploads stop.
   (Google shows an "unverified app" warning when you sign in; that is fine for your own channel.)

Until you do this, everything else still works; the run summary simply tells you to add playlists by hand.

## 2. Every day: the 5-minute check

After each build, open the GitHub run (**Actions > Build episode > the newest run**). Its summary lists the
links and the exact text to paste. Then in YouTube Studio:

1. **Listen** to the first minute of the episode (the cold open and the welcome). Set it **Public**, or
   **Schedule** it for about 8 pm US Eastern, when people go to bed.
2. **Pin the comment.** If the build posted it, open the video's **Comments**, click **⋮** next to it, then
   **Pin**. If not (private videos cannot take comments), post the text from the run summary once the video is
   public, then pin it. It says tomorrow's story and asks viewers which myth they want next.
3. **The Short:** set it **Public** at the same time, and under **Related video** pick tonight's full episode,
   so viewers can tap through from the Short.
4. **Playlists:** check the video is in "Greek Myths for Sleep" and its series (the build adds both once step
   1 is done).

## 3. Once: set up the channel for growth (20 minutes)

- **Playlists.** The build creates them as needed. To have them now, create these (public) in **Content >
  Playlists > New playlist**: Greek Myths for Sleep, Myths of the Sea, Myths of the Night Sky, Myths of Sleep and
  Dreams, Myths of Love and Loyalty, Myths of Changing Shape, Myths of Clever Mortals, Myths of Gifts and Wonders.
  The exact names matter; the build finds them by name. Add the earlier myth episodes: The Moon and the Slow
  Clock (Selene) to Night Sky, The Bird That Stilled the Sea (Alcyone) to Sea, The Jug That Would Not Empty
  (Philemon and Baucis) to Love and Loyalty, and all three to Greek Myths for Sleep.
- **Home page.** **Customization > Layout**: add a "Single playlist" section for Greek Myths for Sleep at the
  top, then "Short videos", then one section per series as they fill up.
- **End screen template.** On one video, **Editor > End screen**: add "Best for viewer" video, the "Greek
  Myths for Sleep" playlist and a Subscribe button, timed to the last 20 seconds. Then use **Import from video**
  on every new upload (end screens cannot be set through the API). Optional: for sleep content most people
  are asleep at the end, so this mainly helps people who finish awake.
- **Upload defaults.** **Settings > Upload defaults**: category Entertainment, language English, comments
  "Hold potentially inappropriate comments for review". The build already sets title, description and tags.
- **Test & compare thumbnails.** When a video has been public for a day, **Editor > Thumbnail > Test &
  compare** lets YouTube try up to 3 thumbnails and keep the one people click most. Worth doing on any episode
  that starts slower than usual.

## 4. Monetization

- **YouTube Partner Program** needs 1,000 subscribers plus either 4,000 public watch hours in the last 12 months
  or 10 million Shorts views in 90 days. Long sleep videos earn watch hours fast once people find them, which is
  why the titles, thumbnails and Shorts matter most right now. Check progress in **Earn**.
- **Stay clear of "inauthentic content".** YouTube does not pay for mass-produced, repetitive videos. Each episode
  here is a different myth, teller, picture and script, which is the right side of that line; keep it that way
  (never re-upload near-copies, never reuse one script with small changes).
- **AI disclosure.** The upload form asks about "altered or synthetic content". YouTube's examples are about
  realistic-looking people or events; a clearly fictional myth narrated by an AI voice is generally not that,
  and the description already says "Narration is an AI voice." If YouTube's wording changes, follow it.

## 5. The YouTube API audit (so uploads can go public by themselves)

YouTube locks every upload from an unaudited API project to **private**. That is why you publish by hand today.
After the audit passes, the build can upload as public or scheduled.

1. In Google Cloud Console, open the project that holds the OAuth client (the one from step 1).
2. Make sure the **OAuth consent screen** has an app name (Fernwick Nights), your email, and a privacy policy URL.
   A simple page is enough, e.g. a short public Google Doc or GitHub page saying the app only uploads videos to
   your own channel and stores no user data.
3. Fill in the **YouTube API Services - Audit and Quota Extension Form**:
   https://support.google.com/youtube/contact/yt_api_form
   - Choose the audit / "compliance audit" option for an existing project.
   - Describe the use plainly: "An internal tool that uploads one video a day, with its thumbnail, captions and
     playlist entry, to my own channel (Fernwick Nights). No other users, no viewing or storing other people's
     data."
   - API client: the project number and the OAuth client id (both in the Console).
   - Link the channel and the repository if asked (the repo is public:
     https://github.com/mkhalidhaque/lamplit-hour).
4. Google replies by email, usually within a few weeks, and sometimes asks for screenshots of how the tool works.
   The Actions run log and this repo are what to show.
5. When it passes, tell Claude. The change is one setting: repo **Settings > Secrets and variables > Actions >
   Variables > YT_PRIVACY** = `public` (or keep `private` and Claude can add scheduled publishing).

Until then, the daily check in section 2 stays the way to go public.
