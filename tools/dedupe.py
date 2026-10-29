"""Nothing is listed twice on a datasheet: a weapon that appears again under the same name (only the capitals differ) in the same group, and a keyword that appears twice.
The first spelling is kept; a repeated weapon is dropped only when its profile is the same.
usage: python -I -X utf8 tools/dedupe.py <data dir> [--write]"""
import glob, json, os, sys
d, write = sys.argv[1], '--write' in sys.argv
n_w = n_k = 0
for f in sorted(glob.glob(os.path.join(d, '*.json'))):
    nm = os.path.basename(f)
    if nm in ('DataInfo.json', 'FactionInfoData.json'): continue
    doc = json.load(open(f, encoding='utf-8')); ch = False
    for u in doc.get('Units', []):
        for g in u.get('Weapons', []):
            seen = {}; keep = []
            for w in g['Weapons']:
                k = w['Name'].lower().replace('’', "'")
                if k in seen and {x: y for x, y in seen[k].items() if x != 'Name'} == {x: y for x, y in w.items() if x != 'Name'}: n_w += 1; ch = True; continue
                seen[k] = w; keep.append(w)
            g['Weapons'] = keep
        for key in ('Keywords', 'FactionKeywords'):
            ks = u.get(key) or []; out = []
            for k in ks:
                if k.lower() in [x.lower() for x in out]: n_k += 1; ch = True
                else: out.append(k)
            u[key] = out
    if ch and write: json.dump(doc, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print({'repeated weapons removed': n_w, 'repeated keywords removed': n_k})
