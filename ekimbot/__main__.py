
import sys

from main import main

options = {}
for arg in sys.argv[1:]:
	k, v = arg.split('=', 1)
	options[k] = v

main(**options)
