"""Core functions and behaviors for Spook Fighters Py"""
from dataclasses import dataclass

import pygame

@dataclass
class Keyset:
    """Keyset representing the character mappings for a player object"""

    LEFT: int
    RIGHT: int
    UP: int
    DOWN: int
    ACTION: int

def collides(spriteA, spriteB):
    """Returns true if sprites arent the same, and if collide_rect returns true"""
    return (spriteA is not spriteB) and (pygame.sprite.collide_rect(spriteA, spriteB))
