import json
from pathlib import Path
from engine import AspaDatabase, CheckInput, check

ROOT = Path(__file__).parent
data = json.loads((ROOT/'dataset.json').read_text())
db = AspaDatabase(data['records'], set(data.get('missing', [])))
fixtures = json.loads((ROOT/'fixtures.json').read_text())
failures = []
for f in fixtures:
    inp = CheckInput(f['local_as'], f['neighbor_as'], f['relationship'], f['as_path'], f.get('as_sets', False), f.get('neighbor_augmented', False), f.get('route_server_client', False))
    got = check(inp, db).status
    if got != f['expected']:
        failures.append((f['id'], f['expected'], got, f['description']))
print(f'{len(fixtures)-len(failures)}/{len(fixtures)} fixtures passed')
if failures:
    for x in failures: print('FAIL', x)
    raise SystemExit(1)
