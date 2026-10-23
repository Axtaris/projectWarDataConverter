#!/bin/bash
# Copy the applied factions (data_new/) into a projectWar checkout and stamp the data version.
# usage: tools/deploy.sh [projectWar dir] [data version]
cd "$(dirname "$0")/.." || exit 1
T="${1:-../projectWar}"; V="${2:-11.3}"
for f in data_new/*.json; do case "$f" in */_*) continue;; esac; cp "$f" "$T/data/"; done
python -I -X utf8 - "$T/data/DataInfo.json" "$V" <<'PY'
import json, sys
p, v = sys.argv[1:3]; d = json.load(open(p, encoding='utf-8-sig')); d['Version'] = v; json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
PY
echo "deployed to $T/data (data version $V)"
