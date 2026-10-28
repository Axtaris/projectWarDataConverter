"""Space Marine army rules, 11th edition: Combat Doctrines, Transhuman Strategist and Librarius (Wahapedia Abilities.csv) replace the 10th edition
"Oath of Moment" that older data still carried in every Space Marine file. Other army rules are left as they are.
usage: python -I -X utf8 tools/wh_army_rules.py <data dir> [--write]"""
import glob, html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wh_load import table
write = '--write' in sys.argv; d = [x for x in sys.argv[1:] if not x.startswith('--')][0]
IDS = [('COMBAT DOCTRINES', '000011158'), ('TRANSHUMAN STRATEGIST', '000011162'), ('LIBRARIUS', '000011163')]
AB = {r['id']: r for r in table('Abilities')}
def text(h):
    h = re.sub(r'<h4[^>]*>(.*?)</h4>', lambda m: '\n▪ ' + m.group(1).strip() + ': ', h)
    h = re.sub(r'<li[^>]*>', '\n▪ ', h); h = re.sub(r'<br\s*/?>\s*<br\s*/?>', '\n', h); h = re.sub(r'<br\s*/?>', '\n', h); h = re.sub(r'<[^>]+>', '', h)
    h = html.unescape(h).replace(' ', ' '); h = re.sub(r'[ \t]+', ' ', h); h = re.sub(r'\n\s*\n+', '\n', h)
    return h.strip()
RULES = [{'Restrictions': '', 'Title': t, 'Text': text(AB[i]['description'])} for t, i in IDS]
n = 0
for f in sorted(glob.glob(os.path.join(d, '*.json'))):
    doc = json.load(open(f, encoding='utf-8'))
    ar = doc.get('ArmyRules')
    if not ar or not any(r['Title'] == 'OATH OF MOMENT' for r in ar): continue
    new = []
    for r in ar:
        if r['Title'] == 'OATH OF MOMENT': new += [dict(x) for x in RULES]
        else: new.append(r)
    doc['ArmyRules'] = new; n += 1; print('rules replaced in', os.path.basename(f))
    if write: json.dump(doc, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(n, 'files')
