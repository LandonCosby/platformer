import pytest

from game.game import Game
from game.level import Level
from game.levels import LEVELS
from game.settings import MOVE_SPEED, TILE, WIDTH
from reachability import (
    Surface,
    can_reach_door,
    can_touch,
    reachable_surfaces,
    find_surfaces,
    jump_arc,
    reach,
    unreachable_coins,
)

LEVEL_IDS = [f"level{i}" for i in range(1, len(LEVELS) + 1)]


def test_parses_tiles_start_and_door():
    level = Level([
        "..C.",
        ".P.D",
        "####",
    ])
    assert len(level.tiles) == 4
    assert len(level.coins) == 1
    assert level.coins[0].center == (2 * TILE + TILE // 2, TILE // 2)
    assert all(tile.size == (TILE, TILE) for tile in level.tiles)
    assert level.start == (TILE, TILE)
    # The door is two tiles tall, standing on the ground in its cell.
    assert level.door.bottom == 2 * TILE
    assert level.door.height == 2 * TILE
    assert level.door.left > 3 * TILE and level.door.right < 4 * TILE
    assert (level.width, level.height) == (4 * TILE, 3 * TILE)


def test_there_are_at_least_three_levels():
    assert len(LEVELS) >= 3


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_levels_are_at_least_three_screens_long(layout):
    assert Level(layout).width >= 3 * WIDTH


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_level_layout_is_well_formed(layout):
    text = "".join(layout)
    assert set(text) <= set(".#PDCEK"), "unknown character in layout"
    assert text.count("K") == 1, "needs exactly one checkpoint"
    assert text.count("C") >= 1, "every level should have at least one coin"
    assert text.count("P") == 1, "needs exactly one player start"
    assert text.count("D") == 1, "needs exactly one door"
    assert len({len(row) for row in layout}) == 1, "all rows should be the same length"


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_every_level_has_enemies(layout):
    assert 3 <= "".join(layout).count("E") <= 4


def enemy_cells(layout):
    return [(r, c) for r, line in enumerate(layout) for c, ch in enumerate(line) if ch == "E"]


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_enemies_stand_on_a_platform_with_room_to_patrol(layout):
    for r, c in enemy_cells(layout):
        assert layout[r + 1][c] == "#", f"enemy at row {r}, col {c} has no ground under it"
        room = sum(1 for cc in (c - 1, c + 1) if layout[r + 1][cc] == "#" and layout[r][cc] != "#")
        assert room >= 1, f"enemy at row {r}, col {c} has nowhere to walk"


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_enemies_are_not_next_to_the_start(layout):
    text_rows = [line.find("P") for line in layout]
    start_row = next(r for r, c in enumerate(text_rows) if c >= 0)
    start_col = text_rows[start_row]
    for r, c in enemy_cells(layout):
        assert abs(c - start_col) >= 5 or abs(r - start_row) >= 3


def checkpoint_cell(layout):
    return next((r, c) for r, line in enumerate(layout) for c, ch in enumerate(line) if ch == "K")


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_checkpoint_is_about_halfway_and_on_the_ground(layout):
    r, c = checkpoint_cell(layout)
    assert 0.35 <= c / len(layout[0]) <= 0.65
    assert layout[r + 1][c] == "#"


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_checkpoint_can_be_reached(layout):
    level, surfaces = reachable_surfaces(layout)
    assert any(can_touch(s, level.checkpoint) for s in surfaces)


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_checkpoint_is_not_on_an_enemy_patrol(layout):
    # Respawning onto a patrolling enemy would be unfair: an enemy on the same row
    # must have a gap in the ground between it and the flag.
    flag_row, flag_col = checkpoint_cell(layout)
    for r, c in enemy_cells(layout):
        if r == flag_row:
            ground_between = layout[r + 1][min(c, flag_col):max(c, flag_col) + 1]
            assert "." in ground_between, f"the enemy at col {c} can walk to the checkpoint"


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_player_does_not_start_on_the_door(layout):
    level = Level(layout)
    game = Game([layout])
    assert not game.player.rect.colliderect(level.door)


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_every_level_can_be_finished(layout):
    assert can_reach_door(layout)


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_every_coin_can_be_collected(layout):
    assert unreachable_coins(layout) == []


# The checker itself: it must say no to levels that really can't be done.

def test_finds_platform_surfaces():
    surfaces = find_surfaces([
        "......",
        ".##...",
        "....##",
        "######",
    ])
    assert Surface(1 * TILE, 3 * TILE, 1 * TILE) in surfaces
    assert Surface(4 * TILE, 6 * TILE, 2 * TILE) in surfaces
    assert Surface(0, 4 * TILE, 3 * TILE) in surfaces  # floor under the open part only
    assert len(surfaces) == 3


def test_running_start_jumps_further_than_standing_jump():
    standing = reach(jump_arc(0), 0)
    running = reach(jump_arc(MOVE_SPEED), 0)
    assert running > standing > 0


def test_detects_a_door_too_high_to_reach():
    impossible = [
        ".......D",
        ".....###",
        "........",
        "........",
        "........",
        "........",
        ".P......",
        "########",
    ]
    assert not can_reach_door(impossible)


def test_detects_a_gap_too_wide_to_jump():
    impossible = [
        "........................",
        ".P....................D.",
        "####..............######",
    ]
    assert not can_reach_door(impossible)


def test_reaches_a_door_across_a_small_gap():
    possible = [
        "............",
        ".P........D.",
        "#####..#####",
    ]
    assert can_reach_door(possible)


def test_detects_a_coin_too_high_to_reach():
    level = [
        "....C...",
        "........",
        "........",
        "........",
        "........",
        "........",
        ".P....D.",
        "########",
    ]
    assert unreachable_coins(level) == [Level(level).coins[0].center]
