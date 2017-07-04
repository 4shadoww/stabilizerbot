# Import python modules
import importlib
import traceback
import sys
import logging

# Import core modules
from core import config_loader

# Get logger
logger = logging.getLogger("infolog")

class Executor:
	rules = []
	last_rules = None

	# Load rules that are listed in config.json at core or in online config
	def loadRules(self):
		if self.last_rules != config_loader.cur_conf["core"]["rules"]:
			self.rules = []
			logger.info("loading rules")
			self.last_rules = config_loader.cur_conf["core"]["rules"]
			for rule in config_loader.cur_conf["core"]["rules"]:
				if rule not in config_loader.cur_conf["core"]["ign_rules"]:
					try:
						module = importlib.import_module("core.rules."+rule)
						self.rules.append(module.YunoModule())
					except ModuleNotFoundError:
						logger.error("module \"%s\" not found" % rule)

	# Check every rule and return True if needed score is reached
	def shouldStabilize(self, rev):
		overall_score = 0
		final_expiry = 0
		self.loadRules()
		scores = {}
		for rule in self.rules:
			try:
				if rule.cfg_ver != config_loader.cfg_ver and rule.name in config_loader.cur_conf["rules"]:
					logger.info("updating config for %s" % rule.name)
					rule.config = config_loader.cur_conf["rules"][rule.name]
					rule.cfg_ver = config_loader.cfg_ver

				score, expiry = rule.run(rev)
				scores[rule.name] = score
				logger.info("%s on page: %s score: %s" % (rule.name, rev["title"], str(score)))

				if score < 0:
					return False

				overall_score += score

				if expiry and final_expiry < expiry:
					final_expiry = expiry
			except KeyboardInterrupt:
				print("terminating yuno...")
				sys.exit(0)

			except:
				scores[rule.name] = 0
				logger.error("unexcepted error on %s check crasreport" % rule.name)
				logger.critical(traceback.format_exc())

		if overall_score >= config_loader.cur_conf["core"]["required_score"]:
			if config_loader.cur_conf["core"]["log_decision"] == "positive" or config_loader.cur_conf["core"]["log_decision"] == "both":
				logdecision(rev["title"], rev["revision"]["new"], rev["user"], rev["timestamp"], scores)
			return final_expiry

		if config_loader.cur_conf["core"]["log_decision"] == "negative" or config_loader.cur_conf["core"]["log_decision"] == "both":
			logdecision(rev["title"], rev["revision"]["new"], rev["user"], rev["timestamp"], scores)

		return False
