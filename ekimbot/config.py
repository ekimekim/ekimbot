
host = None # required
port = None
local_hostname = None
server_name = None
real_name = None

def load_config(conffile, **kwargs):
	g = globals()
	g.update(kwargs)
	execfile(filename, g)
	g.update(kwargs)
