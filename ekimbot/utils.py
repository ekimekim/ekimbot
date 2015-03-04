
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
