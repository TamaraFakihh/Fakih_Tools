import asyncio
import json
from typing import List

import httpx
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

# basic MCP server for all the geo-related tools
app = Server("geo-server")

# just putting a custom user agent so Nominatim doesn't get angry
USER_AGENT = "eece503p-fakih-tools/1.0 (contact: tmf14@mail.aub.edu)"


@app.list_tools()
async def list_tools() -> List[types.Tool]:
    """
    Advertise the tools provided by this map server.
    (the agent will call this to know what it can do)
    """
    return [
        types.Tool(
            name="geocode_place",
            description=(
                "Convert a place name or address into coordinates using "
                "OpenStreetMap Nominatim (lat, lon)."
            ),
            inputSchema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Place or address to geocode (e.g., 'American University of Beirut').",
                    },
                    "country_code": {
                        "type": "string",
                        "description": "Optional 2-letter country code, e.g. 'lb'.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of results.",
                        "default": 3,
                    },
                },
            },
        ),
        types.Tool(
            name="reverse_geocode",
            description="Convert (lat, lon) into a human-readable address using Nominatim.",
            inputSchema={
                "type": "object",
                "required": ["lat", "lon"],
                "properties": {
                    "lat": {
                        "type": "number",
                        "description": "Latitude in decimal degrees.",
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude in decimal degrees.",
                    },
                    "zoom": {
                        "type": "integer",
                        "description": "Zoom level (3–18) controlling detail of address.",
                        "default": 18,
                    },
                },
            },
        ),
        types.Tool(
            name="search_poi",
            description="Search for POIs (cafes, museums, etc.) in a given city using Nominatim.",
            inputSchema={
                "type": "object",
                "required": ["query", "city"],
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Type of POI (e.g. 'cafe', 'museum', 'hospital').",
                    },
                    "city": {
                        "type": "string",
                        "description": "City (e.g. 'Beirut').",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of results.",
                        "default": 5,
                    },
                },
            },
        ),
    ]


async def _nominatim_get(path: str, params: dict) -> dict | list:
    """
    Small helper around the Nominatim HTTP GET.
    Just keeps the request logic in one place.
    """
    base_url = "https://nominatim.openstreetmap.org"
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
        resp = await client.get(f"{base_url}{path}", params=params)
        resp.raise_for_status()
        return resp.json()


async def _tool_geocode_place(arguments: dict) -> list[types.TextContent]:
    # required arg
    query = arguments["query"]
    # optional filters
    country_code = arguments.get("country_code")
    limit = arguments.get("limit", 3)

    params = {
        "q": query,
        "format": "jsonv2",
        "limit": limit,
    }
    if country_code:
        params["countrycodes"] = country_code

    data = await _nominatim_get("/search", params)

    # trimming down the response to just the fields I care about
    results = [
        {
            "display_name": item.get("display_name"),
            "lat": item.get("lat"),
            "lon": item.get("lon"),
            "type": item.get("type"),
            "class": item.get("class"),
        }
        for item in data
    ]

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                {
                    "query": query,
                    "results": results,
                },
                indent=2,
                ensure_ascii=False,
            ),
        )
    ]


async def _tool_reverse_geocode(arguments: dict) -> list[types.TextContent]:
    # here I assume the agent already has lat/lon, just turning it into an address
    lat = arguments["lat"]
    lon = arguments["lon"]
    zoom = arguments.get("zoom", 18)

    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "zoom": zoom,
    }

    data = await _nominatim_get("/reverse", params)

    result = {
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "display_name": data.get("display_name"),
        "address": data.get("address"),
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False),
        )
    ]


async def _tool_search_poi(arguments: dict) -> list[types.TextContent]:
    # simple text-based POI search in a given city (nothing fancy)
    query = arguments["query"]
    city = arguments["city"]
    limit = arguments.get("limit", 5)

    params = {
        "q": f"{query}, {city}",
        "format": "jsonv2",
        "limit": limit,
    }

    data = await _nominatim_get("/search", params)

    results = [
        {
            "name": item.get("display_name"),
            "lat": item.get("lat"),
            "lon": item.get("lon"),
            "type": item.get("type"),
            "class": item.get("class"),
        }
        for item in data
    ]

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                {
                    "query": query,
                    "city": city,
                    "results": results,
                },
                indent=2,
                ensure_ascii=False,
            ),
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """
    Main entry point for MCP tool calls.
    (the server will route calls here based on the tool name)
    """
    try:
        if name == "geocode_place":
            return await _tool_geocode_place(arguments)
        if name == "reverse_geocode":
            return await _tool_reverse_geocode(arguments)
        if name == "search_poi":
            return await _tool_search_poi(arguments)

        # fallback in case I typo the tool name somewhere
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool '{name}'"}, indent=2),
            )
        ]
    except Exception as e:
        # basic error handling so at least the agent sees something readable
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2),
            )
        ]


async def main() -> None:
    """
    Run this MCP server over stdio.
    The Agents SDK will spawn this as a subprocess with `python -m maps.geo_server`.
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="geo-server",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    # standard async entry point
    asyncio.run(main())
