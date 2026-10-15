"""Sizes, physics, colours and controls used across the game."""

import pygame

# Window
WIDTH, HEIGHT = 960, 540
FPS = 60
TILE = 40
CAMERA_EASE = 0.12  # the camera moves this fraction of the way to the player each frame

# Player physics (pixels per frame)
MOVE_SPEED = 5  # top running speed
ACCELERATION = 0.4  # speed gained per frame while holding a direction
FRICTION = 0.5  # speed lost per frame after letting go
TURN_ACCELERATION = ACCELERATION + FRICTION  # when pressing against the current direction
AIR_CONTROL = 0.6  # acceleration and friction are scaled by this in the air
GRAVITY = 0.8
JUMP_SPEED = 15
MAX_FALL_SPEED = 18

# Colours
SKY = (135, 206, 235)
SKY_TOP = (85, 155, 225)
SKY_BOTTOM = (195, 228, 245)
CLOUD = (255, 255, 255)
FAR_HILLS = (150, 190, 215)
NEAR_HILLS = (115, 175, 135)
GROUND = (90, 160, 70)
GROUND_LIGHT = (130, 195, 95)
GROUND_DARK = (60, 120, 50)
DIRT = (125, 88, 58)
DIRT_LIGHT = (150, 110, 75)
DIRT_DARK = (95, 65, 42)
PLAYER = (220, 60, 60)
PLAYER_EDGE = (160, 35, 35)
EYE_WHITE = (255, 255, 255)
EYE_PUPIL = (20, 20, 20)
MOUTH = (90, 20, 20)
PLAYER_SIZE = 34  # the player is a circle; its collision box is the square around it
DOOR = (150, 90, 40)
DOOR_FRAME = (90, 50, 20)
FLAG_POLE = (110, 110, 120)
FLAG_OFF = (200, 200, 205)  # checkpoint not reached yet
FLAG_ON = (60, 190, 90)  # checkpoint reached
DOOR_KNOB = (240, 200, 60)
TEXT = (30, 30, 30)

COIN = (250, 200, 30)
COIN_EDGE = (190, 130, 10)
COIN_SHINE = (255, 240, 150)
COIN_SIZE = 20

HEART = (225, 40, 60)
HEART_EMPTY = (90, 90, 100)
HEART_EDGE = (60, 20, 30)

# Health
MAX_HEALTH = 3  # hearts at the start of every level
INVINCIBLE_FRAMES = 60  # after a hit the player flashes and can't be hurt for this long

# Enemies
ENEMY = (140, 70, 190)
ENEMY_EDGE = (85, 35, 125)
ENEMY_BROW = (40, 15, 60)
ENEMY_WIDTH, ENEMY_HEIGHT = 32, 26
ENEMY_SPEED = 1.5
STOMP_BOUNCE = 9  # upward speed after landing on an enemy (holding jump gives a full jump)
KNOCKBACK_SPEED = MOVE_SPEED  # sideways speed when hurt by an enemy
KNOCKBACK_HOP = 6  # small upward speed when hurt, to break contact

JUMP_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
