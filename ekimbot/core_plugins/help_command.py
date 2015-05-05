
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
	defaults = {'max_lines': 10}

	@CommandHandler("help", 0)
	def help_command(self, msg, *target):
		target = [part.lower() for part in target]
		commands = [handler for handler in self.client.message_handlers if isinstance(handler, CommandHandler)]
		commands = [command for command in commands if startswith(command.name, target)]
		commands.sort(key=lambda command: command.name)

		if target and len(commands) == 0:
			self.reply(msg, "No commands matching {!r} found".format(' '.join(target)))
			return

		if target and len(commands) == 1:
			command, = commands
			summary, description = command.help
			if not description:
				self.reply(msg, "Command {!r} has no help available".format(' '.join(command.name)))
				return
			for line in description.strip().split('\n'):
				line = line.strip()
				if not line: continue
				self.reply(msg, line)
			return

		if len(commands) > self.config.max_lines:
			commands = ', '.join(' '.join(command.name) for command in commands)
			self.reply(msg, "Commands: {}".format(commands))
			return

		for command in commands:
			summary, description = command.help
			if not summary:
				summary = "(no help available)"
			self.reply(msg, "{} - {}".format(' '.join(command.name), summary))
