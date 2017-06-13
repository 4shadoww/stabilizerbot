# Import python modules
import datetime
import time
import json
from sseclient import SSEClient as EventSource
from threading import Thread

# Import core modules
from core import config_loader
from core import rule_executor
from core import mwapi
from core.log import *

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
		if config_loader.current_config["core"]["config_mode"] == "online":
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
				if config_loader.current_config["core"]["config_mode"] == "online":
					config_loader.checkForOnlineUpdate()
				else:
					config_loader.checkForLocalUpdate()

			if self.killer.kill:
				return

			time.sleep(0.5)
			times += 0.5

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

	def shouldCheck(self, revid):
		# Check should revision to be checked at all
		api = mwapi.MWAPI()
		rev = api.getRevision([revid])
		if "badrevids" in rev["query"]:
			return False

		return True

	def run(self):
		try:
			wiki = config_loader.current_config["core"]["lang"]+"wiki"
			# Event stream
			for event in EventSource(config_loader.current_config["core"]["stream_url"]):
				# Filter event stream
				if event.event == 'message':
					try:
						change = json.loads(event.data)
					except ValueError:
						continue

					if change["wiki"] == wiki and change["type"] == "edit" and change["namespace"] in config_loader.current_config["core"]["namespaces"]:
						# Check should revision to be checked at all
						if self.shouldCheck(change["revision"]["new"]):
							print(self.r_exec.shouldStabilize(change))
		except KeyboardInterrupt:
			print("terminating yuno...")
			self.killer.kill = True
			self.cf_updater.join()
