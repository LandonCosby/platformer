import pygame

# Window
WIDTH, HEIGHT = 960, 540
FPS = 60
TILE = 40

# Player physics (pixels per frame)
MOVE_SPEED = 5
GRAVITY = 0.8
JUMP_SPEED = 15
MAX_FALL_SPEED = 18

# Colours
SKY = (135, 206, 235)
GROUND = (90, 160, 70)
DIRT = (120, 85, 55)
PLAYER = (220, 60, 60)
PLAYER_EDGE = (160, 35, 35)
EYE_WHITE = (255, 255, 255)
EYE_PUPIL = (20, 20, 20)
MOUTH = (90, 20, 20)
PLAYER_SIZE = 34  # the player is a circle; its collision box is the square around it
DOOR = (150, 90, 40)
DOOR_FRAME = (90, 50, 20)
DOOR_KNOB = (240, 200, 60)
TEXT = (30, 30, 30)

COIN = (250, 200, 30)
COIN_EDGE = (190, 130, 10)
COIN_SHINE = (255, 240, 150)
COIN_SIZE = 20

# Level layouts: "#" is a solid tile, "P" is the player start, "D" is the door
# to the next level (it is two tiles tall, drawn upward from its cell), "C" is a coin,
# "." is empty.
LEVELS = [
    # Level 1: a couple of gaps to jump.
    # Coins: over the first pit at the top of a jump, on a ledge back from the floating
    # platform, and in a tunnel under the ground reached through a hole.
    [
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        "........................................",
        ".................C......................",
        ".........C.......##.....................",
        "........................................",
        ".....................###................",
        ".P....................................D.",
        "########...#########......####.#########",
        "########...#########......#C...#########",
        "########...#########......##############",
    ],
    # Level 2: hop across floating platforms over a long pit.
    # Coins: on a ledge back over the start, and two high above the highest platform.
    [
        "..................................................",
        "....................................C.............",
        "................................C.................",
        "..................................................",
        "..................................................",
        "..C............................###................",
        "..##.........###.....###..........................",
        ".........................###...........###........",
        "........###.......................................",
        ".P.............................................D..",
        "######.....................................#######",
        "######.....................................#######",
        "######.....................................#######",
    ],
    # Level 3: climb up to the door.
    # Coins: off-screen at the far right of the floor, top-left above the left ledge,
    # and at the very top between the two highest platforms.
    [
        "................C.............",
        "..............................",
        "..............................",
        "............###...###.........",
        ".C..........................D.",
        "........................######",
        "......####....................",
        "..............................",
        ".###..........................",
        "..............................",
        "......###.....................",
        "..............................",
        "...........###................",
        "..............................",
        "......###.....................",
        "..............................",
        ".P..........................C.",
        "##############################",
        "##############################",
        "##############################",
    ],
]


class Player:
    def __init__(self, x, y):
        self.spawn = (x, y)
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing = 1  # 1 is right, -1 is left

    def respawn(self):
        self.rect.topleft = self.spawn
        self.vel_x = self.vel_y = 0

    def update(self, keys, tiles):
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x -= MOVE_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x += MOVE_SPEED
        if self.vel_x:
            self.facing = 1 if self.vel_x > 0 else -1

        # Move and resolve collisions one axis at a time.
        self.rect.x += self.vel_x
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel_x > 0:
                    self.rect.right = tile.left
                elif self.vel_x < 0:
                    self.rect.left = tile.right

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

    def jump(self):
        if self.on_ground:
            self.vel_y = -JUMP_SPEED

    def cut_jump(self):
        # Releasing jump early gives a shorter hop.
        if self.vel_y < -JUMP_SPEED / 3:
            self.vel_y = -JUMP_SPEED / 3


class Level:
    def __init__(self, layout):
        self.tiles = []
        self.start = (TILE, TILE)
        self.door = None
        self.coins = []
        for row, line in enumerate(layout):
            for col, char in enumerate(line):
                if char == "#":
                    self.tiles.append(pygame.Rect(col * TILE, row * TILE, TILE, TILE))
                elif char == "P":
                    self.start = (col * TILE, row * TILE)
                elif char == "D":
                    self.door = pygame.Rect(col * TILE + 6, (row - 1) * TILE, TILE - 12, 2 * TILE)
                elif char == "C":
                    coin = pygame.Rect(0, 0, COIN_SIZE, COIN_SIZE)
                    coin.center = (col * TILE + TILE // 2, row * TILE + TILE // 2)
                    self.coins.append(coin)
        self.width = max(len(line) for line in layout) * TILE
        self.height = len(layout) * TILE


class Game:
    """Game state and rules, kept separate from input handling and drawing."""

    def __init__(self, levels=LEVELS):
        self.levels = levels
        self.total_coins = sum("".join(layout).count("C") for layout in levels)
        self.restart()

    def restart(self):
        self.won = False
        self.coins_collected = 0
        self.start_level(0)

    def start_level(self, index):
        self.level_index = index
        self.level = Level(self.levels[index])
        self.player = Player(*self.level.start)

    def jump_pressed(self):
        self.player.jump()

    def jump_released(self):
        self.player.cut_jump()

    def update(self, keys):
        if self.won:
            return
        player, level = self.player, self.level
        player.update(keys, level.tiles)

        # Keep the player inside the level horizontally; falling off the bottom respawns.
        player.rect.left = max(player.rect.left, 0)
        player.rect.right = min(player.rect.right, level.width)
        if player.rect.top > level.height:
            player.respawn()

        # Collected coins stay collected, even if the player falls and respawns.
        for coin in [c for c in level.coins if player.rect.colliderect(c)]:
            level.coins.remove(coin)
            self.coins_collected += 1

        # Touching the door goes to the next level, or wins after the last one.
        if level.door and player.rect.colliderect(level.door):
            if self.level_index + 1 < len(self.levels):
                self.start_level(self.level_index + 1)
            else:
                self.won = True


def draw_door(screen, door):
    pygame.draw.rect(screen, DOOR_FRAME, door.inflate(8, 4).move(0, -2), border_radius=4)
    pygame.draw.rect(screen, DOOR, door, border_radius=3)
    pygame.draw.circle(screen, DOOR_KNOB, (door.right - 7, door.centery + 4), 3)


def draw_player(screen, rect, facing):
    cx, cy = rect.center
    radius = rect.width // 2
    pygame.draw.circle(screen, PLAYER_EDGE, (cx, cy), radius)
    pygame.draw.circle(screen, PLAYER, (cx, cy), radius - 2)

    # Eyes look the way the player is facing.
    look = 2 * facing
    for side in (-1, 1):
        eye = (cx + side * 6 + facing * 2, cy - 4)
        pygame.draw.circle(screen, EYE_WHITE, eye, 5)
        pygame.draw.circle(screen, EYE_PUPIL, (eye[0] + look, eye[1]), 2)

    # Smile: a short curve below the eyes.
    # Screen y grows downwards, so the middle of the curve has the largest y.
    mx, my = cx + facing * 2, cy + 4
    smile = [(mx + x, my + (49 - x * x) // 12) for x in range(-7, 8)]
    pygame.draw.lines(screen, MOUTH, False, smile, 2)


def draw_coin(screen, center, radius=COIN_SIZE // 2):
    pygame.draw.circle(screen, COIN_EDGE, center, radius)
    pygame.draw.circle(screen, COIN, center, radius - 2)
    pygame.draw.circle(screen, COIN_SHINE, (center[0] - radius // 3, center[1] - radius // 3), radius // 4)


def draw_centered(screen, font, text, y):
    surface = font.render(text, True, TEXT)
    screen.blit(surface, surface.get_rect(center=(WIDTH // 2, y)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Platformer")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 80)
    jump_keys = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
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
                elif event.key in jump_keys:
                    game.jump_pressed()
            elif event.type == pygame.KEYUP and event.key in jump_keys:
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
        for coin in level.coins:
            draw_coin(screen, coin.move(-cam_x, -cam_y).center)
        draw_player(screen, player.rect.move(-cam_x, -cam_y), player.facing)

        label = font.render(f"Level {game.level_index + 1}/{len(game.levels)}", True, TEXT)
        screen.blit(label, (16, 12))
        draw_coin(screen, (26, 56))
        coins = font.render(f"{game.coins_collected}/{game.total_coins}", True, TEXT)
        screen.blit(coins, (44, 44))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
