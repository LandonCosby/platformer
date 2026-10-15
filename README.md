# Platformer

A simple 2D platformer built with pygame: three levels, a door to the next level, and hidden coins to find.

## Setup

```
python -m pip install -r requirements.txt
```

## Play

```
python main.py
```

| Action | Keys |
|---|---|
| Move | ← → or A / D |
| Jump | Space, ↑ or W (hold to jump higher) |
| Quit | Esc |

## Tests

```
python -m pytest tests
```

The tests check movement and physics, health and enemies, level progression and coins, and use a graph of the platforms to confirm every level can be finished and every coin can be reached.

## Code layout

`main.py` starts the game. The game itself is in the `game` package:

| File | What's in it |
|---|---|
| `settings.py` | Window size, physics, health, enemy settings, colours and controls |
| `levels.py` | The level layouts |
| `level.py` | `Level`: turns a layout into tiles, coins, enemies and a door |
| `player.py` | `Player`: movement, acceleration, jumping and rolling |
| `enemy.py` | `Enemy`: patrols a platform |
| `game.py` | `Game`: the rules for coins, the door, health and enemies |
| `drawing.py` | Drawing the player, enemies, coins, door, tiles, hearts and text |
| `background.py` | The sky gradient and the scrolling hills and clouds |
| `app.py` | The window, input, camera and main loop |

## Editing levels

Levels are text grids in `LEVELS` in `game/levels.py`: `#` is solid ground, `P` the player start, `D` the door, `C` a coin, `E` an enemy, `K` the checkpoint flag and `.` empty space.
