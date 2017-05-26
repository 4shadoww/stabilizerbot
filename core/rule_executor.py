# Import python modules
import importlib
import traceback

# Import core modules
from core import config_loader
from core.log import *

class Executor:
	rules = []

	def __init__(self):
		for rule in config_loader.core_config["rules"]:
			if rule not in config_loader.core_config["ign_rules"]:
				module = importlib.import_module("core.rules."+rule)
				self.rules.append(module.YunoModule())

	def shouldStabilize(self, rev):
		overall_score = 0

		for rule in self.rules:
			try:
				if config_loader.core_config["config_mode"] == "online" and rule.cfg_ver != config_loader.cfg_ver:
					printlog("updating config for", rule.name)
					rule.config = config_loader.online_config["rules"][rule.name]
					rule.cfg_ver = config_loader.cfg_ver

				score = rule.run(rev)
				printlog(rule.name, "on page:", rev["title"],  "score:", score)

				if score < 0:
					return False

				overall_score += score
			except:
				crashreport(traceback.format_exc())

		if overall_score >= config_loader.core_config["required_score"]:
			return True

		return False
