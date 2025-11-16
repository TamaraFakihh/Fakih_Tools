import asyncio
import os
import sys

from dotenv import load_dotenv
from agents import Agent, Runner
from agents.mcp import MCPServerStdio


async def main() -> None:
    # load variables from .env so I don't have to export the key every time
    load_dotenv()

    # just in case I forget to set the key → fail fast with a clear message
    if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"]:
        raise RuntimeError(
            "Please set OPENAI_API_KEY in your environment or in a .env file "
            "before running this script."
        )

    # use the same Python that is running this script (should be the venv one)
    python_cmd = sys.executable

    # MCP server for geocoding / reverse / POI search
    geo_server = MCPServerStdio(
        name="Geo MCP Server",
        params={
            "command": python_cmd,
            "args": ["-m", "maps.geo_server"],  # runs `python -m maps.geo_server`
        },
    )

    # MCP server for routing / distance matrix
    routing_server = MCPServerStdio(
        name="Routing MCP Server",
        params={
            "command": python_cmd,
            "args": ["-m", "maps.routing_server"],
        },
    )

    # start both MCP servers and attach them to the agent
    async with geo_server as geo, routing_server as routing:
        # this is the main agent that will call the MCP tools under the hood
        agent = Agent(
            name="Map Assistant",
            instructions=(
                "You are a helpful map assistant. "
                "Use the available MCP tools to: "
                "1) geocode places, 2) search POIs, 3) plan routes and distance matrices. "
                "Always explain what you did and summarize the results clearly."
            ),
            mcp_servers=[geo, routing],
        )

        print("🚀 Map agent ready. Ask things like:")
        print("   - 'What are the coordinates of American University of Beirut?'")
        print("   - 'Plan a driving route from AUB to Beirut Airport.'")
        print("   - 'Find 3 cafes in Beirut and build a distance matrix between them.'")
        print("Type 'exit' to quit.\n")

        # simple REPL loop so I can test the agent from the terminal
        while True:
            try:
                user_input = input("You: ")
            except (EOFError, KeyboardInterrupt):
                # if I Ctrl+C or send EOF, just exit nicely
                print("\nExiting.")
                break

            if user_input.strip().lower() in {"exit", "quit"}:
                break

            # this is where the magic happens: agent + MCP servers handle the query
            result = await Runner.run(starting_agent=agent, input=user_input)

            print("\nAssistant:\n")
            print(result.final_output)
            print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    # run the async main (Python 3.11 style)
    asyncio.run(main())
