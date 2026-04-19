import os
import sys
import dotenv


dotenv.load_dotenv()

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def print_banner():
    print()
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║              Welcome to AgentTina — Setup Wizard             ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    print("  Configure your LLM provider and Gmail OAuth2 integration.")
    print("  Make sure credentials.json is present in this folder for Gmail.")
    print()


def save_to_env(values: dict):
    existing = {}
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            if "=" in line and not line.startswith("#"):
                k, _, _ = line.partition("=")
                existing[k.strip()] = line

    for k, v in values.items():
        if v is None:
            continue
        new_line = f"{k}={v}\n"
        if k in existing:
            lines = [new_line if l.startswith(k + "=") else l for l in lines]
        else:
            lines.append(new_line)

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    dotenv.load_dotenv(ENV_FILE, override=True)


def prompt_provider(default_provider: str) -> str:
    print("─" * 65)
    print("  LLM Provider")
    print("─" * 65)
    print(f"  Current/default provider: {default_provider}")
    print("  [1] Groq (cloud API)")
    print("  [2] Ollama (local model, no API calls)")
    print()

    while True:
        choice = input("  Select provider [1/2]: ").strip()
        if choice == "1":
            print()
            return "groq"
        if choice == "2":
            print()
            return "ollama"
        print("  ⚠  Please enter 1 or 2.")


def prompt_groq_api_key() -> str:
    print("─" * 65)
    print("  GroqCloud API Key")
    print("─" * 65)
    print("  How to get yours:")
    print("    1. Sign up / log in at https://console.groq.com")
    print("    2. Go to API Keys and create a key")
    print("    3. Paste it below")
    print()

    while True:
        value = input("  Paste your GroqCloud API key: ").strip()
        print()
        if not value:
            print("  ⚠  API key cannot be empty.")
            continue
        if " " in value or len(value) < 20:
            print("  ⚠  That does not look like a valid key. Try again.")
            continue
        return value


def prompt_ollama_settings(existing_model: str, existing_base_url: str) -> tuple[str, str]:
    print("─" * 65)
    print("  Ollama Local Settings")
    print("─" * 65)
    print("  Make sure Ollama is installed and running locally.")
    print("  Example: ollama serve")
    print()

    model = input(f"  Ollama model [{existing_model}]: ").strip() or existing_model
    base_url = input(f"  Ollama base URL [{existing_base_url}]: ").strip() or existing_base_url
    print()
    return model, base_url


def ensure_google_credentials_file() -> bool:
    cred_path = os.path.join(PROJECT_ROOT, "credentials.json")
    if os.path.exists(cred_path):
        print("  ✓ credentials.json found. Gmail sending can be enabled.")
        print()
        return True

    print("  ⚠  credentials.json is missing. Gmail sending will not work until you add it.")
    print("  Steps:")
    print("    1. Open https://console.cloud.google.com/")
    print("    2. Create/select a project")
    print("    3. Enable Gmail API")
    print("    4. Create OAuth 2.0 Desktop App credentials")
    print("    5. Download and place credentials.json in this folder")
    print()
    return False


def summarize_config():
    provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    print("  Active configuration:")
    print(f"    LLM_PROVIDER={provider}")
    if provider == "groq":
        api_set = "yes" if os.getenv("API") else "no"
        print(f"    API configured: {api_set}")
    else:
        print(f"    OLLAMA_MODEL={os.getenv('OLLAMA_MODEL', 'llama3.2:3b')}")
        print(f"    OLLAMA_BASE_URL={os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")
    print()


def run_setup(force_reset: bool = False) -> bool:
    print_banner()

    default_provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    if default_provider not in ("groq", "ollama"):
        default_provider = "groq"

    if not force_reset:
        summarize_config()

    provider = prompt_provider(default_provider)

    values = {"LLM_PROVIDER": provider}

    if provider == "groq":
        if force_reset or not os.getenv("API") or default_provider != "groq":
            values["API"] = prompt_groq_api_key()
    else:
        existing_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        existing_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model, base_url = prompt_ollama_settings(existing_model, existing_base_url)
        values["OLLAMA_MODEL"] = model
        values["OLLAMA_BASE_URL"] = base_url

    save_to_env(values)

    if provider == "groq" and not os.getenv("API"):
        print("  ✗ Missing API key for Groq provider.")
        print("  Re-run python setup.py and provide a valid key.")
        print()
        return False

    ensure_google_credentials_file()

    print("  ✓ Setup complete. Configuration saved to .env")
    print()
    print("  Next steps:")
    print("    1. If using Gmail tools, run: python auth.py")
    print("    2. Start server: python tina.py server")
    print()
    return True


if __name__ == "__main__":
    force_reset = "--reset" in sys.argv
    success = run_setup(force_reset=force_reset)
    if not success:
        sys.exit(1)
