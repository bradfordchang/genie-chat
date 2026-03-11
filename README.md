# Genie Chat

A conversational interface for [Databricks Genie](https://docs.databricks.com/en/genie/index.html) that lets users ask natural language questions about their data and get back SQL queries, results, and explanations in real time.

![React](https://img.shields.io/badge/React-18-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green) ![Databricks](https://img.shields.io/badge/Databricks-App-red)

## Features

- **Streaming responses** — real-time status updates as Genie processes your question (reading schemas, generating SQL, running queries)
- **SQL display** — collapsible SQL blocks with natural language descriptions
- **Result tables** — scrollable tables with row counts
- **Markdown rendering** — rich text formatting in Genie's explanations
- **Follow-up questions** — suggested questions for deeper exploration
- **Multi-turn conversations** — context-aware follow-ups within the same conversation

## Architecture

```
frontend/          React + TypeScript + Vite
  src/
    App.tsx        Main chat UI, SSE consumption
    components/    MessageBubble, SqlBlock, ResultTable, etc.
    types.ts       TypeScript interfaces

backend/           FastAPI + Databricks SDK
  main.py          API routes, static file serving
  genie_client.py  Genie API wrapper, SSE streaming via polling
```

The backend polls the Genie API and streams results to the frontend via Server-Sent Events (SSE). The frontend progressively renders SQL, tables, text, and suggestions as they arrive.

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/install.html) authenticated to your workspace
- A [Genie Space](https://docs.databricks.com/en/genie/index.html) with tables configured

### Local Development

```bash
# Backend
pip install -r requirements.txt
cp .env.example .env  # then edit .env with your Genie Space ID
source .env && export GENIE_SPACE_ID
uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Deploy to Databricks Apps

1. Set your Genie Space ID in `app.yaml` (the `GENIE_SPACE_ID` env var)
2. Build the frontend and sync to workspace:

```bash
cd frontend && npm run build && cd ..
databricks workspace import-dir frontend/dist \
  /Workspace/Users/<you>/genie-chat/frontend/dist --overwrite
databricks workspace import-dir backend \
  /Workspace/Users/<you>/genie-chat/backend --overwrite
databricks apps deploy genie-chat \
  --source-code-path /Workspace/Users/<you>/genie-chat
```

## Configuration

| Variable | Description |
|----------|-------------|
| `GENIE_SPACE_ID` | Default Genie Space ID (set in `app.yaml`) |

The Space ID can also be overridden per request via the `space_id` query parameter on the `/api/ask` endpoint.

## License

MIT
