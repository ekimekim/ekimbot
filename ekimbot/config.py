
loglevel = 'DEBUG'

host = None # required
nick = 'ekimbot'
port = 6667
local_hostname = None
server_name = None
real_name = None

def load_config(conffile=None, **kwargs):
	g = globals()
	g.update(kwargs)
	if conffile:
		execfile(conffile, g)
		g.update(kwargs)
