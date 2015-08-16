
from ekimbot.botplugin import ClientPlugin
from ekimbot.commands import CommandHandler


class ClientopsPlugin(ClientPlugin):
	"""Admin operations concerning the client as a whole"""

	name = 'clientops'

	@CommandHandler('restart', 0)
	def restart(self, msg, *args):
		self.client.restart("Reconnecting (administrative restart by {})".format(msg.sender))

	@CommandHandler('stop', 0)
	def stop(self, msg, *args):
		self.client.quit("Stopping (administrative stop by {})".format(msg.sender))
