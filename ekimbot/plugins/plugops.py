
from ekimbot.main import BotPlugin


class PlugopsPlugin(BotPlugin):
	name = 'plugops'

	def init(self):
		self.client.add_handler(self.load_plugin, command='PRIVMSG')

	def load_plugin(self, client, msg):
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
			BotPlugin.enable(arg, self.client)
		except Exception as ex:
			reply = "Failed to load plugin {!r}: {}: {}".format(arg, type(ex).__name__, ex)
		else:
			reply = "Loaded plugin {!r}".format(arg)
		client.msg(msg.targets, reply)

	def cleanup(self):
		self.client.rm_handler(self.load_plugin)
