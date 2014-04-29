import sys
import logging

import geventirc

import config

client = None

def main(**options):
	options.setdefault('conffile', './ekimbot.conf')
	config.load_config(**options)

	loglevel = config.loglevel
	if isinstance(loglevel, basestring):
		loglevel = loglevel.upper()
		loglevel = getattr(logging, loglevel)
	logging.basicConfig(stream=sys.stderr, level=loglevel)

	global client
	client = geventirc.Client(config.host, config.nick, config.port,
	                          config.local_hostname, config.server_name, config.real_name)

	# TODO replace this with a proper plugin system
	import plugins

	client.start()
	client.join()
