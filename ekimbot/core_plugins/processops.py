
import gc
import os
import socket
import sys

import gevent

from ekimbot.main import handoff_all
from ekimbot.botplugin import ClientPlugin
from ekimbot.commands import CommandHandler


class ProcessopsPlugin(ClientPlugin):
	"""Admin operations concerning the entire bot process.
	Only enable this plugin on trusted servers."""

	name = 'processops'

	@CommandHandler('process info', 0)
	def info(self, msg, *args):
		"""Get basic information on the process and where it's running"""
		self.reply(msg, "Running as pid {} on host {}".format(os.getpid(), socket.gethostname()))

	@CommandHandler('process restart', 0)
	def restart(self, msg, *args):
		"""Restart the entire python process, but handoff the connections so we don't need to re-connect"""
		# need to run handoff_all NOT as a greenlet associated with a client
		gevent.spawn(handoff_all)

	@CommandHandler('process stop', 0)
	def stop(self, msg, *args):
		sys.exit()
