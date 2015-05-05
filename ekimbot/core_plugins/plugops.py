
from ekimbot.botplugin import BotPlugin, ClientPlugin
from ekimbot.commands import CommandHandler


class PlugopsPlugin(ClientPlugin):
	name = 'plugops'

	def try_operation(self, msg, func, verb, args):
		"""Some common code that reports success/fail to user,
		or lets errors raise if not called as part of handling a message (if msg is None)."""
		success = set()
		past_verb = verb.rstrip('e') + 'ed' # yeah this is nowhere near complete, but close enough
		for arg in args:
			self.logger.debug("{} {}".format(verb, arg))
			try:
				func(arg)
			except Exception as ex:
				self.logger.warning("Failed to {} plugin {!r}".format(verb, arg), exc_info=True)
				if not msg:
					raise
				self.reply(msg, "Failure to {} plugin {!r} with {}: {}".format(
				                verb, arg, type(ex).__name__, ex))
			else:
				self.logger.info("{} plugin {!r}".format(past_verb.capitalize(), arg))
				success.add(arg)
		if success and msg:
			self.reply(msg, "{} plugin(s): {}".format(past_verb.capitalize(), ', '.join(map(repr, success))))

	@CommandHandler("plugin load", 1)
	def load(self, msg, *modules):
		"""Load a plugin from disk if not already loaded"""
		self.try_operation(msg, BotPlugin.load, "load", modules)

	@CommandHandler("plugin unload", 1)
	def unload(self, msg, *modules):
		"""Globally unload a plugin, disabling any enabled instances"""
		loaded = []
		for module in modules:
			if module in BotPlugin.loaded_by_name:
				loaded.append(module)
			else:
				self.reply(msg, "No such module {!r} is loaded".format(module))
		self.try_operation(msg, BotPlugin.unload, "unload", loaded)

	@CommandHandler("plugin reload", 1)
	def reload(self, msg, *modules):
		"""Unload, then re-load, a plugin. Any instances will be re-enabled."""
		self.try_operation(msg, BotPlugin.reload, "reload", modules)

	def _with_client(self, disable=False):
		"""Returns a function to pass to try_operation that will correctly enable or disable
		plugins, giving them the correct args depending on whether they are a ClientPlugin
		or not."""
		def _with_client_inner(name):
			if disable and name not in BotPlugin.loaded_by_name:
				return
			plugin = BotPlugin.loaded_by_name[name]
			method = 'disable' if disable else 'enable'
			args = (self.client,) if issubclass(plugin, ClientPlugin) else ()
			return getattr(plugin, method)(plugin, *args)
		return _with_client_inner

	@CommandHandler("plugin enable", 1)
	def enable(self, msg, *plugins):
		"""Enable a plugin for this client"""
		self.try_operation(msg, self._with_client(False), "enable", plugins)

	@CommandHandler("plugin disable", 1)
	def disable(self, msg, *plugins):
		"""Disable a plugin for this client"""
		self.try_operation(msg, self._with_client(True), "disable", plugins)
