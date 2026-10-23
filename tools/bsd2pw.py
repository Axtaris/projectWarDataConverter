"""BSData (BattleScribe JSON) -> projectWar faction file. Test converter: writes to a separate folder, never touches data/.

usage: python -I tools/bsd2pw.py --bsd <main catalogue.json> [--lib <other.json> ...] --gs <game system.json>
                                 [--mfm <faction.yaml>] [--wo <current projectWar file>] --out <out.json> [--legends]

Units come from BSData. Points tiers come from BSData modifiers (checked against the MFM when given).
Detachments / enhancements / stratagems / army rules: BSData has no stratagems and no structured effects, so those are MERGED:
costs, DP and rule texts are refreshed from MFM/BSData, curated fields (stratagems, stat/weapon adjustments, requirements) are carried over
from the current projectWar file by name. Anything new is listed in <out>.review.txt."""
import json, os, re, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NB = ' '
PTS = '51b2-306e-1021-d207'
def clean(s): return re.sub(r'\s+', ' ', re.sub(r'\^\^|\*\*', '', (s or '').replace(NB, ' '))).strip()  # drops BSData's ^^**bold^^** markers
def cl(s): return clean(s).replace("'", '’')  # the dataset writes names with a curly apostrophe
def same(a, b): return re.sub(r'[^a-z0-9]+', '', str(a).replace('’', "'").lower()) == re.sub(r'[^a-z0-9]+', '', str(b).replace('’', "'").lower())  # ignores bullets, quotes, case, spacing
def keyn(s): return re.sub(r'[^a-z0-9]+', ' ', str(s).replace('’', "'").lower()).strip()

# ------------------------------------------------------------------ registry across catalogues
class Reg:
    def __init__(self, main, libs, gs):
        self.main = json.load(open(main, encoding='utf-8-sig'))['catalogue']
        self.cats = [self.main] + [json.load(open(p, encoding='utf-8-sig'))['catalogue'] for p in libs]
        self.cats.append(json.load(open(gs, encoding='utf-8-sig'))['gameSystem'])
        self.ent, self.prof, self.rule = {}, {}, {}
        for c in self.cats:
            for k in ('sharedSelectionEntries', 'sharedSelectionEntryGroups'):
                for e in c.get(k, []): self._idx(e)
            for p in c.get('sharedProfiles', []): self.prof[p['id']] = p
            for r in c.get('sharedRules', []): self.rule[r['id']] = r
        self.army_rules = {clean(r['name']) for r in self.main.get('sharedRules', [])}  # rules the faction catalogue itself defines (Reanimation Protocols...)
    def _idx(self, e):
        self.ent[e['id']] = e
        for k in ('selectionEntries', 'selectionEntryGroups'):
            for y in e.get(k, []): self._idx(y)

SKIP_LINKS = {'Tachyon Field Phase Inducer', 'Warlord', 'Detachment', 'Show/Hide Options', 'Order of Battle', 'Crusade'}
def walk(x, reg):
    """x and everything nested in it. Links to shared single entries (e.g. Resurrection orb) are followed; links to shared groups (Weapon Upgrades, Crusade...) are not."""
    if x.get('name') in ('Enhancements', 'Crusade') or x.get('name', '').startswith('Codex ') or cost(x, 'Enhancements'): return  # enhancements / crusade stuff are not part of the datasheet
    yield x
    for k in ('selectionEntries', 'selectionEntryGroups'):
        for y in x.get(k, []): yield from walk(y, reg)
    for l in x.get('entryLinks', []):
        t = reg.ent.get(l.get('targetId')) if l.get('type') == 'selectionEntry' and l.get('name') not in SKIP_LINKS else None
        if t and t.get('type') == 'upgrade': yield from walk(t, reg)

def is_enh(e): return e.get('name') in ('Enhancements', 'Crusade') or e.get('name', '').startswith('Codex ')
def own_walk(x, reg):
    for e in walk(x, reg):
        if not is_enh(e): yield e
def chars(p): return {c['name']: clean(c.get('$text')) for c in p.get('characteristics', [])}
def cost(x, name='pts'):
    for c in x.get('costs', []):
        if c['name'] == name: return c['value']
def sel_constraints(x): return [c for c in x.get('constraints', []) if c.get('field') in (None, 'selections')]
def limit(cs):
    mn = mx = None
    for c in cs:
        if c['type'] == 'min' and mn is None: mn = c['value']
        if c['type'] == 'max' and mx is None: mx = c['value']
    return mn, mx

def link_profiles(x, reg):
    """profiles reached through infoLinks of type 'profile' (e.g. Necrodermis), skipping links hidden by a modifier"""
    out = []
    for l in x.get('infoLinks', []):
        if l.get('type') != 'profile': continue
        if any(m.get('field') == 'hidden' and m.get('type') == 'set' and m.get('value') is True for m in l.get('modifiers', [])): continue
        p = reg.prof.get(l.get('targetId'))
        if p: out.append(p)
    return out

# ------------------------------------------------------------------ unit parts
def stat_lines(x, reg):
    ps, seen = [], set()
    for e in own_walk(x, reg):
        for p in e.get('profiles', []) + link_profiles(e, reg):  # the stat line can be a shared profile linked from the model (Wulfen, Thunderwolf...)
            if p.get('typeName') == 'Unit' and json.dumps([clean(p['name']), chars(p)], sort_keys=True) not in seen: seen.add(json.dumps([clean(p['name']), chars(p)], sort_keys=True)); ps.append(p)  # the same profile repeats on every model entry
    out = []
    for p in ps:
        c = chars(p); s = {'Movement': c.get('M', ''), 'Toughness': c.get('T', ''), 'Save': c.get('Sv', ''), 'Wounds': c.get('W', ''), 'Leadership': c.get('LD', ''), 'OC': c.get('OC', '')}
        if c.get('InSv'): s['InvulSave'] = {'Save': c['InSv']}
        m = re.match(r'(\d+(?:\.\d+)?)(?:\s*x\s*(\d+))?', c.get('Base', ''))
        if m: s['BaseInfo'] = {'Size': m.group(1) + ('x' + m.group(2) if m.group(2) else '')}
        if len(ps) > 1: s['StatName'] = cl(p['name'])
        out.append(s)
    return out

def wname(n):  # BSData prefixes sub-profiles with "➤ " and uses a plain hyphen; the dataset uses an en dash
    n = re.sub(r'^➤\s*', '', clean(n)); return cl(n).replace(' - ', ' – ')

def weapons(x, reg):
    seen, groups = set(), {'Ranged Weapons': [], 'Melee Weapons': []}
    for e in own_walk(x, reg):
        for p in e.get('profiles', []) + link_profiles(e, reg):  # weapons can also be shared profiles linked by infoLink (C'tan powers)
            c = chars(p)
            if not ('Range' in c and 'AP' in c and 'A' in c): continue  # any weapon-shaped profile, whatever its type name (Ranged Weapons, Melee Weapons, C'tan Powers...)
            kind = 'Melee Weapons' if c.get('Range', '').lower() == 'melee' else 'Ranged Weapons'
            name = wname(p['name']); sig = (kind, name, json.dumps(c, sort_keys=True))
            if sig in seen: continue
            seen.add(sig)
            w = {'Name': name}; kw = c.get('Keywords', '')
            kws = ([kw] if kw and kw != '-' else []) + ([p['typeName'].upper().replace("'", '’').rstrip('S')] if p.get('typeName') not in ('Ranged Weapons', 'Melee Weapons') else [])
            if kws: w['Keywords'] = ', '.join(kws).upper()
            w.update({'Range': c.get('Range', ''), 'Attacks': c.get('A', ''), 'ToHit': c.get('BS') or c.get('WS') or '', 'Strength': c.get('S', ''), 'AP': c.get('AP', ''), 'Damage': c.get('D', '')})
            groups[kind].append(w)
    out = []
    if groups['Ranged Weapons']: out.append({'Name': 'RANGED WEAPONS', 'Weapons': groups['Ranged Weapons']})
    if groups['Melee Weapons']: out.append({'IsMelee': True, 'Name': 'MELEE WEAPONS', 'Weapons': groups['Melee Weapons']})
    return out

LEAD = ('Leader', 'Support')
def ability_profiles(x, reg):
    """(profile, source entry) for abilities on the datasheet itself, via profile links, and inside equipment (upgrade) entries"""
    out = []
    for p in x.get('profiles', []):
        if p.get('typeName') == 'Abilities' and clean(p['name']) not in LEAD: out.append((p, None))
    for p in link_profiles(x, reg):
        if p.get('typeName') == 'Abilities' and clean(p['name']) not in LEAD: out.append((p, None))
    for e in own_walk(x, reg):
        if e is x or e.get('type') != 'upgrade': continue
        for p in e.get('profiles', []) + link_profiles(e, reg):
            if p.get('typeName') == 'Abilities': out.append((p, e))
    return out

def abilities_and_defs(x, reg):
    abil, defs, seen = [], {}, set()
    for p, src in ability_profiles(x, reg):
        t = clean(p['name'])
        if t.lower() not in seen:
            seen.add(t.lower()); abil.append({'Title': t, 'Text': clean(chars(p).get('Description'))})
        if src is not None:
            k = cl(src['name']).lower(); defs.setdefault(k, {'Key': k}).setdefault('GrantsAbilities', []).append(t)
    for e in own_walk(x, reg):  # equipment with a points cost
        if e is x or e.get('type') != 'upgrade': continue
        c = cost(e)
        if c: defs.setdefault(cl(e['name']).lower(), {'Key': cl(e['name']).lower()})['Cost'] = c
    return abil, list(defs.values())

def split_infos(abil):
    infos = [{'Title': a['Title'].upper(), 'Text': a['Text']} for a in abil if a['Title'].lower().startswith('damaged')]
    return [a for a in abil if not a['Title'].lower().startswith('damaged')], infos

def leader_info(x, abil):
    for p in x.get('profiles', []):
        if p.get('typeName') == 'Abilities' and clean(p['name']) in LEAD:
            t = clean(chars(p).get('Description')); m = re.search(r'following units?:\s*(.*)$', t)
            names = [n.strip() for n in re.split(r',\s*', m.group(1)) if n.strip()] if m else []
            li = {'UnitNames': names, 'Abilities': [{'AbilityId': a['Title']} for a in abil if re.search(r'(is|are) leading (a|this) unit', a['Text'])]}
            if clean(p['name']) == 'Support': li['LeaderType'] = 'Support'
            return li
    return None

def keywords(x):
    kw, fk = [], []
    for l in x.get('categoryLinks', []):
        n = l['name']
        if n.startswith('Faction:'): fk.append(cl(n.split(':', 1)[1]))
        elif n not in LEAD: kw.append(cl(n))
    return kw, fk

CORE = {'Deep Strike', 'Scouts', 'Infiltrators', 'Fights First', 'Lone Operative', 'Stealth', 'Deadly Demise', 'Firing Deck', 'Hover', 'Feel No Pain', 'Transport'}
def core_abilities(x):
    out = []
    for l in x.get('infoLinks', []):
        n = clean(l['name'])
        hidden = any(md.get('field') == 'hidden' and md.get('type') == 'set' and md.get('value') is True for md in l.get('modifiers', []))  # shown only for some attachments
        if l.get('type') == 'rule' and n in CORE and not hidden:
            for md in l.get('modifiers', []):
                if md.get('field') == 'name' and md.get('type') == 'append': n += ' ' + str(md['value'])
            out.append(n)
    for p in x.get('profiles', []):
        if p.get('typeName') == 'Abilities' and clean(p['name']) in LEAD: out.append(clean(p['name']))
    return out

# ------------------------------------------------------------------ composition
def models_of(x, reg):
    if x.get('type') == 'model': return [x]
    return [e for e in walk(x, reg) if e is not x and e.get('type') == 'model']

def composition(x, reg):
    ms = models_of(x, reg); mc = []
    grp = next((g for g in x.get('selectionEntryGroups', []) if any(m in models_of(g, reg) for m in ms)), None)
    gmn, gmx = limit(sel_constraints(grp)) if grp else (None, None)
    isw = lambda e: e.get('type') == 'upgrade' and any(p.get('typeName') in ('Ranged Weapons', 'Melee Weapons') for p in e.get('profiles', []))
    def req(e): return any(k['type'] == 'min' and k['value'] >= 1 for k in sel_constraints(e))
    for m in ms:
        mn, mx = limit(sel_constraints(m))
        if len(ms) == 1 and gmn is not None: mn, mx = gmn, gmx
        if x.get('type') == 'model': mn = mx = None  # a single-model datasheet has no count
        item = {}
        if mx is not None and mx > 1: item['Limit'] = {'Min': mn if mn is not None else mx, 'Max': mx}
        item['ModelName'] = cl(m['name'])
        init, opts = [], []
        def items(c): return [e for e in c.get('selectionEntries', []) if e.get('type') == 'upgrade'] + [reg.ent[l['targetId']] for l in c.get('entryLinks', []) if l.get('type') == 'selectionEntry' and l['name'] not in SKIP_LINKS and reg.ent.get(l.get('targetId'), {}).get('type') == 'upgrade']
        def scan(c):
            for g in c.get('selectionEntryGroups', []):
                if is_enh(g): continue
                gch = items(g); d = next((e for e in gch if e['id'] == g.get('defaultSelectionEntryId')), None)
                if d is not None:
                    init.append(cl(d['name']).lower()); rest = [e for e in gch if e is not d]
                    if rest: opts.append({'Replaces': [x.strip() for x in re.split(' & | and ', cl(d['name']).lower())], 'Options': [cl(e['name']).replace(' & ', ' and ') for e in rest]})  # a default like 'spear & shield' is two items replaced together; options keep the combined name
                elif gch and all(req(e) for e in gch): init.extend(cl(e['name']).lower() for e in gch if isw(e))
                elif gch: opts.append({'Options': [cl(e['name']).replace(' & ', ' and ') for e in gch]})
                scan(g)
            for e in items(c):
                if req(e) and isw(e): init.append(cl(e['name']).lower())
        scan(m); init = list(dict.fromkeys(init))
        item['Wargear'] = [{'InitalWargear': init, 'Options': opts}] if (init or opts) else []
        mc.append(item)
    # unit size = sum of the limits of the groups that hold the models (e.g. "5-10 Immortals"); falls back to the model limits
    tmn = tmx = 0; found = False
    for g in x.get('selectionEntryGroups', []):
        if models_of(g, reg) and not is_enh(g):
            a, b = limit(sel_constraints(g))
            if b is not None: tmn += a or 0; tmx += b; found = True
    return {'ModelCompositions': mc}, ((tmn or 1, tmx) if found else None)

# ------------------------------------------------------------------ points
def conds(m):
    """every condition dict reachable from a modifier (conditions, conditionGroups, localConditionGroups)"""
    out = []
    def rec(o):
        for c in o.get('conditions', []): out.append(c)
        for k in ('conditionGroups', 'localConditionGroups'):
            for g in o.get(k, []):
                if g.get('type') in ('atLeast', 'atMost', 'equalTo', 'greaterThan', 'lessThan'): out.append({**g, 'conditions': None, '_local': True})  # a local group is itself a count test over its inner conditions
                rec(g)
    rec(m); return out

def points(x, comp, size):
    base = cost(x) or 0
    n_min = size[0] if size else sum(m.get('Limit', {}).get('Min', 1) for m in comp['ModelCompositions']) or 1
    n_max = size[1] if size else sum(m.get('Limit', {}).get('Max', 1) for m in comp['ModelCompositions']) or 1
    steps, inc = [], []  # steps: (model threshold, 'set'|'inc', value); inc: (copy number, delta)
    for md in x.get('modifiers', []):
        if md.get('field') != PTS: continue
        cs = conds(md); local = [c['value'] for c in cs if c.get('type') == 'atLeast' and c.get('_local')]
        thr = [c['value'] for c in cs if c.get('type') == 'atLeast' and not c.get('_local')] + [c['value'] + 1 for c in cs if c.get('type') == 'greaterThan' and not c.get('_local')]
        if md['type'] == 'increment' and any(c.get('type') == 'before' for c in cs): inc.append((max(local) + 1 if local else 2, md['value']))
        elif thr and md['type'] in ('set', 'increment'): steps.append((min(thr), 'set' if md['type'] == 'set' else 'inc', md['value']))
    steps.sort(key=lambda t: t[0])
    # model-count brackets split at every threshold; each bracket is priced at its largest size
    ts = sorted({t for t, _, _ in steps if t > n_min}); bounds = [n_min] + ts + [n_max + 1]; brackets = []
    for i in range(len(bounds) - 1):
        size = min(bounds[i + 1] - 1, n_max) if i + 1 < len(bounds) - 1 else n_max
        c = base
        for t, kind, v in steps:
            if size >= t: c = v if kind == 'set' else c + v
        brackets.append((size, c))
    # copy brackets (the Nth copy of the same unit costs more). the dataset stores the END of a bounded range and the START of the open one.
    starts = [1] + sorted({f for f, _ in inc})
    out = []
    for i, s in enumerate(starts):
        uc = (starts[i + 1] - 1) if i + 1 < len(starts) else s
        delta = sum(d for f, d in inc if f <= s)
        for mc, c in brackets:
            p = {'ModelCount': mc, 'Cost': c + delta}
            if len(starts) > 1: p = {'UnitCount': uc, **p}
            out.append(p)
    return out

# ------------------------------------------------------------------ unit
def convert(x, reg):
    kw, fk = keywords(x); comp, size = composition(x, reg); abil, defs = abilities_and_defs(x, reg)
    comp['WargearDefinitions'] = defs; abil, infos = split_infos(abil)
    fac = next((clean(l['name']) for l in x.get('infoLinks', []) if l.get('type') == 'rule' and clean(l['name']) in reg.army_rules), None)
    return {'Name': re.sub(r'\s*\[(Legends|Crucible)\]', '', x['name']).upper(), 'Faction': fac, 'UnitComposition': comp, 'UnitAbilities': abil, 'LeaderInfo': leader_info(x, abil), 'Infos': infos, 'Keywords': kw,
            'CoreAbilities': core_abilities(x), 'FactionKeywords': fk, 'StatLines': stat_lines(x, reg), 'Weapons': weapons(x, reg), 'Upgrades': [], 'Points': points(x, comp, size)}

def has_unit_profile(x, reg): return any(p.get('typeName') == 'Unit' for e in own_walk(x, reg) for p in e.get('profiles', []) + link_profiles(e, reg))

def mfm_points(mu):
    prs = mu['pricing']; uc = lambda r: (lambda a, b: int(b) if b else int(a))(*re.match(r'\[(\d+),(\d*)', r).groups())
    return [({'UnitCount': uc(p['range'])} if len(prs) > 1 else {}) | {'ModelCount': q['models'], 'Cost': q['points']} for p in prs for q in p['costs']]

def units(reg, legends, mfm=None, review=None):
    seen, out = set(), []
    cands = [reg.ent.get(l.get('targetId')) for l in reg.main.get('entryLinks', []) if l.get('type') == 'selectionEntry']  # only what the catalogue links as a roster entry (shared single-model entries inside units are not units)
    for x in cands:
        if not x or x['id'] in seen or x.get('type') not in ('unit', 'model') or not has_unit_profile(x, reg): continue
        seen.add(x['id'])
        if ('[Legends]' in x['name']) != legends or '[Crucible]' in x['name']: continue
        u = convert(x, reg)
        if mfm:  # the MFM is the official points source: where BSData is missing / differs, the MFM wins and the unit is listed in the review file
            mu = next((m for m in mfm['units'] if keyn(m['name']) == keyn(x['name'].replace(' [Legends]', ''))), None)
            if mu:
                mp = mfm_points(mu); srt = lambda ps: sorted((p.get('UnitCount') or 0, p['ModelCount'], p['Cost']) for p in ps)
                if srt(mp) != srt(u['Points']):
                    review.append(f"points for {x['name']}: BSData {[(p.get('UnitCount'), p['ModelCount'], p['Cost']) for p in u['Points']]} -> MFM {[(p.get('UnitCount'), p['ModelCount'], p['Cost']) for p in mp]}")
                    u['Points'] = mp
        out.append(u)
    return out

# ------------------------------------------------------------------ detachments (merge)
def rule_text(reg, link):
    r = reg.rule.get(link.get('targetId'))
    return (clean(r['name']), clean(r.get('description'))) if r else None

def detachments(reg, mfm, wo, review, whd=None):
    if not mfm: return (wo or {}).get('Dettachments', [])
    cur = {keyn(d['Name']): d for d in (wo or {}).get('Dettachments', [])}
    bsd_det = {}
    for e in reg.ent.values():
        if e.get('type') == 'upgrade' and any(l.get('type') == 'rule' for l in e.get('infoLinks', [])) and any(c.get('name') == 'Detachment Points' for c in e.get('costs', [])):
            bsd_det[keyn(e['name'])] = e
    enh_txt = {}
    for e in reg.ent.values():
        if e.get('type') == 'upgrade' and any(c.get('name') == 'Enhancements' and c.get('value') for c in e.get('costs', [])):
            for p in e.get('profiles', []):
                if p.get('typeName') == 'Abilities': enh_txt[keyn(e['name'])] = (clean(p['name']), clean(chars(p).get('Description')))
    out = []
    for d in mfm['detachments']:
        k = keyn(d['name']); old = cur.get(k)
        if not old: review.append(f"NEW detachment {d['name']}: BSData has no stratagems / effects, added without them")
        det = dict(old or {}); det['Name'] = d['name'].upper(); det['Cost'] = d['dp']
        det['ForceDispositions'] = [o.upper() for o in d.get('objectives', [])]
        b = bsd_det.get(k)
        if b:
            for l in b.get('infoLinks', []):
                rt = rule_text(reg, l)
                if rt:
                    old_rule = (old or {}).get('Rule') or {}
                    if old and same(old_rule.get('Text', ''), rt[1]): det['Rule'] = old_rule
                    else:
                        if old and whd is None: review.append(f"detachment rule text changed: {d['name']} / {rt[0]}")
                        det['Rule'] = {**old_rule, 'Title': rt[0].upper(), 'Text': rt[1]}
        det.setdefault('Stratagems', []); det.setdefault('Rule', {'Title': '', 'Text': ''})
        if whd is not None:  # Wahapedia 11th edition: stratagems (BSData has none) and the detachment rule text
            st = whd.stratagems(d['name'])
            if st:
                if old and not same(' '.join(sorted(x.get('Effect', '') + x.get('When', '') + x.get('Target', '') for x in det['Stratagems'])), ' '.join(sorted(x['Effect'] + x['When'] + x['Target'] for x in st))): review.append(f"stratagems of {d['name']} replaced from Wahapedia ({len(det['Stratagems'])} -> {len(st)})")
                det['Stratagems'] = st
            elif not det['Stratagems']: review.append(f"{d['name']}: no stratagems found in Wahapedia")
            wr = whd.rule(d['name'])
            if wr:
                if old and not same((det.get('Rule') or {}).get('Text', ''), wr['Text']): review.append(f"detachment rule text from Wahapedia: {d['name']} / {wr['Title']}")
                det['Rule'] = {**det.get('Rule', {}), 'Title': wr['Title'], 'Text': wr['Text']}
        base = lambda n: keyn(re.sub(r'\s*\(.*\)$', '', n))
        olde = {base(e['Name']): e for e in det.get('Enhancements', [])}; ne = []
        for e in d.get('enhancements', []):
            ek = base(e['name']); o = dict(olde.get(ek) or {})
            if not o: review.append(f"NEW enhancement {d['name']} / {e['name']} ({e['points']}): description from BSData, no structured adjustments/requirements")
            elif o.get('Cost') != e['points']: review.append(f"enhancement cost {d['name']} / {e['name']}: {o.get('Cost')} -> {e['points']}")
            o['Name'] = o.get('Name') or e['name']; o['Cost'] = e['points']
            t = enh_txt.get(ek)
            if whd is not None:
                we = next((x for x in whd.enhancements(d['name']) if base(x['Name']) == ek), None)
                if we and we['Description']: t = ('', we['Description'])  # Wahapedia text wins over BSData text
            alnum = lambda z: re.sub(r'[^a-z0-9]+', '', str(z).replace('’', "'").lower())
            if t and alnum(t[1]) in alnum(o.get('Description', '')): pass  # the dataset's text = restriction line + BSData text
            elif t and not same(o.get('Description', ''), t[1]):
                if o.get('Description'): review.append(f"enhancement text changed: {d['name']} / {e['name']}")
                o['Description'] = t[1]
            o.setdefault('Description', ''); ne.append(o)
        for ek in olde.keys() - {base(e['name']) for e in d.get('enhancements', [])}: review.append(f"enhancement REMOVED upstream: {d['name']} / {olde[ek]['Name']}")
        det['Enhancements'] = ne; out.append(det)
    for k in cur.keys() - {keyn(d['name']) for d in mfm['detachments']}: review.append(f"detachment only in current projectWar data: {cur[k]['Name']}")
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--wh', default=''); ap.add_argument('--bsd', required=True); ap.add_argument('--lib', action='append', default=[]); ap.add_argument('--gs', required=True)
    ap.add_argument('--mfm'); ap.add_argument('--wo'); ap.add_argument('--out', required=True); ap.add_argument('--legends', action='store_true'); a = ap.parse_args()
    reg = Reg(a.bsd, a.lib, a.gs); review = []
    wo = json.load(open(a.wo, encoding='utf-8-sig')) if a.wo else None
    mfm = None
    if a.mfm:
        import yaml; mfm = yaml.safe_load(open(a.mfm, encoding='utf-8'))
    us = units(reg, a.legends, mfm, review); arm = []
    for r in (wo or {}).get('ArmyRules', []):
        rr = next((x for x in reg.rule.values() if keyn(x['name']) == keyn(r['Title'])), None)
        if rr and not same(rr.get('description'), r['Text']): review.append(f"army rule text changed: {r['Title']}")
        arm.append({**r, 'Text': clean(rr['description']) if rr and not same(rr.get('description'), r['Text']) else r['Text']})
    whd = None
    if a.wh:
        import wh_load; whd = wh_load.WH(a.wh.split(','))
    res = {'Name': reg.main['name'], 'Units': us, 'Dettachments': [] if a.legends else detachments(reg, mfm, wo, review, whd), 'ArmyRules': arm}
    json.dump(res, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(a.out + '.review.txt', 'w', encoding='utf-8').write('\n'.join(review) + '\n')
    print(f'{len(us)} units, {len(res["Dettachments"])} detachments -> {a.out}  ({len(review)} review notes)')

if __name__ == '__main__': main()
