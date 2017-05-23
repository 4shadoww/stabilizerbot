# Import python modules
import importlib

# Import core modules
import core.config
from core.log import *

class Executor:
	rules = []

	config = {
		"required_score": 2,
	}

	def __init__(self):
		for rule in core.config.rules:
			module = importlib.import_module("core.rules."+rule)
			self.rules.append(module.YunoModule())

	def shouldStabilize(self, rev):
		overall_score = 0

		for rule in self.rules:
			score = rule.run(rev)
			printlog(rule.name, "on page:", rev["title"],  "score:", score)

			if score < 0:
				return False

			score += overall_score

		if overall_score >= self.config["required_score"]:
			return True

		return False
