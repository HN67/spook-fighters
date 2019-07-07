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
    NONE = (0, 0)

    @classmethod
    def opposite(cls, direction):
        """Returns the opposite direction"""
        return {
            cls.UP: cls.DOWN, cls.DOWN: cls.UP,
            cls.LEFT: cls.RIGHT, cls.RIGHT: cls.LEFT,
            cls.NONE: cls.NONE
        }[direction]

    def __neg__(self):
        """Negates the direction by calling .opposite(self)"""
        return type(self).opposite(self)

    @classmethod
    def direction_x(cls, value, default=None):
        """Returns a direction based on sign"""
        if value > 0:
            return cls.RIGHT
        elif value < 0:
            return cls.LEFT
        elif default is None:
            return cls.NONE
        else:
            return default

    @classmethod
    def direction_y(cls, value, default=None):
        """Returns a direction based on sign"""
        if value > 0:
            return cls.DOWN
        elif value < 0:
            return cls.UP
        elif default is None:
            return cls.NONE
        else:
            return default

class Color:
    """Color RGB constants"""

    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    TRANSPARENT = (0, 0, 0, 0)

    GRAY = (127, 127, 127)
    LIGHTGRAY = (63, 63, 63)

    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    YELLOW = (255, 255, 0)
    ORANGE = (255, 125, 0)
    PURPLE = (255, 0, 255)

    DARKGREEN = (0, 127, 0)

    SKYBLUE = (0, 200, 200)

    @staticmethod
    def scale(color: "Color", factor: float):
        """Returns a copy of the color with each component scaled by factor"""
        return tuple(component*factor for component in color)

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

    speed: int # Horizontal acceleration
    maxSpeed: int # Maximum horizontal speed
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
    ATTACK: int

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

@dataclass
class Variable:
    """Stores a variable, can be used to pass immutables by reference"""

    value: typing.Any

@dataclass
class HitState:
    """Holds the fields required for player.hit()"""

    damage: int
    force: float
    varForce: float
    vector: Vector

    def mapping(self):
        """Returns the fields as a dictionary, for splatting"""
        return {
            "damage": self.damage, "force": self.force,
            "varForce": self.varForce, "vector": self.vector
        }

    def copy(self):
        """Returns a deepish copy, assuming all parameters are normal types"""
        return HitState(
            self.damage, self.force, self.varForce,
            Vector(self.vector.x, self.vector.y)
        )

# Main game class (very unrefined)
class Screen:
    """Main game class for running a game of Spook Fighters"""

    def __init__(self, screen: pygame.Surface, rect: pygame.Rect, color: Color):

        ## Main fundamental setup

        # Reference the screen to be drawn on
        self.screen = screen

        # Reference the rect used for blit location and dimensions
        self.rect = rect

        # Reference background color
        self.color = color

        # Create game surface
        self.surface = pygame.surface.Surface(rect.size)
        
        # Contined sprite group
        self.sprites = pygame.sprite.Group()

        # Events and keysHeld variables
        self.events = None
        self.keysHeld = None
    
    def gather(self, events):
        """Gathers pygame events and keypresses into object attributes"""
        # Collect events
        self.events = events.copy()

        # Handle events, mostly mouse relativizing
        for event in self.events:

            # Change the pos of mouse events to be relative
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                event.pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)

        # Collect keys held down
        self.keysHeld = pygame.key.get_pressed()

    def update(self, events):
        """Performs a tick of update logic"""

        # Gather events
        self.gather(events)

        # Update contained sprites
        self.sprites.update(self)

    def draw(self):
        """Draws the screens surface onto defined higher screen"""

        # Draw all sprites onto base colors
        self.surface.fill(self.color)
        self.sprites.draw(self.surface)

        # Blit onto the screen
        self.screen.blit(self.surface, (self.rect.x, self.rect.y))

    def get_events(self):
        """Returns the PyGame events collected last update"""
        return self.events

    def keys_held(self):
        """Returns the keys held as of last update"""
        return self.keysHeld

    def add_sprites(self, *sprites):
        """Adds sprites to the screen"""
        self.sprites.add(*sprites)
