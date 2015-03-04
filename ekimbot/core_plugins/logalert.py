
import logging
import os
import smtplib
import socket
from email.MIMEText import MIMEText

import gevent

from ekimbot.botplugin import BotPlugin
from ekimbot.config import config


def send(target, subject, text):
	args = config.logalert

	msg = MIMEText(text)
	msg['From'] = args['smtp_user']
	msg['To'] = target
	msg['Subject'] = subject

	server = smtplib.SMTP(*args['smtp_server'])
	server.ehlo() # Send greeting
	server.starttls() # Switch to SSL
	server.ehlo() # Send greeting again now that we're on SSL
	server.login(args['smtp_user'], args['smtp_password'])
	server.sendmail(args['smtp_user'], target, msg.as_string())
	server.close()


class EmailHandler(logging.Handler):
	LIMIT = 10
	LIMIT_INTERVAL = 3600

	def __init__(self, level=0):
		super(EmailHandler, self).__init__(level)
		if config.logalert is None:
			raise ValueError("Cannot start log alerting; no configration given")
		self.target = config.logalert['target']
		self.limit = self.LIMIT
		self.limit_reset = gevent.spawn(self._limit_reset)

	def _limit_reset(self):
		while True:
			gevent.sleep(self.LIMIT_INTERVAL)
			self.limit = self.LIMIT

	def close(self):
		self.limit_reset.kill()
		super(EmailHandler, self).close()

	def emit(self, record):
		try:
			if self.limit <= 0:
				return
			self.limit -= 1
			subject = "Alert from ekimbot process {}@{}".format(os.getpid(), socket.gethostname())
			text = self.format(record)
			if not self.limit:
				text += '\nNote: Rate limit reached. Further alerts will be ignored.'
			send(self.target, subject, text)
		except Exception:
			root_logger = logging.getLogger()
			if self not in root_logger.handlers:
				root_logger.warning("Failed to emit log in {}".format(self), exc_info=True)


class AlertPlugin(BotPlugin):
	"""Sets up a logging handler to email logs above a certain level"""
	name = 'logalert'
	FORMAT = ("%(levelname)s in %(name)s at %(asctime)s\n"
	          "%(message)s\n\n"
	          "Logged from %(funcName)s:%(lineno)s in %(pathname)s\n"
	         )
	target_logger = 'ekimbot'

	@property
	def level(self):
		level = config.logalert.get('level', None) if config.logalert else None
		level = level or 'WARNING'
		return logging._levelNames[level.upper()]

	def init(self):
		self.log_handler = EmailHandler(self.level)
		self.log_handler.setFormatter(logging.Formatter(self.FORMAT))
		logging.getLogger(self.target_logger).addHandler(self.log_handler)

	def cleanup(self):
		logging.getLogger(self.target_logger).removeHandler(self.log_handler)
		self.log_handler.close()
		super(AlertPlugin, self).cleanup()
