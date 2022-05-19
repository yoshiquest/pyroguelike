from random import choice, choices, randint

from constants import MIN_ROOMS, MAX_ROOMS, MIN_ROOM_WIDTH, \
 MIN_ROOM_HEIGHT, MAX_ROOM_WIDTH, MAX_ROOM_HEIGHT, FLOOR_HEIGHT, \
 FLOOR_WIDTH, MIN_THINGS, MAX_THINGS, MIN_ENEMIES, MAX_ENEMIES
from items import rand_drop
from floors import Room, Hallway, Floor
from entities import enemy_types, Enemy
from misc import Log

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
		while(position in enemy_coordinates):
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
	base_room = Floor.floors[floor_number-1].downstairs_room if floor_number > 0 else None
	hallways = None
	while(hallways is None):
		initial_room = Room(base_room.y, base_room.x, base_room.height, base_room.width) if base_room is not None else None
		rooms = generate_rooms(initial_room)
		hallways = generate_hallways(rooms)
	items = generate_items(rooms)
	enemies = generate_enemies(rooms, hallways, floor_number)
	upstairs_room = initial_room
	upstairs = Floor.floors[floor_number-1].downstairs if floor_number > 0 else None
	downstairs_room = choice(rooms)
	while((downstairs:=downstairs_room.randposition())==upstairs or any(map(lambda x: x.position == downstairs, items)) or any(map(lambda x: x.position == downstairs, enemies))):
		downstairs_room = choice(rooms)
	return Floor(rooms, hallways, upstairs, upstairs_room, downstairs, downstairs_room, enemies, items)
