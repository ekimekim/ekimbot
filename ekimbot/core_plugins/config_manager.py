
from ekimbot.botplugin import BotPlugin, CommandHandler
from ekimbot.config import config


class ConfigManagerPlugin(BotPlugin):

	@CommandHandler('config load', 1)
	def load_config(self, *args):
		path = ' '.join(args)
		try:
			config.from_file(path)
		except Exception as ex:
			self.reply("Failure to load config file {!r} with {}: {}".format(path, type(ex).__name__, ex))
		else:
			self.reply("Config file {!r} loaded".format(path))

	@CommandHandler('config set', 2)
	def set_config(self, key, *value):
		value = ' '.join(value)
		try:
			value = ast.literal_eval(value)
		except SyntaxError:
			pass
		config[key] = value
		self.reply('set config.{} = {!r}'.format(key, value))
