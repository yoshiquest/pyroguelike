import curses
import random
from random import randint, sample, shuffle, seed, choices, choice
from abc import ABC, abstractmethod
from math import copysign

LEVEL_WIDTH = 100
LEVEL_HEIGHT = 50
MIN_ROOMS = 3
MAX_ROOMS = 9
MIN_ROOM_WIDTH = 5
MAX_ROOM_WIDTH = 20
MIN_ROOM_HEIGHT = 5
MAX_ROOM_HEIGHT = 10
MIN_ENEMIES = 3
MAX_ENEMIES = 3
message = ""
turn = 0

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

#TODO:
#Generate level by creating 3-6(?) randomly sized an located rooms. Delete overlapping rooms, and create hallways to connect them.
#Each of these classes will have a "draw" function to aid in refreshing the screen. By separating it, we can hopefully only redraw what is needed.
#Bounds checking can also be done on a per-room/hallway basis. That way instead of checking the whole map bounds, we only check the respective location's bounds.
#By having each hallway store the rooms they're connected to (and maybe vice-versa), we can also more easily check bounds between a room and hallway.
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
		return f"{self.name} {'+' if self.hit_mod >= 0 else ''}{self.hit_mod}{'+' if self.dmg_mod >= 0 else ''}{self.dmg_mod}"
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
	def __repr__(self):
		return f"{self.item} @ ({self.y},{self.x})"
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
	def ai_move_to(self, player):
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
		self.eqweapon = Weapon(*weapon_types[STARTING_WEAPON_TYPE], *STARTING_WEAPON_MODS)
		self.eqarmor = Armor(*armor_types[STARTING_ARMOR_TYPE])
		self.gold = 0
		self.floor = 1
		self.next_exp = 10
		super().__init__(y, x, start_room, PLAYER_NAME, "@", 1, 0, 1, 12, (1,4))
	def status(self):
		return f"Floor: {self.floor} Gold: {self.gold} Hp: {self.health}({self.maxhealth}) Str: {self.strength}({self.maxstrength}) Arm: {self.armor} Level: {self.lvl} Exp: {self.exp}/{self.next_exp}"
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

enemy_types = [(range(1, 9), "Bat", "B", 1, 1, 2, (1,2))]

class Level:
	def __init__(self, rooms, hallways, player, enemies=[], items=[]):
		self.rooms = rooms
		self.hallways = hallways
		self.player = player
		self.enemies = enemies
		self.items = items
		self.locations_to_update = [player.location]
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
		"Attempts to move entity to new_y, new_x. Returns True if moved or attacked successfully, False otherwise."
		if(entity is not self.player and (new_y, new_x) == self.player.position):
			self.attack(entity, self.player)
			return True
		for enemy in self.enemies:
			if(enemy.position == (new_y, new_x)):
				if(entity is self.player):
					#TODO: Add attack code here.
					self.attack(entity, enemy)
					return True
				else:
					return False
		result = self._move_sub(entity, new_y, new_x)
		if(result and entity.location not in self.locations_to_update):
			self.locations_to_update.append(entity.location)
		return result
	def attack(self, entity1, entity2):
		global message
		if(attack_roll(entity1, entity2)):
			damage = entity1.roll_damage()
			message += f"{entity1.name} hit {entity2.name} for {damage} damage! "
			entity2.health -= damage
			if(entity2.health <= 0):
				if(entity1 is self.player):
					entity1.exp+=entity2.exp
					message = f"{entity1.name} slew {entity2.name}."
				elif(entity2 is self.player):
					#Easy way to implement death for now.
					raise Exception("You died!")
				self.enemies.remove(entity2)
		else:
			message += f"{entity1.name} missed {entity2.name}! "
	def draw_update(self, window):
		for location in self.locations_to_update:
			location.draw(window)
			for enemy in self.enemies:
				if enemy.location is location:
					enemy.draw(window)
		self.player.draw(window)
		self.locations_to_update = [self.player.location]
	def regen_hp(self, entity):
		if entity.lvl <= 7:
			if(turn % (21 - (entity.lvl * 2)) == 0):
				entity.health+=1
		elif turn % 3 == 0:
			entity.health+=randint(1, entity.lvl - 7)
	def tick(self):
		global turn
		for enemy in self.enemies:
			target_location = enemy.ai_move_to(self.player)
			if(target_location is not None and target_location != enemy.position):
				result = self.move(enemy, *target_location)

		self.regen_hp(self.player)
		turn+=1
	def draw(self, window):
		for room in self.rooms:
			room.draw(window)
		for hallway in self.hallways:
			hallway.draw(window)
		for enemy in self.enemies:
			enemy.draw(window)
		self.player.draw(window)

def generate_rooms():
	rooms = []
	num_rooms = randint(MIN_ROOMS, MAX_ROOMS)
	current_iter = 0
	while len(rooms) < num_rooms:
		for _ in range(len(rooms), num_rooms):
			width = randint(MIN_ROOM_WIDTH, MAX_ROOM_WIDTH)
			height = randint(MIN_ROOM_HEIGHT, MAX_ROOM_HEIGHT)
			rooms.append(Room(randint(0, LEVEL_HEIGHT-height-1), randint(0, LEVEL_WIDTH-width-1), height, width))
		#Remove overlap
		original_rooms = rooms[:]
		for room1 in original_rooms:
			for room2 in original_rooms:
				if room1 is not room2 and room1 in rooms and room2 in rooms:
					if not (room1.y > room2.yheight + 1 or room2.y > room1.yheight + 1 or room1.x > room2.xwidth + 1 or room2.x > room1.xwidth + 1):
						if(randint(0,1) == 0):
							rooms.remove(room1)
						else:
							rooms.remove(room2)
		current_iter+=1
		if current_iter > 100:
			rooms = []
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

def generate_enemies(rooms, hallways, floor, player):
	num_enemies = randint(MIN_ENEMIES, MAX_ENEMIES)
	valid_enemy_types = list(map(lambda x: x[1:], filter(lambda x: floor in x[0], enemy_types)))
	enemy_rooms = []
	enemy_coordinates = []
	for _ in range(num_enemies):
		room = choice(rooms)
		x = randint(room.x+1, room.xwidth-1)
		y = randint(room.y+1, room.yheight-1)
		while((y,x) in enemy_coordinates or (y,x) == player.position):
			room = choice(rooms)
			x = randint(room.x+1, room.xwidth-1)
			y = randint(room.y+1, room.yheight-1)
		enemy_coordinates.append((y,x))
		enemy_rooms.append(room)
	respective_enemy_types = choices(valid_enemy_types, k=num_enemies)
	enemies = []
	for i in range(num_enemies):
		enemies.append(Enemy(*enemy_coordinates[i], enemy_rooms[i], *respective_enemy_types[i]))
	return enemies

def generate_level(floor, player=None):
	rooms = generate_rooms()
	while((hallways := generate_hallways(rooms)) is None):
		rooms = generate_rooms()
	if(player is None):
		start_room = rooms[0]
		player = Player(randint(start_room.y+1, start_room.yheight-1), randint(start_room.x+1, start_room.xwidth-1), start_room)
	enemies = generate_enemies(rooms, hallways, floor, player)
	return Level(rooms, hallways, player, enemies)

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

def noutrefresh_pad(pad, player, level):
	if (level.max_y - level.min_y) < curses.LINES-1:
		offset_y = (curses.LINES-level.max_y+level.min_y)//2
		new_y = level.min_y
	else:
		offset_y = 1
		if level.max_y - player.y < ((curses.LINES-2)//2):
			new_y = level.max_y - curses.LINES + 3
		else:
			new_y = player.y - ((curses.LINES-2)//2)
			if new_y < level.min_y:
				new_y = level.min_y
	if (level.max_x - level.min_x) < curses.COLS:
		offset_x = (curses.COLS-level.max_x+level.min_x)//2
		new_x = level.min_x
	else:
		offset_x = 0
		if level.max_x - player.x  < ((curses.COLS-1)//2):
			new_x = level.max_x - curses.COLS + 2
		else:
			new_x = player.x-((curses.COLS-1)//2)
			if new_x < level.min_x:
				new_x = level.min_x
	pad.noutrefresh(new_y, new_x, offset_y, offset_x, curses.LINES-2, curses.COLS-1)

def refresh_pad(pad, player, level):
	noutrefresh_pad(pad, player, level)
	curses.doupdate()

def draw_statusbar(window, player):
	status = player.status()
	if(len(status) >= curses.COLS-1):
		status = status[:(curses.COLS-2)]
	window.erase()
	window.addstr(0, 1, status)
	window.noutrefresh()

def draw_messagebar(window):
	global message
	drawmessage = message
	if(len(drawmessage) >= curses.COLS-1):
		drawmessage = drawmessage[:(curses.COLS-2)]
	window.erase()
	window.addstr(0, 1, drawmessage)
	window.noutrefresh()
	# message = ""
def main(scrwindow):
	#For now this simply creates a window full of "a"s, and it should also resize properly.
	#Kill command is currently required to exit.
	#TODO:
	#Use a pad to represent the level, make it.... some size, not sure how big yet.
	#Then if the pad isn't large enough to fit on the screen, center the viewable part of the pad on the player.
	curses.curs_set(0)
	scrwindow.clear()
	# global LEVEL_HEIGHT, LEVEL_WIDTH
	# LEVEL_HEIGHT = curses.LINES-1
	# LEVEL_WIDTH = curses.COLS-2
	# for room in rooms:
	# 	room.draw(scrwindow)
	# scrwindow.refresh()
	# scrwindow.getch()
	global message
	gamewindow = curses.newpad(LEVEL_HEIGHT, LEVEL_WIDTH)
	statusbar = scrwindow.subwin(1, curses.COLS, curses.LINES-1, 0)
	messagebar = scrwindow.subwin(1, curses.COLS, 0, 0)
	level = generate_level(1)
	player = level.player
	level.draw(gamewindow)
	# gamewindow.border()
	# scrwindow.addstr(0, 0, str(player.location))
	# scrwindow.addstr(1, 0, str((player.y, player.x)))
	scrwindow.noutrefresh()
	draw_statusbar(statusbar, player)
	draw_messagebar(messagebar)
	refresh_pad(gamewindow, player, level)
	# curses.doupdate()
	while True:
		do_update = False
		key = scrwindow.getch()
		if key == curses.KEY_RESIZE:
			curses.update_lines_cols()
			statusbar = scrwindow.subwin(1, curses.COLS, curses.LINES-1, 0)
			messagebar = scrwindow.subwin(1, curses.COLS, 0, 0)
			gamewindow.erase()
			scrwindow.erase()
			level.draw(gamewindow)
			draw_statusbar(statusbar, player)
			draw_messagebar(messagebar)
			scrwindow.noutrefresh()
			refresh_pad(gamewindow, player, level)
			# curses.doupdate()
		elif key in key_directions:
			do_update = level.move(player, player.y+key_directions[key][0], player.x+key_directions[key][1])
		elif key == ord("."):
			do_update = True
		if key != -1 and do_update:
			level.tick()
			level.draw_update(gamewindow)
			# scrwindow.addstr(0, 0, str(player.location))
			# scrwindow.addstr(0, 0, str(player.location))
			scrwindow.erase()
			scrwindow.noutrefresh()
			draw_messagebar(messagebar)
			draw_statusbar(statusbar, player)
			refresh_pad(gamewindow, player, level)
			message = ""

#seed(1)
# print(random.getstate())
curses.wrapper(main)