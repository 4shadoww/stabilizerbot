import datetime

from core.rule_core import *
from core import yapi
from core import timelib

class YunoModule:

	name = "abusefilters"
	cfg_ver = None

	config = {
		"filters": [11, 30, 34, 38, 55, 58, 98, 125, 133],
		"hours": 1,
		"rules": [
			{
				"hits": 1,
				"expiry": 24,
				"score": 1
			},
			{
				"hits": 5,
				"expiry": 24,
				"score": 2
			}
		]
	}

	api = yapi.MWAPI

	def run(self, rev):
		score = 0
		expiry = None

		end = datetime.timedelta(hours=self.config["hours"])

		time =  timelib.toString(datetime.datetime.utcnow()-end)

		result = self.api.getAbuseFiler(rev["user"], time, self.config["filters"])

		if "error" in result:
			logger.error("abusefilters error: %s" % result["error"]["code"])
			return score, expiry

		for rule in self.config["rules"]:
			if rule["hits"] <= len(result["query"]["abuselog"]):
				if score < rule["score"]:
					score = rule["score"]
					expiry = rule["expiry"]

		return score, expiry
