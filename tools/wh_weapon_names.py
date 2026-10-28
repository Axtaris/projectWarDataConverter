"""Weapons that exist on one side only (Wahapedia 11th edition vs the data).
 * a data weapon that is the same weapon under another name (a typo, "Twin iliastus accelerator cannon" -> "Iliastus Accelerator Cannon", "Contemptor combat weapon" -> "Contemptor Fist")
   is renamed to Wahapedia's name, in the profile and in everything that mentions it (starting wargear, options, replaced items, wargear definitions). Two weapons are the same weapon
   when their names are close (ratio >= 0.78) or all their numbers are equal, and there is exactly one candidate.
 * a Wahapedia weapon the unit does not have (the "Hunter" profiles, the War Walker options) is added.
Weapons in the data that Wahapedia no longer has are only listed.
usage: python -I -X utf8 tools/wh_weapon_names.py <data dir> [--write] [--report FILE]"""
import argparse, collections, difflib, glob, html, json, os, re, sys
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
def num(x):
    v = re.sub(r'\s+', '', html.unescape(str(x or ''))).lower().replace('"', '').replace('+', ''); return '' if v in ('-', 'n/a', 'na') else v
def kwfmt(d):
    t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html.unescape(d or ''))).strip(); parts, cur, depth = [], '', 0
    for ch in t:
        if ch == '(': depth += 1
        if ch == ')': depth -= 1
        if ch == ',' and depth == 0: parts.append(cur.strip()); cur = ''
        else: cur += ch
    parts.append(cur.strip()); return ', '.join(p.upper().replace('NON-MONSTER', 'non-MONSTER') for p in parts if p and p != '-')
def prof(r):
    melee = r['type'] == 'Melee'; bs = (r['BS_WS'] or '').strip(); rg = (r['range'] or '').strip()
    p = {'Name': re.sub(r' - ', ' – ', r['name'].strip()).replace('Astareus', 'Astraeus'), 'Range': 'Melee' if melee else (rg + '"' if re.match(r'^\d+$', rg) else rg), 'Attacks': r['A'].strip(), 'ToHit': (bs + '+') if re.match(r'^\d$', bs) else 'N/A', 'Strength': r['S'].strip(), 'AP': r['AP'].strip(), 'Damage': r['D'].strip()}
    kw = kwfmt(r['description'])
    if kw: p['Keywords'] = kw
    return p, melee
def datasheet(u, name):
    fids = set(F.get(name, '').split(',')); cand = [r for r in DS if k(r['name']) == k(u['Name']) and (not fids - {''} or r['faction_id'] in fids)] or [r for r in DS if k(r['name']) == k(u['Name'])]
    if not cand: return None
    rank = lambda r: ((k(name) not in KW[r['id']], bool(KW[r['id']] & CHAPTERS)) if k(name) in CHAPTERS else (bool(KW[r['id']] & CHAPTERS),))
    return min(cand, key=rank)
def rename(u, old, new):
    ref = new.split(' – ')[0] if ' – ' in new else new   # a profile called "X – Hunter" is still the weapon "X" in the wargear
    same = lambda x: isinstance(x, str) and nm(x) == nm(old)
    for m in u['UnitComposition']['ModelCompositions']:
        for w in m.get('Wargear') or []:
            w['InitalWargear'] = [ref.lower() if same(x) else x for x in w.get('InitalWargear', [])]
            for o in w.get('Options', []):
                o['Options'] = [ref if same(x) else x for x in o.get('Options', [])]
                if 'Replaces' in o: o['Replaces'] = [ref.lower() if same(x) else x for x in o['Replaces']]
    for d in u['UnitComposition'].get('WargearDefinitions', []):
        if same(d.get('Key')): d['Key'] = ref
        if 'GrantsWeapons' in d: d['GrantsWeapons'] = [ref if same(x) else x for x in d['GrantsWeapons']]
def stats(w, melee): return (('melee' if melee else num(w.get('Range'))), num(w.get('Attacks')), num(w.get('ToHit')), num(w.get('Strength')), num(w.get('AP')), num(w.get('Damage')))
tot = collections.Counter(); rep = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(a.dir, '*.json'))):
    name = os.path.basename(f)[:-5]
    if name in ('DataInfo', 'FactionInfoData') or 'Legends' in name: continue
    doc = json.load(open(f, encoding='utf-8')); ch = False
    for u in doc['Units']:
        r = datasheet(u, name)
        if not r: continue
        wh = {(nm(x['name']), x['type'] == 'Melee'): x for x in byds.get(r['id'], []) if x['name'].strip()}
        have = {}
        for g in u['Weapons']:
            for w in g['Weapons']: have[(nm(w['Name']), bool(g.get('IsMelee')))] = (g, w)
        miss = [kk for kk in wh if kk not in have]; extra = [kk for kk in have if kk not in wh]
        for kk in list(miss):
            other = (kk[0], not kk[1])
            if other in have and other in extra:   # Wahapedia says melee (or ranged) where the data says the opposite: the weapon moves to the right group
                g, w = have[other]; p, melee = prof(wh[kk]); g['Weapons'].remove(w); grp = next((x for x in u['Weapons'] if bool(x.get('IsMelee')) == melee), None)
                if grp is None:
                    grp = {'Name': 'MELEE WEAPONS' if melee else 'RANGED WEAPONS', 'Weapons': []}
                    if melee: grp['IsMelee'] = True
                    u['Weapons'].append(grp)
                grp['Weapons'].append(w); rep['moved'].append((name, u['Name'], f"{w['Name']} -> {'melee' if melee else 'ranged'}")); tot['moved'] += 1; ch = True; extra.remove(other); miss.remove(kk); continue
            p, melee = prof(wh[kk]); best, bs = None, 0
            near = lambda a_, b_, w_: max(difflib.SequenceMatcher(None, a_, b_).ratio(), 1.0 if stats(w_, melee) == stats(p, melee) else 0, 0.9 if len(a_) >= 6 and len(b_) >= 6 and (a_ in b_ or b_ in a_) else 0)
            for ee in extra:
                if ee[1] != melee: continue
                g, w = have[ee]; sc = near(kk[0], ee[0], w)
                if sc > bs: best, bs = ee, sc
            cnt = [ee for ee in extra if ee[1] == melee and near(kk[0], ee[0], have[ee][1]) >= 0.78]
            if best and bs >= 0.78 and len(cnt) == 1:
                g, w = have[best]; old = w['Name']; rename(u, old, p['Name']); w['Name'] = p['Name']
                rep['renamed'].append((name, u['Name'], f'{old} -> {p["Name"]}')); tot['renamed'] += 1; ch = True; extra.remove(best); miss.remove(kk)
        for kk in miss:
            p, melee = prof(wh[kk])
            grp = next((g for g in u['Weapons'] if bool(g.get('IsMelee')) == melee), None)
            if grp is None:
                grp = {'Name': 'MELEE WEAPONS' if melee else 'RANGED WEAPONS', 'Weapons': []}
                if melee: grp['IsMelee'] = True
                u['Weapons'].append(grp)
            grp['Weapons'].append(p); rep['added'].append((name, u['Name'], p['Name'])); tot['added'] += 1; ch = True
        for ee in extra: rep['only in the data'].append((name, u['Name'], have[ee][1]['Name']))
    if ch and a.write: json.dump(doc, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(dict(tot), {kk: len(v) for kk, v in rep.items()})
if a.report:
    with open(a.report, 'w', encoding='utf-8') as fh:
        fh.write('# Weapon names\n\nrenamed = same weapon under another name; added = in Wahapedia, not in the unit; only in the data = Wahapedia no longer lists it.\n')
        for kind, rows in rep.items():
            fh.write(f'\n## {kind} ({len(rows)})\n\n')
            for n_, u_, w_ in rows: fh.write(f'- {n_}: **{u_}**: {w_}\n')
