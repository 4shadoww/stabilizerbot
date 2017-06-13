# Import python modules
import json
import traceback
import sys
import glob
import os

# Import core modules
from core import path

# Import pywikibot
import pywikibot

# Load core config for startup
current_config = {}
try:
	core_config_f = open(path.main()+"core/config.json", "r")
	current_config["core"] = json.load(core_config_f)
	core_config_f.close()
except:
	print("error: failed  to load core config")
	print("failed to startup")
	print(traceback.format_exc())
	sys.exit(1)

# Import core modules
from core.log import *

cfg_ver = 0
site = pywikibot.Site()

def updateConfigItems(holder, new):
	for item in new:
		holder[item] = new[item]

def updateConfig(holder, new):
	for item in new:
		if item == "core":
			updateConfigItems(holder["core"], new)
		else:
			holder[item] = new[item]

# Check for new local configs
def checkForLocalUpdate():
	global current_config
	global cfg_ver
	for conf in glob.glob(path.main()+"conf/"+"*.json"):
		try:
			conf_f = open(conf, "r")
			conf_json = json.load(conf_f)
			conf_f.close()
		except:
			printlog("error: failed to load config from", conf, "check crashreport for more info")
			crashreport(traceback.format_exc())
			continue
		namestr = os.path.basename(conf)[:-5]
		if namestr not in current_config or current_config[namestr] != conf_json:
			current_config[namestr] = conf_json
			cfg_ver += 1
			printlog("new local config \""+namestr+"\" loaded to core")

# Check for new online config
def checkForOnlineUpdate():
	global cfg_ver
	global current_config

	page = pywikibot.Page(site, current_config["core"]["online_conf_path"])

	if not page.exists():
		printlog("error: config page \""+core.config.online_conf_path+"\" doesn't exists")
		return 1
	if page.latestRevision() != cfg_ver:
		printlog("found new online config:", page.latestRevision())
		cfg_ver = page.latestRevision()
		try:
			new = json.loads(page.text)
		except:
			printlog("error: cannot load json:", traceback.format_exc())
			crashreport(traceback.format_exc())
			return 1

		updateConfig(current_config, new)
		printlog("new online config loaded to core")
