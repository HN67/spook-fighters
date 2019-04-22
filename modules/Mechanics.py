"""The mechanics and logic of actual game characters, attacks, classes, etc, and general balance"""

# Import pygame
import pygame

# Import local files
from modules import Base
from modules import Config
from modules import Core

# Import main? not great, but need it for projectile and player
import main

# Constructs an Attack with custom behavior
def Grab(player: "Player"):
    """Returns an Attack with Grab config behavior"""

    # Reference player (different name to prevent masking in callback)
    caster = player

    # Sets a lifespan to a little longer than the projectile
    attack = Base.Attack(
        caster,
        cooldown=Config.attack.grab.cooldown,
        lifeSpan=Config.attack.grab.lifeSpan + 2
    )

    # Reference config
    cfg = Config.attack.grab()

    # Starting x position and speed based on player facings(left/right)
    if player.xDirection == Core.Dir.LEFT:
        xPosition = attack.rect.left - cfg.width
        speed = -cfg.speed
    else:
        xPosition = attack.rect.right
        speed = cfg.speed

    # Create hitstate from config, change vector x based on direction
    hitState = Config.attack.grab.hitState.copy()
    if player.xDirection == Core.Dir.LEFT:
        hitState.vector.x *= -1
    elif player.xDirection == Core.Dir.RIGHT:
        hitState.vector.x *= 1

    # Setup callback for first and only projectile
    def call(projectile, player):
        # Only interact with other players
        if player is not caster: # Caster is from higher scope
            # Hit the player with the hitstate (reference to here ^)
            player.hit(**hitState.mapping()) # hitState is from higher scope
            # Delete projectile
            projectile.kill()

    # Make it follow the caster
    def follow(projectile):
        projectile.rect.x = (((caster.rect.left - cfg.width) if caster.xDirection == Core.Dir.LEFT
                              else caster.rect.right)
                             + speed*projectile.age)
        projectile.rect.y = caster.rect.top

    # Add projectile to be created
    attack.add_projectile(
        main.Projectile(
            pygame.Rect(xPosition, attack.rect.top,
                        cfg.width, attack.rect.height),
            lifeSpan=cfg.lifeSpan,
            callback=call, post=follow,
        ),
        birthTick=1,
    )

    # Return the attack Object
    return attack

# Up grab
def UpGrab(player: "Player"):
    """Creates a grab in the upwards direction"""

    # Reference player (different name to prevent masking in callback)
    caster = player

    # Sets a lifespan to a little longer than the projectile
    attack = Base.Attack(
        caster,
        cooldown=Config.attack.grab.cooldown,
        lifeSpan=Config.attack.grab.lifeSpan + 2
    )

    # Reference config
    cfg = Config.attack.grab()

    # Create hitstate based from config
    hitState = Config.attack.grab.upHitState.copy()

    # Setup callback for first and only projectile
    def call(projectile, player):
        # Only interact with other players
        if player is not caster: # Caster is from higher scope
            # Hit the player with the hitstate (reference to here ^)
            player.hit(**hitState.mapping()) # hitState is from higher scope
            # Delete projectile
            projectile.kill()

    # Make it follow the caster
    def follow(projectile):
        projectile.rect.x = caster.rect.x
        projectile.rect.y = caster.rect.top - cfg.width - cfg.speed*projectile.age

    # Add projectile to be created
    attack.add_projectile(
        main.Projectile(
            pygame.Rect(attack.rect.left, attack.rect.top - cfg.width,
                        attack.rect.width, cfg.width),
            lifeSpan=cfg.lifeSpan,
            callback=call, post=follow,
        ),
        birthTick=1,
    )

    return attack

# Constructs an Attack with custom behavior
def Slash(player: "Player"):
    """Returns an Attack with Sword.basic config behavior"""

    # Reference player (different name to prevent masking in callback)
    caster = player

    # Sets a lifespan to a little longer than the projectile
    attack = Base.Attack(
        caster,
        cooldown=Config.attack.sword.basic.cooldown,
        lifeSpan=Config.attack.sword.basic.lifeSpan + 2
    )

    # Reference config
    cfg = Config.attack.sword.basic()

    # Starting x position and speed based on player facings(left/right)
    if caster.xDirection == Core.Dir.LEFT:
        xPosition = attack.rect.left - cfg.width
        speed = -cfg.xSpeed
    else:
        xPosition = attack.rect.right
        speed = cfg.xSpeed

    # Create hitstate from config, change vector x based on direction
    hitState = Config.attack.sword.basic.hitState.copy()
    if player.xDirection == Core.Dir.LEFT:
        hitState.vector.x = -hitState.vector.x
    elif player.xDirection == Core.Dir.RIGHT:
        hitState.vector.x *= 1

    # Setup callback for first and only projectile
    def call(projectile, player):
        # Only interact with other players
        if player is not caster: # Caster is from higher scope
            # Hit the player with the hitstate (reference to here ^)
            player.hit(**hitState.mapping()) # hitState is from higher scope
            # Delete projectile
            projectile.kill()

    # Add projectile to be created
    attack.add_projectile(
        main.Projectile(
            pygame.Rect(xPosition, attack.rect.centery - cfg.height/2, # Halfway up the player
                        cfg.width, cfg.height),
            xSpeed=speed + caster.xSpeed, ySpeed=cfg.ySpeed,
            lifeSpan=cfg.lifeSpan,
            callback=call,
        ),
        birthTick=1,
    )

    # Return the attack Object
    return attack
