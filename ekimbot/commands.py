
import functools

from girc import Handler, Channel

from ekimbot.utils import reply


class CommandHandler(Handler):
	"""A special case of Handler designed to handle and respond to PRIVMSGs that have a command-like structure.
	A command handler matches if all the following are true:
		* msg is a PRIVMSG beginning with the configured command prefix.
		* After being split on whitespace, the leading words match the values in the "name" arg, case-insensitive.
	(msg, *args, **kwargs) is passed to the callback, where args is the words after the leading words
	that match "name", minus any "--key=value" pairs, which are passed as kwargs instead.
	"""
	def __init__(self, name, *args, **kwargs):
		"""Name may be either a string like "mycmd subcmd", or a list like ["mycmd", "subcmd"]
		nargs should be int and represents the *smallest* number of allowed args.
		Optional kwargs:
			help: Help string that describes command. First line is taken as a summary, subsequent lines
			      are long description. If not given, taken from callback.
			usage: String to display to the user if the args are wrong (ie. if handler raises TypeError)
		Passes other args (ie. match and ordering args) though to Handler
		"""
		self.name = name.split() if isinstance(name, basestring) else name
		self.name = [word.lower() for word in self.name]
		self._help = kwargs.pop('help', None)
		self.usage = kwargs.pop('usage', None)
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
		if any(word.lower() != expected for word, expected in zip(payload, self.name)):
			return
		return payload[len(self.name):]

	def _match_payload(self, client, payload):
		return self._get_args(client, payload) is not None

	@property
	def help(self):
		"""Returns (summary, long description).
		Note that summary is just the first line of long description.
		May return (None, None) if no help is found.
		"""
		helpstr = self._help
		if self.callback and not helpstr:
			helpstr = self.callback.__doc__
		if not helpstr:
			return (None, None)
		summary = helpstr.strip().split('\n')[0]
		return summary, '\n'.join(line.strip() for line in helpstr.split('\n'))

	def _handle(self, client, msg, instance=None):
		args = self._get_args(client, msg.payload)
		args, kwargs = parse_argv(args)
		args = [msg] + list(args)
		if instance:
			args = [instance] + args
		try:
			return self(*args, **kwargs)
		except TypeError:
			if self.usage:
				error_msg = "Bad arguments. Usage: {name} {usage}"
			else:
				error_msg = "Bad arguments for {name}"
			error_msg.format(name=" ".join(self.name), usage=self.usage)
			reply(client, msg, error_msg)


class ChannelCommandHandler(CommandHandler):
	"""Variant of CommandHandler that checks instance.channel at handle time.
	As such, it requires the use of bound instances.
	It will only match if the channel name matches."""
	def set_callback(self, callback):
		if callback is None:
			self.callback = None
			return

		@functools.wraps(callback)
		def wrapper(instance, msg, *args):
			channel = instance.channel
			if isinstance(channel, Channel):
				channel = channel.name
			channel = msg.client.normalize_channel(channel)
			if channel != msg.target:
				return
			return callback(instance, msg, *args)
		self.callback = wrapper
