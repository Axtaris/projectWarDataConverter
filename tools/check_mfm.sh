#!/bin/bash
# Tells whether the official Munitorum Field Manual (as scraped by BSData/wh40k-11e-mfm from mfm.warhammer-community.com) has changed since the files in sources/bsd.
# Printed or PDF copies of the manual are out of date from day one; this is the live source.
cd "$(dirname "$0")/.." || exit 1
RAW=https://raw.githubusercontent.com/BSData/wh40k-11e-mfm/main
curl -fsSL "$RAW/data/meta.yaml" | grep -E '^(version|lastUpdated):'
n=0; for f in sources/bsd/*.yaml; do b=$(basename "$f"); if ! curl -fsSL "$RAW/data/$b" | diff -q - "$f" >/dev/null 2>&1; then echo "changed upstream: $b"; n=$((n+1)); fi; done
echo "$n faction files differ from your copy"; [ "$n" -gt 0 ] && echo "update them with tools/fetch_sources.sh (delete the old yaml first), then run tools/all.sh and tools/apply_all.sh"
