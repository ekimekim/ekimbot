import sys
import logging

from girc import Client
from plugins import Plugin

from config import config


# The way that the plugin system works is such that plugins are inherently global - they are modules.
# Thus, it makes no sense for client to not be global.
# Making it global in this way is the simplest way to access it from plugins.
client = None


class BotPlugin(Plugin):
	"""Plugins should register message handlers with client.
	There are no special hooks."""
	# XXX Due to the way message handlers work, these plugins CANNOT BE UNLOADED.


def main(**options):
	global client

	config.load(user_config=True, argv=True, env=True, **options)

	loglevel = config.loglevel
	if isinstance(loglevel, basestring):
		loglevel = logging._levelNames[loglevel.upper()]
	logging.basicConfig(stream=sys.stderr, level=loglevel)

	if not config.host:
		raise ValueError("You must specify a host")

	BotPlugin.load_paths = config.plugin_paths

	client = Client(config.host, config.nick, port=config.port, password=config.password, ident=config.ident,
	                real_name=config.real_name)

	for plugin in config.enabled_plugins:
		BotPlugin.load(plugin)

	for channel in config.channels:
		client.channel(channel).join()

	client.start()
	client.wait_for_stop()


if __name__ == '__main__':
	main()
