"""Game rules: levels, coins, the checkpoint, the door, health and enemies."""

from .settings import (
    JUMP_SPEED,
    MAX_HEALTH,
    INVINCIBLE_FRAMES,
    STOMP_BOUNCE,
    KNOCKBACK_SPEED,
    KNOCKBACK_HOP,
    JUMP_KEYS,
)
from .level import Level
from .levels import LEVELS
from .player import Player


class Game:
    """Game state and rules, kept separate from input handling and drawing."""

    def __init__(self, levels=LEVELS):
        self.levels = levels
        self.total_coins = sum("".join(layout).count("C") for layout in levels)
        self.restart()

    def restart(self):
        self.won = False
        self.coins_collected = 0
        self.start_level(0)

    def start_level(self, index):
        self.level_index = index
        self.level = Level(self.levels[index])
        self.player = Player(*self.level.start)
        self.health = MAX_HEALTH
        self.invincible = 0  # frames of invincibility left
        self.coins_at_level_start = self.coins_collected
        self.checkpoint_reached = False

    def restart_level(self):
        """Start the current level again from the beginning: full health, the checkpoint
        is reset, and its coins are put back."""
        self.coins_collected = self.coins_at_level_start
        self.start_level(self.level_index)

    def damage(self, amount=1, ignore_invincibility=False):
        """Take hearts away. For enemies and obstacles to call. Returns whether it hurt.

        Losing the last heart restarts the level. Otherwise the player is briefly
        invincible, so one touch can't take several hearts.
        """
        if self.invincible and not ignore_invincibility:
            return False
        self.health -= amount
        if self.health <= 0:
            self.restart_level()
        else:
            self.invincible = INVINCIBLE_FRAMES
        return True

    def jump_pressed(self):
        self.player.jump()

    def jump_released(self):
        self.player.cut_jump()

    def update(self, keys):
        if self.won:
            return
        player, level = self.player, self.level
        if self.invincible:
            self.invincible -= 1
        for enemy in level.enemies:
            enemy.update(level)
        feet_before = player.rect.bottom  # to tell a stomp from a side hit
        player.update(keys, level.tiles)

        # Keep the player inside the level horizontally.
        if player.rect.left < 0 or player.rect.right > level.width:
            player.rect.left = max(player.rect.left, 0)
            player.rect.right = min(player.rect.right, level.width)
            player.x = float(player.rect.x)
            player.vel_x = 0

        # Touching the checkpoint flag moves the respawn point there.
        if level.checkpoint and not self.checkpoint_reached and player.rect.colliderect(level.checkpoint):
            self.checkpoint_reached = True
            player.spawn = level.checkpoint_spawn

        # Falling off the bottom costs a heart (even while invincible) and respawns,
        # at the checkpoint once it has been reached.
        if player.rect.top > level.height:
            player.respawn()
            self.damage(ignore_invincibility=True)
            if self.level is not level:  # that was the last heart: the level restarted
                return

        # Enemies: landing on top defeats them, touching them any other way hurts.
        for enemy in [e for e in level.enemies if player.rect.colliderect(e.rect)]:
            if player.vel_y > 0 and feet_before <= enemy.rect.top:
                level.enemies.remove(enemy)
                player.rect.bottom = enemy.rect.top
                jump_held = any(keys[key] for key in JUMP_KEYS)
                player.vel_y = -JUMP_SPEED if jump_held else -STOMP_BOUNCE
            elif self.damage():
                if self.level is not level:  # that was the last heart: the level restarted
                    return
                away = 1 if player.rect.centerx >= enemy.rect.centerx else -1
                player.vel_x = away * KNOCKBACK_SPEED
                player.vel_y = -KNOCKBACK_HOP

        # Collected coins stay collected, even if the player falls and respawns.
        for coin in [c for c in level.coins if player.rect.colliderect(c)]:
            level.coins.remove(coin)
            self.coins_collected += 1

        # Touching the door goes to the next level, or wins after the last one.
        if level.door and player.rect.colliderect(level.door):
            if self.level_index + 1 < len(self.levels):
                self.start_level(self.level_index + 1)
            else:
                self.won = True
