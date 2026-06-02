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


def test_inventory_report_lists_gold_gear_and_relic_boons():
    state = new_game(seed=13)
    state.player.gold = 27
    state.player.inventory.append("Ember Ring")

    report = inventory_report(state)

    assert "27 gold" in report
    assert "Weathered Blade: A dependable companion" in report
    assert "Ember Ring: The ring flares around your blade. +1 attack." in report


def test_move_into_wall_logs_message():
    state = new_game(seed=1)
    state.player.position.x = 1
    state.player.position.y = 1
    move(state, Direction.WEST)
    assert state.player.position.x == 1
    assert "wall" in state.log[-1]


def test_look_describes_adjacent_features_without_spending_a_turn():
    state = new_game(seed=21, width=11, height=11)
    state.tiles = ["#" * 11, *["#.........#" for _ in range(9)], "#" * 11]
    monster = state.monsters[0]
    state.monsters = [monster]
    state.player.position.x = 5
    state.player.position.y = 5
    monster.position.x = 6
    monster.position.y = 5
    state.treasures = [state.player.position.moved(Direction.NORTH)]
    state.shrines = [state.player.position.moved(Direction.SOUTH)]
    before = state.to_dict()

    report = look(state)

    assert "north: a treasure glint" in report
    assert "south: a healing shrine" in report
    assert "east: the" in report
    assert "wounded to" in report
    assert "west: an open corridor" in report
    assert state.to_dict() == before


def test_objectives_summarize_routes_and_remaining_goals_without_mutation():
    state = new_game(seed=22, width=11, height=11)
    state.tiles = [
        "###########",
        "#@..$....>#",
        *["#.........#" for _ in range(8)],
        "###########",
    ]
    state.player.position.x = 1
    state.player.position.y = 1
    state.monsters = state.monsters[:2]
    state.monsters[0].position.x = 5
    state.monsters[0].position.y = 5
    state.monsters[1].position.x = 7
    state.monsters[1].position.y = 7
    state.treasures = [state.player.position.moved(Direction.EAST).moved(Direction.EAST).moved(Direction.EAST)]
    state.shrines.clear()
    before = state.to_dict()

    report = objectives(state)

    assert "Ember gate: 8 steps, first move east" in report
    assert "Treasures remaining: 1 (3 steps, first move east)" in report
    assert "Healing shrines remaining: 0 (none left)" in report
    assert "Monsters alive: 2" in report
    assert "still" not in report
    assert state.to_dict() == before


def test_threat_report_ranks_monsters_and_rest_safety_without_mutation():
    state = new_game(seed=24, width=11, height=11)
    state.tiles = ["#" * 11, *["#.........#" for _ in range(9)], "#" * 11]
    state.treasures.clear()
    state.shrines.clear()
    close = state.monsters[0]
    far = state.monsters[1]
    state.monsters = [far, close]
    state.player.position.x = 5
    state.player.position.y = 5
    close.name = "ash goblin"
    close.position.x = 6
    close.position.y = 5
    far.name = "rust knight"
    far.position.x = 9
    far.position.y = 9
    before = state.to_dict()

    report = threat_report(state)

    assert report.splitlines()[1].startswith("- ash goblin")
    assert "1 steps away — adjacent and ready to strike" in report
    assert "rust knight" in report
    assert "Rest outlook: unsafe" in report
    assert state.to_dict() == before


def test_adventure_log_limits_numbers_and_does_not_mutate_state():
    state = new_game(seed=25)
    state.log.extend(["A door creaks.", "Boots splash in ash.", "A goblin curses."])
    before = state.to_dict()

    report = adventure_log(state, limit=2)

    assert "Kalidor's last 2 journal entries" in report
    assert "3. Boots splash in ash." in report
    assert "4. A goblin curses." in report
    assert "A door creaks" not in report
    assert state.to_dict() == before


def test_legend_explains_glyphs_with_live_counts_without_mutation():
    state = new_game(seed=26)
    state.monsters = state.monsters[:3]
    state.treasures = state.treasures[:2]
    state.shrines = state.shrines[:1]
    before = state.to_dict()

    report = legend(state)

    assert "@ Kalidor: level 1, 24/24 HP" in report
    assert "# stone wall" in report
    assert ". corridor floor" in report
    assert "M monster: 3 alive" in report
    assert "$ treasure: 2 relic caches remain" in report
    assert "+ shrine: 1 healing shrines remain" in report
    assert "> ember gate: seek it to win" in report
    assert state.to_dict() == before


def test_bestiary_groups_monsters_with_stats_rewards_and_distance_without_mutation():
    state = new_game(seed=27, width=11, height=11)
    state.tiles = ["#" * 11, *["#.........#" for _ in range(9)], "#" * 11]
    first = state.monsters[0]
    second = state.monsters[1]
    third = state.monsters[2]
    state.monsters = [first, second, third]
    state.player.position.x = 5
    state.player.position.y = 5
    first.name = "ash goblin"
    first.position.x = 6
    first.position.y = 5
    first.stats.hp = 5
    first.stats.attack = 3
    first.stats.defense = 1
    first.xp = 4
    first.gold = 2
    second.name = "ash goblin"
    second.position.x = 9
    second.position.y = 5
    second.stats.hp = 9
    second.stats.attack = 5
    second.stats.defense = 2
    second.xp = 8
    second.gold = 7
    third.name = "rust knight"
    third.position.x = 9
    third.position.y = 9
    third.stats.hp = 11
    third.stats.attack = 6
    third.stats.defense = 3
    third.xp = 10
    third.gold = 4
    before = state.to_dict()

    report = bestiary(state)

    assert "Emberfall field bestiary" in report
    assert "ash goblin x2: HP 5-9, ATK 3-5, DEF 1-2, XP 4-8, gold 2-7" in report
    assert "nearest 1 steps (adjacent and ready to strike)" in report
    assert "rust knight x1: HP 11, ATK 6, DEF 3, XP 10, gold 4" in report
    assert state.to_dict() == before


def test_combat_advice_estimates_adjacent_fight_without_mutation():
    state = new_game(seed=30, width=11, height=11)
    state.tiles = ["#" * 11, *["#.........#" for _ in range(9)], "#" * 11]
    monster = state.monsters[0]
    state.monsters = [monster]
    state.player.position.x = 5
    state.player.position.y = 5
    state.player.stats.hp = 12
    monster.name = "ash goblin"
    monster.position.x = 6
    monster.position.y = 5
    monster.stats.hp = 7
    monster.stats.max_hp = 7
    monster.stats.attack = 4
    monster.stats.defense = 1
    before = state.to_dict()

    report = combat_advice(state)

    assert "Kalidor weighs the next exchange" in report
    assert "east: ash goblin at 7/7 HP" in report
    assert "you hit for 5, it hits for 2" in report
    assert "defeat in 2 swings, survival margin 6 enemy swings (favorable)" in report
    assert state.to_dict() == before


def test_combat_advice_points_to_nearest_threat_when_not_adjacent():
    state = new_game(seed=31, width=11, height=11)
    state.tiles = ["#" * 11, *["#.........#" for _ in range(9)], "#" * 11]
    monster = state.monsters[0]
    state.monsters = [monster]
    state.player.position.x = 5
    state.player.position.y = 5
    monster.name = "rust knight"
    monster.position.x = 9
    monster.position.y = 5
    before = state.to_dict()

    report = combat_advice(state)

    assert "No adjacent enemy. Nearest: rust knight, 4 steps away" in report
    assert "Tactical hint" in report
    assert state.to_dict() == before


def test_tactical_hint_recommends_treasure_route_without_mutation():
    state = new_game(seed=32, width=11, height=11)
    state.tiles = [
        "###########",
        "#........>#",
        *["#.........#" for _ in range(8)],
        "###########",
    ]
    state.player.position.x = 1
    state.player.position.y = 1
    state.monsters.clear()
    state.treasures = [state.player.position.moved(Direction.EAST).moved(Direction.EAST)]
    state.shrines.clear()
    before = state.to_dict()

    report = tactical_hint(state)

    assert "Kalidor considers his next move" in report
    assert "Recommended action: move east toward treasure for relic boons" in report
    assert state.to_dict() == before


def test_tactical_hint_prefers_rest_when_hurt_and_safe():
    state = new_game(seed=33, width=11, height=11)
    state.tiles = ["#" * 11, *["#.........#" for _ in range(9)], "#" * 11]
    state.monsters.clear()
    state.player.stats.hp = 10
    before = state.to_dict()

    report = tactical_hint(state)

    assert "Recommended action: rest" in report
    assert "HP is low" in report
    assert state.to_dict() == before


def test_tactical_hint_recommends_winnable_adjacent_attack():
    state = new_game(seed=34, width=11, height=11)
    state.tiles = ["#" * 11, *["#.........#" for _ in range(9)], "#" * 11]
    monster = state.monsters[0]
    state.monsters = [monster]
    state.player.position.x = 5
    state.player.position.y = 5
    monster.name = "ash goblin"
    monster.position.x = 6
    monster.position.y = 5
    monster.stats.hp = 5
    monster.stats.defense = 1
    monster.stats.attack = 3
    before = state.to_dict()

    report = tactical_hint(state)

    assert "Recommended action: move east to strike the ash goblin" in report
    assert "expected win in 1 swings" in report
    assert state.to_dict() == before


def test_route_plan_plots_shortest_safe_path_without_mutation():
    state = new_game(seed=28, width=11, height=11)
    state.tiles = [
        "###########",
        "#........>#",
        *["#.........#" for _ in range(8)],
        "###########",
    ]
    state.player.position.x = 1
    state.player.position.y = 1
    state.monsters.clear()
    state.treasures = [state.player.position.moved(Direction.EAST).moved(Direction.EAST)]
    state.shrines.clear()
    before = state.to_dict()

    report = route_plan(state, goal="treasure")

    assert "Kalidor plots a route toward treasure" in report
    assert "Destination: treasure cache" in report
    assert "Distance: 2 steps" in report
    assert "First move: east" in report
    assert "Route: east, east" in report
    assert state.to_dict() == before


def test_route_plan_reports_missing_objective_without_mutation():
    state = new_game(seed=29)
    state.shrines.clear()
    before = state.to_dict()

    report = route_plan(state, goal="shrine")

    assert "No shrine objective remains" in report
    assert state.to_dict() == before


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


def test_rest_recovers_hp_when_no_monster_is_close():
    state = new_game(seed=18, width=11, height=11)
    state.tiles = ["#" * 11, *["#.........#" for _ in range(9)], "#" * 11]
    state.monsters.clear()
    state.player.stats.hp = 20

    rest(state)

    assert state.player.stats.hp == 22
    assert "recovers 2 HP" in state.log[-1]


def test_rest_is_interrupted_by_nearby_monsters():
    state = new_game(seed=19, width=11, height=11)
    state.tiles = ["#" * 11, *["#.........#" for _ in range(9)], "#" * 11]
    monster = state.monsters[0]
    state.monsters = [monster]
    state.player.position.x = 5
    state.player.position.y = 5
    state.player.stats.hp = 20
    monster.position.x = 6
    monster.position.y = 5

    rest(state)

    assert state.player.stats.hp < 20
    assert "No time to rest" in state.log[-2]
