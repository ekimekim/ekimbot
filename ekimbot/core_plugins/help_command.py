
from girc.message import Notice

from ekimbot.botplugin import ClientPlugin
from ekimbot.commands import CommandHandler


def startswith(a, b):
	"""Returns whether items of iterable a are equal to iterable b for all of iterable b's length.
	ie. it's str.startswith(), but for iterables. b must be finite."""
	a = iter(a)
	for item in b:
		try:
			if item != a.next():
				return False # elements don't match
		except StopIteration:
			return False # a shorter than b
	return True


class HelpPlugin(ClientPlugin):
	name = 'help'
	defaults = {'max_lines': 3}

	@CommandHandler("help", 0)
	def help_command(self, msg, *target):
		self.help(msg, False, *target)

	@CommandHandler("longhelp", 0)
	def longhelp_command(self, msg, *target):
		self.help(msg, True, *target)

	def help(self, msg, long, *target):
		target = [part.lower() for part in target]
		commands = [handler for handler in self.client.message_handlers if isinstance(handler, CommandHandler)]
		commands = [command for command in commands if startswith(command.name, target)]
		commands.sort(key=lambda command: command.name)

		if long:
			reply = lambda s: Notice(self.client, msg.sender, s).send()
		else:
			reply = lambda s: self.reply(msg, s)

		if target and len(commands) == 0:
			reply("No commands matching {!r} found".format(' '.join(target)))
			return

		if target and len(commands) == 1:
			command, = commands
			summary, description = command.help
			if not description:
				reply("Command {!r} has no help available".format(' '.join(command.name)))
				return
			lines = [line.strip() for line in description.strip().split('\n') if line.strip()]
			if len(lines) > self.config.max_lines and not long:
				reply(summary)
				reply("Full description too long. Use longhelp for full description via PM")
				return
			for line in lines:
				reply(line)
			return

		if len(commands) > self.config.max_lines and not long:
			commands = ', '.join(' '.join(command.name) for command in commands)
			reply("Commands: {}".format(commands))
			reply("Use longhelp for full descriptions via PM")
			return

		for command in commands:
			summary, description = command.help
			if not summary:
				summary = "(no help available)"
			reply("{} - {}".format(' '.join(command.name), summary))
