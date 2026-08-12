"""Build the local dev agent: Microsoft Agent Framework `Agent` backed by
`FoundryChatClient`, with an optional MCP server attached as a tool.

This runs the agent loop locally against a model deployment in your Azure AI
Foundry project. For talking to the *deployed* PromptAgent instead, see
foundry_runtime.py.
"""

from __future__ import annotations

import os
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncIterator

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()

DEFAULT_INSTRUCTIONS = (
    "You are a helpful, concise assistant. Use any tools available to you "
    "when they help answer the question, and say when you don't know something."
)


def _mcp_enabled() -> bool:
    return os.environ.get("MCP_ENABLED", "false").strip().lower() in ("1", "true", "yes")


@asynccontextmanager
async def create_agent() -> AsyncIterator[Agent]:
    """Yield a ready-to-use agent, tearing down its connections on exit."""
    client = FoundryChatClient(
        project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
        model=os.environ.get("FOUNDRY_MODEL_NAME"),
        credential=AzureCliCredential(),
    )

    async with AsyncExitStack() as stack:
        tools = None
        if _mcp_enabled():
            mcp_tool = await stack.enter_async_context(
                MCPStreamableHTTPTool(
                    name=os.environ.get("MCP_NAME", "MCP Server"),
                    url=os.environ["MCP_URL"],
                )
            )
            tools = [mcp_tool]

        agent = await stack.enter_async_context(
            Agent(
                client=client,
                name=os.environ.get("FOUNDRY_AGENT_NAME", "BasicAgent"),
                instructions=os.environ.get("AGENT_INSTRUCTIONS", DEFAULT_INSTRUCTIONS),
                tools=tools,
            )
        )
        yield agent
