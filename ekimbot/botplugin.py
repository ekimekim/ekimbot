
from plugins import Plugin
from classtricks import classproperty, dotdict

from girc import Handler

from ekimbot import utils
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
		"""Return actual store object"""
		return Store(config.store_path)

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

	def __init__(self, client):
		self.client = client
		super(ClientPlugin, self).__init__(client)
		Handler.register_all(client, self)

	def get_logger(self):
		return self.client.logger.getChild(self.name)

	def init(self):
		"""Called when plugin is enabled."""
		pass

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
