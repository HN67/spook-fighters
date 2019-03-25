"""The mechanics and logic of actual game characters, attacks, classes, etc, and general balance"""

# Import pygame
import pygame

# Import local files
import Base
import Config
import Core

# Import main? might need to move Projectile to main
import main

# Attack abstract class that handles freeze and references
class Attack(Base.Controller):
    """Base class for attack controllers"""

    def __init__(self, player: "Player", stun: int = 0):
        super().__init__(player.rect.copy()) #?

        # Reference player
        self.player = player

        # Reference starting direction
        self.xDirection = player.xDirection

        # Init age for tick count
        self.tick = 0

        # Freeze caster
        player.xSpeed = 0
        player.stun = stun

    def update(self, game: "Game"):
        """Updates the entity"""
        self.tick += 1

# Grab attack class
class Grab(Attack):
    """Grab attack object"""

    def __init__(self, player: "Player"):
        super().__init__(player, stun=10)

        # Reference config
        cfg = Config.attack.grab()

        # Starting x position and speed (left/right)
        if self.xDirection == Core.Dir.LEFT:
            xPosition = self.rect.left - cfg.width
            speed = -cfg.speed
        else:
            xPosition = self.rect.right
            speed = cfg.speed

        # Create projectile(not added to the game yet)
        self.projectile = main.Projectile(
            pygame.Rect(xPosition, self.rect.top,
                        cfg.width, self.rect.height),
            xSpeed=speed, lifeSpan=cfg.lifeSpan
        )

    def update(self, game: "Game"):
        super().update(game)

        # Create projectile
        if self.tick == 3:
            game.add_projectiles(self.projectile)

        # Garbage the controller
        elif self.tick == 10:
            self.kill()

        # Watch projectile
        if self.projectile.collided:
            # Iterate through player collisions
            for player in self.projectile.hits:
                if player is not self.player:
                    # Damage the other player
                    # TODO config all of these
                    player.stun = 20 #TODO config this
                    player.ySpeed = -15 # TODO config this too
                    if self.xDirection == Core.Dir.LEFT:
                        player.xSpeed = -5
                    elif self.xDirection == Core.Dir.RIGHT:
                        player.xSpeed = 5
                    # Delete the projectile
                    self.projectile.collided = False
                    self.projectile.kill()
