from pyconfig import Config

config = Config()

# log level - specify as integer or level string
config.register('loglevel', long_opts=['log'], default='INFO')

# irc options
config.register('host') # required
config.register('nick', default='ekimbot')
config.register('port', default=6667, map_fn=int)
config.register('password')
config.register('ident')
config.register('real_name')

split_on = lambda arg: (lambda value: value.split(arg))
# paths to search for plugins, list or ":"-seperated string
config.register('plugin_paths', default=[], map_fn=split_on(':'))
# what plugins should be loaded by default, list or whitespace-seperated string
config.register('enabled_plugins', default=[], map_fn=split_on(None))
# what channels should be joined, list or whitespace-seperated string
config.register('channels', default=[], map_fn=split_on(None))
