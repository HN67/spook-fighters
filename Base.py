"""Base classes and functionality for Spook Fighters"""

# Import structure libraries
import pygame

# Import local files
import Core
from Core import Dir, Pair

# Base entity class that holds position and size and frames basic methods
class Entity(pygame.sprite.Sprite):
    """Abstract base class for entities"""

    def __init__(self, rect, image=None):
        # Call superclass Sprite init
        pygame.sprite.Sprite.__init__(self)

        # Create image
        if image is None:
            self.image = pygame.Surface((rect.width, rect.height))
        else:
            self.image = image

        # Reference rect
        self.rect = rect

    def update(self, game: "Game"):
        """Updates the entity, in reference to a Game object"""
        raise NotImplementedError(f"{type(self)} does not update")

    def align(self, entity, direction: Dir):
        """Aligns against entity by moving in 'direction'. rect defaults to self rect"""
        # Align based on direction
        if direction == Dir.UP:
            self.rect.top = entity.rect.bottom
        elif direction == Dir.RIGHT:
            self.rect.right = entity.rect.left
        elif direction == Dir.DOWN:
            self.rect.bottom = entity.rect.top
        elif direction == Dir.LEFT:
            self.rect.left = entity.rect.right
        else:
            raise ValueError(f"Invalid direction {direction}")

    def touching(self, entities, direction: Dir):
        """Checks if this Entity is aligned with any entities"""
        # Create ghost
        ghost = Ghost(self)
        ghost.rect = self.rect.copy()

        # Change hitbox of ghost based on direction
        if direction == Dir.UP:
            ghost.rect.height = 1
            ghost.rect.bottom = self.rect.top
        elif direction == Dir.DOWN:
            ghost.rect.height = 1
            ghost.rect.top = self.rect.bottom
        elif direction == Dir.LEFT:
            ghost.rect.width = 1
            ghost.rect.right = self.rect.left
        elif direction == Dir.RIGHT:
            ghost.rect.width = 1
            ghost.rect.left = self.rect.right
        else:
            raise ValueError(f"Invalid direction {direction}")

        # Return whether there was a collision
        return ghost.collisions(entities)

    def collisions(self, entities):
        """Checks if self collides with every entity in group 'entities'"""
        return pygame.sprite.spritecollide(self, entities, False, collided=Core.collides)

    def move(self, dX: int, dY: int, entities):
        """Moves to a new position and takes into account collisions"""

        # Reference current position
        ghost = Ghost(self)

        # Create collision saver
        collided = Pair(False, False)

        # Construct future position
        future = self.rect.copy()

        # Try moving x
        ghost.rect.x += dX
        # Check collisions
        collisions = ghost.collisions(entities)
        # Fix each collision
        while len(collisions) > 0:
            # Remember that a collision happened
            collided.x = True
            # Align ghost based on direction
            if dX > 0:
                ghost.align(collisions[0], Dir.RIGHT)
            else:
                ghost.align(collisions[0], Dir.LEFT)
            # Recheck for collisions
            collisions = ghost.collisions(entities)
        # Save rect x
        future.x = ghost.rect.x

        # Reset ghost
        ghost = Ghost(self)

        # Check Y movement
        ghost.rect.y += dY
        # Check collisions
        collisions = ghost.collisions(entities)
        # Fix each collision
        while len(collisions) > 0:
            # Remember that a collision happened
            collided.y = True
            # Align ghost based on direction
            if dY > 0:
                ghost.align(collisions[0], Dir.DOWN)
            else:
                ghost.align(collisions[0], Dir.UP)
            # Recheck for collisions
            collisions = ghost.collisions(entities)
        # Save rect y
        future.y = ghost.rect.y

        # Check corner case (literally when collision is only diagonal)
        # Put ghost at future
        ghost = Ghost(self)
        ghost.rect = future

        # Check collisions
        collisions = ghost.collisions(entities)
        # Fix each collision
        while len(collisions) > 0:
            # Remember that a collision (corner) happened
            collided.x = True
            collided.y = True
            # Align ghost based on direction
            # X Align
            if dX > 0:
                ghost.align(collisions[0], Dir.RIGHT)
            else:
                ghost.align(collisions[0], Dir.LEFT)
            # Y align
            if dY > 0:
                ghost.align(collisions[0], Dir.DOWN)
            else:
                ghost.align(collisions[0], Dir.UP)
            # Recheck for collisions
            collisions = ghost.collisions(entities)

        # Move ghost to self
        self.rect = ghost.rect

        # Return the collided pair
        return collided

# Ghost Entity Class (for collision detection)
class Ghost(Entity):
    """Represents a Ghost entity that is an alias of another Entity for collisions"""

    def __init__(self, alias: Entity):
        super().__init__(alias.rect.copy())

        # Reference alias
        self.alias = alias

    def collisions(self, entities):
        """Checks for collisions in SpriteGroup, not colliding with self or alias"""
        return pygame.sprite.spritecollide(self, entities, False, collided=self._collides)

    def _collides(self, this, other):
        """For use with the collisions method"""
        return (
            (this is not other) # Not colliding with the ghost somehow
            and (other is not self.alias) # Will not collide with the alias
            and (pygame.sprite.collide_rect(this, other)) # Actual collision detection
        )

    def update(self, game: "Game"):
        """Updates the entity"""
        raise NotImplementedError(f"{type(self)} does not update")

# Controller class that updates but doesnt really exist in the game
# in terms of collions and visual. Does have a position tho
class Controller(pygame.sprite.Sprite):
    """Abstract class for creating controllers"""

    def __init__(self, rect):
        # Call sprite constructor
        super().__init__()

        # Reference rect (anchor point for the controller to create stuff)
        self.rect = rect

    def update(self, game: "Game"):
        """Updates the entity"""
        raise NotImplementedError(f"{type(self)} does not update")

# Label class for display numbers and text
# TODO make the Label able to be linked to a variable
# either a game attribute, or maybe make wrapper objects so references can be passed around
# Wrapper variables would be a pain, but maybe the `game` can hold wrappers and update them itself?
# Or actually the entities (e.g. player) should probably expose the wrappers themselves,
# and update them from internal primitives every update. The labels should be updated last
class Label(pygame.sprite.Sprite):
    """Class for creating text labels"""

    def __init__(self, rect: pygame.Rect, variable: Core.Variable, 
                 height: int, color: Core.Color, bgColor: Core.Color):
        
        # Call sprite constructor
        super().__init__()

        # Reference rect
        self.rect = rect

        # Reference colors
        self.color = color
        self.bgColor = bgColor

        # Reference variable
        self.text = variable

        # Setup text stuff
        # Create font
        self.font = pygame.font.SysFont("Courier New", height)
        # Render
        self._render()

    def _render(self):
        """Renders the new text onto internal image"""
        self.image = self.font.render(str(self.text.value), True, self.color, self.bgColor)

    def update(self, game: "Game"):
        """Updates the entity"""

        # Redraw the text
        self._render()
