"""Apply the three-way decisions to a projectWar faction file, keeping everything is curated by hand that no source provides
(special abilities, flags, base types, wargear stat adjustments, leader abilities, enhancement effects, ...).
Only fields the comparator judged UPDATE / UPDATE* are touched; OK and REVIEW values stay as they are.
usage: python -X utf8 tools/apply.py --name <WO name> --wh <ids> --mfm <yaml> [--alias ...] [--out-dir data_new]
Reads data/<name>.json (current) and data_bsd/<name>.json (converted); writes <out-dir>/<name>.json and <out-dir>/<name>.changes.txt."""
import argparse, copy, json, os, re, runpy, sys
ap = argparse.ArgumentParser(); ap.add_argument('--name', required=True); ap.add_argument('--wh', required=True); ap.add_argument('--mfm', required=True)
ap.add_argument('--alias', default=''); ap.add_argument('--src', default='baseline'); ap.add_argument('--out-dir', default='data_new'); a = ap.parse_args()
sys.argv = ['three_way.py', '--name', a.name, '--wh', a.wh, '--mfm', a.mfm, '--out', os.path.join(a.out_dir, '_cmp.md'), '--alias', a.alias, '--wo-dir', a.src]
os.makedirs(a.out_dir, exist_ok=True)
G = runpy.run_path('tools/three_way.py', run_name='tw')           # the comparator's state: sources, canonical forms, per-item verdicts
k, an, WH, WHG = G['k'], G['an'], G['WH'], G
wo_doc = json.load(open(f'{a.src}/{a.name}.json', encoding='utf-8-sig')); bs_doc = json.load(open(f'data_bsd/{a.name}.json', encoding='utf-8'))  # wo_doc is always the pristine backup, so re-running gives the same result
BSU = {k(u['Name']): u for u in bs_doc['Units']}
DEC = {}  # canonical unit name -> field -> rows
for f, lst in G['items'].items():
    for uname, vd, rows in lst: DEC.setdefault(k(uname), {})[f] = rows
changes = []
def log(u, msg): changes.append(f"{u['Name']}: {msg}")

import difflib
def canon(raw, u):
    """map a wargear name from a source onto the unit's own weapon / definition name (hyphens, typos: 'special issue bolt pistol' -> 'special-issue bolt pistol')"""
    names = {k(w['Name']): w['Name'].lower() for g in u['Weapons'] for w in g['Weapons']}
    names.update({k(d['Key']): d['Key'] for d in u['UnitComposition'].get('WargearDefinitions', [])})
    if k(raw) in names: return names[k(raw)]
    m = difflib.get_close_matches(k(raw), list(names), n=1, cutoff=0.86)
    return names[m[0]] if m else raw
# ---------------- Wahapedia raw -> projectWar format (only needed where Wahapedia wins)
import wh_load
def wh_weapon(r):
    sk = (r['BS_WS'] or '').strip(); rng = (r['range'] or '').strip()
    w = {'Name': r['name']}
    kw = re.sub(r'<[^>]+>', '', r['description'] or '').strip()
    if kw: w['Keywords'] = kw.upper()
    w.update({'Range': rng if rng.lower() == 'melee' else (rng + '"' if rng and not rng.endswith('"') else rng), 'Attacks': r['A'], 'ToHit': (sk + '+' if sk.isdigit() else 'N/A'), 'Strength': r['S'], 'AP': r['AP'], 'Damage': r['D']})
    return w
def wkey(name, rng): return k(name) + ('~m' if str(rng).strip().lower() == 'melee' else '~r')  # same weapon name can exist as a ranged and a melee profile
def wh_id(key):
    bn = key if key in G['BS'] else G['alias'].get(key); return WH.get(bn) or WH.get(key)

def pick(vd, b, h):  # which source supplies the new value
    return 'wh' if vd == 'UPDATE*' else 'bs'

applied = copy.deepcopy(wo_doc); out_units = []
for u in applied['Units']:
    key = k(u['Name']); dec = DEC.get(key, {})
    if key in G['RETIRED_SET']: log(u, 'unit retired in 11th (not in Wahapedia nor the MFM): removed'); continue
    if not dec: out_units.append(u); continue
    bn = key if key in BSU else G['alias'].get(key); b = BSU.get(bn) if bn else None; hid = wh_id(key)
    if b and bn != key and b['Name'] != u['Name']: log(u, f"renombrada a {b['Name']}"); u['Name'] = b['Name']; u['Keywords'] = [next((x for x in b['Keywords'] if k(x) == bn), x) if k(x) == key else x for x in u['Keywords']]  # renamed in the 11th edition codex (the unit-name keyword follows)
    # ----- points: MFM-backed, replace whole
    if 'points' in dec and b: u['Points'] = b['Points']; log(u, 'points')
    # ----- stats
    for f, kind in (('stats', 'stats'), ('base', 'base')):
        rows = dec.get(f)
        if not rows: continue
        vd = rows[0][1]
        if f == 'stats':
            if vd == 'UPDATE*' and hid:
                ms = {}
                for m in WHG['mod'][hid]: ms[(m['M'], m['T'], m['Sv'], m['W'], m['Ld'], m['OC'], m['inv_sv'])] = m
                for i, m in enumerate(ms.values()):
                    if i < len(u['StatLines']):
                        s = u['StatLines'][i]; s.update({'Movement': m['M'], 'Toughness': m['T'], 'Save': m['Sv'], 'Wounds': m['W'], 'Leadership': m['Ld'], 'OC': m['OC']})
                        if m['inv_sv'] in ('-', ''): s.pop('InvulSave', None)
                        else: s['InvulSave'] = {'Save': m['inv_sv']}
            elif b:
                bl = b['StatLines']
                if len(bl) == len(u['StatLines']):
                    for s, t in zip(u['StatLines'], bl):
                        for fld in ('Movement', 'Toughness', 'Save', 'Wounds', 'Leadership', 'OC'): s[fld] = t[fld]
                        if t.get('InvulSave'): s['InvulSave'] = t['InvulSave']
                        else: s.pop('InvulSave', None)
                else:
                    u['StatLines'] = [{**t, **({'BaseInfo': u['StatLines'][min(i, len(u['StatLines']) - 1)].get('BaseInfo')} if u['StatLines'][min(i, len(u['StatLines']) - 1)].get('BaseInfo') else {})} for i, t in enumerate(bl)]
            log(u, f'stats ({vd})')
        else:
            src = b['StatLines'] if (b and vd != 'UPDATE*') else None
            for i, s in enumerate(u['StatLines']):
                size = None
                if src is not None and i < len(src): size = (src[i].get('BaseInfo') or {}).get('Size')
                elif hid:
                    ms = [m for m in WHG['mod'][hid] if re.sub(r'\D', '', m['base_size'])]
                    if i < len(ms): size = re.sub(r'(\d+(?:\.\d+)?).*', r'\1', ms[i]['base_size'].replace('mm', ''))
                if size: s.setdefault('BaseInfo', {})['Size'] = size
            log(u, f'base ({vd})')
    # ----- keywords
    rows = dec.get('keywords')
    if rows:
        have = {k(x): x for x in u['Keywords']}
        for key2, vd, vw, vb, vh, _ in rows:
            tgt = vh if vd == 'UPDATE*' else vb
            if tgt == 1 and key2 not in have:
                raw = next((x for x in (b['Keywords'] if b else []) if k(x) == key2), None) or next((r['keyword'] for r in WHG['kw'][hid] if k(r['keyword']) == key2), None) if hid else None
                raw = raw or next((x for x in (b['Keywords'] if b else []) if k(x) == key2), key2.title())
                u['Keywords'].append(raw); log(u, f'keyword + {raw}')
            elif tgt == '∅' and key2 in have: u['Keywords'].remove(have[key2]); log(u, f'keyword − {have[key2]}')
    # ----- weapons
    rows = dec.get('weapons')
    if rows:
        bw = {wkey(w['Name'], w['Range']): w for g in (b['Weapons'] if b else []) for w in g['Weapons']}
        hw = {wkey(r['name'], r['range']): r for r in (WHG['wg'][hid] if hid else [])}
        for key2, vd, vw, vb, vh, _ in rows:
            if vd == 'REVIEW': continue
            tgt = vh if vd == 'UPDATE*' else vb
            new = None
            if tgt not in ('∅', None):
                new = wh_weapon(hw[key2]) if vd == 'UPDATE*' and key2 in hw else bw.get(key2)
                if new is None: continue
            where = [(g, i) for g in u['Weapons'] for i, w in enumerate(g['Weapons']) if wkey(w['Name'], w['Range']) == key2]
            if where:
                g, i = where[0]
                if new is None: g['Weapons'].pop(i); log(u, f'arma − {key2}')
                else: g['Weapons'][i] = new; log(u, f'arma ~ {new["Name"]}')
            elif new is not None:
                melee = new['Range'].lower() == 'melee'
                g = next((x for x in u['Weapons'] if bool(x.get('IsMelee')) == melee), None)
                if g is None:
                    g = {'Name': 'MELEE WEAPONS' if melee else 'RANGED WEAPONS', 'Weapons': []}
                    if melee: g['IsMelee'] = True
                    u['Weapons'].append(g)
                g['Weapons'].append(new); log(u, f'arma + {new["Name"]}')
        u['Weapons'] = [g for g in u['Weapons'] if g['Weapons']]
    # ----- abilities (presence and text)
    pres, txt = dec.get('abilities') or [], dec.get('ability text') or []
    if pres or txt:
        by = {an(x['Title']): x for x in u['UnitAbilities']}
        bab = {an(x['Title']): x for x in (b['UnitAbilities'] if b else [])}
        whab = {an(r['name']): r for r in (WHG['ab'][hid] if hid else []) if r['name']}
        def wtext(key2):
            r = whab.get(key2); return wh_load.deshout(wh_load.clean(r['description'], bullets=True)) if r else None
        for key2, vd, vw, vb, vh, _ in pres:
            if vd == 'REVIEW': continue
            tgt = vh if vd == 'UPDATE*' else vb
            if tgt == '∅' and key2 in by: u['UnitAbilities'].remove(by[key2]); log(u, f'habilidad − {by[key2]["Title"]}')
            elif tgt == 1 and key2 not in by:
                src = bab.get(key2); title = src['Title'] if src else (whab[key2]['name'] if key2 in whab else key2.title())
                u['UnitAbilities'].append({'Title': title, 'Text': wtext(key2) or (src or {}).get('Text', '')}); log(u, f'habilidad + {title}')
        by = {an(x['Title']): x for x in u['UnitAbilities']}
        for key2, vd, vw, vb, vh, _ in txt:
            if vd == 'REVIEW' or key2 not in by: continue
            t = wtext(key2) or (bab.get(key2) or {}).get('Text')
            if t and t != by[key2]['Text']: by[key2]['Text'] = t; log(u, f'text {by[key2]["Title"]}')
    # ----- composition: edit the dataset's structure item by item (its defaults / replaces / limits stay unless a source says otherwise)
    comp_rows = {f: [r for r in dec.get(f, []) if r[1] in ('UPDATE', 'UPDATE*')] for f in ('size', 'initial gear', 'offered gear', 'replaced gear')}
    if b and any(comp_rows.values()):
        mcs = u['UnitComposition']['ModelCompositions']; bcs = b['UnitComposition']['ModelCompositions']
        # size
        for r in comp_rows['size']:
            tgt = r[4] if r[1] == 'UPDATE*' else r[3]
            if tgt and len(mcs) == 1 and tgt[1] > 1:
                mcs[0]['Limit'] = {'Min': tgt[0], 'Max': tgt[1]}; log(u, f'size {tgt[0]}-{tgt[1]}')
            elif tgt and len(mcs) == len(bcs):
                for m, bm in zip(mcs, bcs):
                    if bm.get('Limit'): m['Limit'] = dict(bm['Limit'])
                log(u, 'size (per model)')
            elif tgt and len(mcs) == 1 and tgt[1] == 1: mcs[0].pop('Limit', None)
        blocks = [w for m in mcs for w in m.get('Wargear', [])]
        if not blocks and mcs: mcs[0]['Wargear'] = [{'InitalWargear': [], 'Options': []}]; blocks = mcs[0]['Wargear']
        whl = G['wh_init_raw'](hid) if hid else {}
        # initial equipment
        for key2, vd, vw, vb, vh, _ in comp_rows['initial gear']:
            tgt = vh if vd == 'UPDATE*' else vb
            for w in blocks:
                cur = [x for x in w['InitalWargear'] if G['item'](x) == key2]
                if tgt == '∅':
                    for x in cur: w['InitalWargear'].remove(x); log(u, f'initial gear - {x}')
                elif tgt == 1 and not cur and w is blocks[0]:
                    raw = canon(whl.get(key2) or key2, u); w['InitalWargear'].append(raw); log(u, f'initial gear + {raw}')
        # offered / replaced items
        bopts = [o for m in bcs for w in m.get('Wargear', []) for o in w.get('Options', [])]
        for key2, vd, vw, vb, vh, _ in comp_rows['offered gear']:
            tgt = vh if vd == 'UPDATE*' else vb
            if tgt == '∅':
                for w in blocks:
                    for o in list(w['Options']):
                        o['Options'] = [x for x in o.get('Options', []) if all(G['item'](p2) != key2 for p2 in re.split(' and ', x))]
                        if not o['Options']: w['Options'].remove(o)
                log(u, f'offered gear - {key2}')
            elif tgt == 1:
                have_items = {G['item'](p2) for w in blocks for o in w['Options'] for x in o.get('Options', []) for p2 in re.split(' and ', x)}
                if key2 in have_items: continue
                src = next((o for o in bopts if any(G['item'](x) == key2 for x in o.get('Options', []))), None)
                if src:
                    new = {kk: vv for kk, vv in src.items() if kk != 'Options'}; new['Options'] = [x for x in src['Options'] if G['item'](x) not in have_items or G['item'](x) == key2]
                    blocks[0]['Options'].append(copy.deepcopy(new))
                else: blocks[0]['Options'].append({'Options': [key2]})
                log(u, f'offered gear + {key2}')
        for key2, vd, vw, vb, vh, _ in comp_rows['replaced gear']:
            tgt = vh if vd == 'UPDATE*' else vb
            if tgt == '∅':
                for w in blocks:
                    for o in w['Options']:
                        if 'Replaces' in o:
                            o['Replaces'] = [x for x in o['Replaces'] if G['item'](x) != key2]
                            if not o['Replaces']: o.pop('Replaces')
                log(u, f'replaced gear - {key2}')
        # wargear definitions: costs / granted abilities of the converted unit are added, curated fields stay
        old_defs = {d['Key']: d for d in u['UnitComposition'].get('WargearDefinitions', [])}
        for d in b['UnitComposition'].get('WargearDefinitions', []):
            o = old_defs.get(d['Key'])
            if o is None: u['UnitComposition'].setdefault('WargearDefinitions', []).append(d)
            else:
                for kk in ('Cost', 'GrantsAbilities'):
                    if kk in d: o[kk] = d[kk]
    # ----- leaders
    rows = dec.get('leaders')
    if rows and b and b.get('LeaderInfo') and u.get('LeaderInfo') is not None:
        names = list(u['LeaderInfo'].get('UnitNames', []))
        for key2, vd, vw, vb, vh, _ in rows:
            if vd == 'REVIEW': continue
            tgt = vh if vd == 'UPDATE*' else vb
            cur = next((x for x in names if k(x) == key2), None)
            if tgt == '∅' and cur: names.remove(cur); log(u, f'leader - {cur}')
            elif tgt == 1 and not cur:
                names.append(next((x for x in b['LeaderInfo']['UnitNames'] if k(x) == key2), key2.upper())); log(u, f'leader + {key2}')
        u['LeaderInfo']['UnitNames'] = names
    # ----- final pass: wargear names must match the unit's own weapon names after renames (hyphens / spelling), and no duplicates
    wn = {k(w['Name']): w['Name'] for g in u['Weapons'] for w in g['Weapons']}
    def fix(x, lower):
        if ' and ' in x and k(x) not in wn: return x
        m = [k(x)] if k(x) in wn else difflib.get_close_matches(k(x), list(wn), n=1, cutoff=0.92)
        return (wn[m[0]].lower() if lower else wn[m[0]]) if m else x
    for m in u['UnitComposition']['ModelCompositions']:
        for w in m.get('Wargear', []):
            w['InitalWargear'] = list(dict.fromkeys(fix(x, True) for x in w['InitalWargear']))
            for o in w.get('Options', []):
                if 'Replaces' in o: o['Replaces'] = list(dict.fromkeys(fix(x, True) for x in o['Replaces']))
                o['Options'] = list(dict.fromkeys(fix(x, False) for x in o.get('Options', [])))
    out_units.append(u)
applied['Units'] = out_units
# ----- units that exist only in the converted data (new in the 11th edition codex): add as converted
have = {k(u['Name']) for u in applied['Units']}; alias_to = set(G['alias'].values())
for kk, bu in BSU.items():
    mfn = {k(m['name']) for m in G['MF'].get('units', [])}
    other_wo = set()
    if a.name == 'Space Marines':  # chapter units (Deathwatch kill teams...) live in the chapter files, not in the base file
        import glob
        for f in glob.glob(a.src + '/*.json'):
            if os.path.basename(f)[:-5] not in ('Space Marines', 'Space Marines Legends') and 'Legends' not in f:
                try: other_wo |= {k(x['Name']) for x in json.load(open(f, encoding='utf-8-sig'))['Units']}
                except Exception: pass
    if kk not in have and kk not in alias_to and kk not in G['LEG'] and (kk in WH or kk in mfn) and kk not in other_wo: applied['Units'].append(bu); changes.append(f"{bu['Name']}: new unit")
# ----- detachments and army rules come from the converted file (MFM list + Wahapedia texts + the dataset's curated fields carried over by name)
applied['Dettachments'] = bs_doc['Dettachments'] if bs_doc['Dettachments'] else wo_doc['Dettachments']
applied['ArmyRules'] = bs_doc.get('ArmyRules') or wo_doc['ArmyRules']
json.dump(applied, open(os.path.join(a.out_dir, f'{a.name}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open(os.path.join(a.out_dir, f'{a.name}.changes.txt'), 'w', encoding='utf-8').write('\n'.join(changes) + '\n')
print(f'{a.name}: {len(applied["Units"])} units, {len(changes)} changes -> {a.out_dir}/{a.name}.json')
