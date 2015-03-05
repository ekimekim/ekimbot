
import os

from girc import Privmsg


def reply(client, msg, text):
	"""Reply a PRIVMSG to a given msg's sender, or to the whole channel if msg was a PRIVMSG to a channel."""
	client.msg(reply_target(client, msg), text)


def reply_target(client, msg):
	"""For a given msg, return the appropriate target to send replies to:
		channel if msg is PRIVMSG to a channel (aka. target is not us)
		otherwise sender
	"""
	if isinstance(msg, Privmsg) and not client.matches_nick(msg.target):
		return msg.target
	else:
		return msg.sender


def list_modules(path):
	"""Returns a list of python module files in path (.py files or folders containing __init__.py).
	Ignores files with leading '_' character."""
	ret = []
	for name in os.listdir(path):
		if name.startswith('_'):
			continue
		fullname = os.path.join(path, name)
		if os.path.isdir(fullname):
			if os.path.exists(os.path.join(fullname, '__init__.py')):
				ret.append(name)
		elif name.endswith('.py'):
			ret.append(name[:-3])
	return ret


def pretty_interval(interval):
	"""Returns a human-readable description of a time interval"""

	if interval < 0:
		return "-" + pretty_interval(-interval)

	AVG_YEAR = 365.2425
	# list of (unit name, number of previous unit in 1 of this unit)
	# note the hacky use of average months/years, which in this case is close enough
	UNITS = [
		('seconds', 1),
		('minutes', 60),
		('hours', 60),
		('days', 24),
		('weeks', 7),
		('months', AVG_YEAR/12/7),
		('years', AVG_YEAR),
	]
	SCALE_UP_CUTOFF = 1.75

	name = None
	for new_name, factor in UNITS:
		new_interval = interval / factor
		if new_interval <= SCALE_UP_CUTOFF:
			break
		interval = new_interval
		name = new_name

	if name is None:
		# special case for seconds <= SCALE_UP_CUTOFF: print as float instead
		interval = "{:.2f}".format(interval)
		name = 'seconds'
	else:
		# round interval
		interval = int(round(interval))
	return "{} {}".format(interval, name)
