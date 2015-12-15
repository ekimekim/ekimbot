
import gevent.monkey
gevent.monkey.patch_all()

from main import main
main()
