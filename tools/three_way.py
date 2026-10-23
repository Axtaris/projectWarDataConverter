"""Three-way comparator: projectWar (current) vs BSData (converted) vs Wahapedia 11e CSV export, plus the MFM for points and detachments.
For every field of every unit it gives a verdict:
  OK          the current projectWar value is also held by at least one other source
  UPDATE      two or more other sources agree on a value that differs from projectWar  (safe to apply)
  REVIEW     the sources disagree and no value has two supporters                      (check by hand, e.g. on the Wahapedia page)
usage: python -X utf8 tools/three_way.py --name "Adeptus Custodes" --wh AC,AoI,QI,TL --mfm <mfm.yaml> --out informes/custodes.md [--wh-dir DIR]
(reads data/<name>.json, data/<name> Legends.json, data_bsd/<name>.json, data_bsd/<name> Legends.json)"""
import argparse, csv, html, json, os, re, sys
from collections import Counter, defaultdict
ap = argparse.ArgumentParser()
ap.add_argument('--name', required=True); ap.add_argument('--wh', required=True); ap.add_argument('--mfm'); ap.add_argument('--out', required=True)
ap.add_argument('--wh-dir', default='sources/wh')
ap.add_argument('--wo-dir', default='baseline'); ap.add_argument('--alias', default='')  # "WO NAME=OTHER NAME;..." manual renames confirmed elsewhere
a = ap.parse_args(); csv.field_size_limit(10**9)

def k(s): return re.sub(r'[^a-z0-9]+', ' ', html.unescape(str(s)).replace('’', "'").replace('–', ' ').replace(' & ', ' and ').lower()).strip()
def v(s):
    if s in (None, ''): return ''
    x = re.sub(r'\s+', '', html.unescape(str(s)).lower().replace('"', '').replace('+', '').replace('’', "'"))
    x = x.replace('*', '')
    return 'na' if x in ('-', 'n/a', 'na') else x
def T(f): return list(csv.DictReader(open(f'{a.wh_dir}/{f}.csv', encoding='utf-8-sig', newline=''), delimiter='|'))
def txt(s): return k(re.sub(r'<[^>]+>', ' ', html.unescape(s or '')))

# ---------------- load sources
def units(path):
    try: return {k(u['Name']): u for u in json.load(open(path, encoding='utf-8-sig'))['Units']}
    except FileNotFoundError: return {}
def dets(path):
    try: return json.load(open(path, encoding='utf-8-sig')).get('Dettachments', [])
    except FileNotFoundError: return []
N = a.name; WO = units(f'{a.wo_dir}/{N}.json'); BS = units(f'data_bsd/{N}.json')  # Legends are out of scope: they do not change and are not played competitively
fids = set(a.wh.split(','))
ds = {r['id']: r for r in T('Datasheets') if r['faction_id'] in fids}
def grp(f, key='datasheet_id'):
    g = defaultdict(list)
    for r in T(f):
        if r[key] in ds: g[r[key]].append(r)
    return g
mod, kw, wg, ab, cost, comp, opt = (grp(f) for f in ('Datasheets_models', 'Datasheets_keywords', 'Datasheets_wargear', 'Datasheets_abilities', 'Datasheets_models_cost', 'Datasheets_unit_composition', 'Datasheets_options'))
leaders = defaultdict(set)
for r in T('Datasheets_leader'):
    if r['leader_id'] in ds and r['attached_id'] in ds: leaders[r['leader_id']].add(k(ds[r['attached_id']]['name']))
WH = {k(r['name']): i for i, r in ds.items()}
i_loadout = {i: r['loadout'] for i, r in ds.items()}
SRC = {r['id']: r['name'] for r in T('Source')}
LEG = {k(r['name']) for r in ds.values() if 'legends' in SRC.get(r['source_id'], '').lower()}
MF = {}
if a.mfm:
    import yaml; MF = yaml.safe_load(open(a.mfm, encoding='utf-8'))
LEG |= {k(m['name']) for m in MF.get('units', []) if m.get('legends')}
WO = {n: u for n, u in WO.items() if n not in LEG}; BS = {n: u for n, u in BS.items() if n not in LEG}  # Legends are out of scope
MFN = {k(m['name']) for m in MF.get('units', [])}

# ---------------- renames: pair WO units that have no same-named BS unit by content similarity (+ manual aliases)
def sig(u): return ({k(w['Name']) for g in u['Weapons'] for w in g['Weapons']}, {k(x) for x in u['Keywords']}, set(k(u['Name']).split()))
def jac(x, y): return len(x & y) / max(1, len(x | y))
alias = {k(p.split('=')[0]): k(p.split('=')[1]) for p in a.alias.split(';') if '=' in p}
onlyW = [n for n in WO if n not in BS and n not in alias]; poolB = [n for n in BS if n not in WO]
for n in onlyW:
    if not poolB: break
    best = max(poolB, key=lambda m: sum(jac(x, y) * w for x, y, w in zip(sig(WO[n]), sig(BS[m]), (.4, .3, .3))))
    if sum(jac(x, y) * w for x, y, w in zip(sig(WO[n]), sig(BS[best]), (.4, .3, .3))) >= .45: alias[n] = best
# ---------------- canonical extractors
# Whole-value fields are compared as one value; collection fields (keywords, weapons, abilities, leaders) item by item.
WHOLE = ['stats', 'base', 'points', 'size']; COLL = ['keywords', 'weapons', 'abilities', 'ability text', 'leaders', 'initial gear', 'offered gear', 'replaced gear']
def an(s): return k(re.sub(r'\([^)]*\)', ' ', html.unescape(str(s))))  # ability name without (Aura) / (Once per battle...) suffixes
def own(name, kws): return [x for x in kws if k(x) != k(name)]  # the unit's own name is a keyword in some sources only
def item(x):  # a piece of wargear without quantity words, plural or case: "2 particle beamers" -> "particle beamer"
    x = re.sub(r'^(any number of|up to|\d+|one|two|three|1|2)\s+', '', k(x)); x = re.sub(r'^(\d+|one|two)\s+', '', x)
    return ' '.join(w[:-1] if w.endswith('s') and len(w) > 3 else w for w in x.split())
def wo_init(u):
    return {item(x): 1 for m in u['UnitComposition']['ModelCompositions'] for g in m.get('Wargear', []) for x in g['InitalWargear'] for x in re.split(' and ', x)}
def wh_init(i):
    """Wahapedia's loadout line: 'Every model is equipped with: 1 Guardian Spear.' / '1 Combi-bolter; 1 Contemptor Fist'"""
    t = html.unescape(i_loadout[i]); t = re.sub(r'<br\s*/?>', ';', t); t = re.sub(r'<[^>]+>', '', t); out = {}
    for part in t.split(';'):
        if ':' in part: part = part.split(':', 1)[1]
        part = part.strip(' .')
        if k(part): out[item(part)] = 1
    return out
def wh_init_raw(i):
    t = html.unescape(i_loadout[i]); t = re.sub(r'<br\s*/?>', ';', t); t = re.sub(r'<[^>]+>', '', t); out = {}
    for part in t.split(';'):
        if ':' in part: part = part.split(':', 1)[1]
        part = part.strip(' .')
        if k(part): out[item(part)] = re.sub(r'^(?:\d+|one|two|three)\s+', '', part.strip()).lower()
    return out
def wo_opts(u):
    off, rep_ = {}, {}
    for m in u['UnitComposition']['ModelCompositions']:
        for w in m.get('Wargear', []):
            for o in w.get('Options', []):
                for r in o.get('Replaces', []) or []: rep_[item(r)] = 1
                for it in o.get('Options', []) or []:
                    for part in re.split(' and ', it): off[item(part)] = 1  # the dataset lists some combined choices as 'X and Y'
    return off, rep_
def wo_size(u):
    mc = u['UnitComposition']['ModelCompositions']
    return [sum((m.get('Limit') or {}).get('Min', 1) for m in mc), sum((m.get('Limit') or {}).get('Max', 1) for m in mc)]
def wh_opts(i):
    off, rep_ = {}, {}
    for r in opt[i]:
        d = html.unescape(r['description']); lis = re.findall(r'<li[^>]*>(.*?)</li>', d, re.S); t = re.sub(r'<[^>]+>', ' ', d); t = re.sub(r'\s+', ' ', t).strip()
        m = re.search(r"(?:model.s|models.|unit.s|^|each have their|have their)\s*(.+?)\s+(?:can|may) be replaced", t) or re.search(r"(?:have their|replace)\s+(.+?)\s+replaced", t)
        if m:
            for x in re.split(r'\s+and\s+|,\s*', re.sub(r"^(?:all models in this unit can each have their|this model.s|this unit.s|each model.s|any number of models can each have their)\s+", '', m.group(1), flags=re.I)):
                if k(x): rep_[item(x)] = 1
        if lis: items = lis
        else:
            m2 = re.search(r'(?:replaced with|equipped with|can have|can take)\s+(.+?)\.?$', t)
            items = re.split(r'\s+and\s+|,\s*', m2.group(1)) if m2 else []
        for x in items:
            x = re.sub(r'^(?:one of the following:?)\s*', '', x.strip())
            if k(x) and 'replaced' not in x and 'following' not in x.lower(): off[item(x)] = 1
    return off, rep_
def wh_size(i):
    lo = hi = 0
    for r in comp[i]:
        m = re.match(r'\s*(\d+)(?:\s*-\s*(\d+))?\s', r['description'] or '')
        if not m: return None
        lo += int(m.group(1)); hi += int(m.group(2) or m.group(1))
    return [lo, hi] if comp[i] else None
def wo_fields(u):
    st = sorted(set((v(s['Movement']), v(s['Toughness']), v(s['Save']), v(s['Wounds']), v(s['Leadership']), v(s['OC']), v((s.get('InvulSave') or {}).get('Save'))) for s in u['StatLines']))
    base = sorted({re.sub(r'\D', '', str((s.get('BaseInfo') or {}).get('Size', '')).split('x')[0]) for s in u['StatLines'] if (s.get('BaseInfo') or {}).get('Size')})
    wp = {k(w['Name']) + ('~m' if v(w['Range']) == 'melee' else '~r'): (v(w['Range']), v(w['Attacks']), v(w['ToHit']), v(w['Strength']), v(w['AP']), v(w['Damage']), tuple(sorted(k(x) for x in w.get('Keywords', '').split(',') if k(x)))) for g in u['Weapons'] for w in g['Weapons']}
    pts = sorted({(p['ModelCount'], p['Cost']) for p in u['Points'] if p.get('Cost')})
    return {'stats': st, 'base': base, 'points': pts, 'keywords': {k(x): 1 for x in own(u['Name'], u['Keywords'])}, 'weapons': wp, 'abilities': {an(x['Title']): 1 for x in u['UnitAbilities']},
            'ability text': {an(x['Title']): txt(x['Text']) for x in u['UnitAbilities']}, 'leaders': {k(n): 1 for n in (u.get('LeaderInfo') or {}).get('UnitNames', []) or []},
            'size': wo_size(u), 'initial gear': wo_init(u), 'offered gear': wo_opts(u)[0], 'replaced gear': wo_opts(u)[1]}
def wh_fields(i):
    st = sorted(set((v(m['M']), v(m['T']), v(m['Sv']), v(m['W']), v(m['Ld']), v(m['OC']), v('' if m['inv_sv'] in ('-', '') else m['inv_sv'])) for m in mod[i]))
    base = sorted({re.sub(r'\D', '', m['base_size'].split('x')[0]) for m in mod[i] if re.sub(r'\D', '', m['base_size'])})
    wp = {k(w['name']) + ('~m' if v(w['range']) == 'melee' else '~r'): (v(w['range']), v(w['A']), v(w['BS_WS']), v(w['S']), v(w['AP']), v(w['D']), tuple(sorted(k(x) for x in re.sub(r'<[^>]+>', '', w['description']).split(',') if k(x)))) for w in wg[i]}
    pts = []
    for r in cost[i]:
        m = re.match(r'(\d+)', r['description'] or '')
        if m and (r['cost'] or '').isdigit(): pts.append((int(m.group(1)), int(r['cost'])))
    abil = [x for x in ab[i] if x['type'] in ('Datasheet', 'Wargear', 'Special (правая колонка)', 'Primarch', 'Fortification (левая колонка)') and x['name']]
    return {'stats': st, 'base': base, 'points': sorted(set(pts)), 'keywords': {k(x): 1 for x in own(ds[i]['name'], [y['keyword'] for y in kw[i] if y['is_faction_keyword'] != 'true'])}, 'weapons': wp,
            'abilities': {an(x['name']): 1 for x in abil}, 'ability text': {an(x['name']): txt(x['description']) for x in abil}, 'leaders': {n: 1 for n in leaders.get(i, [])},
            'size': wh_size(i), 'initial gear': wh_init(i), 'offered gear': wh_opts(i)[0], 'replaced gear': wh_opts(i)[1]}
def mf_points(name):
    for m in MF.get('units', []):
        if k(m['name']) == name: return sorted({(q['models'], q['points']) for p in m['pricing'] for q in p['costs']})
    return None

FIELDS = WHOLE + COLL
res = {f: Counter() for f in FIELDS}; items = {f: [] for f in FIELDS}; missing = {'bs': [], 'wh': []}
def verdict(w, others):
    others = [(n, x) for n, x in others if x is not None]
    if not others: return 'NO SOURCES'
    c = Counter(json.dumps(x, sort_keys=True, default=str) for _, x in others); cnt = c.most_common(1)[0][1]
    if json.dumps(w, sort_keys=True, default=str) in c: return 'OK'
    if w and all(not x for _, x in others): return 'REVIEW'  # the other sources hold no value: absence is not evidence
    return 'UPDATE' if cnt >= 2 else 'REVIEW'
RETIRED_SET = {n for n in WO if n not in WH and n not in MFN and alias.get(n) not in WH and alias.get(n) not in MFN}  # not in Wahapedia nor in the MFM: no longer a unit of the 11th edition
RANK = {'OK': 0, 'NO SOURCES': 0, 'UPDATE': 1, 'UPDATE*': 2, 'REVIEW': 3}
for n, u in WO.items():
    if n in RETIRED_SET: continue
    bn = n if n in BS else alias.get(n); hn = (bn if bn in WH else (n if n in WH else None))
    if hn is None and bn: hn = WH.get(bn)
    f_w = wo_fields(u); f_b = wo_fields(BS[bn]) if bn else None; f_h = wh_fields(WH[hn]) if hn else None
    if not bn: missing['bs'].append(u['Name'])
    if not hn: missing['wh'].append(u['Name'])
    for f in WHOLE:
        w = f_w[f]; b = f_b[f] if f_b else None; h = f_h[f] if f_h else None
        m = [tuple(x) for x in mf_points(k(BS[bn]['Name'] if bn else n)) or []] or None if f == 'points' else None
        vd = verdict(w, [('BSData', b), ('Wahapedia', h), ('MFM', m)])
        if vd == 'REVIEW' and h not in (None, [], '∅'): vd = 'UPDATE*'  # sources disagree: policy = Wahapedia wins, listed for spot check
        res[f][vd] += 1
        if vd in ('UPDATE', 'UPDATE*', 'REVIEW'): items[f].append((u['Name'], vd, [(f, vd, w, b, h, m)]))
    for f in COLL:
        w, b, h = f_w[f], (f_b[f] if f_b else None), (f_h[f] if f_h else None)
        rows = []; worst = 'OK' if (b is not None or h is not None) else 'NO SOURCES'
        for key in sorted(set(w) | set(b or {}) | set(h or {})):
            vw = w.get(key); vb = None if b is None else b.get(key, '∅'); vh = None if h is None else h.get(key, '∅')
            vd = verdict(vw if vw is not None else '∅', [('BSData', vb), ('Wahapedia', vh)])
            if f == 'initial gear' and vh is not None: vd = 'OK' if vh == (vw if vw is not None else '∅') else 'UPDATE*'  # the loadout line is an explicit statement: Wahapedia wins
            if vd == 'REVIEW' and vh not in (None, '∅'): vd = 'UPDATE*'  # sources disagree: policy = Wahapedia wins (it matched projectWar in most checks; BSData had typos and truncations), listed for spot check
            if vd in ('UPDATE', 'UPDATE*', 'REVIEW'):
                rows.append((key, vd, vw if vw is not None else '∅', vb, vh, None))
                if RANK[vd] > RANK[worst]: worst = vd
        res[f][worst] += 1
        if rows: items[f].append((u['Name'], worst, rows))
# ---------------- detachments
def det_rows():
    out = []
    wd = {k(d['Name']): d for d in dets(f'{a.wo_dir}/{N}.json')}; bd = {k(d['Name']): d for d in dets(f'data_bsd/{N}.json')}
    wh_d = {r['id']: r for r in T('Detachments') if r['faction_id'] in fids and r['dp']}
    whd = {k(r['name']): r for r in wh_d.values()}
    enh = defaultdict(dict)
    for r in T('Enhancements'):
        if r['detachment_id'] in wh_d: enh[k(wh_d[r['detachment_id']]['name'])][k(re.sub(r'\s*\(.*\)$', '', r['name']))] = int(r['cost'] or 0)
    strat = defaultdict(set)
    for r in T('Stratagems'):
        if r['detachment_id'] in wh_d: strat[k(wh_d[r['detachment_id']]['name'])].add(k(r['name']))
    md = {k(d['name']): d for d in MF.get('detachments', [])}
    for n in sorted(set(wd) | set(whd) | set(md)):
        row = {'name': (wd.get(n, {}).get('Name') or md.get(n, {}).get('name') or whd[n]['name']), 'WO': n in wd, 'WH': n in whd, 'MFM': n in md}
        if n in wd: row['wo_dp'] = wd[n].get('Cost') or 1; row['wo_enh'] = {k(re.sub(r'\s*\(.*\)$', '', e['Name'])): e.get('Cost', 0) for e in wd[n].get('Enhancements', [])}; row['wo_strat'] = {k(s['Name']) for s in wd[n].get('Stratagems', [])}
        if n in whd: row['wh_dp'] = int(whd[n]['dp']); row['wh_enh'] = enh.get(n, {}); row['wh_strat'] = strat.get(n, set())
        if n in md: row['mfm_dp'] = md[n]['dp']; row['mfm_enh'] = {k(re.sub(r'\s*\(.*\)$', '', e['name'])): e['points'] for e in md[n].get('enhancements', [])}
        out.append(row)
    return out
DR = det_rows()

# ---------------- report
L = []; P = L.append
P(f'# {N}: three-way comparison\n')
P('Sources: **current projectWar data** (baseline/), **BSData** converted (data_bsd/), **Wahapedia 11th** (CSV, ' + open(a.wh_dir + '/Last_update.csv', encoding='utf-8-sig').read().split('\n')[1].strip('| \r') + ') and **MFM** v' + str(MF.get('version', '?')) + ' for points and detachments.')
P('Verdict per field: **OK** (the current value matches another source), **UPDATE** (two or more sources agree on a different value) and **REVIEW** (the sources disagree and no value has two supporters: check by hand).\n')
P(f'Units: current {len(WO)}, BSData {len(BS)}, Wahapedia {len(WH)}. Renames detected by content: ' + (', '.join(f'{WO[x]["Name"].title()} → {BS[y]["Name"].title()}' for x, y in alias.items()) or 'none') + '.')
P('Sin pareja en BSData: ' + (', '.join(x.title() for x in missing['bs']) or 'none') + '. Sin pareja en Wahapedia: ' + (', '.join(x.title() for x in missing['wh']) or 'none') + '.\n')
P('## Summary per field\n\n| Field | OK | UPDATE | UPDATE* (gana Wahapedia) | REVIEW |\n|---|---|---|---|---|')
for f in FIELDS: P(f'| {f} | {res[f]["OK"]} | {res[f]["UPDATE"]} | {res[f]["UPDATE*"]} | {res[f]["REVIEW"]} |')
P('\nUPDATE: two sources agree against the current value. UPDATE*: BSData and Wahapedia disagree and Wahapedia is applied (spot-check at random). REVIEW: only one source differs from the current value, with no support.')
P('\nCurrent units that are no longer in Wahapedia nor the MFM (possibly retired in 11th, excluded from the comparison): ' + (', '.join(WO[x]['Name'].title() for x in sorted(RETIRED_SET)) or 'none') + '.')
def show(x, lim=200):
    return '—' if x is None else str(x)[:lim]
for f in FIELDS:
    if not items[f]: continue
    P(f'\n## {f}: {len(items[f])} units with differences\n')
    for name, vd, rows in sorted(items[f], key=lambda t: (t[1], t[0])):
        P(f'- **{name.title()}** [{vd}]')
        for key, rvd, vw, vb, vh, vm in rows:
            lab = '' if f in WHOLE else f'{key}: '
            P(f'  - {lab}[{rvd}] projectWar {show(vw)}  |  BSData {show(vb)}  |  Wahapedia {show(vh)}' + (f'  |  MFM {show(vm)}' if vm is not None else ''))
P('\n## Destacamentos y mejoras\n')
P('| Detachment | Current | Wahapedia | MFM | Differences |\n|---|---|---|---|---|')
for r in DR:
    d = []
    dps = {'WO': r.get('wo_dp'), 'WH': r.get('wh_dp'), 'MFM': r.get('mfm_dp')}
    if len({x for x in dps.values() if x is not None}) > 1: d.append('DP ' + ' / '.join(f'{kk} {vv}' for kk, vv in dps.items() if vv is not None))
    for src in ('wh', 'mfm'):
        if r.get('wo_enh') is not None and r.get(src + '_enh') is not None and 'wo_enh' in r:
            e1, e2 = r['wo_enh'], r[src + '_enh']
            for x in e1.keys() ^ e2.keys(): d.append(f'enhancement {x.title()} only in {"current" if x in e1 else src.upper()}')
            for x in e1.keys() & e2.keys():
                if e1[x] != e2[x]: d.append(f'{x.title()} {e1[x]}→{e2[x]} ({src.upper()})')
    if 'wo_strat' in r and 'wh_strat' in r:
        for x in r['wo_strat'] ^ r['wh_strat']: d.append(f'stratagem {x.title()} only in {"current" if x in r["wo_strat"] else "Wahapedia"}')
    P(f'| {r["name"]} | {"yes" if r["WO"] else "-"} | {"yes" if r["WH"] else "-"} | {"yes" if r["MFM"] else "-"} | {"; ".join(dict.fromkeys(d)) or "—"} |')
os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
open(a.out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print(a.out, {f: dict(res[f]) for f in FIELDS})
