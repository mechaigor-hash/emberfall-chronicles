from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path

from emberfall.models import Direction, Entity, GameState, Position, Stats, Tile


MONSTER_NAMES = ["ash goblin", "bone imp", "mire kobold", "cinder wraith", "rust knight"]
LOOT = ["Moonlit Key", "Ember Ring", "Tin Crown", "Oaken Charm", "Starfall Shard"]
LOOT_EFFECTS = {
    "Moonlit Key": "The key hums, revealing safer paths. +1 defense.",
    "Ember Ring": "The ring flares around your blade. +1 attack.",
    "Tin Crown": "The crown steadies your thoughts. +2 max HP.",
    "Oaken Charm": "The charm knits your wounds. +4 HP.",
    "Starfall Shard": "The shard burns like a tiny comet. +1 attack, +1 defense.",
}


class GameError(RuntimeError):
    """Raised when an impossible game action is requested."""


def new_game(seed: int | None = None, width: int = 31, height: int = 17) -> GameState:
    seed = seed if seed is not None else random.randrange(1, 999_999)
    rng = random.Random(seed)
    width = max(15, width | 1)
    height = max(11, height | 1)
    tiles = _generate_map(rng, width, height)
    floors = _floor_positions(tiles, width, height)
    start = floors[0]
    exit_pos = floors[-1]
    _set_tile(tiles, width, exit_pos, Tile.EXIT)

    monsters: list[Entity] = []
    occupied = {(start.x, start.y), (exit_pos.x, exit_pos.y)}
    for idx in range(max(4, (width * height) // 90)):
        pos = _take_free_floor(rng, floors, occupied)
        monsters.append(
            Entity(
                name=rng.choice(MONSTER_NAMES),
                glyph=Tile.MONSTER.value,
                position=pos,
                stats=Stats(hp=7 + idx, max_hp=7 + idx, attack=3 + idx // 2, defense=1 + idx // 3),
                gold=rng.randint(2, 9),
                xp=4 + idx * 2,
            )
        )

    treasures = [_take_free_floor(rng, floors, occupied) for _ in range(4)]
    shrines = [_take_free_floor(rng, floors, occupied) for _ in range(2)]
    player = Entity(
        name="Kalidor",
        glyph=Tile.PLAYER.value,
        position=start,
        stats=Stats(hp=24, max_hp=24, attack=6, defense=2),
        inventory=["Weathered Blade"],
    )
    return GameState(
        seed=seed,
        depth=1,
        width=width,
        height=height,
        tiles=tiles,
        player=player,
        monsters=monsters,
        treasures=treasures,
        shrines=shrines,
        log=["You wake beneath Emberfall Keep. The torches burn blue."],
    )


def move(state: GameState, direction: Direction | str) -> GameState:
    if not state.player.alive or state.won:
        return state
    direction = Direction(direction)
    target = state.player.position.moved(direction)
    if _is_wall(state, target):
        state.log.append("A cold stone wall blocks the way.")
        return state
    monster = monster_at(state, target)
    if monster:
        _attack(state.player, monster, state)
        if not monster.alive:
            state.player.gold += monster.gold
            state.player.xp += monster.xp
            state.log.append(f"The {monster.name} falls. +{monster.xp} XP, +{monster.gold} gold.")
            state.monsters = [item for item in state.monsters if item.alive]
            _maybe_level_up(state)
        _monsters_act(state)
        return state

    state.player.position = target
    _collect_at_player(state)
    if _tile_at(state, target) == Tile.EXIT:
        state.won = True
        state.log.append("You descend through the ember gate. Victory, for tonight.")
    else:
        _monsters_act(state)
    return state


def rest(state: GameState) -> GameState:
    """Spend a turn catching breath, with nearby monsters making it unsafe."""
    if not state.player.alive or state.won:
        return state
    if _danger_nearby(state):
        state.log.append("No time to rest: something scrapes close by.")
    elif state.player.stats.hp < state.player.stats.max_hp:
        recovered = min(2, state.player.stats.max_hp - state.player.stats.hp)
        state.player.stats.hp += recovered
        state.log.append(f"Kalidor catches his breath and recovers {recovered} HP.")
    else:
        state.log.append("Kalidor listens to the dungeon's old static.")
    _monsters_act(state)
    return state


def render(state: GameState, reveal_all: bool = True) -> str:
    grid = [list(row) for row in state.tiles]
    for treasure in state.treasures:
        grid[treasure.y][treasure.x] = Tile.TREASURE.value
    for shrine in state.shrines:
        grid[shrine.y][shrine.x] = Tile.SHRINE.value
    for monster in state.monsters:
        if monster.alive:
            grid[monster.position.y][monster.position.x] = monster.glyph
    grid[state.player.position.y][state.player.position.x] = state.player.glyph
    if not reveal_all:
        grid = _fog(grid, state.player.position)
    stats = state.player.stats
    header = f"Emberfall Depth {state.depth} | HP {stats.hp}/{stats.max_hp} | ATK {stats.attack} DEF {stats.defense} | Gold {state.player.gold} XP {state.player.xp}"
    return header + "\n" + "\n".join("".join(row) for row in grid) + "\n" + "\n".join(state.log[-5:])


def hero_sheet(state: GameState) -> str:
    """Return a compact character sheet for CLI status checks."""
    stats = state.player.stats
    inventory = ", ".join(state.player.inventory) if state.player.inventory else "empty pack"
    lines = [
        f"{state.player.name} — level {state.player.level}",
        f"HP {stats.hp}/{stats.max_hp} | ATK {stats.attack} | DEF {stats.defense}",
        f"Gold {state.player.gold} | XP {state.player.xp}/{state.player.level * 12}",
        f"Inventory: {inventory}",
    ]
    if state.won:
        lines.append("Status: victorious beyond the ember gate")
    elif not state.player.alive:
        lines.append("Status: fallen beneath Emberfall Keep")
    else:
        lines.append("Status: still delving")
    return "\n".join(lines)


def inventory_report(state: GameState) -> str:
    """Describe carried relics and their known boons for quick planning."""
    lines = [f"Kalidor's pack holds {state.player.gold} gold and:"]
    if not state.player.inventory:
        lines.append("- nothing but dungeon dust")
        return "\n".join(lines)
    for item in state.player.inventory:
        effect = LOOT_EFFECTS.get(item, "A dependable companion from better-lit days.")
        lines.append(f"- {item}: {effect}")
    return "\n".join(lines)


def look(state: GameState) -> str:
    """Describe the four adjacent spaces without spending a turn."""
    lines = ["Kalidor studies the nearby gloom:"]
    for direction in Direction:
        target = state.player.position.moved(direction)
        lines.append(f"- {direction.value}: {_describe_position(state, target)}")
    return "\n".join(lines)


def objectives(state: GameState) -> str:
    """Summarize remaining dungeon goals without spending a turn."""
    lines = ["Kalidor checks the quest etched into his lantern glass:"]
    exit_positions = [
        Position(x, y) for y, row in enumerate(state.tiles) for x, ch in enumerate(row) if ch == Tile.EXIT
    ]
    lines.append(f"- Ember gate: {_route_summary(state, exit_positions)}")
    lines.append(f"- Treasures remaining: {len(state.treasures)} ({_route_summary(state, state.treasures)})")
    lines.append(f"- Healing shrines remaining: {len(state.shrines)} ({_route_summary(state, state.shrines)})")
    lines.append(f"- Monsters alive: {sum(1 for monster in state.monsters if monster.alive)}")
    if state.won:
        lines.append("- Fate: the ember gate has already opened.")
    elif not state.player.alive:
        lines.append("- Fate: Kalidor has fallen beneath the keep.")
    else:
        lines.append("- Fate: find the gate before the keep wakes fully.")
    return "\n".join(lines)


def threat_report(state: GameState) -> str:
    """Summarize nearby monster danger without spending a turn."""
    living = [monster for monster in state.monsters if monster.alive]
    lines = ["Kalidor weighs the threats in the torchlight:"]
    if not living:
        lines.append("- No living monsters remain on this level.")
        lines.append("- Rest outlook: safe, if the stones stay quiet.")
        return "\n".join(lines)

    ranked = sorted(living, key=lambda monster: (_monster_distance(state, monster), monster.name))
    for monster in ranked[:5]:
        distance = _monster_distance(state, monster)
        warning = _threat_warning(distance)
        lines.append(
            f"- {monster.name}: {monster.stats.hp}/{monster.stats.max_hp} HP, "
            f"{distance} steps away — {warning}"
        )
    if len(ranked) > 5:
        lines.append(f"- ...and {len(ranked) - 5} more shapes deeper in the dark.")
    rest_outlook = "unsafe: something is within earshot" if _danger_nearby(state) else "safe for now"
    lines.append(f"- Rest outlook: {rest_outlook}.")
    return "\n".join(lines)


def adventure_log(state: GameState, limit: int = 8) -> str:
    """Return recent turn messages as a numbered in-world journal."""
    limit = max(1, limit)
    entries = state.log[-limit:]
    lines = [f"Kalidor's last {len(entries)} journal entries:"]
    if not entries:
        lines.append("1. The parchment is still blank.")
        return "\n".join(lines)
    start = len(state.log) - len(entries) + 1
    for offset, entry in enumerate(entries):
        lines.append(f"{start + offset}. {entry}")
    return "\n".join(lines)


def legend(state: GameState) -> str:
    """Explain map glyphs with current dungeon counts for quick orientation."""
    living_monsters = sum(1 for monster in state.monsters if monster.alive)
    lines = [
        "Emberfall map legend:",
        f"- {Tile.PLAYER.value} Kalidor: level {state.player.level}, {state.player.stats.hp}/{state.player.stats.max_hp} HP",
        f"- {Tile.WALL.value} stone wall: blocks movement and line of flight",
        f"- {Tile.FLOOR.value} corridor floor: safe to step onto unless stalked",
        f"- {Tile.MONSTER.value} monster: {living_monsters} alive on this depth",
        f"- {Tile.TREASURE.value} treasure: {len(state.treasures)} relic caches remain",
        f"- {Tile.SHRINE.value} shrine: {len(state.shrines)} healing shrines remain",
        f"- {Tile.EXIT.value} ember gate: {'opened' if state.won else 'seek it to win'}",
    ]
    return "\n".join(lines)


def bestiary(state: GameState) -> str:
    """Summarize living monster types, combat stats, and rewards."""
    living = [monster for monster in state.monsters if monster.alive]
    lines = ["Emberfall field bestiary:"]
    if not living:
        lines.append("- No monsters remain to catalogue on this depth.")
        return "\n".join(lines)

    for name in sorted({monster.name for monster in living}):
        pack = [monster for monster in living if monster.name == name]
        hp_values = [monster.stats.hp for monster in pack]
        attacks = [monster.stats.attack for monster in pack]
        defenses = [monster.stats.defense for monster in pack]
        xp_values = [monster.xp for monster in pack]
        gold_values = [monster.gold for monster in pack]
        nearest = min(_monster_distance(state, monster) for monster in pack)
        lines.append(
            f"- {name} x{len(pack)}: HP {_range_text(hp_values)}, "
            f"ATK {_range_text(attacks)}, DEF {_range_text(defenses)}, "
            f"XP {_range_text(xp_values)}, gold {_range_text(gold_values)}, "
            f"nearest {nearest} steps ({_threat_warning(nearest)})"
        )
    return "\n".join(lines)


def combat_advice(state: GameState) -> str:
    """Estimate adjacent combat odds without mutating the game state."""
    lines = ["Kalidor weighs the next exchange:"]
    adjacent = [
        (direction, monster_at(state, state.player.position.moved(direction)))
        for direction in Direction
    ]
    targets = [(direction, monster) for direction, monster in adjacent if monster]
    if not targets:
        living = [monster for monster in state.monsters if monster.alive]
        if not living:
            lines.append("- No living monsters remain to challenge your blade.")
        else:
            nearest = min(living, key=lambda monster: (_monster_distance(state, monster), monster.name))
            distance = _monster_distance(state, nearest)
            lines.append(
                f"- No adjacent enemy. Nearest: {nearest.name}, "
                f"{distance} steps away ({_threat_warning(distance)})."
            )
        lines.append("- Tactical hint: use route, look, or rest before committing to a fight.")
        return "\n".join(lines)

    player = state.player
    for direction, monster in targets:
        player_damage = _damage(player, monster)
        monster_damage = _damage(monster, player)
        hero_swings = _turns_to_defeat(monster.stats.hp, player_damage)
        enemy_swings = _turns_to_defeat(player.stats.hp, monster_damage)
        outlook = "favorable" if hero_swings <= enemy_swings else "dangerous"
        lines.append(
            f"- {direction.value}: {monster.name} at {monster.stats.hp}/{monster.stats.max_hp} HP — "
            f"you hit for {player_damage}, it hits for {monster_damage}; "
            f"defeat in {hero_swings} swings, survival margin {enemy_swings} enemy swings ({outlook})."
        )
    return "\n".join(lines)


def tactical_hint(state: GameState) -> str:
    """Recommend one safe next action without mutating the game state."""
    lines = ["Kalidor considers his next move:"]
    if state.won:
        lines.append("- The ember gate is open. No further action is needed on this depth.")
        return "\n".join(lines)
    if not state.player.alive:
        lines.append("- The lantern is dark. Start a new delve to try again.")
        return "\n".join(lines)

    adjacent = [
        (direction, monster_at(state, state.player.position.moved(direction)))
        for direction in Direction
    ]
    targets = [(direction, monster) for direction, monster in adjacent if monster]
    if targets:
        direction, monster = min(
            targets,
            key=lambda item: (
                _turns_to_defeat(item[1].stats.hp, _damage(state.player, item[1])),
                item[1].name,
            ),
        )
        player_damage = _damage(state.player, monster)
        monster_damage = _damage(monster, state.player)
        hero_swings = _turns_to_defeat(monster.stats.hp, player_damage)
        enemy_swings = _turns_to_defeat(state.player.stats.hp, monster_damage)
        if hero_swings <= enemy_swings:
            lines.append(
                f"- Recommended action: move {direction.value} to strike the {monster.name}; "
                f"expected win in {hero_swings} swings."
            )
        else:
            shrine_path = _path_to_positions(state, state.shrines)
            if shrine_path:
                lines.append(
                    f"- Recommended action: avoid this fight and move {shrine_path[0].value} "
                    "toward a healing shrine."
                )
            else:
                lines.append(
                    f"- Recommended action: desperate attack {direction.value}; no safe shrine route is visible."
                )
        return "\n".join(lines)

    if state.player.stats.hp <= state.player.stats.max_hp // 2:
        if not _danger_nearby(state):
            lines.append("- Recommended action: rest; HP is low and no monster is close enough to interrupt.")
            return "\n".join(lines)
        shrine_path = _path_to_positions(state, state.shrines)
        if shrine_path:
            lines.append(
                f"- Recommended action: move {shrine_path[0].value} toward a healing shrine; HP is low."
            )
            return "\n".join(lines)

    if state.treasures:
        treasure_path = _path_to_positions(state, state.treasures)
        if treasure_path:
            lines.append(
                f"- Recommended action: move {treasure_path[0].value} toward treasure for relic boons."
            )
            return "\n".join(lines)

    exit_path = _path_to_positions(state, _exit_positions(state))
    if exit_path:
        lines.append(f"- Recommended action: move {exit_path[0].value} toward the ember gate.")
    else:
        lines.append("- Recommended action: look, then choose a corridor; no safe route is visible.")
    return "\n".join(lines)


def route_plan(state: GameState, goal: str = "any") -> str:
    """Give a shortest safe route toward the requested objective without advancing time."""
    goal = goal.lower()
    goals = _route_goals(state, goal)
    title = goal if goal in {"any", "exit", "treasure", "shrine"} else "unknown"
    lines = [f"Kalidor plots a route toward {title}:"]
    if title == "unknown":
        lines.append("- Unknown goal. Choose any, exit, treasure, or shrine.")
        return "\n".join(lines)
    if not goals:
        lines.append(f"- No {goal} objective remains on this depth.")
        return "\n".join(lines)
    if state.player.position in goals:
        lines.append("- Destination: already here.")
        return "\n".join(lines)

    path = _path_to_positions(state, goals)
    if not path:
        lines.append("- No safe route is currently visible around living monsters.")
        return "\n".join(lines)

    steps = ", ".join(direction.value for direction in path[:10])
    if len(path) > 10:
        steps += f", ... ({len(path) - 10} more)"
    destination = _route_destination_name(state, _follow_path(state.player.position, path))
    lines.append(f"- Destination: {destination}")
    lines.append(f"- Distance: {len(path)} steps")
    lines.append(f"- First move: {path[0].value}")
    lines.append(f"- Route: {steps}")
    return "\n".join(lines)


def save(state: GameState, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
    return path


def load(path: str | Path) -> GameState:
    return GameState.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def simulate(seed: int = 1, steps: int = 60) -> GameState:
    state = new_game(seed=seed)
    rng = random.Random(seed + 777)
    for _ in range(steps):
        if state.won or not state.player.alive:
            break
        path = _path_to_exit_or_goal(state)
        if path:
            move(state, path[0])
        else:
            move(state, rng.choice(list(Direction)))
    return state


def monster_at(state: GameState, position: Position) -> Entity | None:
    return next((m for m in state.monsters if m.alive and m.position == position), None)


def _describe_position(state: GameState, position: Position) -> str:
    if _is_wall(state, position):
        return "a cold stone wall"
    monster = monster_at(state, position)
    if monster:
        return f"the {monster.name}, wounded to {monster.stats.hp}/{monster.stats.max_hp} HP"
    if position in state.treasures:
        return "a treasure glint"
    if position in state.shrines:
        return "a healing shrine"
    if _tile_at(state, position) == Tile.EXIT:
        return "the ember gate"
    return "an open corridor"


def _route_summary(state: GameState, goals: list[Position]) -> str:
    if not goals:
        return "none left"
    if state.player.position in goals:
        return "here"
    path = _path_to_positions(state, goals)
    if not path:
        return "unreachable from here"
    return f"{len(path)} steps, first move {path[0].value}"


def _danger_nearby(state: GameState, radius: int = 2) -> bool:
    return any(
        abs(monster.position.x - state.player.position.x)
        + abs(monster.position.y - state.player.position.y)
        <= radius
        for monster in state.monsters
        if monster.alive
    )


def _monster_distance(state: GameState, monster: Entity) -> int:
    return abs(monster.position.x - state.player.position.x) + abs(
        monster.position.y - state.player.position.y
    )


def _threat_warning(distance: int) -> str:
    if distance == 1:
        return "adjacent and ready to strike"
    if distance <= 2:
        return "too close to rest"
    if distance <= 6:
        return "close enough to stalk your scent"
    return "distant for now"


def _range_text(values: list[int]) -> str:
    low = min(values)
    high = max(values)
    if low == high:
        return str(low)
    return f"{low}-{high}"


def _route_goals(state: GameState, goal: str) -> list[Position]:
    exits = _exit_positions(state)
    if goal == "any":
        return [*state.treasures, *state.shrines, *exits]
    if goal == "exit":
        return exits
    if goal == "treasure":
        return list(state.treasures)
    if goal == "shrine":
        return list(state.shrines)
    return []


def _exit_positions(state: GameState) -> list[Position]:
    return [
        Position(x, y) for y, row in enumerate(state.tiles) for x, ch in enumerate(row) if ch == Tile.EXIT
    ]


def _follow_path(start: Position, path: list[Direction]) -> Position:
    position = start
    for direction in path:
        position = position.moved(direction)
    return position


def _route_destination_name(state: GameState, position: Position) -> str:
    if position in state.treasures:
        return "treasure cache"
    if position in state.shrines:
        return "healing shrine"
    if _tile_at(state, position) == Tile.EXIT:
        return "ember gate"
    return "open corridor"


def _generate_map(rng: random.Random, width: int, height: int) -> list[str]:
    grid = [[Tile.WALL.value for _ in range(width)] for _ in range(height)]
    x, y = 1, 1
    grid[y][x] = Tile.FLOOR.value
    for _ in range(width * height * 5):
        dx, dy = rng.choice([(2, 0), (-2, 0), (0, 2), (0, -2)])
        nx, ny = x + dx, y + dy
        if 1 <= nx < width - 1 and 1 <= ny < height - 1:
            grid[y + dy // 2][x + dx // 2] = Tile.FLOOR.value
            grid[ny][nx] = Tile.FLOOR.value
            x, y = nx, ny
    return ["".join(row) for row in grid]


def _floor_positions(tiles: list[str], width: int, height: int) -> list[Position]:
    floors = [Position(x, y) for y in range(height) for x in range(width) if tiles[y][x] == Tile.FLOOR]
    if not floors:
        raise GameError("map generation produced no floor")
    return floors


def _take_free_floor(rng: random.Random, floors: list[Position], occupied: set[tuple[int, int]]) -> Position:
    choices = [pos for pos in floors if (pos.x, pos.y) not in occupied]
    pos = rng.choice(choices)
    occupied.add((pos.x, pos.y))
    return pos


def _set_tile(tiles: list[str], width: int, position: Position, tile: Tile) -> None:
    index = position.y
    row = list(tiles[index])
    row[position.x] = tile.value
    tiles[index] = "".join(row)


def _tile_at(state: GameState, position: Position) -> Tile:
    return Tile(state.tiles[position.y][position.x])


def _is_wall(state: GameState, position: Position) -> bool:
    return position.x < 0 or position.y < 0 or position.x >= state.width or position.y >= state.height or _tile_at(state, position) == Tile.WALL


def _damage(attacker: Entity, defender: Entity) -> int:
    return max(1, attacker.stats.attack - defender.stats.defense)


def _turns_to_defeat(hp: int, damage: int) -> int:
    return max(1, (hp + damage - 1) // damage)


def _attack(attacker: Entity, defender: Entity, state: GameState) -> None:
    damage = _damage(attacker, defender)
    defender.stats.hp = max(0, defender.stats.hp - damage)
    state.log.append(f"{attacker.name} hits {defender.name} for {damage}.")


def _monsters_act(state: GameState) -> None:
    for monster in list(state.monsters):
        if abs(monster.position.x - state.player.position.x) + abs(monster.position.y - state.player.position.y) == 1:
            _attack(monster, state.player, state)
            if not state.player.alive:
                state.log.append("Your lantern gutters out. The dungeon claims another hero.")
                return
            continue
        if _monster_can_smell_player(monster, state):
            _stalk_player(monster, state)


def _monster_can_smell_player(monster: Entity, state: GameState, radius: int = 6) -> bool:
    distance = abs(monster.position.x - state.player.position.x) + abs(monster.position.y - state.player.position.y)
    return distance <= radius


def _stalk_player(monster: Entity, state: GameState) -> None:
    best = monster.position
    best_distance = abs(monster.position.x - state.player.position.x) + abs(monster.position.y - state.player.position.y)
    occupied = {(item.position.x, item.position.y) for item in state.monsters if item.alive and item is not monster}
    for direction in Direction:
        candidate = monster.position.moved(direction)
        key = (candidate.x, candidate.y)
        distance = abs(candidate.x - state.player.position.x) + abs(candidate.y - state.player.position.y)
        if key in occupied or candidate == state.player.position or _is_wall(state, candidate) or distance >= best_distance:
            continue
        best = candidate
        best_distance = distance
    if best != monster.position:
        monster.position = best
        state.log.append(f"The {monster.name} stalks closer through the gloom.")


def _collect_at_player(state: GameState) -> None:
    pos = state.player.position
    for treasure in list(state.treasures):
        if treasure == pos:
            state.treasures.remove(treasure)
            item = random.Random(state.seed + pos.x * 31 + pos.y).choice(LOOT)
            state.player.inventory.append(item)
            state.player.gold += 10
            effect = _apply_loot_effect(state, item)
            state.log.append(f"You find {item} and 10 gold. {effect}")
    for shrine in list(state.shrines):
        if shrine == pos:
            state.shrines.remove(shrine)
            state.player.stats.hp = state.player.stats.max_hp
            state.log.append("A shrine of old pixels restores your health.")


def _apply_loot_effect(state: GameState, item: str) -> str:
    stats = state.player.stats
    if item == "Moonlit Key":
        stats.defense += 1
    elif item == "Ember Ring":
        stats.attack += 1
    elif item == "Tin Crown":
        stats.max_hp += 2
        stats.hp += 2
    elif item == "Oaken Charm":
        stats.hp = min(stats.max_hp, stats.hp + 4)
    elif item == "Starfall Shard":
        stats.attack += 1
        stats.defense += 1
    return LOOT_EFFECTS[item]


def _maybe_level_up(state: GameState) -> None:
    needed = state.player.level * 12
    if state.player.xp >= needed:
        state.player.level += 1
        state.player.stats.max_hp += 5
        state.player.stats.hp = state.player.stats.max_hp
        state.player.stats.attack += 1
        state.log.append(f"Level up! Kalidor reaches level {state.player.level}.")


def _fog(grid: list[list[str]], origin: Position, radius: int = 5) -> list[list[str]]:
    for y, row in enumerate(grid):
        for x, _ in enumerate(row):
            if abs(x - origin.x) + abs(y - origin.y) > radius:
                row[x] = " "
    return grid


def _path_to_exit_or_goal(state: GameState) -> list[Direction]:
    goals = [Position(x, y) for y, row in enumerate(state.tiles) for x, ch in enumerate(row) if ch == Tile.EXIT]
    goals.extend(state.treasures)
    return _path_to_positions(state, goals)


def _path_to_positions(state: GameState, goals: list[Position]) -> list[Direction]:
    queue: deque[tuple[Position, list[Direction]]] = deque([(state.player.position, [])])
    seen = {(state.player.position.x, state.player.position.y)}
    while queue:
        pos, path = queue.popleft()
        if pos in goals and path:
            return path
        for direction in Direction:
            nxt = pos.moved(direction)
            key = (nxt.x, nxt.y)
            if key in seen or _is_wall(state, nxt) or monster_at(state, nxt):
                continue
            seen.add(key)
            queue.append((nxt, [*path, direction]))
    return []
