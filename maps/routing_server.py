import asyncio
import json
from typing import List

import httpx
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

# MCP server for routing-related tools (OSRM wrapper)
app = Server("routing-server")

# public OSRM instance (good enough for the assignment)
OSRM_BASE = "https://router.project-osrm.org"


@app.list_tools()
async def list_tools() -> List[types.Tool]:
    # advertises all the routing tools this server supports
    return [
        types.Tool(
            name="route_between",
            description=(
                "Get fastest route between two coordinates using OSRM. "
                "Returns distance (meters), duration (seconds), and geometry info."
            ),
            inputSchema={
                "type": "object",
                "required": ["start_lat", "start_lon", "end_lat", "end_lon"],
                "properties": {
                    "start_lat": {"type": "number", "description": "Start latitude."},
                    "start_lon": {"type": "number", "description": "Start longitude."},
                    "end_lat": {"type": "number", "description": "End latitude."},
                    "end_lon": {"type": "number", "description": "End longitude."},
                    "profile": {
                        "type": "string",
                        "description": "Travel mode: driving, walking, cycling.",
                        "default": "driving",
                    },
                    "overview": {
                        "type": "string",
                        "description": "Route overview: 'full' or 'false'.",
                        "default": "false",
                    },
                },
            },
        ),
        types.Tool(
            name="nearest_road",
            description="Snap a coordinate to the nearest road using OSRM Nearest service.",
            inputSchema={
                "type": "object",
                "required": ["lat", "lon"],
                "properties": {
                    "lat": {"type": "number", "description": "Latitude."},
                    "lon": {"type": "number", "description": "Longitude."},
                    "profile": {
                        "type": "string",
                        "description": "Travel mode: driving, walking, cycling.",
                        "default": "driving",
                    },
                },
            },
        ),
        types.Tool(
            name="distance_matrix",
            description="Compute distance/time matrix between coordinates using OSRM Table API.",
            inputSchema={
                "type": "object",
                "required": ["coordinates"],
                "properties": {
                    "coordinates": {
                        "type": "array",
                        "description": "List of [lat, lon] pairs.",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                        "minItems": 2,
                    },
                    "profile": {
                        "type": "string",
                        "description": "Travel mode: driving, walking, cycling.",
                        "default": "driving",
                    },
                    "annotations": {
                        "type": "string",
                        "description": "duration, distance, or 'distance,duration'.",
                        "default": "duration",
                    },
                },
            },
        ),
    ]


async def _osrm_get(path: str, params: dict | None = None) -> dict:
    """
    Small helper to call OSRM and handle the basic error case.
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{OSRM_BASE}{path}", params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok":
            # if OSRM is unhappy, just raise and let the tool wrapper catch it
            raise RuntimeError(f"OSRM error: {data.get('message')}")
        return data


async def _tool_route_between(arguments: dict) -> list[types.TextContent]:
    # unpack the arguments passed from the agent
    start_lat = arguments["start_lat"]
    start_lon = arguments["start_lon"]
    end_lat = arguments["end_lat"]
    end_lon = arguments["end_lon"]
    profile = arguments.get("profile", "driving")
    overview = arguments.get("overview", "false")

    # OSRM expects lon,lat;lon,lat (so I flip the order)
    coord_str = f"{start_lon},{start_lat};{end_lon},{end_lat}"
    path = f"/route/v1/{profile}/{coord_str}"

    data = await _osrm_get(path, params={"overview": overview})

    route = data["routes"][0]
    result = {
        "distance_m": route.get("distance"),
        "duration_s": route.get("duration"),
        "legs": route.get("legs"),
        "geometry": route.get("geometry"),
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, indent=2),
        )
    ]


async def _tool_nearest_road(arguments: dict) -> list[types.TextContent]:
    # single point snap to road
    lat = arguments["lat"]
    lon = arguments["lon"]
    profile = arguments.get("profile", "driving")

    path = f"/nearest/v1/{profile}/{lon},{lat}"
    data = await _osrm_get(path, params={"number": 1})

    waypoint = data["waypoints"][0]
    result = {
        "snapped_location": {
            "lon": waypoint["location"][0],
            "lat": waypoint["location"][1],
        },
        "distance_to_input_m": waypoint.get("distance"),
        "road_name": waypoint.get("name"),
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, indent=2),
        )
    ]


async def _tool_distance_matrix(arguments: dict) -> list[types.TextContent]:
    coordinates = arguments["coordinates"]
    profile = arguments.get("profile", "driving")
    annotations = arguments.get("annotations", "duration")

    # OSRM expects lon,lat;lon,lat;... so I transform [lat, lon] → "lon,lat"
    pairs = [f"{lon},{lat}" for lat, lon in coordinates]
    coord_str = ";".join(pairs)

    path = f"/table/v1/{profile}/{coord_str}"
    params = {"annotations": annotations}

    data = await _osrm_get(path, params=params)

    result = {
        "sources": data.get("sources"),
        "destinations": data.get("destinations"),
        "durations": data.get("durations"),
        "distances": data.get("distances"),
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, indent=2),
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """
    Main MCP entry point: routes the call to the right helper based on tool name.
    """
    try:
        if name == "route_between":
            return await _tool_route_between(arguments)
        if name == "nearest_road":
            return await _tool_nearest_road(arguments)
        if name == "distance_matrix":
            return await _tool_distance_matrix(arguments)

        # guard in case of typos / unknown tool name
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool '{name}'"}, indent=2),
            )
        ]
    except Exception as e:
        # very simple error reporting back to the agent
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2),
            )
        ]


async def main() -> None:
    """
    Run this routing MCP server over stdio.
    The Agents SDK spawns this with `python -m maps.routing_server`.
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="routing-server",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    # normal async entry point
    asyncio.run(main())
