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

        UP=119,
        DOWN=115,
        LEFT=97,
        RIGHT=100,
        ACTION=113,

    )

    # Keyset for Player 2
    keys2 = Core.Keyset(

        UP=273,
        DOWN=274,
        RIGHT=275,
        LEFT=276,
        ACTION=47,

    )

    # Attributes
    speed = 7
    jump = 17
    fastfall = 2
    gravity = 1 # Should this be a global constant

    airJumps = 2
    slide = 1
    wallJumpFreeze = 5
