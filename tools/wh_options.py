"""Wargear options straight from the printed datasheets (Wahapedia 11th edition, Datasheets_options.csv).
BSData's option groups are inferred and differ from the datasheet in many units, so for every unit whose option sentences all parse cleanly,
the options are rebuilt from the sentences. A unit is left untouched (and listed) when any sentence cannot be understood, when the model that
a sentence talks about cannot be told apart, or when an offered weapon has no profile in the unit.
usage: python -I -X utf8 tools/wh_options.py <data dir> [--write] [--only "Black Templars"] [--units "KASRKIN,TEMPESTUS SCIONS"] [--report FILE]
On every run, notes that were read as starting wargear ("this unit can only contain 2 ... if it also contains 8 ...") are removed from the starting wargear."""
import argparse, csv, html, json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wh_load import table, key as k
ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--write', action='store_true'); ap.add_argument('--only'); ap.add_argument('--report'); ap.add_argument('--units', help='comma-separated unit names (upper case): rebuild only these'); a = ap.parse_args()
CHAPTERS = {k(c) for c in ('Black Templars', 'Blood Angels', 'Dark Angels', 'Deathwatch', 'Space Wolves', 'Imperial Fists', 'Iron Hands', 'Raven Guard', 'Salamanders', 'Ultramarines', 'White Scars')}
SM = 'SM,AoI,QI,TL'
F = {'Necrons': 'NEC', 'Adeptus Custodes': 'AC,AoI,QI,TL', 'Space Marines': SM, 'Adepta Sororitas': 'AS', 'Adeptus Mechanicus': 'AdM', 'Astra Militarum': 'AM', 'Grey Knights': 'GK', 'Imperial Agents': 'AoI',
     'Imperial Knights': 'QI', 'Aeldari': 'AE', 'Drukhari': 'DRU', 'Chaos Daemons': 'CD', 'Chaos Knights': 'QT', 'Chaos Space Marines': 'CSM', 'Death Guard': 'DG', "Emperor's Children": 'EC', 'Thousand Sons': 'TS',
     'World Eaters': 'WE', 'Genestealer Cults': 'GC', 'Leagues of Votann': 'LoV', 'Orks': 'ORK', 'Tau Empire': 'TAU', 'Tyranids': 'TYR'}
for c in CHAPTERS: pass
for c in ('Black Templars', 'Blood Angels', 'Dark Angels', 'Deathwatch', 'Space Wolves', 'Imperial Fists', 'Iron Hands', 'Raven Guard', 'Salamanders', 'Ultramarines', 'White Scars'): F[c] = SM
DS, OPT = table('Datasheets'), table('Datasheets_options')
KW = collections.defaultdict(set)
for r in table('Datasheets_keywords'): KW[r['datasheet_id']].add(k(r['keyword']))
opts = collections.defaultdict(list)
for r in OPT: opts[r['datasheet_id']].append(r['description'] or '')
NUM = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}
def fix(s): return html.unescape(s).replace('’', "'").replace('‘', "'").replace(' ', ' ')
def norm(s):
    s = k(fix(s)); s = re.sub(r'^(?:\d+|one|two|three|a|an|the)\s+', '', s); s = re.sub(r'\b(\w+?)s\b', r'\1', s) if False else s
    return re.sub(r'(?<=[a-z])s\b', '', s).strip()
def clean_item(s):
    s = re.sub(r'<[^>]+>', ' ', s); s = fix(s); s = re.sub(r'[*]+', '', s); s = re.sub(r'\s+', ' ', s).strip(' .')
    return s
def split_item(s):  # "1 incinerator and 1 Ancient's banner" -> one combined option "incinerator and Ancient's banner"
    parts = [re.sub(r'^(?:1|one|a|an)\s+', '', p.strip()) for p in re.split(r'\s+and\s+(?=\d|one\b|two\b)', s)]   # a count above one stays ("2 heavy bolters"), like the rest of the data
    return ' and '.join(p for p in parts if p)
RX = re.compile(r"^(?P<pre>.*?)(?:\bcan (?:each )?have (?:their|its|his|her) (?P<r1>.+?) (?:be )?replaced with|['’]s (?P<r2>.+?) can (?:each )?be replaced with|can (?:each )?(?:be )?equipped with|can (?:each )?(?:have|take)\b)\s*(?P<rest>.*)$", re.I | re.S)
def parse_sentence(raw):
    """-> dict(per, max, subj, repl(str|None), items[list of option names]) or None"""
    items = [clean_item(m) for m in re.findall(r'<li[^>]*>(.*?)</li>', raw, re.S)]
    head = re.sub(r'<ul.*?</ul>', ' ', raw, flags=re.S); head = fix(re.sub(r'<[^>]+>', ' ', head)); head = re.sub(r'\s+', ' ', head).strip()
    if not head or head.lower().startswith('none'): return 'skip'
    # footnotes under an option list: limits on repeating a weapon, "that model's X cannot be replaced", "a model cannot have both". They add no option, and used to make the whole unit be left untouched
    if re.match(r"^\*?\s*(?:you cannot select (?:the same weapon|both)|(?:that model['’]s .+|this weapon) cannot be replaced|a model cannot be equipped with more than one)", head, re.I): return 'skip'
    m = RX.match(head)
    if not m: return None
    pre, rest = m.group('pre').strip(), m.group('rest').strip()
    repl = (m.group('r1') or m.group('r2') or '').strip() or None
    per = mx = None; subj = pre
    mm = re.match(r'for every (\d+) models? in (?:this|the) unit,?\s*(.*)$', subj, re.I)
    if mm: per = int(mm.group(1)); subj = mm.group(2)
    mm = re.match(r'(up to )?(\d+|one|two|three|four|five|any number of|all models in this unit|all)\s*(.*)$', subj, re.I)
    anyn = False
    if mm:
        q = mm.group(2).lower()
        if q.startswith('any') or q.startswith('all'): anyn = True
        else: mx = int(q) if q.isdigit() else NUM[q]
        subj = mm.group(3)
    subj = re.sub(r"^(?:the|this)\s+", '', subj.strip(), flags=re.I); subj = re.sub(r"\s*(?:models?|units?)\s*$", '', subj, flags=re.I).strip()
    subj = re.sub(r"\s+(?:equipped with|with)\s.*$", '', subj, flags=re.I)
    if not items:
        one = re.sub(r'\(.*?\)', '', rest); one = clean_item(one)
        mu = re.match(r'^up to (\d+|two|three|four|five|six) (?!of the following)(.+)$', one, re.I)
        if mu and not repl:
            n_ = int(mu.group(1)) if mu.group(1).isdigit() else NUM[mu.group(1).lower()]
            return {'per': None, 'max': None, 'any': False, 'subj': subj, 'repl': None, 'items': [], 'upto': (n_, re.sub(r's$', '', mu.group(2).strip(' .')))}
        one = re.sub(r'^(?:up to \w+ of the following[^:]*|one of the following[^:]*|up to (?:one|two|\d+))\s*:?\s*', '', one, flags=re.I)
        if not one: return None
        items = [x for x in re.split(r',\s+(?=\d|one\b|two\b)', one) if x.strip()]
    if 'duplicate' in head.lower() and 'not allowed' not in head.lower(): pass
    return {'per': per, 'max': mx, 'any': anyn, 'subj': subj, 'repl': repl, 'items': [split_item(i) for i in items if i]}
def process(u, texts, wlib):
    mcs = u['UnitComposition']['ModelCompositions']; why = []
    comp_opts = {i: [] for i in range(len(mcs))}
    for raw in texts:
        p = parse_sentence(raw)
        if p == 'skip': continue
        if p is None: return None, 'unparsed sentence: ' + re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', fix(raw)))[:90]
        # which model composition
        subj = norm(p['subj']) if p['subj'] else ''
        def score(m):
            mn = norm(m['ModelName'])
            return 3 if mn == subj else 2 if subj and set(subj.split()) <= set(mn.split()) else 1 if subj and mn in subj else 0
        sc = [score(m) for m in mcs]; best = max(sc) if sc else 0
        cand = [i for i, v in enumerate(sc) if v and v == best]
        if not subj or subj in ('model', 'unit', 'it', 'model'):
            cand = list(range(len(mcs))) if len(mcs) == 1 else [i for i, m in enumerate(mcs) if (m.get('Limit') or {}).get('Max', 1) > 1]
        if len(cand) != 1 and len(mcs) > 1:
            # the sentence names a role (Sergeant, Champion...) shared by several variants: refuse
            return None, f"cannot tell which model '{p['subj']}' is among {[m['ModelName'] for m in mcs][:5]}"
        ci = cand[0] if cand else 0
        init = ((mcs[ci].get('Wargear') or [{}])[0]).get('InitalWargear', [])
        reps = []
        if p['repl']:
            rn = norm(p['repl'])
            for x in init:
                if norm(x) and (norm(x) in rn): reps.append(x)
            if not reps: return None, f"replaced item '{p['repl']}' is not in the starting wargear {init}"
        names = []
        if p.get('upto'):
            nmax, one = p['upto']; r1 = wlib.resolve(u, one)
            if not r1: return None, f"offered item '{one}' has no profile"
            names = [r1] + [f'{n_} {r1}s' for n_ in range(2, nmax + 1)]
            o = {'Options': names}; comp_opts[ci].append(o); continue
        for it in p['items']:
            # resolve against the unit's weapons / definitions; a combo "a and b" resolves part by part
            whole = wlib.resolve_def(u, it)
            if whole: names.append(whole); continue
            parts = [x.strip() for x in it.split(' and ')]; resolved = []
            for part in parts:
                nm = wlib.resolve(u, part)
                if not nm: return None, f"offered item '{part}' has no profile"
                resolved.append(part if re.match(r'^[2-9]\s', part) and not wlib.resolve_def(u, part) else nm)
            names.append(' and '.join(resolved) if len(resolved) > 1 else resolved[0])
        o = {}
        if p['per']: o['PerXModels'] = p['per']; o['Max'] = p['max'] or 1
        elif p['max'] and not p['any']: o['Max'] = p['max']
        if reps: o['Replaces'] = reps
        o['Options'] = names
        comp_opts[ci].append(o)
    return comp_opts, None
class Lib:
    def __init__(self, units): self.units = units; self.by = collections.defaultdict(list)
    def index(self):
        for u in self.units:
            for g in u['Weapons']:
                for w in g['Weapons']: self.by[norm(w['Name'])].append((u, g.get('IsMelee', False), w))
    def resolve_def(self, u, name):
        dn = lambda x: re.sub(r'\s+', ' ', re.sub(r'\band\b', ' ', norm(x))).strip()
        return next((d['Key'] for d in u['UnitComposition'].get('WargearDefinitions', []) if dn(d['Key']) == dn(name)), None)
    def resolve(self, u, name):
        n = norm(name)
        dn = lambda x: re.sub(r'\s+', ' ', re.sub(r'\band\b', ' ', norm(x))).strip()
        for d in u['UnitComposition'].get('WargearDefinitions', []):   # a priced definition keeps its own key ("2 multi-meltas" costs 10)
            if dn(d['Key']) == dn(name): return d['Key']
        own = {norm(w['Name']): w['Name'] for g in u['Weapons'] for w in g['Weapons']}
        defs = {norm(d['Key']): d['Key'] for d in u['UnitComposition'].get('WargearDefinitions', [])}
        for pool in (own, defs):
            if n in pool: return pool[n]
            for kk, v in pool.items():
                if kk.startswith(n + ' ') or n.startswith(kk + ' '): return name   # profile variants ("Plasma pistol - standard / supercharge"): keep the printed name
        if n in self.by:  # the same weapon is printed on another unit of this faction: copy its profile
            src, melee, w = self.by[n][0]
            tgt = next((g for g in u['Weapons'] if bool(g.get('IsMelee', False)) == bool(melee)), None)
            if tgt is None:
                tgt = {'Name': 'MELEE WEAPONS' if melee else 'RANGED WEAPONS', 'Weapons': []}
                if melee: tgt['IsMelee'] = True
                u['Weapons'].append(tgt)
            tgt['Weapons'].append(json.loads(json.dumps(w))); return w['Name']
        return None
rep = []; tot = collections.Counter()
for name, fids in F.items():
    if a.only and a.only != name: continue
    path = os.path.join(a.dir, name + '.json')
    if not os.path.exists(path): continue
    doc = json.load(open(path, encoding='utf-8')); ids = set(fids.split(',')); ch = False
    ds = {r['id']: r for r in DS if r['faction_id'] in ids}; cand = collections.defaultdict(list)
    for i, r in ds.items(): cand[k(r['name'])].append(i)
    rank = lambda i: ((k(name) not in KW[i], bool(KW[i] & CHAPTERS)) if k(name) in CHAPTERS else (bool(KW[i] & CHAPTERS),))
    NOTE = lambda x: len(x) > 70 or x.endswith('.') or ' this ' in x or ' unit ' in x   # a sentence of the datasheet, not an item
    for u in doc['Units']:
        for m in u['UnitComposition']['ModelCompositions']:
            for wg in m.get('Wargear') or []:
                keep = [x for x in wg.get('InitalWargear', []) if not NOTE(x)]
                if len(keep) != len(wg.get('InitalWargear', [])): wg['InitalWargear'] = keep; ch = True; tot['notes removed from starting wargear'] += 1
    lib = Lib(doc['Units']); lib.index()
    for u in doc['Units']:
        if a.units and u['Name'] not in {x.strip() for x in a.units.split(',')}: continue
        l = cand.get(k(u['Name']))
        if not l: tot['no datasheet'] += 1; continue
        i = min(l, key=rank); texts = opts.get(i, [])
        if not [t for t in texts if parse_sentence(t) != 'skip']: tot['no options printed'] += 1; continue
        before = json.dumps([m.get('Wargear') for m in u['UnitComposition']['ModelCompositions']], sort_keys=True)
        snap = json.loads(json.dumps(u))
        res, why = process(u, texts, lib)
        if res is not None:   # never lose a priced option: a definition with a cost must still be offered after the rebuild
            def reach(unit, optsets):
                out = set()
                for ci, m in enumerate(unit['UnitComposition']['ModelCompositions']):
                    out |= {k(x) for x in ((m.get('Wargear') or [{}])[0]).get('InitalWargear', [])}
                    for o in optsets[ci]:
                        for x in o.get('Options', []): out.add(k(x)); out |= {k(p_) for p_ in x.split(' and ')}
                return out
            was = reach(snap, [((m.get('Wargear') or [{}])[0]).get('Options', []) for m in snap['UnitComposition']['ModelCompositions']]); now = reach(u, [res[ci] for ci in range(len(res))])
            lost = [d['Key'] for d in u['UnitComposition'].get('WargearDefinitions', []) if d.get('Cost') and k(d['Key']) in was and k(d['Key']) not in now]
            if lost: res, why = None, f'would drop the priced option {lost[0]}'
        if res is None:
            u.clear(); u.update(snap); tot['left untouched'] += 1; rep.append((name, u['Name'], why)); continue
        for ci, m in enumerate(u['UnitComposition']['ModelCompositions']):
            if not m.get('Wargear'): m['Wargear'] = [{'InitalWargear': [], 'Options': []}]
            keep = [o for o in m['Wargear'][0].get('Options', []) if set(o) - {'Max', 'PerXModels', 'Replaces', 'Options'}]   # e.g. RequiredDettachment: not on the datasheet, kept
            m['Wargear'][0]['Options'] = res[ci] + keep
        after = json.dumps([m.get('Wargear') for m in u['UnitComposition']['ModelCompositions']], sort_keys=True)
        if before != after or json.dumps(u, sort_keys=True) != json.dumps(snap, sort_keys=True): tot['rebuilt'] += 1; ch = True
        else: tot['already identical'] += 1
    if a.write and ch: json.dump(doc, open(path, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(dict(tot))
if a.report:
    with open(a.report, 'w', encoding='utf-8') as f:
        f.write('# Wargear options left untouched\n\nThese units have option sentences the parser cannot turn into options safely. Review them by hand against the datasheet.\n\n')
        by = collections.defaultdict(list)
        for n, un, w in rep: by[w.split(':')[0]].append((n, un, w))
        for cat, rows in sorted(by.items(), key=lambda x: -len(x[1])):
            f.write(f'\n## {cat} ({len(rows)})\n\n')
            for n, un, w in rows: f.write(f'- {n}: **{un}**: {w}\n')
else:
    for n, un, w in rep[:25]: print('  left:', n, '|', un, '|', w[:150])
