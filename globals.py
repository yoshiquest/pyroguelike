import curses

FLOOR_WIDTH = 100
FLOOR_HEIGHT = 50
MIN_ROOMS = 3
MAX_ROOMS = 9
MIN_ROOM_WIDTH = 5
MAX_ROOM_WIDTH = 20
MIN_ROOM_HEIGHT = 5
MAX_ROOM_HEIGHT = 10
MIN_ENEMIES = 1
MAX_ENEMIES = 4
MIN_THINGS = 0
MAX_THINGS = 5
message = ""
turn = 0
player = None
floors = []
STARTING_WEAPON_TYPE = 0
STARTING_WEAPON_MODS = (1, 1)
STARTING_ARMOR_TYPE = 1

PLAYER_NAME = "Player"

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