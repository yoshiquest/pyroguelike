#Pyroguelike
This is a simple roguelike I made both for fun and to experiment with Python's curses library.
I used the original Rogue's source as a reference for a few things (such as enemy names/types, damage, and similar number stuff), but the code structure is my own.

Not sure how it will work on non-unix-based platforms e.g. windows, as I'm not sure how well the curses/ncurses library works on there.

To run, just clone the repo and run pyroguelike.py with the python command.

Currently supports:

	- Random floor generation, with previous floors' state retained
	- Player movement, both with the arrow keys and the traditional hjkl keyset (including diagonal movement in the later case)
	- A number of different enemies
	- various weapons and armor, with different damage/armor values
	- a basic combat and leveling system

Currently unimplemented:

	- Other item types
	- Saving
	- more advanced enemy AI and mechanics (currently all enemies only move/attack when in the same room as you)
	- Hidden/revealed rooms/item names
	- Ranged weapons and attacks

Controls:
	
	- hjkl (or arrow keys): left, up, down, and right respectively
	- yubn: upleft, upright, downleft and downright respectively
	- .: wait in place one turn
	- i: shows your current inventory
	- g: picks up an item off the ground
	- d: drops an item
	- w: wields a weapon
	- W: wears armor
	- >: goes down a floor if there are stairs here
	- <: goes up a floor if there are stairs here
	While inventory is open:
		- q: cancel selection
		- Space/Enter: choose selected item