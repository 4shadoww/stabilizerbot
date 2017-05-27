# Import python modules
import json

# Import pywikibot
import pywikibot

# Local config file
core_config_f = open("core/config.json", "r")
core_config = json.load(core_config_f)

# Import core modules
from core.log import *

online_config = None
cfg_ver = 0
site = pywikibot.Site()

def updateConfig(old, new):
	for item in new:
		old[item] = new[item]

def checkForUpdate():
	global cfg_ver
	global online_config
	global core_config

	page = pywikibot.Page(site, core_config["online_conf_path"])

	if not page.exists():
		printlog("error: config page \""+core.config.online_conf_path+"\" doesn't exists")
		return 1
	if page.latestRevision() != cfg_ver:
		printlog("found new online config:", page.latestRevision())
		cfg_ver = page.latestRevision()
		online_config = json.loads(page.text)
		has_oc = True

		# Update core config
		updateConfig(core_config, online_config["core"])
		printlog("new config loaded to core")
