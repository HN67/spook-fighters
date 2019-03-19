"""Core functions and behaviors for Spook Fighters Py"""
from dataclasses import dataclass

@dataclass
class Keyset:
    """Keyset representing the character mappings for a player object"""
    
    LEFT: int
    RIGHT: int
    UP: int
    DOWN: int
    ACTION: int
