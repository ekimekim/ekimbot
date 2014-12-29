
from ekimbot.botplugin import BotPlugin, CommandHandler
from ekimbot.config import config


class ConfigManagerPlugin(BotPlugin):
	name = 'config_manager'

	@CommandHandler('config load', 1)
	def load_config(self, msg, *args):
		path = ' '.join(args)
		try:
			config.from_file(path)
		except Exception as ex:
			self.reply(msg, "Failure to load config file {!r} with {}: {}".format(path, type(ex).__name__, ex))
		else:
			self.reply(msg, "Config file {!r} loaded".format(path))

	@CommandHandler('config set', 2)
	def set_config(self, msg, key, *value):
		value = ' '.join(value)
		try:
			value = ast.literal_eval(value)
		except SyntaxError:
			pass
		config[key] = value
		self.reply(msg, 'set config.{} = {!r}'.format(key, value))
