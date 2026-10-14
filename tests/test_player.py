import pygame
import pytest

from conftest import LEFT, NO_KEYS, RIGHT, Keys
from main import GRAVITY, MAX_FALL_SPEED, MOVE_SPEED, PLAYER_SIZE, TILE, Level, Player

FLAT = [
    "..........",
    "..........",
    "..........",
    "..........",
    ".P........",
    "##########",
]
GROUND_TOP = 5 * TILE


def run(player, level, keys=NO_KEYS, frames=1):
    for _ in range(frames):
        player.update(keys, level.tiles)


@pytest.fixture
def level():
    return Level(FLAT)


@pytest.fixture
def grounded(level):
    """A player that has already settled onto the ground."""
    player = Player(*level.start)
    run(player, level, frames=30)
    return player


def jump_peak(player, level, release_after=None):
    """Jump and return how many pixels the player's feet rose at the highest point."""
    start = player.rect.bottom
    player.jump()
    highest = start
    for frame in range(120):
        if frame == release_after:
            player.cut_jump()
        run(player, level)
        highest = min(highest, player.rect.bottom)
        if player.on_ground:
            break
    return start - highest


def test_falls_and_lands_on_ground(grounded):
    assert grounded.on_ground
    assert grounded.rect.bottom == GROUND_TOP
    assert grounded.vel_y == 0


def test_gravity_accelerates_falling_up_to_max_speed():
    player = Player(0, 0)
    speeds = []
    for _ in range(60):
        player.update(NO_KEYS, [])
        speeds.append(player.vel_y)
    assert speeds[0] == pytest.approx(GRAVITY)
    assert speeds[1] > speeds[0]
    assert max(speeds) == MAX_FALL_SPEED
    assert not player.on_ground


@pytest.mark.parametrize("keys, direction", [
    (RIGHT, 1),
    (LEFT, -1),
    (Keys({pygame.K_d: True}), 1),
    (Keys({pygame.K_a: True}), -1),
])
def test_moves_left_and_right(grounded, level, keys, direction):
    x = grounded.rect.x
    run(grounded, level, keys, frames=10)
    assert grounded.rect.x == x + direction * MOVE_SPEED * 10


def test_no_keys_means_no_horizontal_movement(grounded, level):
    x = grounded.rect.x
    run(grounded, level, frames=10)
    assert grounded.rect.x == x


def test_jump_leaves_ground_and_lands_again(grounded, level):
    rise = jump_peak(grounded, level)
    assert rise > 0
    assert grounded.on_ground
    assert grounded.rect.bottom == GROUND_TOP


def test_jump_is_high_enough_for_level_design(grounded, level):
    # Levels are built assuming the player can clear two tiles but not four.
    rise = jump_peak(grounded, level)
    assert 2 * TILE < rise < 4 * TILE


def test_cannot_jump_in_mid_air():
    player = Player(0, 0)
    player.update(NO_KEYS, [])
    falling_speed = player.vel_y
    player.jump()
    assert player.vel_y == falling_speed


def test_releasing_jump_early_gives_shorter_jump(level):
    full = Player(*level.start)
    short = Player(*level.start)
    run(full, level, frames=30)
    run(short, level, frames=30)
    assert jump_peak(short, level, release_after=3) < jump_peak(full, level)


def test_walls_block_horizontal_movement():
    level = Level([
        "......",
        ".P..#.",
        "######",
    ])
    player = Player(*level.start)
    run(player, level, RIGHT, frames=60)
    assert player.rect.right == 4 * TILE


def test_ceiling_stops_upward_movement():
    level = Level([
        "#####",
        ".....",
        ".P...",
        "#####",
    ])
    player = Player(*level.start)
    run(player, level, frames=30)
    player.jump()
    run(player, level, frames=60)
    assert player.on_ground
    # The jump was cut short by the ceiling rather than passing through it.
    for _ in range(5):
        player.jump()
        for _ in range(60):
            run(player, level)
            assert player.rect.top >= TILE


def test_player_hitbox_is_square_to_match_its_circle(level):
    player = Player(*level.start)
    assert player.rect.width == player.rect.height == PLAYER_SIZE


def test_player_faces_the_way_it_last_moved(grounded, level):
    assert grounded.facing == 1
    run(grounded, level, LEFT, frames=2)
    assert grounded.facing == -1
    run(grounded, level, frames=5)  # standing still keeps the last direction
    assert grounded.facing == -1
    run(grounded, level, RIGHT, frames=2)
    assert grounded.facing == 1


def test_respawn_returns_to_start_and_stops(level):
    player = Player(*level.start)
    run(player, level, RIGHT, frames=20)
    player.vel_y = 10
    player.respawn()
    assert player.rect.topleft == level.start
    assert player.vel_x == 0
    assert player.vel_y == 0
