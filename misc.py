from random import randint
import curses

class Log:
	message = ""
	window = None
	@classmethod
	def clear(cls):
		cls.message = ""
	@classmethod
	def draw(cls):
		try:
			cls.window.erase()
			cls.window.addnstr(0, 1, cls.message, cls.window.getmaxyx()[1]-2)
			cls.window.noutrefresh()
		except curses.error as e:
			raise Exception(f"{cls.window}, {cls.message}, {cls.window.getmaxyx()}")
	@classmethod
	def refresh(cls):
		cls.draw()
		curses.doupdate()
	@classmethod
	def crefresh(cls):
		cls.refresh()
		cls.message = ""
	@classmethod
	def lognow(cls, message):
		cls.message = message
		cls.crefresh()

def saferange(a, b):
	return range(b, a+1) if a > b else range(a, b+1)

def make_linefn(y1, x1, y2, x2):
	m = (y2-y1)/(x2-x1)
	b = y1 - m*x1
	def yfn(x):
		return round(m * x + b)
	return yfn

def roll(die, sides):
	return randint(die, sides*die)

def minmax(coll):
	return (min(coll), max(coll))

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

def get_location(locations, y, x):
	for location in locations:
		if (y, x) in location:
			return location
	return None

def attack_roll(attacker, defender):
	atk_roll = roll(1, 20) + 1 + attacker.hit_mod()
	def_val = 20 - attacker.lvl - defender.ac
	return atk_roll >= def_val