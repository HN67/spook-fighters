"""All classes and logic for Spook Fighters game"""
# Spook Fighters Alpha
# Authors: Ryan/Kevin
# GitHub: https://github.com/HN67/spook-fighters

# At some point this should probably be broken into modules?
# Though the stuff is pretty interconnected

# Import modules
import enum
from enum import Enum

# Import pygame
import pygame

# Module level constants
# Determines if debug info is shown
DEBUG_INFO = True

# Define basic classes
class Pair: # pylint: disable=too-few-public-methods
    """Pair class collecting an x and y"""

    def __init__(self, x, y):
        self.x = x
        self.y = y


class Dir(Enum):
    """Relative direction enum"""
    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)

class Color:
    """Color RGB constants"""
    BLACK = (0, 0, 0)
    WHITE = (0, 0, 0)

    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    YELLOW = (255, 255, 0)
    ORANGE = (255, 125, 0)
    PURPLE = (255, 255, 0)

    DARKGREEN = (0, 127, 0)

    SKYBLUE = (0, 200, 200)

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

    def update(self):
        """Updates the entity"""
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
        ghost = Entity(self.rect.copy())

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
        """Checks if self collides with every entity in 'entities'"""
        return pygame.sprite.spritecollide(self, entities, False)

    def move(self, dX: int, dY: int, entities):
        """Moves to a new position and takes into account collisions"""

        # Reference current position
        ghost = Entity(self.rect)

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
        ghost = Entity(self.rect)

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
        ghost = Entity(future)

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


# Basic testing class
class Player(Entity):
    """This represents a controllable player"""

    class Events(Enum):
        """Enumerator of event types for Player"""
        UP = enum.auto()
        DOWN = enum.auto()
        LEFT = enum.auto()
        RIGHT = enum.auto()

    def __init__(self, rect, speed, jump, fall, gravity):
        super().__init__(rect)

        # Reference parameters
        # Movement speed (horizontal)
        # TODO Maybe make horizontal acceleration
        self.speed = speed
        # Jump power
        self.jump = jump
        # Force of gravity
        self.gravity = gravity
        # Power of accelerated falling
        self.fall = fall

        # Number of max air jumps
        # TODO hello this is static again
        self.airJumps = 2
        # Constant for length of wallJump freeze
        # TODO Another static
        self.wallJumpFreezeTicks = 5

        # TODO static, Speed of sliding down wall
        self.slide = 1

        # Construct dynamic variables
        # Dynamic current xSpeed
        self.xSpeed = 0
        # Direction of last wall-cling
        self.cling = 0
        # Freeze prevents movement for an amount of ticks
        self.xFreeze = 0

        # Current ySpeed
        self.ySpeed = 0
        # Remaining number of jumps
        self.jumps = 0

        # Tracks if there was a collision last update()
        self.collided = Pair(False, False)

        # Data collected by collect()
        self.collected = {"barriers": None, "events": None}


    def collect(self, barriers, events):
        """Give barrier list and events (Player.Events) to be used next update()"""

        self.collected = {"barriers": barriers, "events": events}


    def update(self):
        """Updates the physics of the Player, when colliding with the entities SpriteGroup
           And with events from Player.Events passed in"""

        # Reference collected data
        barriers = self.collected["barriers"]
        events = self.collected["events"]

        # Set x speed if not frozen
        if self.xFreeze == 0:
            # A left D right
            if self.Events.LEFT in events:
                self.xSpeed = -self.speed
            elif self.Events.RIGHT in events:
                self.xSpeed = self.speed
            else:
                self.xSpeed = 0
        else:
            # Decrease freeze if frozen
            self.xFreeze -= 1

        # Add gravity pull
        self.ySpeed += self.gravity

        # wall hang logic
        # TODO split left and right into seperate
        if self.touching(barriers, Dir.LEFT) or self.touching(barriers, Dir.RIGHT):

            # Slow gravity (no acceleration)
            self.ySpeed = self.slide

            # Only wall jump if clinging
            if self.Events.LEFT in events or self.Events.RIGHT in events:

                pass

            # Wall jump
            if self.Events.UP in events:

                # Set speed away from wall
                self.xSpeed = -self.cling * self.speed
                # Freeze movement temporarily
                self.xFreeze = self.wallJumpFreezeTicks

        # Add fast fall pull
        if self.Events.DOWN in events:
            self.ySpeed += self.fall

        # Jump code
        if (self.Events.UP in events) and (self.jumps > 0):

            # Decrement jump counter if in air
            if not self.touching(barriers, Dir.DOWN): #TODO broken for some reason
                self.jumps -= 1
            # Set y-velocity
            self.ySpeed = -1*self.jump

            debug("jump", self.collided.y, self.jumps)

        # TODO probably break function here and move rest into another (move or something)

        # Move with collisions enabled
        self.collided = self.move(self.xSpeed, self.ySpeed, barriers)

        # React to collisions
        # Vertical floor/ceiling collision
        if self.collided.y:

            # Reset jumps on floor collision
            if self.ySpeed > 0:
                self.jumps = self.airJumps

            # Zero vertical speed due to vertical collision
            self.ySpeed = 0

        # Horizontal wall collision
        if self.collided.x:

            # Reset jumps for wall jump
            self.jumps = self.airJumps

            # Determine direction of collision
            self.cling = abs(self.xSpeed)/self.xSpeed

            # Zero horizontal speed due to wall collision
            self.xSpeed = 0
            # Cling to wall
            self.ySpeed = 0

        # TODO add projectile logic


# Basic barrier class
class Barrier(Entity):
    """Creates barrier, using rect and optionally image
        Color will override image
    """

    def __init__(self, rect, image=None, color=None):

        super().__init__(rect, image)

        if color is not None:
            debug(color)
            self.image.fill(color)

    def update(self):
        pass


# Basic projectile class
class Projectile(Entity):
    """Linear Moving projectile"""

    def __init__(self, rect, image=None, xSpeed=0, ySpeed=0, lifeSpan=-1):
        """Creates a projectile object for game
           If lifespan is set to False, the projectile is immortal,
           otherwise it lives for the lifespan number of ticks"""

        # Call standard entity constructor
        super().__init__(rect, image)

        # Reference parameters
        self.xSpeed = xSpeed
        self.ySpeed = ySpeed

        self.age = lifeSpan

    def update(self):
        # Decrement age
        self.age -= 1

        # Change position
        self.rect.x += self.xSpeed
        self.rect.y += self.ySpeed

        # Return False when 'dead'
        return self.age > 0



# Main game class (very unrefined)
class Game:
    """Main game class for running a game of Spook Fighters"""

    def __init__(self, screen):
        ## Main fundamental setup
        # Reference the window screen
        self.screen = screen

        # Create game surface
        self.surface = pygame.surface.Surface((400, 300))

        # Create SpriteGroups
        self.allSprites = pygame.sprite.Group()

        self.barriers = pygame.sprite.Group()

        ## Basic testing
        # Create Player
        # TODO whole bunch of statics
        self.player = Player(pygame.Rect(25, 25, 20, 20), 3, 9, 1, 0.5)
        self.player.add(self.allSprites)



        # Create Barriers
        blocks = (

            # Stage floor
            Barrier(pygame.Rect(0, 250, 400, 50), color=Color.DARKGREEN),

            # Stage walls
            Barrier(cornerRect(-50, 0, 0, 300)),
            Barrier(cornerRect(400, 0, 450, 300)),

            # Stage ceiling
            Barrier(cornerRect(-50, -50, 450, 0)),

            # Random blocks
            Barrier(pygame.Rect(50, 50, 25, 25), color=Color.BLUE),
            Barrier(pygame.Rect(100, 70, 25, 25), color=Color.RED),
            Barrier(pygame.Rect(300, 200, 25, 50), color=Color.PURPLE),
            Barrier(pygame.Rect(150, 200, 25, 25), color=Color.ORANGE),

        )
        self.allSprites.add(*blocks)
        self.barriers.add(*blocks)

    def game_update(self):
        """Represents one update of entire game logic"""

        # Prepare for player events
        playerEvents = set()

        # COllect events TODO make key constants (A-> 97)
        for event in pygame.event.get():
            print(event)
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == 119:
                    playerEvents.add(Player.Events.UP)

        # Check for keys held down
        keysHeld = pygame.key.get_pressed()
        if keysHeld[97]:
            playerEvents.add(Player.Events.LEFT)
        if keysHeld[100]:
            playerEvents.add(Player.Events.RIGHT)
        if keysHeld[115]:
            playerEvents.add(Player.Events.DOWN)

        # Update sprites
        # Buffer player
        self.player.collect(self.barriers, playerEvents)

        # update all sprites
        self.allSprites.update()

        # Draw all sprites TODO create color constants
        self.surface.fill(Color.SKYBLUE)
        self.allSprites.draw(self.surface)

        # Blit onto the screen
        self.screen.blit(self.surface, (0, 0))

        # Finish sucsessfully
        return True

## Define some top-scope functions
# Function to produce a corner-rect
def cornerRect(left, top, right, bottom):
    """Creates a Rect using corners"""
    return pygame.Rect(left, top, right - left, bottom - top)


# Debug info function that can turn off all debug print statements
if DEBUG_INFO:
    def debug(*value, sep=" ", end="\n"):
        """Acts the exact same as pythons 'print', but can be disabled by a global"""
        print(*value, sep=sep, end=end)
else:
    def debug(*value, sep=" ", end="\n"): #pylint: disable=unused-argument
        """Acts the exact same as pythons 'print', but can be disabled by a global"""
        return None

def main():
    """Main function to start the game"""

    # Init pygame
    pygame.init()

    # Create clock
    clock = pygame.time.Clock()

    # Create screen
    # TODO make config for sizes and set window title
    screen = pygame.display.set_mode((400, 300))

    # Set captions
    pygame.display.set_caption("Spook Fighters Py")

    # Create flag for when game is quit
    running = True

    # Create game object
    spook = Game(screen)

    # Run the object
    while running:

        running = spook.game_update()

        pygame.display.flip()

        # Frame rate
        # TODO move to config
        clock.tick(60)

if __name__ == "__main__":
    main()
