"""Hand-verified corrections (checked against Wahapedia 11th) applied on top of data_new/*.json after apply.py. Idempotent.
  python -I -X utf8 tools/fixes.py [dir]"""
import json, sys, os
D = sys.argv[1] if len(sys.argv) > 1 else 'data_new'

def load(f): return json.load(open(f'{D}/{f}.json', encoding='utf-8-sig'))
def save(f, d): json.dump(d, open(f'{D}/{f}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
def unit(d, n): return next(u for u in d['Units'] if u['Name'] == n)
def model(u, n=None): return next(m for m in u['UnitComposition']['ModelCompositions'] if n is None or m['ModelName'] == n)
def wg(m): return m['Wargear'][0]

# ---- Astra Militarum
d = load('Astra Militarum')
model(unit(d, 'GAUNT’S GHOSTS'), 'Tanith Ghosts')['Limit'] = {'Min': 5, 'Max': 5}  # 1 Gaunt + 5 Tanith Ghosts = 6 models
model(unit(d, 'CATACHAN COMMAND SQUAD'), 'Veteran Guardsmen')['Limit'] = {'Min': 4, 'Max': 4}  # 1 Commander + 4
for n in ('ROGAL DORN BATTLE TANK', 'ROGAL DORN COMMANDER'):  # twin battle cannon -> oppressor cannon + coaxial autocannon
    w = wg(model(unit(d, n)))
    w['Options'] = [o for o in w['Options'] if o.get('Options') != ['Coaxial autocannon']]
    if not any(o.get('Replaces') == ['twin battle cannon'] for o in w['Options']):
        w['Options'].insert(1, {'Replaces': ['twin battle cannon'], 'Options': ['Oppressor cannon and coaxial autocannon']})
unit(d, 'NORK DEDDOG')['LeaderInfo'] = None  # no Leader rule in 11th (Loyal Protector stays as an ability)
save('Astra Militarum', d)

# ---- Orks
d = load('Orks')
g = unit(d, 'GRETCHIN')  # Runtherd is its own datasheet in 11th: Gretchin are 10-20 models
g['UnitComposition']['ModelCompositions'] = [m for m in g['UnitComposition']['ModelCompositions'] if m['ModelName'] != 'Runtherds']
wg(model(g, 'Gretchin'))['InitalWargear'] = ['scavenged shivs', 'grot blasta']
for w in unit(d, 'MEGANOBZ')['Weapons'][0]['Weapons'] + [x for gg in unit(d, 'MEGANOBZ')['Weapons'] for x in gg['Weapons']]:
    if w['Name'] == 'Twin killsaw': w.update(Attacks='3', Strength='10', AP='-2', Damage='3')  # Wahapedia + BSData: Twin Killsaws A3 S10 AP-2 D3
set_init = lambda n, init, opts=None, m=None: (wg(model(unit(d, n), m)).update(InitalWargear=init, **({'Options': opts} if opts is not None else {})))
set_init('WARTRAKKS', ['multi-busta launcha', 'kustom choppa', 'kustom shoota'], [])
set_init('RUNTHERD', ['runtherd’s toolz', 'slugga'], [])
set_init('GUNWAGON', ['crushin’ bulk', 'kannon'], [{'Options': ['Wreckin’ Ball']}, {'Options': ['Grabbin’ Klaw']}, {'Options': ['Lobba']}, {'Options': ['Big Shoota'], 'Max': 4}, {'Replaces': ['kannon'], 'Options': ['Killkannon', 'Zzap Gun']}])
for m in unit(d, 'WARBUGGIES')['UnitComposition']['ModelCompositions']:
    w = wg(m)
    for x in ('extra dakka', 'spiked ram'):
        if x not in w['InitalWargear']: w['InitalWargear'].append(x)
g = unit(d, 'GHAZGHKULL THRAKA')  # 11th: 1 model, no Leader rule (Wahapedia + BSData)
g['UnitComposition']['ModelCompositions'] = [m for m in g['UnitComposition']['ModelCompositions'] if m['ModelName'] != 'Makari']
g['LeaderInfo'] = None
save('Orks', d)

# ---- other armies
d = load('Leagues of Votann')
model(unit(d, 'BRÔKHYR IRON-MASTER'), 'E-COG')['Limit'] = {'Min': 3, 'Max': 3}  # 1 Iron-master + 1 Ironkin Assistant + 3 E-COGs = 5 models
save('Leagues of Votann', d)
d = load('Tau Empire')
u = unit(d, 'BROADSIDE BATTLESUITS')  # 1 Shas'vre + 0-2 Shas'ui
model(u, 'Broadside Shas’vre').pop('Limit', None); model(u, 'Broadside Shas’ui')['Limit'] = {'Min': 0, 'Max': 2}
save('Tau Empire', d)
d = load('Adepta Sororitas')
w = wg(model(unit(d, 'CANONESS')))
for o in ({'Options': ['Brazier of holy fire', 'Null rod']}, {'Options': ['Rod of office']}):
    if o not in w['Options']: w['Options'].append(o)
save('Adepta Sororitas', d)
print('fixes ok')
