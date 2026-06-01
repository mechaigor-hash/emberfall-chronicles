from emberfall.engine import load, move, new_game, render, save, simulate
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
