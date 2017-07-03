# Import python modules
import datetime
import time
import json
from sseclient import SSEClient as EventSource
from threading import Thread
import sys
import resource
import traceback

# Import core modules
from core import config_loader as cfgl
from core import rule_executor
from core import mwapi
from core.log import *
from core import path

api = mwapi.MWAPI()

def shouldCheck(rev):
	# Check should revision to be checked at all
	revs = api.getRevision([rev["revision"]["new"]])

	if "badrevids" in revs["query"]:
		return False

	if api.stabilized(rev["title"]):
		return False

	if not api.reviewed:
		return False

	return True

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

class Stabilizer(Thread):

	killer = None
	f = open(path.main()+"core/dict.json")
	dictionary = json.load(f)
	api = mwapi.MWAPI()

	def __init__(self, killer, rev, expiry):
		self.killer = killer
		self.rev = rev
		self.expiry = expiry
		super(Stabilizer, self).__init__()

	def stabilize(self):
		# Calculate expiry
		dtexpiry = datetime.datetime.utcnow() + datetime.timedelta(hours=self.expiry, minutes=0, seconds=0)
		strexpiry = dtexpiry.strftime("%Y-%m-%dT%H:%M:%SZ")
		# Set reason
		revlink = "[[Special:Diff/"+str(self.rev["revision"]["new"])+"|"+str(self.rev["revision"]["new"])+"]]"
		reason = self.dictionary[cfgl.current_config["core"]["lang"]]["reasons"]["YV1"] % revlink

		# Stabilize
		api.stabilize(self.rev["title"], reason, expiry=strexpiry)

		return True

	def run(self):
		times = 0
		while times < cfgl.current_config["core"]["s_delay"]:
			if self.killer.kill:
				return False
			time.sleep(0.5)
			times += 0.5

		if shouldCheck(self.rev):
			self.stabilize()
		return True

class Worker:
	r_exec = None
	killer = None
	cf_updater = None

	def __init__(self):
		self.r_exec = rule_executor.Executor()
		# Init ConfigUpdater
		self.killer = Killer()
		self.cf_updater = ConfigUpdate(self.killer)
		self.cf_updater.start()

	def run(self):
		try:
			statusreport("starting...")
			laststatus = datetime.datetime.utcnow()

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
						if shouldCheck(change):
							expiry = self.r_exec.shouldStabilize(change)
							usagereport("memory usage:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
							if datetime.datetime.utcnow() - laststatus >= datetime.timedelta(hours=0, minutes=0, seconds=cfgl.current_config["core"]["status_lps"]):
								laststatus = datetime.datetime.utcnow()
								statusreport("running...")

							if expiry and not cfgl.current_config["core"]["test"]:
								#self.stabilize(change, expiry)
								stabilizer = Stabilizer(self.killer, change, expiry)
								stabilizer.start()

		except KeyboardInterrupt:
			print("terminating stabilizer...")
			self.killer.kill = True
			self.cf_updater.join()
		except:
			printlog("error: faced unexcepted error check crash report")
			crashreport(traceback.format_exc())
			printlog("terminating threads")
			sys.exit(1)
