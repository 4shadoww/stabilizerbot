from core.rule_core import *
from core import mwapi
import datetime

class YunoModule:

	name = "abusefilters"

	config = {
		"filters": [11, 30, 34, 38, 55, 58, 98, 133],
		"hours": 1,
		"rules": {
			"0": {
				"hits": 1,
				"score": 1
			},
			"1": {
				"hits": 5,
				"score": 2
			}
		}
	}

	api = mwapi.MWAPI()

	def run(self, rev):
		score = 0

		end = datetime.timedelta(hours=self.config["hours"], minutes=0, seconds=0)
		timeutc = datetime.datetime.utcnow()

		time = timeutc-end
		time = time.strftime('%Y-%m-%dT%H:%M:%SZ')

		result = self.api.getAbuseFiler(rev["user"], time, self.config["filters"])

		for rule in self.config["rules"]:
			if self.config["rules"][rule]["hits"] <= len(result["query"]["abuselog"]):
				if score < self.config["rules"][rule]["score"]:
					score = self.config["rules"][rule]["score"]

		return score