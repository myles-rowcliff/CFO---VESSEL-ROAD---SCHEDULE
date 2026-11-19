"""Write docs/data/sitesva.json: Tabubil site stock, scheduled (locked 19 Nov plan) vs actual.

Usage (from the repo root):
    python tools/make_sitesva.py

Scheduled closing stock = the locked plan's closing stock (engine/baseline_19nov.json), plus any later
changes made to the scheduled deliveries in docs/data/sva.json (e.g. direct runs to Kiunga, corrections).
"Actual closing stock (L)" is entered by hand and is kept when the file is rebuilt (null = not entered yet).
"""
import json, os

base = json.load(open('engine/baseline_19nov.json'))
sva = json.load(open('docs/data/sva.json'))['value']['rows']
sched = {r[0]: (r[1] or 0) + (r[2] or 0) for k, r in sva.items() if k != '1'}
out = 'docs/data/sitesva.json'
old = {}
if os.path.exists(out):
    for k, r in json.load(open(out))['value']['rows'].items():
        if k != '1': old[r[0]] = r[2]
rows = [['Date', 'Scheduled closing stock (L)', 'Actual closing stock (L)']]
adj = 0
for d, rv, tr, use, close, *_ in base['site']:
    adj += sched.get(d, rv + tr) - (rv + tr)
    rows.append([d, round(close + adj), old.get(d)])
json.dump({'value': {'rows': {str(i + 1): r for i, r in enumerate(rows)}}}, open(out, 'w'), ensure_ascii=False)
print(len(rows) - 1, 'rows')
