# examples/demo_routing.py

import asyncio
import json

from maps.routing_server import (
    _tool_route_between,
    _tool_nearest_road,
    _tool_distance_matrix,
)


async def main() -> None:
    # I’m using rough coordinates around AUB and Beirut Airport for the demo
    aub_lat, aub_lon = 33.9010, 35.4800
    airport_lat, airport_lon = 33.8209, 35.4884

    print("=== Demo: route_between (AUB -> Beirut Airport) ===")
    route_result = await _tool_route_between(
        {
            "start_lat": aub_lat,
            "start_lon": aub_lon,
            "end_lat": airport_lat,
            "end_lon": airport_lon,
            "profile": "driving",
            "overview": "false",
        }
    )
    print(json.dumps(json.loads(route_result[0].text), indent=2))
    print("\n" + "=" * 60 + "\n")

    print("=== Demo: nearest_road (around AUB) ===")
    nearest_result = await _tool_nearest_road(
        {
            "lat": aub_lat,
            "lon": aub_lon,
            "profile": "driving",
        }
    )
    print(json.dumps(json.loads(nearest_result[0].text), indent=2))
    print("\n" + "=" * 60 + "\n")

    print("=== Demo: distance_matrix (3 cafes in Beirut, dummy coords) ===")
    # here I'm just putting made-up coordinates for the sake of testing the function
    coords = [
        [33.895, 35.480],  # point 1
        [33.897, 35.485],  # point 2
        [33.899, 35.490],  # point 3
    ]
    matrix_result = await _tool_distance_matrix(
        {
            "coordinates": coords,
            "profile": "driving",
            "annotations": "duration,distance",
        }
    )
    print(json.dumps(json.loads(matrix_result[0].text), indent=2))
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    # quick and dirty test for the routing server helpers
    asyncio.run(main())
