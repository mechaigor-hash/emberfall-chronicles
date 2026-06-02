# Emberfall Chronicles

A Python-based retro fantasy RPG: tiny ASCII dungeons, turn-based combat, stalking monsters, treasure, shrines, save/load, and deterministic simulation for tests and CI.

## Quick start

```bash
uv venv
uv pip install -e . pytest ruff
uv run emberfall new --seed 42
uv run emberfall status
uv run emberfall inventory
uv run emberfall look
uv run emberfall objectives
uv run emberfall threats
uv run emberfall move east
uv run emberfall simulate --seed 7 --steps 120
```

No mandatory runtime dependencies: the game engine is standard-library Python.

## Gameplay

You are **Kalidor**, a blade-bearing wanderer trapped under Emberfall Keep. Explore the maze, fight monsters, find relics, heal at shrines, and reach the ember gate (`>`). Monsters now sense nearby footsteps and stalk toward you through open corridors, so lingering in one place is dangerous. Relics are more than trophies: each treasure grants a small deterministic stat boon such as sharper attacks, sturdier defense, or restored health. The `inventory` command lists carried gear, gold, and the boon text for each known relic. The `look` command scouts the four adjacent spaces without advancing the turn, helping you spot monsters, treasure, shrines, and the ember gate before moving. The `objectives` command gives a non-mutating quest readout with remaining treasures, shrines, monsters, and shortest-route hints. The `threats` command ranks nearby monsters and calls out whether resting is currently safe. When the corridors are quiet, the `rest` command lets Kalidor spend a turn recovering a little HP, but nearby monsters interrupt the respite.

Legend:

| Glyph | Meaning |
| --- | --- |
| `@` | Kalidor |
| `#` | wall |
| `.` | floor |
| `M` | monster |
| `$` | treasure |
| `+` | shrine |
| `>` | exit |

## Commands

```bash
emberfall new --seed 123 --save saves/run.json
emberfall show saves/run.json
emberfall status saves/run.json
emberfall inventory saves/run.json
emberfall look saves/run.json
emberfall objectives saves/run.json
emberfall threats saves/run.json
emberfall move north saves/run.json
emberfall move south saves/run.json
emberfall move east saves/run.json
emberfall move west saves/run.json
emberfall rest saves/run.json
emberfall simulate --seed 123 --steps 80
```

## Development roadmap

This repo is intentionally built to be iterated by agents overnight. Near-term ideas:

- patrol routes and ranged monster behavior
- item effects rather than collectible names only
- multi-floor campaign mode
- curses or Textual UI
- procedural town / quest generator
- sprite-like ANSI color renderer

## Test

```bash
uv run pytest
uv run ruff check src tests
```
