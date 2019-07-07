"""Config file"""
# Config file for Spook Fighters Py

# Import Core
from modules import Core

class screen:
    """Config for specifically the screen"""

    # Width and height of the display screen
    width = 800
    height = 600

    # Name of the window
    name = "Spook Fighters Py"

    # Frames (ticks) per second max of the game
    fps = 60

class game:
    """General configuration for the game"""

    # Position on screen
    x = 0
    y = 0

    # Width and height of the game area
    width = 800
    height = 600

class menu:
    """Configuration for menu screen"""

    # Position of title bar
    titlePos = (125, 100)

    # Size of title text
    titleSize = 60

    # Position of start button
    startPos = (350, 400)

    # Size of text on menu screen
    textSize = 25

class hud:
    """Configuration for the HUD"""

    # Text label height
    textHeight = 40

    # Height of the damage variables
    damageHeight = textHeight

    margin = 10
    yPosition = game.height - margin - damageHeight

    x1Position = 10
    x2Position = game.width - damageHeight * 2 - margin

    lifeYPosition = yPosition - damageHeight
    lifeHeight = damageHeight

    # Default font used from system
    # Should probably also add True font or something
    # Ideally would always be monospace?
    sysFont = "Courier New"

class stage:
    """Config for stage setup"""

    # Killbox distance
    killDistance = 100
    killBoxWidth = 100

    # Respawn
    respawnX = game.width / 2
    respawnY = 100

class player:
    """Config for players"""

    # Height and width of player
    height = 50
    width = 50

    # Stock count
    lives = 3

    # Keyset for Player 1
    keys1 = Core.Keyset(

        UP=119, # W
        DOWN=115, # S
        LEFT=97, # A
        RIGHT=100, # D
        ACTION=99, # C
        ATTACK=118, # V

    )

    # Keyset for Player 2
    keys2 = Core.Keyset(

        UP=273, # ^ Arrow
        DOWN=274, # Down Arrow
        RIGHT=275, # > Arrow
        LEFT=276, # < Arrow
        ACTION=105, # I
        ATTACK=111, # O

    )

    # Attributes
    attributes = Core.PlayerAttributes(
        speed=4,
        maxSpeed=7,
        jump=17,
        fastfall=2,
        gravity=1,

        airJumps=2,
        slide=1,
        wallJumpFreeze=5,

        ySpeedStun=15,
        xSpeedStun=10,
    )

class attack:
    """Config for the different attacks"""

    class grab:
        """Config for grab attack"""

        width = 10

        speed = 5 # Relative horizontal speed

        lifeSpan = 6

        cooldown = 10 # Ticks to cooldown caster for

        # Hit state
        hitState = Core.HitState(
            damage=4,
            force=10,
            varForce=1/10,
            vector=Core.Vector(0.5, -0.3)
        )

        upHitState = hitState.copy()
        upHitState.vector = Core.Vector(0, -0.75)

    class sword:
        """Attacks for the swordsman class"""

        class basic:
            """Basic attack"""

            hitState = Core.HitState(
                damage=7,
                force=10,
                varForce=1/8,
                vector=Core.Vector(0.5, -0.75)
            )

            xSpeed = 10
            ySpeed = -4

            lifeSpan = 6

            cooldown = 25

            # Width and height of the actual projectile
            width = 20
            height = 20
