# basic-agent

A conversational agent built with [Microsoft Agent Framework](https://github.com/microsoft/agent-framework), structured as a **Foundry hosted agent** — the format the [Foundry Toolkit extension for VS Code](https://marketplace.visualstudio.com/) deploys directly to Azure AI Foundry. It talks over the OpenAI-compatible Responses protocol, which manages multi-turn conversation history for you, and can optionally call tools from an MCP (Model Context Protocol) server.

## Prerequisites

- VS Code with the **Foundry Toolkit** extension installed
- Python 3.12+
- An Azure AI Foundry project with a chat model deployed (e.g. `gpt-4o`) — note the project endpoint and the model's deployment name from the Foundry portal's "Overview" and "Models + endpoints" pages
- Signed in to Azure (`az login`, or via the Foundry Toolkit extension) — your identity needs the appropriate role, e.g. **Azure AI User**, on the Foundry project

## Project layout

```
main.py            # agent + hosting server entrypoint (this is what the container runs)
agent.yaml          # hosted agent manifest (protocol, resources, env vars) read by the Foundry Toolkit
requirements.txt
Dockerfile
.dockerignore
.env.example
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set FOUNDRY_PROJECT_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT_NAME
```

## Run locally

Open the folder in VS Code and press **F5** — the Foundry Toolkit extension launches `main.py` with `debugpy` attached and opens the Agent Inspector so you can chat with the agent and step through requests.

Without the extension, you can run it directly:

```bash
python main.py
```

This starts an OpenAI-compatible Responses server on `http://localhost:8088`. Multi-turn memory comes from the Responses protocol itself: each reply includes a response id, and follow-up requests pass it back as `previous_response_id` so the service keeps the conversation's context — there's no local session code to manage.

## Optional: attach MCP servers

Set `MCP_SERVERS` in `.env` to a JSON array — one entry per MCP server:

```bash
MCP_SERVERS='[
  {"name": "Microsoft Learn MCP", "url": "https://learn.microsoft.com/api/mcp"},
  {"name": "GitHub", "url": "https://api.githubcopilot.com/mcp/", "approval_mode": "always_require", "headers": {"Authorization": "Bearer <token>"}}
]'
```

`main.py` registers each entry as a hosted/remote tool (`client.get_mcp_tool(...)`) the agent can call during the conversation. Per server:

- `name` / `url` — required
- `approval_mode` — `never_require` or `always_require` (defaults to `never_require`)
- `headers` — optional, e.g. for an `Authorization` bearer token

Leave `MCP_SERVERS` empty/unset to run with no MCP tools at all.

## Deploy to Azure AI Foundry

With the Foundry Toolkit extension installed, open the Command Palette and run **"Foundry Toolkit: Deploy Hosted Agent."** It builds the `Dockerfile`, pushes the image, and registers the agent in your Foundry project using the definition in `agent.yaml`.
