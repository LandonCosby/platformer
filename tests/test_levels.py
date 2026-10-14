from collections import deque

import pytest

from conftest import LEFT, NO_KEYS, RIGHT
from main import LEVELS, TILE, Game, Level

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
def test_level_layout_is_well_formed(layout):
    text = "".join(layout)
    assert set(text) <= set(".#PDC"), "unknown character in layout"
    assert text.count("C") >= 1, "every level should have at least one coin"
    assert text.count("P") == 1, "needs exactly one player start"
    assert text.count("D") == 1, "needs exactly one door"
    assert len({len(row) for row in layout}) == 1, "all rows should be the same length"


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_player_does_not_start_on_the_door(layout):
    level = Level(layout)
    game = Game([layout])
    assert not game.player.rect.colliderect(level.door)


def can_finish(layout):
    """Whether the door can be reached."""
    return search(Game([layout]), lambda game: game.won)


def can_collect(layout, coin_index):
    """Whether one particular coin can be reached (the level's other coins are removed)."""
    rows = [[] for _ in layout]
    seen_coins = 0
    for r, line in enumerate(layout):
        for char in line:
            if char == "C":
                char = "C" if seen_coins == coin_index else "."
                seen_coins += 1
            rows[r].append(char)
    game = Game([["".join(row) for row in rows]])
    return search(game, lambda game: game.coins_collected == 1)


def search(game, goal, max_states=200_000):
    """Search every combination of left/right/none and jump, using the real game rules,
    to see whether goal(game) can be made true."""
    for _ in range(30):
        game.update(NO_KEYS)
    p = game.player
    start = (p.rect.x, p.rect.y, p.vel_y, p.on_ground)
    seen, queue = {start}, deque([start])
    while queue and len(seen) < max_states:
        x, y, vel_y, on_ground = queue.popleft()
        for jump in (False, True) if on_ground else (False,):
            for keys in (NO_KEYS, LEFT, RIGHT):
                p.rect.topleft, p.vel_y, p.on_ground = (x, y), vel_y, on_ground
                if jump:
                    game.jump_pressed()
                game.update(keys)
                if goal(game):
                    return True
                if game.won:
                    # Reached the door while looking for something else: a dead end.
                    game.won = False
                    continue
                state = (p.rect.x, p.rect.y, round(p.vel_y, 2), p.on_ground)
                if state not in seen:
                    seen.add(state)
                    queue.append(state)
    return False


@pytest.mark.parametrize("layout", LEVELS, ids=LEVEL_IDS)
def test_every_level_can_be_finished(layout):
    assert can_finish(layout)


COINS = [
    pytest.param(layout, index, id=f"level{level}-coin{index + 1}")
    for level, layout in enumerate(LEVELS, 1)
    for index in range("".join(layout).count("C"))
]


@pytest.mark.parametrize("layout, coin_index", COINS)
def test_every_coin_can_be_collected(layout, coin_index):
    assert can_collect(layout, coin_index)


def test_solver_detects_an_unreachable_coin():
    sealed = [
        "#####",
        "#C#..",
        "###..",
        "...P.",
        "#####",
    ]
    assert not can_collect(sealed, 0)


def test_solver_detects_an_impossible_level():
    # Door on a ledge far too high to jump to.
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
    assert not can_finish(impossible)
