from items import Weapon, Armor, weapon_types, armor_types
from constants import STARTING_WEAPON_TYPE, STARTING_WEAPON_MODS, STARTING_ARMOR_TYPE, PLAYER_NAME
from misc import roll, direction, attack_roll

			  #Floor Range,Name,Symbol,level,experience,armor,base damage, % item drop chance
enemy_types = [(range(0, 8), "Bat", "B", 1, 1, 8, (1,2), 0),
			   (range(0, 7), "Emu", "E", 1, 2, 4, (1,2), 0),
			   (range(0, 9), "Hobgoblin", "H", 1, 3, 6, (1,8), 0),
			   (range(0, 10), "Ice Monster", "I", 1, 5, 2, (0,0), 0),
			   (range(0, 6), "Kestral", "K", 1, 1, 4, (1,4), 0),
			   (range(0, 11), "Snake", "S", 1, 2, 6, (1,3), 0),
			   (range(2, 12), "Orc", "O", 1, 5, 5, (1,8), 15),
			   (range(2, 14), "Zombie", "Z", 2, 6, 3, (1,8), 0),
			   (range(3, 13), "Rattlesnake", "R", 2, 9, 8, (1,6), 0),
			   (range(5, 15), "Leprechaun", "L", 3, 10, 3, (1,1), 0),
			   (range(6, 16), "Centaur", "C", 4, 17, 7, (1,2,1,5,1,5), 15),
			   (range(7, 17), "Aquator", "A", 5, 20, 9, (0,0,0,0), 0),
			   (range(8, 18), "Quagga", "Q", 3, 15, 8, (1,5,1,5), 0),
			   (range(9, 19), "Nymph", "N", 3, 37, 2, (0,0), 100),
			   (range(10, 20), "Yeti", "Y", 4, 50, 5, (1,6,1,6), 30),
			   (range(11, 21), "Troll", "T", 6, 120, 7, (1,8,1,8,2,6), 50),
			   (range(12, 22), "Wraith", "W", 5, 55, 7, (1,6), 0),
			   #(range(13, 23), "Flytrap", "F", 8, 80, 8, (0,0), 0), #will add later when functionality is better known
			   (range(14, 24), "Phantom", "P", 8, 120, 8, (4,4), 0),
			   (range(15, 25), "Black Unicorn", "U", 7, 190, 13, (1,9,1,9,2,9), 0),
			   (range(16, 26), "Griffin", "G", 13, 2000, 9, (4,3,3,5), 20),
			   (range(17, 1000), "Medusa", "M", 8, 200, 9, (3,4,3,4,2,5), 40),
			   (range(18, 1000), "Xeroc", "X", 7, 100, 4, (4,4), 30),
			   (range(19, 1000), "Vampire", "V", 8, 350, 10, (1,10), 20),
			   (range(20, 1000), "Jabberwock", "J", 15, 3000, 5, (2,12,2,4), 70),
			   (range(21, 1000), "Dragon", "D", 10, 5000, 12, (1,8,1,8,3,10), 100)]

# strength_hmod_table = list(range(-7, 0)) + ([0] * 10) + [1, 1, 2, 2] + ([3] * 10) + [4]
strength_hmod_table = [-7, -6, -5, -4, -3, -2, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4]
# strength_dmod_table = list(range(-7, 0)) + ([0] * 9) + [1, 2, 3, 3, 4, 4] + ([5] * 9) + [6]
strength_dmod_table = [-7, -6, -5, -4, -3, -2, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 3, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6]

class Entity:
	def __init__(self, y, x, start_room, name, symbol, lvl, exp, armor, maxhealth, base_dmg):
		self.y, self.x, self.location, self.name, self.symbol, self.lvl, self.exp, self.armor, self.base_dmg = (y, x, start_room, name, symbol, lvl, exp, armor, base_dmg)
		if(isinstance(maxhealth, tuple)):
			self.maxhealth = roll(*maxhealth)
		else:
			self.maxhealth = maxhealth
		self.health = self.maxhealth
	def draw(self, window):
		window.addch(self.y, self.x, self.symbol)
	@property
	def health(self):
		return self._health
	@health.setter
	def health(self, value):
		self._health = min(self.maxhealth, value)
	@property
	def position(self):
		return (self.y, self.x)
	@property
	def ac(self):
		return 11 - self.armor
	def roll_attacks(self, target):
		for num,sides in zip(self.base_dmg[::2], self.base_dmg[1::2]):
			if(attack_roll(self, target)):
				return roll(num,sides)
		return None
	def hit_mod(self):
		return 0

class Enemy(Entity):
	def __init__(self, y, x, start_room, name, symbol, lvl, exp, armor, base_dmg, carry):
		super().__init__(y, x, start_room, name, symbol, lvl, exp, armor, (lvl, 8), base_dmg)
		if(self.lvl == 1):
			expmod = (self.maxhealth//8)
		else:
			expmod = (self.maxhealth//6)
		if(self.lvl > 9):
			expmod *= 20
		elif(self.lvl > 6):
			expmod *= 4
		self.exp += expmod
		self.carry = carry
	def ai_move_to(self):
			#Don't move if player isn't in the same room
			player = Player.instance
			if(player.location is self.location):
				new_y, new_x = (self.y + direction(player.y, self.y), self.x + direction(player.x, self.x))
				if(new_x == self.location.xwidth):
					new_x = self.location.xwidth-1
				elif(new_x == self.location.x):
					new_x = self.location.x+1
				if(new_y == self.location.yheight):
					new_y = self.location.yheight-1
				elif(new_y == self.location.y):
					new_y = self.location.y+1
				return (new_y, new_x)
			return None

class Player(Entity):
	instance = None
	def __init__(self, y, x, start_room):
		self.strength = 16
		self.maxstrength = 16
		self.inventory = []
		self.eqweapon = Weapon(*weapon_types[STARTING_WEAPON_TYPE], False, *STARTING_WEAPON_MODS)
		self.eqarmor = Armor(*armor_types[STARTING_ARMOR_TYPE])
		self.gold = 0
		self.floor = 0
		self.next_exp = 10
		Player.instance = self
		super().__init__(y, x, start_room, PLAYER_NAME, "@", 1, 0, 1, 12, (1,4))
	def status(self):
		return f"Floor: {self.floor+1} Gold: {self.gold} Hp: {self.health}({self.maxhealth}) Str: {self.strength}({self.maxstrength}) Arm: {self.armor} Level: {self.lvl} Exp: {self.exp}/{self.next_exp}"
	@property
	def exp(self):
		return self._exp
	@exp.setter
	def exp(self, value):
		while(value >= self.next_exp):
			self.lvl+=1
			hpup = roll(1, 10)
			self.maxhealth += hpup
			self.health += hpup
			self.next_exp *= 2
		self._exp = value
	@property
	def armor(self):
		if(self.eqarmor is None):
			return self._armor
		return self._armor + self.eqarmor.armor
	@armor.setter
	def armor(self, value):
		self._armor = value
	def roll_attacks(self, target):
		sdmod = strength_dmod_table[self.strength] if self.strength < len(strength_dmod_table) else strength_dmod_table[-1]
		if(self.eqweapon is None):
			damage = super().roll_attacks(target)
		else:
			damage = self.eqweapon.roll_attacks(self, target)
		if(damage is not None):
			damage += sdmod
		return damage
	def hit_mod(self):
		shmod = strength_hmod_table[self.strength] if self.strength < len(strength_hmod_table) else strength_hmod_table[-1]
		if(self.eqweapon is None):
			return sdmod
		return self.eqweapon.hit_mod + shmod