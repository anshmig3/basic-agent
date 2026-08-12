"""Interactive REPL against the agent *deployed* to Azure AI Foundry.

Connects with `FoundryAgent` by name (and optionally version) instead of
building the agent locally — instructions, model, and any hosted tools are
whatever was published by deploy/deploy_agent.py. Run that script first.
"""

from __future__ import annotations

import asyncio
import os

from agent_framework.foundry import FoundryAgent
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    agent = FoundryAgent(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        agent_name=os.environ.get("FOUNDRY_AGENT_NAME", "BasicAgent"),
        agent_version=os.environ.get("FOUNDRY_AGENT_VERSION") or None,
        credential=AzureCliCredential(),
    )

    session = agent.create_session()
    print(f"Connected to deployed agent '{agent.name}'. Type 'exit' to quit.\n")

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

        result = await agent.run(user_input, session=session)
        print(f"{agent.name}: {result.text}\n")


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
