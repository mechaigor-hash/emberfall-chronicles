# Overnight Agent Log

This file is for autonomous iteration notes before the 08:00 UK check-in.

## Initial brief

- Python based project
- Fantasy RPG, retro theme
- Create GitHub repo
- Iterate overnight

## Current baseline

- Standard-library Python RPG engine
- CLI entry point: `emberfall`
- Procedural ASCII dungeon
- Save/load JSON files
- Deterministic simulation command
- Pytest coverage for core engine behavior
- GitHub Actions CI

## 2026-06-01 23:59 BST — hero status command

Changed:
- Added a `hero_sheet` engine helper that summarizes Kalidor's level, HP, attack, defense, gold, XP progress, inventory, and adventure status.
- Added a new `emberfall status [save]` CLI command for checking a save file without rendering the full map.
- Added regression coverage for the hero sheet output and documented the new command in the README.

Verification:
- `uv run pytest` → 8 passed in 0.07s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 23 --save /tmp/emberfall-status-cron.json` → created and rendered a deterministic save successfully.
- `uv run emberfall status /tmp/emberfall-status-cron.json` → printed level 1 Kalidor with 24/24 HP, Weathered Blade, and "still delving" status.

## 2026-06-01 23:28 BST — relic stat effects

Changed:
- Treasure relics now apply deterministic mechanical effects when collected instead of only adding names to inventory.
- Added five item effect messages covering defense, attack, max HP, healing, and hybrid boosts.
- Added regression coverage proving treasure pickup changes player stats and records the relic effect in the log.
- Updated README gameplay notes to explain that relics grant stat boons.

Verification:
- `uv run pytest` → 7 passed in 0.07s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall simulate --seed 11 --steps 40` → command rendered a delve successfully; outcome was "still delving".

## 2026-06-01 22:55 BST — stalking monster AI

Changed:
- Added scent-radius monster stalking: non-adjacent monsters within 6 tiles now step toward Kalidor when there is an open, unoccupied move that reduces distance.
- Adjacent monsters still attack immediately, preserving the existing combat loop.
- Added regression coverage for a monster closing distance after the player takes a turn.
- Updated README gameplay notes and roadmap to reflect active monster pursuit.

Verification:
- `uv run pytest` → 6 passed in 0.06s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall simulate --seed 11 --steps 20` → command rendered a delve successfully; outcome was "still delving".

## 2026-06-02 00:32 BST — safe rest command

Changed:
- Added an engine-level `rest` action that spends a turn and restores up to 2 HP when no living monster is within two tiles.
- Nearby monsters now interrupt resting, preserving danger and still taking their normal turn.
- Added a new `emberfall rest [save]` CLI command and documented it in the README command list and gameplay notes.
- Added regression coverage for both successful resting and monster-interrupted resting.

Verification:
- `uv run pytest` → 10 passed in 0.07s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 31 --save /tmp/emberfall-rest-cron.json && uv run emberfall rest /tmp/emberfall-rest-cron.json` → created a deterministic save, ran the new rest command, rendered the game, and logged "Kalidor listens to the dungeon's old static." for a full-health safe rest.

## 2026-06-02 01:04 BST — adjacent look command

Changed:
- Added an engine-level `look` helper that describes the four adjacent spaces without mutating game state or advancing monster turns.
- Added a new `emberfall look [save]` CLI command for safely scouting nearby walls, corridors, monsters, treasure, shrines, and the ember gate.
- Added regression coverage proving look reports adjacent features and leaves the save state unchanged.
- Documented the new scouting command in the README quick start, gameplay notes, and command list.

Verification:
- `uv run pytest` → 11 passed in 0.07s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 44 --save /tmp/emberfall-look-cron.json && uv run emberfall look /tmp/emberfall-look-cron.json` → created a deterministic save and printed adjacent-space scouting output: north/west walls and south/east open corridors.

## 2026-06-02 01:37 BST — objectives route summary

Changed:
- Added an engine-level `objectives` helper that summarizes the ember gate route, remaining treasure and shrine counts, living monsters, and current fate without mutating game state.
- Added a new `emberfall objectives [save]` CLI command for quick quest guidance between turns.
- Reused the simulation BFS pathing through a shared route helper so objective hints use the same passability rules as automated delves.
- Added regression coverage for objective summaries and documented the command in the README quick start, gameplay notes, and command list.

Verification:
- `uv run pytest` → 12 passed in 0.08s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 52 --save /tmp/emberfall-objectives-cron.json && uv run emberfall objectives /tmp/emberfall-objectives-cron.json` → created a deterministic save and printed objective guidance: ember gate 42 steps away, treasures 13 steps away, shrines 14 steps away, and 5 monsters alive.

## 2026-06-02 02:10 BST — inventory command

Changed:
- Added an engine-level `inventory_report` helper that lists Kalidor's gold, carried gear, and known relic boon text without mutating game state.
- Added a new `emberfall inventory [save]` CLI command for quick equipment and relic-effect planning.
- Added regression coverage for the inventory report and documented the command in the README quick start, gameplay notes, and command list.

Verification:
- `uv run pytest` → 13 passed in 0.08s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 61 --save /tmp/emberfall-inventory-cron.json && uv run emberfall inventory /tmp/emberfall-inventory-cron.json` → created a deterministic save and printed Kalidor's 0 gold plus Weathered Blade inventory entry.

## 2026-06-02 02:42 BST — monster threat report

Changed:
- Added an engine-level `threat_report` helper that ranks living monsters by distance from Kalidor and labels immediate, rest-blocking, stalking, and distant danger bands.
- Added a new `emberfall threats [save]` CLI command for checking monster danger and rest safety without advancing a turn.
- Added regression coverage proving the threat report ranks monsters, reports unsafe rest conditions, and does not mutate game state.
- Documented the threats command in the README quick start, gameplay notes, and command list.

Verification:
- `uv run pytest` → 14 passed in 0.09s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 72 --save /tmp/emberfall-threats-cron.json && uv run emberfall threats /tmp/emberfall-threats-cron.json` → created a deterministic save and printed five ranked monster threats plus "Rest outlook: safe for now.".

## 2026-06-02 03:15 BST — adventure log command

Changed:
- Added an engine-level `adventure_log` helper that formats recent turn messages as a numbered journal without mutating game state.
- Added a new `emberfall log [save] --limit N` CLI command for reviewing recent events after multi-command or automated delves.
- Added regression coverage for journal limiting, numbering, and non-mutation behavior.
- Documented the new command in the README quick start, gameplay notes, and command list.

Verification:
- `uv run pytest` → 15 passed in 0.10s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 83 --save /tmp/emberfall-log-cron.json && uv run emberfall move east /tmp/emberfall-log-cron.json && uv run emberfall log /tmp/emberfall-log-cron.json --limit 3` → created a deterministic save, advanced one turn, and printed a two-entry numbered journal ending with a monster stalking message.

## 2026-06-02 03:48 BST — map legend command

Changed:
- Added an engine-level `legend` helper that explains each ASCII map glyph while including live hero HP, monster, treasure, shrine, and ember-gate status counts.
- Added a new `emberfall legend [save]` CLI command for quick map orientation without advancing turns or mutating saves.
- Added regression coverage proving the legend output reports live counts and leaves game state unchanged.
- Documented the legend command in the README quick start, gameplay notes, and command list.

Verification:
- `uv run pytest` → 16 passed in 0.10s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 94 --save /tmp/emberfall-legend-cron.json && uv run emberfall legend /tmp/emberfall-legend-cron.json` → created a deterministic save and printed the new map legend with 5 monsters, 4 relic caches, 2 shrines, and the ember gate objective.

## 2026-06-02 04:20 BST — field bestiary command

Changed:
- Added an engine-level `bestiary` helper that groups living monsters by type and summarizes HP, attack, defense, XP, gold, nearest distance, and threat wording without mutating state.
- Added a new `emberfall bestiary [save]` CLI command for combat planning before choosing a route or rest.
- Added regression coverage for grouped stat/reward ranges and non-mutation behavior.
- Documented the bestiary command in the README quick start, gameplay notes, and command list.

Verification:
- `uv run pytest` → 17 passed in 0.10s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 105 --save /tmp/emberfall-bestiary-cron.json && uv run emberfall bestiary /tmp/emberfall-bestiary-cron.json` → created a deterministic save and printed grouped bone imp and rust knight bestiary entries with stat/reward ranges and nearest-distance warnings.

## 2026-06-02 04:53 BST — route planner command

Changed:
- Added an engine-level `route_plan` helper that prints a concrete shortest safe path without mutating game state.
- Added a new `emberfall route [save] --goal any|exit|treasure|shrine` CLI command for turn-free navigation planning.
- Added regression coverage for successful treasure routing and missing-objective reporting.
- Documented the route command in the README quick start, gameplay notes, and command list.

Verification:
- `uv run pytest` → 19 passed in 0.08s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 42 --save <tmp>/route.json && uv run emberfall route <tmp>/route.json --goal treasure` → created a deterministic save and printed an 18-step route to a treasure cache, first move south.

## 2026-06-02 05:26 BST — combat odds command

Changed:
- Added an engine-level `combat_advice` helper that estimates adjacent fight odds without mutating game state.
- The report shows damage dealt both ways, swings needed to defeat adjacent enemies, enemy survival margin, and a favorable/dangerous outlook.
- Added a new `emberfall combat [save]` CLI command plus README quick-start, gameplay, and command-list documentation.
- Added regression coverage for adjacent combat math, nearest-threat fallback, and non-mutation behavior.

Verification:
- `uv run pytest` → 21 passed in 0.09s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 117 --save <tmp>/combat.json && uv run emberfall combat <tmp>/combat.json` → created a deterministic save and printed the combat-advice report with no adjacent enemy, nearest ash goblin 15 steps away, and a tactical hint.

## 2026-06-02 06:00 BST — tactical hint command

Changed:
- Added an engine-level `tactical_hint` helper that recommends one next action without mutating game state.
- The hint logic considers completed/failed runs, adjacent combat odds, low-HP resting, shrine routes, treasure routes, and the ember gate.
- Added a new `emberfall hint [save]` CLI command and documented it in the README quick start, gameplay notes, and command list.
- Added regression coverage for treasure-route, safe-rest, and winnable-adjacent-attack recommendations.

Verification:
- `uv run pytest` → 24 passed in 0.09s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 128 --save <tmp>/hint.json && uv run emberfall hint <tmp>/hint.json` → created a deterministic save and printed "Recommended action: move south toward treasure for relic boons.".

## 2026-06-02 06:33 BST — score card command

Changed:
- Added an engine-level `score_report` helper that converts gold, XP, level, relics, defeated monsters, and fate into a deterministic delve score.
- Added a new `emberfall score [save]` CLI command for comparing runs without advancing turns.
- Added regression coverage proving the score card summarizes progress and does not mutate game state.
- Documented the score command in the README quick start, gameplay notes, and command list.

Verification:
- `uv run pytest` → 25 passed in 0.15s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 44 --save /tmp/emberfall-score.json && uv run emberfall score /tmp/emberfall-score.json` → created a deterministic save and printed score 15 with 0 gold, 0 XP, 0 relics, and 5 monsters still hunting.

## 2026-06-02 07:06 BST — immediate choices command

Changed:
- Added an engine-level `action_report` helper that lists all four immediate moves without mutating game state.
- The report calls out walls, open corridors, treasure caches, healing shrines, ember-gate exits, and adjacent combat odds where relevant.
- Added a new `emberfall choices [save]` CLI command and README documentation for quick turn-by-turn decision support.
- Added regression coverage proving the choices report covers all nearby outcomes and leaves state unchanged.

Verification:
- `uv run pytest` → 26 passed in 0.15s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 139 --save /tmp/emberfall-choices.json && uv run emberfall choices /tmp/emberfall-choices.json` → created a deterministic save and printed the choices report with north/west blocked, south/east open, and a suggested move toward treasure.

## 2026-06-02 07:38 BST — torch-fog map view

Changed:
- Added a `--fog` option to `emberfall show` so saved games can be rendered through Kalidor's limited torchlight instead of always revealing the full dungeon.
- Reused the engine's existing fog renderer for CLI play, preserving the normal full-map `show` behavior by default.
- Added regression coverage proving fog rendering keeps nearby tiles visible while hiding distant exits.
- Documented the fog view in the README quick start, gameplay notes, and command list.

Verification:
- `uv run pytest` → 27 passed in 0.15s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 44 --save /tmp/emberfall-fog-cron.json && uv run emberfall show /tmp/emberfall-fog-cron.json --fog` → created a deterministic save and rendered only the torchlit north-west section around Kalidor, hiding the distant ember gate.

## 2026-06-02 08:12 BST — monster route target

Changed:
- Extended `route_plan` and the `emberfall route` CLI so `--goal monster` plots a path to the nearest living monster for deliberate combat planning.
- Updated route destination naming so monster routes report the specific target, and pathfinding can end on a monster tile while still treating other monsters as blockers.
- Added regression coverage proving monster routing chooses the nearest target and does not mutate state.
- Documented the new route goal in the README quick start, gameplay notes, and command list.

Verification:
- `uv run pytest` → 28 passed in 0.17s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 77 --save /tmp/emberfall-monster-route-cron.json && uv run emberfall route /tmp/emberfall-monster-route-cron.json --goal monster` → created a deterministic save and printed a monster route to a cinder wraith 13 steps away, first move south.

## 2026-06-02 08:46 BST — ANSI color map renderer

Changed:
- Added an optional ANSI color palette to the engine renderer for Kalidor, walls, floors, monsters, treasure, shrines, and the ember gate.
- Added `--color` rendering flags for `emberfall new`, `show`, `move`, `rest`, and `simulate` while preserving plain ASCII output by default.
- Added regression coverage proving colored rendering emits expected ANSI glyphs without mutating game state.
- Documented color rendering in the README quick start, gameplay notes, command list, and roadmap.

Verification:
- `uv run pytest` → 29 passed in 0.10s.
- `uv run ruff check src tests` → All checks passed.
- `uv run emberfall new --seed 146 --save /tmp/emberfall-color-cron.json --color && uv run emberfall show /tmp/emberfall-color-cron.json --fog --color` → created a deterministic save and rendered the color-enabled full and torch-fog map views successfully.
- Final post-log check: `uv run emberfall show /tmp/emberfall-color-cron.json --fog --color` → rendered the saved color-enabled torch-fog map successfully.
