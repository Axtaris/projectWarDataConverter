"""Points straight from the official Munitorum Field Manual (the yaml scraped from the Warhammer Community MFM, 11th edition).
Units whose Points differ from the yaml are set to the yaml's pricing (model counts, and the cost of the 1st-2nd / 3rd+ copy). Nothing else is touched; Legends are skipped.
usage: python -I -X utf8 tools/mfm_points.py <data dir> <yaml dir> [--write]"""
import glob, json, os, re, sys, yaml
write = '--write' in sys.argv; args = [x for x in sys.argv[1:] if not x.startswith('--')]; data, ydir = args[0], args[1]
k = lambda s: re.sub(r'[^a-z0-9]+', ' ', str(s).replace('’', "'").lower()).strip()
def mfm_points(mu):
    prs = mu['pricing']; uc = lambda r: (lambda a, b: int(b) if b else int(a))(*re.match(r'\[(\d+),(\d*)', r).groups())
    return [({'UnitCount': uc(p['range'])} if len(prs) > 1 else {}) | {'ModelCount': q['models'], 'Cost': q['points']} for p in prs for q in p['costs']]
srt = lambda ps: sorted((p.get('UnitCount') or 0, p['ModelCount'], p['Cost']) for p in ps)
files = {k(os.path.basename(f)[:-5]): f for f in glob.glob(os.path.join(data, '*.json'))}
tot = 0
for y in sorted(glob.glob(os.path.join(ydir, '*.yaml'))):
    doc = yaml.safe_load(open(y, encoding='utf-8')); f = files.get(k(doc.get('name', '')))
    if not f: print('no data file for', doc.get('name')); continue
    d = json.load(open(f, encoding='utf-8')); by = {k(u['Name']): u for u in d['Units']}; ch = False
    for mu in doc['units']:
        u = by.get(k(mu['name']))
        if not u or mu.get('legends'): continue
        mp = mfm_points(mu)
        if any(len({q['models'] for q in pr['costs']}) != len(pr['costs']) for pr in mu['pricing']): print('  skipped (two prices for the same model count):', mu['name']); continue   # our Points cannot tell the variants apart
        if srt(mp) != srt(u['Points']):
            print(f"  {os.path.basename(f)[:-5]} | {u['Name']}: {[(p.get('UnitCount'), p['ModelCount'], p['Cost']) for p in u['Points']]} -> {[(p.get('UnitCount'), p['ModelCount'], p['Cost']) for p in mp]}")
            u['Points'] = mp; ch = True; tot += 1
    if ch and write: json.dump(d, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(tot, 'units' + (' updated' if write else ' differ'))
