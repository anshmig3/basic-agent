"""Deploy the agent to Azure AI Foundry.

Creates a new version of the agent's PromptAgentDefinition (model,
instructions, and an optional MCP tool) in your Foundry project, then routes
100% of the agent's traffic to that new version. Re-run this after changing
AGENT_INSTRUCTIONS, FOUNDRY_MODEL_NAME, or the MCP_* settings in .env to
publish a new version.

Usage:
    python deploy/deploy_agent.py

Requires:
    pip install "azure-ai-projects>=2.0.0" azure-identity python-dotenv
    az login   (or another credential supported by DefaultAzureCredential)
"""

from __future__ import annotations

import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentEndpointConfig,
    FixedRatioVersionSelectionRule,
    MCPTool,
    PromptAgentDefinition,
    ProtocolConfiguration,
    ResponsesProtocolConfiguration,
    VersionSelector,
)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

DEFAULT_INSTRUCTIONS = (
    "You are a helpful, concise assistant. Use any tools available to you "
    "when they help answer the question, and say when you don't know something."
)


def _build_tools() -> list:
    if os.environ.get("MCP_ENABLED", "false").strip().lower() not in ("1", "true", "yes"):
        return []
    return [
        MCPTool(
            server_label=os.environ.get("MCP_SERVER_LABEL", "mcp-server"),
            server_url=os.environ["MCP_URL"],
            require_approval=os.environ.get("MCP_REQUIRE_APPROVAL", "never"),
        )
    ]


def main() -> None:
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    model = os.environ["FOUNDRY_MODEL_NAME"]
    agent_name = os.environ.get("FOUNDRY_AGENT_NAME", "BasicAgent")
    instructions = os.environ.get("AGENT_INSTRUCTIONS", DEFAULT_INSTRUCTIONS)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
    ):
        version = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=model,
                instructions=instructions,
                tools=_build_tools(),
            ),
        )
        print(f"Created '{agent_name}' version {version.version}")

        project_client.agents.update_details(
            agent_name=agent_name,
            agent_endpoint=AgentEndpointConfig(
                version_selector=VersionSelector(
                    version_selection_rules=[
                        FixedRatioVersionSelectionRule(
                            agent_version=version.version, traffic_percentage=100
                        )
                    ]
                ),
                protocol_configuration=ProtocolConfiguration(
                    responses=ResponsesProtocolConfiguration()
                ),
            ),
        )
        print(f"Routed 100% of traffic on '{agent_name}' to version {version.version}")
        print(
            f"\nDeployed. Set FOUNDRY_AGENT_VERSION={version.version} in .env "
            "(or leave it blank to always follow whichever version has traffic), "
            "then run: basic-agent-remote-chat"
        )


if __name__ == "__main__":
    main()
