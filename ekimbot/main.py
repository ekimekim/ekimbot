import logging

import gevent
from backoff import Backoff
from girc import Client
from modulemanager import Referenced

from ekimbot.config import config
from ekimbot.botplugin import BotPlugin, ClientPlugin

RETRY_START = 1
RETRY_LIMIT = 300
RETRY_FACTOR = 1.5

main_logger = logging.getLogger('ekimbot')

# maps name to manager controlling client
clients = {}


def main(**options):
	config.load(user_config=True, argv=True, env=True, **options)

	configure_logging()
	main_logger.info("Starting up")

	for plugin in config.load_plugins:
		main_logger.debug("Load {}".format(plugin))
		BotPlugin.load(plugin)

	for plugin in config.global_plugins:
		main_logger.debug("Enable {}".format(plugin))
		BotPlugin.enable(plugin)

	for name in config.clients:
		ClientManager.spawn(name)

	main_logger.debug("Main going to sleep")
	try:
		try:
			gevent.wait()
			main_logger.info("Nothing running - exiting")
		except (KeyboardInterrupt, SystemExit):
			main_logger.info("Stopping all clients")
			for manager in clients.values():
				manager.client.quit("Shutting down", block=False)
			for manager in clients.values():
				manager.get()
	except BaseException:
		main_logger.exception("Failed to stop cleanly")
		raise
	else:
		main_logger.info("Exited cleanly")


def configure_logging():
	"""Set handlers and level on root logger as per config options.
	Will remove any existing handlers."""
	root = logging.getLogger()
	for handler in root.handlers:
		root.removeHandler(handler)

	loglevel = config.loglevel
	if isinstance(loglevel, basestring):
		loglevel = logging._levelNames[loglevel.upper()]
	root.setLevel(loglevel)

	handlers = [logging.StreamHandler()]
	if config.logfile:
		handlers.append(logging.FileHandler(config.logfile))
	for handler in handlers:
		handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
		root.addHandler(handler)


class ClientManager(gevent.Greenlet):
	"""Wrapper for a client to manage clean restarts, etc"""
	# We mostly handle state via a synchronous main function, hence we base off Greenlet

	INIT_ARGS = {'hostname', 'nick', 'port', 'password', 'ident', 'real_name', 'twitch'}

	client = None
	_can_signal = False # indicates if main loop is in good state to get a stop/restart

	class _Restart(Exception):
		"""Indicates the client manager should cleanly disconnect and reconnect"""

	def __init__(self, name):
		self.name = name
		self.logger = main_logger.getChild(name)
		super(ClientManager, self).__init__()

	def restart(self, message):
		"""Gracefully restart the client"""
		# if can_signal is false, restarting isn't a valid operation (ie. we're already restarting)
		# otherwise, send a _Restart exception to the main loop
		if self._can_signal:
			self.kill(self._Restart(message), block=False)

	def _run(self):
		if self.name in clients:
			return # already running, ignore second attempt to start
		clients[self.name] = self

		try:
			plugins = None
			self.retry_timer = Backoff(RETRY_START, RETRY_LIMIT, RETRY_FACTOR)

			while True:
				if self.name not in config.clients_with_defaults:
					self.logger.info("No such client, stopping")
					return

				options = config.clients_with_defaults[self.name]

				channels = options.get('channels', [])
				if plugins is None:
					plugins = []
					for name in options.get('plugins', []):
						args = ()
						if ':' in name:
							name, args = name.split(':', 1)
							args = args.split(',')
						plugins.append((name, args))

				try:
					self.logger.info("Starting client")
					self.client = EkimbotClient(self.name,
					                            logger=self.logger,
					                            **{key: options[key] for key in self.INIT_ARGS if key in options})

					self.logger.info("Enabling {} plugins".format(len(plugins)))
					for plugin, args in plugins:
						self.logger.debug("Enabling plugin {} with args {}".format(plugin, args))
						ClientPlugin.enable(plugin, self.client, *args)
					plugin = None # don't leave long-lived useless references

					self.logger.info("Joining {} channels".format(len(channels)))
					for channel in channels:
						self.logger.debug("Joining channel {}".format(channel))
						self.client.channel(channel).join()

					try:
						self._can_signal = True
						self.client.start()
						self.logger.debug("Client started")
						self.retry_timer.reset()
						self.client.wait_for_stop()
						self.logger.info("Client exited cleanly, not re-connecting")
						break
					finally:
						self._can_signal = False

				except Exception as ex:
					if isinstance(ex, self._Restart):
						self.logger.info("Client gracefully restarting: {}".format(ex))
						try:
							self.client.quit(str(ex))
						except Exception:
							self.logger.warning("Client failed during graceful restart", exc_info=True)
					else:
						self.logger.warning("Client failed, re-connecting in {}s".format(self.retry_timer.peek()), exc_info=True)

					if self.client:
						# save then disable enabled plugins
						# note that we will re-enable all plugins that were enabled, not configured plugins
						plugins = set()
						try:
							# in rare cases, disabling a plugin will cause more plugins to activate (eg. slave)
							# we keep going until no plugins are left
							while self.client.plugins:
								enabled = {(type(plugin), plugin.args) for plugin in self.client.plugins}
								for plugin, args in enabled:
									assert args[0] is self.client
									ClientPlugin.disable(plugin, *args[1:])
								plugins |= enabled
						except Referenced:
							self.logger.error("Failed to clean up after old connection: plugin {} still referenced.".format(plugin))
							# in leiu of knowing exactly what the old client's state is, revert to config
							plugins = options.get('plugins', [])
						plugin = None # don't leave long-lived useless references

						self.client = None

					if not isinstance(ex, self._Restart):
						gevent.sleep(self.retry_timer.get())

		except Exception:
			self.logger.critical("run_client failed with unhandled exception")
			raise

		finally:
			assert clients[self.name] is self
			del clients[self.name]


class EkimbotClient(Client):
	"""A girc Client with some ekimbot specialization"""

	def __init__(self, name, **options):
		self.name = name
		super(EkimbotClient, self).__init__(**options)

	@property
	def config(self):
		return config.clients_with_defaults.get(self.name, {})

	@property
	def plugins(self):
		return {plugin for plugin in ClientPlugin.enabled if plugin.client is self}

	def restart(self, message):
		if clients[self.name].client is not self:
			# this Client is not the active client - this is a weird situation, let's do nothing
			return
		clients[self.name].restart(message)
