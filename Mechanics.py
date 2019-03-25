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
        player.stun = stun

    def update(self, game: "Game"):
        """Updates the entity"""
        self.tick += 1

# Grab attack class
class Grab(Attack):
    """Grab attack object"""

    def __init__(self, player: "Player"):
        super().__init__(player, stun=10)

    def update(self, game: "Game"):
        super().update(game)

        # Create projectile
        if self.tick == 3:

            # Reference config
            cfg = Config.attack.grab()

            # Starting x position and speed (left/right)
            if self.xDirection == Core.Dir.LEFT:
                xPosition = self.rect.left - cfg.width
                speed = -cfg.speed
            else:
                xPosition = self.rect.right
                speed = cfg.speed

            # Create projectile
            game.add_projectiles(main.Projectile(
                pygame.Rect(xPosition, self.rect.top,
                            cfg.width, self.rect.height),
                xSpeed=speed, lifeSpan=cfg.lifeSpan
            ))

        elif self.tick == 10:
            self.kill()

"""
elif self.xDirection == Dir.LEFT:
                game.add_projectiles(Projectile(
                    pygame.Rect(self.rect.left - cfg.width, self.rect.top,
                                cfg.width, self.rect.height),
                    xSpeed=self.xSpeed - cfg.speed, lifeSpan=cfg.lifeSpan
                ))
"""