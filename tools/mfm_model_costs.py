"""Units whose Munitorum Field Manual price depends on which models they hold ("3 Wolf Guard Headtakers" 85, "3 Wolf Guard Headtakers, 3 Hunting Wolves" 115,
"6 Wolf Guard Headtakers" 170, "6 Wolf Guard Headtakers, 6 Hunting Wolves" 230): the tier is chosen by the count of one model type (PointsModel) and every
model of the other type adds a fixed cost (ModelCosts). The step is refused for a unit whose prices are not exactly "tier + fixed cost per extra model".
Checked against three sources: the MFM yaml, Wahapedia (Datasheets_models_cost) and New Recruit, which prices the same four builds identically.
usage: python -I -X utf8 tools/mfm_model_costs.py <data dir> <yaml dir> [--write]"""
import glob, json, os, re, sys, yaml
write = '--write' in sys.argv; args = [x for x in sys.argv[1:] if not x.startswith('--')]; data, ydir = args[0], args[1]
k = lambda s: re.sub(r'[^a-z0-9]+', ' ', str(s).replace('’', "'").lower()).strip()
files = {k(os.path.basename(f)[:-5]): f for f in glob.glob(os.path.join(data, '*.json'))}
uc = lambda r: (lambda a, b: int(b) if b else int(a))(*re.match(r'\[(\d+),(\d*)', r).groups())
def parts(desc):   # "3 Wolf Guard Headtakers, 3 Hunting Wolves" -> {"wolf guard headtakers": 3, "hunting wolves": 3}
    return {k(m.group(2)): int(m.group(1)) for m in (re.match(r'^(\d+)\s+(.+)$', x.strip()) for x in desc.split(',')) if m}
n = 0
for y in sorted(glob.glob(os.path.join(ydir, '*.yaml'))):
    doc = yaml.safe_load(open(y, encoding='utf-8')); f = files.get(k(doc.get('name', '')))
    if not f: continue
    d = json.load(open(f, encoding='utf-8')); by = {k(u['Name']): u for u in d['Units']}; ch = False
    for mu in doc['units']:
        u = by.get(k(mu['name']))
        if not u or mu.get('legends') or not all('desc' in q and ',' in q['desc'] or 'desc' in q for pr in mu['pricing'] for q in pr['costs']): continue
        prs = mu['pricing']; multi = len(prs) > 1; base = None; extra = {}; pts = []; ok = True
        for pr in prs:
            tiers = [(parts(q['desc']), q['points']) for q in pr['costs']]
            names = set().union(*[set(t[0]) for t in tiers]); bm = [m for m in names if all(m in t[0] for t in tiers)]
            if len(bm) != 1: ok = False; break
            base = base or bm[0]; ex = [m for m in names if m != base]
            if len(ex) != 1: ok = False; break
            plain = {t[0][base]: t[1] for t in tiers if ex[0] not in t[0]}
            for t in tiers:
                if ex[0] in t[0]:
                    c = (t[1] - plain.get(t[0][base], None)) / t[0][ex[0]] if plain.get(t[0][base]) is not None else None
                    if c is None or c != int(c) or extra.setdefault(ex[0], int(c)) != int(c): ok = False
            pts += [({'UnitCount': uc(pr['range'])} if multi else {}) | {'ModelCount': m, 'Cost': c} for m, c in sorted(plain.items())]
        if not ok or not base: print('  not "tier + fixed cost per model":', mu['name']); continue
        rows = {k(m['ModelName']): m['ModelName'] for m in u['UnitComposition']['ModelCompositions']}
        if base not in rows or any(e not in rows for e in extra): print('  model names differ:', mu['name'], base, list(extra)); continue
        new = {'Points': pts, 'PointsModel': rows[base], 'ModelCosts': [{'ModelName': rows[e], 'Cost': c} for e, c in extra.items()]}
        if any(u.get(a) != b for a, b in new.items()):
            print(f"  {os.path.basename(f)[:-5]} | {u['Name']}: tiers by {rows[base]} {[(p.get('UnitCount'), p['ModelCount'], p['Cost']) for p in pts]}, extra {new['ModelCosts']}")
            u.update(new); ch = True; n += 1
    if ch and write: json.dump(d, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(n, 'units' + (' updated' if write else ' differ'))
