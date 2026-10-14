import os
import sys

# Run pygame without opening a window or audio device.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402


class Keys(dict):
    """Stand-in for pygame.key.get_pressed(): any key not set counts as not pressed."""

    def __getitem__(self, key):
        return self.get(key, False)


NO_KEYS = Keys()
LEFT = Keys({pygame.K_LEFT: True})
RIGHT = Keys({pygame.K_RIGHT: True})
