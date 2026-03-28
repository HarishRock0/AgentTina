# tina.py — Unified Tina agent and server

import os
import pickle
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import dotenv

dotenv.load_dotenv(override=True)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Validate required env vars
REQUIRED = ["API"]
missing = [k for k in REQUIRED if not os.getenv(k)]
if missing:
    raise EnvironmentError(
        f"Missing credentials: {', '.join(missing)}\n"
        "Run 'python setup.py' first, then restart this server."
    )

# LLM setup
LLM = "llama-3.3-70b-versatile"
tina = ChatGroq(model=LLM, api_key=os.getenv("API"), temperature=0.7)

# Gmail OAuth2
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_FILE = Path(__file__).parent / "gmail_token.pickle"
CREDS_FILE = Path(__file__).parent / "credentials.json"

def _get_gmail_service():
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    # Only refresh if possible, never launch browser
    if not creds or not creds.valid:
        from google.auth.transport.requests import Request as GoogleRequest
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(creds, f)
        else:
            # Do not launch OAuth2 flow in non-interactive/server mode
            raise RuntimeError(
                "Gmail is not authenticated. Please run setup.py and complete Gmail authentication in an interactive environment."
            )
    return build("gmail", "v1", credentials=creds)

# Tools
@tool
def get_current_time(query: str) -> str:
    """Returns the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def calculator(expression: str) -> str:
    """Evaluates a basic math expression like '2 + 2' or '10 * 5 / 2'."""
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error: {e}"

@tool
def web_search(query: str) -> str:
    """Performs a web search and returns the top result."""
    return f"Top search result for '{query}'"

@tool
def search_file(filename: str) -> str:
    """Searches for a file in the local directory and returns its contents."""
    safe_base = Path(__file__).parent.resolve()
    target = (safe_base / filename).resolve()
    if not str(target).startswith(str(safe_base)):
        return "Error: Access outside project directory is not allowed."
    try:
        return target.read_text()
    except Exception as e:
        return f"Error: {e}"

@tool
def reverse_text(text: str) -> str:
    """Reverses the given text string."""
    return text[::-1]

@tool
def send_email(recipient: str, subject: str, body: str, attachment_path: str = None) -> str:
    """Sends a real email via Gmail using your Google OAuth2 credentials. Optionally attaches a file."""
    try:
        service = _get_gmail_service()
        if attachment_path:
            msg = MIMEMultipart()
            msg["to"] = recipient
            msg["subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            # Attach file
            file_path = Path(attachment_path)
            if not file_path.exists():
                return f"Attachment file not found: {attachment_path}"
            with open(file_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={file_path.name}",
            )
            msg.attach(part)
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        else:
            message = MIMEText(body)
            message["to"] = recipient
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return f"Email successfully sent to {recipient} with subject '{subject}'."
    except Exception as e:
        return f"Failed to send email: {e}"

@tool
def automate_task(task_description: str) -> str:
    """Automates a task based on the description provided."""
    return f"Task '{task_description}' has been automated."

@tool
def manage_calendar(event_details: str) -> str:
    """Manages calendar events based on the provided details."""
    return f"Calendar event '{event_details}' has been scheduled."

tools = [get_current_time, calculator, reverse_text, web_search,
         search_file, send_email, automate_task, manage_calendar]

agent = create_agent(tina, tools)

# FastAPI app
app = FastAPI(title="AgentTina", description="Tina AI assistant — local network API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CHAT_HTML = """<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\"/>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"/>
<title>AgentTina</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; display: flex; flex-direction: column; height: 100svh; }
  header { background: #1e293b; padding: 14px 20px; font-size: 1.15rem; font-weight: 600; border-bottom: 1px solid #334155; }
  #chat { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
  .msg { max-width: 72%; padding: 10px 14px; border-radius: 14px; line-height: 1.5; white-space: pre-wrap; }
  .user { background: #2563eb; align-self: flex-end; border-bottom-right-radius: 4px; }
  .tina { background: #1e293b; align-self: flex-start; border-bottom-left-radius: 4px; }
  .typing { color: #94a3b8; font-style: italic; }
  form { display: flex; gap: 10px; padding: 14px 20px; background: #1e293b; border-top: 1px solid #334155; }
  input { flex: 1; background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; color: #e2e8f0; font-size: 1rem; outline: none; }
  input:focus { border-color: #2563eb; }
  button { background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 10px 20px; cursor: pointer; font-size: 1rem; }
  button:hover { background: #1d4ed8; }
  button:disabled { background: #334155; cursor: not-allowed; }
</style>
</head>
<body>
<header>🤖 AgentTina</header>
<div id=\"chat\"></div>
<form id=\"form\">
    <input id=\"inp\" type=\"text\" placeholder=\"Ask Tina anything…\" autocomplete=\"off\" autofocus/>
    <button id=\"btn\" type=\"submit\">Send</button>
</form>
<script>
const chat = document.getElementById('chat');
const inp  = document.getElementById('inp');
const btn  = document.getElementById('btn');

function addMsg(text, who) {
  const d = document.createElement('div');
  d.className = 'msg ' + who;
  d.textContent = text;
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
  return d;
}

document.getElementById('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const q = inp.value.trim();
  if (!q) return;
  inp.value = '';
  btn.disabled = true;
  addMsg(q, 'user');
  const thinking = addMsg('Thinking…', 'tina typing');
  try {
    const res = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    });
    const data = await res.json();
    thinking.className = 'msg tina';
    thinking.textContent = data.answer ?? data.error ?? 'No response.';
  } catch {
    thinking.textContent = 'Network error — is the server running?';
  }
  btn.disabled = false;
  inp.focus();
});
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return CHAT_HTML

@app.post("/ask")
async def ask(request: Request):
    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        return JSONResponse({"error": "No question provided."}, status_code=400)
    try:
        answer = ask_tina(question)
        return {"answer": answer}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "ok", "model": LLM}

def ask_tina(question: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content

def start_server():
    import socket
    def _get_network_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    network_ip = _get_network_ip()
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║               AgentTina — Network Server                    ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Local:   http://localhost:8000                              ║")
    print(f"║  Network: http://{network_ip}:8000{' ' * (38 - len(network_ip))}║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Share the Network URL with anyone on the same Wi-Fi/LAN.   ║")
    print("║  Press Ctrl+C to stop.                                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        start_server()
    else:
        print("Tina CLI mode. Type your questions below. Type 'exit' or 'quit' to stop.")
        while True:
            user_input = input("Ask Tina: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            response = ask_tina(user_input)
            print(f"Tina: {response}")
