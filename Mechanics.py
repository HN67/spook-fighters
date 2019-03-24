"""The mechanics and logic of actual game characters, attacks, classes, etc, and general balance"""

# Import main for base classes
import Base

# TODO should there be an Attack/Power class that extends Controller that is then inherited?
# It would have startup frames, link to the player, etc
# Grab attack class
class Grab(Base.Controller):
    """Grab attack object"""

    def __init__(self, rect):
        super().__init__(rect)

    def update(self, game: "Game"):
        pass