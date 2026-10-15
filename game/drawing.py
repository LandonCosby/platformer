"""Drawing the player, enemies, coins, door, tiles and on-screen display.

Every sprite is drawn once at SUPERSAMPLE times its real size, then shrunk with
smoothscale, which gives soft (anti-aliased) edges. The result is cached, so each
sprite is only ever drawn once.
"""

import math
import random
from functools import lru_cache

import pygame

from .settings import (
    WIDTH,
    TILE,
    PLAYER,
    PLAYER_EDGE,
    PLAYER_SIZE,
    EYE_WHITE,
    EYE_PUPIL,
    MOUTH,
    DOOR,
    DOOR_FRAME,
    DOOR_KNOB,
    TEXT,
    COIN,
    COIN_EDGE,
    COIN_SHINE,
    COIN_SIZE,
    HEART,
    HEART_EMPTY,
    HEART_EDGE,
    MAX_HEALTH,
    ENEMY,
    ENEMY_EDGE,
    ENEMY_BROW,
    ENEMY_WIDTH,
    ENEMY_HEIGHT,
    FLAG_POLE,
    FLAG_OFF,
    FLAG_ON,
    GROUND,
    GROUND_LIGHT,
    GROUND_DARK,
    DIRT,
    DIRT_LIGHT,
    DIRT_DARK,
)

SUPERSAMPLE = 4
TILE_VARIANTS = 4  # different speckle patterns, so the ground doesn't look repeated


def smooth_sprite(width, height, paint, alpha=True):
    """Make a width x height sprite: paint(surface, s) draws it at s times the size."""
    s = SUPERSAMPLE
    big = pygame.Surface((width * s, height * s), pygame.SRCALPHA if alpha else 0)
    paint(big, s)
    sprite = pygame.transform.smoothscale(big, (width, height))
    if pygame.display.get_surface() is not None:
        sprite = sprite.convert_alpha() if alpha else sprite.convert()
    return sprite


def round_line(surface, colour, points, width):
    """A thick line with rounded joints, which looks better than draw.lines when thick."""
    for a, b in zip(points, points[1:]):
        pygame.draw.line(surface, colour, a, b, width)
    for point in points:
        pygame.draw.circle(surface, colour, point, width / 2)


# Player

@lru_cache(maxsize=None)
def player_sprite(facing):
    def paint(surface, s):
        c = PLAYER_SIZE * s / 2
        pygame.draw.circle(surface, PLAYER_EDGE, (c, c), PLAYER_SIZE / 2 * s)
        pygame.draw.circle(surface, PLAYER, (c, c), (PLAYER_SIZE / 2 - 2) * s)
        # A soft highlight on the upper left makes it look round.
        pygame.draw.circle(surface, (240, 110, 110), (c - 7 * s, c - 8 * s), 4 * s)
        # Eyes look the way the player is facing.
        for side in (-1, 1):
            ex, ey = c + (side * 6 + facing * 2) * s, c - 4 * s
            pygame.draw.circle(surface, EYE_WHITE, (ex, ey), 5 * s)
            pygame.draw.circle(surface, EYE_PUPIL, (ex + 2 * facing * s, ey), 2.2 * s)
        # Smile: a short curve below the eyes (screen y grows downwards).
        smile = [(c + (facing * 2 + x) * s, c + (4 + (49 - x * x) / 12) * s) for x in range(-7, 8)]
        round_line(surface, MOUTH, smile, 2 * s)
    return smooth_sprite(PLAYER_SIZE, PLAYER_SIZE, paint)


def draw_player(screen, rect, facing, angle=0.0):
    # The sprite is drawn upright; turn it by the roll angle. rotozoom turns
    # anticlockwise for positive degrees, and our angle is clockwise.
    sprite = pygame.transform.rotozoom(player_sprite(facing), -math.degrees(angle), 1)
    screen.blit(sprite, sprite.get_rect(center=rect.center))


# Enemy

@lru_cache(maxsize=None)
def enemy_sprite(direction):
    def paint(surface, s):
        w, h = ENEMY_WIDTH * s, ENEMY_HEIGHT * s
        body = pygame.Rect(0, 0, w, h)
        pygame.draw.rect(surface, ENEMY_EDGE, body, border_top_left_radius=16 * s,
                         border_top_right_radius=16 * s, border_bottom_left_radius=4 * s,
                         border_bottom_right_radius=4 * s)
        pygame.draw.rect(surface, ENEMY, body.inflate(-4 * s, -4 * s), border_top_left_radius=14 * s,
                         border_top_right_radius=14 * s, border_bottom_left_radius=3 * s,
                         border_bottom_right_radius=3 * s)
        pygame.draw.circle(surface, (175, 115, 220), (w / 2 - 8 * s, 7 * s), 3 * s)  # highlight
        cx = w / 2 + direction * 2 * s
        eye_y = 11 * s
        for side in (-1, 1):
            ex = cx + side * 6 * s
            pygame.draw.circle(surface, EYE_WHITE, (ex, eye_y), 4 * s)
            pygame.draw.circle(surface, EYE_PUPIL, (ex + direction * s, eye_y + s), 2 * s)
            # Eyebrows slope down towards the middle.
            outer = (ex + side * 5 * s, eye_y - 7 * s)
            inner = (ex - side * 2 * s, eye_y - 4 * s)
            round_line(surface, ENEMY_BROW, [outer, inner], 2 * s)
    return smooth_sprite(ENEMY_WIDTH, ENEMY_HEIGHT, paint)


def draw_enemy(screen, rect, direction):
    screen.blit(enemy_sprite(direction), rect)


# Coins, door, checkpoint

@lru_cache(maxsize=None)
def coin_sprite():
    def paint(surface, s):
        c, r = COIN_SIZE * s / 2, COIN_SIZE * s / 2
        pygame.draw.circle(surface, COIN_EDGE, (c, c), r)
        pygame.draw.circle(surface, COIN, (c, c), r - 2 * s)
        pygame.draw.circle(surface, COIN_EDGE, (c, c), r - 5 * s, max(1, s))  # inner ring
        pygame.draw.circle(surface, COIN_SHINE, (c - r / 3, c - r / 3), r / 4)
    return smooth_sprite(COIN_SIZE, COIN_SIZE, paint)


def draw_coin(screen, center):
    sprite = coin_sprite()
    screen.blit(sprite, sprite.get_rect(center=center))


@lru_cache(maxsize=None)
def door_sprite(width, height):
    # The frame sticks out 4px on each side and above the door.
    def paint(surface, s):
        frame = pygame.Rect(0, 0, (width + 8) * s, (height + 4) * s)
        door = pygame.Rect(4 * s, 4 * s, width * s, height * s)
        pygame.draw.rect(surface, DOOR_FRAME, frame, border_radius=4 * s)
        pygame.draw.rect(surface, DOOR, door, border_radius=3 * s)
        for top in (0.12, 0.55):  # two inset panels
            panel = pygame.Rect(0, 0, (width - 10) * s, height * 0.33 * s)
            panel.midtop = (door.centerx, door.top + height * top * s)
            pygame.draw.rect(surface, DOOR_FRAME, panel, max(1, s), border_radius=2 * s)
        pygame.draw.circle(surface, DOOR_KNOB, (door.right - 7 * s, door.centery + 4 * s), 3 * s)
    return smooth_sprite(width + 8, height + 4, paint)


def draw_door(screen, door):
    screen.blit(door_sprite(door.width, door.height), (door.x - 4, door.y - 4))


@lru_cache(maxsize=None)
def checkpoint_sprite(width, height, reached):
    """A flag on a pole: grey until the checkpoint is reached, then green."""
    def paint(surface, s):
        pole_x = (width / 2 - 8) * s
        pygame.draw.line(surface, FLAG_POLE, (pole_x, height * s), (pole_x, 4 * s), 4 * s)
        pygame.draw.circle(surface, FLAG_POLE, (pole_x, 4 * s), 4 * s)
        flag = [(pole_x + 2 * s, 8 * s), (pole_x + 26 * s, 17 * s), (pole_x + 2 * s, 26 * s)]
        pygame.draw.polygon(surface, FLAG_ON if reached else FLAG_OFF, flag)
    return smooth_sprite(width, height, paint)


def draw_checkpoint(screen, area, reached):
    screen.blit(checkpoint_sprite(area.width, area.height, reached), area)


# Tiles

@lru_cache(maxsize=None)
def tile_sprite(grass, underside, variant):
    """A dirt tile, with grass on top if nothing is above it and a shaded underside if
    nothing is below it. variant picks the speckles."""
    def paint(surface, s):
        size = TILE * s
        surface.fill(DIRT)
        if underside:
            # Darken the bottom few pixels so floating platforms look solid.
            for y in range(size - 8 * s, size):
                t = (y - (size - 8 * s)) / (8 * s)
                colour = [round(a + (b - a) * t) for a, b in zip(DIRT, DIRT_DARK)]
                pygame.draw.line(surface, colour, (0, y), (size, y))
        rng = random.Random(variant)
        for _ in range(7):
            x, y = rng.uniform(3, TILE - 3) * s, rng.uniform(12 if grass else 3, TILE - 3) * s
            colour = DIRT_LIGHT if rng.random() < 0.5 else DIRT_DARK
            pygame.draw.ellipse(surface, colour, (x, y, rng.uniform(2, 4) * s, rng.uniform(1.5, 3) * s))
        if grass:
            # A grass band with a wavy bottom edge and a light top.
            wave = [(x * s, (9 + 2.5 * math.sin((x + variant * 7) * 0.55)) * s) for x in range(0, TILE + 1)]
            pygame.draw.polygon(surface, GROUND_DARK, [(0, 0)] + [(x, y + 2 * s) for x, y in wave] + [(size, 0)])
            pygame.draw.polygon(surface, GROUND, [(0, 0)] + wave + [(size, 0)])
            pygame.draw.rect(surface, GROUND_LIGHT, (0, 0, size, 3 * s))
    return smooth_sprite(TILE, TILE, paint, alpha=False)


def tile_art(level):
    """(rect, sprite) for every tile in a level, worked out once per level."""
    art = []
    for tile in level.tiles:
        col, row = tile.x // TILE, tile.y // TILE
        grass = (col, row - 1) not in level.solid
        underside = (col, row + 1) not in level.solid
        art.append((tile, tile_sprite(grass, underside, (col * 7 + row * 13) % TILE_VARIANTS)))
    return art


def draw_tiles(screen, art, cam_x, cam_y):
    view = screen.get_rect().move(cam_x, cam_y)
    for tile, sprite in art:
        if view.colliderect(tile):
            screen.blit(sprite, (tile.x - cam_x, tile.y - cam_y))


# On-screen display

@lru_cache(maxsize=None)
def heart_sprite(full, size=12):
    """A heart made of two circles on top of a downward-pointing triangle."""
    box = 2 * size + 6

    def paint(surface, s):
        x, y = box / 2 * s, (size - 1) * s
        r = size / 2 * s
        colour = HEART if full else HEART_EMPTY
        left, right = (x - r, y - r / 2), (x + r, y - r / 2)
        # Outline first, slightly bigger, then the fill on top.
        pygame.draw.circle(surface, HEART_EDGE, left, r + 2 * s)
        pygame.draw.circle(surface, HEART_EDGE, right, r + 2 * s)
        pygame.draw.polygon(surface, HEART_EDGE, [(x - (size + 2) * s, y - r / 4),
                                                  (x + (size + 2) * s, y - r / 4), (x, y + (size + 3) * s)])
        pygame.draw.circle(surface, colour, left, r)
        pygame.draw.circle(surface, colour, right, r)
        pygame.draw.polygon(surface, colour, [(x - size * s, y - r / 4), (x + size * s, y - r / 4),
                                              (x, y + size * s)])
        if full:
            pygame.draw.circle(surface, (250, 140, 150), (left[0] - r / 3, left[1] - r / 3), r / 3)
    return smooth_sprite(box, box, paint)


def draw_health(screen, health):
    for i in range(MAX_HEALTH):
        sprite = heart_sprite(i < health)
        screen.blit(sprite, sprite.get_rect(center=(WIDTH - 30 - (MAX_HEALTH - 1 - i) * 34, 32)))


def draw_hud_panel(screen, rect):
    """A soft, see-through panel behind on-screen text so it stands out from the level."""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (255, 255, 255, 150), panel.get_rect(), border_radius=10)
    screen.blit(panel, rect)


def draw_centered(screen, font, text, y):
    surface = font.render(text, True, TEXT)
    screen.blit(surface, surface.get_rect(center=(WIDTH // 2, y)))
