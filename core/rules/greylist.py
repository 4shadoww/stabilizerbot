import json

from core.rule_core import *
from core import yapi

class YunoModule:

	name = "greylist"
	cfg_ver = None
	list_ver = None
	api = yapi.MWAPI
	config = {
		"expiry": 24,
		"list_path": "Käyttäjä:VakauttajaBot/greylist.json"
	}
	greylist = None

	def run(self, rev):
		score = 0
		expiry = None

		lastrev = self.api.getLatestRev(self.config["list_path"])

		if not lastrev:
			logger.critical("greylist not found")
			return score, expiry

		if lastrev != self.list_ver:
			self.greylist = json.loads(self.api.getText(self.config["list_path"]))
			self.list_ver = lastrev

		for user in self.greylist:
			if user == rev["user"] and self.greylist[user] > score:
				score = self.greylist[user]
				expiry = self.config["expiry"]

		return score, expiry
