"""Upload out/episode.mp4 (+ thumbnail) and out/short.mp4 to YouTube.

Secrets (repo Settings > Secrets > Actions): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
Skips quietly if they are missing. Uploads are PRIVATE by default: YouTube locks uploads from
unaudited API projects to private. Set YT_PRIVACY to public/unlisted only after the audit passes.
Usage: python scripts/youtube_upload.py queue/2026-10-08.json
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, load_episode  # noqa: E402

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
    tags = " ".join(h if h.startswith("#") else "#" + h for h in ep.get("hashtags", ["sleepstory", "bedtimestoriesforadults", "cozy"])[:3])
    teller = ep.get("teller", {})
    told = f"Told by {teller['name']}, {teller['who']}.\n\n" if teller.get("name") and teller.get("who") else ""
    return (
        f"{ep['description_summary']}\n\n{told}Tonight in Fernwick: {ep['description_setting']}\n\n"
        f"{chapter_lines()}"
        "About Fernwick: a quiet seaside town where nothing much happens. A new evening every night, "
        "told by a different Fernwick storyteller.\n\n"
        "Narration is an AI voice. Stories are original works written for Fernwick Nights, set in Fernwick.\n\n"
        f"{tags}"
    )


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

    creds = Credentials(None, refresh_token=refresh, token_uri="https://oauth2.googleapis.com/token",
                        client_id=cid, client_secret=secret,
                        scopes=["https://www.googleapis.com/auth/youtube.upload"])
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

    short = OUT / "short.mp4"
    if short.exists():
        stitle = (ep["story_title"][: 100 - 8] + " #Shorts")
        sid = insert(youtube, short, {
            "snippet": {"title": stitle, "description": f"Full episode: https://youtu.be/{vid}\n\n#Shorts #sleepstory",
                        "tags": ["sleep story", "Shorts"], "categoryId": CATEGORY},
            "status": status})
        print(f"Uploaded Short as {privacy}: https://youtu.be/{sid}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
