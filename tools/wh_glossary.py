"""Glossary of the core rules that datasheets refer to: every weapon ability ([LETHAL HITS]...) and core ability (Deep Strike...) of section 24 of the 11th edition core rules,
plus the keywords the core rules give a rule to (BATTLELINE, DEDICATED TRANSPORT, EPIC HERO). Written into FactionInfoData.json as "Glossary", used for the tooltips of the app.
The text is Wahapedia's core rules page saved as HTML (sources/wh/Core_rules_11e.html).
usage: python -I -X utf8 tools/wh_glossary.py <data dir> <core rules html> [--write]"""
import html, json, os, re, sys
d, src, write = sys.argv[1], sys.argv[2], '--write' in sys.argv
t = open(src, encoding='utf-8').read()
x = re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S); x = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x))).replace('­', '')
a = x.index('Abilities 24.01'); b = x.index('Muster Armies 25', a); sec = x[a:b]
HEAD = re.compile(r"(?:(?<=\s)|^)(\[[A-Z][A-Z\- ]*\]|[A-Z][A-Z\-]*(?: [A-Z][A-Z\-]*)*) (24\.\d\d)(?= )")
marks = [(m.start(), m.end(), m.group(1), m.group(2)) for m in HEAD.finditer(sec)]
out = []
for i, (s, e, name, num) in enumerate(marks):
    nxt = marks[i + 1][0] if i + 1 < len(marks) else len(sec)
    body = sec[e:nxt].strip()
    body = re.split(r' SEE ALSO | (?=\d\d\.\d\d\.\d\d )', body)[0].strip()
    body = re.sub(r'\s*/ [A-Z]+$', '', body).strip()   # "LEADER 24.22 / SUPPORT 24.34": the heading of the next entry
    if name in ('SCOUT MOVE', 'DUPLICATED ABILITIES') or not body: continue
    out.append({'Name': name.strip('[]'), 'Kind': 'weapon' if name.startswith('[') else 'core', 'Section': num, 'Text': body})
sup = next((e for e in out if e['Name'] == 'SUPPORT'), None)
for e in out:
    if e['Name'] == 'LEADER' and sup and len(e['Text']) < 5: e['Text'] = sup['Text']   # "LEADER 24.22 / SUPPORT 24.34" share one text
KEYWORDS = [
    ('BATTLELINE', '25.03', 'The unit limit for BATTLELINE units is double the unit limit of the battle size (Incursion 2 becomes 4, Strike Force 3 becomes 6).'),
    ('DEDICATED TRANSPORT', '25.03', 'The unit limit for DEDICATED TRANSPORT units is double the unit limit of the battle size (Incursion 2 becomes 4, Strike Force 3 becomes 6).'),
    ('EPIC HERO', '25.03', 'Every EPIC HERO has a unit limit of 1, regardless of the battle size.'),
    ('WARLORD', '25.04', 'The supreme leader of your army: one CHARACTER model of a CHARACTER unit with the faction keyword you chose as army faction. That model gains the WARLORD keyword.'),
]
for n, s, tx in KEYWORDS: out.append({'Name': n, 'Kind': 'keyword', 'Section': s, 'Text': tx})
print(len(out), 'entries:', ', '.join(e['Name'] for e in out))
f = os.path.join(d, 'FactionInfoData.json'); doc = json.load(open(f, encoding='utf-8-sig'))
doc['Glossary'] = out
if write: json.dump(doc, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
