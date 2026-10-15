"""The sky, hills and clouds behind the level.

The hills and clouds are layers that scroll slower than the level (parallax), which
makes them look far away. Each layer is drawn once, twice as wide as the screen,
and repeats seamlessly.
"""

import math
import random

import pygame

from .settings import (
    WIDTH,
    HEIGHT,
    SKY_TOP,
    SKY_BOTTOM,
    CLOUD,
    FAR_HILLS,
    NEAR_HILLS,
)

LAYER_WIDTH = 2 * WIDTH
SUPERSAMPLE = 2


def sky_gradient():
    sky = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        colour = [round(a + (b - a) * t) for a, b in zip(SKY_TOP, SKY_BOTTOM)]
        pygame.draw.line(sky, colour, (0, y), (WIDTH, y))
    return sky


def hills(colour, base, waves):
    """A band of hills. waves is (height, repeats across the layer, phase) for each
    sine wave added together; whole repeats make the layer join up seamlessly."""
    s = SUPERSAMPLE
    big = pygame.Surface((LAYER_WIDTH * s, HEIGHT * s), pygame.SRCALPHA)
    points = [(0, HEIGHT * s)]
    for x in range(0, LAYER_WIDTH + 1, 4):
        y = base - sum(h * math.sin(2 * math.pi * k * x / LAYER_WIDTH + p) for h, k, p in waves)
        points.append((x * s, y * s))
    points.append((LAYER_WIDTH * s, HEIGHT * s))
    pygame.draw.polygon(big, colour, points)
    return pygame.transform.smoothscale(big, (LAYER_WIDTH, HEIGHT))


def clouds(count, seed):
    s = SUPERSAMPLE
    big = pygame.Surface((LAYER_WIDTH * s, HEIGHT * s), pygame.SRCALPHA)
    rng = random.Random(seed)
    for i in range(count):
        # Spread evenly with some jitter, away from the layer's edges so it repeats cleanly.
        cx = (i + 0.5) * LAYER_WIDTH / count + rng.uniform(-60, 60)
        cy = rng.uniform(40, 200)
        size = rng.uniform(0.8, 1.4)
        for dx, dy, r in ((-30, 6, 22), (0, -6, 30), (32, 4, 24), (14, 10, 22), (-14, 10, 20)):
            pygame.draw.circle(big, (*CLOUD, 220), ((cx + dx * size) * s, (cy + dy * size) * s), r * size * s)
    return pygame.transform.smoothscale(big, (LAYER_WIDTH, HEIGHT))


class Background:
    def __init__(self):
        self.sky = sky_gradient()
        # (image, how fast it scrolls compared with the level, drift in pixels per frame),
        # furthest first. Only the clouds drift on their own.
        self.layers = [
            (clouds(7, seed=3), 0.08, 0.15),
            (hills(FAR_HILLS, base=380, waves=((40, 3, 0.5), (22, 7, 2.0), (10, 13, 1.0))), 0.18, 0),
            (hills(NEAR_HILLS, base=450, waves=((35, 4, 1.7), (18, 9, 0.3), (8, 17, 2.5))), 0.35, 0),
        ]
        if pygame.display.get_surface() is not None:
            self.sky = self.sky.convert()
            self.layers = [(image.convert_alpha(), speed, drift) for image, speed, drift in self.layers]

    def draw(self, screen, cam_x=0, cam_y=0, lowest_cam_y=0, frame=0):
        """lowest_cam_y is cam_y when the camera is at the bottom of the level; the
        layers sit lower as the camera climbs above that."""
        screen.blit(self.sky, (0, 0))
        for image, speed, drift in self.layers:
            x = -(cam_x * speed + frame * drift) % LAYER_WIDTH
            y = (lowest_cam_y - cam_y) * speed
            screen.blit(image, (x - LAYER_WIDTH, y))
            screen.blit(image, (x, y))
