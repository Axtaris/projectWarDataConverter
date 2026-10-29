"""Errata and FAQs of an official faction pack (the PDF Games Workshop publishes on Warhammer Community; Source.csv has the link and the date) written into the faction file.
The "RULES UPDATES" pages have two columns: UPDATES (army rules, one block per detachment, datasheets) and FAQS. Each entry is attached to what it names:
 * a datasheet (its name is in the heading)  -> unit["Errata"]  [{"Title","Text"}]   and unit["FAQ"]  [{"Q","A"}]
 * a detachment                              -> detachment["Errata"]
 * the army rules / nothing recognised        -> top level "Errata" / "FAQ"
usage: python -I -X utf8 tools/pack_errata.py <faction pack pdf> <data dir> <faction file name> [--write] [--dump FILE]
Needs poppler's pdftotext (-x -y -W -H crop the two columns); set PDFTOTEXT to its path when it is not on PATH."""
import json, os, re, shutil, subprocess, sys
args = [x for i, x in enumerate(sys.argv[1:], 1) if not x.startswith('--') and sys.argv[i - 1] not in ('--dump', '--date')]; write = '--write' in sys.argv
pdf, ddir, fname = args[0], args[1], args[2]
dump = sys.argv[sys.argv.index('--dump') + 1] if '--dump' in sys.argv else None
PT = os.environ.get('PDFTOTEXT') or shutil.which('pdftotext')
for c in (r'C:\Users\Diego\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin\pdftotext.exe',):
    if os.path.exists(c): PT = c; break
def text(p, extra=()): return subprocess.run([PT, '-f', str(p), '-l', str(p), *extra, pdf, '-'], capture_output=True, encoding='utf-8').stdout
INFO = os.path.join(os.path.dirname(PT), 'pdfinfo.exe')
pages = int(re.search(r'Pages:\s+(\d+)', subprocess.run([INFO if os.path.exists(INFO) else 'pdfinfo', pdf], capture_output=True, encoding='utf-8').stdout).group(1))
first = next(p for p in range(1, pages + 1) if 'This section presents updates' in text(p))
last = first
for p in range(first + 1, pages + 1):
    t = text(p)
    if 'RANGED WEAPONS' in t or 'MELEE WEAPONS' in t: break
    last = p
lines = []
for p in range(first, last + 1):
    for x in (0, 297):
        lines += [l.rstrip() for l in text(p, ('-x', str(x), '-y', '0', '-W', '298', '-H', '842')).splitlines()]
lines = [re.sub(r'[\x00-\x08\x0b-\x1f]', '', l.replace('\ufffd', '-').replace('\u2011', '-')) for l in lines]
SKIP = ('NECR', 'RONS', 'RULES U', 'This section presents', 'Changes applied after', 'les, designed to improve', 'highlighted in red')
rows = [l.strip() for l in lines if l.strip() and not l.strip().startswith(SKIP)]
OPENQ = ('\u2018', "'", '`'); BUL = ('\u25aa', '\u25ab', '\u25cf', '\u2022')
CHANGE = re.compile(r'^(Change|Add|Remove|Replace|Delete)\b')
def ends_quote(x): return x.endswith(('\u2019', "'", '\u2019.', "'."))
def marker(x):
    if x in ('UPDATES', 'FAQS', 'ARMY RULES', 'DATASHEETS'): return x
    m = re.fullmatch(r"([A-Z][A-Z' \-]+) DETACHMENT", x)
    return ('DET', m.group(1).strip()) if m else None
SCOPE = None; DET = None; MODE = 'updates'; entries, faqs, head, body, q = [], [], [], None, None
inq = False
def close():
    global body, head, inq
    if body is not None and head: entries.append({'Scope': SCOPE, 'Detachment': DET, 'Heading': ' '.join(head).strip(), 'Text': ' '.join(body).strip()})
    body = None; head = []; inq = False
for i, s in enumerate(rows):
    nxt = rows[i + 1] if i + 1 < len(rows) else ''
    mk = marker(s)
    if mk:
        close()
        if mk == 'UPDATES': MODE = 'updates'
        elif mk == 'FAQS': MODE = 'faq'
        elif mk == 'ARMY RULES': SCOPE, DET = 'army', None
        elif mk == 'DATASHEETS': SCOPE, DET = 'datasheets', None
        else: SCOPE, DET = 'detachment', mk[1]
        continue
    if MODE == 'faq':
        if s.startswith('Q:'): q = {'Q': s[2:].strip(), 'A': None}; faqs.append(q)
        elif s.startswith('A:') and q: q['A'] = s[2:].strip()
        elif q and q['A'] is None: q['Q'] += ' ' + s
        elif q: q['A'] += ' ' + s
        continue
    if inq:
        body.append(s)
        if ends_quote(s): inq = False; (None if nxt.startswith(BUL) else close())
        continue
    if body is not None:
        if s.startswith(OPENQ):   # the quoted text of a bullet that ended with a colon, or of a "Change to:" line
            body.append(s); inq = not ends_quote(s) or len(s) == 1
            if not inq and not nxt.startswith(BUL): close()
            continue
        if s.startswith(BUL) or (body and body[-1].endswith(':')):
            body.append(s)
            if s.count('‘') > s.count('’'): inq = True; continue   # a bullet that opens a quote and carries it over the next lines
            if s.endswith(':') and nxt.startswith(OPENQ): pass
            elif not nxt.startswith(BUL + OPENQ) and not (nxt and nxt[0].islower()): close()
            continue
        close()   # a new heading
    if CHANGE.search(s) or s.startswith(OPENQ) or s.startswith(BUL):
        if not head and entries: head = [entries[-1]['Heading']]   # a second change under the same heading
        body = [s]
        if s.startswith(OPENQ): inq = not ends_quote(s) or len(s) == 1
        elif s.count('‘') > s.count('’'): inq = True
        if inq: continue
        if s.endswith(':') and nxt.startswith(OPENQ): continue
        if nxt.startswith(BUL + OPENQ): continue
        close()
    else:
        head.append(s)
close()
# ---- attach
path = os.path.join(ddir, fname + '.json'); doc = json.load(open(path, encoding='utf-8-sig'))
units = {u['Name'].lower().replace('\u2019', "'"): u for u in doc['Units']}; names = sorted(units, key=len, reverse=True)
dets = {d['Name'].lower(): d for d in doc.get('Dettachments', [])}
def mention(txt, pool):
    out, t = [], txt.lower().replace('\u2019', "'")
    for n in pool:
        if re.search(r'(?<![a-z])' + re.escape(n) + r'(?![a-z])', t): out.append(n); t = t.replace(n, '\0' * len(n))
    return out
for u in doc['Units']: u.pop('Errata', None); u.pop('FAQ', None)
for d in doc.get('Dettachments', []): d.pop('Errata', None)
doc['Errata'] = []; doc['FAQ'] = []; stat = {'unit entries': 0, 'detachment entries': 0, 'army entries': 0, 'unplaced datasheet entries': 0, 'unit faq': 0, 'faq general': 0}
for e in entries:
    item = {'Title': e['Heading'], 'Text': e['Text']}
    if e['Scope'] == 'datasheets':
        hit = mention(e['Heading'], names)
        rest = e['Heading'].split(' \u2013 ')[-1] if ' \u2013 ' in e['Heading'] else e['Heading']   # "A, B, C \u2013 Resurrection Orb Ability" -> the subject
        for n in names: rest = re.sub(r'(?<![A-Za-z])' + re.escape(n) + r'(?![A-Za-z])', '', rest, flags=re.I)
        rest = re.sub(r'\s*,\s*', ' ', rest).strip(' ,-')
        item['Title'] = rest or 'Datasheet'
        for n in hit: units[n].setdefault('Errata', []).append(item); stat['unit entries'] += 1
        if not hit: doc['Errata'].append(dict(item, Scope='datasheets')); stat['unplaced datasheet entries'] += 1
    elif e['Scope'] == 'detachment' and e['Detachment'].lower() in dets:
        dets[e['Detachment'].lower()].setdefault('Errata', []).append(item); stat['detachment entries'] += 1
    else: doc['Errata'].append(dict(item, Scope=e['Scope'] or 'army')); stat['army entries'] += 1
for f in faqs:
    hit = mention(f['Q'] + ' ' + (f['A'] or ''), names)
    if hit:
        for n in hit[:3]: units[n].setdefault('FAQ', []).append(f); stat['unit faq'] += 1
    else: doc['FAQ'].append(f); stat['faq general'] += 1
src = re.search(r'VERSION ([\d.]+)', text(1)); doc['ErrataSource'] = {'Pack': 'Faction Pack', 'Version': src.group(1) if src else '', 'Pages': f'{first}-{last}'}
if '--date' in sys.argv: doc['ErrataSource']['Date'] = sys.argv[sys.argv.index('--date') + 1]
print(stat, 'entries', len(entries), 'faqs', len(faqs), 'pages', first, last)
if dump: json.dump({'entries': entries, 'faqs': faqs}, open(dump, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
if write: json.dump(doc, open(path, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
