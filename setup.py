import os
import sys
import dotenv

dotenv.load_dotenv()

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
def print_banner():
    print()
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║              Welcome to AgentTina — Setup Wizard             ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()


def check_missing():
    required = ["API", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"]
    return [k for k in required if not os.getenv(k)]


def prompt_groq() -> str | None:
    print("─" * 65)
    print("  [1] GroqCloud API Key")
    print("─" * 65)
    print("  How to get yours:")
    print("    1. Sign up / log in at  https://console.groq.com")
    print("    2. Go to  API Keys  →  Create API Key")
    print("    3. Copy the key and paste it below.")
    print()
    value = input("  Paste your GroqCloud API key: ").strip()
    print()
    return value or None


def prompt_google() -> dict:
    print("─" * 65)
    print("  [2] Google Cloud Console — OAuth2 Credentials")
    print("─" * 65)
    print("  ⚠  Each user MUST create their OWN Google Cloud project.")
    print("     Never share or commit your Client ID / Secret.\n")
    print("  Steps:")
    print("    1. Go to  https://console.cloud.google.com/")
    print("    2. Create a NEW project  (e.g. 'AgentTina-yourname')")
    print("    3. Enable these APIs in  APIs & Services → Library:")
    print("         • Gmail API              (used by send_email tool)")
    print("         • Google Calendar API    (used by manage_calendar tool)")
    print("    4. Go to  APIs & Services → Credentials")
    print("    5. Click  Create Credentials → OAuth 2.0 Client ID")
    print("    6. Choose  Application type: Desktop App  → Create")
    print("    7. Copy the Client ID and Client Secret shown.")
    print()
    client_id     = input("  Paste your Google Client ID:     ").strip()
    client_secret = input("  Paste your Google Client Secret: ").strip()
    print()
    return {
        "GOOGLE_CLIENT_ID": client_id or None,
        "GOOGLE_CLIENT_SECRET": client_secret or None,
    }


def save_to_env(values: dict):
    """Write key=value pairs to .env, updating existing keys or appending new ones."""
    # Read existing lines
    existing = {}
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()
        for line in lines:
            if "=" in line and not line.startswith("#"):
                k, _, _ = line.partition("=")
                existing[k.strip()] = line

    # Update or append
    for k, v in values.items():
        if v is None:
            continue
        new_line = f"{k}={v}\n"
        if k in existing:
            lines = [new_line if (l.startswith(k + "=")) else l for l in lines]
        else:
            lines.append(new_line)

    with open(ENV_FILE, "w") as f:
        f.writelines(lines)

    dotenv.load_dotenv(ENV_FILE, override=True)


def reset_keys(keys: list):
    """Clear specified keys from .env and re-prompt for them."""
    if not os.path.exists(ENV_FILE):
        print("  ⚠  No .env file found. Nothing to reset.")
        print()
        return

    with open(ENV_FILE, "r") as f:
        lines = f.readlines()

    # Remove the selected keys
    lines = [l for l in lines if not any(l.startswith(k + "=") for k in keys)]

    with open(ENV_FILE, "w") as f:
        f.writelines(lines)

    # Clear from current environment so check_missing picks them up
    for k in keys:
        os.environ.pop(k, None)

    print()
    print("  ✓ Key(s) cleared:", ", ".join(keys))
    print()


def reset_menu():
    """Interactive menu to choose which keys to reset."""
    print("  Which credentials do you want to reset?\n")
    print("    [1] GroqCloud API Key  (API)")
    print("    [2] Google OAuth2 credentials  (GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET)")
    print("    [3] All of the above")
    print("    [0] Cancel")
    print()
    choice = input("  Enter choice: ").strip()
    print()

    if choice == "1":
        reset_keys(["API"])
        return ["API"]
    elif choice == "2":
        reset_keys(["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"])
        return ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"]
    elif choice == "3":
        reset_keys(["API", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"])
        return ["API", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"]
    else:
        print("  Cancelled. No changes made.")
        print()
        return []


def collect_and_save(missing: list):
    collected = {}

    if "API" in missing:
        val = prompt_groq()
        if val:
            collected["API"] = val

    if "GOOGLE_CLIENT_ID" in missing or "GOOGLE_CLIENT_SECRET" in missing:
        google_vals = prompt_google()
        collected.update({k: v for k, v in google_vals.items() if v})

    if collected:
        save_to_env(collected)
        print("  ✓ Credentials saved to .env\n")
    else:
        print("  ⚠  No values entered.")
        print(f"     You can manually edit: {ENV_FILE}\n")


def run_setup(force_reset: bool = False):
    print_banner()
    missing = check_missing()

    if not missing and not force_reset:
        print("  ✓ All credentials found.")
        print(f"    (stored in {ENV_FILE})\n")
        print("  Options:")
        print("    [1] Reset / update a specific key")
        print("    [2] Exit")
        print()
        choice = input("  Enter choice: ").strip()
        print()
        if choice == "1":
            reset_menu()
            missing = check_missing()
            if missing:
                collect_and_save(missing)
        else:
            return True
    elif force_reset:
        reset_menu()
        missing = check_missing()
        if missing:
            collect_and_save(missing)
    else:
        print("  SETUP REQUIRED — the following credentials are missing:\n")
        for k in missing:
            print(f"    ✗  {k}")
        print()
        collect_and_save(missing)

    still_missing = check_missing()
    if still_missing:
        print("  ⚠  Some credentials are still missing:")
        for k in still_missing:
            print(f"     ✗  {k}")
        print()
        print("  Re-run  python setup.py  once you have them.")
        print()
        return False

    print("  ✓ All credentials set! You're ready to use AgentTina.")
    print()
    return True


if __name__ == "__main__":
    force_reset = "--reset" in sys.argv
    success = run_setup(force_reset=force_reset)
    if not success:
        sys.exit(1)
