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

	# Load rules that are listed in config.json or in online config
	def loadRules(self):
		if self.last_rules != config_loader.current_config["core"]["rules"]:
			printlog("loading rules")
			self.last_rules = config_loader.current_config["core"]["rules"]
			for rule in config_loader.current_config["core"]["rules"]:
				if rule not in config_loader.current_config["core"]["ign_rules"]:
					try:
						module = importlib.import_module("core.rules."+rule)
						self.rules.append(module.YunoModule())
					except ModuleNotFoundError:
						printlog("error module \""+ rule +"\" not found")

	# Check every rule and return True if needed score is reached
	def shouldStabilize(self, rev):
		overall_score = 0
		self.loadRules()
		scores = {}

		for rule in self.rules:
			try:
				if rule.cfg_ver != config_loader.cfg_ver and rule.name in config_loader.current_config["rules"]:
					printlog("updating config for", rule.name)
					rule.config = config_loader.current_config["rules"][rule.name]
					rule.cfg_ver = config_loader.cfg_ver

				score = rule.run(rev)
				scores[rule.name] = score
				printlog(rule.name, "on page:", rev["title"],  "score:", score)

				if score < 0:
					return False

				overall_score += score
			except:
				scores[rule.name] = 0
				printlog("unexcepted error on", rule.name, "check crasreport")
				crashreport(traceback.format_exc())

		if overall_score >= config_loader.current_config["core"]["required_score"]:
			if config_loader.current_config["core"]["log_decision"] == "positive" or config_loader.current_config["core"]["log_decision"] == "both":
				logdecision(rev["title"], rev["revision"]["new"], rev["user"], rev["timestamp"], scores)
			return True

		if config_loader.current_config["core"]["log_decision"] == "negative" or config_loader.current_config["core"]["log_decision"] == "both":
			logdecision(rev["title"], rev["revision"]["new"], rev["user"], rev["timestamp"], scores)

		return False
