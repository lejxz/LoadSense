"""
Fetch public transport route relations from OpenStreetMap Overpass API around Cebu and import into local API.
Usage: venv\Scripts\python.exe tools\fetch_osm_routes.py --bbox "14.58,120.97,14.62,120.99"
If no bbox provided, uses a default Cebu bounding box.
"""
import argparse
import requests
import time

OVERPASS = 'https://overpass-api.de/api/interpreter'
API = 'http://127.0.0.1:8000/api/routes'

parser = argparse.ArgumentParser()
parser.add_argument('--bbox', help='minlat,minlon,maxlat,maxlon', default='14.58,120.97,14.62,120.99')
args = parser.parse_args()
minlat, minlon, maxlat, maxlon = map(float, args.bbox.split(','))

# Query relations with public_transport=platform or route=bus/tram within bbox
query = f"""
[out:json][timeout:25];
(
  relation[route~"bus|tram|trolleybus|subway|light_rail|train"]({minlat},{minlon},{maxlat},{maxlon});
  relation[network~"bus|jeepney|PUV"]({minlat},{minlon},{maxlat},{maxlon});
);
out body;
>;
out skel qt;
"""
print('Querying Overpass...')
r = requests.post(OVERPASS, data={'data': query}, timeout=60)
r.raise_for_status()
data = r.json()
print('Received elements:', len(data.get('elements', [])))

# Build relations -> ways -> nodes mapping
nodes = {}
ways = {}
relations = []
for el in data.get('elements', []):
    if el['type'] == 'node':
        nodes[el['id']] = (el.get('lat'), el.get('lon'))
    elif el['type'] == 'way':
        ways[el['id']] = [nodes.get(n) for n in el.get('nodes', []) if nodes.get(n)]
    elif el['type'] == 'relation':
        members = el.get('members', [])
        # assemble polyline by concatenating way member node coords
        poly = []
        for m in members:
            if m.get('type') == 'way' and m.get('ref') in ways:
                poly.extend(ways[m.get('ref')])
        if not poly:
            # fallback: try tags with stops
            continue
        name = el.get('tags', {}).get('name') or el.get('tags', {}).get('ref') or f"Route {el['id']}"
        route_id = el.get('tags', {}).get('ref') or (el.get('tags', {}).get('name') or str(el['id']))
        relations.append({'route': str(route_id), 'name': name, 'polyline': poly})

print('Found relations with polylines:', len(relations))

# Post to local API
for r in relations:
    payload = {'route': r['route'], 'name': r['name'], 'polyline': [[lat, lon] for lat, lon in r['polyline']]}
    try:
        resp = requests.post(API, json=payload, timeout=10)
        print(resp.status_code, resp.text)
    except Exception as e:
        print('failed to POST', e)
    time.sleep(0.5)

print('Done')
