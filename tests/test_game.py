import pygame
import pytest

from conftest import LEFT, NO_KEYS, RIGHT
import main
from main import LEVELS, TILE, Game

# Small levels where walking right reaches the door quickly.
SHORT = [
    "......",
    ".P..D.",
    "######",
]
WITH_PIT = [
    "......",
    ".P....",
    "##..##",
]


COIN_ON_PATH = [
    "........",
    ".P.C..D.",
    "########",
]
COIN_OVER_PIT = [
    "......",
    ".P.C..",
    "##..##",
]


def walk_right_until_level_changes(game, frames=120):
    index = game.level_index
    for _ in range(frames):
        game.update(RIGHT)
        if game.won or game.level_index != index:
            return


def test_starts_on_first_level_at_its_start():
    game = Game()
    assert game.level_index == 0
    assert not game.won
    assert game.player.rect.topleft == game.level.start


def test_touching_door_goes_to_next_level():
    game = Game([SHORT, SHORT, SHORT])
    walk_right_until_level_changes(game)
    assert game.level_index == 1
    assert not game.won
    assert game.player.rect.topleft == game.level.start


def test_touching_last_door_wins():
    game = Game([SHORT, SHORT])
    walk_right_until_level_changes(game)
    walk_right_until_level_changes(game)
    assert game.won


def test_nothing_moves_after_winning():
    game = Game([SHORT])
    walk_right_until_level_changes(game)
    assert game.won
    position = game.player.rect.topleft
    game.update(RIGHT)
    assert game.player.rect.topleft == position


def test_restart_returns_to_first_level():
    game = Game([SHORT, SHORT])
    walk_right_until_level_changes(game)
    walk_right_until_level_changes(game)
    game.restart()
    assert game.level_index == 0
    assert not game.won
    assert game.player.rect.topleft == game.level.start


def test_falling_off_the_level_respawns_at_start():
    game = Game([WITH_PIT])
    for _ in range(10):
        game.update(RIGHT)
    for _ in range(60):
        game.update(NO_KEYS)
        if game.player.rect.topleft == game.level.start:
            break
    assert game.player.rect.topleft == game.level.start


@pytest.mark.parametrize("keys, edge", [(LEFT, "left"), (RIGHT, "right")])
def test_player_cannot_leave_the_sides_of_the_level(keys, edge):
    game = Game([[
        "........",
        "...P....",
        "########",
    ]])
    for _ in range(120):
        game.update(keys)
    if edge == "left":
        assert game.player.rect.left == 0
    else:
        assert game.player.rect.right == game.level.width


def test_total_coins_counts_every_level():
    assert Game([COIN_ON_PATH, SHORT, COIN_ON_PATH]).total_coins == 2
    assert Game().total_coins == sum("".join(layout).count("C") for layout in LEVELS)


def test_touching_a_coin_collects_it():
    game = Game([COIN_ON_PATH, SHORT])
    assert game.coins_collected == 0
    for _ in range(20):
        game.update(RIGHT)
    assert game.coins_collected == 1
    assert game.level.coins == []


def test_a_coin_can_only_be_collected_once():
    game = Game([COIN_ON_PATH, SHORT])
    for _ in range(20):
        game.update(RIGHT)
    for _ in range(20):
        game.update(LEFT)
    for _ in range(20):
        game.update(RIGHT)
    assert game.coins_collected == 1


def test_coins_stay_collected_after_falling_and_respawning():
    game = Game([COIN_OVER_PIT])
    for _ in range(80):
        game.update(RIGHT)
    assert game.player.rect.topleft != game.level.start or game.coins_collected == 1
    assert game.coins_collected == 1
    assert game.level.coins == []


def test_coin_count_carries_over_to_the_next_level():
    game = Game([COIN_ON_PATH, COIN_ON_PATH, SHORT])
    walk_right_until_level_changes(game)
    assert game.level_index == 1
    assert game.coins_collected == 1
    walk_right_until_level_changes(game)
    assert game.coins_collected == 2


def test_skipped_coins_are_not_counted():
    game = Game([COIN_ON_PATH])
    game.level.coins.clear()  # as if the player had gone around it
    walk_right_until_level_changes(game)
    assert game.won
    assert game.coins_collected == 0


def test_restart_resets_coins_and_puts_them_back():
    game = Game([COIN_ON_PATH])
    walk_right_until_level_changes(game)
    assert game.won and game.coins_collected == 1
    game.restart()
    assert game.coins_collected == 0
    assert len(game.level.coins) == 1


def test_jump_controls_reach_the_player():
    game = Game([SHORT])
    for _ in range(30):
        game.update(NO_KEYS)
    game.jump_pressed()
    assert game.player.vel_y < 0
    game.jump_released()
    assert game.player.vel_y > -main.JUMP_SPEED / 2


def test_real_levels_are_used_by_default():
    assert Game().levels is LEVELS


def test_game_window_runs_and_quits(monkeypatch):
    """Smoke test: the real main loop starts, draws every level and the win screen, and exits."""
    # Start each level on its door, so the loop moves through every level to the win screen.
    original_init = main.Level.__init__

    def start_on_door(self, layout):
        original_init(self, layout)
        self.start = self.door.topleft

    monkeypatch.setattr(main.Level, "__init__", start_on_door)
    pygame.init()
    pygame.time.set_timer(pygame.QUIT, 500)
    main.main()  # Returns once the timer's QUIT event arrives; main() also shuts pygame down.
