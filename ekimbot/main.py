
import config

def main(**options):
	options.setdefault('conffile', './ekimbot.conf')
	config.load_config(**options)
