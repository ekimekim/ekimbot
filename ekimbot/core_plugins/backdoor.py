
from ekimbot.botplugin import BotPlugin

from gevent.backdoor import BackdoorServer


class BackdoorPlugin(BotPlugin):
	name = 'backdoor'
	defaults = {
		'port': 1234,
	}

	def init(self):
		self.server = BackdoorServer(('localhost', self.config.port))
		self.server.start()

	def cleanup(self):
		super(BackdoorPlugin, self).cleanup()
		self.server.stop()
