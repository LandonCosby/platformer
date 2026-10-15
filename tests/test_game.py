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
    fell = False
    for _ in range(120):
        game.update(RIGHT)
        if game.player.rect.top > 2 * TILE:
            fell = True
        if fell and game.player.rect.topleft == game.level.start:
            break
    assert fell
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
    # The edge stops the player like a wall: only a sliver of speed between frames.
    assert abs(game.player.vel_x) <= 2 * main.ACCELERATION


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


def fall_into_pit(game):
    """Walk right into the pit in WITH_PIT and wait until the respawn."""
    level = game.level
    for _ in range(120):
        game.update(RIGHT)
        if game.player.rect.topleft == game.level.start and game.player.vel_y == 0:
            if game.level is not level or game.health < main.MAX_HEALTH:
                return


def test_starts_with_full_health():
    game = Game([SHORT])
    assert game.health == main.MAX_HEALTH == 3
    assert game.invincible == 0


def test_damage_takes_a_heart_and_makes_the_player_briefly_invincible():
    game = Game([SHORT])
    assert game.damage()
    assert game.health == 2
    assert game.invincible == main.INVINCIBLE_FRAMES


def test_no_damage_while_invincible():
    game = Game([SHORT])
    game.damage()
    assert not game.damage()
    assert game.health == 2


def test_can_be_hurt_again_once_invincibility_wears_off():
    game = Game([[".........", ".P.......", "#########"]])
    game.damage()
    for _ in range(main.INVINCIBLE_FRAMES):
        game.update(NO_KEYS)
    assert game.invincible == 0
    assert game.damage()
    assert game.health == 1


def test_damage_can_take_more_than_one_heart():
    game = Game([SHORT])
    game.damage(2)
    assert game.health == 1


def test_falling_in_a_pit_costs_a_heart():
    game = Game([WITH_PIT])
    fall_into_pit(game)
    assert game.health == 2


def test_falling_in_a_pit_costs_a_heart_even_while_invincible():
    game = Game([WITH_PIT])
    game.damage()
    fall_into_pit(game)
    assert game.health == 1


def test_losing_every_heart_restarts_the_level():
    game = Game([WITH_PIT])
    game.damage()
    game.damage(ignore_invincibility=True)
    assert game.health == 1
    game.player.rect.x += 50  # somewhere other than the start
    game.damage(ignore_invincibility=True)
    assert game.health == main.MAX_HEALTH
    assert game.invincible == 0
    assert game.player.rect.topleft == game.level.start


def test_restarting_a_level_puts_its_coins_back_but_keeps_earlier_ones():
    game = Game([COIN_ON_PATH, COIN_ON_PATH])
    walk_right_until_level_changes(game)  # collects level 1's coin
    for _ in range(20):
        game.update(RIGHT)  # collects level 2's coin
    assert game.coins_collected == 2
    game.damage(3)
    assert game.level_index == 1
    assert game.coins_collected == 1  # level 1's coin is kept
    assert len(game.level.coins) == 1  # level 2's coin is back


def test_hearts_refill_on_the_next_level():
    game = Game([SHORT, SHORT])
    game.damage()
    walk_right_until_level_changes(game)
    assert game.level_index == 1
    assert game.health == main.MAX_HEALTH


def test_restart_after_winning_gives_full_health():
    game = Game([SHORT])
    game.damage()
    walk_right_until_level_changes(game)
    game.restart()
    assert game.health == main.MAX_HEALTH


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
