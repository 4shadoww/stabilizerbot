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


	def run(self):
		api = APISite("fi")
		timeutc = datetime.datetime(2017, 4, 21, 11, 20, 0, 0)
		oldtime = datetime.datetime(2017, 4, 21, 11, 0, 0, 0)

		for rev in api.recentchanges(start=timeutc, end=oldtime):
			if rev["user"] == "4shadoww":
				self.r_exec.shouldProtect(rev["title"])
