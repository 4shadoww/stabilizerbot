# Import python modules
import importlib

# Import pywikibot
import pywikibot
from pywikibot.site import APISite

# Import core modules
import core.config
from core.log import *

class Executor:

	site = pywikibot.Site()
	rules = []

	config = {
		"required_score": 2,
	}

	def __init__(self):
		for rule in core.config.rules:
			module = importlib.import_module("core.rules."+rule)
			self.rules.append(module.YunoModule())

	def shouldProtect(self, revid):
		overall_score = 0

		api = APISite("fi")

		

		for rule in self.rules:
			score = rule.run(title)
			printlog(rule.name, "on page:", title,  "score:", score)

			if score < 0:
				return False

			score += overall_score

		if overall_score >= self.config["required_score"]:
			return True

		return False
