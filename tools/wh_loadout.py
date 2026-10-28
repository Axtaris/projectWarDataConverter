"""Starting wargear of every model straight from Wahapedia's loadout text ("Every Boy is equipped with: Choppa; Shoota; Slugga.").
A model row is updated only when its starting items differ from the loadout and the row can be told apart by name ("Every model" / "This model" give the same items to every row).
Items keep the names of the unit's own weapon profiles; an item without a profile (a shield, a banner) is kept as written, in lower case.
usage: python -I -X utf8 tools/wh_loadout.py <data dir> [--write] [--report FILE]"""
import argparse, collections, glob, html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wh_load import table, key as k
ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--write', action='store_true'); ap.add_argument('--report'); a = ap.parse_args()
CHAPTERS = {k(c) for c in ('Black Templars', 'Blood Angels', 'Dark Angels', 'Deathwatch', 'Space Wolves', 'Imperial Fists', 'Iron Hands', 'Raven Guard', 'Salamanders', 'Ultramarines', 'White Scars')}
SM = 'SM,AoI,QI,TL'
F = {'Necrons': 'NEC', 'Adeptus Custodes': 'AC,AoI,QI,TL', 'Space Marines': SM, 'Adepta Sororitas': 'AS', 'Adeptus Mechanicus': 'AdM', 'Astra Militarum': 'AM', 'Grey Knights': 'GK', 'Imperial Agents': 'AoI', 'Imperial Knights': 'QI', 'Aeldari': 'AE', 'Drukhari': 'DRU', 'Chaos Daemons': 'CD', 'Chaos Knights': 'QT', 'Chaos Space Marines': 'CSM', 'Death Guard': 'DG', "Emperor's Children": 'EC', 'Thousand Sons': 'TS', 'World Eaters': 'WE', 'Genestealer Cults': 'GC', 'Leagues of Votann': 'LoV', 'Orks': 'ORK', 'Tau Empire': 'TAU', 'Tyranids': 'TYR'}
for c in ('Black Templars', 'Blood Angels', 'Dark Angels', 'Deathwatch', 'Space Wolves', 'Imperial Fists', 'Iron Hands', 'Raven Guard', 'Salamanders', 'Ultramarines', 'White Scars'): F[c] = SM
DS = table('Datasheets'); KW = collections.defaultdict(set)
for r in table('Datasheets_keywords'): KW[r['datasheet_id']].add(k(r['keyword']))
def sing(s):
    s = k(html.unescape(s).replace('’', '').replace("'", '')); return ' '.join(re.sub(r'(?<=[a-z]{2})[sz]$', '', re.sub(r'ies$', 'y', w)) for w in s.split())
def inorm(x):
    x = k(html.unescape(x).replace('’', '').replace("'", '').replace('&', ' and ')); x = re.sub(r'\band\b', ' ', x); x = re.sub(r'^\d+ ', '', re.sub(r'\s+', ' ', x)).strip()
    return ' '.join(re.sub(r'(?<=[a-z]{2})s$', '', w) for w in x.split())
def parse(lo):
    t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(lo or ''))).strip(); out = []
    for m in re.finditer(r'(?:(?:The|Every|This|Each)\s+)?(.+?)\s+(?:is|are) equipped with:\s*([^.]+?)(?:\.(?=\s|$)|$)', t):
        out.append((m.group(1).strip(), [x.strip(' .') for x in m.group(2).split(';') if x.strip(' .')]))
    return out
def datasheet(u, name):
    fids = set(F.get(name, '').split(',')); cand = [r for r in DS if k(r['name']) == k(u['Name']) and (not fids - {''} or r['faction_id'] in fids)] or [r for r in DS if k(r['name']) == k(u['Name'])]
    if not cand: return None
    rank = lambda r: ((k(name) not in KW[r['id']], bool(KW[r['id']] & CHAPTERS)) if k(name) in CHAPTERS else (bool(KW[r['id']] & CHAPTERS),))
    return min(cand, key=rank)
tot = collections.Counter(); rep = []
for f in sorted(glob.glob(os.path.join(a.dir, '*.json'))):
    name = os.path.basename(f)[:-5]
    if name in ('DataInfo', 'FactionInfoData') or 'Legends' in name: continue
    doc = json.load(open(f, encoding='utf-8')); ch = False
    for u in doc['Units']:
        r = datasheet(u, name)
        if not r: continue
        lo = parse(r['loadout'])
        if not lo: tot['no loadout text'] += 1; continue
        weap = {}
        for g in u['Weapons']:
            for w in g['Weapons']: weap.setdefault(inorm(w['Name']), w['Name'])
        mcs = u['UnitComposition']['ModelCompositions']; want = {}; clash = set()
        for subj, items in lo:
            s = re.sub(r'^(?:the|every|each|one|1|other)\s+', '', subj, flags=re.I); gen = k(s) in ('model', 'unit') or k(s).startswith('model')
            exact = [m for m in mcs if sing(m['ModelName']) == sing(s)]
            rows = mcs if gen else exact or [m for m in mcs if sing(s) in sing(m['ModelName']) or sing(m['ModelName']) in sing(s)]
            if not rows: rep.append((name, u['Name'], f'no model row for "{subj}"')); tot['unmatched subject'] += 1; continue
            if not gen and not exact and len(rows) > 1: rep.append((name, u['Name'], f'"{subj}" fits several rows')); tot['ambiguous subject'] += 1; continue
            res = []
            for it in items:
                c = re.match(r'^(\d+)\s+(.+)$', it); cnt, base = (int(c.group(1)), c.group(2)) if c else (1, it)
                key = inorm(base); nm_ = weap.get(key) or next((v for kk, v in weap.items() if kk.startswith(key + ' ')), None)
                nm_ = (re.sub(r'\s*–.*$', '', nm_) if nm_ and not weap.get(key) else nm_) if nm_ else None
                text = nm_ or base.strip().lower()
                res.append((f'{cnt} {text}' if cnt > 1 else text))
            for m in rows:
                if id(m) in want and sorted(set(inorm(x) for x in want[id(m)][1])) != sorted(set(inorm(x) for x in res)): clash.add(id(m))
                want[id(m)] = (m, res)
        for m, res in want.values():
            if id(m) in clash: rep.append((name, u['Name'], f"{m['ModelName']}: several different loadouts for one row, left as it is")); tot['row with several loadouts'] += 1; continue
            w0 = (m.get('Wargear') or [{}])[0]; cur = w0.get('InitalWargear', [])
            if sorted(set(inorm(x) for x in cur)) == sorted(set(inorm(x) for x in res)): continue
            if not m.get('Wargear'): m['Wargear'] = [{'InitalWargear': [], 'Options': []}]
            m['Wargear'][0]['InitalWargear'] = res; ch = True; tot['rows updated'] += 1
            rep.append((name, u['Name'], f"{m['ModelName']}: {cur} -> {res}"))
    if ch and a.write: json.dump(doc, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(dict(tot))
if a.report:
    with open(a.report, 'w', encoding='utf-8') as fh:
        fh.write('# Starting wargear changes and cases not understood\n\n')
        for n_, u_, t_ in rep: fh.write(f'- {n_}: **{u_}**: {t_}\n')
