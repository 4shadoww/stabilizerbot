# Import python modules
import datetime
import time
import json
from sseclient import SSEClient as EventSource
from threading import Thread

# Import pywikibot
import pywikibot
from pywikibot.site import APISite
from pywikibot.pagegenerators import RepeatingGenerator

# Import tinydb
#from tinydb import TinyDB, Query

# Import core modules
from core import config_loader
from core import rule_executor
from core import mwapi
from core.log import *

class Killer:
	kill = False

class ConfigUpdate(Thread):

	killer = None

	def __init__(self, killer):
		self.killer = killer
		super(ConfigUpdate, self).__init__()

	def run(self):
		times = 60
		while True:
			if self.killer.kill:
				return
			if times >= 60:
				times = 0
				config_loader.checkForUpdate()

			if self.killer.kill:
				return

			time.sleep(0.5)
			times += 0.5

class Worker:
	r_exec = None
	site = pywikibot.Site()
	#db = TinyDB("db/revid.json")
	#rev = Query()
	killer = None
	cf_updater = None

	def __init__(self):
		self.r_exec = rule_executor.Executor()
		if config_loader.core_config["config_mode"] == "online":
			printlog("online mode enabled")
			self.killer = Killer()
			self.cf_updater = ConfigUpdate(self.killer)
			self.cf_updater.start()

	def shouldCheck(self, revid):
		api = mwapi.MWAPI()
		rev = api.getRevision([revid])
		if "badrevids" in rev["query"]:
			return False

		return True

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
		try:
			wiki = config_loader.core_config["lang"]+"wiki"
			for event in EventSource(config_loader.core_config["stream_url"]):
				if event.event == 'message':
					try:
						change = json.loads(event.data)
					except ValueError:
						continue

					if change["wiki"] == wiki and change["type"] == "edit" and change["namespace"] in config_loader.core_config["namespaces"]:
						if self.shouldCheck(change["revision"]["new"]):
							print(self.r_exec.shouldStabilize(change))
		except KeyboardInterrupt:
			print("terminating yuno...")
			if config_loader.core_config["config_mode"] == "online":
				self.killer.kill = True
				self.cf_updater.join()
