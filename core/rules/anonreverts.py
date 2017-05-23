from core.rule_core import *

class YunoModule:

	name = "annonreverts"

	config = {
		"hours": 1,
		"reverts_required": 1,
	}

	def run(self, rev):
		site = pywikibot.Site()
		edits = op.createEditList(rev["title"], end_hours=self.config["hours"])
		reverts = op.getRevertList(edits, end_hours=self.config["hours"])

		ip_reverts = 0

		if len(reverts) >= self.config["reverts_required"]:
			for rev in reverts:
				reverter = pywikibot.User(site, title=rev["reverter"])
				victim = pywikibot.User(site, title=rev["victim"])

				if "autoconfirmed" not in victim.groups() or "autoconfirmed" not in reverter.groups():
					ip_reverts += 1

		if ip_reverts >= self.config["reverts_required"]:
			return 1

		return 0
