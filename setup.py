from setuptools import setup, find_packages

setup(
	name='ekimbot',
	description='Just another IRC Bot',
	requires=[
		"geventirc",
		"gevent>=1.0",
	],
	packages=find_packages(),
)
