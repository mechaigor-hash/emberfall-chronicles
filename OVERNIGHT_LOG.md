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
