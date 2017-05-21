# Import python modules
import datetime
import time

# Import pywikibot
import pywikibot
from pywikibot.site import APISite

# Import core modules
from core import op
from core import rule_executor

class Worker:
	r_exec = None

	def __init__(self):
		self. r_exec = rule_executor.Executor()

	def checked(self, title):
		

	def run(self):
		site = pywikibot.Site()

		api = APISite("fi")
		#timeutc = datetime.datetime(2017, 4, 21, 11, 20, 0, 0)
		timeutc = datetime.datetime.utcnow()
		#oldtime = datetime.datetime(2017, 4, 21, 11, 0, 0, 0)
		oldtime = timeutc-datetime.timedelta(hours=12, minutes=0, seconds=0)

		for rev in api.recentchanges(start=timeutc, end=oldtime, namespaces=[0]):
			page = pywikibot.Page(site, rev["title"])
			if page.exists() and not self.checked(rev["title"]):
				print(self.r_exec.shouldProtect(rev["title"]))
