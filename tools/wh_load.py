"""Wahapedia 11th edition CSV export -> projectWar detachment objects (stratagems, detachment rule, enhancement text).
Only the wh40k11ed export is used. Importable (bsd2pw.py) and runnable as a self-test against the current projectWar data:
  python -X utf8 tools/wh_load.py <faction id> <current projectWar json>"""
import csv, html, json, re, sys
from collections import defaultdict
csv.field_size_limit(10**9)
import os
WH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sources', 'wh')
def table(f, d=WH_DIR): return list(csv.DictReader(open(f'{d}/{f}.csv', encoding='utf-8-sig', newline=''), delimiter='|'))
def key(s): return re.sub(r'[^a-z0-9]+', ' ', html.unescape(str(s)).replace('\u2019', "'").lower()).strip()

def kw_title(m):  # <span class="kwb">NECRONS</span> -> Necrons (the dataset writes keywords in title case inside rule text)
    return ' '.join(w[:1] + w[1:].lower() if w.isupper() and len(w) > 1 else w for w in m.group(1).split(' '))
def clean(s, bullets=False):
    s = html.unescape(s or '').replace('\u00a0', ' ')
    s = re.sub(r'<span class="kwb">(.*?)</span>', lambda m: kw_title(m), s)
    s = re.sub(r'</span>\s*<span[^>]*>', ' ', s) if False else s
    if bullets: s = re.sub(r'<li[^>]*>', '\u25aa ', s); s = re.sub(r'</li>\s*', '\n', s)
    s = re.sub(r'<br\s*/?>', '\n', s); s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'[ \t]+', ' ', s); s = re.sub(r'\s*\n\s*', '\n', s)
    return s.strip()

def deshout(s):
    """Wahapedia sometimes prints keywords in plain capitals (NECRONS INFANTRY CHARACTER); the dataset writes them in title case. [BRACKET] abilities stay as they are."""
    def fix(m):
        t = m.group(0)
        return ' '.join(w[:1] + w[1:].lower() for w in re.split(r'(?<=[A-Z]) (?=[A-Z])', t)) if False else re.sub(r'[A-Z]{3,}', lambda x: x.group(0).capitalize(), t)
    out, i = [], 0
    for part in re.split(r'(\[[^\]]*\])', s):
        out.append(part if part.startswith('[') else re.sub(r'(?<![A-Za-z0-9])[A-Z]{3,}(?![A-Za-z0-9])', lambda x: x.group(0).capitalize(), part))
    return ''.join(out)
def blocks(desc):
    """WHEN / TARGET / EFFECT / RESTRICTIONS out of the stratagem html"""
    out = {}
    for m in re.finditer(r'<b>\s*(WHEN|TARGET|EFFECT|RESTRICTIONS?)\s*:\s*</b>(.*?)(?=<b>\s*(?:WHEN|TARGET|EFFECT|RESTRICTIONS?)\s*:|\Z)', desc or '', re.S):
        out[m.group(1).upper().rstrip('S')] = deshout(clean(m.group(2)))
    return out
PHASE = {'your turn': 'friendly', 'opponent\u2019s turn': 'opponent', 'either player\u2019s turn': 'any'}

class WH:
    def __init__(self, fids, d=WH_DIR):
        self.fids = set(fids)
        self.det = {r['id']: r for r in table('Detachments', d) if r['faction_id'] in self.fids and r['dp']}  # dp = a real 11th detachment (Boarding Actions ones have none)
        self.by_name = {key(r['name']): r for r in self.det.values()}
        self.strat = defaultdict(list); self.enh = defaultdict(list); self.abil = defaultdict(list)
        for r in table('Stratagems', d):
            if r['detachment_id'] in self.det: self.strat[r['detachment_id']].append(r)
        for r in table('Enhancements', d):
            if r['detachment_id'] in self.det: self.enh[r['detachment_id']].append(r)
        for r in table('Detachment_abilities', d):
            if r['detachment_id'] in self.det: self.abil[r['detachment_id']].append(r)
    def get(self, name): return self.by_name.get(key(name))
    def stratagems(self, name):
        det = self.get(name); out = []
        if not det: return out
        for r in self.strat[det['id']]:
            b = blocks(r['description']); cat = re.sub(r'\s*[\u2013-]\s*', ' - ', r['type']).upper()
            if ' - ' not in cat: cat = re.sub(r'\s*STRATAGEM$', '', cat)  # no sub-type: projectWar shows just the detachment name
            s = {'Name': r['name'].title() if r['name'].isupper() else r['name'], 'Category': cat, 'CPCost': int(r['cp_cost'] or 0), 'Phase': PHASE.get(r['turn'].lower(), 'any'),
                 'When': b.get('WHEN', ''), 'Target': b.get('TARGET', ''), 'Effect': b.get('EFFECT', '')}
            if b.get('RESTRICTION'): s['Restrictions'] = b['RESTRICTION']
            out.append(s)
        return out
    def rule(self, name):
        det = self.get(name)
        if not det or not self.abil[det['id']]: return None
        a = self.abil[det['id']][0]
        return {'Title': a['name'].upper(), 'Text': clean(a['description'], bullets=True), 'Restrictions': ''}
    def enhancements(self, name):
        det = self.get(name)
        return [{'Name': r['name'], 'Cost': int(r['cost'] or 0), 'Description': clean(r['description']), 'upgrade': r.get('upgrade') == 'true'} for r in self.enh[det['id']]] if det else []

if __name__ == '__main__':
    fid, path = sys.argv[1], sys.argv[2]
    w = WH(fid.split(',')); wo = json.load(open(path, encoding='utf-8-sig'))
    n = lambda s: re.sub(r'[^a-z0-9]+', '', str(s).lower().replace('\u2019', "'"))
    same = diff = missing = 0; shown = 0
    for d in wo['Dettachments']:
        mine = {n(s['Name']): s for s in w.stratagems(d['Name'])}
        for s in d['Stratagems']:
            m = mine.get(n(s['Name']))
            if not m: missing += 1; continue
            bad = [f for f in ('Category', 'CPCost', 'Phase', 'When', 'Target', 'Effect') if n(m[f]) != n(s.get(f, ''))]
            if bad:
                diff += 1
                if shown < 6: shown += 1; print('  differs', d['Name'], '/', s['Name'], bad, '\n    WO:', {f: str(s.get(f))[:90] for f in bad}, '\n    WH:', {f: str(m[f])[:90] for f in bad})
            else: same += 1
    print(f'stratagems of detachments present in projectWar: identical {same}, differ {diff}, not found in Wahapedia {missing}')
    r = next((x for x in (w.rule(d['Name']) for d in wo['Dettachments']) if x), None)
    if r: print('rule sample:', r['Title'], '|', r['Text'][:160].replace('\n', ' / '))
