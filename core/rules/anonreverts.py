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
			ip_reverts = 0
			reverts = op.getReverts(rev["title"], hours=rule["hours"])
			if not reverts:
				continue
			if len(reverts) >= rule["reverts_required"]:
				for revert in reverts:
					if revert["reverter"] != revert["victim"]:
						victim_groups = api.getUserRights(revert["victim"])
						reverter_groups = api.getUserRights(revert["reverter"])
						
						if not victim_groups or not reverter_groups:
							continue

						if all(i not in victim_groups for i in rule["groups"]) or all(i not in reverter_groups for i in rule["groups"]):
							ip_reverts += 1

		if ip_reverts >= rule["reverts_required"]:
			return rule["score"], rule["expiry"]

		return 0, None
