"""The window, input, camera and main loop."""

import pygame

from .settings import (
    WIDTH,
    HEIGHT,
    FPS,
    CAMERA_EASE,
    TEXT,
    JUMP_KEYS,
)
from .background import Background
from .drawing import (
    draw_centered,
    draw_checkpoint,
    draw_coin,
    draw_door,
    draw_enemy,
    draw_health,
    draw_hud_panel,
    draw_player,
    draw_tiles,
    tile_art,
)
from .game import Game


def open_window():
    # vsync stops tearing while scrolling. pygame only offers it with SCALED windows,
    # and not on every system, so fall back to a plain window without it.
    try:
        return pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED, vsync=1)
    except pygame.error:
        return pygame.display.set_mode((WIDTH, HEIGHT))


def camera_target(level, player):
    """Where the camera wants to be: centred on the player, kept inside the level.
    Also returns the lowest the camera can go, which the background needs."""
    lowest = level.height - HEIGHT
    x = min(max(player.rect.centerx - WIDTH // 2, 0), level.width - WIDTH)
    y = min(max(player.rect.centery - HEIGHT // 2, 0), lowest)
    return x, y, lowest


def main():
    pygame.init()
    screen = open_window()
    pygame.display.set_caption("Platformer")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 80)
    background = Background()
    game = Game()
    shown_level = None  # the level the camera and tile art were last set up for
    frame = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game.won and event.key == pygame.K_RETURN:
                    game.restart()
                elif event.key in JUMP_KEYS:
                    game.jump_pressed()
            elif event.type == pygame.KEYUP and event.key in JUMP_KEYS:
                game.jump_released()

        frame += 1
        if game.won:
            background.draw(screen, frame=frame)
            draw_centered(screen, big_font, "You win!", HEIGHT // 2 - 50)
            draw_centered(screen, font, f"Coins collected: {game.coins_collected}/{game.total_coins}",
                          HEIGHT // 2 + 10)
            draw_centered(screen, font, "Press Enter to play again or Esc to quit", HEIGHT // 2 + 50)
            pygame.display.flip()
            clock.tick(FPS)
            continue

        game.update(pygame.key.get_pressed())
        if game.won:
            continue
        level, player = game.level, game.player

        # The camera eases towards the player rather than snapping, which looks
        # smoother. On a new or restarted level it jumps straight there.
        target_x, target_y, lowest_cam_y = camera_target(level, player)
        if level is not shown_level:
            shown_level, tiles = level, tile_art(level)
            cam_x, cam_y = target_x, target_y
        else:
            cam_x += (target_x - cam_x) * CAMERA_EASE
            cam_y += (target_y - cam_y) * CAMERA_EASE

        background.draw(screen, cam_x, cam_y, lowest_cam_y, frame)
        # Everything in the level is drawn at whole pixels, so it doesn't shimmer.
        ox, oy = round(cam_x), round(cam_y)
        draw_tiles(screen, tiles, ox, oy)
        if level.door:
            draw_door(screen, level.door.move(-ox, -oy))
        if level.checkpoint:
            draw_checkpoint(screen, level.checkpoint.move(-ox, -oy), game.checkpoint_reached)
        for coin in level.coins:
            draw_coin(screen, coin.move(-ox, -oy).center)
        for enemy in level.enemies:
            draw_enemy(screen, enemy.rect.move(-ox, -oy), enemy.direction)
        # Flash while invincible: hidden for 5 frames out of every 10.
        if not game.invincible or (game.invincible // 5) % 2 == 0:
            draw_player(screen, player.rect.move(-ox, -oy), player.facing, player.angle)

        draw_hud_panel(screen, pygame.Rect(6, 4, 128, 72))
        draw_hud_panel(screen, pygame.Rect(WIDTH - 118, 6, 112, 52))
        label = font.render(f"Level {game.level_index + 1}/{len(game.levels)}", True, TEXT)
        screen.blit(label, (16, 12))
        draw_coin(screen, (26, 56))
        coins = font.render(f"{game.coins_collected}/{game.total_coins}", True, TEXT)
        screen.blit(coins, (44, 44))
        draw_health(screen, game.health)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
