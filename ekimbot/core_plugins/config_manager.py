
import logging
import ast

from ekimbot.botplugin import ClientPlugin
from ekimbot.commands import CommandHandler
from ekimbot.config import config


class ConfigManagerPlugin(ClientPlugin):
	name = 'config_manager'

	@CommandHandler('config load', 0)
	def load_config(self, msg, *args):
		"""Load given config file (or the default) and add to existing config."""
		path = ' '.join(args)
		if not path:
			path = config.conf_file
			if not path:
				self.reply(msg, "No known config file - please specify a path")
				return
		self.logger.debug("Loading config from {!r}".format(path))
		try:
			config.from_file(path)
		except Exception as ex:
			self.reply(msg, "Failure to load config file {!r} with {}: {}".format(path, type(ex).__name__, ex))
		else:
			self.refresh()
			self.logger.info("Loaded config from {!r}".format(path))
			self.reply(msg, "Config file {!r} loaded".format(path))

	@CommandHandler('config set', 2)
	def set_config(self, msg, key, *value):
		"""Set config key to value. Value may be a python literal, or raw string."""
		value = ' '.join(value)
		try:
			value = ast.literal_eval(value)
		except Exception:
			pass
		self.logger.debug("Setting config.{} = {!r}".format(key, value))
		config[key] = value
		self.refresh()
		self.logger.info("Set config.{} = {!r}".format(key, value))
		self.reply(msg, 'set config.{} = {!r}'.format(key, value))

	def refresh(self):
		logging.getLogger().setLevel(logging._levelNames[config.loglevel.upper()]
		                             if isinstance(config.loglevel, basestring) else config.loglevel)
