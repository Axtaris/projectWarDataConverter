#!/bin/bash
# Full pipeline: convert each faction into data_bsd/ (units only, Legends are out of scope), then three-way reports into informes/.
B="sources/bsd"
cd "$(dirname "$0")/.." || exit 1
SM="Imperium - Space Marines|Library - Astartes Heresy Legends|Imperium - Agents of the Imperium|Library - Titans|Imperium - Imperial Knights - Library"
conv() { # name bsdfile mfm whfids libs report alias
  local n="$1" b="$2" m="$3" w="$4"; local L=(); IFS='|' read -ra A <<< "$5"; for l in "${A[@]}"; do [ -n "$l" ] && L+=(--lib "$B/$l.json"); done
  local WB="baseline"; [ -f "baseline_ext/$n.json" ] && WB="baseline_ext"
  python -I -X utf8 tools/bsd2pw.py --bsd "$B/$b.json" "${L[@]}" --gs "$B/Warhammer 40,000.json" --mfm "$B/$m.yaml" --wh "$w" --wo "$WB/$n.json" --out "data_bsd/$n.json" | head -1
  if [[ "$6" == capitulo-* ]]; then
    case "$n" in "Imperial Fists"|"Iron Hands"|"Raven Guard"|"Salamanders"|"Ultramarines"|"White Scars") cy="-";; *) cy="$B/$m.yaml";; esac
    python -I -X utf8 tools/chapter.py "$n" "$cy" "$WB/$n.json"
  fi
  python -X utf8 tools/three_way.py --name "$n" --wh "$w" --mfm "$B/$m.yaml" --out "informes/$6.md" --alias "$7" --wo-dir "$WB" | cut -c1-70
}
python -I -X utf8 tools/chapter_baseline.py > /dev/null
ONLY="$1"
run() { [ -z "$ONLY" ] || [ "$ONLY" = "$6" ] && conv "$@"; }
run "Necrons" "Necrons" necrons NEC "Unaligned Forces" necrons ""
run "Adeptus Custodes" "Imperium - Adeptus Custodes" adeptus-custodes AC,AoI,QI,TL "Imperium - Imperial Knights - Library|Imperium - Agents of the Imperium|Library - Titans" custodes "Prosecutors=Prosecutor Squad;Witchseekers=Witchseeker Squad;Vigilators=Vigilator Squad;Custodian Guard=Custodian Guard Sodality"
run "Space Marines" "Imperium - Space Marines" space-marines SM,AoI,QI,TL "Library - Astartes Heresy Legends|Imperium - Agents of the Imperium|Library - Titans|Imperium - Imperial Knights - Library" space-marines "Eradicator Squad=Eradicator Squad With Melta Rifles"
for c in "Black Templars:black-templars" "Blood Angels:blood-angels" "Dark Angels:dark-angels" "Deathwatch:deathwatch" "Space Wolves:space-wolves" "Imperial Fists:space-marines" "Iron Hands:space-marines" "Raven Guard:space-marines" "Salamanders:space-marines" "Ultramarines:space-marines" "White Scars:space-marines"; do
  n="${c%%:*}"; y="${c##*:}"; slug=$(echo "$n" | tr 'A-Z ' 'a-z-')
  run "$n" "Imperium - $n" "$y" SM,AoI,QI,TL "$SM" "capitulo-$slug" ""
done
run "Adepta Sororitas" "Imperium - Adepta Sororitas" adepta-sororitas AS "Imperium - Agents of the Imperium|Imperium - Imperial Knights - Library|Library - Titans|Imperium - Astra Militarum - Library" adepta-sororitas ""
run "Adeptus Mechanicus" "Imperium - Adeptus Mechanicus" adeptus-mechanicus AdM "Imperium - Agents of the Imperium|Imperium - Imperial Knights - Library|Library - Titans|Imperium - Astra Militarum - Library" adeptus-mechanicus ""
run "Astra Militarum" "Imperium - Astra Militarum" astra-militarum AM "Imperium - Agents of the Imperium|Imperium - Imperial Knights - Library|Library - Titans|Imperium - Astra Militarum - Library" astra-militarum ""
run "Grey Knights" "Imperium - Grey Knights" grey-knights GK "Imperium - Agents of the Imperium|Imperium - Imperial Knights - Library|Library - Titans|Imperium - Astra Militarum - Library" grey-knights ""
run "Imperial Agents" "Imperium - Agents of the Imperium" imperial-agents AoI "Imperium - Agents of the Imperium|Imperium - Imperial Knights - Library|Library - Titans|Imperium - Astra Militarum - Library" imperial-agents ""
run "Imperial Knights" "Imperium - Imperial Knights - Library" imperial-knights QI "Imperium - Imperial Knights|Imperium - Agents of the Imperium|Library - Titans|Imperium - Astra Militarum - Library" imperial-knights ""
run "Aeldari" "Aeldari - Craftworlds" aeldari AE "Aeldari - Aeldari Library" aeldari ""
run "Drukhari" "Aeldari - Drukhari" drukhari DRU "Aeldari - Aeldari Library" drukhari ""
run "Chaos Daemons" "Chaos - Chaos Daemons Library" chaos-daemons CD "Chaos - Chaos Daemons|Chaos - Chaos Knights Library|Library - Titans" chaos-daemons ""
run "Chaos Knights" "Chaos - Chaos Knights Library" chaos-knights QT "Chaos - Chaos Knights|Chaos - Chaos Daemons Library|Library - Titans" chaos-knights ""
run "Chaos Space Marines" "Chaos - Chaos Space Marines" chaos-space-marines CSM "Chaos - Chaos Daemons Library|Chaos - Chaos Knights Library|Library - Titans" chaos-space-marines ""
run "Death Guard" "Chaos - Death Guard" death-guard DG "Chaos - Chaos Daemons Library|Chaos - Chaos Knights Library|Library - Titans" death-guard ""
run "Emperor's Children" "Chaos - Emperor's Children" emperors-children EC "Chaos - Chaos Daemons Library|Chaos - Chaos Knights Library|Library - Titans" emperors-children ""
run "Thousand Sons" "Chaos - Thousand Sons" thousand-sons TS "Chaos - Chaos Daemons Library|Chaos - Chaos Knights Library|Library - Titans" thousand-sons ""
run "World Eaters" "Chaos - World Eaters" world-eaters WE "Chaos - Chaos Daemons Library|Chaos - Chaos Knights Library|Library - Titans" world-eaters ""
run "Genestealer Cults" "Genestealer Cults" genestealer-cults GC "Library - Tyranids" genestealer-cults ""
run "Leagues of Votann" "Leagues of Votann" leagues-of-votann LoV "" leagues-of-votann ""
run "Orks" "Orks" orks ORK "" orks ""
run "Tau Empire" "T'au Empire" tau-empire TAU "" tau-empire ""
run "Tyranids" "Tyranids" tyranids TYR "Library - Tyranids" tyranids ""
