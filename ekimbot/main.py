import sys
import logging

from girc import Client

from ekimbot.config import config
from ekimbot.botplugin import BotPlugin


def main(**options):
	config.load(user_config=True, argv=True, env=True, **options)

	loglevel = config.loglevel
	if isinstance(loglevel, basestring):
		loglevel = logging._levelNames[loglevel.upper()]
	logging.basicConfig(stream=sys.stderr, level=loglevel)
	if config.logfile:
		handler = logging.FileHandler(config.logfile)
		handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
		logging.getLogger().addHandler(handler)

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
