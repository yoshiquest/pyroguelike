import curses
from globals import FLOOR_HEIGHT, FLOOR_WIDTH, key_directions
import globals
from generation import generate_floor
from screens import *
from items import GroundItem, Armor, Weapon

def drop_item(floor, selection):
	if(any(filter(lambda item: item.position == globals.player.position, floor.items))):
		globals.message = "There's an item in the way! "
	else:
		globals.message = f"Dropped a {globals.player.inventory[selection]}. "
		floor.items.append(GroundItem(globals.player.y, globals.player.x, globals.player.location, *(globals.player.inventory[selection] if isinstance(globals.player.inventory[selection], tuple) else (globals.player.inventory[selection], 1))))
		del globals.player.inventory[selection]

def action_select(floor, selection):
	pass

def wear_item(floor, selection):
	if(isinstance(globals.player.inventory[selection], Armor)):
		if(globals.player.eqarmor is not None):
			globals.player.inventory.append(globals.player.eqarmor)
		globals.player.eqarmor = globals.player.inventory[selection]
		del globals.player.inventory[selection]
	else:
		globals.message += f"Cannot wear a {(globals.player.inventory[selection][0].name if isinstance(globals.player.inventory[selection], tuple) else globals.player.inventory[selection].name)}. "

def wield_item(floor, selection):
	global message
	if(isinstance(globals.player.inventory[selection], Weapon)):
		if(globals.player.eqweapon is not None):
			globals.player.inventory.append(globals.player.eqweapon)
		globals.player.eqweapon = globals.player.inventory[selection]
		del globals.player.inventory[selection]
	else:
		globals.message += f"Cannot wield a {(globals.player.inventory[selection][0].name if isinstance(globals.player.inventory[selection], tuple) else globals.player.inventory[selection].name)}. "

inventory_fns = {ord("i"): action_select,
				 ord("d"): drop_item,
				 ord("W"): wear_item,
				 ord("w"): wield_item}

def main(scrwindow):
	curses.curs_set(0)
	scrwindow.clear()
	gamewindow = curses.newpad(FLOOR_HEIGHT, FLOOR_WIDTH)
	statusbar = scrwindow.subwin(1, curses.COLS, curses.LINES-1, 0)
	messagebar = scrwindow.subwin(1, curses.COLS, 0, 0)
	floor = generate_floor(0)
	globals.floors.append(floor)
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
		globals.floors[globals.player.floor].draw(gamewindow)
		refresh_pad(gamewindow, globals.floors[globals.player.floor])
	while True:
		do_update = False
		key = scrwindow.getch()
		if key == curses.KEY_RESIZE:
			refresh_all()
		elif key == ord("Q"):
			globals.message = "Are you sure you want to quit? (y/n)"
			draw_messagebar(messagebar)
			curses.doupdate()
			globals.message = ""
			while((key:=scrwindow.getch()) != ord("n") and key != ord("N")):
				if(key == ord("y") or key == ord("Y")):
					return
			draw_messagebar(messagebar)
			curses.doupdate()
		elif key == ord(">"):
			if(globals.floors[globals.player.floor].downstairs == globals.player.position):
				globals.player.floor+=1
				if(len(globals.floors) == globals.player.floor):
					globals.floors.append(generate_floor(globals.player.floor))
				floor = globals.floors[globals.player.floor]
				globals.player.location = globals.floors[globals.player.floor].upstairs_room
				globals.player.y,globals.player.x = globals.floors[globals.player.floor].upstairs
				refresh_all()
			else:
				globals.message = "There aren't any stairs going down here!"
				draw_messagebar(messagebar)
				curses.doupdate()
				globals.message = ""
		elif key == ord("<"):
			if(globals.floors[globals.player.floor].upstairs == globals.player.position):
				assert globals.player.floor != 0, "Somehow able to go upstairs on top floor, unexpected error!"
				globals.player.floor-=1
				floor = globals.floors[globals.player.floor]
				globals.player.location = globals.floors[globals.player.floor].downstairs_room
				globals.player.y,globals.player.x = globals.floors[globals.player.floor].downstairs
				refresh_all()
			else:
				globals.message = "There aren't any stairs going up here!"
				draw_messagebar(messagebar)
				curses.doupdate()
				globals.message = ""
		elif key in inventory_fns:
			if(len(globals.player.inventory)==0):
				globals.message = "Your inventory is empty!"
				draw_messagebar(messagebar)
				curses.doupdate()
				globals.message = ""
			else:
				selection = inv_menu(scrwindow)
				if(selection is not None):
					inventory_fns[key](floor, selection)
				refresh_all()
				globals.message = ""
		elif key != -1:
			if key in key_directions:
				do_update = floor.move(globals.player, globals.player.y+key_directions[key][0], globals.player.x+key_directions[key][1])
			elif key == ord("."):
				do_update = True
			elif key == ord("g"):
				do_update = floor.pickup(globals.player)
			if do_update:
				globals.floors[globals.player.floor].tick()
				globals.floors[globals.player.floor].draw_update(gamewindow)
				draw_statusbar(statusbar)
				draw_messagebar(messagebar)
				globals.message = ""
				refresh_pad(gamewindow, floor)
			else:
				draw_messagebar(messagebar)
				curses.doupdate()
				globals.message = ""
		# message = str(key)
		# draw_messagebar(messagebar)
		# curses.doupdate()
		# message = ""

curses.wrapper(main)