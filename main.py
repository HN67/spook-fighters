"""All classes and logic for Spook Fighters game"""
# Spook Fighters Py
# Authors: Ryan/Kevin
# GitHub: https://github.com/HN67/spook-fighters

# TODO At some point this should probably be broken into modules?
# Though the stuff is pretty interconnected

# Import modules
import enum
from enum import Enum

# Import pygame
import pygame

# Import local files
import Config
from Core import Dir, Color, Pair

from Base import Entity

import Mechanics

# Module level constants
# Determines if debug info is shown
DEBUG_INFO = True

# Basic testing class
class Player(Entity):
    """This represents a controllable player"""

    class Events(Enum):
        """Enumerator of event types for Player"""
        UP = enum.auto()
        DOWN = enum.auto()
        LEFT = enum.auto()
        RIGHT = enum.auto()

        ACTION = enum.auto()

    def __init__(self, rect,
                 speed, jump, fall, gravity,
                 airJumps, wallJumpFreeze, slide, *, color=None, keyset
                ):

        super().__init__(rect)

        # Set color
        if color is not None:
            self.image.fill(color)

        # Reference parameters
        # Movement speed (horizontal)
        self.speed = speed
        # Jump power
        self.jump = jump
        # Force of gravity
        self.gravity = gravity
        # Power of accelerated falling
        self.fall = fall

        # Number of max air jumps
        # Reference airJumps
        self.airJumps = airJumps
        # Constant for length of wallJump freeze
        # Reference wallFreeze
        self.wallJumpFreezeTicks = wallJumpFreeze

        # Reference wallslide
        self.slide = slide

        # Construct dynamic variables
        # Dynamic current xSpeed for acceleration if needed
        self.xSpeed = 0

        # Stun ticks (freezes movement) remaining
        self.stun = 0

        # Setup which direction you are facing
        self.xDirection = None

        # Current ySpeed
        self.ySpeed = 0
        # Remaining number of jumps
        self.jumps = 0

        # Tracks if there was a collision last update()
        self.collided = Pair(False, False)

        # Data collected by collect()
        self.collected = {"barriers": None, "events": None}

        # Reference keyset
        self.keyset = keyset

    def parse_events(self, events, keysHeld):
        """Parses PyGame events and held keys into Player events using its keyset"""

        # Create player events set
        playerEvents = set()

        # Check for held keys (LEFT/RIGHT/DOWN)
        if keysHeld[self.keyset.LEFT]:
            playerEvents.add(Player.Events.LEFT)
        if keysHeld[self.keyset.RIGHT]:
            playerEvents.add(Player.Events.RIGHT)
        if keysHeld[self.keyset.DOWN]:
            playerEvents.add(Player.Events.DOWN)

        # Check for pressed keys (UP)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == self.keyset.UP:
                    playerEvents.add(Player.Events.UP)
                elif event.key == self.keyset.ACTION:
                    playerEvents.add(Player.Events.ACTION)

        # Return player events
        return playerEvents

    def update(self, game: "Game"):
        """Updates the physics of the Player, when colliding with the entities SpriteGroup
           And with events from Player.Events passed in"""

        # Reference collected data
        barriers = game.get_barriers()
        solids = game.get_solids()
        events = self.parse_events(game.get_events(), game.keys_held())

        # Gravity pull
        self.ySpeed += self.gravity

        # Wall hang logic
        if self.touching(barriers, Dir.LEFT) or self.touching(barriers, Dir.RIGHT):
            # Slow falling
            self.ySpeed = self.slide

        # Set x speed if not frozen
        if self.stun == 0:

            # A left D right
            if self.Events.LEFT in events:
                # Set speed
                self.xSpeed = -self.speed
                # Remember direction
                self.xDirection = Dir.LEFT
            elif self.Events.RIGHT in events:
                # Set speed
                self.xSpeed = self.speed
                # Remember direction
                self.xDirection = Dir.RIGHT
            else:
                self.xSpeed = 0

            # Add fast fall pull
            if self.Events.DOWN in events:
                self.ySpeed += self.fall

            # Jump code
            if (self.Events.UP in events) and (self.jumps > 0):

                # Decrement jump counter if in air # CAN JUMP OFF ANY SOLID
                if not (self.touching(solids, Dir.DOWN) or
                        self.touching(solids, Dir.LEFT) or
                        self.touching(solids, Dir.RIGHT)):
                    self.jumps -= 1
                # Set y-velocity
                self.ySpeed = -self.jump

                # Wall jump
                # Left wall jump
                if self.touching(solids, Dir.LEFT):

                    # Move right
                    self.xSpeed = self.speed

                    # Freeze movement temporarily
                    self.stun = self.wallJumpFreezeTicks

                # Right wall jump
                elif self.touching(solids, Dir.RIGHT):

                    # Move left
                    self.xSpeed = -self.speed

                    # Freeze movement temporarily
                    self.stun = self.wallJumpFreezeTicks

        else:
            # Decrease freeze if frozen
            self.stun -= 1

        # TODO probably break function here and move rest into another (move or something
        # TODO maybe dont do that but this update() should be broken into logical components

        # Move with collisions enabled
        self.collided = self.move(self.xSpeed, self.ySpeed, solids)

        # React to collisions
        # Vertical floor/ceiling collision
        if self.collided.y:

            # Reset jumps on floor collision
            if self.touching(solids, Dir.DOWN):
                self.jumps = self.airJumps

            # Zero vertical speed due to vertical collision
            self.ySpeed = 0

        # Horizontal wall collision
        if self.collided.x:

            # Reset jumps for wall jump
            self.jumps = self.airJumps

            # Zero horizontal speed due to wall collision
            self.xSpeed = 0

        # Projectile code

        # Action event
        if self.Events.ACTION in events:
            # Create Grab Attack
            game.add_controllers(Mechanics.Grab(self))


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

    def update(self, game: "Game"):
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

        # Shows if there was a collision last tick
        self.collided = False

        # Which players the projectile collided with
        self.hits = None

    def update(self, game: "Game"):

        # Die at end of lifespan
        if self.age == 0:
            # Remove from spritegroups
            self.kill()
        else:
            # Decrement age
            self.age -= 1

            # Change position
            self.rect.x += self.xSpeed
            self.rect.y += self.ySpeed

            # Check for player collisions and update signal
            self.hits = self.collisions(game.get_players())
            if len(self.hits) > 0:
                self.collided = True
            else:
                self.collided = False

# Main game class (very unrefined)
class Game:
    """Main game class for running a game of Spook Fighters"""

    def __init__(self, screen):
        ## Main fundamental setup
        # Reference the window screen
        self.screen = screen

        # Create game surface
        self.surface = pygame.surface.Surface((Config.game.width, Config.game.height))

        # Create SpriteGroups
        self.allSprites = pygame.sprite.Group()

        self.barriers = pygame.sprite.Group()

        self.players = pygame.sprite.Group()

        self.solids = pygame.sprite.Group()

        self.projectiles = pygame.sprite.Group()

        self.controllers = pygame.sprite.Group()

        self.visibles = pygame.sprite.Group()

        # Events and keysHeld variables
        self.events = None
        self.keysHeld = None

        ## Basic testing
        # Create Players
        # TODO whole bunch of statics maybe its better now but not really for the starting position
        players = (
            Player(
                pygame.Rect(
                    Config.game.width / 2 - Config.player.width / 2,
                    Config.game.height - Config.stage.floorHeight - 2*Config.player.height,
                    Config.player.width, Config.player.height,
                ),
                Config.player.speed, Config.player.jump,
                Config.player.fastfall, Config.player.gravity,
                airJumps=Config.player.airJumps,
                wallJumpFreeze=Config.player.wallJumpFreeze,
                slide=Config.player.slide,
                color=Color.ORANGE,
                keyset=Config.player.keys1,
            ),
            Player(
                pygame.Rect(
                    Config.game.width / 2 - Config.player.width / 2 + 100,
                    Config.game.height - Config.stage.floorHeight - 2*Config.player.height,
                    Config.player.width, Config.player.height,
                ),
                Config.player.speed, Config.player.jump,
                Config.player.fastfall, Config.player.gravity,
                airJumps=Config.player.airJumps,
                wallJumpFreeze=Config.player.wallJumpFreeze,
                slide=Config.player.slide,
                color=Color.BLUE,
                keyset=Config.player.keys2,
            )
        )
        self.create_player(players[0])
        self.create_player(players[1])

        # TODO statics should at least be moved and created with hooks
        # Create Barriers
        blocks = (

            # Screen borders
            # Stage bottom border
            Barrier(cornerRect(-100, Config.game.height,
                               Config.game.width + 100, Config.game.height + 100)),

            # Stage wall borders
            Barrier(cornerRect(-100, 0, 0, Config.game.height)), # LEFT
            Barrier(cornerRect(Config.game.width, 0,
                               Config.game.width + 100, Config.game.height)), # RIGHT

            # Stage ceiling border
            Barrier(cornerRect(-100, -100, Config.game.width + 100, 0)),

            # Floor/ground
            Barrier(cornerRect(0, Config.game.height - Config.stage.floorHeight,
                               Config.game.width, Config.game.height),
                    color=Color.DARKGREEN),

            # Floating blocks
            #Barrier(pygame.Rect(50, 50, 25, 25), color=Color.BLUE),
            #Barrier(pygame.Rect(100, 70, 25, 25), color=Color.RED),
            #Barrier(pygame.Rect(300, 200, 25, 50), color=Color.GREEN),
            #Barrier(pygame.Rect(150, 200, 25, 25), color=Color.ORANGE),

            Barrier(pygame.Rect(Config.game.width/2 - 200, 200,
                                400, 100), color=Color.DARKGREEN),

        )
        self.add_barriers(*blocks)

    def game_update(self):
        """Represents one update of entire game logic, returns False once the game is over"""

        # COllect events
        self.events = pygame.event.get()
        for event in self.events:
            print(event)
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                pass

        # Check for keys held down
        self.keysHeld = pygame.key.get_pressed()

        # Update all sprites
        #self.allSprites.update(self)
        # In specific order
        self.barriers.update(self)
        self.players.update(self)
        self.projectiles.update(self)
        self.controllers.update(self)

        # Draw all sprites onto sky color
        self.surface.fill(Color.SKYBLUE)
        self.visibles.draw(self.surface)

        # Blit onto the screen
        self.screen.blit(self.surface, (0, 0))

        # Finish sucsessfully
        return True

    def get_events(self):
        """Returns the PyGame events collected last update"""
        return self.events

    def keys_held(self):
        """Returns the keys held as of last update"""
        return self.keysHeld

    def add_barriers(self, *barriers):
        """Add barriers to the game"""
        self.barriers.add(*barriers)
        self.allSprites.add(*barriers)
        self.solids.add(*barriers)
        self.visibles.add(*barriers)

    def create_player(self, player):
        """Add a player to the game"""
        self.players.add(player)
        self.allSprites.add(player)
        self.solids.add(player)
        self.visibles.add(player)

    def add_projectiles(self, *projectiles):
        """Adds projectiles to the game state"""
        self.projectiles.add(*projectiles)
        self.allSprites.add(*projectiles)
        self.visibles.add(*projectiles)

    def add_controllers(self, *controllers):
        """Adds controllers to the game state"""
        self.allSprites.add(*controllers)
        self.controllers.add(*controllers)

    def get_solids(self):
        """Returns the solid objects (for collisions) of the game"""
        return self.solids

    def get_players(self):
        """Returns the players of the game"""
        return self.players

    def get_barriers(self):
        """Returns the barriers of the game"""
        return self.barriers

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
    # Make screen based on config
    screen = pygame.display.set_mode((Config.game.width, Config.game.height))

    # Set captions
    pygame.display.set_caption(Config.game.name)

    # Create flag for when game is quit
    running = True

    # Create game object
    spook = Game(screen)

    # Run the object
    while running:

        running = spook.game_update()

        pygame.display.flip()

        # Frame rate based on config
        clock.tick(Config.game.fps)

if __name__ == "__main__":
    main()
