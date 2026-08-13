# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import os

from agent_framework import Agent, ToolTypes
from agent_framework.foundry import FoundryChatClient, ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_INSTRUCTIONS = (
    "You are a helpful, concise assistant. Use any tools available to you "
    "when they help answer the question."
)


def _load_mcp_servers() -> list[dict]:
    """Parse MCP_SERVERS, a JSON array of {name, url, approval_mode, headers} objects."""
    raw = os.environ.get("MCP_SERVERS", "").strip()
    if not raw:
        return []
    try:
        servers = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"MCP_SERVERS is not valid JSON: {exc}") from exc
    if not isinstance(servers, list):
        raise RuntimeError("MCP_SERVERS must be a JSON array of {name, url, ...} objects")
    return servers


def main():
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )

    tools: list[ToolTypes] = []
    for server in _load_mcp_servers():
        url = server.get("url")
        if not url:
            logger.warning("Skipping MCP server entry missing 'url': %s", server)
            continue
        kwargs = {
            "name": server.get("name", "MCP Server"),
            "url": url,
            "approval_mode": server.get("approval_mode", "never_require"),
        }
        if "headers" in server:
            kwargs["headers"] = server["headers"]
        tools.append(client.get_mcp_tool(**kwargs))

    agent = Agent(
        client=client,
        name=os.environ.get("AGENT_NAME", "BasicAgent"),
        instructions=os.environ.get("AGENT_INSTRUCTIONS", DEFAULT_INSTRUCTIONS),
        tools=tools,
        # History is managed by the hosting infrastructure (Responses protocol,
        # via previous_response_id), so the agent itself doesn't need to store it.
        default_options={"store": False},
    )

    server = ResponsesHostServer(agent)
    server.run()


if __name__ == "__main__":
    main()
