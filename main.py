# Spook Fighters Alpha
# Authors: Ryan/Kevin
# GitHub: https://github.com/HN67/spook-fighters

# At some point this should probably be broken into modules?
# Though the stuff is pretty interconnected (is that an issue?)

# Import modules
from dataclasses import dataclass
import enum
from enum import Enum

# tkinter package for graphics
import tkinter as tk

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


# Base entity class that holds position and size and frames basic methods
class Entity(pygame.sprite.Sprite):
    """Abstract base class for entities"""

    def __init__(self, rect):
        # Call superclass Sprite init
        pygame.sprite.Sprite.__init__(self)

        # Create image
        self.image = pygame.Surface((rect.width, rect.height))

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
        # Movement speed (horizontal) TODO Maybe make horizontal acceleration
        self.speed = speed
        # Jump power
        self.jump = jump
        # Force of gravity
        self.gravity = gravity
        # Power of accelerated falling
        self.fall = fall

        # Number of max air jumps TODO hello this is static again
        self.airJumps = 2
        # Constant for length of wallJump freeze TODO Another static
        self.wallJumpFreezeTicks = 2

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

        self.collided = Pair(False, False)


    def update(self, entities, events):
        """Updates the physics of the Player, when colliding with the entities SpriteGroup
           And with events from Player.Events passed in"""

        # Set x speed if not frozen and on ground
        if self.xFreeze == 0:
            if self.collided.y:

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
        
        # Add fast fall pull
        self.ySpeed += (self.fall if (self.Events.DOWN in events) else 0)

        # Add gravity pull
        self.ySpeed += self.gravity

        # wall input code
        if self.collided.x:

            # Wall jump
            if self.Events.UP in events:

                # Set speed away from wall
                self.xSpeed = -self.cling * self.jump
                # Freeze movement temporarily
                self.xFreeze = self.wallJumpFreezeTicks

        # Jump code
        if (self.Events.UP in events) and (self.jumps > 0):

            # Decrement jump counter if in air
            if not self.collided.y:
                self.jumps -= 1
            # Set y-velocity
            self.ySpeed = -1*self.jump

        # TODO probably break function here and move rest into another (move or something)

        # Move with collisions enabled
        self.collided = self.move(self.xSpeed, self.ySpeed, entities)

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

        """
        ## Manage the creation of projectiles
        #print(self.newPresses)
        if ("q" in self.game.newKeys):
            print("blam")
            self.game.activate.add(Projectile(self.game, self.x, self.y,
                                              5, 5,
                                              0, -5, 10, "red"))
        """


# Basic barrier class with various location means
class Barrier(Entity):
    """Creates barrier, using second point set as relative or fixed (size/corners),
            Origin is always first set, so second should be greater to prevent odd behavior"""

    def __init__(self, game, x1, y1, x2, y2, form="size", color = "black", visible = True):
        if form == "size":
            super().__init__(game, x1, y1, x2, y2)
        elif form == "corners":
            super().__init__(game, x1, y1, x2 - x1 + 1, y2 - y1 + 1)

        self.color = color

        self.sprite = self.game.canvas.create_rectangle(*corners(self.x, self.y,
                                       self.width, self.height),
                                       fill = self.color, outline = self.color)

        if not visible:
            game.canvas.itemconfig(self.sprite, state = "hidden")

    def start(self):
        super().start()
        self.game.barriers.add(self)
        self.draw()

    def draw(self):
        self.sprite = self.game.canvas.create_rectangle(*corners(self.x, self.y,
                                       self.width, self.height),
                                       fill = self.color, outline = self.color)

    def remove(self):
        self.game.canvas.delete(self.sprite)
        self.game.entities.remove(self)
        self.game.barriers.remove(self)
    
    def redraw(self):
        # Update canvas
        self.game.canvas.coords(
            self.sprite, *corners(self.x, self.y,
                                       self.width, self.height))

    def check(self):
        pass

    def act(self):
        pass

# Basic projectile class
class Projectile(Entity):

    def __init__(self, game, x, y, width, height, xSpeed, ySpeed, lifeSpan, color):
        """Creates a projectile object for game
           If lifespan is set to False, the projectile is immortal,
           otherwise it lives for the lifespan number of ticks"""

        # Call standard entity constructor
        super().__init__(game, x, y, width, height)

        self.xSpeed = xSpeed
        self.ySpeed = ySpeed

        self.lifeSpan = lifeSpan
        
        self.color = color
        
        # Initialize age field
        self.age = 0

    def draw(self):
        self.sprite = self.game.canvas.create_rectangle(
                                    *corners(self.x, self.y, self.width, self.height),
                                                        fill = self.color,
                                                        outline = self.color)

    def redraw(self):
        # Update canvas
        self.game.canvas.coords(self.sprite, *corners(self.x, self.y,
                                       self.width, self.height))

    def remove(self):
        self.game.canvas.delete(self.sprite)
        self.game.entities.remove(self)

    def check(self):
        # Check age if not immortal
        if not self.lifeSpan == False:
            if self.age >= self.lifeSpan:
                # Delete projectile
                self.game.removal.add(self)
                
    def act(self):
        # Increment age
        self.age += 1
        # Change position
        self.x += self.xSpeed
        self.y += self.ySpeed

        # Queue for redrawal
        self.game.redraw.add(self)

        

# Main game class (very unrefined)
class Game:

    def __init__(self):
        ## Main fundamental setup
        # Creates main tk window
        self.root = tk.Tk()

        # Creates main canvas
        self.canvas = tk.Canvas(self.root, width = 400, height = 300,
                                bd = 0, bg = "cyan", highlightthickness = 0)
        self.canvas.pack()

        self.canvas.focus_set()

        # Sets to track entities
        self.entities = set()
        self.barriers = set()

        # Sets that track entities with action requests
        self.redraw = set()
        self.activate = set()
        self.removal = set()

        # Sets that track key presses
        self.keysPressed = set()
        self.lastKeys = set()
        self.newKeys = set()

        self.canvas.bind("<KeyPress>", self.check_press)
        self.canvas.bind("<KeyRelease>", self.check_release)

        ## Basic testing
        # Controllable entity
        Player(self, 100, 100, 15, 15, 3, 9, 1, 0.5).start()

        # Stage walls
        Barrier(self, -50, 0, -1, 299, form = "corners", visible = False).start()
        Barrier(self, 400, 0, 449, 299, form = "corners", visible = False).start()
        Barrier(self, 0, -50, 399, -1, form = "corners", visible = False).start()
        Barrier(self, 0, 250, 399, 299, form = "corners", color = "green").start()
        # Random blocks in stage
        Barrier(self, 50, 200, 25, 25).start()
        Barrier(self, 50, 75, 24, 125, color = "Green").start()
        Barrier(self, 150, 100, 25, 25, color = "Pink").start()
        Barrier(self, 250, 50, 25, 25, color = "Orange").start()
    
    def check_press(self, event):      
        self.keysPressed.add(event.char)

    def check_release(self, event):     
        self.keysPressed.remove(event.char)

    def game_loop(self):

        self.newKeys = self.keysPressed - self.lastKeys  

        for entity in self.activate:
            entity.start()
        self.activate.clear()
        
        for entity in self.entities:
            entity.check()

        for entity in self.removal:
            entity.remove()
        self.removal.clear()
        
        for entity in self.entities:
            entity.act()

        for entity in self.redraw:
            entity.redraw()       
        self.redraw.clear()
        
        self.lastKeys = self.keysPressed.copy()
        
        self.root.after(20, self.game_loop)

## Define some top-scope functions

# Debug info function that can turn off all debug print statements
if DEBUG_INFO:
    def debug(*value, sep = " ", end = "\n"):
        print(*value, sep = sep, end = end)
else:
    def debug(*value, sep = " ", end = "\n"):
        return None

# Function that returns topleft bottomright corners based
# on topleft corner + width/height
def corners(x, y, width, height):
    return [x, y, x + width-1, y + height-1]

def main():
    pygame.init()

    spook = Game()
    spook.game_loop()
    tk.mainloop()

if __name__ == "__main__":
    main()