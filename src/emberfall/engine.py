from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path

from emberfall.models import Direction, Entity, GameState, Position, Stats, Tile


MONSTER_NAMES = ["ash goblin", "bone imp", "mire kobold", "cinder wraith", "rust knight"]
LOOT = ["Moonlit Key", "Ember Ring", "Tin Crown", "Oaken Charm", "Starfall Shard"]


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


def _attack(attacker: Entity, defender: Entity, state: GameState) -> None:
    damage = max(1, attacker.stats.attack - defender.stats.defense)
    defender.stats.hp = max(0, defender.stats.hp - damage)
    state.log.append(f"{attacker.name} hits {defender.name} for {damage}.")


def _monsters_act(state: GameState) -> None:
    for monster in list(state.monsters):
        if abs(monster.position.x - state.player.position.x) + abs(monster.position.y - state.player.position.y) == 1:
            _attack(monster, state.player, state)
            if not state.player.alive:
                state.log.append("Your lantern gutters out. The dungeon claims another hero.")
                return


def _collect_at_player(state: GameState) -> None:
    pos = state.player.position
    for treasure in list(state.treasures):
        if treasure == pos:
            state.treasures.remove(treasure)
            item = random.Random(state.seed + pos.x * 31 + pos.y).choice(LOOT)
            state.player.inventory.append(item)
            state.player.gold += 10
            state.log.append(f"You find {item} and 10 gold.")
    for shrine in list(state.shrines):
        if shrine == pos:
            state.shrines.remove(shrine)
            state.player.stats.hp = state.player.stats.max_hp
            state.log.append("A shrine of old pixels restores your health.")


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
