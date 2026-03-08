# AgentTina

AgentTina is an open-source AI agent built with [LangChain](https://www.langchain.com/), [LangGraph](https://www.langgraph.com/), and [Groq](https://groq.com/), powered by the `llama-3.3-70b-versatile` model.

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
pip install langchain-groq langgraph langchain-core python-dotenv \
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
