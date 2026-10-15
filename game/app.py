"""The window, input, camera and main loop."""

import pygame

from .settings import (
    WIDTH,
    HEIGHT,
    FPS,
    SKY,
    GROUND,
    DIRT,
    TEXT,
    JUMP_KEYS,
)
from .drawing import (
    draw_centered,
    draw_checkpoint,
    draw_coin,
    draw_door,
    draw_enemy,
    draw_health,
    draw_player,
)
from .game import Game


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Platformer")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 80)
    game = Game()

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

        if game.won:
            screen.fill(SKY)
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

        # Camera follows the player, clamped to the level edges.
        cam_x = min(max(player.rect.centerx - WIDTH // 2, 0), level.width - WIDTH)
        cam_y = min(max(player.rect.centery - HEIGHT // 2, 0), level.height - HEIGHT)

        screen.fill(SKY)
        for tile in level.tiles:
            r = tile.move(-cam_x, -cam_y)
            pygame.draw.rect(screen, DIRT, r)
            pygame.draw.rect(screen, GROUND, (r.x, r.y, r.w, 8))
        if level.door:
            draw_door(screen, level.door.move(-cam_x, -cam_y))
        if level.checkpoint:
            draw_checkpoint(screen, level.checkpoint.move(-cam_x, -cam_y), game.checkpoint_reached)
        for coin in level.coins:
            draw_coin(screen, coin.move(-cam_x, -cam_y).center)
        for enemy in level.enemies:
            draw_enemy(screen, enemy.rect.move(-cam_x, -cam_y), enemy.direction)
        # Flash while invincible: hidden for 5 frames out of every 10.
        if not game.invincible or (game.invincible // 5) % 2 == 0:
            draw_player(screen, player.rect.move(-cam_x, -cam_y), player.facing, player.angle)

        label = font.render(f"Level {game.level_index + 1}/{len(game.levels)}", True, TEXT)
        screen.blit(label, (16, 12))
        draw_coin(screen, (26, 56))
        coins = font.render(f"{game.coins_collected}/{game.total_coins}", True, TEXT)
        screen.blit(coins, (44, 44))
        draw_health(screen, game.health)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
