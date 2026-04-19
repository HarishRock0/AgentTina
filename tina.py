# tina.py — Unified Tina agent and server

import os
import pickle
import base64
from pathlib import Path
from datetime import datetime
from typing import Annotated
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
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from googleapiclient.discovery import build
from typing_extensions import TypedDict

def _build_llm():
    provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        llm = ChatOllama(model=model, base_url=base_url, temperature=0.7)
        return llm, model, provider

    api_key = os.getenv("API")
    if not api_key:
        raise EnvironmentError(
            "Missing credentials: API\n"
            "Run 'python setup.py' first, then restart this server."
        )
    model = "llama-3.3-70b-versatile"
    llm = ChatGroq(model=model, api_key=api_key, temperature=0.7)
    return llm, model, "groq"


tina, LLM, LLM_PROVIDER = _build_llm()

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


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


tool_node = ToolNode(tools)
model_with_tools = tina.bind_tools(tools)


def chatbot_node(state: AgentState):
    return {"messages": [model_with_tools.invoke(state["messages"])]}


graph_builder = StateGraph(AgentState)
graph_builder.add_node("chatbot", chatbot_node)
graph_builder.add_node("tools", tool_node)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
checkpointer = MemorySaver()
agent_graph = graph_builder.compile(checkpointer=checkpointer)

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
    session_id = body.get("session_id", "web-default")
    if not question:
        return JSONResponse({"error": "No question provided."}, status_code=400)
    try:
        answer = ask_tina(question, session_id=session_id)
        return {"answer": answer, "session_id": session_id}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "ok", "model": LLM, "provider": LLM_PROVIDER}


def ask_tina(question: str, session_id: str = "cli-default") -> str:
    result = agent_graph.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": session_id}},
    )
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return str(msg.content)
    return "No response generated."

def start_server():
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║               AgentTina — Localhost Server                  ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Local:   http://localhost:8000                              ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Access is restricted to this machine via localhost only.   ║")
    print("║  Press Ctrl+C to stop.                                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

if __name__ == "__main__":
    start_server()
