
from ekimbot.botplugin import BotPlugin, CommandHandler


class PlugopsPlugin(BotPlugin):
	name = 'plugops'

	def try_operation(self, msg, func, verb, args):
		"""Some common code that reports success/fail to user,
		or lets errors raise if not called as part of handling a message (if msg is None)."""
		success = set()
		past_verb = verb.rstrip('e') + 'ed' # yeah this is nowhere near complete, but close enough
		for arg in args:
			try:
				func(arg)
			except Exception as ex:
				self.logger.warning("Failed to {} plugin {!r}".format(verb, arg), exc_info=True)
				if not msg:
					raise
				self.reply(msg, "Failure to {} plugin {!r} with {}: {}".format(
				                verb, arg, type(ex).__name__, ex))
			else:
				success.add(arg)
				self.logger.info("{} plugin {!r}".format(past_verb.capitalize(), arg))
		if success and msg:
			self.reply(msg, "{} plugin(s): {}".format(past_verb.capitalize(), ', '.join(map(repr, success))))

	@CommandHandler("plugin load", 1)
	def load(self, msg, *modules):
		self.try_operation(msg, BotPlugin.load, "load", modules)

	@CommandHandler("plugin unload", 1)
	def unload(self, msg, *modules):
		self.try_operation(msg, BotPlugin.unload, "unload", modules)

	@CommandHandler("plugin reload", 1)
	def reload(self, msg, *modules):
		self.try_operation(msg, BotPlugin.reload, "reload", modules)

	@CommandHandler("plugin enable", 1)
	def enable(self, msg, *modules):
		self.try_operation(msg, lambda name: BotPlugin.enable(name, self.client), "enable", modules)

	@CommandHandler("plugin disable", 1)
	def disable(self, msg, *modules):
		self.try_operation(msg, lambda name: BotPlugin.disable(name, self.client), "disable", modules)

