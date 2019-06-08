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
from modules import Config
from modules import Core
from modules.Core import Dir, Color, Pair

from modules import Base
from modules.Base import Entity

from modules import Mechanics

# Module level constants
# Determines if debug info is shown
DEBUG_INFO = True

# Basic player class
# Important notes:
# Stun is applied by being hit
# Cooldown is stun from starting a move
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
                 keyset: Core.Keyset, attributes: Core.PlayerAttributes, lives: int
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

        # Init lives
        self.lives = Core.Variable(lives)

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

    def respawn(self, game: "Game"):
        """Respawns in reference to a game"""
        # Reset damage
        self.damage.value = 0
        # Decrement life
        self.lives.value -= 1
        # Reset speed vectors
        self.xSpeed = 0
        self.ySpeed = 0
        # Reset cooldowns
        self.stun = 0
        self.cooldown = 0
        # Move to respawn point
        self.rect.x = game.respawn.x
        self.rect.y = game.respawn.y

    def snap_platforms(self, platforms: pygame.sprite.Group, presses: set, oldRect: pygame.Rect, ):
        """Logic for colliding with platforms"""
        # Setup collision groups
        collisions = self.collisions(platforms)
        checked = pygame.sprite.Group()
        # Fix each collisions
        while len(collisions) > 0:
            # Reference current
            current = list(collisions)[0]
            # Collide if conditions met
            if (
                    # Check that you fell on the platform
                    oldRect.bottom <= current.rect.top
                    # Allow phasing with S key
                    and not self.Events.DOWN in presses
            ):
                # Align
                self.align(current, Dir.DOWN)
                # Set collided
                self.collided.y = True
            # Otherwise, remeber this entity is okay
            else:
                # remember this entity has been checked
                checked.add(current)
            # Recheck for collisions
            collisions = self.collisions(platforms)
            collisions.remove(checked)

    def parse_events(self, pyEvents, keysHeld):
        """Parses PyGame events and held keys into Player events using its keyset
        Returns (newEvents, currentEvents)
        """

        # Create player events set
        events = set()
        pressEvents = set()
        releaseEvents = set()

        # Check for held keys
        if keysHeld[self.keyset.LEFT]:
            events.add(Player.Events.LEFT)
        if keysHeld[self.keyset.RIGHT]:
            events.add(Player.Events.RIGHT)
        if keysHeld[self.keyset.DOWN]:
            events.add(Player.Events.DOWN)
        if keysHeld[self.keyset.UP]:
            events.add(Player.Events.UP)
        if keysHeld[self.keyset.ACTION]:
            events.add(Player.Events.ACTION)
        if keysHeld[self.keyset.ATTACK]:
            events.add(Player.Events.ATTACK)

        # Check for key events
        for event in pyEvents:
            # Check for key presses
            if event.type == pygame.KEYDOWN:
                if event.key == self.keyset.LEFT:
                    pressEvents.add(Player.Events.LEFT)
                if event.key == self.keyset.RIGHT:
                    pressEvents.add(Player.Events.RIGHT)
                if event.key == self.keyset.DOWN:
                    pressEvents.add(Player.Events.DOWN)
                if event.key == self.keyset.UP:
                    pressEvents.add(Player.Events.UP)
                elif event.key == self.keyset.ACTION:
                    pressEvents.add(Player.Events.ACTION)
                elif event.key == self.keyset.ATTACK:
                    pressEvents.add(Player.Events.ATTACK)
            # Check for releases
            elif event.type == pygame.KEYUP:
                if event.key == self.keyset.LEFT:
                    releaseEvents.add(Player.Events.LEFT)
                if event.key == self.keyset.RIGHT:
                    releaseEvents.add(Player.Events.RIGHT)
                if event.key == self.keyset.DOWN:
                    releaseEvents.add(Player.Events.DOWN)
                if event.key == self.keyset.UP:
                    releaseEvents.add(Player.Events.UP)
                elif event.key == self.keyset.ACTION:
                    releaseEvents.add(Player.Events.ACTION)
                elif event.key == self.keyset.ATTACK:
                    releaseEvents.add(Player.Events.ATTACK)

        # Return player events
        return (pressEvents, releaseEvents, events)

    def update(self, game: "Game"):
        """Updates the physics of the Player"""

        # Reference collected data
        barriers = game.get_barriers()
        solids = game.get_solids()
        platforms = game.get_platforms()
        grounds = pygame.sprite.Group(solids, platforms)
        presses, releases, events = self.parse_events(game.get_events(), game.keys_held())

        # Gravity pull if in air and not hanging from cooldown
        if (
                not self.touching(solids, Dir.DOWN)
                and not self.touching(game.get_platforms(), Dir.DOWN)
            ):
            self.ySpeed += self.attributes.gravity

        # Check to make sure not stunned for most movement options
        if self.stun == 0 and self.cooldown == 0:

            # Wall hang logic, only wall hang if not stunned
            if self.touching(barriers, Dir.LEFT) or self.touching(barriers, Dir.RIGHT):
                # Slow falling: Cant slow faster than slide attribute
                self.ySpeed = min(self.attributes.slide, self.ySpeed)

            # A left D right
            if self.Events.LEFT in events and self.Events.RIGHT in events:
                # Slow down (cancellation) based on current direction of movement
                if self.xSpeed > 0:
                    self.xSpeed -= self.attributes.speed
                    # Align
                    if self.xSpeed > 0:
                        self.xSpeed = 0
                elif self.xSpeed < 0:
                    self.xSpeed += self.attributes.speed
                    # Align
                    if self.xSpeed > 0:
                        self.xSpeed = 0
            elif self.Events.LEFT in events:
                # Set speed
                if self.xSpeed > -self.attributes.maxSpeed:
                    self.xSpeed -= self.attributes.speed
                    # Align
                    if self.xSpeed < -self.attributes.maxSpeed:
                        self.xSpeed = -self.attributes.maxSpeed
                # Remember direction
                self.xDirection = Dir.LEFT
            elif self.Events.RIGHT in events:
                # Set speed
                if self.xSpeed < self.attributes.maxSpeed:
                    self.xSpeed += self.attributes.speed
                    # Align
                    if self.xSpeed > self.attributes.maxSpeed:
                        self.xSpeed = self.attributes.maxSpeed
                # Remember direction
                self.xDirection = Dir.RIGHT
            else:
                # Slow down based on current direction of movement
                if self.xSpeed > 0:
                    self.xSpeed -= self.attributes.speed
                    # Align
                    if self.xSpeed > 0:
                        self.xSpeed = 0
                elif self.xSpeed < 0:
                    self.xSpeed += self.attributes.speed
                    # Align
                    if self.xSpeed > 0:
                        self.xSpeed = 0

            # Add fast fall pull
            if self.Events.DOWN in events:
                self.ySpeed += self.attributes.fastfall

            # Jump code
            if (self.Events.UP in presses) and (self.jumps > 0):

                # Decrement jump counter if in air # CAN JUMP OFF ANY SOLID
                if not (self.touching(solids, Dir.DOWN) or
                        self.touching(solids, Dir.LEFT) or
                        self.touching(solids, Dir.RIGHT) or
                        self.touching(game.get_platforms(), Dir.DOWN)):
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

        # TODO update() method needs to be broken into logical components

        # Dont move if cooling
        dX = self.xSpeed
        dY = self.ySpeed

        # Save old rect
        oldRect = self.rect.copy()

        # Move with collisions enabled
        self.collided = self.move(dX, dY, solids)

        # Check for platforms
        self.snap_platforms(game.get_platforms(), presses, oldRect)

        # React to collisions
        # Vertical floor/ceiling collision
        if self.collided.y:

            # Reset jumps on floor or platform collision
            if self.touching(solids, Dir.DOWN) or self.touching(game.get_platforms(), Dir.DOWN):
                self.jumps = self.attributes.airJumps

            # Zero vertical speed due to vertical collision
            self.ySpeed = 0
            # Zero horizontal speed
            self.xSpeed = 0
            ## Reset stun because (prevent combo locking, against floor?)
            #self.stun = 0

        # Horizontal wall collision
        if self.collided.x:

            # Reset jumps for wall jump
            self.jumps = self.attributes.airJumps

            # Zero horizontal speed due to wall collision
            self.xSpeed = 0

            # Zero vertical speed due to wall collision
            self.ySpeed = 0

            ## Reset stun to prevent wall locking
            #self.stun = 0

        # Attack code
        # Only attack if not cooling down
        if self.cooldown == 0:

            # Also cant be movement stunned
            if self.stun == 0:
                # Action event
                if self.Events.ACTION in presses:
                    # Create Grab Attack
                    if self.Events.UP in events:
                        game.add_controllers(Mechanics.UpGrab(self))
                    else:
                        game.add_controllers(Mechanics.Grab(self))
                    # Stop if on ground
                    if self.touching(grounds, Dir.DOWN):
                        self.xSpeed = 0
                # Attack event
                if self.Events.ATTACK in presses:
                    # Create slash attack
                    game.add_controllers(Mechanics.Slash(self))
                    # Stop if on ground
                    if self.touching(grounds, Dir.DOWN):
                        self.xSpeed = 0

        # Decrease stun and cooldown
        self.stun -= 1
        self.cooldown -= 1
        # Align cooldown at 0
        if self.cooldown <= 0:
            self.cooldown = 0
        # Align stun at 0
        if self.stun <= 0:
            self.stun = 0

        # Update image
        if not self.hasImage:
            # Gray for stun
            if self.stun > 0:
                self.image.fill(Core.Color.GRAY)
            # Darkened for cooling down
            elif self.cooldown > 0:
                self.image.fill(Core.Color.scale(self.color, 0.5))
            # Otherwise normal color
            else:
                self.image.fill(self.color)

        # Check for death
        if len(self.collisions(game.get_killBoxes())) > 0:
            # Respawn
            self.respawn(game)

# Basic projectile class
# TODO create after_update passable function or something
class Projectile(Entity):
    """Moving projectile\n
    Calls post after every update, providing self, defaults to an empty function
    Calls callback on hit with a player, providing self,player as arguments\n
    If a callback isnt provided, the Projectile will kill itself on collision"""

    def __init__(self, rect, image=None, xSpeed=0, ySpeed=0, lifeSpan=None,
                 post: typing.Callable = None, callback: typing.Callable = None):

        # Call standard entity constructor
        super().__init__(rect, image)

        # Reference parameters
        self.xSpeed = xSpeed
        self.ySpeed = ySpeed

        self.lifeSpan = lifeSpan

        # Init age
        self.age = 0

        self.callback = callback

        # Reference post or create
        if post is None:
            self.post = lambda proj: None
        else:
            self.post = post

    def update(self, game: "Game"):

        # Die at end of lifespan
        if self.lifeSpan is not None and self.age >= self.lifeSpan:
            # Remove from spritegroups
            self.kill()
        else:
            # Increase age
            self.age += 1

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

        # Call post update
        self.post(self)

# Main game class (very unrefined)
class Game:
    """Main game class for running a game of Spook Fighters"""

    def __init__(self, screen):
        ## Main fundamental setup
        # Reference the window screen
        self.screen = screen

        # Create game surface
        self.surface = pygame.surface.Surface((Config.game.width, Config.game.height))
        
        # Blit location
        self.position = (Config.game.x, Config.game.y)

        # Create SpriteGroups

        # All group
        self.allSprites = pygame.sprite.Group()
        # Barriers: solid ground for players to jump off
        self.barriers = pygame.sprite.Group()
        # Platforms: one way platforms that players can jump through
        self.platforms = pygame.sprite.Group()
        # Players: controllable characters
        self.players = pygame.sprite.Group()
        # Solids: they are used for collisions
        self.solids = pygame.sprite.Group()
        # Killboxes: player 'dies' on collisions
        self.killBoxes = pygame.sprite.Group()
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

        # Game variables
        # Respawn point
        self.respawn = Core.Pair(0, 0)

    def game_update(self, events):
        """Represents one update of entire game logic, returns False once the game is over"""

        # Collect events
        self.events = events.copy()

        # Check each event, debug it
        for event in self.events:

            # Change the pos of mouse events to be relative
            # TODO the events are being passed by reference, so this modifies the entire
            # events for anything. events should probably be copied
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                event.pos = (event.pos[0] - self.position[0], event.pos[1] - self.position[1])

        # Collect keys held down
        self.keysHeld = pygame.key.get_pressed()

        # Update all sprites
        #self.allSprites.update(self)
        # In specific order
        # Update barriers (why)?
        # Update players, create controllers
        # Update projectiles, sometimes based on players
        # Update conntrollers, create projectiles
        # Update labels
        self.players.update(self)
        self.projectiles.update(self)
        self.controllers.update(self)
        self.labels.update(self)

        # Draw all sprites onto sky color, labels above everything
        self.surface.fill(Color.SKYBLUE)
        self.visibles.draw(self.surface)
        self.labels.draw(self.surface)

        # Blit onto the screen
        self.screen.blit(self.surface, (Config.game.x, Config.game.y))

        # Finish sucsessfully
        return True

    def get_events(self):
        """Returns the PyGame events collected last update"""
        return self.events

    def keys_held(self):
        """Returns the keys held as of last update"""
        return self.keysHeld

    def set_spawn(self, x: int, y: int):
        """Sets the player spawn point"""
        self.respawn = Core.Pair(x, y)

    def add_barriers(self, *barriers):
        """Add barriers to the game"""
        self.barriers.add(*barriers)
        self.allSprites.add(*barriers)
        self.solids.add(*barriers)
        self.visibles.add(*barriers)

    def add_platforms(self, *platforms):
        """Adds platforms to the game"""
        self.platforms.add(*platforms)
        self.allSprites.add(*platforms)
        self.visibles.add(*platforms)

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

    def add_killBoxes(self, *killBoxes):
        """Adds killBoxes to the game"""
        self.allSprites.add(*killBoxes)
        self.killBoxes.add(*killBoxes)

    def get_solids(self):
        """Returns the solid objects (for collisions) of the game"""
        return self.solids

    def get_players(self):
        """Returns the players of the game"""
        return self.players

    def get_barriers(self):
        """Returns the barriers of the game"""
        return self.barriers

    def get_platforms(self):
        """Returns the platforms of the game"""
        return self.platforms

    def get_killBoxes(self):
        """Returns the killboxes of the game"""
        return self.killBoxes

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
                Config.game.width / 2 - Config.player.width*2,
                0,
                Config.player.width, Config.player.height,
            ),
            attributes=Config.player.attributes,
            color=Color.ORANGE,
            keyset=Config.player.keys1,
            lives=Config.player.lives,
        ),
        Player(
            pygame.Rect(
                Config.game.width / 2 + Config.player.width,
                0,
                Config.player.width, Config.player.height,
            ),
            attributes=Config.player.attributes,
            color=Color.BLUE,
            keyset=Config.player.keys2,
            lives=Config.player.lives,
        )
    )
    game.create_player(players[0])
    game.create_player(players[1])

    # TODO not bad staticity, but probably room for improvement,
    # especially with the floating platform
    # Create Barriers
    blocks = (

        # Floor/ground
        Base.Barrier(cornerRect(100, Config.game.height - 200,
                                Config.game.width - 100, Config.game.height - 100),
                     color=Color.DARKGREEN),

    )
    game.add_barriers(*blocks)

    # Passable platforms
    platforms = (
        # Floating platforms
        Base.Barrier(pygame.Rect(100, Config.game.height - 400,
                                 150, 20),
                     color=Color.DARKGREEN),

        Base.Barrier(pygame.Rect(Config.game.width - 250, Config.game.height - 400,
                                 150, 20),
                     color=Color.DARKGREEN),
    )
    game.add_platforms(*platforms)

    # Create killboxes
    killboxes = (
        Base.Barrier(
            # Top corner to corner
            cornerRect(
                -Config.stage.killDistance - Config.stage.killBoxWidth,
                -Config.stage.killDistance - Config.stage.killBoxWidth,
                Config.game.width + Config.stage.killDistance + Config.stage.killBoxWidth,
                -Config.stage.killDistance
            )
        ),
        Base.Barrier(
            # Bottom corner to corner
            cornerRect(
                -Config.stage.killDistance - Config.stage.killBoxWidth,
                Config.game.height + Config.stage.killDistance,
                Config.game.width + Config.stage.killDistance + Config.stage.killBoxWidth,
                Config.game.height + Config.stage.killDistance + Config.stage.killBoxWidth
            )
        ),
        Base.Barrier(
            # Left
            cornerRect(
                -Config.stage.killDistance - Config.stage.killBoxWidth,
                -Config.stage.killDistance,
                -Config.stage.killDistance,
                Config.game.height + Config.stage.killDistance
            )
        ),
        Base.Barrier(
            # Right
            cornerRect(
                Config.game.width + Config.stage.killDistance,
                -Config.stage.killDistance,
                Config.game.width + Config.stage.killDistance + Config.stage.killBoxWidth,
                Config.game.height + Config.stage.killDistance
            )
        ),
    )
    game.add_killBoxes(*killboxes)

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

        Base.Label(
            pygame.Rect(Config.hud.x1Position, Config.hud.lifeYPosition, 0, 0),
            height=Config.hud.lifeHeight,
            variable=players[0].lives,
            color=Color.BLACK, bgColor=Color.ORANGE
        ),

        Base.Label(
            pygame.Rect(Config.hud.x2Position, Config.hud.lifeYPosition, 0, 0),
            height=Config.hud.lifeHeight,
            variable=players[1].lives,
            color=Color.BLACK, bgColor=Color.BLUE
        ),

    )
    game.add_labels(*labels)

    # Set spawn
    game.set_spawn(Config.stage.respawnX, Config.stage.respawnY)

    # Return the game object
    return game

def main():
    """Main function to start the game"""

    # Init pygame
    pygame.init()

    # Create clock
    clock = pygame.time.Clock()

    # Make screen based on config
    screen = pygame.display.set_mode((Config.screen.width, Config.screen.height))

    # Set captions
    pygame.display.set_caption(Config.screen.name)

    # Create game object
    spook = setup_game(screen)

    # Create flag for when game is quit
    running = True

    # Run the object
    while running:

        # Collect events
        events = pygame.event.get()

        # Check each event, debug it
        for event in events:
            
            # Debug event
            debug(event)

            # break if the window was quit
            if event.type == pygame.QUIT:
                running = False

        # Update the game with events
        spook.game_update(events)

        # Flip the display
        pygame.display.flip()

        # Frame rate based on config
        clock.tick(Config.screen.fps)

# Run main() automatically if this is the __main__ file
if __name__ == "__main__":
    main()
