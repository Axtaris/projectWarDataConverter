"""Weapon profiles straight from Wahapedia (11th edition, Datasheets_wargear.csv): range, attacks, skill, strength, AP, damage and keywords of every weapon a datasheet has.
Only weapons that already exist on a unit (same name and same kind, melee or ranged, once "&", "and", dashes and plurals are ignored) are updated; names and structure are kept.
Weapons that exist on one side only are listed in the report (they are handled by tools/wh_weapon_names.py).
usage: python -I -X utf8 tools/wh_weapons.py <data dir> [--write] [--report FILE]"""
import argparse, collections, glob, html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wh_load import table, key as k
ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--write', action='store_true'); ap.add_argument('--report'); a = ap.parse_args()
CHAPTERS = {k(c) for c in ('Black Templars', 'Blood Angels', 'Dark Angels', 'Deathwatch', 'Space Wolves', 'Imperial Fists', 'Iron Hands', 'Raven Guard', 'Salamanders', 'Ultramarines', 'White Scars')}
SM = 'SM,AoI,QI,TL'
F = {'Necrons': 'NEC', 'Adeptus Custodes': 'AC,AoI,QI,TL', 'Space Marines': SM, 'Adepta Sororitas': 'AS', 'Adeptus Mechanicus': 'AdM', 'Astra Militarum': 'AM', 'Grey Knights': 'GK', 'Imperial Agents': 'AoI', 'Imperial Knights': 'QI', 'Aeldari': 'AE', 'Drukhari': 'DRU', 'Chaos Daemons': 'CD', 'Chaos Knights': 'QT', 'Chaos Space Marines': 'CSM', 'Death Guard': 'DG', "Emperor's Children": 'EC', 'Thousand Sons': 'TS', 'World Eaters': 'WE', 'Genestealer Cults': 'GC', 'Leagues of Votann': 'LoV', 'Orks': 'ORK', 'Tau Empire': 'TAU', 'Tyranids': 'TYR'}
for c in ('Black Templars', 'Blood Angels', 'Dark Angels', 'Deathwatch', 'Space Wolves', 'Imperial Fists', 'Iron Hands', 'Raven Guard', 'Salamanders', 'Ultramarines', 'White Scars'): F[c] = SM
DS, W = table('Datasheets'), table('Datasheets_wargear')
KW = collections.defaultdict(set)
for r in table('Datasheets_keywords'): KW[r['datasheet_id']].add(k(r['keyword']))
byds = collections.defaultdict(list)
for r in W: byds[r['datasheet_id']].append(r)
def nm(s):
    s = html.unescape(s).replace('’', '').replace("'", '').replace('&', ' and ').replace('–', ' ').replace('-', ' ')
    s = re.sub(r'\band\b', ' ', k(s)).replace('astareus', 'astraeus'); return ' '.join(re.sub(r'(?<=[a-z]{2})s$', '', w) for w in s.split())
def kwfmt(d):
    t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html.unescape(d or ''))).strip()
    parts, cur, depth = [], '', 0
    for ch in t:
        if ch == '(': depth += 1
        if ch == ')': depth -= 1
        if ch == ',' and depth == 0: parts.append(cur.strip()); cur = ''
        else: cur += ch
    parts.append(cur.strip()); return ', '.join(p.upper().replace('NON-MONSTER', 'non-MONSTER') for p in parts if p and p != '-')
kwset = lambda s: sorted(x.strip().upper().replace('’', "'") for x in s.split(',') if x.strip())
def prof(r):
    melee = r['type'] == 'Melee'; bs = (r['BS_WS'] or '').strip(); rg = (r['range'] or '').strip()
    return {'Range': 'Melee' if melee else (rg + '"' if re.match(r'^\d+$', rg) else rg), 'Attacks': r['A'].strip(), 'ToHit': (bs + '+') if re.match(r'^\d$', bs) else 'N/A', 'Strength': r['S'].strip(), 'AP': r['AP'].strip(), 'Damage': r['D'].strip(), 'Keywords': kwfmt(r['description'])}
def datasheet(u, name):
    fids = set(F.get(name, '').split(',')); cand = [r for r in DS if k(r['name']) == k(u['Name']) and (not fids - {''} or r['faction_id'] in fids)] or [r for r in DS if k(r['name']) == k(u['Name'])]
    if not cand: return None
    rank = lambda r: ((k(name) not in KW[r['id']], bool(KW[r['id']] & CHAPTERS)) if k(name) in CHAPTERS else (bool(KW[r['id']] & CHAPTERS),))
    return min(cand, key=rank)
tot = collections.Counter(); rep = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(a.dir, '*.json'))):
    name = os.path.basename(f)[:-5]
    if name in ('DataInfo', 'FactionInfoData') or 'Legends' in name: continue
    doc = json.load(open(f, encoding='utf-8')); ch = False
    for u in doc['Units']:
        r = datasheet(u, name)
        if not r: tot['no datasheet'] += 1; continue
        wh = {(nm(x['name']), x['type'] == 'Melee'): x for x in byds.get(r['id'], [])}
        have = set()
        for g in u['Weapons']:
            for w in g['Weapons']:
                key = (nm(w['Name']), bool(g.get('IsMelee'))); have.add(key)
                if key not in wh: rep['extra'].append((name, u['Name'], w['Name'])); continue
                p = prof(wh[key])
                for x, v in p.items():
                    if x == 'Keywords':
                        if kwset(w.get(x, '')) == kwset(v): continue
                        if v: w[x] = v
                        else: w.pop(x, None)
                    elif w.get(x, '') != v and not (x == 'ToHit' and w.get(x) in ('N/A', '-') and v == 'N/A'): w[x] = v
                    else: continue
                    tot['fields changed'] += 1; tot['field ' + x] += 1; ch = True
        for key, x in wh.items():
            if key not in have: rep['missing'].append((name, u['Name'], x['name']))
    if ch and a.write: json.dump(doc, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(dict(tot), {kk: len(v) for kk, v in rep.items()})
if a.report:
    with open(a.report, 'w', encoding='utf-8') as fh:
        fh.write('# Weapons that exist on one side only\n\nmissing = in Wahapedia, not in the data; extra = in the data, not in Wahapedia.\n')
        for kind, rows in rep.items():
            fh.write(f'\n## {kind} ({len(rows)})\n\n')
            for n_, u_, w_ in rows: fh.write(f'- {n_}: **{u_}**: {w_}\n')
