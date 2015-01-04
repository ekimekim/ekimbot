from pyconfig import Config

config = Config()

# log level - specify as integer or level string
config.register('loglevel', long_opts=['log'], default='INFO')
# paths to search for plugins, list or ":"-seperated string
config.register('plugin_paths', default=[], map_fn=lambda value: value.split(':'))
# plugins to load on startup, list or space-seperated string
config.register('load_plugins', default=[], map_fn=lambda value: value.split())
# global plugins to enable, list or space-seperated string
config.register('global_plugins', default=[], map_fn=lambda value: value.split())

# irc options
# Each client should take host, optionally nick, port, password, ident, real_name, plugins, channels
# Most of those should be obvious, plugins is what plugins to enable on startup
config.register('clients', default=[])

# command prefix, only run commands when they're prefixed by this exact string
config.register('command_prefix', default='ekimbot: ')
