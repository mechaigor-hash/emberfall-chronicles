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
