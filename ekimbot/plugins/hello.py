
from ekimbot.main import client


@client.add_handler(command='PRIVMSG')
def hello(client, msg):
	if client.nick not in msg.payload:
		return
	reply = [msg.sender if target == client.nick else target for target in msg.targets]
	client.msg(reply, "Hello, {}!".format(msg.sender))
