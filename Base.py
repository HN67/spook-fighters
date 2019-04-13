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

# Attack class that handles freeze and references
# Could be used manually to add projectiles to it, but is also
# Used a lot in the Mechanics file to implement custom attack
class Attack(Controller):
    """Abstract Base class for attack controllers that manage projectiles"""

    def __init__(self, player: "Player", cooldown: int, lifeSpan: int):
        super().__init__(player.rect.copy())

        # Reference player
        self.player = player

        # Apply cooldown
        self.player.cooldown = cooldown

        # Init age for tick count
        self.tick = 0
        self.lifeSpan = lifeSpan

        # Dictionary of lists for holding projectiles
        self.projectileBuffer = {}

        # Group of active projectiles
        self.projectiles = pygame.sprite.Group()

    def add_projectile(self, projectile, birthTick: int):
        """Adds a projectile to the Attack to monitor\n
        The projectile will be added to a 'Game' on the birth tick
        """
        # Add or create the projectile to a list in the projBuffer
        if birthTick in self.projectileBuffer:
            self.projectileBuffer[birthTick].add(projectile)
        else:
            self.projectileBuffer[birthTick] = [projectile]

    def update(self, game: "Game"):
        """Updates the entity"""
        self.tick += 1

        # Checks for death. note: This will still finish remaining code for this update
        if self.tick == self.lifeSpan:
            self.kill()

        # Check if projectiles should be created
        if self.tick in self.projectileBuffer:
            # Add the projectiles to the game
            game.add_projectiles(self.projectileBuffer[self.tick])
            # Remove that set from the dict
            del self.projectileBuffer[self.tick]

# Label class for display numbers and text
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

    # The game argument needs to be there for ducktyping higher in the hierchy
    # Also it might be used later
    def update(self, game: "Game"): #pylint: disable=unused-argument
        """Updates the entity"""

        # Redraw the text
        self._render()
