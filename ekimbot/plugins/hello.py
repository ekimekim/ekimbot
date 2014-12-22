
from ekimbot.main import BotPlugin


class HelloPlugin(BotPlugin):
	name = 'hello'

	def init(self):
		self.client.add_handler(self.hello, command='PRIVMSG')

	def hello(self, client, msg):
		if client.nick not in msg.payload:
			return
		reply = [msg.sender if target == client.nick else target for target in msg.targets]
		client.msg(reply, "Hello, {}!".format(msg.sender))

	def cleanup(self):
		self.client.rm_handler(self.hello)
