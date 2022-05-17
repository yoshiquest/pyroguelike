from random import choice, randint
from misc import roll, attack_roll

weapon_types = [("Mace", (2,4)), ("Long sword", (3,4)), ("Dagger", (1,6)), ("2H sword", (4,4)), ("Spear", (2,3))]
armor_types = [("Leather", 2), ("Ring Mail", 3), ("Studded Leather", 3), ("Scale Mail", 4), ("Chain Mail", 5), ("Splint Mail", 6), ("Banded Mail", 6), ("Plate Mail", 7)]
class Weapon:
	def __init__(self, name, base_dmg, iscursed=False, hit_mod=0, dmg_mod=0):
		self.name, self.base_dmg,  self.iscursed, self.hit_mod, self.dmg_mod,= (name, base_dmg, iscursed, hit_mod, dmg_mod)
	def __repr__(self):
		return f"{'Cursed ' if self.iscursed else ''}{self.name} {'+' if self.hit_mod >= 0 else ''}{self.hit_mod}{'+' if self.dmg_mod >= 0 else ''}{self.dmg_mod}"
	def roll_attacks(self, attacker, target):
		for num,sides in zip(self.base_dmg[::2], self.base_dmg[1::2]):
			if(attack_roll(attacker, target)):
				return roll(num,sides) + self.dmg_mod
		return None

class Armor:
	def __init__(self, name, armor, iscursed=False):
		self.name, self.armor, self.iscursed = (name, armor, iscursed)
	def __repr__(self):
		return f"{self.name} {'+' if self.armor >= 0 else ''}{self.armor}"

class GroundItem:
	def __init__(self, y, x, location, item, amount=1):
		self.y, self.x, self.location, self.item, self.amount = (y, x, location, item, amount)
	@property
	def symbol(self):
		if(isinstance(self.item, Weapon)):
			return ")"
		elif(isinstance(self.item, Armor)):
			return "]"
		else:
			return "_"
	@property
	def position(self):
		return (self.y, self.x)
	def __repr__(self):
		return self.item.name
	def draw(self, window):
		window.addch(self.y, self.x, self.symbol)

def rand_weapon():
	cursed,hmod = False, 0
	r = randint(0,99)
	if(r < 10):
		cursed = True
		hmod -= randint(1,4)
	elif(r < 15):
		hmod += randint(1,4)
	return (Weapon(*choice(weapon_types), cursed, hmod), 1)

def rand_armor():
	armor = Armor(*choice(armor_types))
	r = randint(0,99)
	if(r < 20):
		armor.iscursed = True
		armor.armor -= randint(1,4)
	elif(r < 28):
		armor.armor += randint(1,4)
	return (armor, 1)

rand_item_table = [rand_weapon, rand_armor]

def rand_drop(y, x, location):
	return GroundItem(y, x, location, *(choice(rand_item_table)()))