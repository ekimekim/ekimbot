
from ekimbot.botplugin import BotPlugin, CommandHandler

from gevent.backdoor import BackdoorServer


class BackdoorPlugin(BotPlugin):
	name = 'backdoor'
	PORT = 1234

	def init(self):
		self.server = BackdoorServer(('localhost', self.PORT))
		self.server.start()

	def cleanup(self):
		super(BackdoorPlugin, self).cleanup()
		self.server.stop()
