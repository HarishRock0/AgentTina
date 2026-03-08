import os
import sys
import pickle
from pathlib import Path
import dotenv

dotenv.load_dotenv()

TOKEN_FILE = Path(__file__).parent / "gmail_token.pickle"
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def print_banner():
    print()
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║           AgentTina — Gmail Authorization                    ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()


def check_env():
    missing = [k for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET") if not os.getenv(k)]
    if missing:
        print("  ✗ Missing credentials:", ", ".join(missing))
        print("  Run  python setup.py  first to enter your Google OAuth2 credentials.")
        print()
        sys.exit(1)


def is_already_authorized() -> bool:
    if not TOKEN_FILE.exists():
        return False
    try:
        from google.auth.transport.requests import Request
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
        if creds and creds.valid:
            return True
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(creds, f)
            return True
    except Exception:
        pass
    return False


def authorize_gmail():
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_config = {
        "installed": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    print("  A browser window will open for you to log in with Google.")
    print("  Steps:")
    print("    1. Choose the Gmail account you want AgentTina to send from.")
    print("    2. If you see 'Google hasn't verified this app' → click 'Advanced'")
    print("       then 'Go to AgentTina (unsafe)' — this is normal for personal apps.")
    print("    3. Click  Allow  to grant permission to send emails.")
    print()
    input("  Press Enter to open the browser... ")
    print()

    flow = InstalledAppFlow.from_client_config(client_config, GMAIL_SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)

    print()
    print("  ✓ Authorization successful!")
    print(f"  Token saved to: {TOKEN_FILE}")
    print()


def revoke_and_delete():
    """Remove the saved token so the user can re-authorize with a different account."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        print("  ✓ Gmail authorization removed. Run auth.py again to re-authorize.")
    else:
        print("  No saved authorization found.")
    print()


def main():
    print_banner()
    check_env()

    if len(sys.argv) > 1 and sys.argv[1] == "--revoke":
        revoke_and_delete()
        return

    if is_already_authorized():
        print("  ✓ Gmail is already authorized and the token is valid.")
        print()
        print("  To switch accounts, run:")
        print("    python auth.py --revoke")
        print("  Then run  python auth.py  again to re-authorize.")
        print()
        return

    print("  Gmail is not yet authorized. Let's connect your account.\n")
    authorize_gmail()
    print("  You're all set! AgentTina can now send emails on your behalf.")
    print()


if __name__ == "__main__":
    main()
