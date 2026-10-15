"""The player: movement, jumping and rolling."""

import math

import pygame

from .settings import (
    MOVE_SPEED,
    ACCELERATION,
    FRICTION,
    TURN_ACCELERATION,
    AIR_CONTROL,
    GRAVITY,
    JUMP_SPEED,
    MAX_FALL_SPEED,
    PLAYER_SIZE,
)


class Player:
    def __init__(self, x, y):
        self.spawn = (x, y)
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.x = float(x)  # exact horizontal position; rect.x is this rounded to whole pixels
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing = 1  # 1 is right, -1 is left
        self.angle = 0.0  # how far the player has rolled, in radians; clockwise is positive

    def respawn(self):
        self.rect.topleft = self.spawn
        self.x = float(self.rect.x)
        self.vel_x = self.vel_y = 0
        self.angle = 0.0

    def update(self, keys, tiles):
        direction = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction += 1
        if direction:
            self.facing = direction
        self.accelerate(direction)

        # If something else moved the rect (respawn, level edges), start from there.
        if round(self.x) != self.rect.x:
            self.x = float(self.rect.x)

        # Move and resolve collisions one axis at a time.
        start_x = self.x
        self.x += self.vel_x
        self.rect.x = round(self.x)
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel_x > 0:
                    self.rect.right = tile.left
                elif self.vel_x < 0:
                    self.rect.left = tile.right
                self.x = float(self.rect.x)
                self.vel_x = 0

        # Roll like a ball: turn by the distance actually moved over the radius.
        self.angle = (self.angle + (self.x - start_x) / (PLAYER_SIZE / 2)) % math.tau

        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        self.rect.y += self.vel_y
        self.on_ground = False
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel_y > 0:
                    self.rect.bottom = tile.top
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = tile.bottom
                self.vel_y = 0

    def accelerate(self, direction):
        """Speed up towards top speed in `direction` (-1, 0 or 1), or slow down when it is 0."""
        control = 1 if self.on_ground else AIR_CONTROL
        if direction == 0:
            # Slide to a stop.
            slow = FRICTION * control
            self.vel_x = max(self.vel_x - slow, 0) if self.vel_x > 0 else min(self.vel_x + slow, 0)
            return
        turning = self.vel_x * direction < 0
        step = (TURN_ACCELERATION if turning else ACCELERATION) * control
        self.vel_x = max(-MOVE_SPEED, min(MOVE_SPEED, self.vel_x + step * direction))

    def jump(self):
        if self.on_ground:
            self.vel_y = -JUMP_SPEED

    def cut_jump(self):
        # Releasing jump early gives a shorter hop.
        if self.vel_y < -JUMP_SPEED / 3:
            self.vel_y = -JUMP_SPEED / 3
