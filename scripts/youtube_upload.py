"""Upload out/episode.mp4 (+ thumbnail) and out/short.mp4 to YouTube.

Secrets (repo Settings > Secrets > Actions): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
Skips quietly if they are missing. Uploads are PRIVATE by default: YouTube locks uploads from
unaudited API projects to private. Set YT_PRIVACY to public/unlisted only after the audit passes.
Growth (Khalid, 2026-10-16): the curiosity title (title_options[0]), "Series" and "Tomorrow night" lines in the
description, the video added to its playlists (world/series.json; created if missing), and a comment with
tomorrow's story posted for Khalid to pin. Playlists and the comment need a refresh token made with the
youtube.force-ssl scope (get_refresh_token.py asks for it); with an upload-only token they are skipped with a
note. The comment text and a short to-do list are always written to the Actions run summary.
Usage: python scripts/youtube_upload.py queue/2026-10-08.json
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, load_episode, load_series, short_title  # noqa: E402

CATEGORY = "24"  # Entertainment


def stamp(seconds):
    s = int(seconds)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def chapter_lines():
    """'0:00 Welcome' lines from out/chapters.json (YouTube needs 3+ chapters, 10 s apart, starting at 0:00)."""
    f = OUT / "chapters.json"
    if not f.exists():
        return ""
    ch = json.loads(f.read_text())
    ok = [c for i, c in enumerate(ch) if i == 0 or c["start"] - ch[i - 1]["start"] >= 10]
    if len(ok) < 3 or ok[0]["start"] != 0:
        return ""
    return "Chapters\n" + "\n".join(f"{stamp(c['start'])} {c['title']}" for c in ok) + "\n\n"


def description(ep):
    tags = " ".join(h if h.startswith("#") else "#" + h for h in ep.get("hashtags", ["greekmythology", "sleepstory", "bedtimestoriesforadults"])[:3])
    teller = ep.get("teller", {})
    told = f"Told by {teller['name']}, {teller['who']}.\n\n" if teller.get("name") and teller.get("who") else ""
    sources = "Ancient sources: " + "; ".join(ep["myth_sources"]) + "\n\n" if ep.get("myth_sources") else ""
    series = f"Series: {ep['series']}\n" if ep.get("series") else ""
    nxt = (ep.get("next_story") or {}).get("teaser")
    tomorrow = f"Tomorrow night: {nxt}\n" if nxt else ""
    return (
        f"{ep['description_summary']}\n\n{told}{ep['description_setting']}\n\n"
        f"{series}{tomorrow}{chr(10) if series or tomorrow else ''}"
        f"{chapter_lines()}"
        f"{sources}"
        "Fernwick Nights: a story from the Greek myths every night, told slowly and calmly "
        "by a different storyteller, for falling asleep.\n\n"
        "Narration is an AI voice. Each retelling is an original work written for Fernwick Nights from the "
        "ancient, public-domain sources.\n\n"
        f"{tags}"
    )


def pinned_comment(ep):
    """The comment to pin under the episode: tomorrow's story and a question that invites replies."""
    if ep.get("pinned_comment"):
        return ep["pinned_comment"].strip()
    nxt = (ep.get("next_story") or {}).get("teaser")
    first = f"Tomorrow night: {nxt}\n\n" if nxt else ""
    return first + "Which Greek myth would you like to fall asleep to next? Leave a name below and it may become a story."


def playlist_id(youtube, title, description, known=""):
    """The channel's playlist with this exact title; created (public) if there is none."""
    if known:
        return known
    req = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
    while req is not None:
        resp = req.execute()
        for it in resp.get("items", []):
            if it["snippet"]["title"] == title:
                return it["id"]
        req = youtube.playlists().list_next(req, resp)
    made = youtube.playlists().insert(part="snippet,status", body={
        "snippet": {"title": title, "description": description}, "status": {"privacyStatus": "public"}}).execute()
    print(f"Created playlist: {title}")
    return made["id"]


def add_to_playlists(youtube, vid, ep):
    """Add the episode to the umbrella playlist and its series playlist (world/series.json). Returns titles."""
    cfg = load_series()
    wanted = [cfg["umbrella"]]
    s = cfg["series"].get(ep.get("series", ""))
    if s:
        wanted.append({"title": ep["series"], **s})
    done = []
    for pl in wanted:
        pid = playlist_id(youtube, pl["title"], pl.get("description", ""), pl.get("playlist_id", ""))
        youtube.playlistItems().insert(part="snippet", body={
            "snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
        done.append(pl["title"])
    return done


def summary(lines):
    """Write the to-do list for Khalid to the GitHub Actions run summary (and the log)."""
    text = "\n".join(lines) + "\n"
    print(text)
    f = os.environ.get("GITHUB_STEP_SUMMARY")
    if f:
        with open(f, "a", encoding="utf-8") as out:
            out.write(text)


def insert(youtube, media, body):
    from googleapiclient.http import MediaFileUpload
    req = youtube.videos().insert(part="snippet,status", body=body,
                                  media_body=MediaFileUpload(str(media), mimetype="video/mp4",
                                                             resumable=True, chunksize=-1))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp["id"]


def main(ep_path):
    cid = os.environ.get("YT_CLIENT_ID", "").strip()
    secret = os.environ.get("YT_CLIENT_SECRET", "").strip()
    refresh = os.environ.get("YT_REFRESH_TOKEN", "").strip()
    if not (cid and secret and refresh):
        print("YouTube secrets not set - skipping upload.")
        return 0
    ep = load_episode(ep_path)
    privacy = os.environ.get("YT_PRIVACY", "private").strip() or "private"

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    # no scopes here: the access token gets every scope the refresh token was granted (upload, and captions if allowed)
    creds = Credentials(None, refresh_token=refresh, token_uri="https://oauth2.googleapis.com/token",
                        client_id=cid, client_secret=secret)
    youtube = build("youtube", "v3", credentials=creds)
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}

    title = ep["title_options"][0][:100]
    vid = insert(youtube, OUT / "episode.mp4", {
        "snippet": {"title": title, "description": description(ep), "tags": ep["tags"][:12], "categoryId": CATEGORY},
        "status": status})
    print(f"Uploaded episode as {privacy}: https://youtu.be/{vid}")
    thumb = OUT / "thumb.jpg"
    if thumb.exists():
        try:
            youtube.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb))).execute()
        except Exception as e:  # needs a verified channel and the youtube scope; not fatal
            print(f"thumbnail not set ({type(e).__name__}); set it in YouTube Studio")

    playlists = []
    try:
        playlists = add_to_playlists(youtube, vid, ep)
        print("Added to playlists: " + ", ".join(playlists))
    except Exception as e:  # needs the youtube.force-ssl scope; not fatal
        print(f"playlists not set ({type(e).__name__}); re-run get_refresh_token.py to allow it")
    comment = pinned_comment(ep)
    (OUT / "pinned_comment.txt").write_text(comment + "\n", encoding="utf-8")
    posted = False
    try:
        youtube.commentThreads().insert(part="snippet", body={"snippet": {
            "videoId": vid, "topLevelComment": {"snippet": {"textOriginal": comment}}}}).execute()
        posted = True
        print("Comment posted (pin it in YouTube Studio)")
    except Exception as e:  # private videos and upload-only tokens cannot take comments; Khalid pastes it
        print(f"comment not posted ({type(e).__name__}); paste it from the run summary")

    sid = None
    short = OUT / "short.mp4"
    if short.exists():
        hook = short_title(ep)
        fig = ep.get("myth_figure", "")
        stitle = f"{hook} | {fig}" if fig and fig.lower() not in hook.lower() else hook
        stitle = stitle[: 100 - 8] + " #Shorts"
        nxt = (ep.get("next_story") or {}).get("teaser")
        sdesc = f"The full story: https://youtu.be/{vid}\n\n" + (f"Tomorrow night: {nxt}\n\n" if nxt else "")
        sid = insert(youtube, short, {
            "snippet": {"title": stitle, "description": sdesc + "#Shorts #greekmythology #sleepstory",
                        "tags": ["sleep story", "greek mythology", "Shorts"] + ([fig] if fig else []),
                        "categoryId": CATEGORY},
            "status": status})
        print(f"Uploaded Short as {privacy}: https://youtu.be/{sid}")

    todo = [f"## To do in YouTube Studio: {title}", "",
            f"1. Listen to the start of https://studio.youtube.com/video/{vid}/edit and set it Public or Scheduled.",
            "2. Pin this comment (" + ("already posted: open Comments, then ⋮ > Pin" if posted
                                         else "post it after the video is public, then ⋮ > Pin") + "):", "",
            "```", comment, "```", ""]
    if not playlists:
        todo.append(f"3. Add the video to the playlists \"{load_series()['umbrella']['title']}\" and \"{ep.get('series', '')}\".")
    if sid:
        todo.append(f"{4 if not playlists else 3}. Short https://studio.youtube.com/video/{sid}/edit: set Public, and set "
                    "its Related video to the full episode.")
    summary(todo)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
