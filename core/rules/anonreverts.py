from core.rule_core import *

class YunoModule:

	name = "anonreverts"
	cfg_ver = None

	config = [
		{
			"hours": 1,
			"reverts_required": 2,
			"score": 1,
			"groups": ["autoconfirmed"]
		}
	]

	def run(self, rev):
		site = pywikibot.Site()

		for rule in self.config:
			edits = op.createEditList(rev["title"], end_hours=rule["hours"])
			reverts = op.getRevertList(edits, end_hours=rule["hours"])
			ip_reverts = 0

			if len(reverts) >= rule["reverts_required"]:
				for revert in reverts:
					reverter = pywikibot.User(site, title=revert["reverter"])
					victim = pywikibot.User(site, title=revert["victim"])

					if all(i not in victim.groups() for i in rule["groups"]) or  all(i not in reverter.groups() for i in rule["groups"]):
						ip_reverts += 1

		if ip_reverts >= rule["reverts_required"]:
			return rule["score"]

		return 0
