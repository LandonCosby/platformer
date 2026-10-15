"""Turning a level layout into tiles, coins, enemies, a checkpoint and a door."""

import pygame

from .settings import (
    TILE,
    COIN_SIZE,
    PLAYER_SIZE,
)
from .enemy import Enemy


class Level:
    def __init__(self, layout):
        self.tiles = []
        self.solid = set()  # (col, row) of every solid tile
        self.start = (TILE, TILE)
        self.door = None
        self.checkpoint = None  # the flag's area: touching it saves the respawn point
        self.checkpoint_spawn = None  # where the player respawns once the flag is touched
        self.coins = []
        self.enemies = []
        for row, line in enumerate(layout):
            for col, char in enumerate(line):
                if char == "#":
                    self.tiles.append(pygame.Rect(col * TILE, row * TILE, TILE, TILE))
                    self.solid.add((col, row))
                elif char == "E":
                    self.enemies.append(Enemy(col * TILE, row * TILE))
                elif char == "P":
                    self.start = (col * TILE, row * TILE)
                elif char == "D":
                    self.door = pygame.Rect(col * TILE + 6, (row - 1) * TILE, TILE - 12, 2 * TILE)
                elif char == "K":
                    # Two tiles tall like the door, so it's easy to touch while passing.
                    self.checkpoint = pygame.Rect(col * TILE, (row - 1) * TILE, TILE, 2 * TILE)
                    self.checkpoint_spawn = (col * TILE + (TILE - PLAYER_SIZE) // 2, row * TILE)
                elif char == "C":
                    coin = pygame.Rect(0, 0, COIN_SIZE, COIN_SIZE)
                    coin.center = (col * TILE + TILE // 2, row * TILE + TILE // 2)
                    self.coins.append(coin)
        self.width = max(len(line) for line in layout) * TILE
        self.height = len(layout) * TILE

    def solid_at(self, x, y):
        """Whether the pixel (x, y) is inside a solid tile."""
        return (x // TILE, y // TILE) in self.solid
