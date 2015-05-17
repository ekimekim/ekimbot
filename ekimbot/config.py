
"""Defines and documents main bot config options.
Run as __main__ for a debug check that simply prints the results of loading the config
"""

import os
import string
import random

from pyconfig import Config

from ekimbot import core_plugins
from ekimbot.utils import list_modules


# Core plugin auto-detect
core_plugins_path = os.path.dirname(core_plugins.__file__)
core_plugins_list = list_modules(core_plugins_path)


class BotConfig(Config):
	# Contains some special derived properties

	@property
	def clients_with_defaults(self):
		for client in self.clients:
			d = self.client_defaults.copy()
			d.update(client)
			yield d


config = BotConfig()

# === Option descriptions ===
# Does not include plugin-specific configs - see individual plugin docs.

# --- Logging ---
# log level - specify as integer or level string
config.register('loglevel', long_opts=['log'], default='INFO')
# log file - file to log to, or None to disable. Default to "/var/log/ekimbot.log".
config.register('logfile', default='/var/log/ekimbot.log')

# --- Plugins ---
# These options contain default values that should not be overwritten.
# Instead, append to them. In particular, all core plugins are auto-loaded (but *not* auto-enabled).
# plugin_paths - list of paths to search for plugins
config.register('plugin_paths', default=[core_plugins_path])
# load_plugins - list of plugins to load on startup
config.register('load_plugins', default=core_plugins_list[:])
# global_plugins - list of global plugins to enable
config.register('global_plugins', default=[])

# --- Persistence ---
# store_path - JSON file to store persistent data - defaults to a random file in /tmp
config.register('store_path',
                default="/tmp/ekimbot-{}.json".format(''.join(random.choice(string.letters + string.digits) for x in range(8))))

# --- Per-client options ---
# clients - Should be a list of client option dicts containing client options.
# Each client should take host, optionally nick, port, password, ident, real_name, plugins, channels
# Most of those should be obvious, plugins is what plugins to enable on startup
config.register('clients', default=[])
# client_defaults - As per client option dicts, but provides defaults for option dicts in clients option.
# Note that the default value of client_defaults already defines some defaults - you probably want to
# update the existing value instead of overwriting it.
config.register('client_defaults', default={
	'command_prefix': 'ekimbot: ',
	'plugins': ['plugops', 'config_manager', 'help'],
})


if __name__ == '__main__':
	from pprint import pformat
	config.load(user_config=True, argv=True, env=True)
	registered = config.get_registered()
	non_registered = {k: v for k, v in config.get_most().items() if k not in registered}
	def format_opts(opts):
		return '\n'.join("{} = {}".format(k, pformat(v)) for k, v in opts.items())
	print '======= Main Options ======='
	print format_opts(registered)
	print '======= Extra Options ======='
	print format_opts(non_registered)
