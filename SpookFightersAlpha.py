# Spook Fighters Alpha
# Authors: Ryan/Kevin
# Collab site: http://collabedit.com/yv4ad
# GitHub: https://github.com/HN67/spook-fighters

# At some point this should probably be broken into modules?
# Though the stuff is pretty interconnected (is that an issue?)

## Import modules

# tkinter package for graphics
import tkinter as tk

## Define basic classes
# A basic container that has an x and y attribute
class Point:

    def __init__(self, x, y):
        self.x = x
        self.y = y


# Base entity class that holds position and size and frames basic methods
class Entity:
    """Abstract base class for entities"""

    # The entity class should perhaps automatically
    # add itself to the game entities set
    # (consider implementing)
    # Pros: Reliability?, Especially for projectile
    # Cons: Inability for "invisible" objects that have not been added to game yet
    # Cons cont.: However it already auto adds to canvas, so its not invisible  
    
    def __init__(self, game, x, y, width, height):
        self.game = game

        self.y = y
        self.x = x
        self.height = height
        self.width = width

    def check(self):
        raise NotImplementedError("{} is an abstract class".format(type(self)))

    def act(self):
        raise NotImplementedError("{} is an abstract class".format(type(self)))

    def collisions(self, *others):
        """Takes a list of other entities and checks for collisions"""
        results = set()
        for other in others:
            if (abs(self.center().x - other.center().x) < (self.width/2 + other.width/2)
            and abs(self.center().y - other.center().y) < (self.height/2 + other.height/2)):
                results.add(other)
        return results

    def center(self):
        return Point(self.x + self.width/2, self.y + self.height/2)

    def align(self, vector, speed, entity):
        """Aligns against wall of entity based on speed and vector"""
        # Logic is based on origin being top left
        if vector == "x":
            if speed < 0:
                self.x = entity.x + entity.width
            elif speed > 0:
                self.x = entity.x - self.width
        elif vector == "y":
            if speed < 0:
                self.y = entity.y + entity.height
            elif speed > 0:
                self.y = entity.y - self.height
            

    def move_collide(self, speed, objects):
        """Takes a Point object that contains x/y speed, and collides with provided objects"""

        # Save current position
        oriX = self.x
        oriY = self.y
        
        # Move x based on speed
        self.x += speed.x
        collX = False
        # Check for collisions
        wall = list(self.collisions(*objects))
        # Fix collisions and check again
        while len(wall) > 0:
            collX = True
            # Align to edge of wall based on speed
            self.align("x", speed.x, wall[0])
            # Recheck collisions
            wall = list(self.collisions(*objects))
        # Move current position into storage and reset x to check y properly
        futureX = self.x
        self.x = oriX

        # Move y based on speed    
        self.y += speed.y
        collY = False
        # Check for collisions
        wall = list(self.collisions(*objects))
        # Fix collisions and check again
        while len(wall) > 0:
            collY = True
            # Align to edge of wall based on speed
            self.align("y", speed.y, wall[0])
            # Recheck collisions
            wall = list(self.collisions(*objects))
        # Move current position and reset y (simply for potential forward compat)
        futureY = self.y
        self.y = oriY

        # Update position
        self.x = futureX
        self.y = futureY
        
        # Check corner case (literally when colliding with corner at diagonal velocity)
        '''
           C
          /
        []
        '''
        wall = list(self.collisions(*objects))
        # Fix collision
        while len(wall) > 0:
            collX = True
            collY = True
            # Align to corner of wall based on speed in both vectors
            self.align("x", speed.x, wall[0])
            self.align("y", speed.y, wall[0])
            # Recheck collisions
            wall = list(self.collisions(*objects))  

        # Return object holding truth of collisions in each axis
        # (For jump resets mostly)
        return Point(collX, collY)

# Abstract character class for playable characters
# Unimplemented
class Character(Entity):

    def __init__(self, game, x, y, width, height, health):
        super().__init__(game, x, y, width, height)
        self.maxHealth = health

    def offensive(self):
        pass

    def defensive(self):
        pass

    def skill(self):
        pass

    def ultimate(self):
        pass

# Basic testing class
class ControllableBox(Entity):

    def __init__(self, game, x, y, width, height, speed, jump, fall, gravity):
        super().__init__(game, x, y, width, height)

        self.controls = {"a":{"x":-1,"y":0},
                         "d":{"x":1,"y":0},
                         "w":{"x":0,"y":-1},
                         "s":{"x":0,"y":1}}
        
        self.keyPresses = set()
        self.newPresses = set()

        self.speed = speed
        self.jump = jump
        self.gravity = gravity
        self.fall = fall

        self.xSpeed = 0
        self.ySpeed = 0

        self.sprite = self.game.canvas.create_rectangle(*corners(self.x, self.y,
                                       self.width, self.height))

    def check(self):
        self.newPresses = self.game.newKeys.intersection(self.controls)
        self.keyPresses = self.game.keysPressed.intersection(self.controls)

    def act(self):
        # Create speed x/y based on key presses
        self.xSpeed = self.speed*sum([self.controls[i]["x"] for i in self.keyPresses])
        if ("w" in self.newPresses):
            self.ySpeed = -1*self.jump
        #self.ySpeed -= (self.jump if ("w" in self.newPresses) else 0)
        self.ySpeed += (self.fall if ("s" in self.keyPresses) else 0)
        self.ySpeed += self.gravity

        #print(self.xSpeed, self.ySpeed)
        
        # Handle wall collisions
        collided = self.move_collide(Point(self.xSpeed, self.ySpeed), self.game.barriers)

        # Zero speeds upon collision
        # Perhaps implement logic to detect between floor and ceiling
        if collided.x:
            # Zero horizontal speed due to wall collision
            self.xSpeed = 0
            # Experimental zeroing of vertical speed to simulate wall cling
            # (Needs drastic refinement)
            self.ySpeed = 0
        if collided.y:
            # Zero vertical speed due to ceiling or floor collision
            self.ySpeed = 0

        # Update canvas
        self.game.canvas.coords(self.sprite, *corners(self.x, self.y,
                                       self.width, self.height))

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

    def check(self):
        pass

    def act(self):
        pass

# Basic projectile class
class Projectile(Entity):

    def __init__(self, game, x, y, width, height, xSpeed, ySpeed, lifespan, color):
        """Creates a projectile object for game
           If lifespan is set to False, the projectile is immortal,
           otherwise it lives for the lifespan number of ticks"""

        # Call standard entity constructor
        super().__init__(game, x, y, width, height)

        self.color = color

        self.sprite = self.game.canvas.create_rectangle(x, y, width, height,
                                                        fill = self.color,
                                                        outline = self.color)
        
        # Initialize age field
        age = 0

    def check(self):
        # Check age if not immortal
        if not lifespan == False:
            if age >= lifespan:
                # Delete projectile by deleting object reference and
                # removing from game entities set
                self.game.canvas.delete(self)
                self.game.entities.remove(self)
                del self
        # Maybe this should be moved to act()
        age += 1
        
    def act(self):
        pass

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
        
        self.keysPressed = set()
        self.lastKeys = set()
        self.newKeys = set()

        self.canvas.bind("<KeyPress>", self.check_press)
        self.canvas.bind("<KeyRelease>", self.check_release)

        ## Basic testing
        # Controllable entity
        self.entities.add(ControllableBox(self, 100, 100, 15, 15, 3,
                                          15, 1, 1))

        # Stage walls
        self.add_barrier(Barrier(self, -50, 0, -1, 299, form = "corners",
                                  visible = False))
        self.add_barrier(Barrier(self, 400, 0, 449, 299, form = "corners",
                         visible = False))
        self.add_barrier(Barrier(self, 0, -50, 399, -1, form = "corners",
                         visible = False))
        self.add_barrier(Barrier(self, 0, 250, 399, 299, form = "corners",
                                 color = "green"))
        # Random blocks in stage
        self.add_barrier(Barrier(self, 50, 200, 25, 25))
        self.add_barrier(Barrier(self, 50, 75, 24, 125, color = "Green"))
        self.add_barrier(Barrier(self, 150, 100, 25, 25, color = "Pink"))
        self.add_barrier(Barrier(self, 250, 50, 25, 25, color = "Orange"))

    def add_barrier(self, barrier):
        self.entities.add(barrier)
        self.barriers.add(barrier)
    
    def check_press(self, event):      
        self.keysPressed.add(event.char)

    def check_release(self, event):     
        self.keysPressed.remove(event.char)

    def game_loop(self):

        self.newKeys = self.keysPressed - self.lastKeys  
        
        for entity in self.entities:
            entity.check()
        for entity in self.entities:
            entity.act()

        self.lastKeys = self.keysPressed.copy()
        
        self.root.after(20, self.game_loop)

## Define some top-scope functions
def corners(x, y, width, height):
    return [x, y, x + width-1, y + height-1]

spook = Game()
spook.game_loop()
tk.mainloop()
