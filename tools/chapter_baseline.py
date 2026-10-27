"""Extended baseline for the "codex" chapters (Imperial Fists, Iron Hands, Raven Guard, Salamanders, Ultramarines, White Scars).
Their baseline files only hold the chapter's own units; every chapter also fields the whole Space Marines roster, so this adds the shared
units and detachments (with their hand-curated fields) from baseline/Space Marines.json. Writes baseline_ext/<chapter>.json."""
import json, os, re
k = lambda s: re.sub(r'[^a-z0-9]+', ' ', s.replace('\u2019', "'").lower()).strip()
sm = json.load(open('baseline/Space Marines.json', encoding='utf-8-sig'))
os.makedirs('baseline_ext', exist_ok=True)
for name in ('Imperial Fists', 'Iron Hands', 'Raven Guard', 'Salamanders', 'Ultramarines', 'White Scars'):
    doc = json.load(open(f'baseline/{name}.json', encoding='utf-8-sig'))
    have = {k(u['Name']) for u in doc['Units']}; doc['Units'] += [u for u in sm['Units'] if k(u['Name']) not in have]
    have = {k(d['Name']) for d in doc['Dettachments']}; doc['Dettachments'] += [d for d in sm['Dettachments'] if k(d['Name']) not in have]
    json.dump(doc, open(f'baseline_ext/{name}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{name}: {len(doc["Units"])} units, {len(doc["Dettachments"])} detachments in the extended baseline')
