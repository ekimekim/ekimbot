
from plugins import Plugin
from classtricks import classproperty, dotdict

from girc import Handler, Channel

from ekimbot import utils
from ekimbot.commands import CommandHandler
from ekimbot.config import config
from ekimbot.store import Store


class BotPlugin(Plugin):
	"""Generic plugin. You should only use this if your plugin does not use a specific irc client instance."""
	defaults = {}

	@classproperty
	def load_paths(cls):
		return config.plugin_paths

	def __init__(self, *args):
		super(BotPlugin, self).__init__(*args)
		self.logger = self.get_logger()
		self.init()

	def init(self):
		"""Called when plugin is enabled."""
		pass

	def get_logger(self):
		# lazy import to break cyclic dependency
		from ekimbot.main import main_logger
		return main_logger.getChild(self.name)

	@property
	def config(self):
		"""Returns config for this plugin, which should be a dict of the plugin's name inside the main config.
		Uses defaults from the "defaults" attr.
		Returned object is a dotdict.
		"""
		d = dotdict(self.defaults)
		d.update(config.get(self.name, {}))
		return d

	@property
	def _store(self):
		"""Return actual store object.
		We save a reference after first access to keep it alive for the lifetime of the plugin,
		even though Store has singleton semantics."""
		self.__store = Store(config.store_path)
		return self.__store

	@property
	def store(self):
		"""Dict which will be persisted to disk when save_store() is called."""
		return self._store.data.setdefault(self.name, {})

	def save_store(self):
		self._store.save()


class ClientPlugin(BotPlugin):
	"""Plugins that interact with a client.
	Plugins may either define handlers on methods (which will automatically register to the client
	when the plugin is enabled), or define handlers on self.client in init().
	Default cleanup() will automatically unregister handlers that were automatically registered.
	"""

	def __init__(self, client, *args):
		self.client = client
		super(ClientPlugin, self).__init__(client, *args)
		Handler.register_all(client, self)
		client.stop_handlers.add(lambda client: self.cleanup())

	def get_logger(self):
		return self.client.logger.getChild(self.name)

	def cleanup(self):
		"""Called on disable. Should clean up any ongoing operations. The default one unregisters
		methods that are Handlers."""
		Handler.unregister_all(self.client, self)

	def reply(self, msg, text):
		utils.reply(self.client, msg, text)

	@property
	def config(self):
		"""As BotHandler but also searches for config under plugin name inside client's config"""
		d = super(ClientPlugin, self).config
		d.update(self.client.config.get(self.name, {}))
		return d

	@property
	def store(self):
		"""As bothandler but additionally indexes by client name"""
		return super(ClientPlugin, self).store.setdefault(self.client.name, {})


class ChannelPlugin(ClientPlugin):
	"""Plugins that interact with and maintain per-channel state.
	Mostly the same as ClientPlugin. You should use ChannelCommandHandlers to automatically
	restrict commands to the context of the target channel."""

	def __init__(self, client, channel, *args):
		if isinstance(channel, Channel):
			self.channel = channel
		else:
			self.channel = client.channel(channel)
		super(ChannelPlugin, self).__init__(client, channel, *args)

	def get_logger(self):
		return super(ChannelPlugin, self).get_logger().getChild(self.channel.name)

	@property
	def config(self):
		"""As ClientHandler but merges top-level config with any config found under channel name,
		eg. {"a": 1, "b": 2, "#foo": {"b": 3}} would resolve to {"a": 1", "b": 3} for #foo
		"""
		d = super(ChannelPlugin, self).config
		d.update(d.pop(self.channel.name, {}))
		return d

	@property
	def store(self):
		"""As ClientHandler but additionally indexes by channel name"""
		return super(ChannelPlugin, self).store.setdefault(self.channel.name, {})


def command_plugin(*args, **kwargs):
	"""Helper utility for creating client plugins that consist of a single command.
	Args are as per CommandHandler.
	Plugin name is name of wrapped function.
	Note you still need to take a `self` argument - this is the generated plugin and contains all the normal things
	like config, store, reply...
	"""
	def _command_plugin(fn):
		class _GeneratedCommandPlugin(ClientPlugin):
			name = fn.__name__
			command = CommandHandler(*args, **kwargs)(fn)
		_GeneratedCommandPlugin.__name__ = "command_plugin_{}".format(fn.__name__)
		_GeneratedCommandPlugin.__module__ = fn.__module__
		return _GeneratedCommandPlugin
	return _command_plugin
