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

	def run(self, rev):
		scores = self.ores_api.getScore([rev["revision"]["new"]])

		revid_data = scores[str(rev["revision"]["new"])]

		score = 0

		for rule in self.config:
			failed = False

			for item in rule["models"]:
				if failed:
					break

				for value in rule["models"][item]:
					if "probability" not in revid_data[item]:
						crashreport(revid_data)

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

		return score
