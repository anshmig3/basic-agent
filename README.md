# basic-agent

A minimal conversational agent sample built with [Microsoft Agent Framework](https://github.com/microsoft/agent-framework), connected to a model deployed in your Azure AI Foundry project. It remembers the conversation across turns, and can optionally call tools from an MCP (Model Context Protocol) server.

Deployment to Azure AI Foundry is up to you (portal, CLI, container, or your own pipeline) — this sample only covers building and running the agent itself.

## Prerequisites

- Python 3.10+
- An Azure AI Foundry project with a chat model deployed (e.g. `gpt-4o`) — note the project endpoint and the model's deployment name from the Foundry portal's "Overview" and "Models + endpoints" pages.
- Azure CLI, logged in: `az login` (used by `AzureCliCredential` for auth; your identity needs the appropriate role, e.g. **Azure AI User**, on the Foundry project).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL_NAME
```

## Run

```bash
python basic_agent.py
```

Starts an interactive chat loop, streaming responses, with memory of the whole conversation for that session (`AgentSession`).

## Optional: attach an MCP server

Set in `.env`:

```bash
MCP_ENABLED=true
MCP_NAME=Microsoft Learn MCP
MCP_URL=https://learn.microsoft.com/api/mcp
```

The agent connects to the MCP server over Streamable HTTP and can call its tools during the conversation. Point `MCP_URL` at any MCP server you have access to. Leave `MCP_ENABLED=false` (the default) to run with no MCP tools at all.
