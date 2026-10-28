"""Detachments that let another faction's units into the army get an "Allies" field the app reads:
  {"Faction": data file of the allies, "Keyword": the Faction keyword that picks their own units, "MaxPoints": cap, "NoWarlord": true}
Only the cases below are described so far (the rule text of the detachment says the same): Deathwatch Support of the Space Marines and the Chapters.
usage: python -I -X utf8 tools/wh_allies.py <data dir> [--write]"""
import glob, json, os, re, sys
write = '--write' in sys.argv; d = [x for x in sys.argv[1:] if not x.startswith('--')][0]
RULES = {'DEATHWATCH SUPPORT': {'Faction': 'Deathwatch', 'Keyword': 'Deathwatch', 'MaxPoints': 500, 'NoWarlord': True}}
n = 0
for f in sorted(glob.glob(os.path.join(d, '*.json'))):
    doc = json.load(open(f, encoding='utf-8')); ch = False
    for det in doc.get('Dettachments') or []:
        a = RULES.get(det['Name'])
        if not a: continue
        text = re.sub(r'\s+', ' ', det['Rule'].get('Text', ''))
        if not re.search(r'You can include Deathwatch units in your army', text): continue   # the rule must say so in this file too
        if det.get('Allies') != [a]: det['Allies'] = [dict(a)]; ch = True
    if ch:
        n += 1; print('allies set in', os.path.basename(f))
        if write: json.dump(doc, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(n, 'files')
