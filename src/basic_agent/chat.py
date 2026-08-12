"""Interactive REPL for the local dev agent.

Keeps one `AgentSession` for the life of the process so the agent remembers
earlier turns of the conversation.
"""

from __future__ import annotations

import asyncio

from basic_agent.agent import create_agent


async def main() -> None:
    async with create_agent() as agent:
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


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
