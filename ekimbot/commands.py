
import functools

from girc import Handler, Channel

from ekimbot.utils import reply


class EkimbotHandler(Handler):
	"""Contains some standard matching criteria in order to implement bot-wide things
	like master-mode and ignore lists"""
	def __init__(self, *args, **kwargs):
		"""Takes additional kwargs:
			no_ignore=True: don't ignore senders on the ignore list
			master: Governs how this relates to master state
				True: (default) Only when we are master
				False: Only when we are NOT master
				None: Either
		"""
		no_ignore = kwargs.pop('no_ignore', False)
		master = kwargs.pop('master', True)

		# because we check nick state under lock, we can't wait go before sync
		# as this would cause a deadlock. We can't catch all circumstances but we can do what we can.
		if (
			(master is not None or not no_ignore) and 
			(kwargs.get('sync', False) or 'sync' in kwargs.get('before', []))
		):
			raise Exception("Can't define a default EkimbotHandler for before sync due to potential deadlock")

		def check_sender(client, sender):
			try:
				if master is not None or not no_ignore:
					current_nick = client.nick
				if not no_ignore:
					if any(sender.lower() == ignored_nick.lower() for ignored_nick in client.config['ignore']):
						return False
				if master is not None:
					is_master = current_nick == client.config['nick']
					if master != is_master:
						return False
				return True
			except Exception:
				# match args consider errors to be failures, so we need to report our own errors here
				client.logger.exception("Error in EkimbotHandler check_sender")
				return False

		kwargs.update(
			sender=check_sender
		)
		super(EkimbotHandler, self).__init__(*args, **kwargs)


class CommandHandler(EkimbotHandler):
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
		Optional kwargs:
			help: Help string that describes command. First line is taken as a summary, subsequent lines
			      are long description. If not given, taken from callback.
		"""
		self.name = name.split() if isinstance(name, basestring) else name
		self.name = [word.lower() for word in self.name]
		self.nargs = nargs
		self._help = kwargs.pop('help', None)
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
		if len(args) < self.nargs:
			reply(client, msg, "Command {!r} requires at least {} args".format(' '.join(self.name), self.nargs))
		args = [msg] + list(args)
		if instance:
			args = [instance] + args
		return self(*args)


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
