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

The tests check movement and physics, level progression and coins, and use a solver to confirm every level can be finished and every coin can be reached.

## Editing levels

Levels are text grids in `LEVELS` in `main.py`: `#` is solid ground, `P` the player start, `D` the door, `C` a coin and `.` empty space.
