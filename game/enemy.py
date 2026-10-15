"""Enemies that patrol platforms."""

import pygame

from .settings import (
    TILE,
    ENEMY_WIDTH,
    ENEMY_HEIGHT,
    ENEMY_SPEED,
)


class Enemy:
    """A blob that patrols its platform, turning around at walls and edges."""

    def __init__(self, x, y):
        # Stands on the floor of the tile cell whose top-left is (x, y).
        self.rect = pygame.Rect(0, 0, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.rect.midbottom = (x + TILE // 2, y + TILE)
        self.x = float(self.rect.x)
        self.direction = -1  # 1 is right, -1 is left

    def update(self, level):
        step = ENEMY_SPEED * self.direction
        self.x += step
        self.rect.x = round(self.x)
        front = self.rect.right if self.direction > 0 else self.rect.left - 1
        wall = level.solid_at(front, self.rect.centery)
        edge = not level.solid_at(front, self.rect.bottom + 1)
        outside = self.rect.left < 0 or self.rect.right > level.width
        if wall or edge or outside:
            self.x -= step
            self.rect.x = round(self.x)
            self.direction = -self.direction
