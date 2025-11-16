# examples/demo_geo.py

import asyncio
import json

# importing the internal tool helpers directly from the geo server
from maps.geo_server import (
    _tool_geocode_place,
    _tool_reverse_geocode,
    _tool_search_poi,
)


async def main() -> None:
    print("=== Demo: geocode_place ===")
    geo_result = await _tool_geocode_place(
        {
            "query": "American University of Beirut",
            "country_code": "lb",
            "limit": 1,
        }
    )
    # each tool returns a list of TextContent objects, so I just print the text
    print(json.dumps(json.loads(geo_result[0].text), indent=2, ensure_ascii=False))
    print("\n" + "=" * 60 + "\n")

    print("=== Demo: reverse_geocode ===")
    # rough coordinates of AUB (these can be adjusted)
    reverse_result = await _tool_reverse_geocode(
        {
            "lat": 33.9010,
            "lon": 35.4800,
            "zoom": 18,
        }
    )
    print(json.dumps(json.loads(reverse_result[0].text), indent=2, ensure_ascii=False))
    print("\n" + "=" * 60 + "\n")

    print("=== Demo: search_poi (cafes in Beirut) ===")
    poi_result = await _tool_search_poi(
        {
            "query": "cafe",
            "city": "Beirut",
            "limit": 3,
        }
    )
    print(json.dumps(json.loads(poi_result[0].text), indent=2, ensure_ascii=False))
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    # just run all three calls in sequence to sanity–check the geo server logic
    asyncio.run(main())
