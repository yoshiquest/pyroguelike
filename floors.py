import curses
from random import randint

from misc import saferange, swapxy, make_linefn
import globals

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
		self.locations_to_update = [(globals.player.location if upstairs_room is None else upstairs_room)]
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
		if(entity is not globals.player and (new_y, new_x) == globals.player.position):
			self.attack(entity, globals.player)
			return True
		for enemy in self.enemies:
			if(enemy.position == (new_y, new_x)):
				if(entity is globals.player):
					#TODO: Add attack code here.
					self.attack(entity, enemy)
					return True
				else:
					return False
		result = self._move_sub(entity, new_y, new_x)
		if(result and entity.location not in self.locations_to_update):
			self.locations_to_update.append(entity.location)
		if(result and entity is globals.player):
			for item in self.items:
				if(entity.position == item.position):
					globals.message = f"You see a {item} on the ground. "
			if(entity.position == self.upstairs):
				globals.message += "You see a staircase going up here. "
			elif(entity.position == self.downstairs):
				globals.message += "You see a staircase going down here. "
		return result
	def pickup(self, entity):
		for item in self.items:
			if(item.position == entity.position):
				if(item.amount == 1):
					entity.inventory.append(item.item)
				else:
					entity.inventory.append((item.item, item.amount))
				self.items.remove(item)
				globals.message = f"Picked up a {item}. "
				return True
		globals.message = "There's nothing here. "
		return False
	def attack(self, entity1, entity2):
		damage = entity1.roll_attacks(entity2)
		if(damage is not None):
			globals.message += f"{entity1.name} hit {entity2.name} for {damage} damage! "
			entity2.health -= damage
			if(entity2.health <= 0):
				if(entity1 is globals.player):
					entity1.exp+=entity2.exp
					globals.message = f"{entity1.name} slew {entity2.name}. "
					if(randint(0,99) < entity2.carry and (not any(map(lambda i: (entity2.y, entity2.x) == i.position, self.items)))):
						self.items.append(rand_drop(entity2.y, entity2.x, entity2.location))
				elif(entity2 is globals.player):
					#Easy way to implement death for now.
					raise Exception("You died!")
				self.enemies.remove(entity2)
		else:
			globals.message += f"{entity1.name} missed {entity2.name}! "
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
		globals.player.draw(window)
		self.locations_to_update = [globals.player.location]
	def regen_hp(self, entity):
		if entity.lvl <= 7:
			if(globals.turn % (21 - (entity.lvl * 2)) == 0):
				entity.health+=1
		elif globals.turn % 3 == 0:
			entity.health+=randint(1, entity.lvl - 7)
	def tick(self):
		global turn
		for enemy in self.enemies:
			target_location = enemy.ai_move_to()
			if(target_location is not None and target_location != enemy.position):
				result = self.move(enemy, *target_location)
		self.regen_hp(globals.player)
		globals.turn+=1
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
		globals.player.draw(window)