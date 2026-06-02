from __future__ import annotations

import argparse
import sys
from pathlib import Path

from emberfall.engine import (
    adventure_log,
    bestiary,
    combat_advice,
    hero_sheet,
    inventory_report,
    legend,
    load,
    look,
    move,
    new_game,
    objectives,
    render,
    rest,
    route_plan,
    save,
    simulate,
    tactical_hint,
    threat_report,
)
from emberfall.models import Direction

BANNER = r"""
  _____           _              __      _ _ 
 | ____|_ __ ___ | |__   ___ _ _/ _|__ _| | |
 |  _| | '_ ` _ \| '_ \ / _ \ '__| |_/ _` | | |
 | |___| | | | | | |_) |  __/ |  |  _ (_| | | |
 |_____|_| |_| |_|_.__/ \___|_|  |_| \__,_|_|_|
""".strip("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emberfall Chronicles retro fantasy RPG")
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="start a new dungeon")
    new.add_argument("--seed", type=int, default=None)
    new.add_argument("--save", type=Path, default=Path("saves/emberfall.json"))
    new.add_argument("--width", type=int, default=31)
    new.add_argument("--height", type=int, default=17)

    show = sub.add_parser("show", help="render a saved game")
    show.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    status = sub.add_parser("status", help="show hero stats and inventory for a saved game")
    status.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    pack = sub.add_parser("inventory", help="list carried gear, relic boons, and gold")
    pack.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    scout = sub.add_parser("look", help="describe adjacent tiles without spending a turn")
    scout.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    goals = sub.add_parser("objectives", help="summarize remaining dungeon goals and routes")
    goals.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    threats = sub.add_parser("threats", help="summarize nearby monsters and rest safety")
    threats.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    journal = sub.add_parser("log", help="show recent adventure log entries without advancing time")
    journal.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))
    journal.add_argument("--limit", type=int, default=8, help="number of recent entries to show")

    glyphs = sub.add_parser("legend", help="explain map glyphs and current dungeon counts")
    glyphs.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    beasts = sub.add_parser("bestiary", help="summarize living monster types and rewards")
    beasts.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    combat = sub.add_parser("combat", help="estimate adjacent fight odds without advancing time")
    combat.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    hint = sub.add_parser("hint", help="recommend one safe next action without advancing time")
    hint.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    route = sub.add_parser("route", help="plot shortest safe route to an objective")
    route.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))
    route.add_argument(
        "--goal",
        choices=["any", "exit", "treasure", "shrine"],
        default="any",
        help="objective to route toward",
    )

    step = sub.add_parser("move", help="move north/south/east/west in a saved game")
    step.add_argument("direction", choices=[item.value for item in Direction])
    step.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    wait = sub.add_parser("rest", help="spend a turn recovering a little HP when safe")
    wait.add_argument("save", type=Path, nargs="?", default=Path("saves/emberfall.json"))

    auto = sub.add_parser("simulate", help="run an automated delve")
    auto.add_argument("--seed", type=int, default=1)
    auto.add_argument("--steps", type=int, default=80)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "new":
        state = new_game(seed=args.seed, width=args.width, height=args.height)
        save(state, args.save)
        print(BANNER)
        print(render(state))
        print(f"\nSaved to {args.save}")
        return 0
    if args.command == "show":
        print(render(load(args.save)))
        return 0
    if args.command == "status":
        print(hero_sheet(load(args.save)))
        return 0
    if args.command == "inventory":
        print(inventory_report(load(args.save)))
        return 0
    if args.command == "look":
        print(look(load(args.save)))
        return 0
    if args.command == "objectives":
        print(objectives(load(args.save)))
        return 0
    if args.command == "threats":
        print(threat_report(load(args.save)))
        return 0
    if args.command == "log":
        print(adventure_log(load(args.save), limit=args.limit))
        return 0
    if args.command == "legend":
        print(legend(load(args.save)))
        return 0
    if args.command == "bestiary":
        print(bestiary(load(args.save)))
        return 0
    if args.command == "combat":
        print(combat_advice(load(args.save)))
        return 0
    if args.command == "hint":
        print(tactical_hint(load(args.save)))
        return 0
    if args.command == "route":
        print(route_plan(load(args.save), goal=args.goal))
        return 0
    if args.command == "move":
        state = load(args.save)
        move(state, Direction(args.direction))
        save(state, args.save)
        print(render(state))
        return 0
    if args.command == "rest":
        state = load(args.save)
        rest(state)
        save(state, args.save)
        print(render(state))
        return 0
    if args.command == "simulate":
        state = simulate(seed=args.seed, steps=args.steps)
        print(BANNER)
        print(render(state))
        print("\nOutcome:", "victory" if state.won else "dead" if not state.player.alive else "still delving")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
