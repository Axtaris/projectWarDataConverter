"""Detachment rules that grant a plain, permanent ability to every unit of a keyword ("Friendly Astra Militarum units (excluding TITANIC units) have Stealth.") become a
detachment Effect, so the datasheets of those units show the ability. Conditional rules (re-rolls, triggers, "while", battle rounds...) stay plain text.
Only detachments with no effects yet are touched.
usage: python -I -X utf8 tools/wh_detachment_effects.py <data dir> [--write]"""
import glob, json, os, re, sys
write = '--write' in sys.argv; d0 = [x for x in sys.argv[1:] if not x.startswith('--')][0]
CORE = r'(Infiltrators|Stealth|Fights First|Lone Operative(?: \d+")?|Scouts \d+"|Deep Strike|Hover)'
NOT_COND = r'(?<![A-Za-z])(while|if|each time|once|until|when|unless|select|can|may|roll|within|in your|at the|against|during|battle round)(?![A-Za-z])'
RX = re.compile(r"^friendly (?P<kw>[A-Za-z' ]+?) units(?: \(excluding (?P<ex>[A-Za-z' ]+?) units\))? (?:have|has) (?:the )?" + CORE + r"(?: abilit(?:y|ies))?$", re.I)
n_ok = 0; seen = []
for f in sorted(glob.glob(os.path.join(d0, '*.json'))):
    nm = os.path.basename(f)
    if nm in ('DataInfo.json', 'FactionInfoData.json') or 'Legends' in nm: continue
    doc = json.load(open(f, encoding='utf-8')); ch = False
    for d in doc.get('Dettachments', []):
        if d.get('Effects'): continue
        text = re.sub(r'\s+', ' ', re.sub(r'[▪•]', '. ', d['Rule'].get('Text', '')).replace('’', "'")).strip()
        effs = []
        for sen in [x.strip().rstrip('.') for x in re.split(r'(?<=[.!])\s+', text) if x.strip()]:
            if re.search(NOT_COND, sen, re.I): continue
            m = RX.match(sen)
            if not m: continue
            eff = {'AffectedUnits': [], 'AffectedUnitsByKeyword': [m.group('kw').strip()], 'DatasheetAdjustments': [{'Target': 'CoreAbilities', 'Type': 'Add', 'Scope': 'Unit', 'Values': [m.group(3)]}]}
            if m.group('ex'): eff['AffectedUnitsExcludeKeyword'] = [m.group('ex').strip()]
            effs.append(eff)
        if effs: d['Effects'] = effs; ch = True; n_ok += 1; seen.append((nm[:14], d['Name'], [e['AffectedUnitsByKeyword'] + e.get('AffectedUnitsExcludeKeyword', []) + e['DatasheetAdjustments'][0]['Values'] for e in effs]))
    if write and ch: json.dump(doc, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('detachments structured:', n_ok)
for x in seen: print('  ', x)
