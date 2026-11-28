#!/usr/bin/env python3
"""Writes site/land.svg, the land outline behind the runner map, from Natural Earth's 1:110m land polygons.

Coordinates use the Miller projection in degree units, matching project() in site/app.js:
x is longitude and y is -1.25 * ln(tan(45° + 0.4 * latitude)), converted to degrees.
"""
import json
import math
import urllib.request

SOURCE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_110m_land.geojson"
MIN_LAT = -58


def project(lon, lat):
    return lon, -math.degrees(1.25 * math.log(math.tan(math.pi / 4 + 0.4 * math.radians(lat))))


def ring_path(ring):
    points, last = [], None
    for lon, lat in ring:
        x, y = project(lon, max(lat, MIN_LAT))
        point = (round(x, 1), round(y, 1))
        if point != last:
            points.append(point)
            last = point
    if len(points) < 3:
        return ""
    return "M" + "L".join(f"{x:g} {y:g}" for x, y in points) + "Z"


def main():
    with urllib.request.urlopen(SOURCE, timeout=30) as resp:
        land = json.load(resp)
    paths = []
    for feature in land["features"]:
        geometry = feature["geometry"]
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        for polygon in polygons:
            if max(lat for _, lat in polygon[0]) < MIN_LAT:
                continue
            paths.extend(ring_path(ring) for ring in polygon)
    top, bottom = project(0, 84)[1], project(0, MIN_LAT)[1]
    d = "".join(paths)
    with open("site/land.svg", "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-180 {top:.1f} 360 {bottom - top:.1f}">'
                f'<path id="land" d="{d}"/></svg>\n')


if __name__ == "__main__":
    main()
