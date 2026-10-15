import math

import pygame
import pytest

from conftest import LEFT, NO_KEYS, RIGHT, Keys
from game.level import Level
from game.player import Player
from game.settings import (
    ACCELERATION,
    AIR_CONTROL,
    GRAVITY,
    MAX_FALL_SPEED,
    MOVE_SPEED,
    PLAYER_SIZE,
    TILE,
    TURN_ACCELERATION,
)

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
    assert (grounded.rect.x - x) * direction > 0
    assert grounded.vel_x * direction > 0


@pytest.fixture
def long_floor():
    """A level wide enough to reach top speed and slide to a stop without hitting anything."""
    level = Level([
        "." * 60,
        "." * 30 + "P" + "." * 29,
        "#" * 60,
    ])
    player = Player(*level.start)
    run(player, level, frames=30)
    return player, level


def test_speeds_up_gradually(long_floor):
    player, level = long_floor
    speeds = []
    for _ in range(5):
        run(player, level, RIGHT)
        speeds.append(player.vel_x)
    assert speeds[0] == pytest.approx(ACCELERATION)
    assert speeds == sorted(speeds)
    assert speeds[-1] < MOVE_SPEED


def test_reaches_and_holds_top_speed(long_floor):
    player, level = long_floor
    run(player, level, RIGHT, frames=60)
    assert player.vel_x == MOVE_SPEED
    x = player.rect.x
    run(player, level, RIGHT, frames=10)
    assert player.rect.x - x == MOVE_SPEED * 10


def test_slides_to_a_stop_after_letting_go(long_floor):
    player, level = long_floor
    run(player, level, RIGHT, frames=60)
    x = player.rect.x
    run(player, level)
    assert 0 < player.vel_x < MOVE_SPEED  # still moving, but slower
    run(player, level, frames=60)
    assert player.vel_x == 0
    assert player.rect.x > x  # slid forward before stopping
    stopped_at = player.rect.x
    run(player, level, frames=10)
    assert player.rect.x == stopped_at


def test_turning_around_is_quicker_than_starting(long_floor):
    player, level = long_floor
    run(player, level, RIGHT, frames=60)
    run(player, level, LEFT)
    assert MOVE_SPEED - player.vel_x == pytest.approx(TURN_ACCELERATION)
    assert TURN_ACCELERATION > ACCELERATION


def test_less_control_in_the_air(long_floor):
    player, level = long_floor
    player.jump()
    run(player, level, RIGHT)  # take-off frame still counts as on the ground
    assert not player.on_ground
    speed = player.vel_x
    run(player, level, RIGHT)
    assert player.vel_x - speed == pytest.approx(ACCELERATION * AIR_CONTROL)


def test_hitting_a_wall_stops_horizontal_speed():
    level = Level([
        "......",
        ".P..#.",
        "######",
    ])
    player = Player(*level.start)
    run(player, level, RIGHT, frames=60)
    assert player.rect.right == 4 * TILE
    # Pushing into the wall can only build a sliver of speed before it is stopped again.
    assert 0 <= player.vel_x <= 2 * ACCELERATION
    run(player, level, LEFT, frames=2)
    assert player.vel_x < 0  # turns away straight off, with no built-up speed to cancel


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


def turn_per_frame(player, level, keys):
    """Signed turn over one frame: positive is clockwise."""
    before = player.angle
    run(player, level, keys)
    return (player.angle - before + math.pi) % math.tau - math.pi


@pytest.mark.parametrize("keys, sign", [(RIGHT, 1), (LEFT, -1)])
def test_rolls_clockwise_moving_right_and_anticlockwise_moving_left(long_floor, keys, sign):
    player, level = long_floor
    run(player, level, keys, frames=20)
    assert turn_per_frame(player, level, keys) * sign > 0


def test_rolls_like_a_ball_one_turn_per_circumference(long_floor):
    player, level = long_floor
    run(player, level, RIGHT, frames=20)
    start_x, start_angle = player.x, player.angle
    run(player, level, RIGHT, frames=3)
    turned = (player.angle - start_angle) % math.tau
    assert turned == pytest.approx((player.x - start_x) / (PLAYER_SIZE / 2))


def test_does_not_roll_while_standing_still(grounded, level):
    angle = grounded.angle
    run(grounded, level, frames=20)
    assert grounded.angle == angle


def test_does_not_roll_when_pushing_against_a_wall():
    level = Level([
        "......",
        ".P..#.",
        "######",
    ])
    player = Player(*level.start)
    run(player, level, RIGHT, frames=60)  # now pressed against the wall
    angle = player.angle
    run(player, level, RIGHT, frames=20)
    assert player.angle == pytest.approx(angle, abs=0.1)


def test_angle_stays_within_one_turn(long_floor):
    player, level = long_floor
    run(player, level, RIGHT, frames=200)
    assert 0 <= player.angle < math.tau


def test_respawn_returns_to_start_and_stops(level):
    player = Player(*level.start)
    run(player, level, RIGHT, frames=20)
    player.vel_y = 10
    player.respawn()
    assert player.rect.topleft == level.start
    assert player.x == level.start[0]
    assert player.angle == 0  # upright again
    assert player.vel_x == 0
    assert player.vel_y == 0
