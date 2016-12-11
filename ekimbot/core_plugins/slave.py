
import gevent

import modulemanager
from girc import Handler, Client, replycodes

from ekimbot.botplugin import ClientPlugin
from ekimbot.commands import CommandHandler


class SlavePlugin(ClientPlugin):
	"""Adds redundancy to the bot by allowing it to run in multiple places.
	Since only one connection can hold the configured nick, we call this the "master".
	We have other handlers predicate on client nick matching configured nick
	"""
	name = 'slave'

	defaults = {
		'poll_interval': 5,
	}

	master = True
	saved_plugins = None

	def init(self):
		self.check_user_poller = self.client._group.spawn(self.poll_check_users)

	def cleanup(self):
		self.check_user_poller.kill()
		super(SlavePlugin, self).cleanup()

	@property
	def master_nick(self):
		return self.client.config['nick']

	# it's a bit hacky, but "after sync" ensures that the user list has been updated
	@Handler(command={'QUIT', 'NICK'}, after={'sync'})
	def check_users(self, *_):
		"""Called after any user is observed to leave or change nick.
		Also called peroidically in case this happened without us being able to see it.
		Checks if any user can be seen with master nick. If not, tries to change nick to master nick.
		"""
		if self.client.nick == self.master_nick:
			return
		if self.abdicated_until is not None and time.time() < self.abdicated_until:
			return
		for channel in self.client._channels.values():
			if channel.users_ready.is_set() and self.master_nick in channel.users.users:
				return
		self.client.nick = self.master_nick

	def poll_check_users(self):
		while True:
			gevent.sleep(self.config.poll_interval)
			self.check_users()

	@CommandHandler("abdicate", 0)
	def abdicate(self, msg, *args):
		if args:
			try:
				timeout = int(args[0])
			except ValueError:
				self.reply(msg, "Bad timeout value")
				return
		else:
			timeout = self.config.poll_interval * 2
		self.logger.info("Stepping down as master")
		self.abdicated_until = time.time() + timeout
		self.client.nick = self.client.increment_nick(self.client.nick)
