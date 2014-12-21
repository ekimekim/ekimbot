
from ekimbot.main import client, BotPlugin


@client.add_handler(command='PRIVMSG')
def load_plugin(client, msg):
	words = msg.payload.split()
	if len(words) != 3:
		return
	name, command, arg = words
	if not client.matches_nick(name):
		return
	if command != 'load':
		return
	try:
		BotPlugin.load(arg)
	except Exception as ex:
		reply = "Failed to load plugin {!r}: {}: {}".format(arg, type(ex).__name__, ex)
	else:
		reply = "Loaded plugin {!r}".format(arg)
	client.msg(msg.targets, reply)
