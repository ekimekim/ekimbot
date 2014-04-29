
import sys

from main import main

options = {}
for arg in sys.argv:
	k, v = arg.split('=', 1)
	options[k] = v

main(**options)
