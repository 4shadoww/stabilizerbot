from core.rule_core import *
from core import mwapi

class YunoModule:

	name = "ores"
	cfg_ver = None

	ores_api = mwapi.ORES()

	config = [
		{
			"models": {
				"damaging": {"max_false": 0.15, "min_true": 0.8},
				"goodfaith": {"min_false": 0.8, "max_true": 0.15}
			},
			"score": 1
		},
		{
			"models": {
				"damaging": {"max_false": 0.1, "min_true": 0.9},
				"goodfaith": {"min_false": 0.9, "max_true": 0.1}
			},
			"score": 2
		}
	]

	def load_config(self):
		if core.config.config_mode == "online":
			pass

	def getScores(self, rev):
		tries = 2
		revid_data = 1
		# Check result and check for errors
		# If error faced then try again once
		for i in reversed(range(tries)):
			scores = self.ores_api.getScore([rev["revision"]["new"]])
			revid_data = scores[str(rev["revision"]["new"])]

			for item in revid_data:
				if "error" in revid_data[item] and "probability" not in revid_data[item]:
					if i <= 0:
						printlog("error: failed to fetch ores revision data:", revid_data)
						return False
				else:
					break

		return revid_data

	def run(self, rev):
		score = 0
		expiry = None

		revid_data = self.getScores(rev)

		if not revid_data:
			return score, expiry

		for rule in self.config:
			failed = False

			for item in rule["models"]:
				if failed:
					break

				for value in rule["models"][item]:
					if value == "max_false" and rule["models"][item][value] < revid_data[item]["probability"]["false"]:
						failed = True
						break
					elif value == "min_false" and rule["models"][item][value] > revid_data[item]["probability"]["false"]:
						failed = True
						break
					elif value == "max_true" and rule["models"][item][value] < revid_data[item]["probability"]["true"]:
						failed = True
						break
					elif value == "min_true" and rule["models"][item][value] > revid_data[item]["probability"]["true"]:
						failed = True
						break

			if not failed and rule["score"] > score:
				score = rule["score"]
				expiry = rule["expiry"]

		return score, expiry
