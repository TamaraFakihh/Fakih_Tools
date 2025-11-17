# Fakih_Tools – MCP Map Assistant

This project is my EECE503P assignment on **Model Context Protocol (MCP)** and the **OpenAI Agents SDK**. The main idea is to turn classic map functionality (geocoding, POI search, routing, distance matrices) into **MCP servers**, and then plug them into a single **“Map Assistant” agent** that can call these tools dynamically instead of hard-coding HTTP calls inside the agent logic.

Concretely, I implemented:

- A **Geo MCP server** (`geo-server`) that wraps OpenStreetMap **Nominatim** for:
  - `geocode_place` → place name/address → coordinates  
  - `reverse_geocode` → coordinates → human-readable address  
  - `search_poi` → POI search in a given city (e.g. cafes in Beirut)
- A **Routing MCP server** (`routing-server`) that wraps **OSRM** for:
  - `route_between` → fastest route between two coordinates  
  - `nearest_road` → snap a coordinate to the nearest road  
  - `distance_matrix` → travel time/distance matrix for multiple points
- A **Map Assistant agent** that connects to both MCP servers and answers natural-language map questions by deciding which tools to call (geocoding, POI search, routing, distance matrix, etc.).

The goal is not to re-invent map algorithms, but to **expose existing map APIs as MCP tools** and show how an agent can orchestrate them in a clean, protocol-based way.

---

## Features

- 🌍 **Geocoding & reverse geocoding** via OpenStreetMap Nominatim  
- 📍 **POI search** in a given city (e.g. “3 cafes in Beirut”)  
- 🛣️ **Routing** between two coordinates using OSRM  
- 🧲 **Nearest road snapping** for noisy GPS-like coordinates  
- 🧮 **Distance matrix** for multiple points (useful for comparisons / planning)  
- 🤖 **Single Map Assistant agent** that uses both MCP servers as tools

---

## Prerequisites

- **Python 3.10+** (I used Python 3.11)
- A working **virtual environment** (recommended)
- An **OpenAI API key** with access to the models used by `openai-agents`

---

## Setup

From your terminal / PowerShell:

```bash
# 1. Clone the repo
git clone https://github.com/TamaraFakihh/Fakih_Tools.git
cd Fakih_Tools

# 2. Create and activate a virtual environment (example for Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

```

Then create a .env file in the project root:
```bash
# Fakih_Tools/.env
OPENAI_API_KEY=sk-...
```

Make sure this key matches the account you used on the OpenAI platform.

##How to Run the Map Assistant

The agent.main_agent script automatically spins up the two MCP servers (geo-server and routing-server) over stdio and attaches them to a single Map Assistant.

From inside the virtual environment:
```bash
python -m agent.main_agent
```

If everything is configured, you should see something like:
```bash
🚀 Map agent ready. Ask things like:
   - 'What are the coordinates of American University of Beirut?'
   - 'Plan a driving route from AUB to Beirut Airport.'
   - 'Find 3 cafes in Beirut and build a distance matrix between them.'
Type 'exit' to quit.
```

Now you can type questions in natural language, for example:

- What are the coordinates of American University of Beirut?

- Find 3 cafes in Beirut and give me their coordinates and a distance matrix.

- Plan a driving route from American University of Beirut to Beirut–Rafic Hariri International Airport.

- Given these 3 locations, which one is closest to AUB by driving time?

The agent will decide which MCP tools to call (geocode, POI search, routing, distance matrix) and then summarize the results back in plain English.

##Quick Demos / Tests for the MCP Servers

I also added simple demo scripts that call the MCP server helpers directly, without going through the agent, just to sanity check the logic.

From the project root:
```bash
# (Optional) Demo for geo tools – may hit 403 if Nominatim rate-limits
python -m examples.demo_geo

# Demo for routing tools – OSRM routing / nearest / distance matrix
python -m examples.demo_routing
```

These scripts directly call the helper functions used by the MCP tools and print the JSON results. They are useful to debug things like:

- wrong parameters,

- HTTP errors from public services,

- unexpected response formats.

##Demo Video

You can watch a short walkthrough of the project (code, MCP servers, and the agent in action) here:

👉 Demo video (demo.mp4)

This video shows:

- how the geo-server and routing-server are defined as MCP servers,

- how the tools (geocode_place, search_poi, route_between, etc.) are exposed,

- and how the Map Assistant uses them to answer real map-related questions from the terminal.
