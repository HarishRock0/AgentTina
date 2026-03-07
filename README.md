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

## Getting Started

### Prerequisites

```
pip install langchain-groq langgraph langchain-core python-dotenv
```

### Setup

1. Create a `.env` file in the project root:
   ```
   API=your-groq-api-key
   ```
2. Open `tina.ipynb` and run the cells in order.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
