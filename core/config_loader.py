# Import python modules
import json
import traceback
import sys
import glob
import os
import logging

logger = logging.getLogger("infolog")

# Import core modules
from core import path

# Load core config for startup
cur_conf = {}
try:
	core_config_f = open(path.main()+"core/config.json", "r")
	cur_conf["core"] = json.load(core_config_f)
	core_config_f.close()
except:
	logger.critical("failed  to load core config")
	logger.critical("failed to startup")
	logger.critical(traceback.format_exc())
	sys.exit(1)

# Import core modules
from core import yapi

cfg_ver = 0

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
	global cur_conf
	global cfg_ver
	for conf in glob.glob(path.main()+"conf/"+"*.json"):
		try:
			conf_f = open(conf, "r")
			conf_json = json.load(conf_f)
			conf_f.close()
		except:
			logger.error("failed to load config from %s check crashreport for more info" % conf)
			logger.critical(traceback.format_exc())
			continue
		namestr = os.path.basename(conf)[:-5]
		if namestr not in cur_conf or cur_conf[namestr] != conf_json:
			cur_conf[namestr] = conf_json
			cfg_ver += 1
			logger.info("new local config \"%s\" loaded to core" % namestr)

# Check for new online config
def checkForOnlineUpdate():
	global cfg_ver
	global cur_conf

	lastrev = yapi.MWAPI.getLatestRev(cur_conf["core"]["online_conf_path"])

	if not lastrev:
		logger.error("config page \"%s\" doesn't exists" % cur_conf["core"]["online_conf_path"])
		return 1
	if lastrev != cfg_ver:
		logger.info("found new online config: %s" % str(lastrev))
		cfg_ver = lastrev
		conf = yapi.MWAPI.getText(cur_conf["core"]["online_conf_path"])
		try:
			new = json.loads(conf)
		except:
			logger.error("cannot load json: %s" % traceback.format_exc())
			logger.critical(traceback.format_exc())
			return 1

		updateConfig(cur_conf, new)
		logger.info("new online config loaded to core")
