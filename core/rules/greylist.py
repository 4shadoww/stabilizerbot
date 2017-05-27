from core.rule_core import *
import json

class YunoModule:

	name = "greylist"
	cfg_ver = None

	site = pywikibot.Site()
	list_ver = None

	config = {
		"list_path": "Käyttäjä:4shadowwBOT/greylist.json"
	}
	greylist = None

	def run(self, rev):
		score = 0
		page = pywikibot.Page(self.site, self.config["list_path"])

		if page.latestRevision() != self.list_ver:
			self.greylist = json.loads(page.text)

		for user in self.greylist:
			if user == rev["user"] and self.greylist[user] > score:
				score = self.greylist[user]

		return score
