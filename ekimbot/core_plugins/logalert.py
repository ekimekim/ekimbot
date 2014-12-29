
import logging
import smtplib
import socket
from email.MIMEText import MIMEText

import gevent

from ekimbot.botplugin import BotPlugin
from ekimbot.config import config


def send(subject, text):
	args = config.logalert

	msg = MIMEText(text)
	msg['From'] = args.smtp_user
	msg['To'] = args.target
	msg['Subject'] = subject

	server = smtplib.SMTP(*args.smtp_server)
	server.ehlo() # Send greeting
	server.starttls() # Switch to SSL
	server.ehlo() # Send greeting again now that we're on SSL
	server.login(args.smtp_user, args.smtp_password)
	server.sendmail(args.smtp_user, args.target, msg.as_string())
	server.close()


class EmailHandler(logging.Handler):
	LIMIT = 10
	LIMIT_INTERVAL = 3600

	def __init__(self, client, level=0):
		super(EmailHandler, self).__init__(level)
		self.client = client
		if config.logalert is None:
			raise ValueError("Cannot start log alerting; no configration given")
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
		if self.limit <= 0:
			return
		self.limit -= 1
		subject = "Alert from ekimbot instance {self.client._nick}@{self.client.host}:{self.client.port}".format(self=self)
		text = self.format(record)
		if not self.limit:
			text += '\nNote: Rate limit reached. Further alerts will be ignored.'
		send(subject, text)


class AlertPlugin(BotPlugin):
	"""Sets up a logging handler to email logs above a certain level"""
	name = 'logalert'
	LEVEL = logging.WARNING
	FORMAT = ("%(levelname)s in %(name)s at %(asctime)s\n"
	          "%(message)s\n\n"
	          "Logged from %(funcName)s:%(lineno)s in %(pathname)s\n"
	          "From process %(process)d on {}\n"
	         ).format(socket.gethostname())

	def init(self):
		self.log_handler = EmailHandler(self.client, self.LEVEL)
		self.log_handler.setFormatter(logging.Formatter(self.FORMAT))
		self.client.logger.addHandler(self.log_handler)

	def cleanup(self):
		self.log_handler.close()
		super(AlertPlugin, self).cleanup()
