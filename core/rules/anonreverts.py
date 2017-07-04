from core.rule_core import *
from core import op
from core import yapi

api = yapi.MWAPI

class YunoModule:

	name = "anonreverts"
	cfg_ver = None

	config = [
		{
			"expiry": 24,
			"hours": 1,
			"reverts_required": 2,
			"score": 1,
			"groups": ["autoconfirmed"]
		}
	]

	def run(self, rev):
		for rule in self.config:
			reverts = op.getReverts(rev["title"], hours=rule["hours"])
			ip_reverts = 0

			if len(reverts) >= rule["reverts_required"]:
				for revert in reverts:
					if revert["reverter"] != revert["victim"]:
						if all(i not in api.getUserRights(revert["victim"]) for i in rule["groups"]) or all(i not in api.getUserRights(revert["reverter"]) for i in rule["groups"]):
							ip_reverts += 1

		if ip_reverts >= rule["reverts_required"]:
			return rule["score"], rule["expiry"]

		return 0, None
