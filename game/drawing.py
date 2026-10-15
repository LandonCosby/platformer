"""Drawing the player, enemies, coins, door and on-screen display."""

import math

import pygame

from .settings import (
    WIDTH,
    PLAYER,
    PLAYER_EDGE,
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
    FLAG_POLE,
    FLAG_OFF,
    FLAG_ON,
)


def draw_checkpoint(screen, area, reached):
    """A flag on a pole: grey until the checkpoint is reached, then green."""
    pole_x = area.centerx - 8
    pygame.draw.line(screen, FLAG_POLE, (pole_x, area.bottom), (pole_x, area.top + 4), 4)
    pygame.draw.circle(screen, FLAG_POLE, (pole_x, area.top + 4), 4)
    flag = [(pole_x + 2, area.top + 8), (pole_x + 26, area.top + 17), (pole_x + 2, area.top + 26)]
    pygame.draw.polygon(screen, FLAG_ON if reached else FLAG_OFF, flag)


def draw_door(screen, door):
    pygame.draw.rect(screen, DOOR_FRAME, door.inflate(8, 4).move(0, -2), border_radius=4)
    pygame.draw.rect(screen, DOOR, door, border_radius=3)
    pygame.draw.circle(screen, DOOR_KNOB, (door.right - 7, door.centery + 4), 3)


def draw_player(screen, rect, facing, angle=0.0):
    cx, cy = rect.center
    radius = rect.width // 2
    pygame.draw.circle(screen, PLAYER_EDGE, (cx, cy), radius)
    pygame.draw.circle(screen, PLAYER, (cx, cy), radius - 2)

    # The face is laid out upright around the centre, then turned by the roll angle.
    # With screen y pointing down, a positive angle turns it clockwise.
    cos, sin = math.cos(angle), math.sin(angle)

    def turned(x, y):
        return (cx + x * cos - y * sin, cy + x * sin + y * cos)

    # Eyes look the way the player is facing.
    for side in (-1, 1):
        ex, ey = side * 6 + facing * 2, -4
        pygame.draw.circle(screen, EYE_WHITE, turned(ex, ey), 5)
        pygame.draw.circle(screen, EYE_PUPIL, turned(ex + 2 * facing, ey), 2)

    # Smile: a short curve below the eyes.
    # Screen y grows downwards, so the middle of the curve has the largest y.
    smile = [turned(facing * 2 + x, 4 + (49 - x * x) / 12) for x in range(-7, 8)]
    pygame.draw.lines(screen, MOUTH, False, smile, 2)


def draw_enemy(screen, rect, direction):
    """A purple blob: rounded on top, flat on the bottom, with angry eyes."""
    pygame.draw.rect(screen, ENEMY_EDGE, rect, border_top_left_radius=16,
                     border_top_right_radius=16, border_bottom_left_radius=4, border_bottom_right_radius=4)
    pygame.draw.rect(screen, ENEMY, rect.inflate(-4, -4), border_top_left_radius=14,
                     border_top_right_radius=14, border_bottom_left_radius=3, border_bottom_right_radius=3)
    cx = rect.centerx + direction * 2
    eye_y = rect.top + 11
    for side in (-1, 1):
        eye = (cx + side * 6, eye_y)
        pygame.draw.circle(screen, EYE_WHITE, eye, 4)
        pygame.draw.circle(screen, EYE_PUPIL, (eye[0] + direction * 1, eye[1] + 1), 2)
        # Eyebrows slope down towards the middle.
        outer, inner = (eye[0] + side * 5, eye[1] - 7), (eye[0] - side * 2, eye[1] - 4)
        pygame.draw.line(screen, ENEMY_BROW, outer, inner, 2)


def draw_coin(screen, center, radius=COIN_SIZE // 2):
    pygame.draw.circle(screen, COIN_EDGE, center, radius)
    pygame.draw.circle(screen, COIN, center, radius - 2)
    pygame.draw.circle(screen, COIN_SHINE, (center[0] - radius // 3, center[1] - radius // 3), radius // 4)


def draw_heart(screen, center, full, size=12):
    """A heart made of two circles on top of a downward-pointing triangle."""
    x, y = center
    r = size // 2
    colour = HEART if full else HEART_EMPTY
    left, right = (x - r, y - r // 2), (x + r, y - r // 2)
    point = [(x - size, y - r // 4), (x + size, y - r // 4), (x, y + size)]
    # Outline first, slightly bigger, then the fill on top.
    pygame.draw.circle(screen, HEART_EDGE, left, r + 2)
    pygame.draw.circle(screen, HEART_EDGE, right, r + 2)
    pygame.draw.polygon(screen, HEART_EDGE, [(x - size - 2, y - r // 4), (x + size + 2, y - r // 4), (x, y + size + 3)])
    pygame.draw.circle(screen, colour, left, r)
    pygame.draw.circle(screen, colour, right, r)
    pygame.draw.polygon(screen, colour, point)


def draw_health(screen, health):
    for i in range(MAX_HEALTH):
        draw_heart(screen, (WIDTH - 30 - (MAX_HEALTH - 1 - i) * 34, 30), full=i < health)


def draw_centered(screen, font, text, y):
    surface = font.render(text, True, TEXT)
    screen.blit(surface, surface.get_rect(center=(WIDTH // 2, y)))
