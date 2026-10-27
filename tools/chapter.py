"""Build a chapter file: the whole Space Marines roster (shared units) plus the chapter's own units.
BSData keeps only the chapter-specific entries in the chapter catalogue and imports the rest from the Space Marines catalogue; the MFM chapter yaml
says which shared units the chapter fields and at which points.
usage: chapter.py <chapter name> <mfm chapter yaml or -> <current chapter json>   (reads/writes data_bsd/<name>.json, needs data_bsd/Space Marines.json)"""
import json, re, sys, yaml
name, ymfm, wo_path = sys.argv[1:4]
k = lambda s: re.sub(r'[^a-z0-9]+', ' ', s.replace('’', "'").lower()).strip()
sm = {k(u['Name']): u for u in json.load(open('data_bsd/Space Marines.json', encoding='utf-8'))['Units']}
own_doc = json.load(open(f'data_bsd/{name}.json', encoding='utf-8')); own = {k(u['Name']): u for u in own_doc['Units']}
wo = json.load(open(wo_path, encoding='utf-8-sig'))
review = []
def mfm_points(mu):
    prs = mu['pricing']; uc = lambda r: (lambda a, b: int(b) if b else int(a))(*re.match(r'\[(\d+),(\d*)', r).groups())
    return [({'UnitCount': uc(p['range'])} if len(prs) > 1 else {}) | {'ModelCount': q['models'], 'Cost': q['points']} for p in prs for q in p['costs']]
roster = dict(own)
if ymfm != '-':
    m = yaml.safe_load(open(ymfm, encoding='utf-8'))
    for mu in m['units']:
        if mu.get('legends'): continue
        n = k(mu['name'])
        base = own.get(n) or sm.get(n)
        if not base: review.append(f"{mu['name']}: in the chapter MFM but in no converted catalogue"); continue
        u = json.loads(json.dumps(base)); u['Points'] = mfm_points(mu); roster[n] = u
else:  # chapters without their own MFM file (the "codex" chapters): the whole Space Marines roster at base points, plus their own units
    CHAPTERS = {'black templars', 'blood angels', 'dark angels', 'deathwatch', 'space wolves', 'imperial fists', 'iron hands', 'raven guard', 'salamanders', 'ultramarines', 'white scars'}
    for n, u in sm.items():  # units that carry another chapter's keyword (Deathwatch kill teams, ...) are not shared
        if {k(x) for x in u.get('FactionKeywords', [])} & (CHAPTERS - {k(name)}): continue
        roster.setdefault(n, json.loads(json.dumps(u)))
names = {k(u['Name']) for u in roster.values()}
for u in roster.values():  # leaders can only lead units the chapter actually has
    li = u.get('LeaderInfo')
    if li and li.get('UnitNames'): li['UnitNames'] = [x for x in li['UnitNames'] if k(x) in names]
# detachments: with a chapter yaml they come from it; without one: every Space Marines detachment except the ones locked to another chapter
LOCKED = {'Ultramarines': ['Blade of Ultramar'], 'Imperial Fists': ['Ceramite Sentinels'], 'Salamanders': ['Forgefather\u2019s Seekers'], 'Raven Guard': ['Shadowmark Talon'], 'White Scars': ['Spearpoint Task Force']}
others = {k(d) for c, ds in LOCKED.items() if c != name for d in ds}
dets = own_doc['Dettachments'] if ymfm != '-' else [d for d in own_doc['Dettachments'] if k(d['Name']) not in others]
own_doc['Units'] = list(roster.values()); own_doc['Dettachments'] = dets
json.dump(own_doc, open(f'data_bsd/{name}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(f'data_bsd/{name}.json.review.txt', 'a', encoding='utf-8').write('\n'.join(review) + '\n')
print(f'{name}: {len(own)} own + {len(roster) - len(own)} shared = {len(roster)} units, {len(dets)} detachments ({len(review)} notes)')
