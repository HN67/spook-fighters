"""Core functions and behaviors for Spook Fighters Py"""

# Import core libraries
from dataclasses import dataclass
from enum import Enum
import typing

# Import structure libraries
import pygame

# Define basic classes
@dataclass
class Pair:
    """Pair class collecting an x and y"""

    x: typing.Any
    y: typing.Any


class Dir(Enum):
    """Relative direction enum"""
    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)

class Color:
    """Color RGB constants"""
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (127, 127, 127)

    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    YELLOW = (255, 255, 0)
    ORANGE = (255, 125, 0)
    PURPLE = (255, 0, 255)

    DARKGREEN = (0, 127, 0)

    SKYBLUE = (0, 200, 200)

class AttributeSet:
    """Object that holds information on a variety of attributes\n
    Each keyword argument passed is set as an attribute"""

    def __init__(self, **attrs):
        # Create an attribute for each passed in
        for attribute in attrs:
            setattr(self, attribute, attrs[attribute])

@dataclass
class PlayerAttributes:
    """Stores various data about the behavior of the player"""

    speed: int
    jump: int
    fastfall: int
    gravity: int

    airJumps: int
    slide: int
    wallJumpFreeze: int

    # Collisions at a speed greater than this will stun
    ySpeedStun: int
    xSpeedStun: int

@dataclass
class Keyset:
    """Keyset representing the character mappings for a player object"""

    LEFT: int
    RIGHT: int
    UP: int
    DOWN: int
    ACTION: int

def collides(spriteA, spriteB):
    """Returns true if sprites arent the same, and if collide_rect returns true"""
    return (spriteA is not spriteB) and (pygame.sprite.collide_rect(spriteA, spriteB))

@dataclass
class Vector:
    """Represents a vertical x horizontal vector"""

    x: int
    y: int

    def xy_ratio(self):
        """Returns the ratio of x to y"""
        return self.x/self.y

    def yx_ratio(self):
        """Returns the ratio of y to x"""
        return 1/self.xy_ratio()
