
from girc import Handler

from ekimbot.config import config
from ekimbot.utils import reply


class CommandHandler(Handler):
	"""A special case of Handler designed to handle and respond to PRIVMSGs that have a command-like structure.
	A command handler matches if all the following are true:
		* msg is a PRIVMSG beginning with the configured command prefix.
		* After being split on whitespace, the leading words match the values in the "name" arg, case-insensitive.
	It is checked that there are at least nargs further words. If there isn't, an error message is replied.
	(msg, *args) is passed to the callback, where args is the words after the leading words that match "name".
	"""
	def __init__(self, name, nargs, *args, **kwargs):
		"""Name may be either a string like "mycmd subcmd", or a list like ["mycmd", "subcmd"]
		nargs should be int and represents the *smallest* number of allowed args.
		"""
		self.name = name.split() if isinstance(name, basestring) else name
		self.name = [word.lower() for word in self.name]
		self.nargs = nargs
		kwargs.update(
			command='PRIVMSG',
			payload=self._match_payload,
		)
		super(CommandHandler, self).__init__(*args, **kwargs)

	def _get_args(self, client, payload):
		prefix = client.config['command_prefix']
		if not payload.startswith(prefix):
			return
		payload = payload[len(prefix):]
		payload = payload.split()
		if [word.lower() for word in payload[:len(self.name)]] != self.name:
			return
		return payload[len(self.name):]

	def _match_payload(self, client, payload):
		return self._get_args(client, payload) is not None

	def _handle(self, client, msg, instance=None):
		args = self._get_args(client, msg.payload)
		if len(args) < self.nargs:
			reply(client, msg, "Command {!r} requires at least {} args".format(' '.join(self.name), self.nargs))
		args = [msg] + list(args)
		if instance:
			args = [instance] + args
		return self(*args)

