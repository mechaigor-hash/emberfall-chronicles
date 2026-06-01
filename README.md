# Emberfall Chronicles

A Python-based retro fantasy RPG: tiny ASCII dungeons, turn-based combat, stalking monsters, treasure, shrines, save/load, and deterministic simulation for tests and CI.

## Quick start

```bash
uv venv
uv pip install -e . pytest ruff
uv run emberfall new --seed 42
uv run emberfall move east
uv run emberfall simulate --seed 7 --steps 120
```

No mandatory runtime dependencies: the game engine is standard-library Python.

## Gameplay

You are **Kalidor**, a blade-bearing wanderer trapped under Emberfall Keep. Explore the maze, fight monsters, find relics, heal at shrines, and reach the ember gate (`>`). Monsters now sense nearby footsteps and stalk toward you through open corridors, so lingering in one place is dangerous.

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
emberfall move north saves/run.json
emberfall move south saves/run.json
emberfall move east saves/run.json
emberfall move west saves/run.json
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
