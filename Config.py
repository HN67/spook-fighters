"""Config file"""
# Config file for Spook Fighters Py

# Import Core
import Core

class game:
    """General configuration for the game"""

    # Width and height of the display screen
    width = 800
    height = 600

    # Name of the window
    name = "Spook Fighters Py"

    # Frames (ticks) per second max of the game
    fps = 60

class hud:
    """Configuration for the HUD"""

    # Height of the damage variables
    damageHeight = 40

    margin = 10
    yPosition = game.height - margin - damageHeight

    x1Position = 10
    x2Position = game.width - damageHeight * 2 - margin

class stage:
    """Config for stage setup"""

    # Floor height
    floorHeight = 100

class player:
    """Config for players"""

    # Height and width of player
    height = 50
    width = 50

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
        speed=7,
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
        lifeSpan = 2

        cooldown = 20 # Ticks to cooldown for

        # Hit state
        hitState = Core.HitState(
            damage=5,
            force=20,
            varForce=1/20,
            vector=Core.Vector(0.1, -0.5)
        )

    class sword:
        """Attacks for the swordsman class"""

        class basic:
            """Basic attack"""

            hitState = Core.HitState(
                damage=15,
                force=30,
                varForce=1/5,
                vector=Core.Vector(0.1, -0.25)
            )

            xSpeed = 10
            ySpeed = 2

            lifeSpan = 10

            cooldown = 60

            # Width and height of the actual projectile
            width = 10
            height = 10
