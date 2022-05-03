import curses
import random
from random import randint, sample, shuffle, seed

LEVEL_WIDTH = 100
LEVEL_HEIGHT = 50
MIN_ROOMS = 3
MAX_ROOMS = 8
MIN_ROOM_WIDTH = 5
MAX_ROOM_WIDTH = 20
MIN_ROOM_HEIGHT = 5
MAX_ROOM_HEIGHT = 10

def saferange(a, b):
	return range(b, a+1) if a > b else range(a, b+1)
def minmax(coll):
	return (min(coll), max(coll))
class HallwaySegment:
	def __init__(self, y1, x1, y2, x2):
		self.y1 = y1
		self.x1 = x1
		self.y2 = y2
		self.x2 = x2
	def draw(self, window):
		for y in saferange(self.y1, self.y2):
			for x in saferange(self.x1, self.x2):
				window.addch(y, x, curses.ACS_CKBOARD)
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
				return (y in saferange(self.y1, self.y2)) and (x in saferange(self.x1, self.x2))
		return False

def swapxy(t):
	if(len(t) == 4):
		return t[1::-1] + t[:1:-1]
	else:
		return t[::-1]

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
		# window.addstr(self.y+1, self.x+1, str(self))

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
	def move(self, entity, new_y, new_x):
		"Attempts to move entity to new_y, new_x. Returns True if moved successfully, False otherwise."
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
					entity.y = new_y
					entity.x = new_x
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
	def draw(self, window):
		for room in self.rooms:
			room.draw(window)
		for hallway in self.hallways:
			hallway.draw(window)

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
	room1 = sample(list(rooms), 1)[0]
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
			room1 = sample(list(rooms), 1)[0]
			room2 = None
			unconnected_rooms.remove(room1.tuple())
			num_iter = 0
			for room in rooms:
				room.hallwaydoors = {}
		if(room2 is None):
			room2tuple = sample(list(unconnected_rooms), 1)[0]
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

def generate_level():
	rooms = generate_rooms()
	while((hallways := generate_hallways(rooms)) is None):
		rooms = generate_rooms()
	return Level(rooms, hallways)

key_directions = {curses.KEY_UP: (-1, 0),
				  curses.KEY_DOWN: (1, 0),
				  curses.KEY_LEFT: (0, -1),
				  curses.KEY_RIGHT: (0, 1),
				  # curses.KEY_SR: (-1, 1), #Shift Up
				  # curses.KEY_SF: (1, -1), #Shift Down
				  # curses.KEY_SLEFT: (-1, -1),
				  # curses.KEY_SRIGHT: (1, 1)
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
	gamewindow = curses.newpad(LEVEL_HEIGHT, LEVEL_WIDTH)
	level = generate_level()
	start_room = level.rooms[0]
	player = Player(randint(start_room.y+1, start_room.yheight-1), randint(start_room.x+1, start_room.xwidth-1), start_room)
	level.draw(gamewindow)
	player.draw(gamewindow)
	# gamewindow.border()
	# scrwindow.addstr(0, 0, str(player.location))
	# scrwindow.addstr(1, 0, str((player.y, player.x)))
	scrwindow.noutrefresh()
	refresh_pad(gamewindow, player, level)
	# curses.doupdate()
	while True:
		do_update = False
		key = scrwindow.getch()
		player.location.draw(gamewindow)
		if key == curses.KEY_RESIZE:
			curses.update_lines_cols()
			gamewindow.clear()
			level.draw(gamewindow)
			player.draw(gamewindow)
			scrwindow.noutrefresh()
			refresh_pad(gamewindow, player, level)
			# curses.doupdate()
		elif key in key_directions:
			do_update = level.move(player, player.y+key_directions[key][0], player.x+key_directions[key][1])
		player.draw(gamewindow)
		# scrwindow.addstr(0, 0, str(player.location))
		# scrwindow.addstr(0, 0, str(player.location))
		scrwindow.erase()
		scrwindow.noutrefresh()
		refresh_pad(gamewindow, player, level)

#seed(1)
# print(random.getstate())
curses.wrapper(main)