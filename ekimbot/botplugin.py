
from plugins import Plugin
from classtricks import classproperty, get_resolved_dict

from girc import Handler, Privmsg

from ekimbot.config import config


def _reply(client, msg, text):
	"""Reply a PRIVMSG to a given msg's sender, or to the whole channel if msg was a PRIVMSG to a channel."""
	if isinstance(msg, Privmsg):
		targets = set(msg.sender if client.matches_nick(target) else target for target in msg.targets)
	else:
		targets = {msg.sender}
	for target in targets:
		client.msg(target, text)


class BotPlugin(Plugin):
	"""Generic plugin. You should only use this if your plugin does not use a specific irc client instance."""
	def __init__(self, *args):
		super(BotPlugin, self).__init__(*args)
		self.logger = self.get_logger()
		self.init()

	def get_logger(self):
		# lazy import to break cyclic dependency
		from ekimbot.main import main_logger
		return main_logger.getChild(self.name)

	@classproperty
	def load_paths(cls):
		return config.plugin_paths


class ClientPlugin(BotPlugin):
	"""Plugins that interact with a client.
	Plugins may either define handlers on methods (which will automatically register to the client
	when the plugin is enabled), or define handlers on self.client in init().
	Default cleanup() will automatically unregister handlers that were automatically registered.
	"""

	def __init__(self, client):
		self.client = client
		super(ClientPlugin, self).__init__(client)
		for handler in self.find_handlers().values():
			handler.register(self.client)

	def get_logger(self):
		return self.client.logger.getChild(self.name)

	def init(self):
		"""Called when plugin is enabled."""
		pass

	def cleanup(self):
		"""Called on disable. Should clean up any ongoing operations. The default one unregisters
		methods that are Handlers."""
		for handler in self.find_handlers().values():
			handler.unregister(self.client)

	def find_handlers(self):
		"""Return a map {attr: value} for all attributes of cls that are a Handler."""
		# scan for handlers
		ret = {key: value for key, value in get_resolved_dict(self).items() if isinstance(value, Handler)}
		# re-fetch them via getattr so __get__ works as intended
		ret = {key: getattr(self, key) for key in ret}
		return ret

	def reply(self, msg, text):
		_reply(self.client, msg, text)


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

	def _get_args(self, payload):
		if not payload.startswith(config.command_prefix):
			return
		payload = payload[len(config.command_prefix):]
		payload = payload.lower().split()
		if payload[:len(self.name)] != self.name:
			return
		return payload[len(self.name):]

	def _match_payload(self, payload):
		return self._get_args(payload) is not None

	def _handle(self, client, msg, instance=None):
		args = self._get_args(msg.payload)
		if len(args) < self.nargs:
			_reply(client, msg, "Command {!r} requires at least {} args".format(' '.join(self.name), self.nargs))
		args = [msg] + list(args)
		if instance:
			args = [instance] + args
		return self(*args)

