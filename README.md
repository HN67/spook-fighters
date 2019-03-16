# spook-fighters
A repository for the development of the free open-source game Spook Fighters. This is a hobby project, and is currently under volatile development.

# playing
If you wish to play Spook Fighters, you need Python 3.7+ and Pygame 1.9+ (older versions may or may not work). Clone the repo and then run the main.py file and it should start.

If you have never used Python before, simply install it from https://www.python.org/downloads/release/python-372/ and then open command prompt and run 'pip install pygame'.

# mechanics
Possible Mechanic Designs:

	a) Classic (Spook Fighter X):
	
		-Standard HP (Hits deal damage, upon reaching 0 health, you lose)
		
		-Basic attack
		
		-3 Special Attacks with cooldown
		
	b) Brawlhalla / Smash Bros
	
		-Percentage Damage, more damage taken increases knockback
		
		-Death by being knocked out of arena
		
		-Basic attack and heavy attack that change based on direction
		
	c) New Option 1
	
		-HP, but top part of HP (e.g. 30%) regenerates fairly quickly after not taking damage for a while
		
		-Middle hp (e.g.  middle 50%) regenerates slowly out of combat
		
		-Bottom HP (e.g. bottom 20%) does not regenerate naturally
		
		-Standard Attack (Offensive oriented)
		
		-Shield Attack (Smaller range, damage taken while shield attack active is directed to shield health instead)
		
		-Shield Health (Regenerates extremly fast once out of combat, but only absorbs damage while shield attack is active)
		
		-Ultimate attack (Strong offensive and actives shield), has cooldown (may be signifigant)
