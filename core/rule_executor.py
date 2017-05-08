# Import python modules
import importlib

# Import core modules
import core.config

class Executor:

	rules = []

	def __init__(self):
		for rule in core.config.rules:
			module = importlib.import_module("core.rules."+rule)
			self.rules.append(module.YunoModule())

	def shouldProtect(self, page):
		for rule in self.rules:
			rule.run(page)
