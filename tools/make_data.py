"""Write the website's schedule data (docs/data/fly, river, amigo, site .json) from engine output.

Usage (from the repo root):
    python tools/make_data.py data/engine_out.json docs/data

fleet.json, amigoset.json, sva.json and meta.json are edited by hand.
"""
import json, sys, os

HEAD = {
    'fly': ['Vessel', 'Voy #', 'Depart POM', 'ETA Aiambak', 'CFO (L)', 'Transferred to', 'To river vessels (L)',
            'To Amigo 1 (L)', 'ETA Kiunga (river)', 'Lead time POM→Kiunga (days)', 'Load start POM',
            'Depart Aiambak (empty)', 'ETA POM (return)', 'Extra wait at Aiambak (h)'],
    'river': ['Vessel', 'Loaded at', 'Loaded from', 'Load start', 'Depart', 'ETA Kiunga', 'CFO (L)', 'ETA Aiambak (return)', 'Discharge start'],
    'amigo': ['Date', 'CFO in from Fly (L)', 'Filled from Amigo 1 (L)', 'Closing stock (L)', 'Waiting aboard Fly vessels (L)',
              'Fly vessels arriving', 'River vessels loading', 'Trucks sent to Kiunga (L)'],
    'site': ['Date', 'River arrivals (L)', 'Truck arrivals (L)', 'Site use (L)', 'Closing stock (L)', 'Days of fuel',
             'Status', 'Lowest during day (L)'],
}

def main(src, outdir):
    e = json.load(open(src, encoding='utf-8'))
    for name, head in HEAD.items():
        rows = [head] + e[name]
        doc = {'value': {'rows': {str(i + 1): r for i, r in enumerate(rows)}}}
        with open(os.path.join(outdir, name + '.json'), 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))
        print(name, len(rows) - 1, 'rows')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
