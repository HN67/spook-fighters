"""All classes and logic for Spook Fighters game"""
# Spook Fighters Py
# Authors: Ryan/Kevin
# GitHub: https://github.com/HN67/spook-fighters

# Import modules
import enum
from enum import Enum
import typing

# Import pygame
import pygame

# Import local files
import Config
import Core
from Core import Dir, Color, Pair

import Base
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
        ATTACK = enum.auto()

    def __init__(self, rect, *, color=Core.Color.BLACK, image=None,
                 keyset: Core.Keyset, attributes: Core.PlayerAttributes
                ):

        super().__init__(rect, image)
        self.hasImage = (image is not None)

        # Set color
        self.color = color
        self.image.fill(self.color)

        # Reference attributes
        self.attributes = attributes

        # Construct dynamic variables
        # Dynamic current xSpeed for acceleration if needed
        self.xSpeed = 0

        # Stun ticks (freezes movement) remaining
        self.stun = 0

        # Cooldown ticks (freezes attacks)
        self.cooldown = 0

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

        # Init damage counter
        self.damage = Core.Variable(0)

    def hit(self, damage: int, force: int, varForce: float, vector: Core.Vector):
        """Handles the player getting hit\n
        damage - damage counter increase\n
        force - modifier for knockback and stun\n
        varforce - additional force that scales with total damage\n
        vector - direction of attack and knockback\n
        """
        # Increase damage
        self.damage.value += damage
        # Calculate total force
        totalForce = force + int(self.damage.value * varForce)
        # Take stun
        self.stun = totalForce
        # Take knockback based on vector and stun (calced above)
        self.xSpeed = vector.x * totalForce
        self.ySpeed = vector.y * totalForce

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
                elif event.key == self.keyset.ATTACK:
                    playerEvents.add(Player.Events.ATTACK)

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
        self.ySpeed += self.attributes.gravity

        # Check to make sure not stunned for most movement options
        if self.stun == 0:

            # Update color
            if not self.hasImage:
                self.image.fill(self.color)

            # Wall hang logic, only wall hang if not stunned
            if self.touching(barriers, Dir.LEFT) or self.touching(barriers, Dir.RIGHT):
                # Slow falling: Cant slow faster than slide attribute
                self.ySpeed = min(self.attributes.slide, self.ySpeed)

            # A left D right
            if self.Events.LEFT in events:
                # Set speed
                self.xSpeed = -self.attributes.speed
                # Remember direction
                self.xDirection = Dir.LEFT
            elif self.Events.RIGHT in events:
                # Set speed
                self.xSpeed = self.attributes.speed
                # Remember direction
                self.xDirection = Dir.RIGHT
            else:
                self.xSpeed = 0

            # Add fast fall pull
            if self.Events.DOWN in events:
                self.ySpeed += self.attributes.fastfall

            # Jump code
            if (self.Events.UP in events) and (self.jumps > 0):

                # Decrement jump counter if in air # CAN JUMP OFF ANY SOLID
                if not (self.touching(solids, Dir.DOWN) or
                        self.touching(solids, Dir.LEFT) or
                        self.touching(solids, Dir.RIGHT)):
                    self.jumps -= 1
                # Set y-velocity
                self.ySpeed = -self.attributes.jump

                # Wall jump
                # Left wall jump
                if self.touching(solids, Dir.LEFT) and not self.touching(solids, Dir.RIGHT):

                    # Move right
                    self.xSpeed = self.attributes.speed

                    # Freeze movement temporarily
                    self.stun = self.attributes.wallJumpFreeze

                # Right wall jump
                elif self.touching(solids, Dir.RIGHT) and not self.touching(solids, Dir.LEFT):

                    # Move left
                    self.xSpeed = -self.attributes.speed

                    # Freeze movement temporarily
                    self.stun = self.attributes.wallJumpFreeze

        else:

            # Make color gray while stunnned
            if not self.hasImage:
                self.image.fill(Core.Color.GRAY)

            # Detick stun
            self.stun -= 1

            # Align stun at 0
            if self.stun <= 0:
                self.stun = 0

        # TODO update() method needs to be broken into logical components

        # Move with collisions enabled
        self.collided = self.move(self.xSpeed, self.ySpeed, solids)

        # React to collisions
        # Vertical floor/ceiling collision
        if self.collided.y:

            # Reset jumps on floor collision
            if self.touching(solids, Dir.DOWN):
                self.jumps = self.attributes.airJumps

            # Zero vertical speed due to vertical collision
            self.ySpeed = 0
            # Reset stun because (prevent combo locking, against floor?)
            self.stun = 0

        # Horizontal wall collision
        if self.collided.x:

            # Reset jumps for wall jump
            self.jumps = self.attributes.airJumps

            # Zero horizontal speed due to wall collision
            self.xSpeed = 0

            # Zero vertical speed due to wall collision
            self.ySpeed = 0

            # Reset stun to prevent wall locking
            self.stun = 0

        # Attack code
        # Only attack if not cooling down
        if self.cooldown == 0:

            # Also cant be movement stunned
            if self.stun == 0:
                # Action event
                if self.Events.ACTION in events:
                    # Create Grab Attack
                    game.add_controllers(Mechanics.Grab(self))
                # Attack event
                if self.Events.ATTACK in events:
                    # Create slash attack
                    game.add_controllers(Mechanics.Slash(self))

        else:

            # Detick cooldown
            self.cooldown -= 1

            # Align cooldown at 0
            if self.cooldown <= 0:
                self.cooldown = 0


# Basic projectile class
class Projectile(Entity):
    """Moving projectile\n
    Calls callback on hit with a player, providing self,player as arguments\n
    If a callback isnt provided, the Projectile will kill itself on collision"""

    def __init__(self, rect, image=None, xSpeed=0, ySpeed=0, lifeSpan=-1, callback=None):

        # Call standard entity constructor
        super().__init__(rect, image)

        # Reference parameters
        self.xSpeed = xSpeed
        self.ySpeed = ySpeed

        self.age = lifeSpan

        self.callback = callback

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

            # Check for player collisions
            for player in self.collisions(game.get_players()):
                if self.callback is None:
                    self.kill()
                    break # Dont bother checking other players, no behavior to callback
                else:
                    self.callback(self, player)

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

        # All group
        self.allSprites = pygame.sprite.Group()
        # Barriers: solid ground for players to jump off
        self.barriers = pygame.sprite.Group()
        # Players: controllable characters
        self.players = pygame.sprite.Group()
        # Solids: they are used for collisions
        self.solids = pygame.sprite.Group()
        # Projectile: moving, non colliding, non controllable (usually)
        self.projectiles = pygame.sprite.Group()
        # Controllers: they manage projectiles
        self.controllers = pygame.sprite.Group()
        # Visibiles: what actually gets drawn (apart from labels)
        self.visibles = pygame.sprite.Group()
        # Labels: HUD/GUI labels for information output
        self.labels = pygame.sprite.Group()

        # Events and keysHeld variables
        self.events = None
        self.keysHeld = None

    def game_update(self):
        """Represents one update of entire game logic, returns False once the game is over"""

        # Collect events
        self.events = pygame.event.get()

        # Check each event, debug it
        for event in self.events:

            debug(event)

            # Return False (break) if the window was quit
            if event.type == pygame.QUIT:
                return False

            # Check for key events, right now the objects mostly check keys themselves
            if event.type == pygame.KEYDOWN:
                pass

        # Collect keys held down
        self.keysHeld = pygame.key.get_pressed()

        # Update all sprites
        #self.allSprites.update(self)
        # In specific order
        self.barriers.update(self)
        self.projectiles.update(self)
        self.players.update(self)
        self.controllers.update(self)
        self.labels.update(self)

        # Draw all sprites onto sky color, labels above everything
        self.surface.fill(Color.SKYBLUE)
        self.visibles.draw(self.surface)
        self.labels.draw(self.surface)

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

    def add_labels(self, *labels):
        """Adds labels to the game"""
        self.allSprites.add(*labels)
        self.labels.add(*labels)

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

def setup_game(screen):
    """Sets up and returns Game instance based on 'screen'"""

    # Create game object
    game = Game(screen)

    # Populate the game object
    # Create Players
    # TODO position is based on screen size, but should probably be moved to config
    # Also, the color should and can easily be moved to config
    players = (
        Player(
            pygame.Rect(
                Config.game.width / 2 - Config.player.width / 2,
                Config.game.height - Config.stage.floorHeight - 2*Config.player.height,
                Config.player.width, Config.player.height,
            ),
            attributes=Config.player.attributes,
            color=Color.ORANGE,
            keyset=Config.player.keys1,
        ),
        Player(
            pygame.Rect(
                Config.game.width / 2 - Config.player.width / 2 + 100,
                Config.game.height - Config.stage.floorHeight - 2*Config.player.height,
                Config.player.width, Config.player.height,
            ),
            attributes=Config.player.attributes,
            color=Color.BLUE,
            keyset=Config.player.keys2,
        )
    )
    game.create_player(players[0])
    game.create_player(players[1])

    # TODO not bad staticity, but probably room for improvement,
    # especially with the floating platform
    # Create Barriers
    blocks = (

        # Screen borders
        # Stage bottom border
        Base.Barrier(cornerRect(-100, Config.game.height,
                                Config.game.width + 100, Config.game.height + 100)),

        # Stage wall borders
        Base.Barrier(cornerRect(-100, 0, 0, Config.game.height)), # LEFT
        Base.Barrier(cornerRect(Config.game.width, 0,
                                Config.game.width + 100, Config.game.height)), # RIGHT

        # Stage ceiling border
        Base.Barrier(cornerRect(-100, -100, Config.game.width + 100, 0)),

        # Floor/ground
        Base.Barrier(cornerRect(0, Config.game.height - Config.stage.floorHeight,
                                Config.game.width, Config.game.height),
                     color=Color.DARKGREEN),

        # Floating platform
        Base.DirectionalBarrier(pygame.Rect(Config.game.width/2 - 200, 300,
                                            400, 15),
                                {Core.Dir.UP}, color=Color.DARKGREEN),

    )
    game.add_barriers(*blocks)

    # Create labels
    labels = (

        Base.Label(
            pygame.Rect(Config.hud.x1Position, Config.hud.yPosition, 0, 0),
            height=Config.hud.damageHeight,
            variable=players[0].damage,
            color=Color.BLACK, bgColor=Color.ORANGE
        ),

        Base.Label(
            pygame.Rect(Config.hud.x2Position, Config.hud.yPosition, 0, 0),
            height=Config.hud.damageHeight,
            variable=players[1].damage,
            color=Color.BLACK, bgColor=Color.BLUE
        ),

    )
    game.add_labels(*labels)

    # Return the game object
    return game

def main():
    """Main function to start the game"""

    # Init pygame
    pygame.init()

    # Create clock
    clock = pygame.time.Clock()

    # Make screen based on config
    screen = pygame.display.set_mode((Config.game.width, Config.game.height))

    # Set captions
    pygame.display.set_caption(Config.game.name)

    # Create game object
    spook = setup_game(screen)

    # Create flag for when game is quit
    running = True

    # Run the object
    while running:

        # Update the game (it draws itself onto the screen)
        running = spook.game_update()

        # Flip the display
        pygame.display.flip()

        # Frame rate based on config
        clock.tick(Config.game.fps)

# Run main() automatically if this is the __main__ file
if __name__ == "__main__":
    main()
