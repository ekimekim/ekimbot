
import os
import socket
import sys

from ekimbot.botplugin import ClientPlugin
from ekimbot.commands import CommandHandler
from ekimbot.main import Restart


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
		"""Restart the entire python process"""
		# We do a self-execve() - this should always do the right thing, and leave our PID unchanged.
		os.execve(sys.executable, [sys.executable] + sys.argv, os.environ)

	@CommandHandler('process stop', 0)
	def stop(self, msg, *args):
		sys.exit()
