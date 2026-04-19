# AgentTina

AgentTina is an AI-powered assistant with Gmail integration, file search, and a web UI, built with FastAPI, LangChain, and LangGraph. It supports running locally or in Docker.

## Features
- LLM-powered chat with provider switching (Groq cloud API or local Ollama)
- Gmail OAuth2 email sending (with attachments)
- File search in project directory
- Web UI (FastAPI + HTML/JS)
- CLI and server modes
- Docker support

## Quick Start (Local)
1. Clone the repo and enter the directory.
2. Install Python 3.10+ and pip.
3. Install dependencies:
  ```sh
  pip install -r requirements.txt
  ```
4. Run setup:
  ```sh
  python setup.py
  ```
5. Start the server:
  ```sh
  python tina.py server
  ```
6. Open [http://localhost:8000](http://localhost:8000) in your browser.

## Quick Start (Docker)
1. Build the image:
  ```sh
  docker build -t agentina .
  ```
2. Run the container:
  ```sh
  docker run -p 8000:8000 agentina python tina.py server
  ```
3. Open [http://localhost:8000](http://localhost:8000) in your browser.

## Environment & Credentials
- Place your `credentials.json` (Google OAuth2) in the project root.
- Run `python setup.py` to set up Gmail and LLM API keys.
- Setup now lets you choose your LLM provider:
  - `groq` (requires `API` key)
  - `ollama` (local model via `OLLAMA_MODEL` and `OLLAMA_BASE_URL`)
- Tokens (`token.json`, `gmail_token.pickle`) are generated after authentication.

## Development
- Main code: `tina.py`
- Runtime orchestration: LangGraph state graph with tool-routing and checkpointed sessions.
- Web UI: served at `/` (HTML/JS in Python string)
- API: `/ask` (POST, accepts optional `session_id`), `/health` (GET)

## License
MIT

AgentTina is an open-source AI agent built with [LangChain](https://www.langchain.com/) and [LangGraph](https://www.langgraph.com/), with support for both [Groq](https://groq.com/) and local [Ollama](https://ollama.com/) models.

## License

This project is open-source and freely available for anyone to use, modify, and distribute.

## Features

- Conversational AI powered by Groq LLM
- ReAct agent with built-in tools:
  - **get_current_time** — Returns the current date and time
  - **calculator** — Evaluates math expressions
  - **reverse_text** — Reverses a string
  - **web_search** — Performs a web search (placeholder)
  - **search_file** — Reads a local file by name
  - **send_email** — Sends an email via Gmail using OAuth2
  - **manage_calendar** — Creates and manages Google Calendar events
  - **automate_task** — Automates general tasks described in natural language

## Getting Started

### Prerequisites

Install all required Python packages:

```
pip install langchain-groq langchain-ollama langgraph langchain-core python-dotenv \
            google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Setup

#### 1. Run the Setup Wizard

Run `setup.py` to enter your API credentials interactively. It will save them to a `.env` file automatically:

```
python setup.py
```

You will be prompted for:
- **GroqCloud API Key** — Get one at [console.groq.com](https://console.groq.com)
- **Google Client ID & Secret** — Required for Gmail and Google Calendar tools

#### 2. Create a Google Cloud Project (for Gmail & Calendar)

> Each user must create their **own** Google Cloud project. Never share or commit your credentials.

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create a new project (e.g. `AgentTina-yourname`)
3. Enable the following APIs under **APIs & Services → Library**:
   - **Gmail API** (used by `send_email`)
   - **Google Calendar API** (used by `manage_calendar`)
4. Go to **APIs & Services → Credentials**
5. Click **Create Credentials → OAuth 2.0 Client ID**
6. Choose **Application type: Desktop App** → Create
7. Copy the **Client ID** and **Client Secret**

#### 3. Authorize Gmail

After running `setup.py`, authorize AgentTina to send emails on your behalf:

```
python auth.py
```

A browser window will open. Log in with your Google account and click **Allow**. The token is saved locally and reused automatically on future runs.

#### 4. Launch the Agent

Open `tina.ipynb` and run the cells in order.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
