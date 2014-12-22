import sys
import logging

from girc import Client
from plugins import Plugin
from classtricks import classproperty

from config import config


class BotPlugin(Plugin):
	"""Plugins should register message handlers with self.client
	"""

	@classproperty
	def load_paths(cls):
		return config.plugin_paths

	def __init__(self, client):
		super(BotPlugin, self).__init__(client)
		self.client = client
		self.init()

	def init(self):
		"""Called when plugin is enabled. You should add your client handlers here."""
		pass


def main(**options):
	config.load(user_config=True, argv=True, env=True, **options)

	loglevel = config.loglevel
	if isinstance(loglevel, basestring):
		loglevel = logging._levelNames[loglevel.upper()]
	logging.basicConfig(stream=sys.stderr, level=loglevel)

	if not config.host:
		raise ValueError("You must specify a host")

	client = Client(config.host, config.nick, port=config.port, password=config.password, ident=config.ident,
	                real_name=config.real_name)

	for plugin in config.enabled_plugins:
		BotPlugin.load(plugin)
		BotPlugin.enable(plugin, client)

	for channel in config.channels:
		client.channel(channel).join()

	client.start()
	client.wait_for_stop()
