# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from contextlib import AsyncExitStack

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

"""
Basic Foundry Agent - conversational agent with memory and an optional MCP tool

Connects to a model deployed in your Microsoft Foundry project via
FoundryChatClient, and runs an interactive chat loop that remembers earlier
turns of the conversation (via AgentSession). Attach an MCP server as a tool
by setting MCP_ENABLED=true.

Deploying this agent to Azure AI Foundry (as a PromptAgent, container, etc.)
is up to you - this sample only covers building and running the agent.

Environment variables:
    FOUNDRY_PROJECT_ENDPOINT - Microsoft Foundry project endpoint
    FOUNDRY_MODEL_NAME       - Deployment name of the model to use
    FOUNDRY_AGENT_NAME       - Agent name (optional, defaults to "BasicAgent")
    AGENT_INSTRUCTIONS       - System instructions (optional)

    MCP_ENABLED              - "true" to attach an MCP server as a tool (optional)
    MCP_NAME                 - Display name for the MCP tool
    MCP_URL                  - Streamable HTTP URL of the MCP server
"""

load_dotenv()

DEFAULT_INSTRUCTIONS = (
    "You are a helpful, concise assistant. Use any tools available to you "
    "when they help answer the question."
)


async def main() -> None:
    client = FoundryChatClient(
        project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
        model=os.environ.get("FOUNDRY_MODEL_NAME"),
        credential=AzureCliCredential(),
    )

    async with AsyncExitStack() as stack:
        tools = None
        if os.environ.get("MCP_ENABLED", "false").lower() in ("1", "true", "yes"):
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

        # One session for the whole conversation - the agent remembers earlier turns.
        session = agent.create_session()
        print(f"{agent.name} ready. Type 'exit' to quit.\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                break

            print(f"{agent.name}: ", end="", flush=True)
            async for chunk in agent.run(user_input, session=session, stream=True):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            print("\n")


if __name__ == "__main__":
    asyncio.run(main())
