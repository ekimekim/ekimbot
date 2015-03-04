
import os

from pyconfig import Config

from ekimbot import core_plugins


# Core plugin auto-detect
core_plugins_path = os.path.dirname(core_plugins.__file__)
core_plugins_list = [name[:3] for name in os.listdir(core_plugins_path) if name.endswith('.py')]


class ModifiesProperty(object):
	"""Special kind of property that passes setting through to the super(),
	and on get calls the wrapped function with the unmodified value.
	The wrapped function's return value (expected to be the modified version of the value) is returned.
	NOTE: This value is only intended to act as a decorator. In particular, it uses func.__name__ to know what
	super value to look up.
	"""
	# XXX We hard-code BotConfig here because there's a dependency loop with defining BotConfig using this
	# and passing in the cls to give super() at init time.
	def __init__(self, func):
		self.func = func
		self.name = func.__name__
	def __get__(self, instance, owner):
		if not instance:
			return self
		value = getattr(super(BotConfig, instance), self.name)
		return self.func(instance, value)
	def __set__(self, instance, value):
		setattr(super(BotConfig, instance), self.name, value)


class BotConfig(Config):
	# We override certain keys with properties to do dynamic modification of their values

	@ModifiesProperty
	def plugin_paths(self, value):
		# always include core plugins
		return list(value) + [core_plugins_path]

	@ModifiesProperty
	def load_plugins(self, value):
		# always include core plugins
		return list(value) + [core_plugins_list]

	@ModifiesProperty
	def global_plugins(self, value):
		# lazy import to work around circular dependency
		from ekimbot.botplugin import BotPlugin, ClientPlugin
		# always include core plugins
		plugins = [BotPlugins.loaded_by_name[name] for name in core_plugins_list
		           if name in BotPlugins.loaded_by_name]
		return list(value) + [plugin for plugin in plugins if not isinstance(plugin, ClientPlugin)]


config = BotConfig()


# --- Logging ---
# log level - specify as integer or level string
config.register('loglevel', long_opts=['log'], default='INFO')
# log file - file to log to, or None to disable. Default to "/var/log/ekimbot.log".
config.register('logfile', default='/var/log/ekimbot.log')

# --- Plugins ---
# plugin_paths - paths to search for plugins, list or ":"-seperated string
config.register('plugin_paths', default=[], map_fn=lambda value: value.split(':'))
# load_plugins - plugins to load on startup, list or space-seperated string
config.register('load_plugins', default=[], map_fn=lambda value: value.split())
# global_plugins - global plugins to enable, list or space-seperated string
config.register('global_plugins', default=[], map_fn=lambda value: value.split())

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
})

