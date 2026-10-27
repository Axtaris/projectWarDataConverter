# projectWarDataConverter

The tool that builds the faction data for [projectWar](https://github.com/Axtaris/projectWar) from community sources. Its output is published separately in [projectWarData](https://github.com/Axtaris/projectWarData).

> **Work in progress.** It reproduces the current data set, but it is a research tool with rough edges: heuristics for wargear options, a few hand-made corrections, and no automated tests.

## What it does

Three upstream sources describe the same game in different ways. The converter reads all three, compares them field by field, and writes the result in projectWar's JSON format:

| Source | Role |
|---|---|
| [BSData `wh40k-11e`](https://github.com/BSData/wh40k-11e) (BattleScribe JSON catalogues) | Units, weapons, abilities, keywords, compositions |
| [BSData `wh40k-11e-mfm`](https://github.com/BSData/wh40k-11e-mfm) (Munitorum Field Manual as YAML) | Official points, detachment points, enhancement costs, change log, `legends` flag |
| Wahapedia 11th edition CSV export | Rules text, loadouts, stratagems, detachment rules, which datasheets exist |

The pipeline has three stages:

1. **Convert** (`tools/bsd2pw.py`, `tools/chapter.py`): BSData to projectWar format, one faction at a time. Prices are rebuilt from BSData's modifiers, and the MFM wins when they differ. Detachments merge MFM points, BSData text and Wahapedia stratagems (`tools/wh_load.py`).
2. **Compare** (`tools/three_way.py`): for every unit and field it labels the current value against the other sources and writes a Markdown report.
3. **Apply** (`tools/apply.py`, then `tools/fixes.py`): changes only what the comparison justifies, keeps hand-curated fields, and writes the new faction files.

### Verdicts

| Verdict | Meaning | Action |
|---|---|---|
| `OK` | The current value is held by at least one other source | none |
| `UPDATE` | Two or more sources agree on a different value | applied |
| `UPDATE*` | BSData and Wahapedia disagree | Wahapedia wins; listed for spot checks |
| `REVIEW` | Only one source differs, with no support | not applied; check by hand |
| `NO SOURCES` | Nothing to compare against | none |

### Policies

- Points: the MFM always wins.
- Texts and starting loadouts: Wahapedia wins over BSData (BSData has typos and truncated texts).
- Units in neither Wahapedia nor the MFM are retired and removed. Legends units are excluded.
- Renamed units are detected by content similarity plus a manual alias map.
- `tools/fixes.py` holds the hand-verified corrections that no source can express. It is idempotent.

### Space Marine chapters

A chapter is a customisation of the Space Marines roster, so `tools/chapter.py` builds each chapter file as *the whole shared roster plus the chapter's own units*. Chapters with their own Munitorum file (Black Templars, Blood Angels, Dark Angels, Deathwatch, Space Wolves) take their roster, points and detachments from it. The other six (Imperial Fists, Iron Hands, Raven Guard, Salamanders, Ultramarines, White Scars) get the full shared roster at base points and every Space Marines detachment except the ones locked to another chapter (see `LOCKED` in `chapter.py`). Units that carry another chapter's keyword are never shared. `tools/chapter_baseline.py` extends the baseline of those six with the shared units so their hand-curated fields are kept.

## Requirements

- Python 3.10+ with PyYAML (`pip install pyyaml`) and a POSIX shell (Git Bash on Windows works).
- Roughly 60 MB of disk for the downloaded sources.

## Setup

```bash
git clone https://github.com/Axtaris/projectWarDataConverter.git
cd projectWarDataConverter

bash tools/fetch_sources.sh         # BSData catalogues + MFM files into sources/bsd
# Wahapedia: download the 11th edition CSV export and unzip it into sources/wh
#            (Datasheets.csv, Datasheets_models.csv, Stratagems.csv, ... pipe-separated)

git clone https://github.com/Axtaris/projectWarData.git baseline   # the data set to update
```

`baseline/` is the *current* data set. The converter never modifies it; it writes new files next to it.

## Running

```bash
bash tools/all.sh                   # convert every faction and write reports to informes/
bash tools/apply_all.sh             # apply the decisions into data_new/ and print a self-check per faction
bash tools/deploy.sh ../projectWar 11.3   # copy data_new/ into a checkout's data/ and stamp the data version
```

Last step, `python -I -X utf8 tools/wh_authority.py <data dir> [--write]`: Wahapedia (11th edition) is the authority for what it publishes, so stat lines, ability names and ability texts are forced to its values (BSData still lags behind the 10th edition and can agree with stale data). Dry run unless `--write`.

Both scripts accept a faction name to run just one, for example `bash tools/all.sh necrons` (report name) and `bash tools/apply_all.sh Necrons`. After `apply_all.sh`, the self-check should show almost only `OK`; a few `UPDATE` / `REVIEW` rows are normal.

### Folders

| Folder | Content | In git? |
|---|---|---|
| `tools/` | The pipeline | yes |
| `sources/` | Downloaded upstream data | no |
| `baseline/` | The data set being updated | no |
| `baseline_ext/` | Baseline of the six codex chapters extended with the shared roster (generated) | no |
| `data_bsd/` | Converted output and per-faction review notes | no |
| `informes/` | Three-way comparison reports (Markdown) | no |
| `data_new/` | Final output, ready to deploy | no |

## Adding or updating a faction

Factions are listed in `tools/all.sh` and `tools/apply_all.sh` with: the BSData file, the MFM slug, the Wahapedia faction ids, the library catalogues it imports, and optional unit aliases. For factions whose roster lives in a "Library" catalogue (for example Imperial Knights or Chaos Daemons), pass the library as the main file.

## Limitations

- Wargear options are inferred from BSData groups and Wahapedia option text. They are right for most units, not all.
- Enhancements and detachments new in 11th get text and costs but no structured effects.
- The reports are generated English Markdown meant for a human reviewer; they are not part of the output.
- Wahapedia data has to be downloaded by hand, and its terms of use apply.

## License

Public domain under the [Unlicense](https://unlicense.org) (see `LICENSE`). The upstream data keeps its own licences and terms; *Warhammer 40,000* is a trademark of Games Workshop Ltd and this is an unofficial fan project.
