import curses
import random
from random import randint, sample, shuffle, seed, choices, choice
from abc import ABC, abstractmethod
from math import copysign

FLOOR_WIDTH = 100
FLOOR_HEIGHT = 50
MIN_ROOMS = 3
MAX_ROOMS = 9
MIN_ROOM_WIDTH = 5
MAX_ROOM_WIDTH = 20
MIN_ROOM_HEIGHT = 5
MAX_ROOM_HEIGHT = 10
MIN_ENEMIES = 3
MAX_ENEMIES = 9
MIN_THINGS = 3
MAX_THINGS = 9
message = ""
turn = 0
player = None
floors = []

def roll(die, sides):
	return randint(die, sides*die)
def saferange(a, b):
	return range(b, a+1) if a > b else range(a, b+1)
def minmax(coll):
	return (min(coll), max(coll))

def make_linefn(y1, x1, y2, x2):
	m = (y2-y1)/(x2-x1)
	b = y1 - m*x1
	def yfn(x):
		return round(m * x + b)
	return yfn

class HallwaySegment:
	def __init__(self, y1, x1, y2, x2):
		self.y1 = y1
		self.x1 = x1
		self.y2 = y2
		self.x2 = x2
	def draw(self, window):
		if(self.y1 == self.y2):
			for x in saferange(self.x1, self.x2):
				window.addch(self.y1, x, curses.ACS_CKBOARD)
		elif(self.x1 == self.x2):
			for y in saferange(self.y1, self.y2):
				window.addch(y, self.x1, curses.ACS_CKBOARD)
		else:
			yfn = make_linefn(self.y1, self.x1, self.y2, self.x2)
			for x in saferange(self.x1, self.x2):
				window.addch(yfn(x), x, curses.ACS_CKBOARD)
	@property
	def xmin(self):
		return self.x1 if self.x1 < self.x2 else self.x2
	@property
	def xmax(self):
		return self.x2 if self.x1 < self.x2 else self.x1
	@property
	def ymin(self):
		return self.y1 if self.y1 < self.y2 else self.y2
	@property
	def ymax(self):
		return self.y2 if self.y1 < self.y2 else self.y1
	def __repr__(self):
		return f"({self.y1}, {self.x1}) <-> ({self.y2}, {self.x2})"
	def __contains__(self, element):
		if(isinstance(element, tuple)):
			if(len(element) == 2):
				y,x = element
				if(self.x1 == self.x2 or self.y1 == self.y2):
					return (y in saferange(self.y1, self.y2)) and (x in saferange(self.x1, self.x2))
				else:
					yfn = make_linefn(self.y1, self.x1, self.y2, self.x2)
					return (y == yfn(x))

		return False

def swapxy(t):
	if(len(t) == 4):
		return t[1::-1] + t[:1:-1]
	else:
		return t[::-1]

def direction(x1, x2):
	if x1-x2 == 0:
		return 0
	if x1-x2 < 0:
		return -1
	return 1

class Hallway:
	def __init__(self, room1, room2):
		self.room1 = room1
		self.room2 = room2
		horizontal = (self.room1.xwidth + 1 < self.room2.x or self.room2.xwidth + 1 < self.room1.x)
		vertical = (self.room1.yheight + 1 < self.room2.y or self.room2.yheight + 1 < self.room1.y)
		if horizontal and vertical:
			if(randint(0,1) == 0):
				vertical = False
		if not (horizontal or vertical):
			raise Exception(f"Error! {self.room1} and {self.room2} overlap.")
		t1,t2 = (self.room1.tuple(),self.room2.tuple())
		if vertical:
			t1,t2 = (swapxy(t1), swapxy(t2))
		if(t1[3] > t2[1]):
			self.room1, self.room2 = (self.room2, self.room1)
			t1, t2 = (t2, t1)
		door1 = (randint(t1[0]+1, t1[2]-1), t1[3])
		door2 = (randint(t2[0]+1, t2[2]-1), t2[1])
		while (door1[::-1] if vertical else door1) in self.room1.hallwaydoors or (door2[::-1] if vertical else door2) in self.room2.hallwaydoors:
			door1 = (randint(t1[0]+1, t1[2]-1), t1[3])
			door2 = (randint(t2[0]+1, t2[2]-1), t2[1])
		midpoint = randint(t1[3]+1, t2[1]-1)
		point1 = (door1[0], door1[1] + 1)
		point2 = (door2[0], door2[1] - 1)
		pointm1 = (door1[0], midpoint)
		pointm2 = (door2[0], midpoint)
		if vertical:
			door1,door2,point1,point2,pointm1,pointm2 = [x[::-1] for x in (door1, door2, point1, point2, pointm1, pointm2)]
		self.seg1 = HallwaySegment(point1[0], point1[1], pointm1[0], pointm1[1])
		self.seg2 = HallwaySegment(pointm2[0], pointm2[1], point2[0], point2[1])
		self.segmid = HallwaySegment(pointm1[0], pointm1[1], pointm2[0], pointm2[1])
		self.door1 = door1
		self.door2 = door2
		if self.room1 == room2:
			self.room1, self.room2, self.door1, self.door2 = (self.room2, self.room1, self.door2, self.door1)
		assert door1 not in self.room1.hallwaydoors and door1 not in self.room2.hallwaydoors and door2 not in self.room1.hallwaydoors and door2 not in self.room2.hallwaydoors
		self.room1.hallwaydoors[self.door1] = self
		self.room2.hallwaydoors[self.door2] = self
	def __repr__(self):
		return f"H({self.seg1},{self.segmid},{self.seg2})"
	def __contains__(self, element):
		return (element in self.seg1 or element in self.seg2 or element in self.segmid)
	def draw(self, window):
		self.seg1.draw(window)
		self.segmid.draw(window)
		self.seg2.draw(window)

class Room:
	def __init__(self, y, x, height, width):
		self.y, self.x, self.height, self.width = y, x, height, width
		self.hallwaydoors = {}
	@property
	def xwidth(self):
		return self.x + self.width
	@property
	def yheight(self):
		return self.y + self.height
	def __repr__(self):
		return f"R({self.y}, {self.x}, {self.yheight}, {self.xwidth})"
	def tuple(self):
		return (self.y, self.x, self.yheight, self.xwidth)
	def __eq__(self, other):
		return isinstance(other, Room) and self.x == other.x and self.y == other.y and self.height == other.height and self.width == other.width
	def __contains__(self, element):
		if isinstance(element, Hallway):
			return (element.seg1 in self or element.seg2 in self or element.segmid in self)
		elif isinstance(element, HallwaySegment):
			tminy, tminx = (max(element.ymin, self.y), max(element.xmin, self.x))
			tmaxy, tmaxx = (min(element.ymax, self.yheight), min(element.xmax, self.xwidth))
			return (not (tminx > tmaxx or tmaxy > tminy))
		elif isinstance(element, tuple):
			if(len(element) == 2):
				return (element[0] in range(self.y+1, self.yheight)) and (element[1] in range(self.x+1, self.xwidth))
		return False
	def randposition(self):
		return (randint(self.y+1, self.yheight-1), randint(self.x+1, self.xwidth-1))
	def draw(self, window):
		#Clear interior:
		for y in range(self.y+1, self.yheight):
			for x in range(self.x+1, self.xwidth):
				window.addch(y, x, " ")
		#First we draw the corners:
		try:
			window.addch(self.y, self.x, curses.ACS_ULCORNER)
			window.addch(self.yheight, self.x, curses.ACS_LLCORNER)
			window.addch(self.y, self.xwidth, curses.ACS_URCORNER)
			window.addch(self.yheight, self.xwidth, curses.ACS_LRCORNER)
		except curses.error as e:
			raise Exception(str(self))
		#Draw horizontal lines:
		for i in range(self.x+1,self.xwidth):
			window.addch(self.y, i, curses.ACS_HLINE)
			window.addch(self.yheight, i, curses.ACS_HLINE)
		#And vertical lines:
		for i in range(self.y+1,self.yheight):
			window.addch(i, self.x, curses.ACS_VLINE)
			window.addch(i, self.xwidth, curses.ACS_VLINE)
		#Add the doors:
		for door in self.hallwaydoors.keys():
			window.addch(door[0], door[1], "+")

weapon_types = [("Mace", (2,4)), ("Long sword", (3,4)), ("Dagger", (1,6)), ("2H sword", (4,4)), ("Spear", (2,3))]
armor_types = [("Leather", 2), ("Ring Mail", 3), ("Studded Leather", 3), ("Scale Mail", 4), ("Chain Mail", 5), ("Splint Mail", 6), ("Banded Mail", 6), ("Plate Mail", 7)]
STARTING_WEAPON_TYPE = 0
STARTING_WEAPON_MODS = (1, 1)
STARTING_ARMOR_TYPE = 1

class Weapon:
	def __init__(self, name, base_dmg, iscursed=False, hit_mod=0, dmg_mod=0):
		self.name, self.base_dmg,  self.iscursed, self.hit_mod, self.dmg_mod,= (name, base_dmg, iscursed, hit_mod, dmg_mod)
	def __repr__(self):
		return f"{'Cursed ' if self.iscursed else ''}{self.name} {'+' if self.hit_mod >= 0 else ''}{self.hit_mod}{'+' if self.dmg_mod >= 0 else ''}{self.dmg_mod}"
	def roll_damage(self):
		return roll(*self.base_dmg)+self.dmg_mod

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
	def roll_damage(self):
		return roll(*self.base_dmg)
	def hit_mod(self):
		return 0

class Enemy(Entity):
	def __init__(self, y, x, start_room, name, symbol, lvl, exp, armor, base_dmg):
		super().__init__(y, x, start_room, name, symbol, lvl, exp, armor, (lvl, 8), base_dmg)
	def ai_move_to(self):
			#Don't move if player isn't in the same room
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

PLAYER_NAME = "Player"

# strength_hmod_table = list(range(-7, 0)) + ([0] * 10) + [1, 1, 2, 2] + ([3] * 10) + [4]
strength_hmod_table = [-7, -6, -5, -4, -3, -2, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4]
# strength_dmod_table = list(range(-7, 0)) + ([0] * 9) + [1, 2, 3, 3, 4, 4] + ([5] * 9) + [6]
strength_dmod_table = [-7, -6, -5, -4, -3, -2, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 3, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6]

class Player(Entity):
	def __init__(self, y, x, start_room):
		self.strength = 16
		self.maxstrength = 16
		self.inventory = []
		self.eqweapon = Weapon(*weapon_types[STARTING_WEAPON_TYPE], False, *STARTING_WEAPON_MODS)
		self.eqarmor = Armor(*armor_types[STARTING_ARMOR_TYPE])
		self.gold = 0
		self.floor = 0
		self.next_exp = 10
		super().__init__(y, x, start_room, PLAYER_NAME, "@", 1, 0, 1, 12, (1,4))
	def status(self):
		return f"Floor: {self.floor+1} Gold: {self.gold} Hp: {self.health}({self.maxhealth}) Str: {self.strength}({self.maxstrength}) Arm: {self.armor} Level: {self.lvl} Exp: {self.exp}/{self.next_exp}"
	@property
	def exp(self):
		return self._exp
	@exp.setter
	def exp(self, value):
		if(value >= self.next_exp):
			self.lvl+=1
			self.next_exp*=2
		self._exp = value
	@property
	def armor(self):
		if(self.eqarmor is None):
			return self._armor
		return self._armor + self.eqarmor.armor
	@armor.setter
	def armor(self, value):
		self._armor = value
	def roll_damage(self):
		sdmod = strength_dmod_table[self.strength] if self.strength < len(strength_dmod_table) else strength_dmod_table[-1]
		if(self.eqweapon is None):
			return super().roll_damage() + sdmod
		return self.eqweapon.roll_damage() +sdmod
	def hit_mod(self):
		shmod = strength_hmod_table[self.strength] if self.strength < len(strength_hmod_table) else strength_hmod_table[-1]
		if(self.eqweapon is None):
			return sdmod
		return self.eqweapon.hit_mod + shmod

def attack_roll(attacker, defender):
	atk_roll = roll(1, 20) + 1 + attacker.hit_mod()
	def_val = 20 - attacker.lvl - defender.ac
	return atk_roll >= def_val

enemy_types = [(range(0, 8), "Bat", "B", 1, 1, 2, (1,2))]

def get_location(locations, y, x):
	for location in locations:
		if (y, x) in location:
			return location
	return None

class Floor:
	def __init__(self, rooms, hallways, upstairs, upstairs_room, downstairs, downstairs_room, enemies=[], items=[]):
		self.rooms = rooms
		self.hallways = hallways
		self.enemies = enemies
		self.items = items
		self.upstairs_room = upstairs_room
		self.upstairs = upstairs
		self.downstairs_room = downstairs_room
		self.downstairs = downstairs
		self.locations_to_update = [(player.location if upstairs_room is None else upstairs_room)]
	@property
	def min_x(self):
		return min(self.rooms, key=lambda r: r.x).x
	@property
	def min_y(self):
		return min(self.rooms, key=lambda r: r.y).y
	@property
	def max_x(self):
		return max(self.rooms, key=Room.xwidth.fget).xwidth
	@property
	def max_y(self):
		return max(self.rooms, key=Room.yheight.fget).yheight
	def _move_sub(self, entity, new_y, new_x):
		new_coords = (new_y, new_x)
		if(isinstance(entity.location, Room)):
			room = entity.location
			if((new_y < room.yheight and room.y < new_y and new_x < room.xwidth and room.x < new_x) or
				(new_coords in room.hallwaydoors)):
				entity.y, entity.x = new_coords
				return True
			elif((entity.y, entity.x) in room.hallwaydoors):
				hallway = room.hallwaydoors[(entity.y, entity.x)]
				if(new_coords in hallway):
					entity.y, entity.x = new_coords
					entity.location = hallway
					return True
		elif(isinstance(entity.location, Hallway)):
			hallway = entity.location
			if(new_coords in hallway):
				entity.y, entity.x = new_coords
				return True
			elif(new_coords == hallway.door1 or new_coords == hallway.door2):
				entity.y, entity.x = new_coords
				entity.location = hallway.room1 if new_coords == hallway.door1 else hallway.room2
				return True
			else:
				for hall2 in self.hallways:
					if(new_coords in hall2):
						entity.y, entity.x = new_coords
						entity.location = hall2
						return True
				for room in self.rooms:
					if(new_coords in room.hallwaydoors):
						entity.y, entity.x = new_coords
						entity.location = room
						return True
		return False
	def move(self, entity, new_y, new_x):
		"Attempts to move entity to new_y, new_x. Returns True if time passed, False otherwise."
		if(entity is not player and (new_y, new_x) == player.position):
			self.attack(entity, player)
			return True
		for enemy in self.enemies:
			if(enemy.position == (new_y, new_x)):
				if(entity is player):
					#TODO: Add attack code here.
					self.attack(entity, enemy)
					return True
				else:
					return False
		result = self._move_sub(entity, new_y, new_x)
		if(result and entity.location not in self.locations_to_update):
			self.locations_to_update.append(entity.location)
		if(result and entity is player):
			for item in self.items:
				if(entity.position == item.position):
					global message
					message = f"You see a {item} on the ground. "
			if(entity.position == self.upstairs):
				message += "You see a staircase going up here. "
			elif(entity.position == self.downstairs):
				message += "You see a staircase going down here. "
		return result
	def pickup(self, entity):
		global message
		for item in self.items:
			if(item.position == entity.position):
				if(item.amount == 1):
					entity.inventory.append(item.item)
				else:
					entity.inventory.append((item.item, item.amount))
				self.items.remove(item)
				message = f"Picked up a {item}. "
				return True
		message = "There's nothing here. "
		return False
	def attack(self, entity1, entity2):
		global message
		if(attack_roll(entity1, entity2)):
			damage = entity1.roll_damage()
			message += f"{entity1.name} hit {entity2.name} for {damage} damage! "
			entity2.health -= damage
			if(entity2.health <= 0):
				if(entity1 is player):
					entity1.exp+=entity2.exp
					message = f"{entity1.name} slew {entity2.name}. "
				elif(entity2 is player):
					#Easy way to implement death for now.
					raise Exception("You died!")
				self.enemies.remove(entity2)
		else:
			message += f"{entity1.name} missed {entity2.name}! "
	def draw_update(self, window):
		for location in self.locations_to_update:
			location.draw(window)
			if(self.upstairs_room is location):
				window.addch(*self.upstairs, "<")
			if(self.downstairs_room is location):
				window.addch(*self.downstairs, ">")
			for item in self.items:
				if item.location is location:
					item.draw(window)
			for enemy in self.enemies:
				if enemy.location is location:
					enemy.draw(window)
		player.draw(window)
		self.locations_to_update = [player.location]
	def regen_hp(self, entity):
		if entity.lvl <= 7:
			if(turn % (21 - (entity.lvl * 2)) == 0):
				entity.health+=1
		elif turn % 3 == 0:
			entity.health+=randint(1, entity.lvl - 7)
	def tick(self):
		global turn
		for enemy in self.enemies:
			target_location = enemy.ai_move_to()
			if(target_location is not None and target_location != enemy.position):
				result = self.move(enemy, *target_location)
		self.regen_hp(player)
		turn+=1
	def draw(self, window):
		for room in self.rooms:
			room.draw(window)
		for hallway in self.hallways:
			hallway.draw(window)
		if(self.upstairs is not None):
			window.addch(*self.upstairs, "<")
		if(self.downstairs is not None):
			window.addch(*self.downstairs, ">")
		for item in self.items:
			item.draw(window)
		for enemy in self.enemies:
			enemy.draw(window)
		player.draw(window)

def generate_rooms(initial_room=None):
	rooms = []
	if(initial_room is not None):
		rooms.append(initial_room)
	num_rooms = randint(MIN_ROOMS, MAX_ROOMS)
	current_iter = 0
	while len(rooms) < num_rooms:
		for _ in range(len(rooms), num_rooms):
			width = randint(MIN_ROOM_WIDTH, MAX_ROOM_WIDTH)
			height = randint(MIN_ROOM_HEIGHT, MAX_ROOM_HEIGHT)
			rooms.append(Room(randint(0, FLOOR_HEIGHT-height-1), randint(0, FLOOR_WIDTH-width-1), height, width))
		#Remove overlap
		original_rooms = rooms[:]
		for room1 in original_rooms:
			for room2 in original_rooms:
				if room1 is not room2 and room1 in rooms and room2 in rooms:
					if not (room1.y > room2.yheight + 1 or room2.y > room1.yheight + 1 or room1.x > room2.xwidth + 1 or room2.x > room1.xwidth + 1):
						if(room2 is initial_room or (room1 is not initial_room and randint(0,1) == 0)):
							rooms.remove(room1)
						else:
							rooms.remove(room2)
		current_iter+=1
		if current_iter > 100:
			rooms = []
			if(initial_room is not None):
				rooms.append(initial_room)
			current_iter = 0
	return rooms

def check_hallway_intersection(rooms, hallway):
	for room in rooms:
		if(room is not hallway.room1 and room is not hallway.room2):
			if hallway in room:
				return room
	return False

def generate_hallways(rooms):
	hallways = []
	unconnected_rooms = {room.tuple() for room in rooms}
	room1 = choice(list(rooms))
	room2 = None
	unconnected_rooms.remove(room1.tuple())
	meta_iter = 0
	num_iter = 0
	while(len(unconnected_rooms) != 0):
		if(num_iter > 100):
			meta_iter+=1
			if meta_iter > 100:
				return None
			hallways = []
			unconnected_rooms = {room.tuple() for room in rooms}
			room1 = choice(list(rooms))
			room2 = None
			unconnected_rooms.remove(room1.tuple())
			num_iter = 0
			for room in rooms:
				room.hallwaydoors = {}
		if(room2 is None):
			room2tuple = choice(list(unconnected_rooms))
			for room in rooms:
				if(room.tuple() == room2tuple):
					room2 = room
			assert room2.tuple() == room2tuple, "room 2 not found"
		hallway = Hallway(room1, room2)
		collision = check_hallway_intersection(rooms, hallway)
		if(collision):
			del room1.hallwaydoors[hallway.door1]
			del room2.hallwaydoors[hallway.door2]
			if(collision.tuple() in unconnected_rooms):
				room2 = collision
			else:
				room1 = collision
				room2 = None
		else:
			hallways.append(hallway)
			unconnected_rooms.remove(room2.tuple())
			room1 = room2
			room2 = None
		num_iter+=1
	return hallways

def generate_items(rooms):
	item_locations = set()
	num_items = randint(MIN_THINGS, MAX_THINGS)
	while(len(item_locations) < num_items):
		roomnum = randint(0, len(rooms)-1)
		item_locations.add((*rooms[roomnum].randposition(), roomnum))
	return [rand_drop(y,x,rooms[roomnum]) for y,x,roomnum in list(item_locations)]

def generate_enemies(rooms, hallways, floor):
	num_enemies = randint(MIN_ENEMIES, MAX_ENEMIES)
	valid_enemy_types = list(map(lambda x: x[1:], filter(lambda x: floor in x[0], enemy_types)))
	if(valid_enemy_types == []):
		return []
	enemy_rooms = []
	enemy_coordinates = []
	for _ in range(num_enemies):
		room = choice(rooms)
		position = room.randposition()
		while(position in enemy_coordinates or position == player.position):
			room = choice(rooms)
			position = room.randposition()
		enemy_coordinates.append(position)
		enemy_rooms.append(room)
	respective_enemy_types = choices(valid_enemy_types, k=num_enemies)
	enemies = []
	for i in range(num_enemies):
		enemies.append(Enemy(*enemy_coordinates[i], enemy_rooms[i], *respective_enemy_types[i]))
	return enemies

def generate_floor(floor_number):
	global player
	if player is None:
		initial_room = None
	else:
		initial_room = Room(player.location.y, player.location.x, player.location.height, player.location.width)
	rooms = generate_rooms(initial_room)
	while((hallways := generate_hallways(rooms)) is None):
		rooms = generate_rooms(initial_room)
	if(player is None):
		start_room = rooms[0]
		player = Player(*start_room.randposition(), start_room)
	items = generate_items(rooms)
	enemies = generate_enemies(rooms, hallways, floor_number)
	upstairs_room = initial_room if floor_number > 0 else None
	upstairs = player.position if floor_number > 0 else None
	downstairs_room = choice(rooms)
	while((downstairs:=downstairs_room.randposition())==upstairs or any(map(lambda x: x.position == downstairs, items)) or any(map(lambda x: x.position == downstairs, enemies))):
		pass
	return Floor(rooms, hallways, upstairs, upstairs_room, downstairs, downstairs_room, enemies, items)

key_directions = {curses.KEY_UP: (-1, 0),
				  curses.KEY_DOWN: (1, 0),
				  curses.KEY_LEFT: (0, -1),
				  curses.KEY_RIGHT: (0, 1),
				  # curses.KEY_SR: (-1, 1), #Shift Up
				  # curses.KEY_SF: (1, -1), #Shift Down
				  # curses.KEY_SLEFT: (-1, -1),
				  # curses.KEY_SRIGHT: (1, 1)
				  121: (-1, -1), #y
				  117: (-1, 1), #u
				  98: (1, -1), #b
				  110: (1, 1), #n
				  104: (0, -1), #h
				  106: (-1, 0), #j
				  107: (1, 0), #k
				  108: (0, 1) #l
				  }

def noutrefresh_pad(pad, floor):
	if (floor.max_y - floor.min_y) < curses.LINES-1:
		offset_y = (curses.LINES-floor.max_y+floor.min_y)//2
		new_y = floor.min_y
	else:
		offset_y = 1
		if floor.max_y - player.y < ((curses.LINES-2)//2):
			new_y = floor.max_y - curses.LINES + 3
		else:
			new_y = player.y - ((curses.LINES-2)//2)
			if new_y < floor.min_y:
				new_y = floor.min_y
	if (floor.max_x - floor.min_x) < curses.COLS:
		offset_x = (curses.COLS-floor.max_x+floor.min_x)//2
		new_x = floor.min_x
	else:
		offset_x = 0
		if floor.max_x - player.x  < ((curses.COLS-1)//2):
			new_x = floor.max_x - curses.COLS + 2
		else:
			new_x = player.x-((curses.COLS-1)//2)
			if new_x < floor.min_x:
				new_x = floor.min_x
	pad.noutrefresh(new_y, new_x, offset_y, offset_x, curses.LINES-2, curses.COLS-1)

def refresh_pad(pad, floor):
	noutrefresh_pad(pad, floor)
	curses.doupdate()

def draw_statusbar(window):
	status = player.status()
	if(len(status) >= curses.COLS-1):
		status = status[:(curses.COLS-2)]
	window.erase()
	window.addstr(0, 1, status)
	window.noutrefresh()

def draw_messagebar(window):
	# if(len(drawmessage) >= curses.COLS-1):
	# 	drawmessage = drawmessage[:(curses.COLS-2)]
	window.erase()
	window.addnstr(0, 1, message, curses.COLS-1)
	window.noutrefresh()
	# message = ""

def draw_inv_menu(window, inventory, selection):
	lines, cols = window.getmaxyx()
	if selection < lines//2:
		start_index = 0
	elif len(inventory) - selection < lines//2:
		start_index = len(inventory) - lines
	else:
		start_index = selection - lines//2
	for i in range(lines):
		invi = i + start_index
		if(invi >= len(inventory)):
			return
		if(invi == selection):
			window.addnstr(i, 0, str(inventory[invi]), cols, curses.A_STANDOUT)
		else:
			window.addnstr(i, 0, str(inventory[invi]), cols)

def inv_menu(window):
	key = None
	window.erase()
	invwindow = window.subwin(curses.LINES-1, curses.COLS-3, 1, 0)
	selection = 0
	draw_inv_menu(invwindow, player.inventory, selection)
	invwindow.refresh()
	while ((key:=window.getch())!=ord(" ") and (key != ord("\n"))):
		if(key == curses.KEY_RESIZE):
			curses.update_lines_cols()
			invwindow = window.subwin(curses.LINES-1, curses.COLS-3, 1, 0)
		elif((key == curses.KEY_UP or key == 106) and selection > 0):
			selection-=1
		elif((key == curses.KEY_DOWN or key == 107) and selection < len(player.inventory) - 1):
			selection+=1
		elif(key == 9 or key == ord("q")):
			return None
		invwindow.erase()
		draw_inv_menu(invwindow, player.inventory, selection)
		invwindow.refresh()
	return selection

def drop_item(floor, selection):
	global message
	if(any(filter(lambda item: item.position == player.position, floor.items))):
		message = "There's an item in the way! "
	else:
		message = f"Dropped a {player.inventory[selection]}. "
		floor.items.append(GroundItem(player.y, player.x, player.location, *(player.inventory[selection] if isinstance(player.inventory[selection], tuple) else (player.inventory[selection], 1))))
		del player.inventory[selection]

def action_select(floor, selection):
	pass

def wear_item(floor, selection):
	global message
	if(isinstance(player.inventory[selection], Armor)):
		if(player.eqarmor is not None):
			player.inventory.append(player.eqarmor)
		player.eqarmor = player.inventory[selection]
		del player.inventory[selection]
	else:
		message += f"Cannot wear a {(player.inventory[selection][0].name if isinstance(player.inventory[selection], tuple) else player.inventory[selection].name)}. "

def wield_item(floor, selection):
	global message
	if(isinstance(player.inventory[selection], Weapon)):
		if(player.eqweapon is not None):
			player.inventory.append(player.eqweapon)
		player.eqweapon = player.inventory[selection]
		del player.inventory[selection]
	else:
		message += f"Cannot wield a {(player.inventory[selection][0].name if isinstance(player.inventory[selection], tuple) else player.inventory[selection].name)}. "

inventory_fns = {ord("i"): action_select,
				 ord("d"): drop_item,
				 ord("W"): wear_item,
				 ord("w"): wield_item}

def main(scrwindow):
	curses.curs_set(0)
	scrwindow.clear()
	global message
	gamewindow = curses.newpad(FLOOR_HEIGHT, FLOOR_WIDTH)
	statusbar = scrwindow.subwin(1, curses.COLS, curses.LINES-1, 0)
	messagebar = scrwindow.subwin(1, curses.COLS, 0, 0)
	floor = generate_floor(0)
	floors.append(floor)
	floor.draw(gamewindow)
	scrwindow.noutrefresh()
	draw_statusbar(statusbar)
	draw_messagebar(messagebar)
	refresh_pad(gamewindow, floor)
	def refresh_all():
		curses.update_lines_cols()
		statusbar.resize(1, curses.COLS)
		statusbar.mvwin(curses.LINES-1, 0)
		messagebar.resize(1, curses.COLS)
		gamewindow.erase()
		scrwindow.erase()
		scrwindow.noutrefresh()
		draw_statusbar(statusbar)
		draw_messagebar(messagebar)
		floors[player.floor].draw(gamewindow)
		refresh_pad(gamewindow, floors[player.floor])
	while True:
		do_update = False
		key = scrwindow.getch()
		if key == curses.KEY_RESIZE:
			refresh_all()
		elif key == ord("Q"):
			message = "Are you sure you want to quit? (y/n)"
			draw_messagebar(messagebar)
			curses.doupdate()
			message = ""
			while((key:=scrwindow.getch()) != ord("n") and key != ord("N")):
				if(key == ord("y") or key == ord("Y")):
					return
			draw_messagebar(messagebar)
			curses.doupdate()
		elif key == ord(">"):
			if(floors[player.floor].downstairs == player.position):
				player.floor+=1
				if(len(floors) == player.floor):
					floors.append(generate_floor(player.floor))
				floor = floors[player.floor]
				player.location = floors[player.floor].upstairs_room
				player.y,player.x = floors[player.floor].upstairs
				refresh_all()
			else:
				message = "There aren't any stairs going down here!"
				draw_messagebar(messagebar)
				curses.doupdate()
				message = ""
		elif key == ord("<"):
			if(floors[player.floor].upstairs == player.position):
				assert player.floor != 0, "Somehow able to go upstairs on top floor, unexpected error!"
				player.floor-=1
				floor = floors[player.floor]
				player.location = floors[player.floor].downstairs_room
				player.y,player.x = floors[player.floor].downstairs
				refresh_all()
			else:
				message = "There aren't any stairs going up here!"
				draw_messagebar(messagebar)
				curses.doupdate()
				message = ""
		elif key in inventory_fns:
			if(len(player.inventory)==0):
				message = "Your inventory is empty!"
				draw_messagebar(messagebar)
				curses.doupdate()
				message = ""
			else:
				selection = inv_menu(scrwindow)
				if(selection is not None):
					inventory_fns[key](floor, selection)
				refresh_all()
				message = ""
		elif key != -1:
			if key in key_directions:
				do_update = floor.move(player, player.y+key_directions[key][0], player.x+key_directions[key][1])
			elif key == ord("."):
				do_update = True
			elif key == ord("g"):
				do_update = floor.pickup(player)
			if do_update:
				floors[player.floor].tick()
				floors[player.floor].draw_update(gamewindow)
				draw_statusbar(statusbar)
				draw_messagebar(messagebar)
				message = ""
				refresh_pad(gamewindow, floor)
			else:
				draw_messagebar(messagebar)
				curses.doupdate()
				message = ""
		# message = str(key)
		# draw_messagebar(messagebar)
		# curses.doupdate()
		# message = ""

curses.wrapper(main)