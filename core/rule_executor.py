# Import python modules
import importlib

# Import core modules
import core.config
from core.log import *

class Executor:

	rules = []

	def __init__(self):
		for rule in core.config.rules:
			module = importlib.import_module("core.rules."+rule)
			self.rules.append(module.YunoModule())

	def shouldProtect(self, title):
		for rule in self.rules:
			printlog(rule.name, "on page:", title)

			if rule.run(title):
				return True

			return False
