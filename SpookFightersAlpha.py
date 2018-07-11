# Spook Fighters Alpha
# Authors: Ryan/Kevin
# Possible collab site: http://collabedit.com/yv4ad

## Import modules

# tkinter package for graphics
import tkinter as tk

## Define basic classes

# Base entity class that holds position and size and frames basic methods
class Entity:

    def __init__(self, game, y, x, height, width):
        self.game = game

        self.y = y
        self.x = x
        self.height = height
        self.width = width

    def check(self):
        raise NotImplementedError("{} is an abstract class".format(type(self)))

    def act(self):
        raise NotImplementedError("{} is an abstract class".format(type(self)))

# Abstract character class for playable characters
class Character(Entity):

    def __init__(self, canvas, y, x, height, width, health):
        super().__init__(canvas, y, x, height, width)
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

    def __init__(self, game, y, x, height, width, speed):
        super().__init__(game, y, x, height, width)
        self.speed = speed

        self.controls = {"a":{"x":-1,"y":0},
                         "d":{"x":1,"y":0},
                         "w":{"x":0,"y":-1},
                         "s":{"x":0,"y":1}}
        
        self.keyPresses = []

        self.sprite = self.game.canvas.create_rectangle(self.x, self.y,
                                       self.x+self.width, self.y+self.height)

    def check(self):
        self.keyPresses = self.game.keysPressed.intersection(self.controls)

    def act(self):
        self.x += sum([self.speed*self.controls[i]["x"] for i in self.keyPresses])
        self.y += sum([self.speed*self.controls[i]["y"] for i in self.keyPresses])
        self.game.canvas.coords(self.sprite, self.x, self.y,
                                self.x+self.width, self.y+self.height)

# Main game class (very unrefined)
class Game:

    def __init__(self):
        ## Main fundamental setup
        self.root = tk.Tk()
        
        self.canvas = tk.Canvas(self.root, width = 400, height = 300,
                                bd = 0, bg = "cyan")
        self.canvas.pack()

        self.canvas.focus_set()

        self.entities = set()
        
        self.keysPressed = set()

        self.canvas.bind("<KeyPress>", self.check_press)
        self.canvas.bind("<KeyRelease>", self.check_release)

        ## Basic testing
        self.entities.add(ControllableBox(self, 0, 50, 15, 15, 3))

    def check_press(self, event):      
        self.keysPressed.add(event.char)

    def check_release(self, event):     
        self.keysPressed.remove(event.char)

    def game_loop(self):
        print(self.keysPressed)
        for entity in self.entities:
            entity.check()
        for entity in self.entities:
            entity.act()
        self.root.after(20, self.game_loop)

spook = Game()
spook.game_loop()
tk.mainloop()
