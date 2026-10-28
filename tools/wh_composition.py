"""Unit composition limits of the datasheets listed below, straight from Wahapedia ("1-2 Nob models", "9-18 Boy models").
The audit of every unit (tools/audit: row by row against Datasheets_unit_composition) found only these two with wrong limits: the data allowed 19 Boyz and a single Nob,
so a Boyz unit could reach 20 models with 1 Nob + 19 Boyz, one more Boy than the datasheet allows.
usage: python -I -X utf8 tools/wh_composition.py <data dir> [--write]"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wh_load import table, key as k
write = '--write' in sys.argv; d = [x for x in sys.argv[1:] if not x.startswith('--')][0]
UNITS = {'Orks': ['BOYZ', 'BEAST SNAGGA BOYZ']}
DS = {k(r['name']): r['id'] for r in table('Datasheets') if r['faction_id'] == 'ORK'}; UC = table('Datasheets_unit_composition')
sing = lambda s: re.sub(r'(?<=[a-z]{2})[sz]$', '', k(s))
RX = re.compile(r'^(?:(\d+)\s*-\s*(\d+)|(\d+))\s+(.+?)\s+models?$', re.I)
n = 0
for fname, names in UNITS.items():
    p = os.path.join(d, fname + '.json'); doc = json.load(open(p, encoding='utf-8')); ch = False
    for u in doc['Units']:
        if u['Name'] not in names: continue
        rows = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', r['description'] or '')).strip() for r in UC if r['datasheet_id'] == DS[k(u['Name'])]]
        for t in rows:
            m = RX.match(t)
            if not m: continue
            lo, hi, one, nm = m.groups(); lo = int(lo or one); hi = int(hi or one)
            hit = [mc for mc in u['UnitComposition']['ModelCompositions'] if sing(mc['ModelName']).endswith(sing(nm)) or sing(nm) in sing(mc['ModelName'])]
            if len(hit) != 1: print('  cannot place', t, 'in', u['Name']); continue
            lim = {'Min': lo, 'Max': hi} if (lo, hi) != (1, 1) else None
            if (hit[0].get('Limit') or None) != lim:
                print(f"  {u['Name']}: {hit[0]['ModelName']} {hit[0].get('Limit')} -> {lim}"); n += 1; ch = True
                if lim: hit[0]['Limit'] = lim
                else: hit[0].pop('Limit', None)
    if ch and write: json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(n, 'rows' + (' updated' if write else ' differ'))
