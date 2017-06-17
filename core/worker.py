# Import python modules
import datetime
import time
import json
from sseclient import SSEClient as EventSource
from threading import Thread

# Import core modules
from core import config_loader as cfgl
from core import rule_executor
from core import mwapi
from core.log import *
from core import path

# Object that sends kill signal to ConfigUpdater thread
class Killer:
	kill = False

# Updates config when changed every 30 seconds
class ConfigUpdate(Thread):

	killer = None

	def __init__(self, killer):
		self.killer = killer
		super(ConfigUpdate, self).__init__()

	def run(self):
		if cfgl.current_config["core"]["config_mode"] == "online":
			printlog("online config mode enabled")
		else:
			printlog("local config mode enabled")

		uf = 30
		times = uf
		while True:
			if self.killer.kill:
				return
			if times >= uf:
				times = 0
				if cfgl.current_config["core"]["config_mode"] == "online":
					cfgl.checkForOnlineUpdate()
				else:
					cfgl.checkForLocalUpdate()

			if self.killer.kill:
				return

			time.sleep(0.5)
			times += 0.5

class Worker:
	r_exec = None
	killer = None
	cf_updater = None
	api = mwapi.MWAPI()
	f = open(path.main()+"core/dict.json")
	dictionary = json.load(f)

	def __init__(self):
		self.r_exec = rule_executor.Executor()
		# Init ConfigUpdater
		self.killer = Killer()
		self.cf_updater = ConfigUpdate(self.killer)
		self.cf_updater.start()

	def shouldCheck(self, rev):
		# Check should revision to be checked at all
		revs = self.api.getRevision([rev["revision"]["new"]])

		if "badrevids" in revs["query"]:
			return False

		if self.api.stabilized(rev["title"]):
			return False

		if not self.api.reviewed:
			return False

		return True

	def stabilize(self, rev, expiry):
		# Calculate expiry
		dtexpiry = datetime.datetime.utcnow() + datetime.timedelta(hours=expiry, minutes=0, seconds=0)
		strexpiry = dtexpiry.strftime("%Y-%m-%dT%H:%M:%SZ")
		# Stabilize
		revlink = "[[Special:Diff/"+str(rev["revision"]["new"])+"|"+str(rev["revision"]["new"])+"]]"

		reason = self.dictionary[cfgl.current_config["core"]["lang"]]["reasons"]["YV1"] % revlink

		self.api.stabilize(rev["title"], reason, expiry=strexpiry)

		return True

	def run(self):
		try:
			wiki = cfgl.current_config["core"]["lang"]+"wiki"
			# Event stream
			for event in EventSource(cfgl.current_config["core"]["stream_url"]):
				# Filter event stream
				if event.event == 'message':
					try:
						change = json.loads(event.data)
					except ValueError:
						continue

					if change["wiki"] == wiki and change["type"] == "edit" and change["namespace"] in cfgl.current_config["core"]["namespaces"]:
						# Check should revision to be checked at all
						if self.shouldCheck(change):
							expiry = self.r_exec.shouldStabilize(change)
							if expiry and not cfgl.current_config["core"]["test"]:
								self.stabilize(change, expiry)

		except KeyboardInterrupt:
			print("terminating yuno...")
			self.killer.kill = True
			self.cf_updater.join()
