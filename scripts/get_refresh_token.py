"""Run ONCE on your own computer to get the YT_REFRESH_TOKEN for Fernwick Nights channel.

    python -m pip install google-auth-oauthlib
    python get_refresh_token.py

It reads the client id and secret from the newest client_secret*.json file in your Downloads
folder (the file Google lets you download when you create an OAuth "Desktop app" client), so you
don't have to copy and paste them. You can also pass the file path: python get_refresh_token.py FILE.json
If no file is found it asks you to type them. A browser opens: pick the NEW channel when Google asks.
It prints a refresh token. Paste it into the GitHub secret YT_REFRESH_TOKEN. Never commit it.
"""
import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def find_json():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    files = sorted((Path.home() / "Downloads").glob("client_secret*.json"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def main():
    path = find_json()
    if path and path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        cfg = data.get("installed") or data.get("web")
        print(f"Using {path.name}; client id ends ...{cfg['client_id'][-30:]}")
        if "installed" not in data:
            print("WARNING: this is not a Desktop app client; it may not work.")
    else:
        print("No client_secret*.json found in Downloads. Type the values instead.")
        cid = input("Client ID: ").strip()
        secret = input("Client secret: ").strip()  # shown on screen so you can check it
        cfg = {"client_id": cid, "client_secret": secret,
               "auth_uri": "https://accounts.google.com/o/oauth2/auth",
               "token_uri": "https://oauth2.googleapis.com/token",
               "redirect_uris": ["http://localhost"]}
        print(f"Secret length {len(secret)} (Google secrets are usually 35 and start GOCSPX-)")
    flow = InstalledAppFlow.from_client_config({"installed": cfg}, SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    print("\nYT_CLIENT_ID     =", cfg["client_id"])
    print("YT_CLIENT_SECRET = (the secret in your downloaded file)")
    print("YT_REFRESH_TOKEN =", creds.refresh_token)


if __name__ == "__main__":
    main()
