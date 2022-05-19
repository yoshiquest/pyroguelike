import curses
from entities import Player

def noutrefresh_pad(pad, floor):
	if (floor.max_y - floor.min_y) < curses.LINES-1:
		offset_y = (curses.LINES-floor.max_y+floor.min_y)//2
		new_y = floor.min_y
	else:
		offset_y = 1
		if floor.max_y - Player.instance.y < ((curses.LINES-2)//2):
			new_y = floor.max_y - curses.LINES + 3
		else:
			new_y = Player.instance.y - ((curses.LINES-2)//2)
			if new_y < floor.min_y:
				new_y = floor.min_y
	if (floor.max_x - floor.min_x) < curses.COLS:
		offset_x = (curses.COLS-floor.max_x+floor.min_x)//2
		new_x = floor.min_x
	else:
		offset_x = 0
		if floor.max_x - Player.instance.x  < ((curses.COLS-1)//2):
			new_x = floor.max_x - curses.COLS + 2
		else:
			new_x = Player.instance.x-((curses.COLS-1)//2)
			if new_x < floor.min_x:
				new_x = floor.min_x
	pad.noutrefresh(new_y, new_x, offset_y, offset_x, curses.LINES-2, curses.COLS-1)

def refresh_pad(pad, floor):
	noutrefresh_pad(pad, floor)
	curses.doupdate()

def draw_statusbar(window):
	status = Player.instance.status()
	if(len(status) >= curses.COLS-1):
		status = status[:(curses.COLS-2)]
	window.erase()
	window.addstr(0, 1, status)
	window.noutrefresh()

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
	player = Player.instance
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