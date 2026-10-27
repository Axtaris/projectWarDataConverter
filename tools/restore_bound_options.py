"""Options that only exist inside one detachment (RequiredDettachment) came from the original data and were dropped by the conversion:
a Chaos unit in Pactbound Zealots chooses its Mark, a vehicle in a Headhunter Task Force can be a Tank Ace Character, a Steel Hammer super-heavy can be a Character...
Without them the detachment's enhancements cannot be given to those units. This puts them back from the original data, only when the detachment still exists in
the 11th edition file and the unit is still there, and copies the wargear definitions they need.
usage: python -I -X utf8 tools/restore_bound_options.py <data dir> <original data dir> [--write]"""
import glob, json, os, re, sys, collections
args = [x for x in sys.argv[1:] if not x.startswith('--')]; write = '--write' in sys.argv
cur_dir, base_dir = args[0], args[1]
def k(s): return re.sub(r'[^a-z0-9]+', ' ', str(s).lower().replace('’', "'")).strip()
tot = collections.Counter(); notes = []
for f in sorted(glob.glob(os.path.join(cur_dir, '*.json'))):
    n = os.path.basename(f)
    if n in ('DataInfo.json', 'FactionInfoData.json') or 'Legends' in n: continue
    bp = os.path.join(base_dir, n)
    if not os.path.exists(bp): continue
    cur = json.load(open(f, encoding='utf-8')); base = json.load(open(bp, encoding='utf-8-sig'))
    dets = {d['Name'] for d in cur.get('Dettachments', [])}; bu = {u['Name']: u for u in base.get('Units', [])}; ch = False
    for u in cur['Units']:
        b = bu.get(u['Name'])
        if not b: continue
        for bm in b['UnitComposition']['ModelCompositions']:
            for bg in bm.get('Wargear') or []:
                for o in bg.get('Options', []):
                    det = o.get('RequiredDettachment')
                    if det and det not in dets: tot['detachment not in the current file'] += 1; continue
                    if not det:   # a plain option that offers wargear definitions (a Mark, a vox-caster, a banner) the conversion left defined but not offered
                        dk = {k(d['Key']) for d in u['UnitComposition'].get('WargearDefinitions', []) if any(d.get(x) for x in ('StatAdjustments', 'WeaponAdjustments', 'DatasheetAdjustments', 'Cost', 'GrantsAbilities'))}
                        names = [k(x) for x in o.get('Options', [])]
                        offered = {k(x) for m_ in u['UnitComposition']['ModelCompositions'] for g_ in (m_.get('Wargear') or []) for o_ in g_.get('Options', []) for x in o_.get('Options', [])} | {k(x) for m_ in u['UnitComposition']['ModelCompositions'] for g_ in (m_.get('Wargear') or []) for x in g_.get('InitalWargear', [])}
                        if not names or not all(x in dk for x in names) or any(x in offered for x in names): continue
                        dm = {k(d['Key']): d for d in u['UnitComposition'].get('WargearDefinitions', [])}
                        gr = lambda ns: {k(g) for x in ns for g in (dm.get(x, {}).get('GrantsAbilities') or [])}
                        if gr(names) and gr(names) <= gr([x for x in dm if x in offered]): continue   # the same ability is already offered another way (Simulacrum Imperialis)
                    tm = next((m for m in u['UnitComposition']['ModelCompositions'] if k(m['ModelName']) == k(bm['ModelName'])), None) or u['UnitComposition']['ModelCompositions'][0]
                    if not tm.get('Wargear'): tm['Wargear'] = [{'InitalWargear': [], 'Options': []}]
                    tg = tm['Wargear'][0]
                    if any(x.get('RequiredDettachment') == det and [k(a) for a in x.get('Options', [])] == [k(a) for a in o.get('Options', [])] for x in tg.get('Options', [])): tot['already there'] += 1; continue
                    tot['bound to a detachment' if det else 'plain definition options'] += 1
                    tg.setdefault('Options', []).append(json.loads(json.dumps(o)))
                    defs = u['UnitComposition'].setdefault('WargearDefinitions', []); have = {k(d['Key']) for d in defs}
                    for a in o.get('Options', []):
                        if k(a) not in have:
                            src = next((d for d in b['UnitComposition'].get('WargearDefinitions', []) if k(d['Key']) == k(a)), None)
                            if src: defs.append(json.loads(json.dumps(src))); have.add(k(a))
                    tot['restored'] += 1; ch = True; notes.append((n[:16], u['Name'], det, o['Options']))
    if write and ch: json.dump(cur, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(dict(tot))
for x in notes[:int(os.environ.get('N', 12))]: print('  ', x)
