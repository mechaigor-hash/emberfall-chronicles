from emberfall.engine import hero_sheet, load, move, new_game, render, save, simulate
from emberfall.models import Direction


def test_new_game_is_deterministic():
    a = new_game(seed=42)
    b = new_game(seed=42)
    assert a.tiles == b.tiles
    assert a.player.position == b.player.position
    assert [m.position for m in a.monsters] == [m.position for m in b.monsters]


def test_render_contains_retro_glyphs():
    state = new_game(seed=7)
    screen = render(state)
    assert "@" in screen
    assert "#" in screen
    assert "Emberfall Depth" in screen


def test_hero_sheet_summarizes_stats_and_inventory():
    state = new_game(seed=12)
    state.player.gold = 17
    state.player.xp = 5

    sheet = hero_sheet(state)

    assert "Kalidor — level 1" in sheet
    assert "HP 24/24 | ATK 6 | DEF 2" in sheet
    assert "Gold 17 | XP 5/12" in sheet
    assert "Weathered Blade" in sheet
    assert "still delving" in sheet


def test_move_into_wall_logs_message():
    state = new_game(seed=1)
    state.player.position.x = 1
    state.player.position.y = 1
    move(state, Direction.WEST)
    assert state.player.position.x == 1
    assert "wall" in state.log[-1]


def test_save_load_roundtrip(tmp_path):
    state = new_game(seed=99)
    path = tmp_path / "save.json"
    save(state, path)
    restored = load(path)
    assert restored.to_dict() == state.to_dict()


def test_simulation_does_not_crash():
    state = simulate(seed=5, steps=200)
    assert state.player.stats.hp >= 0
    assert state.won or state.player.alive or not state.player.alive


def test_treasure_relics_grant_a_mechanical_effect():
    state = new_game(seed=11, width=11, height=11)
    state.tiles = ["#" * 11, *["#.........#" for _ in range(9)], "#" * 11]
    state.monsters.clear()
    state.shrines.clear()
    state.treasures = [state.player.position.moved(Direction.EAST)]
    state.player.stats.hp = 10
    before = (
        state.player.stats.hp,
        state.player.stats.max_hp,
        state.player.stats.attack,
        state.player.stats.defense,
    )

    move(state, Direction.EAST)

    after = (
        state.player.stats.hp,
        state.player.stats.max_hp,
        state.player.stats.attack,
        state.player.stats.defense,
    )
    assert state.player.inventory[-1] in state.log[-1]
    assert "+" in state.log[-1]
    assert after != before


def test_monsters_stalk_nearby_player_after_a_turn():
    state = new_game(seed=3, width=11, height=11)
    state.tiles = ["#" * 11, *["#.........#" for _ in range(9)], "#" * 11]
    state.treasures.clear()
    state.shrines.clear()
    monster = state.monsters[0]
    state.monsters = [monster]
    state.player.position.x = 5
    state.player.position.y = 5
    monster.position.x = 8
    monster.position.y = 5
    expected_player_position = state.player.position.moved(Direction.WEST)
    before = abs(monster.position.x - expected_player_position.x) + abs(monster.position.y - expected_player_position.y)

    move(state, Direction.WEST)

    after = abs(monster.position.x - state.player.position.x) + abs(monster.position.y - state.player.position.y)
    assert after < before
    assert monster.position.x == 7
    assert "stalks closer" in state.log[-1]
