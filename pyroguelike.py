import curses
from constants import FLOOR_HEIGHT, FLOOR_WIDTH
from generation import generate_floor
from screens import *
from items import GroundItem, Armor, Weapon
from floors import Floor
from entities import Player
from misc import Log
from random import choice

def drop_item(player, floor, selection):
	if(any(filter(lambda item: item.position == player.position, floor.items))):
		Log.message = "There's an item in the way! "
	else:
		Log.message = f"Dropped a {player.inventory[selection]}. "
		floor.items.append(GroundItem(player.y, player.x, player.location, *(player.inventory[selection] if isinstance(player.inventory[selection], tuple) else (player.inventory[selection], 1))))
		del player.inventory[selection]

def action_select(player, floor, selection):
	pass

def wear_item(player, floor, selection):
	if(isinstance(player.inventory[selection], Armor)):
		if(player.eqarmor is not None):
			player.inventory.append(player.eqarmor)
		player.eqarmor = player.inventory[selection]
		del player.inventory[selection]
	else:
		Log.message += f"Cannot wear a {(player.inventory[selection][0].name if isinstance(player.inventory[selection], tuple) else player.inventory[selection].name)}. "

def wield_item(player, floor, selection):
	if(isinstance(player.inventory[selection], Weapon)):
		if(player.eqweapon is not None):
			player.inventory.append(player.eqweapon)
		player.eqweapon = player.inventory[selection]
		del player.inventory[selection]
	else:
		Log.message += f"Cannot wield a {(player.inventory[selection][0].name if isinstance(player.inventory[selection], tuple) else player.inventory[selection].name)}. "

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

inventory_fns = {ord("i"): action_select,
				 ord("d"): drop_item,
				 ord("W"): wear_item,
				 ord("w"): wield_item}

def main(scrwindow):
	curses.curs_set(0)
	scrwindow.clear()
	gamewindow = curses.newpad(FLOOR_HEIGHT, FLOOR_WIDTH)
	statusbar = scrwindow.subwin(1, curses.COLS, curses.LINES-1, 0)
	Log.window = scrwindow.subwin(1, curses.COLS, 0, 0)
	floor = generate_floor(0)
	player = None
	while(player is None):
		start_room = choice(floor.rooms)
		position = start_room.randposition()
		if (position!=floor.downstairs and not any(map(lambda x: x.position == position, floor.items)) and not any(map(lambda x: x.position == position, floor.enemies))):
			player = Player(*position, start_room)
	floor.draw(gamewindow)
	scrwindow.noutrefresh()
	draw_statusbar(statusbar)
	Log.draw()
	refresh_pad(gamewindow, floor)
	def refresh_all():
		curses.update_lines_cols()
		statusbar.resize(1, curses.COLS)
		statusbar.mvwin(curses.LINES-1, 0)
		Log.window.resize(1, curses.COLS)
		gamewindow.erase()
		scrwindow.erase()
		scrwindow.noutrefresh()
		draw_statusbar(statusbar)
		Log.draw()
		floor.draw(gamewindow)
		refresh_pad(gamewindow, floor)
	while True:
		do_update = False
		key = scrwindow.getch()
		if key == curses.KEY_RESIZE:
			refresh_all()
		elif key == ord("Q"):
			Log.lognow("Are you sure you want to quit? (y/n)")
			while((key:=scrwindow.getch()) != ord("n") and key != ord("N")):
				if(key == ord("y") or key == ord("Y")):
					return
			Log.refresh()
		elif key == ord(">"):
			if(floor.downstairs == player.position):
				player.floor+=1
				while(len(Floor.floors) <= player.floor):
					generate_floor(player.floor)
				floor = Floor.floors[player.floor]
				player.location = Floor.floors[player.floor].upstairs_room
				player.y,player.x = Floor.floors[player.floor].upstairs
				refresh_all()
			else:
				Log.lognow("There aren't any stairs going down here!")
		elif key == ord("<"):
			if(floor.upstairs == player.position):
				assert player.floor != 0, "Somehow able to go upstairs on top floor, unexpected error!"
				player.floor-=1
				floor = Floor.floors[player.floor]
				player.location = floor.downstairs_room
				player.y,player.x = floor.downstairs
				refresh_all()
			else:
				Log.lognow("There aren't any stairs going up here!")
		elif key in inventory_fns:
			if(len(player.inventory)==0):
				Log.lognow("Your inventory is empty!")
			else:
				selection = inv_menu(scrwindow)
				if(selection is not None):
					inventory_fns[key](player, floor, selection)
				refresh_all()
				Log.clear()
		elif key != -1:
			if key in key_directions:
				do_update = floor.move(player, player.y+key_directions[key][0], player.x+key_directions[key][1])
			elif key == ord("."):
				do_update = True
			elif key == ord("g"):
				do_update = floor.pickup(player)
			if do_update:
				floor.tick()
				floor.draw_update(gamewindow)
				draw_statusbar(statusbar)
				Log.draw()
				refresh_pad(gamewindow, floor)
				Log.clear()
			else:
				Log.crefresh()

curses.wrapper(main)