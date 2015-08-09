
import gevent

import plugins
from girc import Handler, Client, replycodes

from ekimbot.botplugin import ClientPlugin
from ekimbot.commands import CommandHandler
from ekimbot.main import Restart


class SlavePlugin(ClientPlugin):
	"""Adds redundancy to the bot by allowing it to run in multiple places.
	Since only one connection can hold the configured nick, we call this the "master".
	All others are "slaves" and have all per-client modules disabled (except this one).
	They are automatically re-enabled upon becoming the master.
	Note that there are almost unavoidable race cdns between changing nick and dis/enabling modules.
	"""
	name = 'slave'

	defaults = {
		'poll_interval': 5,
	}

	master = True
	saved_plugins = None

	def init(self):
		self.check_nick()
		self.check_user_poller = self.client._group.spawn(self.poll_check_users)

	def cleanup(self):
		self.check_user_poller.kill()
		super(SlavePlugin, self).cleanup()

	@property
	def master_nick(self):
		return self.client.config['nick']

	@Handler(command={replycodes.errors.NICKNAMEINUSE, 'NICK'},
	         after={Client.nick_in_use, Client.forced_nick_change})
	def check_nick(self, *_):
		"""Called after any non-explicit name change, checks if we are now master"""
		# note that client.nick will block if nick is changing
		is_master = self.client.nick == self.master_nick
		if self.master and not is_master:
			self.demote()
		elif not self.master and is_master:
			self.promote()

	# it's a bit hacky, but "after sync" ensures that the user list has been updated
	@Handler(command={'QUIT', 'NICK'}, after={'sync'})
	def check_users(self, *_):
		"""Called after any user is observed to leave or change nick.
		Also called peroidically in case this happened without us being able to see it.
		Checks if any user can be seen with master nick. If not, tries to change nick to master nick.
		"""
		if self.client.nick != self.master_nick:
			for channel in self.client._channels.values():
				if channel.users_ready.is_set() and self.master_nick in channel.users.users:
					return
			self.client.nick = self.master_nick
		self.check_nick()

	def poll_check_users(self):
		while True:
			gevent.sleep(self.config.poll_interval)
			self.check_users()

	def demote(self):
		self.logger.info("Becoming slave")
		self.master = False
		self.saved_plugins = set(type(plugin) for plugin in ClientPlugin.enabled
		                         if plugin.client is self.client and plugin is not self)
		plugin = None # no hanging references
		try:
			for plugin_cls in self.saved_plugins:
				ClientPlugin.disable(plugin_cls, self.client)
		except plugins.Referenced:
			self.logger.error("Failed to go into slave mode: {} plugin still referenced".format(plugin_cls))
			self.client.stop(Restart("Unrecoverable error while entering slave mode. Reconnecting."))

	def promote(self):
		self.logger.info("Becoming master")
		assert self.saved_plugins is not None, "SlavePlugin: promote() called before demote()"
		self.master = True
		for plugin_cls in self.saved_plugins:
			ClientPlugin.enable(plugin_cls, self.client)
		self.saved_plugins = None

	@CommandHandler("abdicate", 0)
	def abdicate(self, msg, *args):
		self.logger.info("Stepping down as master")
		self.demote()
		self.client.nick = self.client.increment_nick(self.client.nick)
