"""Structured effects for enhancements: turns plain, unconditional enhancement text into the adjustments the app applies to the statline and the weapon profiles
(StatAdjustments, WeaponStatAdjustments, DatasheetAdjustments). Only enhancements that have no effects yet are touched. A sentence becomes an effect only when it matches a
known template and carries no condition ("while", "if", "each time", "instead"...); every other sentence stays as plain text for a human to look at.
usage: python -I -X utf8 tools/wh_effects.py <data dir> [--write] [--report FILE]"""
import argparse, glob, json, os, re, collections
ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--write', action='store_true'); ap.add_argument('--report'); a = ap.parse_args()
KEYS = ('StatAdjustments', 'WeaponStatAdjustments', 'DatasheetAdjustments')
W = {'attacks': 'Attacks', 'strength': 'Strength', 'armour penetration': 'AP', 'damage': 'Damage', 'ballistic skill': 'ToHit', 'weapon skill': 'ToHit', 'range': 'Range'}
STAT = {'oc': 'OC', 'm': 'Move', 't': 'Toughness', 'w': 'Wounds', 'ld': 'Leadership'}
CORE = r'(Infiltrators|Stealth|Fights First|Lone Operative(?: \d+")?|Scouts \d+"|Feel No Pain \d\+|Deep Strike|Hover)'
NOT_COND = r'(?<![A-Za-z])(while|if|each time|instead|once|until|when|unless|select|can|may|roll|within|in your|at the|against|excluding)(?![A-Za-z])'
def n(s): return re.sub(r'\s+', ' ', s.replace('’', "'").replace('‘', "'").replace(' ', ' ')).strip()
def wscope(w):
    w = (w or '').strip().lower(); return 'Melee' if w.startswith('melee') else 'Ranged' if w.startswith('ranged') else 'All'
def chars(txt):
    out = []
    for p in re.split(r',\s*|\s+and\s+', txt.strip().lower()):
        p = re.sub(r'characteristics?', '', p).strip()
        if not p: continue
        if p not in W: return None
        out.append(W[p])
    return out
def sentence(s):
    """one sentence -> list of (list name, adjustment), or None when it is not a plain, unconditional effect"""
    s = n(s).rstrip('.')
    if re.search(NOT_COND, s, re.I): return None
    m = re.match(r"^(?:add|improve) (\d+) to the (.+?) characteristics? of the bearer's (melee |ranged )?(?:weapons|weapon)$", s, re.I)
    if m:
        cs = chars(m.group(2))
        return None if not cs else [('WeaponStatAdjustments', {'Value': m.group(1), 'Type': 'Add', 'Target': c, 'WeaponScope': wscope(m.group(3))}) for c in cs]
    m = re.match(r"^improve the (.+?) characteristics? of the bearer's (melee |ranged )?weapons by (\d+)$", s, re.I)
    if m:
        cs = chars(m.group(1))
        return None if not cs else [('WeaponStatAdjustments', {'Value': m.group(3), 'Type': 'Add', 'Target': c, 'WeaponScope': wscope(m.group(2))}) for c in cs]
    m = re.match(r"^add (\d+) to the (attacks|strength|damage) characteristics? of the bearer's pistols$", s, re.I)
    if m: return [('WeaponStatAdjustments', {'Value': m.group(1), 'Type': 'Add', 'Target': W[m.group(2).lower()], 'WeaponScope': 'Ranged', 'IncludedKeywords': ['PISTOL']})]
    m = re.match(r"^(?:the bearer's (melee |ranged )?weapons|(melee |ranged )?weapons equipped by the bearer) (?:have|has) the ((?:\[[A-Za-z0-9+ \-]+\](?: and |, )?)+) abilit(?:y|ies)$", s, re.I)
    if m:
        kws = re.findall(r'\[([A-Za-z0-9+ \-]+)\]', m.group(3))
        return [('WeaponStatAdjustments', {'Value': k.upper(), 'Type': 'Add', 'Target': 'Keywords', 'WeaponScope': wscope(m.group(1) or m.group(2))}) for k in kws]
    m = re.match(r"^(this model|this unit|the bearer)'s (melee|ranged) (?:attacks|weapons) have (?:the )?\[([A-Za-z0-9+ \-]+)\](?: ability)?$", s, re.I)
    if m:
        adj = {'Value': m.group(3).upper(), 'Type': 'Add', 'Target': 'Keywords', 'WeaponScope': wscope(m.group(2))}
        if m.group(1).lower() == 'this unit': adj['Scope'] = 'Unit'
        return [('WeaponStatAdjustments', adj)]
    m = re.match(r"^the bearer has a (\d)\+ invulnerable save$", s, re.I)
    if m: return [('StatAdjustments', {'Target': 'InvulSave', 'Value': m.group(1) + '+'})]
    m = re.match(r"^the bearer has a save characteristic of (\d)\+$", s, re.I)
    if m: return [('StatAdjustments', {'Target': 'Save', 'Value': m.group(1) + '+'})]
    m = re.match(r"^(this unit|the bearer|this model) has \+(\d+)(\")? (OC|M|T|W|Ld)$", s, re.I)
    if m:
        adj = {'Target': STAT[m.group(4).lower()], 'Type': 'Add', 'Value': m.group(2) + ('"' if m.group(3) else '')}
        if m.group(1).lower() == 'this unit': adj['Scope'] = 'Unit'
        return [('StatAdjustments', adj)]
    m = re.match(r"^(?:models in (?:the bearer's unit|this unit)|the bearer's unit|this unit) (?:has|have) (?:the )?" + CORE + r"(?: abilit(?:y|ies))?$", s, re.I)
    if m: return [('DatasheetAdjustments', {'Target': 'CoreAbilities', 'Type': 'Add', 'Scope': 'Unit', 'Values': [m.group(1)]})]
    m = re.match(r"^(this unit|the bearer|this model) has (?:the )?" + CORE + r"(?: ability)?$", s, re.I)
    if m:
        adj = {'Target': 'CoreAbilities', 'Type': 'Add', 'Values': [m.group(2)]}
        if m.group(1).lower() == 'this unit': adj['Scope'] = 'Unit'
        return [('DatasheetAdjustments', adj)]
    return None
def extract(desc):
    body = n(re.sub(r'<[^>]+>', ' ', desc or ''))
    body = re.sub(r"^[^.]*?(?<![A-Za-z])(?:model|unit)s? only(?: \([^)]*\))?\.\s*", '', body, flags=re.I)   # "Adepta Sororitas model only."
    out = []
    for sen in [x for x in re.split(r'(?<=[.!])\s+', body) if x.strip()]:
        r = sentence(sen)
        if r is not None: out += r
    return out or None
if __name__ == '__main__':
    tot = collections.Counter(); done = []
    for f in sorted(glob.glob(os.path.join(a.dir, '*.json'))):
        nm = os.path.basename(f)
        if nm in ('DataInfo.json', 'FactionInfoData.json') or 'Legends' in nm: continue
        doc = json.load(open(f, encoding='utf-8')); ch = False
        for d in doc.get('Dettachments', []):
            for e in d.get('Enhancements', []):
                tot['enhancements'] += 1
                if any(e.get(k) for k in KEYS): tot['already structured'] += 1; continue
                r = extract(e.get('Description'))
                if r is None: tot['plain text (conditional or unusual)'] += 1; continue
                for k, adj in r: e.setdefault(k, []).append(adj)
                tot['structured now'] += 1; ch = True; done.append((nm[:14], d['Name'], e['Name'], e['Description'][:150], r))
        if a.write and ch: json.dump(doc, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(dict(tot))
    if a.report:
        with open(a.report, 'w', encoding='utf-8') as fh:
            fh.write('# Enhancements structured from their text\n\n')
            for nm, dn, en, desc, r in done: fh.write(f'- {nm} / {dn} / **{en}**: {desc}\n  - {json.dumps([x[1] for x in r])}\n')
    else:
        for nm, dn, en, desc, r in done[:int(os.environ.get('N', 12))]: print(f' {nm} / {dn} / {en}: {desc}\n      -> {json.dumps([x[1] for x in r])[:260]}')
