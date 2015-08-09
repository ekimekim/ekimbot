
import gc
import os
import socket
import sys

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
		"""Restart the entire python process"""
		# We do a self-execve() - this should always do the right thing, and leave our PID unchanged.
		# We need to suspend some stuff to ensure nothing interrupts this critical section
		gc.disable()
		for fd in os.listdir('/proc/self/fd'):
			fd = int(fd)
			if fd <= 2:
				continue # don't close stdin/out/err
			# the listdir will contain the listdir's fd, so we ignore errors on close
			try:
				os.close(fd)
			except OSError:
				pass
		os.execve(sys.executable, [sys.executable, '-m', 'ekimbot'] + sys.argv[1:], os.environ)

	@CommandHandler('process stop', 0)
	def stop(self, msg, *args):
		sys.exit()
