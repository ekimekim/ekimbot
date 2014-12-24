
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
		def load(arg):
			BotPlugin.load(arg)
			BotPlugin.enable(arg, self.client)
		dispatch = dict(
			load = load,
			unload = BotPlugin.unload,
			reload = BotPlugin.reload,
		)
		if command not in dispatch:
			return
		try:
			dispatch[command](arg)
		except Exception as ex:
			reply = "Failed to load plugin {!r}: {}: {}".format(arg, type(ex).__name__, ex)
		else:
			reply = "Loaded plugin {!r}".format(arg)
		client.msg(msg.targets, reply)

	def cleanup(self):
		self.client.rm_handler(self.load_plugin)
