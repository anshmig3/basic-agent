# Copyright (c) Microsoft. All rights reserved.

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


def main():
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )

    tools: list[ToolTypes] = []
    if os.environ.get("MCP_ENABLED", "false").lower() in ("1", "true", "yes"):
        mcp_url = os.environ.get("MCP_URL")
        if not mcp_url:
            logger.warning("MCP_ENABLED is true but MCP_URL is not set. Skipping the MCP tool.")
        else:
            tools.append(
                client.get_mcp_tool(
                    name=os.environ.get("MCP_NAME", "MCP Server"),
                    url=mcp_url,
                    approval_mode=os.environ.get("MCP_APPROVAL_MODE", "never_require"),
                )
            )

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
