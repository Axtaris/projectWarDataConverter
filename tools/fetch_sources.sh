#!/bin/bash
# Download the BSData catalogues and the MFM files into sources/bsd.
# Wahapedia's CSV export has to be downloaded by hand into sources/wh (see README).
cd "$(dirname "$0")/.." || exit 1
D=sources/bsd; mkdir -p "$D" sources/wh
CAT=https://raw.githubusercontent.com/BSData/wh40k-11e/main
MFM=https://raw.githubusercontent.com/BSData/wh40k-11e-mfm/main

enc() { python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$1" 2>/dev/null || python -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$1"; }

for f in "Warhammer 40,000" "Necrons" "Unaligned Forces" "Orks" "T'au Empire" "Tyranids" "Genestealer Cults" "Leagues of Votann" \
  "Aeldari - Aeldari Library" "Aeldari - Craftworlds" "Aeldari - Drukhari" \
  "Chaos - Chaos Daemons" "Chaos - Chaos Daemons Library" "Chaos - Chaos Knights" "Chaos - Chaos Knights Library" "Chaos - Chaos Space Marines" \
  "Chaos - Death Guard" "Chaos - Emperor's Children" "Chaos - Thousand Sons" "Chaos - World Eaters" \
  "Imperium - Adepta Sororitas" "Imperium - Adeptus Custodes" "Imperium - Adeptus Mechanicus" "Imperium - Agents of the Imperium" \
  "Imperium - Astra Militarum" "Imperium - Astra Militarum - Library" "Imperium - Grey Knights" "Imperium - Imperial Knights" "Imperium - Imperial Knights - Library" \
  "Imperium - Space Marines" "Imperium - Black Templars" "Imperium - Blood Angels" "Imperium - Dark Angels" "Imperium - Deathwatch" \
  "Imperium - Imperial Fists" "Imperium - Iron Hands" "Imperium - Raven Guard" "Imperium - Salamanders" "Imperium - Space Wolves" "Imperium - Ultramarines" "Imperium - White Scars" \
  "Library - Astartes Heresy Legends" "Library - Titans" "Library - Tyranids"; do
  [ -f "$D/$f.json" ] || curl -fsSL -o "$D/$f.json" "$CAT/$(enc "$f").json" || echo "failed: $f"
done

for y in adepta-sororitas adeptus-custodes adeptus-mechanicus aeldari astra-militarum black-templars blood-angels chaos-daemons chaos-knights \
  chaos-space-marines dark-angels death-guard deathwatch drukhari emperors-children genestealer-cults grey-knights imperial-agents imperial-knights \
  leagues-of-votann necrons orks space-marines space-wolves tau-empire thousand-sons tyranids world-eaters; do
  [ -f "$D/$y.yaml" ] || curl -fsSL -o "$D/$y.yaml" "$MFM/data/$y.yaml" || echo "failed: $y"
done
echo "sources ready in $D (now add the Wahapedia CSV export to sources/wh)"
