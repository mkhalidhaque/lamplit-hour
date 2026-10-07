"""Run ONCE on your own computer to get the YT_REFRESH_TOKEN for The Lamplit Hour channel.

    pip install google-auth-oauthlib
    python scripts/get_refresh_token.py

It asks for the same Google OAuth client id and secret the trader repo uses, opens a browser, and
prints a refresh token. In the browser, pick the NEW channel (not the trader channel) when Google
asks which account or channel to use. Paste the printed token into the GitHub secret YT_REFRESH_TOKEN.
Never commit the token or the secret.
"""
import getpass

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    cid = input("YT_CLIENT_ID: ").strip()
    secret = getpass.getpass("YT_CLIENT_SECRET (hidden): ").strip()
    cfg = {"installed": {
        "client_id": cid, "client_secret": secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"]}}
    flow = InstalledAppFlow.from_client_config(cfg, SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    print("\nYT_REFRESH_TOKEN =", creds.refresh_token)


if __name__ == "__main__":
    main()
