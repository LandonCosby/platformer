"""Checks whether a level's door and coins can be reached, using a graph of platforms.

1. Simulate one jump with the real player physics to get the jump arc: how far
   sideways the player travels for every height it reaches.
2. Find every platform surface: a run of solid tiles with empty space above.
3. Link two surfaces when the jump arc can carry the player from the edge of one
   onto the other.
4. Search the graph from the start. The door or a coin is reachable if the jump
   arc can touch it from a reachable surface.

Walls and ceilings in the way of a jump are ignored, so this can say a jump is
possible when something actually blocks it.
"""
from collections import deque
from functools import lru_cache
from typing import NamedTuple

import pygame

from game.level import Level
from game.player import Player
from game.settings import MOVE_SPEED, PLAYER_SIZE, TILE


class Surface(NamedTuple):
    left: int  # pixels
    right: int
    top: int


class _HoldRight(dict):
    def __getitem__(self, key):
        return key == pygame.K_RIGHT


def find_surfaces(layout):
    solid = {(r, c) for r, line in enumerate(layout) for c, ch in enumerate(line) if ch == "#"}
    surfaces = []
    for r, line in enumerate(layout):
        start = None
        for c in range(len(line) + 1):
            standable = (r, c) in solid and (r - 1, c) not in solid
            if standable and start is None:
                start = c
            elif not standable and start is not None:
                surfaces.append(Surface(start * TILE, c * TILE, r * TILE))
                start = None
    return surfaces


def runway_speed(surface):
    """Fastest speed the player can reach running from one end of the surface to the other."""
    player = Player(0, 0)
    player.on_ground = True
    runway = surface.right - surface.left - PLAYER_SIZE
    distance = 0.0
    while player.vel_x < MOVE_SPEED:
        before = player.vel_x
        player.accelerate(1)
        if distance + player.vel_x > runway:
            player.vel_x = before
            break
        distance += player.vel_x
    return player.vel_x


@lru_cache(maxsize=None)
def jump_arc(start_speed):
    """(sideways distance, feet height above take-off) for each frame of a full jump,
    taken at start_speed while holding the direction of travel."""
    player = Player(0, 0)
    player.on_ground = True
    player.vel_x = start_speed
    player.jump()
    arc = []
    for _ in range(400):
        player.update(_HoldRight(), [])
        arc.append((player.x, -player.rect.y))
        if player.rect.y > 3000:
            break
    return tuple(arc)


def reach(arc, height):
    """Furthest sideways distance at which the player's feet are still at or above `height`.
    None if the jump never gets that high. Any shorter distance works too, by holding back."""
    distances = [x for x, h in arc if h >= height]
    return max(distances) if distances else None


def gap_between(a_left, a_right, b_left, b_right):
    """Horizontal gap between two spans in pixels (negative when they overlap)."""
    return max(b_left - a_right, a_left - b_right)


def can_jump(a, b):
    """Whether the player can get from surface a onto surface b."""
    # The player can stand with all but a pixel hanging off the edge, and only needs
    # to land a pixel onto b, so it travels the gap minus nearly its own width.
    needed = gap_between(a.left, a.right, b.left, b.right) - (PLAYER_SIZE - 2)
    distance = reach(jump_arc(runway_speed(a)), a.top - b.top)
    return distance is not None and distance >= needed


def can_touch(a, rect):
    """Whether the player can touch rect (a coin or door) by jumping from surface a."""
    needed = gap_between(a.left, a.right, rect.left, rect.right) - (PLAYER_SIZE - 1)
    # The player's top is PLAYER_SIZE above its feet, so its feet need only get that
    # close to the bottom of the rect.
    distance = reach(jump_arc(runway_speed(a)), a.top - rect.bottom - PLAYER_SIZE + 1)
    return distance is not None and distance >= needed


def start_surface(level, surfaces):
    """The surface the player lands on when the level starts."""
    x, y = level.start
    below = [s for s in surfaces
             if s.top >= y + PLAYER_SIZE and s.left < x + PLAYER_SIZE and s.right > x]
    return min(below, key=lambda s: s.top) if below else None


def reachable_surfaces(layout):
    level = Level(layout)
    surfaces = find_surfaces(layout)
    start = start_surface(level, surfaces)
    if start is None:
        return level, set()
    seen, queue = {start}, deque([start])
    while queue:
        a = queue.popleft()
        for b in surfaces:
            if b not in seen and can_jump(a, b):
                seen.add(b)
                queue.append(b)
    return level, seen


def can_reach_door(layout):
    level, surfaces = reachable_surfaces(layout)
    return any(can_touch(s, level.door) for s in surfaces)


def unreachable_coins(layout):
    """Centres of the coins that cannot be reached from the start."""
    level, surfaces = reachable_surfaces(layout)
    return [coin.center for coin in level.coins
            if not any(can_touch(s, coin) for s in surfaces)]
