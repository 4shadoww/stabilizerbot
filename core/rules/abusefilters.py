from core.rule_core import *
from core import mwapi
import datetime

class YunoModule:

	name = "abusefilters"
	cfg_ver = None

	config = {
		"filters": [11, 30, 34, 38, 55, 58, 98, 125, 133],
		"hours": 1,
		"rules": [
			{
				"hits": 1,
				"score": 1
			},
			{
				"hits": 5,
				"score": 2
			}
		]
	}

	api = mwapi.MWAPI()

	def run(self, rev):
		score = 0

		end = datetime.timedelta(hours=self.config["hours"], minutes=0, seconds=0)
		timeutc = datetime.datetime.utcnow()

		time = timeutc-end
		time = time.strftime('%Y-%m-%dT%H:%M:%SZ')

		result = self.api.getAbuseFiler(rev["user"], time, self.config["filters"])

		if "error" in result:
			printlog("abusefilters error:",result["error"]["code"])
			return score

		for rule in self.config["rules"]:
			if rule["hits"] <= len(result["query"]["abuselog"]):
				if score < rule["score"]:
					score = rule["score"]

		return score
