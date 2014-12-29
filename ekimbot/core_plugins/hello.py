
from ekimbot.botplugin import BotPlugin, CommandHandler


class HelloPlugin(BotPlugin):
	name = 'hello'

	@CommandHandler('hello', 0)
	def hello(self, msg, *args):
		self.reply(msg, "Hello, {msg.sender}!".format(msg=msg))
		#self.reply(msg, "Hello, {msg.sender}! \xe2\x98\x83".format(msg=msg))
