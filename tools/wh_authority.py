"""Last pass: Wahapedia (11th edition) is the authority for what it publishes.
The three-way comparator keeps a value when BSData agrees with it, and BSData still lags behind (10th), so stale 10th values
survived as "OK". This pass forces, for every unit found in Wahapedia: stat lines, ability names and ability texts.
usage: python -I -X utf8 tools/wh_authority.py <data dir> [--write] [--only "Space Wolves"]   (dry run unless --write)"""
import argparse, html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wh_load
from wh_load import table, key as k, clean, deshout
ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--write', action='store_true'); ap.add_argument('--only'); ap.add_argument('--show', action='store_true'); a = ap.parse_args()
SM = 'SM,AoI,QI,TL'
F = {'Necrons': 'NEC', 'Adeptus Custodes': 'AC,AoI,QI,TL', 'Space Marines': SM, 'Adepta Sororitas': 'AS', 'Adeptus Mechanicus': 'AdM', 'Astra Militarum': 'AM', 'Grey Knights': 'GK',
     'Imperial Agents': 'AoI', 'Imperial Knights': 'QI', 'Aeldari': 'AE', 'Drukhari': 'DRU', 'Chaos Daemons': 'CD', 'Chaos Knights': 'QT', 'Chaos Space Marines': 'CSM', 'Death Guard': 'DG',
     "Emperor's Children": 'EC', 'Thousand Sons': 'TS', 'World Eaters': 'WE', 'Genestealer Cults': 'GC', 'Leagues of Votann': 'LoV', 'Orks': 'ORK', 'Tau Empire': 'TAU', 'Tyranids': 'TYR'}
for c in ('Black Templars', 'Blood Angels', 'Dark Angels', 'Deathwatch', 'Space Wolves', 'Imperial Fists', 'Iron Hands', 'Raven Guard', 'Salamanders', 'Ultramarines', 'White Scars'): F[c] = SM
def an(s): return k(re.sub(r'\([^)]*\)', ' ', s))
def flat(s): return re.sub(r'\W+', '', s.lower())
DS, MOD, ABL = table('Datasheets'), table('Datasheets_models'), table('Datasheets_abilities')
ABIL = {r['id']: r for r in table('Abilities')}
ALLAB = collections.defaultdict(list)
for r in ABL: ALLAB[r['datasheet_id']].append(r)
KW = {}
for r in table('Datasheets_keywords'): KW.setdefault(r['datasheet_id'], set()).add(k(r['keyword']))
CHAPTERS = {k(c) for c in ('Black Templars', 'Blood Angels', 'Dark Angels', 'Deathwatch', 'Space Wolves', 'Imperial Fists', 'Iron Hands', 'Raven Guard', 'Salamanders', 'Ultramarines', 'White Scars')}
STAT = (('Movement', 'M'), ('Toughness', 'T'), ('Save', 'Sv'), ('Wounds', 'W'), ('Leadership', 'Ld'), ('OC', 'OC'))
def ek_norm(x): return re.sub(r' (upgrade|one per army|aura)$', '', k(x))
UPG = {}
for r in table('Enhancements'): UPG[(ek_norm(r['detachment']), ek_norm(r['name']))] = UPG.get((ek_norm(r['detachment']), ek_norm(r['name'])), False) or r['upgrade'] == 'true'
total = 0
for name, fids in F.items():
    if a.only and a.only != name: continue
    path = os.path.join(a.dir, name + '.json')
    if not os.path.exists(path): continue
    doc = json.load(open(path, encoding='utf-8')); ids = set(fids.split(','))
    ds = {r['id']: r for r in DS if r['faction_id'] in ids}; cand = {}
    for i, r in ds.items(): cand.setdefault(k(r['name']), []).append(i)
    # a name can exist twice (generic datasheet and chapter-specific one): chapter files take their own, everyone else the one without a chapter keyword
    rank = lambda i: (k(name) not in KW.get(i, ()), bool(KW.get(i, set()) & CHAPTERS)) if k(name) in CHAPTERS else (bool(KW.get(i, set()) & CHAPTERS),)
    by = {n: min(l, key=rank) for n, l in cand.items()}
    mods, abl = {}, {}
    for r in MOD:
        if r['datasheet_id'] in ds: mods.setdefault(r['datasheet_id'], []).append(r)
    for r in ABL:
        if r['datasheet_id'] in ds and r['name']: abl.setdefault(r['datasheet_id'], []).append(r)
    log = []
    for u in doc['Units']:
        i = by.get(k(u['Name']))
        if not i: continue
        # stats: only when both sides have the same number of distinct lines; model order follows Wahapedia's line number
        seen, wl = set(), []
        for m in sorted(mods.get(i, []), key=lambda m: int(m['line'] or 0)):
            t = tuple(m[x] for _, x in STAT)
            if t not in seen: seen.add(t); wl.append(m)
        if len(wl) == len(u.get('StatLines', [])) == 1:   # several lines carry no model name here, so they cannot be told apart safely
            for s, m in zip(u['StatLines'], wl):
                for f, x in STAT:
                    n = m[x].strip()
                    if n and n != '-' and s.get(f) != n and re.sub(r'\W', '', str(s.get(f))) != re.sub(r'\W', '', n): log.append(f"{u['Name']}: {f} {s.get(f)} -> {n}"); s[f] = n
        # abilities
        wa = {}
        for r in sorted(abl.get(i, []), key=lambda r: int(r['line'] or 0)): wa.setdefault(an(r['name']), r)
        mine = {an(x['Title']): x for x in u['UnitAbilities']}
        for t, r in wa.items():
            text = deshout(clean(r['description'], bullets=True)); title = re.sub(r'\s*\(psychic level \d+\)', ' (Psychic)', r['name'].strip(), flags=re.I)
            if t in mine:
                if flat(mine[t]['Text']) != flat(text):
                    log.append(f"{u['Name']}: text {mine[t]['Title']}" + (f"\n        old: {mine[t]['Text'][:200]!r}\n        new: {text[:200]!r}" if a.show else '')); mine[t]['Text'] = text
            else: log.append(f"{u['Name']}: + {title}"); u['UnitAbilities'].append({'Title': title, 'Text': text})
        added = sum(1 for t in wa if t not in mine)   # an ability only we have goes when Wahapedia added one under another name (a rename); otherwise it may be curated, so it stays
        # Character / Epic Hero keywords decide who may be the Warlord; Wahapedia's "cannot / must be your Warlord" text decides the flags (bit 1 cannot, bit 2 must)
        have = {k(x) for x in u['Keywords']}
        for kwd in ('Character', 'Epic Hero'):
            if k(kwd) in KW.get(i, ()) and k(kwd) not in have: log.append(f"{u['Name']}: keyword + {kwd}"); u['Keywords'].append(kwd)
        wtxt = ' '.join(re.sub(r'<[^>]+>', '', html.unescape(r['description'] or ABIL.get(r['ability_id'], {}).get('description', ''))).lower() for r in ALLAB.get(i, []))   # core/faction abilities are only referenced by id (Last Survivor...)
        bits = (1 if re.search(r'cannot (?:be selected (?:to be|as) |be )?your warlord', wtxt) else 0) | (2 if 'must be your warlord' in wtxt else 0)
        if (u.get('Flags', 0) & 3) != bits:
            log.append(f"{u['Name']}: warlord flags {u.get('Flags', 0) & 3} -> {bits}"); u['Flags'] = (u.get('Flags', 0) & ~3) | bits
            if not u['Flags']: u.pop('Flags')
        for t, x in list(mine.items()):
            if t not in wa and wa and added > 0: added -= 1; log.append(f"{u['Name']}: - {x['Title']}"); u['UnitAbilities'].remove(x)
    # enhancements flagged "upgrade" by Wahapedia are the ones plain units (not only Characters) can take: the app reads that from Features
    for d in doc.get('Dettachments', []):
        for e in d.get('Enhancements', []):
            ek = (ek_norm(d['Name']), ek_norm(e['Name']))
            if UPG.get(ek) and 'Upgrade' not in (e.get('Features') or ''):
                log.append(f"{d['Name']} / {e['Name']}: Upgrade feature"); e['Features'] = ','.join(x for x in (e.get('Features'), 'Upgrade') if x)
    print(f'{name}: {len(log)} changes'); total += len(log)
    for l in log: print('   ', l if a.show else l[:140])
    if a.write and log: json.dump(doc, open(path, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('total', total)
