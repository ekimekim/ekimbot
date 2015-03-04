
import os

from pyconfig import Config

from ekimbot import core_plugins


# Core plugin auto-detect
core_plugins_path = os.path.dirname(core_plugins.__file__)
core_plugins_list = [name[:3] for name in os.listdir(core_plugins_path) if name.endswith('.py')]


class BotConfig(Config):
	# Contains some special derived properties

	@property
	def core_plugins(self):
		from ekimbot.botplugin import BotPlugin
		return [BotPlugin.loaded_by_name[name] for name in core_plugins_list
		        if name in BotPlugin.loaded_by_name]

	@property
	def global_core_plugins(self):
		from ekimbot.botplugin import ClientPlugin
		return [plugin for plugin in self.core_plugins if not isinstance(plugin, ClientPlugin)]

	@property
	def all_global_plugins(self):
		return self.global_plugins + self.global_core_plugins

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
# Instead, append to them.
# plugin_paths - list of paths to search for plugins
config.register('plugin_paths', default=[], map_fn=lambda value: value.split(':'))
# load_plugins - list of plugins to load on startup
config.register('load_plugins', default=core_plugins_list[:])
# global_plugins - list of global plugins to enable
config.register('global_plugins', default=[])

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
	'plugins': ['plugops', 'config_manager'],
})

