
loglevel = 'DEBUG'

host = None # required
nick = 'ekimbot'
port = 194
local_hostname = None
server_name = None
real_name = None

def load_config(conffile, **kwargs):
	g = globals()
	g.update(kwargs)
	execfile(filename, g)
	g.update(kwargs)
