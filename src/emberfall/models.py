from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Tile(StrEnum):
    WALL = "#"
    FLOOR = "."
    EXIT = ">"
    PLAYER = "@"
    MONSTER = "M"
    TREASURE = "$"
    SHRINE = "+"


class Direction(StrEnum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.NORTH: (0, -1),
    Direction.SOUTH: (0, 1),
    Direction.EAST: (1, 0),
    Direction.WEST: (-1, 0),
}


@dataclass(slots=True)
class Position:
    x: int
    y: int

    def moved(self, direction: Direction) -> "Position":
        dx, dy = DIRECTION_DELTAS[direction]
        return Position(self.x + dx, self.y + dy)


@dataclass(slots=True)
class Stats:
    hp: int
    max_hp: int
    attack: int
    defense: int


@dataclass(slots=True)
class Entity:
    name: str
    glyph: str
    position: Position
    stats: Stats
    gold: int = 0
    xp: int = 0
    level: int = 1
    inventory: list[str] = field(default_factory=list)

    @property
    def alive(self) -> bool:
        return self.stats.hp > 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Entity":
        return cls(
            name=data["name"],
            glyph=data["glyph"],
            position=Position(**data["position"]),
            stats=Stats(**data["stats"]),
            gold=data.get("gold", 0),
            xp=data.get("xp", 0),
            level=data.get("level", 1),
            inventory=list(data.get("inventory", [])),
        )


@dataclass(slots=True)
class GameState:
    seed: int
    depth: int
    width: int
    height: int
    tiles: list[str]
    player: Entity
    monsters: list[Entity]
    treasures: list[Position]
    shrines: list[Position]
    log: list[str] = field(default_factory=list)
    won: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "depth": self.depth,
            "width": self.width,
            "height": self.height,
            "tiles": self.tiles,
            "player": self.player.to_dict(),
            "monsters": [monster.to_dict() for monster in self.monsters],
            "treasures": [asdict(position) for position in self.treasures],
            "shrines": [asdict(position) for position in self.shrines],
            "log": self.log,
            "won": self.won,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        return cls(
            seed=data["seed"],
            depth=data["depth"],
            width=data["width"],
            height=data["height"],
            tiles=list(data["tiles"]),
            player=Entity.from_dict(data["player"]),
            monsters=[Entity.from_dict(item) for item in data.get("monsters", [])],
            treasures=[Position(**item) for item in data.get("treasures", [])],
            shrines=[Position(**item) for item in data.get("shrines", [])],
            log=list(data.get("log", [])),
            won=bool(data.get("won", False)),
        )
