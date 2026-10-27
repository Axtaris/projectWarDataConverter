#!/bin/bash
# Apply the conversions to data_new/ (always starting from the pristine backup) and print each self-check.
B="sources/bsd"
cd "$(dirname "$0")/.." || exit 1
ap() { # name whids mfm alias
  local SRC="baseline"; [ -f "baseline_ext/$1.json" ] && SRC="baseline_ext"
  PYTHONPATH=tools python -X utf8 tools/apply.py --name "$1" --wh "$2" --mfm "$B/$3.yaml" --alias "$4" --src "$SRC" 2>&1 | tail -1
  python -X utf8 tools/three_way.py --name "$1" --wh "$2" --mfm "$B/$3.yaml" --wo-dir data_new --alias "" --out data_new/_verify.md | python -X utf8 -c "
import sys,ast,collections
line=sys.stdin.read().strip(); d=ast.literal_eval(line.split(' ',1)[1]); c=collections.Counter()
for f,v in d.items():
    for k,n in v.items(): c[k]+=n
print('   self-check:',dict(c))"
}
ONLY="$1"
run() { [ -z "$ONLY" ] || [ "$ONLY" = "$1" ] && ap "$@"; }
run "Necrons" NEC necrons ""
run "Adeptus Custodes" AC,AoI,QI,TL adeptus-custodes "Prosecutors=Prosecutor Squad;Witchseekers=Witchseeker Squad;Vigilators=Vigilator Squad;Custodian Guard=Custodian Guard Sodality"
run "Space Marines" SM,AoI,QI,TL space-marines "Eradicator Squad=Eradicator Squad With Melta Rifles"
for c in "Black Templars:black-templars" "Blood Angels:blood-angels" "Dark Angels:dark-angels" "Deathwatch:deathwatch" "Space Wolves:space-wolves" "Imperial Fists:space-marines" "Iron Hands:space-marines" "Raven Guard:space-marines" "Salamanders:space-marines" "Ultramarines:space-marines" "White Scars:space-marines"; do
  run "${c%%:*}" SM,AoI,QI,TL "${c##*:}" ""
done
run "Adepta Sororitas" AS adepta-sororitas ""
run "Adeptus Mechanicus" AdM adeptus-mechanicus ""
run "Astra Militarum" AM astra-militarum ""
run "Grey Knights" GK grey-knights ""
run "Imperial Agents" AoI imperial-agents ""
run "Imperial Knights" QI imperial-knights ""
run "Aeldari" AE aeldari ""
run "Drukhari" DRU drukhari ""
run "Chaos Daemons" CD chaos-daemons ""
run "Chaos Knights" QT chaos-knights ""
run "Chaos Space Marines" CSM chaos-space-marines ""
run "Death Guard" DG death-guard ""
run "Emperor's Children" EC emperors-children ""
run "Thousand Sons" TS thousand-sons ""
run "World Eaters" WE world-eaters ""
run "Genestealer Cults" GC genestealer-cults ""
run "Leagues of Votann" LoV leagues-of-votann ""
run "Orks" ORK orks ""
run "Tau Empire" TAU tau-empire ""
run "Tyranids" TYR tyranids ""
python -I -X utf8 tools/fixes.py data_new
