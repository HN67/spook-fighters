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
        ACTION=113, # Q

    )

    # Keyset for Player 2
    keys2 = Core.Keyset(

        UP=273, # ^ Arrow
        DOWN=274, # Down Arrow
        RIGHT=275, # > Arrow
        LEFT=276, # < Arrow
        ACTION=47, # / key

    )

    # Attributes
    speed = 7
    jump = 17
    fastfall = 2
    gravity = 1 # Should this be a global constant

    airJumps = 2
    slide = 1
    wallJumpFreeze = 5

class attack:
    """Config for the different attacks"""

    class grab:
        """Config for grab attack"""

        displacement = 0 # Starting distance from player
        width = 10

        speed = 5 # Relative horizontal speed
        lifeSpan = 4
