#!/usr/bin/env python3
"""Build a compact named POI list from Geofabrik's Berlin/Brandenburg OSM extract."""
import json
import os
from pathlib import Path
import osmium

SOURCE = Path(os.environ.get("OSM_PBF", "region.osm.pbf"))
DEST = Path("places.json")
CATEGORIES = {
    "amenity": {"cafe": "food", "restaurant": "food", "ice_cream": "food"},
    "tourism": {"museum": "culture", "gallery": "culture", "attraction": "culture", "viewpoint": "culture"},
    "historic": {"castle": "culture", "monument": "culture", "ruins": "culture"},
    "leisure": {"park": "nature", "garden": "nature"},
    "natural": {"beach": "nature"},
}
# Keep Berlin and the nearby Brandenburg area. This covers the app's 15 km radius.
BOUNDS = (52.20, 12.95, 52.78, 14.05)
places = {}

def category(tags):
    for key, choices in CATEGORIES.items():
        value = tags.get(key)
        if value in choices:
            return choices[value]
    return None

class Places(osmium.SimpleHandler):
    def node(self, n):
        cat = category(n.tags)
        name = n.tags.get("name")
        if not cat or not name or not n.location.valid():
            return
        lat, lon = n.location.lat, n.location.lon
        if not (BOUNDS[0] <= lat <= BOUNDS[2] and BOUNDS[1] <= lon <= BOUNDS[3]):
            return
        places[f"n{n.id}"] = {"id": f"n{n.id}", "name": name, "lat": round(lat, 6), "lon": round(lon, 6), "category": cat}

print(f"Reading {SOURCE}", flush=True)
Places().apply_file(str(SOURCE))
if len(places) < 100:
    raise SystemExit(f"Only {len(places)} places found; refusing to replace data")
data = sorted(places.values(), key=lambda p: p["id"])
DEST.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"Saved {len(data)} named places to {DEST}", flush=True)
