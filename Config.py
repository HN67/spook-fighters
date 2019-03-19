"""Config file"""
# Config file for Spook Fighters Py

class game:
    """General configuration for the game"""

    # Width and height of the display screen
    width = 800
    height = 600

    # Name of the window
    name = "Spook Fighters Py"

class stage:
    """Config for stage setup"""

    # Floor height
    floorHeight = 100

class player:

    # Height and width of player
    height = 50
    width = 50
    
    class keys:
        pass

    # Attributes
    speed = 7
    jump = 17
    fastfall = 2
    gravity = 1 # Should this be a global constant
        
