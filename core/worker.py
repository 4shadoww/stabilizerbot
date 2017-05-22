# Import python modules
import datetime
import time

# Import pywikibot
import pywikibot
from pywikibot.pagegenerators import RepeatingGenerator

# Import tinydb
from tinydb import TinyDB, Query

# Import core modules
from core import op
from core import rule_executor

class Worker:
	r_exec = None
	site = pywikibot.Site()
	db = TinyDB("db/revid.json")
	rev = Query()

	config = {
		"sleep_duration": 5
	}

	def __init__(self):
		self. r_exec = rule_executor.Executor()

	def checked(self, title):
		result = self.db.search(self.rev.title == title)
		page = pywikibot.Page(self.site, title)
		latestrev = page.latestRevision()

		if len(result) > 0 and result[0]["revid"] == latestrev:
			return True

		# Update database
		if len(result) > 0:
			self.db.update({"revid": latestrev}, self.rev.title == title)
		else:
			self.db.insert({"title": title, "revid": latestrev})

		return False

	def run(self):

		for rev in RepeatingGenerator(self.site.recentchanges, lambda x: x['revid'], sleep_duration=self.config["sleep_duration"]):
			#print(rev)
			print(self.r_exec.shouldProtect(rev["revid"]))
