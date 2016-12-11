import gc
import json
import logging
import os
import socket
import sys

import gevent
from backoff import Backoff
from girc import Client

from ekimbot.config import config
from ekimbot.botplugin import BotPlugin, ClientPlugin
from ekimbot.utils import list_modules

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

	for path in config.plugin_paths:
		for plugin_name in list_modules(path):
			BotPlugin.load(plugin_name)

	for plugin in config.global_plugins:
		main_logger.debug("Enable {}".format(plugin))
		BotPlugin.enable(plugin)

	if config.handoff_data:
		# expects a dict { client name: {'fd': sock fd, **kwargs for from_handoff()}}
		handoff_data = json.loads(config.handoff_data)
		# json deals in unicode, we want bytes
		for k, v in handoff_data.items():
			if isinstance(v, unicode):
				handoff_data[k] = v.encode('utf-8')
	else:
		handoff_data = {}

	for name in config.clients:
		ClientManager.spawn(name, handoff_data=handoff_data.get(name))

	main_logger.debug("Main going to sleep")
	try:
		try:
			gevent.wait()
			main_logger.info("Nothing running - exiting")
		except (KeyboardInterrupt, SystemExit):
			main_logger.info("Stopping all clients")
			for manager in clients.values():
				manager.stop('Shutting down')
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


def handoff_all():
	main_logger.info("Preparing to re-exec with handoffs")

	handoff_data = {}
	for name, manager in clients.items():
		data = manager.handoff()
		if data:
			handoff_data[name] = data

	main_logger.info("Final handoff data: {!r}".format(handoff_data))

	for manager in clients.values():
		manager.get()

	main_logger.info("All managers stopped")

	# TODO this will fail if the bytes contain invalid utf-8
	handoff_data_str = json.dumps(handoff_data)
	env = os.environ.copy()
	env['handoff_data'] = handoff_data_str
	main_logger.info("Calling execve({!r}, {!r}, {!r})".format(sys.executable, sys.argv, env))

	# critical section - absolutely no blocking calls beyond this point
	gc.disable() # we don't want any destructors running
	open_fds = set(map(int, os.listdir('/proc/self/fd')))
	for fd in open_fds - {0, 1, 2} - set(data['fd'] for data in handoff_data.values()):
		try:
			os.close(fd)
		except OSError:
			pass # this is probably EBADF, but even if it isn't we can't do anything about it
	os.execve(sys.executable, [sys.executable, '-m', 'ekimbot'] + sys.argv[1:], env)


class ClientManager(gevent.Greenlet):
	"""Wrapper for a client to manage clean restarts, etc"""
	# We mostly handle state via a synchronous main function, hence we base off Greenlet

	INIT_ARGS = {'hostname', 'nick', 'port', 'password', 'ident', 'real_name', 'twitch'}

	client = None
	_can_signal = False # indicates if main loop is in good state to get a stop/restart
	_stop = False # indicates to quit after next client quit

	class _Restart(Exception):
		"""Indicates the client manager should cleanly disconnect and reconnect"""

	def __init__(self, name, handoff_data=None):
		self.name = name
		self.handoff_data = handoff_data
		self.logger = main_logger.getChild(name)
		super(ClientManager, self).__init__()

	def stop(self, message):
		"""Gracefully stop the client"""
		self._stop = True
		if self._can_signal:
			self.client.quit("Shutting down", block=False)
		else:
			# we are mid-restart or similar, just kill the main loop
			self.kill(block=False)

	def restart(self, message):
		"""Gracefully restart the client"""
		# if can_signal is false, restarting isn't a valid operation (ie. we're already restarting)
		# otherwise, send a _Restart exception to the main loop
		if self._can_signal:
			self.kill(self._Restart(message), block=False)

	def handoff(self):
		"""Gracefully shut down and prepare for handoff.
		This stops the client and returns a dict suitable to pass as config.handoff_data[name]
		to a child or re-exec()ed process.
		However, if the client is not currently in a good state for handoff (eg. it is currently restarting)
		this method will still stop the client manager, but will return None. In this case,
		there was no state to handoff so the best thing to do is let the child re-create a new client.
		"""
		# Note this method intentionally leaks an fd so we can't accidentially close it
		# due to destructors. This fd is then passed onto the child / re-exec()ed process.
		self.logger.info("Attempting to handoff")

		if not self._can_signal:
			self.logger.info("Handoff aborted - client is not running")
			# we are mid-restart or similar, just kill the main loop
			self.kill(block=False)
			return

		try:
			self.client._prepare_for_handoff()
		except Exception:
			# this can happen if we're mid-start, best thing to do is just abort
			self.logger.info("Handoff aborted - client in bad state")
			self.client.stop()
			self.kill(block=False)
			return

		data = self.client._get_handoff_data()
		data['fd'] = os.dup(self.client._socket.fileno())
		self.logger.info("Handoff initiated with data {!r}".format(data))
		# this will gracefully stop, which will cause the main loop to exit
		self.client._finalize_handoff()

		return data

	def _parse_config_plugins(self):
		plugins = []
		for name in config.clients_with_defaults[self.name].get('plugins', []):
			args = ()
			if ':' in name:
				name, args = name.split(':', 1)
				args = args.split(',')
			plugins.append((name, args))
		return plugins

	def _run(self):
		if self.name in clients:
			return # already running, ignore second attempt to start
		clients[self.name] = self

		try:
			self.retry_timer = Backoff(RETRY_START, RETRY_LIMIT, RETRY_FACTOR)

			while not self._stop:
				if self.name not in config.clients_with_defaults:
					raise Exception("No such client {!r}".format(self.name))

				options = config.clients_with_defaults[self.name]

				channels = options.get('channels', [])
				plugins = self._parse_config_plugins()

				try:
					if self.handoff_data:
						self.logger.info("Accepting handoff with data {!r}".format(self.handoff_data))
						client_sock = socket.fromfd(self.handoff_data.pop('fd'), socket.AF_INET, socket.SOCK_STREAM)
						self.client = EkimbotClient._from_handoff(client_sock, name=self.name, logger=self.logger, **self.handoff_data)
						self.handoff_data = None
					else:
						self.logger.info("Starting client")
						self.client = EkimbotClient(self.name,
						                            logger=self.logger,
						                            **{key: options[key] for key in self.INIT_ARGS if key in options})

					self.logger.info("Enabling {} plugins".format(len(plugins)))
					for plugin, args in plugins:
						self.logger.debug("Enabling plugin {} with args {}".format(plugin, args))
						ClientPlugin.enable(plugin, self.client, *args)

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

					if not self._stop and not isinstance(ex, self._Restart):
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
