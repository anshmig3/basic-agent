# basic-agent

A conversational agent built with [Microsoft Agent Framework](https://github.com/microsoft/agent-framework), deployable to **Azure AI Foundry**. It remembers conversation context across turns, and can optionally call tools exposed by an MCP (Model Context Protocol) server.

## How it fits together

- **Local dev agent** (`basic_agent.agent`, run via `basic-agent-chat`) — builds an `Agent` locally with `FoundryChatClient`, which calls a model deployment in your Foundry project. Fastest loop for iterating on instructions/tools.
- **Deploy script** (`deploy/deploy_agent.py`) — publishes the agent (model, instructions, optional MCP tool) as a versioned **PromptAgent** in your Foundry project using the `azure-ai-projects` SDK, and routes traffic to it.
- **Deployed-agent runtime** (`basic_agent.foundry_runtime`, run via `basic-agent-remote-chat`) — connects to the *deployed* agent by name via `FoundryAgent`, so instructions/model/tools all come from what you published.

Conversation memory is handled the same way in both cases: an `AgentSession` is created once per REPL run and passed into every `agent.run(...)` call, so the agent has full context of earlier turns.

## Prerequisites

- Python 3.10+
- An Azure AI Foundry project with a chat model deployed (e.g. `gpt-4o`) — note the project endpoint and the model's deployment name from the Foundry portal's "Overview" and "Models + endpoints" pages.
- Azure CLI, logged in: `az login` (used by `AzureCliCredential` / `DefaultAzureCredential` for auth; your identity needs the appropriate role, e.g. **Azure AI User**, on the Foundry project).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

cp .env.example .env
# then edit .env: set FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL_NAME at minimum
```

## Run locally

```bash
basic-agent-chat
```

This starts an interactive chat loop against your Foundry model deployment, streaming responses, with memory of the whole conversation for that session.

## Optional: attach an MCP server

Set in `.env`:

```bash
MCP_ENABLED=true
MCP_NAME=Microsoft Learn MCP
MCP_URL=https://learn.microsoft.com/api/mcp
```

The agent connects to the MCP server over Streamable HTTP and can call its tools during the conversation (`src/basic_agent/agent.py`). Point `MCP_URL` at any MCP server you have access to — remote or one you're running locally. Leave `MCP_ENABLED=false` (the default) to run with no MCP tools at all.

## Deploy to Azure AI Foundry

```bash
python deploy/deploy_agent.py
```

This creates a new **version** of the `FOUNDRY_AGENT_NAME` PromptAgent in your Foundry project (model + instructions + the MCP tool, if `MCP_ENABLED=true`), then routes 100% of that agent's traffic to the new version. Re-run it any time you change `AGENT_INSTRUCTIONS`, `FOUNDRY_MODEL_NAME`, or the `MCP_*` settings to publish an update.

For a hosted MCP tool, approval is governed by `MCP_REQUIRE_APPROVAL` (`never` or `always`) — with `always`, tool calls need an approval response before the agent can use them; see `foundry_chat_client_with_hosted_mcp.py`-style approval handling if you build that flow into a client.

### Talk to the deployed agent

```bash
# optional: pin to a specific version; otherwise follows whatever has traffic
echo 'FOUNDRY_AGENT_VERSION=1' >> .env

basic-agent-remote-chat
```

This connects to the agent as deployed in Foundry (not rebuilt locally), still with per-session memory.

## Configuration reference

| Variable | Purpose |
|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | Your Foundry project endpoint |
| `FOUNDRY_MODEL_NAME` | Deployed model name to use |
| `FOUNDRY_AGENT_NAME` | Agent name, local and in Foundry |
| `FOUNDRY_AGENT_VERSION` | Version to connect to in `basic-agent-remote-chat` (blank = follow traffic routing) |
| `AGENT_INSTRUCTIONS` | System instructions (optional, has a default) |
| `MCP_ENABLED` | `true`/`false` — attach the MCP server as a tool |
| `MCP_NAME` | Display name for the MCP tool (local dev agent) |
| `MCP_URL` | Streamable HTTP URL of the MCP server |
| `MCP_SERVER_LABEL` | Label for the MCP tool when deployed |
| `MCP_REQUIRE_APPROVAL` | `never`/`always` — approval policy for the hosted MCP tool |

## Project layout

```
src/basic_agent/
  agent.py           # local dev agent (FoundryChatClient + optional MCP tool)
  chat.py            # REPL for the local dev agent
  foundry_runtime.py # REPL against the deployed Foundry agent
deploy/
  deploy_agent.py    # publishes/updates the agent in Azure AI Foundry
```
