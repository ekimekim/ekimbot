
from ekimbot.botplugin import ClientPlugin
from ekimbot.commands import EkimbotHandler, CommandHandler


class DidYouMeanPlugin(ClientPlugin):
	name = 'didyoumean'

	@EkimbotHandler(
		command='PRIVMSG',
		payload=lambda client, s: s.startswith(client.config['command_prefix']),
	)
	def didyoumean(self, client, msg):
		"""Matches if command prefix is present.
		Runs after all CommandHandlers and, if none of them matched, responds with an error
		and optionally suggestions for the intended command."""
		if msg.extra.get('command_matched'):
			# A command succesfully matched, we don't need to do anything
			return

		# We make a simple effort to work out what the user might have meant:
		# If a word prefix matches, we try to find something at a close edit distance
		# for the non-matching part. If not, we sugggest 'help PREFIX' (if help enabled),
		# or just 'no such subcommand'.
		# Otherwise, if the whole thing is close in edit distance to one match, we suggest it,
		# or just 'no such command'.

		words = msg.payload[len(client.config['command_prefix']):].split()
		names = [h.name for h in client.message_handlers if isinstance(h, CommandHandler)]
		help_enabled = ClientPlugin.get_plugin('help', client)

		if not words:
			# special case - no command given
			self.reply(msg, "Yes, what?")
			return

		longest_word_prefix = []
		for name in names:
			common_prefix = []
			for got, want in zip(words, name):
				if got != want:
					break
				common_prefix.append(want)
			if len(longest_word_prefix) < len(common_prefix):
				longest_word_prefix = common_prefix

		if longest_word_prefix:
			if longest_word_prefix == words:
				# special case: words is an exact prefix of some command group
				self.reply(msg, "{words!r} is a command group, please specify a subcommand{help}".format(
					words=' '.join(words),
					help=(
						' or try {command_prefix}help {prefix}' if help else ''
					).format(
						command_prefix=self.client.config['command_prefix'],
						prefix=' '.join(words),
					),
				))
				return
			n = len(longest_word_prefix)
			match = self.find_close(
				words[n],
				set(name[n] for name in names if name[:n] == longest_word_prefix),
			)
			if match:
				self.reply_with(msg, words[n], match, prefix=longest_word_prefix)
			else:
				self.reply_with(msg, words[n], prefix=longest_word_prefix, help=help_enabled)
			return

		match = self.find_close(words[0], set(name[0] for name in names))
		if match:
			self.reply_with(msg, words[0], match)
		else:
			self.reply_with(msg, words[0])

	def reply_with(self, msg, word, match=None, prefix=(), help=False):
		reply = "No such {command}{didyoumean}{help}".format(
			command=(
				'subcommand {word!r} in group {prefix!r}' if prefix else 'command {word!r}'
			).format(word=word, prefix=' '.join(prefix)),
			didyoumean=(
				', did you mean {!r}?' if match else ''
			).format(match),
			help=(
				', try {command_prefix}help {prefix}' if help else ''
			).format(
				command_prefix=self.client.config['command_prefix'],
				prefix=' '.join(prefix),
			),
		)
		self.reply(msg, reply)

	def find_close(self, got, corpus):
		"""Returns a string from corpus if it is within some edit distance of got,
		and nothing else is. Otherwise returns None."""
		pass # TODO later
