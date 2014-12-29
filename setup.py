from setuptools import setup, find_packages

setup(
	name='ekimbot',
	description='Just another IRC Bot',
	requires=[
		"girc",
		"gevent(>=1.0)",
	],
	packages=find_packages(),
)
