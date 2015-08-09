
from ekimbot.botplugin import ClientPlugin
from ekimbot.commands import CommandHandler
from ekimbot.main import Restart


class ClientopsPlugin(ClientPlugin):
	"""Admin operations concerning the client as a whole"""

	name = 'clientops'

	@CommandHandler('restart', 0)
	def restart(self, msg, *args):
		self.client.stop(Restart("Reconnecting (administrative restart by {})".format(msg.sender)))

	@CommandHandler('stop', 0)
	def stop(self, msg, *args):
		self.client.quit("Stopping (administrative stop by {})".format(msg.sender))
