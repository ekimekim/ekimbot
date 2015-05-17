
import os
import json
import weakref


class _StoreMeta(type):
	# provides singleton mechanics for Store based on filepath
	_stores = weakref.WeakValueDictionary()
	def __call__(self, filepath):
		if filepath not in self._stores:
			new_store = super(_StoreMeta, self).__call__(filepath)
			self._stores[filepath] = new_store
		return self._stores[filepath]


class Store(object):
	"""Provides means for an easy to use JSON store as a file."""
	__metaclass__ = _StoreMeta

	def __init__(self, filepath):
		self.filepath = filepath
		self.load()

	def load(self):
		if not os.path.exists(self.filepath):
			self.data = {}
			self.save()
			return
		with open(self.filepath) as f:
			self.data = json.load(f)

	def save(self):
		# write-then-rename for atomic overwrite
		tmpfile = "{}.tmp".format(self.filepath)
		with open(tmpfile, 'w') as f:
			f.write(json.dumps(self.data, indent=4))
		os.rename(tmpfile, self.filepath)
