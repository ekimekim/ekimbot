
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
