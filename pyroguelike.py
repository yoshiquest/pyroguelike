import curses
from random import randint, sample, shuffle

LEVEL_WIDTH = 100
LEVEL_HEIGHT = 100
MIN_ROOMS = 3
MAX_ROOMS = 8
MIN_ROOM_WIDTH = 5
MAX_ROOM_WIDTH = 20
MIN_ROOM_HEIGHT = 5
MAX_ROOM_HEIGHT = 10

# def saferange(a, b):
# 	return range(b, a+1) if a > b else range(a, b+1)

# class HallwaySegment:
# 	def __init__(self, y1, x1, y2, x2):
# 		self.y1 = y1
# 		self.x1 = x1
# 		self.y2 = y2
# 		self.x2 = x2
# 	def draw(self, window):
# 		for y in saferange(self.y1, self.y2):
# 			for x in saferange(self.x1, self.x2):
# 				window.addch(y, x, curses.ACS_CKBOARD)
# 	def __contains__(self, element):
# 		if(isinstance(element, tuple)):
# 			if(len(element) == 2):
# 				y,x = element
# 				return (y in saferange(self.y1, self.y2)) and (x in saferange(self.x1, self.x2))
# 		return False

#TODO:
#Generate level by creating 3-6(?) randomly sized an located rooms. Delete overlapping rooms, and create hallways to connect them.
#Each of these classes will have a "draw" function to aid in refreshing the screen. By separating it, we can hopefully only redraw what is needed.
#Bounds checking can also be done on a per-room/hallway basis. That way instead of checking the whole map bounds, we only check the respective location's bounds.
#By having each hallway store the rooms they're connected to (and maybe vice-versa), we can also more easily check bounds between a room and hallway.
class Hallway:
	def __init__(self, room1, room2):
		self.room1 = room1
		self.room2 = room2
		self.door1 = None
		self.door2 = None
		self.horizontal = (room1.xwidth + 1 < room2.x or room2.xwidth + 1 < room1.x)
		vertical = (room1.yheight + 1 < room2.y or room2.yheight + 1 < room1.y)
		if self.horizontal and vertical:
			if(randint(0,1) == 0):
				self.horizontal = False
		if self.horizontal:
			if(room1.xwidth < room2.x):
				#Room1 is left of Room2, put door on right of room1, left of room2
				self.door1 = (randint(room1.y+1, room1.yheight-1), room1.xwidth)
				self.door2 = (randint(room2.y+1, room2.yheight-1), room2.x)
				self.midpoint = randint(room1.xwidth+1, room2.x-1)
				while(self.door1 in room1.hallwaydoors):
					self.door1 = (randint(room1.y+1, room1.yheight-1), room1.xwidth)
				while(self.door2 in room2.hallwaydoors):
					self.door2 = (randint(room2.y+1, room2.yheight-1), room2.x)
			else:
				self.door1 = (randint(room1.y+1, room1.yheight-1), room1.x)
				self.door2 = (randint(room2.y+1, room2.yheight-1), room2.xwidth)
				self.midpoint = randint(room2.xwidth+1, room1.x-1)
				while(self.door1 in room1.hallwaydoors):
					self.door1 = (randint(room1.y+1, room1.yheight-1), room1.x)
				while(self.door2 in room2.hallwaydoors):
					self.door2 = (randint(room2.y+1, room2.yheight-1), room2.xwidth)
		elif vertical:
			if(room1.yheight < room2.y):
				self.door1 = (room1.yheight, randint(room1.x+1, room1.xwidth-1))
				self.door2 = (room2.y, randint(room2.x+1, room2.xwidth-1))
				self.midpoint = randint(room1.yheight+1, room2.y-1)
				while(self.door1 in room1.hallwaydoors):
					self.door1 = (room1.yheight, randint(room1.x+1, room1.xwidth-1))
				while(self.door2 in room2.hallwaydoors):
					self.door2 = (room2.y, randint(room2.x+1, room2.xwidth-1))
			else:
				self.door1 = (room1.y, randint(room1.x+1, room1.xwidth-1))
				self.door2 = (room2.yheight, randint(room2.x+1, room2.xwidth-1))
				self.midpoint = randint(room2.yheight+1, room1.y-1)
				while(self.door1 in room1.hallwaydoors):
					self.door1 = (room1.y, randint(room1.x+1, room1.xwidth-1))
				while(self.door2 in room2.hallwaydoors):
					self.door2 = (room2.yheight, randint(room2.x+1, room2.xwidth-1))
		else:
			raise Exception(f"Error! {room1} and {room2} overlap.")
		room1.hallwaydoors[self.door1] = self
		room2.hallwaydoors[self.door2] = self
		self.leftdoor,self.rightdoor = (self.door1,self.door2) if self.door1[1] < self.door2[1] else (self.door2,self.door1)
		self.topdoor,self.bottomdoor = (self.door1,self.door2) if self.door1[0] < self.door2[0] else (self.door2,self.door1)
	# @property
	# def leftdoor(self):
	# 	return self.door1 if self.door1[1] < self.door2[1] else self.door2
	# @property
	# def rightdoor(self):
	# 	return self.door2 if self.door1[1] < self.door2[1] else self.door1
	# @property
	# def topdoor(self):
	# 	return self.door1 if self.door1[0] < self.door2[0] else self.door2
	# @property
	# def bottomdoor(self):
	# 	return self.door2 if self.door1[0] < self.door2[0] else self.door1
	def __repr__(self):
		return f"H({self.door1},{self.door2},{self.midpoint})"
	def __contains__(self, tupple):
		if(len(tupple) == 2):
			y,x = tupple
			if(self.horizontal):
				return (y == self.leftdoor[0] and x < self.midpoint and self.leftdoor[1] < x) \
					or (y == self.rightdoor[0] and self.midpoint < x and x < self.rightdoor[1]) \
					or (x == self.midpoint and  y <= self.bottomdoor[0] and self.topdoor[0] <= y)
			else:
				return (x == self.topdoor[1] and y < self.midpoint and self.topdoor[0] < y) \
					or (x == self.bottomdoor[1] and self.midpoint < y and y < self.bottomdoor[0]) \
					or (y == self.midpoint and x <= self.rightdoor[1] and self.leftdoor[1] <= x)
		return False
	def draw(self, window):
		if(self.midpoint is not None):
			if(self.horizontal):
				#Draw line from first door to mid.
				# leftdoor,rightdoor = (self.door1,self.door2) if self.door1[1] < self.door2[1] else (self.door2,self.door1)
				for i in range(self.leftdoor[1]+1, self.midpoint):
					window.addch(self.leftdoor[0], i, curses.ACS_CKBOARD)
				for i in range(self.midpoint+1, self.rightdoor[1]):
					window.addch(self.rightdoor[0], i, curses.ACS_CKBOARD)
				for i in range(self.topdoor[0], self.bottomdoor[0]+1):
					window.addch(i, self.midpoint, curses.ACS_CKBOARD)
			else:
				# topdoor,bottomdoor = (self.door1,self.door2) if self.door1[0] < self.door2[0] else (self.door2,self.door1)
				for i in range(self.topdoor[0]+1, self.midpoint):
					window.addch(i, self.topdoor[1], curses.ACS_CKBOARD)
				for i in range(self.midpoint+1, self.bottomdoor[0]):
					window.addch(i, self.bottomdoor[1], curses.ACS_CKBOARD)
				for i in range(self.leftdoor[1], self.rightdoor[1]+1):
					window.addch(self.midpoint, i, curses.ACS_CKBOARD)


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
		return f"R({self.y}, {self.x}, {self.height}, {self.width})"
	def tupple(self):
		return (self.y, self.x, self.height, self.width)
	def __eq__(self, other):
		return isinstance(other, Room) and self.x == other.x and self.y == other.y and self.height == other.height and self.width == other.width
	def draw(self, window):
		#First we draw the corners:
		window.addch(self.y, self.x, curses.ACS_ULCORNER)
		window.addch(self.yheight, self.x, curses.ACS_LLCORNER)
		window.addch(self.y, self.xwidth, curses.ACS_URCORNER)
		window.addch(self.yheight, self.xwidth, curses.ACS_LRCORNER)
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
		#Clear interior:
		for y in range(self.y+1, self.yheight):
			for x in range(self.x+1, self.xwidth):
				window.addch(y, x, " ")

class Player:
	def __init__(self, y, x, start_room):
		self.y = y
		self.x = x
		self.location = start_room
	def draw(self, window):
		window.addch(self.y, self.x, "@")

class Level:
	def __init__(self, rooms, hallways):
		self.rooms = rooms
		self.hallways = hallways
	def move(self, entity, new_y, new_x):
		"Attempts to move entity to new_y, new_x. Returns True if moved successfully, False otherwise."
		if(isinstance(entity.location, Room)):
			room = entity.location
			if((new_y < room.yheight and room.y < new_y and new_x < room.xwidth and room.x < new_x) or
				((new_y, new_x) in room.hallwaydoors)):
				entity.y = new_y
				entity.x = new_x
				return True
			elif((entity.y, entity.x) in room.hallwaydoors):
				hallway = room.hallwaydoors[(entity.y, entity.x)]
				if((new_y, new_x) in hallway):
					entity.y = new_y
					entity.x = new_x
					entity.location = hallway
					return True
		elif(isinstance(entity.location, Hallway)):
			hallway = entity.location
			if((new_y, new_x) in hallway):
				entity.y = new_y
				entity.x = new_x
				return True
			elif((new_y, new_x) == hallway.door1 or (new_y, new_x) == hallway.door2):
				entity.y = new_y
				entity.x = new_x
				entity.location = hallway.room1 if (new_y, new_x) == hallway.door1 else hallway.room2
				return True
			else:
				for hall2 in self.hallways:
					if((new_y, new_x) in hall2):
						entity.y = new_y
						entity.x = new_x
						entity.location = hall2
						return True
				for room in self.rooms:
					if((new_y, new_x) in room.hallwaydoors):
						entity.y = new_y
						entity.x = new_x
						entity.location = room
						return True
		return False
	def draw(self, window):
		for room in self.rooms:
			room.draw(window)
		for hallway in self.hallways:
			hallway.draw(window)

def generate_rooms():
	rooms = []
	num_rooms = randint(MIN_ROOMS, MAX_ROOMS)
	current_iter = 0
	while len(rooms) < num_rooms and current_iter < 100:
		for _ in range(len(rooms), num_rooms):
			width = randint(MIN_ROOM_WIDTH, MAX_ROOM_WIDTH)
			height = randint(MIN_ROOM_HEIGHT, MAX_ROOM_HEIGHT)
			rooms.append(Room(randint(0, LEVEL_HEIGHT-height), randint(0, LEVEL_WIDTH-width), height, width))
		#Remove overlap
		original_rooms = rooms[:]
		for room1 in original_rooms:
			for room2 in original_rooms:
				if room1 is not room2 and room1 in rooms and room2 in rooms:
					if not (room1.y > room2.yheight + 1 or room2.y > room1.yheight + 1 or room1.x > room2.xwidth + 1 or room2.x > room1.xwidth + 1):
						#The smaller-sized room is removed (upside: bigger rooms are nice, downside: bigger rooms could have more overlaps)
						# if room2.height + room2.width > room1.height + room1.width:
						# 	rooms.remove(room1)
						# else:
						# 	rooms.remove(room2)
						if(randint(0,1) == 0):
							rooms.remove(room1)
						else:
							rooms.remove(room2)
		current_iter+=1
	return rooms

def check_hallway_intersection(rooms, hallway):
	#TODO: Needs cleaning up, but works for now.
	for room in rooms:
		if(room is not hallway.room1 and room is not hallway.room2):
			leftdoor,rightdoor = (hallway.door1,hallway.door2) if hallway.door1[1] < hallway.door2[1] else (hallway.door2,hallway.door1)
			topdoor,bottomdoor = (hallway.door1,hallway.door2) if hallway.door1[0] < hallway.door2[0] else (hallway.door2,hallway.door1)
			if(hallway.horizontal):
				if not ((hallway.midpoint < room.x or room.xwidth < leftdoor[1] or leftdoor[0] < room.y or room.yheight < leftdoor[0])
					    and (room.xwidth < hallway.midpoint or rightdoor[1] < room.x or rightdoor[0] < room.y or room.yheight < rightdoor[0])
					    and (bottomdoor[0] < room.y or room.yheight < topdoor[0] or room.xwidth < hallway.midpoint or hallway.midpoint < room.x)):
					return room
			else:
				if not ((room.yheight < topdoor[0] or hallway.midpoint < room.y or room.xwidth < topdoor[1] or topdoor[1] < room.x)
					and (room.yheight < hallway.midpoint or bottomdoor[0] < room.y or bottomdoor[1] < room.x or room.xwidth < bottomdoor[1])
					and (rightdoor[1] < room.x or room.xwidth < leftdoor[1] or room.yheight < hallway.midpoint or hallway.midpoint < room.y)):
					return room
	return False

def generate_hallways(rooms):
	num_hallways = len(rooms)
	hallways = []
	unconnected_rooms = {room.tupple() for room in rooms}
	room1 = sample(list(rooms), 1)[0]
	room2 = None
	unconnected_rooms.remove(room1.tupple())
	while(len(unconnected_rooms) != 0):
		room2tuple = sample(list(unconnected_rooms), 1)[0]
		for room in rooms:
			if(room.tupple() == room2tuple):
				room2 = room
		hallway = Hallway(room1, room2)
		collision = check_hallway_intersection(rooms, hallway)
		if(collision):
			del room1.hallwaydoors[hallway.door1]
			del room2.hallwaydoors[hallway.door2]
			if(collision.tupple() in unconnected_rooms):
				room2 = collision
			elif(len(unconnected_rooms)==1):
				room1 = collision
				room2 = list(unconnected_rooms)[0]
			else:
				room2tuple = sample(list(unconnected_rooms), 1)[0]
				for room in rooms:
					if(room.tupple() == room2tuple):
						room2 = room
		else:
			hallways.append(hallway)
			unconnected_rooms.remove(room2.tupple())
			room1 = room2
			room2 = None
	return hallways

	# for _ in range(num_hallways):
	# 	hallway = None
	# 	shuffle(rooms)
	# 	rooms.sort(key=lambda x: len(x.hallwaydoors))
	# 	room1,room2 = rooms[:2]
	# 	hallway = Hallway(room1, room2)
	# 	collision = check_hallway_intersection(rooms, hallway)
	# 	if(collision):
	# 		#Remove the hallway, and try again between the collided room and another room
	# 		del room1.hallwaydoors[hallway.door1]
	# 		del room2.hallwaydoors[hallway.door2]
	# 			# if(randint(0,1) == 0):
	# 			# 	room1 = collision
	# 			# else:
	# 			# 	room2 = collision
	# 	else:
	# 		hallways.append(hallway)
	# return hallways

key_directions = {curses.KEY_UP: (-1, 0),
				  curses.KEY_DOWN: (1, 0),
				  curses.KEY_LEFT: (0, -1),
				  curses.KEY_RIGHT: (0, 1),
				  # curses.KEY_SR: (-1, 1), #Shift Up
				  # curses.KEY_SF: (1, -1), #Shift Down
				  # curses.KEY_SLEFT: (-1, -1),
				  # curses.KEY_SRIGHT: (1, 1)
				  }

def main(scrwindow):
	#For now this simply creates a window full of "a"s, and it should also resize properly.
	#Kill command is currently required to exit.
	#TODO:
	#Use a pad to represent the level, make it.... some size, not sure how big yet.
	#Then if the pad isn't large enough to fit on the screen, center the viewable part of the pad on the player.
	curses.curs_set(0)
	scrwindow.clear()
	global LEVEL_HEIGHT, LEVEL_WIDTH
	LEVEL_HEIGHT = curses.LINES-1
	LEVEL_WIDTH = curses.COLS-2
	rooms = generate_rooms()
	hallways = generate_hallways(rooms)
	start_room = rooms[0]
	player = Player(randint(start_room.y+1, start_room.yheight-1), randint(start_room.x+1, start_room.xwidth-1), start_room)
	level = Level(rooms, hallways)
	level.draw(scrwindow)
	player.draw(scrwindow)
	scrwindow.refresh()
	while True:
		do_update = False
		key = scrwindow.getch()
		player.location.draw(scrwindow)
		if key == curses.KEY_RESIZE:
			curses.update_lines_cols()
			scrwindow.clear()
			level.draw(scrwindow)
			player.draw(scrwindow)
			scrwindow.refresh()
		elif key in key_directions:
			do_update = level.move(player, player.y+key_directions[key][0], player.x+key_directions[key][1])
		player.draw(scrwindow)
		# scrwindow.addstr(0, 0, str(player.location))
		# scrwindow.addstr(1, 0, str((player.y, player.x)))
		scrwindow.refresh()

curses.wrapper(main)