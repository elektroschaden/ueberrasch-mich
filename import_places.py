#!/usr/bin/env python3
"""Download named Berlin-area POIs once for the static web app."""
import json, time, urllib.parse, urllib.request
from pathlib import Path
ENDPOINTS = ["https://overpass.private.coffee/api/interpreter", "https://overpass.ultra.cc/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
# Berlin and nearby Brandenburg, split to avoid oversized Overpass queries.
BOXES = [(52.35,13.20,52.52,13.52),(52.35,13.52,52.62,13.75),(52.52,13.20,52.65,13.52)]
TAGS = [('amenity','cafe|restaurant|ice_cream','food'),('tourism','museum|gallery|attraction|viewpoint','culture'),('historic','castle|monument|ruins','culture'),('leisure','park|garden','nature'),('natural','beach','nature')]
places = {}
for i,(south,west,north,east) in enumerate(BOXES,1):
    parts = [f'node["{key}"~"^({values})$"]["name"]({south},{west},{north},{east});' for key,values,_ in TAGS]
    query='[out:json][timeout:20];('+''.join(parts)+');out body;'
    payload=urllib.parse.urlencode({'data':query}).encode()
    data=None
    for attempt in range(3):
        endpoint=ENDPOINTS[attempt%len(ENDPOINTS)]
        try:
            request=urllib.request.Request(endpoint,data=payload,headers={'User-Agent':'UeberraschMich/1.0 (GitHub Pages static POI import)','Content-Type':'application/x-www-form-urlencoded'})
            with urllib.request.urlopen(request,timeout=30) as response:
                data=json.load(response)
            break
        except Exception as exc:
            print(f'Area {i} attempt {attempt+1}: {exc}',flush=True)
            time.sleep(2)
    if data is None:
        raise SystemExit(f'Import failed in area {i}; leaving existing data unchanged')
    for element in data.get('elements',[]):
        tags=element.get('tags',{})
        name=tags.get('name','').strip()
        lat,lon=element.get('lat'),element.get('lon')
        if not name or lat is None or lon is None: continue
        kind=next((category for key,values,category in TAGS if tags.get(key) in values.split('|')),None)
        if not kind: continue
        places[str(element['id'])]={'id':element['id'],'name':name,'lat':round(lat,6),'lon':round(lon,6),'category':kind}
    print(f'Area {i}: total {len(places)} named places',flush=True)
    time.sleep(2)
if len(places)<30:
    raise SystemExit(f'Only {len(places)} places: refusing to overwrite data')
Path('places.json').write_text(json.dumps(list(places.values()),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(f'Saved {len(places)} places',flush=True)
