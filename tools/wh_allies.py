"""Detachments that let another faction's units into the army get an "Allies" field the app reads:
  Faction      data file the allied units come from
  Keyword      list: a unit is allowed when one of its Faction keywords, keywords or its name is one of these      (or)
  UnitNames    list of datasheet names
  ExcludeKeyword  keywords that are not allowed through this rule
  MaxPoints    cap in points, or MaxPointsBySize {"1000": 500, "2000": 1000, "3000": 1500} (Incursion, Strike Force, Onslaught)
  NoWarlord    none of the allied models can be the Warlord
Every entry is only written when the detachment's own rule text says it (the NEEDLE must be found in it), so a change in the data is noticed.
Not described yet: Devoted of Ynnead (Aeldari): the Ynnari units live in the Aeldari file and would have to be hidden until the detachment is chosen.
usage: python -I -X utf8 tools/wh_allies.py <data dir> [--write]"""
import glob, json, os, re, sys
write = '--write' in sys.argv; d = [x for x in sys.argv[1:] if not x.startswith('--')][0]
BY_SIZE = {'1000': 500, '2000': 1000, '3000': 1500}
RULES = {
    'DEATHWATCH SUPPORT': ('You can include Deathwatch units in your army', {'Faction': 'Deathwatch', 'Keyword': ['Deathwatch'], 'MaxPoints': 500, 'NoWarlord': True}),
    'ICONOCLAST FIEFDOM': ('You can include DAMNED units in your army', {'Faction': 'Chaos Space Marines', 'Keyword': ['Damned'], 'MaxPoints': 500}),
    'TALLYBAND SUMMONERS': ('You can include Plague Legions units in your army', {'Faction': 'Chaos Daemons', 'Keyword': ['Nurgle'], 'MaxPointsBySize': BY_SIZE, 'NoWarlord': True}),
    'REAPER’S WAGER': ('You can include Harlequins units in your army', {'Faction': 'Aeldari', 'Keyword': ['Harlequins'], 'MaxPointsBySize': BY_SIZE, 'NoWarlord': True}),
    'CARNIVAL OF EXCESS': ('You can include Legions of Excess units in your army', {'Faction': 'Chaos Daemons', 'Keyword': ['Slaanesh'], 'MaxPointsBySize': BY_SIZE, 'NoWarlord': True}),
    'BROOD BROTHERS AUXILIA': ('You can include Astra Militarum units in your army', {'Faction': 'Astra Militarum', 'Keyword': ['Astra Militarum'], 'ExcludeKeyword': ['Aircraft', 'Commissar', 'Epic Hero', 'Militarum Tempestus', 'Ogryn', 'Ratling', 'Ratlings', 'Tech-Priest Enginseer', 'Ministorum Priest'], 'MaxPointsBySize': BY_SIZE, 'NoWarlord': True}),
    'QUESTOR FORGEPACT': ('You can include Tech-Priest Dominus', {'Faction': 'Adeptus Mechanicus', 'UnitNames': ['TECH-PRIEST DOMINUS', 'TECH-PRIEST MANIPULUS', 'SKITARII MARSHAL', 'SKITARII RANGERS', 'SKITARII VANGUARD'], 'MaxPoints': 500}),
    'CHANGEHOST OF DECEIT': ('You can include Scintillating Legions units in your army', {'Faction': 'Chaos Daemons', 'Keyword': ['Tzeentch'], 'MaxPointsBySize': BY_SIZE, 'NoWarlord': True}),
    'KHORNE DAEMONKIN': ('You can include the Blood Legions units in your army', {'Faction': 'Chaos Daemons', 'Keyword': ['Khorne'], 'MaxPointsBySize': BY_SIZE, 'NoWarlord': True}),
}
n = 0
for f in sorted(glob.glob(os.path.join(d, '*.json'))):
    doc = json.load(open(f, encoding='utf-8')); ch = False
    for det in doc.get('Dettachments') or []:
        r = RULES.get(det['Name'])
        if not r: continue
        needle, a = r
        if needle not in re.sub(r'\s+', ' ', det['Rule'].get('Text', '')): print('  rule text differs, skipped:', os.path.basename(f), det['Name']); continue
        if det.get('Allies') != [a]: det['Allies'] = [json.loads(json.dumps(a))]; ch = True
    if ch:
        n += 1; print('allies set in', os.path.basename(f))
        if write: json.dump(doc, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(n, 'files')
