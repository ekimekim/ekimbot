import sys
import logging

import gevent
import gtools
from girc import Client
from backoff import Backoff

from ekimbot.config import config
from ekimbot.botplugin import BotPlugin, ClientPlugin

RETRY_START = 1
RETRY_LIMIT = 300
RETRY_FACTOR = 1.5

main_logger = logging.getLogger('ekimbot')


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

	main_logger.info("Starting up")

	for plugin in config.load_plugins:
		main_logger.debug("Load {}".format(plugin))
		BotPlugin.load(plugin)

	for plugin in config.global_plugins:
		main_logger.debug("Enable {}".format(plugin))
		BotPlugin.enable(plugin)

	gtools.gmap(lambda options: run_client(**options), config.clients_with_defaults)

	main_logger.info("All clients exited")


def run_client(host=None, nick='ekimbot', port=6667, password=None, ident=None, real_name=None,
               plugins=(), channels=(), **extra):
	if not host:
		main_logger.error("No host given for client")
		return

	name = '{}@{}:{}'.format(nick, host.replace('.', '_'), port)
	logger = main_logger.getChild(name)
	retry_timer = Backoff(RETRY_START, RETRY_LIMIT, RETRY_FACTOR)

	while True:
		try:
			logger.info("Starting client")
			client = Client(host, nick, port=port, password=password, ident=ident, real_name=real_name,
			                logger=logger)
			# include originals for changable args
			extra.update(nick=nick)
			client.config = extra

			logger.info("Enabling {} plugins".format(len(plugins)))
			for plugin in plugins:
				logger.debug("Enabling plugin {}".format(plugin))
				ClientPlugin.enable(plugin, client)
			plugin = None # don't leave long-lived useless references

			logger.info("Joining {} channels".format(len(channels)))
			for channel in channels:
				logger.debug("Joining channel {}".format(channel))
				client.channel(channel).join()

			client.start()
			logger.debug("Client started")
			client.wait_for_stop()

		except Exception:
			logger.warning("Client failed, re-connecting in {}s".format(retry_timer.peek()), exc_info=True)

			# save then disable enabled plugins
			# note that by overwriting plugins arg we will re-enable all plugins that were enabled, not configured plugins
			plugins = [type(plugin) for plugin in ClientPlugin.enabled if plugin.client is client]
			for plugin in plugins:
				ClientPlugin.disable(plugin, client)
			plugin = None # don't leave long-lived useless references

			gevent.sleep(retry_timer.get())
			continue

		break

	logger.info("Client exited cleanly, not re-connecting")
