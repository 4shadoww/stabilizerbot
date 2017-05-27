# Import python modules
import importlib
import traceback

# Import core modules
from core import config_loader
from core.log import *

class Executor:
	rules = []
	last_rules = None

	def __init__(self):
		self.loadRules()

	def loadRules(self):
		if self.last_rules != config_loader.core_config["rules"]:
			printlog("loading rules")
			self.last_rules = config_loader.core_config["rules"]
			for rule in config_loader.core_config["rules"]:
				if rule not in config_loader.core_config["ign_rules"]:
					try:
						module = importlib.import_module("core.rules."+rule)
						self.rules.append(module.YunoModule())
					except ModuleNotFoundError:
						printlog("error module \""+ rule +"\" not found")

	def shouldStabilize(self, rev):
		overall_score = 0
		self.loadRules()
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
				printlog("unexcepted error on", rule.name, "check crasreport")
				crashreport(traceback.format_exc())

		if overall_score >= config_loader.core_config["required_score"]:
			if config_loader.core_config["log_decision"] == "positive" or config_loader.core_config["log_decision"] == "both":
				logdecision(rev["title"], rev["revision"]["new"], rev["user"])
			return True

		return False
