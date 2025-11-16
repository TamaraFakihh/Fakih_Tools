<!-- .github/copilot-instructions.md for Fakih_Tools -->
# Copilot instructions for this repository

Purpose

- Provide concise, actionable guidance to AI coding agents working on this repo.

Quick overview

- This repository contains a small Map-focused agent framework.
- Key runtime pieces:
  - `agent/main_agent.py` — agent entrypoint used for interactive runs. It creates two MCP servers (Geo and Routing) and starts an assistant loop. Expects `OPENAI_API_KEY` in environment or `.env`.
  - `maps/geo_server.py` — MCP server exposing geocoding and POI search tools (HTTP clients to external geocoding services).
  - `maps/routing_server.py` — MCP server exposing routing, nearest-road, and distance-matrix tools backed by OSRM.

How to run (developer workflows)

- Install dependencies from `requirements.txt` (the project uses `openai-agents`, `mcp`, `httpx`, and `python-dotenv`).
  - Example (PowerShell):
    ```powershell
    python -m pip install -r requirements.txt
    ```
- Run a single MCP server for manual testing:
  - Geo server: `python -m maps.geo_server`
  - Routing server: `python -m maps.routing_server`
- Run the interactive agent (starts both servers via MCP wrapper):
  - `python -m agent.main_agent` or `python agent/main_agent.py`
  - Ensure `OPENAI_API_KEY` is set (or place it in a `.env` file). `agent/main_agent.py` checks this and uses the current Python executable.

Project-specific patterns & conventions

- MCP pattern: both servers use the `mcp` library and implement `list_tools()` and `call_tool(...)`. Tools return `types.TextContent` JSON payloads. Follow the existing shape when adding tools.
- OSRM usage: `maps/routing_server.py` calls Project-OSRM HTTP endpoints. OSRM expects lon,lat ordering for coordinates; helper code in the file converts `[lat, lon]` to `lon,lat` strings. Keep this ordering convention when adding callers.
- Error handling: servers wrap tool calls and return JSON with an `error` key for tool failures (see `call_tool` implementations). Preserve this textual/JSON return shape for compatibility with agents.
- Stream/stdio servers: both servers run a stdio-based MCP server (`mcp.server.stdio.stdio_server`) — they expect to be launched as modules so `-m maps.geo_server` works correctly.

Integration points & external dependencies

- External HTTP services used:
  - OSRM: `https://router.project-osrm.org` (used in `maps/routing_server.py`)
  - Geo/POI services: referenced in `maps/geo_server.py` (check that file for the specific service names and auth patterns).
- Environment: `OPENAI_API_KEY` is required for `agent/main_agent.py` interactive agent. `.env` is supported via `python-dotenv`.

Editing guidance for AI agents

- When adding a new MCP tool:
  - Add a `types.Tool` entry in `list_tools()` with a clear `inputSchema` and defaults.
  - Implement the corresponding handler in `call_tool(name, arguments)` and return a list of `types.TextContent` items (JSON stringified payload is acceptable).
  - Mirror the existing error JSON shape: `{ "error": "..." }` to make downstream parsing predictable.
- When modifying routing geometry or coordinate handling, keep the `lon,lat` conversion comments and tests in sync — many callers assume `lat, lon` in Python structures but OSRM expects `lon,lat` strings.

Files to inspect for examples

- `agent/main_agent.py` — shows how MCP servers are configured and run together; shows the expectation for environment variables and `Runner.run()` usage.
- `maps/routing_server.py` — canonical examples of `list_tools()`/`call_tool()` and HTTP client usage with `httpx`.
- `maps/geo_server.py` — examples of geocoding/POI tool shapes and common payload formats.

Testing & debugging notes

- There are no automated unit tests in `tests/` (the `quick_manual_test.md` file is currently empty). Manual test flows:
  - Start a server: `python -m maps.geo_server` or `python -m maps.routing_server` and POST/GET to the service in a way the MCP stdio wrapper expects when used with an agent harness.
  - Run `python -m agent.main_agent` to exercise both servers through the agent loop; use simple prompts from the printed examples.
- Use `httpx`'s AsyncClient timeouts as examples; follow the same pattern for external requests.

If something is missing

- If a required credential or service base URL is not obvious, search for the host string (for OSRM, it's `router.project-osrm.org`) or open the server file to see service-specific keys and defaults.

Questions for maintainers

- Do you want this file to require running tests or CI checks before merging changes? If yes, provide the CI commands and I'll include them.

-- End of instructions
